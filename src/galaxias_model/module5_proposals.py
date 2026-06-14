from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from galaxias_model.io import (
    EXPECTED_PARAMETER_COUNT,
    _resolve_family_parameter_rows,
    _validate_resolved_constraints,
)
from galaxias_model.types import ModelInputs, ResolvedParameters


DEFAULT_DRY_RUN_VARIANT = "baseline_current"
DEFAULT_DRY_RUN_SEED = 20260410
DEFAULT_DRY_RUN_REPLICATES = 5
DEFAULT_DRY_RUN_OUTPUT_DIR = Path("outputs/module5_dry_run_baseline_current_20260410")
DEFAULT_DRY_RUN_SEED_BASE_LABEL = "galaxias-module5-dry-run-v1"
DEFAULT_PARAMETER_VALUES_SHA256 = "49e080a23dcaca2f29874c0e3825bd806406f494b2db046307a84a74e8673c4c"
DEFAULT_PARAMETER_VALUES_PATH = Path(
    "outputs/remote/module4_observation_sensitivity_20260522T101942Z/"
    "baseline_current_seed20260410/parameter_values.csv.gz"
)
DEFAULT_PROPOSAL_MEMBERSHIP_PATH = Path("data/module4_5_proposal_set_membership.csv")
DEFAULT_MODULE4_MANIFEST_PATH = Path("data/module4_raw_artifact_manifest.csv")

APPROVED_DRY_RUN_PROPOSALS: tuple[tuple[str, str], ...] = (
    ("persistent_joint_cause", "persistent_joint_cause:p00162"),
    ("climbing_only", "climbing_only:p00216"),
    ("transient_perfect_storm", "transient_perfect_storm:p00144"),
    ("habitat_only_null", "habitat_only_null:p00761"),
    ("trout_only", "trout_only:p00814"),
)
APPROVED_DRY_RUN_PROPOSAL_IDS = tuple(proposal_id for _, proposal_id in APPROVED_DRY_RUN_PROPOSALS)
PROPOSAL_SOURCE_KEY_FIELDS: tuple[str, ...] = (
    "module4_run_id",
    "variant_id",
    "seed",
    "run_dir_name",
    "family_id",
    "proposal_id",
)


@dataclass(frozen=True)
class SelectedProposal:
    module4_run_id: str
    family_id: str
    family_label: str
    proposal_id: str
    proposal_source_key: str
    variant_id: str
    seed: int
    proposal_seed: int
    run_dir_name: str
    in_family_winners: bool


@dataclass(frozen=True)
class ParameterValuesArtifact:
    path: Path
    sha256: str
    manifest_row: dict[str, object]


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _source_key_part(field_name: str, value: object) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"Missing Module 5 proposal source-key field: {field_name}")
    if "|" in text:
        raise ValueError(f"Module 5 proposal source-key field contains '|': {field_name}={text}")
    return text


def build_proposal_source_key(
    *,
    module4_run_id: object,
    variant_id: object,
    seed: object,
    run_dir_name: object,
    family_id: object,
    proposal_id: object,
) -> str:
    """Build the canonical source-context key for a Module 5 proposal row."""
    values = {
        "module4_run_id": module4_run_id,
        "variant_id": variant_id,
        "seed": seed,
        "run_dir_name": run_dir_name,
        "family_id": family_id,
        "proposal_id": proposal_id,
    }
    return "|".join(_source_key_part(field, values[field]) for field in PROPOSAL_SOURCE_KEY_FIELDS)


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"seed": "Int64"}, keep_default_na=False)


def _relative_or_absolute(path: Path) -> Path:
    if path.is_absolute():
        return path
    return Path.cwd() / path


def load_selected_dry_run_proposals(
    proposal_membership_path: Path = DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
) -> tuple[SelectedProposal, ...]:
    membership = _read_csv(proposal_membership_path)
    selected_by_id = {
        proposal_id: family_id for family_id, proposal_id in APPROVED_DRY_RUN_PROPOSALS
    }

    subset = membership.loc[
        membership["proposal_id"].isin(selected_by_id)
        & (membership["variant_id"] == DEFAULT_DRY_RUN_VARIANT)
        & (membership["seed"].astype(int) == DEFAULT_DRY_RUN_SEED)
    ].copy()

    found = set(subset["proposal_id"].astype(str))
    expected = set(selected_by_id)
    if found != expected:
        raise ValueError(f"Selected dry-run proposals mismatch. Missing={sorted(expected - found)}, extra={sorted(found - expected)}")

    proposals_by_id: dict[str, SelectedProposal] = {}
    for row in subset.to_dict(orient="records"):
        proposal_id = str(row["proposal_id"])
        family_id = str(row["family_id"])
        module4_run_id = str(row["module4_run_id"])
        variant_id = str(row["variant_id"])
        seed = int(row["seed"])
        run_dir_name = str(row["run_dir_name"])
        expected_family = selected_by_id[proposal_id]
        if family_id != expected_family:
            raise ValueError(f"Proposal {proposal_id} family mismatch: {family_id} != {expected_family}")
        if not _as_bool(row["in_family_winners"]):
            raise ValueError(f"Proposal {proposal_id} is not marked in_family_winners")
        proposal_source_key = build_proposal_source_key(
            module4_run_id=module4_run_id,
            variant_id=variant_id,
            seed=seed,
            run_dir_name=run_dir_name,
            family_id=family_id,
            proposal_id=proposal_id,
        )
        proposals_by_id[proposal_id] = SelectedProposal(
            module4_run_id=module4_run_id,
            family_id=family_id,
            family_label=str(row["family_label"]),
            proposal_id=proposal_id,
            proposal_source_key=proposal_source_key,
            variant_id=variant_id,
            seed=seed,
            proposal_seed=int(row["proposal_seed"]),
            run_dir_name=run_dir_name,
            in_family_winners=_as_bool(row["in_family_winners"]),
        )

    return tuple(proposals_by_id[proposal_id] for proposal_id in APPROVED_DRY_RUN_PROPOSAL_IDS)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_parameter_values_artifact(
    module4_manifest_path: Path = DEFAULT_MODULE4_MANIFEST_PATH,
    parameter_values_path: Path = DEFAULT_PARAMETER_VALUES_PATH,
) -> ParameterValuesArtifact:
    manifest = _read_csv(module4_manifest_path)
    subset = manifest.loc[
        (manifest["variant_id"] == DEFAULT_DRY_RUN_VARIANT)
        & (manifest["seed"].astype(int) == DEFAULT_DRY_RUN_SEED)
        & (manifest["file_role"] == "parameter_values")
    ]
    if len(subset) != 1:
        raise ValueError(f"Expected one parameter_values manifest row, found {len(subset)}")

    row = subset.iloc[0].to_dict()
    manifest_path = _relative_or_absolute(Path(str(row["local_path"]))).resolve()
    requested_path = _relative_or_absolute(parameter_values_path).resolve()
    if manifest_path != requested_path:
        raise ValueError(f"Parameter artifact path mismatch: {requested_path} != manifest {manifest_path}")
    if not requested_path.exists():
        raise FileNotFoundError(f"Missing parameter-values artifact: {requested_path}")

    actual_sha = _sha256(requested_path)
    expected_sha = str(row["local_sha256"])
    if actual_sha != expected_sha:
        raise ValueError(f"Parameter-values SHA-256 mismatch: {actual_sha} != {expected_sha}")
    if actual_sha != DEFAULT_PARAMETER_VALUES_SHA256:
        raise ValueError(f"Parameter-values SHA-256 does not match Goal 006 expected hash: {actual_sha}")

    return ParameterValuesArtifact(path=requested_path, sha256=actual_sha, manifest_row=row)


def load_parameter_values_table(parameter_values_path: Path = DEFAULT_PARAMETER_VALUES_PATH) -> pd.DataFrame:
    return pd.read_csv(parameter_values_path)


def _validate_parameter_subset(proposal: SelectedProposal, subset: pd.DataFrame) -> None:
    if len(subset) != EXPECTED_PARAMETER_COUNT:
        raise ValueError(f"{proposal.proposal_id} has {len(subset)} parameter rows, expected {EXPECTED_PARAMETER_COUNT}")
    if subset["parameter_id"].nunique() != EXPECTED_PARAMETER_COUNT:
        raise ValueError(f"{proposal.proposal_id} has duplicate parameter_id rows")
    families = set(subset["family_id"].astype(str))
    if families != {proposal.family_id}:
        raise ValueError(f"{proposal.proposal_id} family mismatch in parameter values: {families}")
    missing = {"parameter_id", "parameter_status", "value_natural", "value_sampling", "sampled_flag"} - set(subset.columns)
    if missing:
        raise ValueError(f"{proposal.proposal_id} parameter table missing columns: {sorted(missing)}")


def resolve_proposal_parameters(
    model_inputs: ModelInputs,
    proposal: SelectedProposal,
    parameter_values: pd.DataFrame,
) -> ResolvedParameters:
    subset = parameter_values.loc[parameter_values["proposal_id"] == proposal.proposal_id].copy()
    _validate_parameter_subset(proposal, subset)

    family_rows = _resolve_family_parameter_rows(model_inputs, proposal.family_id)
    proposal_rows = subset.rename(columns={"parameter_status": "proposal_parameter_status"})
    merged = family_rows.merge(
        proposal_rows[
            [
                "parameter_id",
                "proposal_parameter_status",
                "value_natural",
                "value_sampling",
                "sampled_flag",
            ]
        ],
        on="parameter_id",
        how="inner",
    )
    if len(merged) != EXPECTED_PARAMETER_COUNT:
        raise ValueError(f"Failed to merge all sampled parameters for {proposal.proposal_id}")

    status_mismatch = merged.loc[
        merged["parameter_status"].astype(str) != merged["proposal_parameter_status"].astype(str),
        ["parameter_id", "parameter_status", "proposal_parameter_status"],
    ]
    if not status_mismatch.empty:
        raise ValueError(f"Parameter status mismatch for {proposal.proposal_id}: {status_mismatch.to_dict(orient='records')}")

    values: dict[str, float] = {}
    statuses: dict[str, str] = {}
    manifest_records: list[dict[str, object]] = []

    for row in merged.to_dict(orient="records"):
        parameter_id = str(row["parameter_id"])
        status = str(row["proposal_parameter_status"])
        effective_value = float(row["value_natural"])
        values[parameter_id] = effective_value
        statuses[parameter_id] = status
        manifest_records.append(
            {
                "proposal_id": proposal.proposal_id,
                "proposal_source_key": proposal.proposal_source_key,
                "module4_run_id": proposal.module4_run_id,
                "variant_id": proposal.variant_id,
                "seed": proposal.seed,
                "proposal_seed": proposal.proposal_seed,
                "run_dir_name": proposal.run_dir_name,
                "family_id": proposal.family_id,
                "family_label": proposal.family_label,
                "parameter_id": parameter_id,
                "parameter_name": row["parameter_name"],
                "parameter_group": row["parameter_group"],
                "status": status,
                "active": status != "unused",
                "default_value": float(row["default_value"]),
                "effective_value": effective_value,
                "value_sampling": float(row["value_sampling"]),
                "sampled_flag": _as_bool(row["sampled_flag"]),
                "fixed_value": row["fixed_value"],
                "distribution_family": row["distribution_family"],
                "sampling_transform": row["sampling_transform"],
                "source_strategy": row["source_strategy"],
                "notes": row["notes"],
                "family_notes": row["notes_family"],
            }
        )

    _validate_resolved_constraints(model_inputs.constraints, values, proposal.family_id, statuses)

    manifest = pd.DataFrame(manifest_records).sort_values("parameter_id").reset_index(drop=True)
    return ResolvedParameters(
        family_id=proposal.family_id,
        family_label=proposal.family_label,
        manifest=manifest,
        values=values,
        statuses=statuses,
    )


def proposals_by_family(proposals: Iterable[SelectedProposal]) -> dict[str, SelectedProposal]:
    by_family: dict[str, SelectedProposal] = {}
    for proposal in proposals:
        if proposal.family_id in by_family:
            raise ValueError(f"Duplicate selected proposal for family {proposal.family_id}")
        by_family[proposal.family_id] = proposal
    return by_family


def derive_module5_seed(
    proposal_source_key: str,
    intervention_id: str,
    stochastic_replicate_id: int,
    base_label: str = DEFAULT_DRY_RUN_SEED_BASE_LABEL,
) -> int:
    key = f"{base_label}|{proposal_source_key}|{intervention_id}|{stochastic_replicate_id}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    return int.from_bytes(digest[:8], "big") % (2**32)
