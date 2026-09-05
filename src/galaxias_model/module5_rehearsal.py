from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from galaxias_model.io import load_model_inputs
from galaxias_model.module5_counterfactual import (
    DEFAULT_INTERVENTIONS_PATH,
    DEFAULT_OUTCOME_SCHEMA_PATH,
    _attach_uncertainty_summaries,
    _build_output_row,
    _file_sha256,
    _git_sha,
    _git_status_short,
    _relative_path,
    _run_matched_pair,
    read_intervention_rows,
    read_outcome_schema_columns,
)
from galaxias_model.module5_partitions import PARTITION_DEFINITIONS
from galaxias_model.module5_proposals import (
    DEFAULT_MODULE4_MANIFEST_PATH,
    DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
    PROPOSAL_SOURCE_KEY_FIELDS,
    SelectedProposal,
    build_proposal_source_key,
    derive_module5_seed,
    load_parameter_values_table,
    resolve_proposal_parameters,
)
from galaxias_model.types import SimulationConfig


DEFAULT_REHEARSAL_REPLICATES = 25
REHEARSAL_STATUS = "module5_matched_counterfactual_execution"
REHEARSAL_SEED_BASE_LABEL = "galaxias-module5-25rep-rehearsal-v1"
DEFAULT_REHEARSAL_OUTPUT_DIR = Path("outputs/module5_25rep_rehearsal")
DEFAULT_REHEARSAL_SCRIPT_PATH = Path("scripts/run_module5_25rep_rehearsal.py")

REHEARSAL_PARTITION_ROW_COUNTS: dict[str, int] = {
    "headline/persistent_joint_cause": 26500,
    "headline/climbing_only": 11750,
    "headline/transient_perfect_storm": 25000,
    "diagnostic_sidecar/climbing_only_no_trout_pressure": 5875,
    "negative_reference/habitat_only_null": 375,
    "negative_reference/trout_only": 375,
}


@dataclass(frozen=True)
class RehearsalSource:
    source_set: str
    module4_run_id: str
    variant_id: str
    seed: int
    run_dir_name: str
    family_id: str
    family_label: str
    proposal_id: str
    proposal_seed: int
    proposal_source_key: str

    @property
    def context_key(self) -> tuple[str, str, str, str]:
        return (
            self.module4_run_id,
            self.variant_id,
            str(self.seed),
            self.run_dir_name,
        )

    def to_selected_proposal(self) -> SelectedProposal:
        return SelectedProposal(
            module4_run_id=self.module4_run_id,
            family_id=self.family_id,
            family_label=self.family_label,
            proposal_id=self.proposal_id,
            proposal_source_key=self.proposal_source_key,
            variant_id=self.variant_id,
            seed=self.seed,
            proposal_seed=self.proposal_seed,
            run_dir_name=self.run_dir_name,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "source_set": self.source_set,
            "module4_run_id": self.module4_run_id,
            "variant_id": self.variant_id,
            "seed": self.seed,
            "run_dir_name": self.run_dir_name,
            "family_id": self.family_id,
            "family_label": self.family_label,
            "proposal_id": self.proposal_id,
            "proposal_seed": self.proposal_seed,
            "proposal_source_key": self.proposal_source_key,
        }


@dataclass(frozen=True)
class ParameterArtifact:
    context_key: tuple[str, str, str, str]
    local_path: Path
    remote_artifact_path: Path
    expected_bytes: int
    expected_sha256: str
    manifest_row: dict[str, object]

    def with_paths(
        self,
        *,
        local_path: Path | None = None,
        remote_artifact_path: Path | None = None,
        expected_bytes: int | None = None,
        expected_sha256: str | None = None,
    ) -> "ParameterArtifact":
        return replace(
            self,
            local_path=local_path if local_path is not None else self.local_path,
            remote_artifact_path=(
                remote_artifact_path
                if remote_artifact_path is not None
                else self.remote_artifact_path
            ),
            expected_bytes=(
                expected_bytes if expected_bytes is not None else self.expected_bytes
            ),
            expected_sha256=(
                expected_sha256 if expected_sha256 is not None else self.expected_sha256
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "context_key": "|".join(self.context_key),
            "local_path": self.local_path.as_posix(),
            "remote_artifact_path": self.remote_artifact_path.as_posix(),
            "expected_bytes": self.expected_bytes,
            "expected_sha256": self.expected_sha256,
        }


@dataclass(frozen=True)
class VerifiedArtifact:
    context_key: tuple[str, str, str, str]
    path: Path
    source: str
    expected_bytes: int
    actual_bytes: int
    expected_sha256: str
    actual_sha256: str
    verified: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "context_key": "|".join(self.context_key),
            "path": self.path.as_posix(),
            "source": self.source,
            "expected_bytes": self.expected_bytes,
            "actual_bytes": self.actual_bytes,
            "expected_sha256": self.expected_sha256,
            "actual_sha256": self.actual_sha256,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class RehearsalPartitionPlan:
    label: str
    source_set: str
    family_id: str
    intervention_ids: tuple[str, ...]
    sources: tuple[RehearsalSource, ...]
    intervention_rows: tuple[dict[str, str], ...]

    def expected_rows(self, replicates: int) -> int:
        return len(self.sources) * len(self.intervention_rows) * replicates

    @property
    def source_intervention_units(self) -> int:
        return len(self.sources) * len(self.intervention_rows)

    def to_summary_dict(self, replicates: int) -> dict[str, object]:
        return {
            "label": self.label,
            "source_set": self.source_set,
            "family_id": self.family_id,
            "source_count": len(self.sources),
            "intervention_ids": list(self.intervention_ids),
            "intervention_count": len(self.intervention_rows),
            "source_intervention_units": self.source_intervention_units,
            "replicates": replicates,
            "expected_rows": self.expected_rows(replicates),
        }


@dataclass(frozen=True)
class RehearsalPlan:
    replicates: int
    partitions: tuple[RehearsalPartitionPlan, ...]
    required_artifacts: tuple[ParameterArtifact, ...]

    @property
    def partition_row_counts(self) -> dict[str, int]:
        return {
            partition.label: partition.expected_rows(self.replicates)
            for partition in self.partitions
        }

    @property
    def expected_row_count(self) -> int:
        return sum(self.partition_row_counts.values())

    @property
    def source_intervention_unit_count(self) -> int:
        return sum(partition.source_intervention_units for partition in self.partitions)

    @property
    def distinct_sources(self) -> tuple[RehearsalSource, ...]:
        by_key: dict[str, RehearsalSource] = {}
        for partition in self.partitions:
            for source in partition.sources:
                by_key.setdefault(source.proposal_source_key, source)
        return tuple(by_key[key] for key in sorted(by_key))

    @property
    def distinct_proposal_source_key_count(self) -> int:
        return len(self.distinct_sources)

    @property
    def source_context_count(self) -> int:
        return len({source.context_key for source in self.distinct_sources})

    def accepted_source_count_by_family(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for source in self.distinct_sources:
            if source.source_set == "accepted":
                counts[source.family_id] = counts.get(source.family_id, 0) + 1
        return dict(sorted(counts.items()))

    def negative_reference_source_count_by_family(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for source in self.distinct_sources:
            if source.source_set == "family_winners":
                counts[source.family_id] = counts.get(source.family_id, 0) + 1
        return dict(sorted(counts.items()))

    def to_summary_dict(self) -> dict[str, object]:
        return {
            "replicates": self.replicates,
            "expected_row_count": self.expected_row_count,
            "source_intervention_unit_count": self.source_intervention_unit_count,
            "distinct_proposal_source_key_count": self.distinct_proposal_source_key_count,
            "source_context_count": self.source_context_count,
            "accepted_source_count_by_family": self.accepted_source_count_by_family(),
            "negative_reference_source_count_by_family": self.negative_reference_source_count_by_family(),
            "partition_row_counts": self.partition_row_counts,
            "partitions": [
                partition.to_summary_dict(self.replicates)
                for partition in self.partitions
            ],
            "required_artifacts": [
                artifact.to_dict() for artifact in self.required_artifacts
            ],
        }


def _as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if reader.fieldnames is None:
            raise ValueError(f"CSV missing header: {path}")
        return rows, reader.fieldnames


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def _source_from_membership(row: dict[str, str], source_set: str) -> RehearsalSource:
    seed = int(row["seed"])
    proposal_source_key = build_proposal_source_key(
        module4_run_id=row["module4_run_id"],
        variant_id=row["variant_id"],
        seed=seed,
        run_dir_name=row["run_dir_name"],
        family_id=row["family_id"],
        proposal_id=row["proposal_id"],
    )
    return RehearsalSource(
        source_set=source_set,
        module4_run_id=row["module4_run_id"],
        variant_id=row["variant_id"],
        seed=seed,
        run_dir_name=row["run_dir_name"],
        family_id=row["family_id"],
        family_label=row["family_label"],
        proposal_id=row["proposal_id"],
        proposal_seed=int(row["proposal_seed"]),
        proposal_source_key=proposal_source_key,
    )


def _select_sources(
    membership_rows: list[dict[str, str]],
    *,
    family_id: str,
    source_set: str,
) -> tuple[RehearsalSource, ...]:
    if source_set == "accepted":
        selected = [
            row
            for row in membership_rows
            if row["family_id"] == family_id and _as_bool(row["in_accepted"])
        ]
    elif source_set == "family_winners":
        selected = [
            row
            for row in membership_rows
            if row["family_id"] == family_id and _as_bool(row["in_family_winners"])
        ]
    else:
        raise ValueError(f"Unsupported rehearsal source_set: {source_set}")

    sources = tuple(
        sorted(
            (_source_from_membership(row, source_set) for row in selected),
            key=lambda source: source.proposal_source_key,
        )
    )
    duplicate_keys = pd.Series([source.proposal_source_key for source in sources])
    if not duplicate_keys.empty and duplicate_keys.duplicated().any():
        duplicates = sorted(duplicate_keys.loc[duplicate_keys.duplicated()].unique())
        raise ValueError(f"Duplicate proposal_source_key values in source selection: {duplicates[:5]}")
    return sources


def _artifact_from_manifest(row: dict[str, str]) -> ParameterArtifact:
    context_key = (
        row["run_id"],
        row["variant_id"],
        str(row["seed"]),
        row["run_dir_name"],
    )
    return ParameterArtifact(
        context_key=context_key,
        local_path=Path(row["local_path"]),
        remote_artifact_path=Path(row["remote_artifact_path"]),
        expected_bytes=int(row["local_bytes"]),
        expected_sha256=row["local_sha256"],
        manifest_row=dict(row),
    )


def build_rehearsal_plan(
    proposal_membership_path: Path = DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
    interventions_path: Path = DEFAULT_INTERVENTIONS_PATH,
    module4_manifest_path: Path = DEFAULT_MODULE4_MANIFEST_PATH,
    replicates: int = DEFAULT_REHEARSAL_REPLICATES,
) -> RehearsalPlan:
    if replicates < 1:
        raise ValueError("replicates must be >= 1")

    membership_rows, _ = _read_csv_rows(proposal_membership_path)
    intervention_rows = read_intervention_rows(interventions_path)
    interventions_by_id = {row["intervention_id"]: row for row in intervention_rows}
    manifest_rows, _ = _read_csv_rows(module4_manifest_path)

    partitions: list[RehearsalPartitionPlan] = []
    for definition in PARTITION_DEFINITIONS:
        sources = _select_sources(
            membership_rows,
            family_id=definition.family_id,
            source_set=definition.source_set,
        )
        missing_interventions = [
            intervention_id
            for intervention_id in definition.intervention_ids
            if intervention_id not in interventions_by_id
        ]
        if missing_interventions:
            raise ValueError(f"Missing intervention rows: {missing_interventions}")
        selected_interventions = tuple(
            interventions_by_id[intervention_id]
            for intervention_id in definition.intervention_ids
        )
        for intervention in selected_interventions:
            if intervention["family_id"] != definition.family_id:
                raise ValueError(
                    f"{intervention['intervention_id']} family mismatch: "
                    f"{intervention['family_id']} != {definition.family_id}"
                )
        partitions.append(
            RehearsalPartitionPlan(
                label=definition.label,
                source_set=definition.source_set,
                family_id=definition.family_id,
                intervention_ids=definition.intervention_ids,
                sources=sources,
                intervention_rows=selected_interventions,
            )
        )

    contexts = {source.context_key for partition in partitions for source in partition.sources}
    parameter_rows_by_context: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for row in manifest_rows:
        if row["file_role"] != "parameter_values":
            continue
        context = (
            row["run_id"],
            row["variant_id"],
            str(row["seed"]),
            row["run_dir_name"],
        )
        parameter_rows_by_context.setdefault(context, []).append(row)

    missing_contexts = sorted(contexts - set(parameter_rows_by_context))
    if missing_contexts:
        raise ValueError(f"Missing parameter_values manifest contexts: {missing_contexts}")

    required_artifacts: list[ParameterArtifact] = []
    for context in sorted(contexts):
        rows = parameter_rows_by_context.get(context, [])
        if len(rows) != 1:
            raise ValueError(f"Expected one parameter_values row for {context}, found {len(rows)}")
        required_artifacts.append(_artifact_from_manifest(rows[0]))

    plan = RehearsalPlan(
        replicates=replicates,
        partitions=tuple(partitions),
        required_artifacts=tuple(required_artifacts),
    )
    if replicates == DEFAULT_REHEARSAL_REPLICATES and plan.partition_row_counts != REHEARSAL_PARTITION_ROW_COUNTS:
        raise ValueError(
            "Goal 012 partition row counts changed: "
            f"{plan.partition_row_counts} != {REHEARSAL_PARTITION_ROW_COUNTS}"
        )
    if replicates == DEFAULT_REHEARSAL_REPLICATES and plan.expected_row_count != 69875:
        raise ValueError(f"Goal 012 expected row count changed: {plan.expected_row_count}")
    return plan


def _choose_artifact_path(
    artifact: ParameterArtifact,
    *,
    root: Path,
    path_preference: str,
) -> tuple[Path, str]:
    local_path = _resolve_path(artifact.local_path, root)
    remote_path = artifact.remote_artifact_path
    if path_preference not in {"auto", "local", "remote"}:
        raise ValueError(f"Unsupported path_preference: {path_preference}")

    candidates: list[tuple[Path, str]] = []
    if path_preference in {"auto", "remote"} and str(remote_path):
        candidates.append((remote_path, "remote_artifact_path"))
    if path_preference in {"auto", "local"}:
        candidates.append((local_path, "local_path"))
    if path_preference == "local" and str(remote_path):
        candidates.append((remote_path, "remote_artifact_path"))
    if path_preference == "remote":
        candidates.append((local_path, "local_path"))

    for path, source in candidates:
        if path.exists():
            return path, source
    raise FileNotFoundError(
        f"No parameter_values artifact found for {'|'.join(artifact.context_key)}"
    )


def verify_required_parameter_artifacts(
    artifacts: Iterable[ParameterArtifact],
    *,
    root: Path = Path("."),
    path_preference: str = "auto",
) -> tuple[VerifiedArtifact, ...]:
    verified: list[VerifiedArtifact] = []
    for artifact in artifacts:
        path, source = _choose_artifact_path(
            artifact,
            root=root,
            path_preference=path_preference,
        )
        actual_bytes = path.stat().st_size
        if actual_bytes != artifact.expected_bytes:
            raise ValueError(
                f"Size mismatch for {path}: {actual_bytes} != {artifact.expected_bytes}"
            )
        actual_sha = _sha256(path)
        if actual_sha != artifact.expected_sha256:
            raise ValueError(
                f"SHA-256 mismatch for {path}: {actual_sha} != {artifact.expected_sha256}"
            )
        verified.append(
            VerifiedArtifact(
                context_key=artifact.context_key,
                path=path,
                source=source,
                expected_bytes=artifact.expected_bytes,
                actual_bytes=actual_bytes,
                expected_sha256=artifact.expected_sha256,
                actual_sha256=actual_sha,
                verified=True,
            )
        )
    return tuple(verified)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_rehearsal_preflight(
    output_dir: Path,
    plan: RehearsalPlan,
    verified_artifacts: tuple[VerifiedArtifact, ...],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "rehearsal_plan.json", plan.to_summary_dict())
    pd.DataFrame([artifact.to_dict() for artifact in verified_artifacts]).to_csv(
        output_dir / "artifact_verification.csv",
        index=False,
    )


def _write_rehearsal_provenance(
    output_dir: Path,
    output_file: Path,
    *,
    run_id: str,
    plan: RehearsalPlan,
    verified_artifacts: tuple[VerifiedArtifact, ...],
    proposal_membership_path: Path,
    module4_manifest_path: Path,
    interventions_path: Path,
    outcome_schema_path: Path,
    stochastic: bool,
    workers: int,
) -> None:
    payload = {
        "module": "Module 5 matched-counterfactual execution",
        "status": REHEARSAL_STATUS,
        "production_attribution": False,
        "run_id": run_id,
        "output_file": _relative_path(output_file),
        "output_dir": _relative_path(output_dir),
        "script_path": DEFAULT_REHEARSAL_SCRIPT_PATH.as_posix(),
        "proposal_membership_path": _relative_path(proposal_membership_path),
        "module4_manifest_path": _relative_path(module4_manifest_path),
        "interventions_path": _relative_path(interventions_path),
        "outcome_schema_path": _relative_path(outcome_schema_path),
        "expected_replicates": plan.replicates,
        "expected_row_count": plan.expected_row_count,
        "expected_partition_row_counts": plan.partition_row_counts,
        "expected_source_intervention_units": plan.source_intervention_unit_count,
        "expected_distinct_proposal_source_keys": plan.distinct_proposal_source_key_count,
        "source_context_count": plan.source_context_count,
        "selected_proposal_source_keys": [
            source.proposal_source_key for source in plan.distinct_sources
        ],
        "source_identity_fields": list(PROPOSAL_SOURCE_KEY_FIELDS),
        "source_identity_strategy": (
            "proposal_source_key=module4_run_id|variant_id|seed|run_dir_name|family_id|proposal_id"
        ),
        "seed_derivation": "sha256(base_label|proposal_source_key|intervention_id|stochastic_replicate_id) modulo 2**32",
        "seed_base_label": REHEARSAL_SEED_BASE_LABEL,
        "partition_plan": [
            partition.to_summary_dict(plan.replicates)
            for partition in plan.partitions
        ],
        "accepted_source_count_by_family": plan.accepted_source_count_by_family(),
        "negative_reference_source_count_by_family": plan.negative_reference_source_count_by_family(),
        "artifact_verification": [
            artifact.to_dict() for artifact in verified_artifacts
        ],
        "artifact_verification_count": len(verified_artifacts),
        "git_sha": _git_sha(),
        "git_status_short": _git_status_short(),
        "python_version": sys.version.split()[0],
        "compute_host": platform.node(),
        "stochastic": stochastic,
        "workers": workers,
        "matched_outcomes_sha256": _file_sha256(output_file),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "boundary_note": (
            "This matched-counterfactual execution uses the configured replicate "
            "count. It is not production attribution or manuscript evidence."
        ),
    }
    _write_json(output_dir / "provenance.json", payload)


def run_module5_25rep_rehearsal(
    *,
    data_dir: Path,
    proposal_membership_path: Path = DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
    module4_manifest_path: Path = DEFAULT_MODULE4_MANIFEST_PATH,
    interventions_path: Path = DEFAULT_INTERVENTIONS_PATH,
    outcome_schema_path: Path = DEFAULT_OUTCOME_SCHEMA_PATH,
    output_dir: Path = DEFAULT_REHEARSAL_OUTPUT_DIR,
    run_id: str = "local-module5-25rep-rehearsal",
    replicates: int = DEFAULT_REHEARSAL_REPLICATES,
    stochastic: bool = True,
    path_preference: str = "auto",
    plan_only: bool = False,
    overwrite: bool = False,
    workers: int = 1,
) -> Path:
    if workers < 1:
        raise ValueError("workers must be >= 1")
    proposal_membership_path = proposal_membership_path.resolve()
    module4_manifest_path = module4_manifest_path.resolve()
    interventions_path = interventions_path.resolve()
    outcome_schema_path = outcome_schema_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "matched_outcomes.csv"
    if output_file.exists() and not overwrite and not plan_only:
        raise FileExistsError(f"Refusing to overwrite existing rehearsal output: {output_file}")

    plan = build_rehearsal_plan(
        proposal_membership_path=proposal_membership_path,
        interventions_path=interventions_path,
        module4_manifest_path=module4_manifest_path,
        replicates=replicates,
    )
    verified_artifacts = verify_required_parameter_artifacts(
        plan.required_artifacts,
        root=Path.cwd(),
        path_preference=path_preference,
    )
    write_rehearsal_preflight(output_dir, plan, verified_artifacts)
    if plan_only:
        return output_dir / "rehearsal_plan.json"

    schema_columns = read_outcome_schema_columns(outcome_schema_path)
    verified_by_context = {artifact.context_key: artifact for artifact in verified_artifacts}
    timestamp = datetime.now(timezone.utc).isoformat()
    tasks = _build_execution_tasks(
        plan=plan,
        verified_by_context=verified_by_context,
        data_dir=data_dir,
        interventions_path=interventions_path,
        module4_manifest_path=module4_manifest_path,
        stochastic=stochastic,
        timestamp=timestamp,
    )
    output_rows = _run_execution_tasks(tasks, workers=workers)

    output_rows = _attach_uncertainty_summaries(output_rows)
    pd.DataFrame(output_rows).loc[:, schema_columns].to_csv(output_file, index=False)
    _write_rehearsal_provenance(
        output_dir,
        output_file,
        run_id=run_id,
        plan=plan,
        verified_artifacts=verified_artifacts,
        proposal_membership_path=proposal_membership_path,
        module4_manifest_path=module4_manifest_path,
        interventions_path=interventions_path,
        outcome_schema_path=outcome_schema_path,
        stochastic=stochastic,
        workers=workers,
    )
    return output_file


def _build_execution_tasks(
    *,
    plan: RehearsalPlan,
    verified_by_context: dict[tuple[str, str, str, str], VerifiedArtifact],
    data_dir: Path,
    interventions_path: Path,
    module4_manifest_path: Path,
    stochastic: bool,
    timestamp: str,
) -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    task_index = 0
    for partition in plan.partitions:
        for source in partition.sources:
            artifact = verified_by_context[source.context_key]
            tasks.append(
                {
                    "task_index": task_index,
                    "source": source.to_dict(),
                    "intervention_rows": list(partition.intervention_rows),
                    "replicates": plan.replicates,
                    "artifact_path": artifact.path.as_posix(),
                    "data_dir": data_dir.as_posix(),
                    "interventions_path": interventions_path.as_posix(),
                    "module4_manifest_path": module4_manifest_path.as_posix(),
                    "stochastic": stochastic,
                    "timestamp": timestamp,
                }
            )
            task_index += 1
    return tasks


def _source_from_dict(payload: dict[str, object]) -> RehearsalSource:
    return RehearsalSource(
        source_set=str(payload["source_set"]),
        module4_run_id=str(payload["module4_run_id"]),
        variant_id=str(payload["variant_id"]),
        seed=int(payload["seed"]),
        run_dir_name=str(payload["run_dir_name"]),
        family_id=str(payload["family_id"]),
        family_label=str(payload["family_label"]),
        proposal_id=str(payload["proposal_id"]),
        proposal_seed=int(payload["proposal_seed"]),
        proposal_source_key=str(payload["proposal_source_key"]),
    )


def _run_execution_task(task: dict[str, object]) -> tuple[int, list[dict[str, object]]]:
    source = _source_from_dict(task["source"])  # type: ignore[arg-type]
    model_inputs = load_model_inputs(Path(str(task["data_dir"])))
    parameter_values = load_parameter_values_table(Path(str(task["artifact_path"])))
    params = resolve_proposal_parameters(
        model_inputs,
        source.to_selected_proposal(),
        parameter_values,
    )
    config = SimulationConfig(stochastic=bool(task["stochastic"]))
    rows: list[dict[str, object]] = []
    for intervention_row in task["intervention_rows"]:  # type: ignore[union-attr]
        intervention = {str(key): str(value) for key, value in dict(intervention_row).items()}
        for replicate_id in range(int(task["replicates"])):
            stochastic_seed = derive_module5_seed(
                source.proposal_source_key,
                intervention["intervention_id"],
                replicate_id,
                base_label=REHEARSAL_SEED_BASE_LABEL,
            )
            baseline, counterfactual = _run_matched_pair(
                intervention,
                params,
                config,
                seed=stochastic_seed,
            )
            rows.append(
                _build_output_row(
                    intervention,
                    baseline,
                    counterfactual,
                    replicate_id,
                    source.proposal_seed,
                    stochastic_seed,
                    str(task["timestamp"]),
                    Path(str(task["interventions_path"])),
                    proposal_id=source.proposal_id,
                    variant_id=source.variant_id,
                    source_seed=source.seed,
                    proposal_source_key=source.proposal_source_key,
                    module4_run_id=source.module4_run_id,
                    run_dir_name=source.run_dir_name,
                    provenance_script=DEFAULT_REHEARSAL_SCRIPT_PATH,
                    module4_manifest=Path(str(task["module4_manifest_path"])),
                )
            )
    return int(task["task_index"]), rows


def _run_execution_tasks(tasks: list[dict[str, object]], *, workers: int) -> list[dict[str, object]]:
    ordered_results: dict[int, list[dict[str, object]]] = {}
    total = len(tasks)
    if workers == 1:
        for position, task in enumerate(tasks, start=1):
            task_index, rows = _run_execution_task(task)
            ordered_results[task_index] = rows
            if position % 50 == 0 or position == total:
                print(f"completed_tasks={position}/{total}", flush=True)
    else:
        max_workers = min(workers, os.cpu_count() or workers)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_execution_task, task) for task in tasks]
            for position, future in enumerate(as_completed(futures), start=1):
                task_index, rows = future.result()
                ordered_results[task_index] = rows
                if position % 50 == 0 or position == total:
                    print(f"completed_tasks={position}/{total}", flush=True)

    output_rows: list[dict[str, object]] = []
    for task_index in sorted(ordered_results):
        output_rows.extend(ordered_results[task_index])
    return output_rows
