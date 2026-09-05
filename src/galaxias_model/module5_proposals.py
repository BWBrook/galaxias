from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from galaxias_model.io import (
    EXPECTED_PARAMETER_COUNT,
    _resolve_family_parameter_rows,
    _validate_resolved_constraints,
)
from galaxias_model.types import ModelInputs, ResolvedParameters


DEFAULT_PROPOSAL_MEMBERSHIP_PATH = Path("data/module4_5_proposal_set_membership.csv")
DEFAULT_MODULE4_MANIFEST_PATH = Path("data/module4_raw_artifact_manifest.csv")

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


def load_parameter_values_table(parameter_values_path: Path) -> pd.DataFrame:
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


def derive_module5_seed(
    proposal_source_key: str,
    intervention_id: str,
    stochastic_replicate_id: int,
    *,
    base_label: str,
) -> int:
    key = f"{base_label}|{proposal_source_key}|{intervention_id}|{stochastic_replicate_id}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    return int.from_bytes(digest[:8], "big") % (2**32)
