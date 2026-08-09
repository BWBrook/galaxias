from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

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
    apply_module5_intervention_overrides,
    read_intervention_rows,
    read_outcome_schema_columns,
)
from galaxias_model.module5_interaction_stability import (
    FACTORIAL_FAMILIES,
    REMOVAL_AXES,
)
from galaxias_model.module5_proposals import (
    DEFAULT_MODULE4_MANIFEST_PATH,
    DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
    PROPOSAL_SOURCE_KEY_FIELDS,
    load_parameter_values_table,
    resolve_proposal_parameters,
)
from galaxias_model.module5_rehearsal import (
    ParameterArtifact,
    RehearsalSource,
    VerifiedArtifact,
    _artifact_from_manifest,
    _read_csv_rows,
    _select_sources,
    _source_from_dict,
    verify_required_parameter_artifacts,
)
from galaxias_model.simulation import run_historical_simulation
from galaxias_model.types import ResolvedParameters, SimulationConfig, SimulationResult


DEFAULT_FACTORIAL_EXTENSION_REPLICATES = 250
DEFAULT_FACTORIAL_EXTENSION_OUTPUT_DIR = Path("outputs/module5_factorial_extension")
DEFAULT_FACTORIAL_EXTENSION_SCRIPT_PATH = Path(
    "scripts/run_module5_factorial_extension.py"
)
FACTORIAL_EXTENSION_STATUS = "module5_shared_four_arm_extension"
FACTORIAL_EXTENSION_SEED_BASE_LABEL = "galaxias-module5-shared-four-arm-v1"
FACTORIAL_EXTENSION_SOURCE_COUNTS = {
    "persistent_joint_cause": 265,
    "transient_perfect_storm": 250,
}
ARM_AXES = ("status_quo", *REMOVAL_AXES)


@dataclass(frozen=True)
class FactorialFamilyPlan:
    family_id: str
    sources: tuple[RehearsalSource, ...]
    intervention_rows: tuple[dict[str, str], ...]

    def expected_rows(self, replicates: int) -> int:
        return len(self.sources) * len(self.intervention_rows) * replicates

    def expected_simulations(self, replicates: int) -> int:
        return len(self.sources) * len(ARM_AXES) * replicates


@dataclass(frozen=True)
class FactorialExtensionPlan:
    replicates: int
    families: tuple[FactorialFamilyPlan, ...]
    required_artifacts: tuple[ParameterArtifact, ...]

    @property
    def sources(self) -> tuple[RehearsalSource, ...]:
        return tuple(source for family in self.families for source in family.sources)

    @property
    def source_count_by_family(self) -> dict[str, int]:
        return {family.family_id: len(family.sources) for family in self.families}

    @property
    def source_count(self) -> int:
        return len(self.sources)

    @property
    def source_context_count(self) -> int:
        return len({source.context_key for source in self.sources})

    @property
    def expected_source_replicate_blocks(self) -> int:
        return self.source_count * self.replicates

    @property
    def expected_source_intervention_units(self) -> int:
        return self.source_count * len(REMOVAL_AXES)

    @property
    def expected_row_count(self) -> int:
        return sum(family.expected_rows(self.replicates) for family in self.families)

    @property
    def expected_simulation_count(self) -> int:
        return sum(
            family.expected_simulations(self.replicates) for family in self.families
        )

    @property
    def expected_family_row_counts(self) -> dict[str, int]:
        return {
            family.family_id: family.expected_rows(self.replicates)
            for family in self.families
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "replicates": self.replicates,
            "arm_axes": list(ARM_AXES),
            "stored_contrast_axes": list(REMOVAL_AXES),
            "source_count": self.source_count,
            "source_count_by_family": self.source_count_by_family,
            "source_context_count": self.source_context_count,
            "expected_source_replicate_blocks": self.expected_source_replicate_blocks,
            "expected_source_intervention_units": self.expected_source_intervention_units,
            "expected_row_count": self.expected_row_count,
            "expected_simulation_count": self.expected_simulation_count,
            "expected_family_row_counts": self.expected_family_row_counts,
            "required_artifacts": [
                artifact.to_dict() for artifact in self.required_artifacts
            ],
        }


def derive_factorial_block_seed(
    proposal_source_key: str,
    replicate_id: int,
    *,
    base_label: str = FACTORIAL_EXTENSION_SEED_BASE_LABEL,
) -> int:
    if not proposal_source_key.strip():
        raise ValueError("proposal_source_key must be non-empty")
    if replicate_id < 0:
        raise ValueError("replicate_id must be >= 0")
    payload = f"{base_label}|{proposal_source_key}|{replicate_id}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (
        (1 << 63) - 1
    )


def _required_artifacts(
    sources: tuple[RehearsalSource, ...],
    manifest_rows: list[dict[str, str]],
) -> tuple[ParameterArtifact, ...]:
    contexts = {source.context_key for source in sources}
    rows_by_context: dict[tuple[str, str, str, str], list[dict[str, str]]] = {}
    for row in manifest_rows:
        if row["file_role"] != "parameter_values":
            continue
        context = (
            row["run_id"],
            row["variant_id"],
            str(row["seed"]),
            row["run_dir_name"],
        )
        rows_by_context.setdefault(context, []).append(row)

    missing = sorted(contexts - set(rows_by_context))
    if missing:
        raise ValueError(f"Missing parameter_values manifest contexts: {missing}")
    artifacts: list[ParameterArtifact] = []
    for context in sorted(contexts):
        rows = rows_by_context[context]
        if len(rows) != 1:
            raise ValueError(
                f"Expected one parameter_values row for {context}, found {len(rows)}"
            )
        artifacts.append(_artifact_from_manifest(rows[0]))
    return tuple(artifacts)


def build_factorial_extension_plan(
    proposal_membership_path: Path = DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
    interventions_path: Path = DEFAULT_INTERVENTIONS_PATH,
    module4_manifest_path: Path = DEFAULT_MODULE4_MANIFEST_PATH,
    *,
    replicates: int = DEFAULT_FACTORIAL_EXTENSION_REPLICATES,
) -> FactorialExtensionPlan:
    if replicates < 1:
        raise ValueError("replicates must be >= 1")
    membership_rows, _ = _read_csv_rows(proposal_membership_path)
    manifest_rows, _ = _read_csv_rows(module4_manifest_path)
    intervention_rows = read_intervention_rows(interventions_path)

    families: list[FactorialFamilyPlan] = []
    for family_id in FACTORIAL_FAMILIES:
        sources = _select_sources(
            membership_rows,
            family_id=family_id,
            source_set="accepted",
        )
        rows_by_axis = {
            row["intervention_axis"]: row
            for row in intervention_rows
            if row["family_id"] == family_id
            and row["intervention_axis"] in ARM_AXES
        }
        missing_axes = sorted(set(ARM_AXES) - set(rows_by_axis))
        if missing_axes:
            raise ValueError(f"{family_id} missing factorial axes: {missing_axes}")
        selected_rows = tuple(rows_by_axis[axis] for axis in REMOVAL_AXES)
        families.append(
            FactorialFamilyPlan(
                family_id=family_id,
                sources=sources,
                intervention_rows=selected_rows,
            )
        )

    all_sources = tuple(source for family in families for source in family.sources)
    plan = FactorialExtensionPlan(
        replicates=replicates,
        families=tuple(families),
        required_artifacts=_required_artifacts(all_sources, manifest_rows),
    )
    if plan.source_count_by_family != FACTORIAL_EXTENSION_SOURCE_COUNTS:
        raise ValueError(
            "Accepted factorial source counts changed: "
            f"{plan.source_count_by_family} != {FACTORIAL_EXTENSION_SOURCE_COUNTS}"
        )
    if plan.source_context_count != 15 or len(plan.required_artifacts) != 15:
        raise ValueError(
            "Expected 15 source contexts and parameter artifacts, found "
            f"{plan.source_context_count} and {len(plan.required_artifacts)}"
        )
    return plan


def _run_four_arm_block(
    params: ResolvedParameters,
    family_id: str,
    config: SimulationConfig,
    intervention_rows: tuple[dict[str, str], ...],
    *,
    seed: int,
) -> dict[str, SimulationResult]:
    results = {
        "status_quo": run_historical_simulation(params, family_id, config, seed=seed)
    }
    for row in intervention_rows:
        axis = row["intervention_axis"]
        intervention_params = apply_module5_intervention_overrides(params, axis)
        results[axis] = run_historical_simulation(
            intervention_params,
            family_id,
            config,
            seed=seed,
        )
    return results


def _build_tasks(
    plan: FactorialExtensionPlan,
    verified_artifacts: tuple[VerifiedArtifact, ...],
    *,
    data_dir: Path,
    interventions_path: Path,
    module4_manifest_path: Path,
    stochastic: bool,
    timestamp: str,
    git_sha: str,
) -> list[dict[str, object]]:
    verified_by_context = {
        artifact.context_key: artifact for artifact in verified_artifacts
    }
    tasks: list[dict[str, object]] = []
    for task_index, (family, source) in enumerate(
        (family, source) for family in plan.families for source in family.sources
    ):
        artifact = verified_by_context[source.context_key]
        tasks.append(
            {
                "task_index": task_index,
                "source": source.to_dict(),
                "intervention_rows": list(family.intervention_rows),
                "replicates": plan.replicates,
                "artifact_path": artifact.path.as_posix(),
                "data_dir": data_dir.as_posix(),
                "interventions_path": interventions_path.as_posix(),
                "module4_manifest_path": module4_manifest_path.as_posix(),
                "stochastic": stochastic,
                "timestamp": timestamp,
                "git_sha": git_sha,
            }
        )
    return tasks


def _run_task(task: dict[str, object]) -> tuple[int, list[dict[str, object]]]:
    source = _source_from_dict(task["source"])  # type: ignore[arg-type]
    intervention_rows = tuple(
        {str(key): str(value) for key, value in dict(row).items()}
        for row in task["intervention_rows"]  # type: ignore[union-attr]
    )
    model_inputs = load_model_inputs(Path(str(task["data_dir"])))
    parameter_values = load_parameter_values_table(Path(str(task["artifact_path"])))
    params = resolve_proposal_parameters(
        model_inputs,
        source.to_selected_proposal(),
        parameter_values,
    )
    config = SimulationConfig(stochastic=bool(task["stochastic"]))
    rows: list[dict[str, object]] = []
    for replicate_id in range(int(task["replicates"])):
        stochastic_seed = derive_factorial_block_seed(
            source.proposal_source_key,
            replicate_id,
        )
        results = _run_four_arm_block(
            params,
            source.family_id,
            config,
            intervention_rows,
            seed=stochastic_seed,
        )
        for intervention in intervention_rows:
            rows.append(
                _build_output_row(
                    intervention,
                    results["status_quo"],
                    results[intervention["intervention_axis"]],
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
                    provenance_script=DEFAULT_FACTORIAL_EXTENSION_SCRIPT_PATH,
                    module4_manifest=Path(str(task["module4_manifest_path"])),
                    provenance_git_sha=str(task["git_sha"]),
                )
            )
    return int(task["task_index"]), rows


def _run_tasks(
    tasks: list[dict[str, object]],
    *,
    workers: int,
) -> list[dict[str, object]]:
    ordered: dict[int, list[dict[str, object]]] = {}
    total = len(tasks)
    if workers == 1:
        for position, task in enumerate(tasks, start=1):
            task_index, rows = _run_task(task)
            ordered[task_index] = rows
            if position % 50 == 0 or position == total:
                print(f"completed_tasks={position}/{total}", flush=True)
    else:
        max_workers = min(workers, os.cpu_count() or workers)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_run_task, task) for task in tasks]
            for position, future in enumerate(as_completed(futures), start=1):
                task_index, rows = future.result()
                ordered[task_index] = rows
                if position % 50 == 0 or position == total:
                    print(f"completed_tasks={position}/{total}", flush=True)
    return [row for task_index in sorted(ordered) for row in ordered[task_index]]


def _seed_facts(plan: FactorialExtensionPlan) -> dict[str, int]:
    seeds = [
        derive_factorial_block_seed(source.proposal_source_key, replicate_id)
        for source in plan.sources
        for replicate_id in range(plan.replicates)
    ]
    return {
        "source_replicate_block_count": len(seeds),
        "distinct_seed_count": len(set(seeds)),
        "collision_excess_count": len(seeds) - len(set(seeds)),
        "minimum_seed": min(seeds),
        "maximum_seed": max(seeds),
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_preflight(
    output_dir: Path,
    plan: FactorialExtensionPlan,
    verified_artifacts: tuple[VerifiedArtifact, ...],
) -> None:
    _write_json(output_dir / "execution_plan.json", plan.to_dict())
    pd.DataFrame([artifact.to_dict() for artifact in verified_artifacts]).to_csv(
        output_dir / "artifact_verification.csv",
        index=False,
    )


def _write_provenance(
    output_dir: Path,
    output_file: Path,
    *,
    run_id: str,
    plan: FactorialExtensionPlan,
    verified_artifacts: tuple[VerifiedArtifact, ...],
    proposal_membership_path: Path,
    module4_manifest_path: Path,
    interventions_path: Path,
    outcome_schema_path: Path,
    stochastic: bool,
    workers: int,
    git_sha: str,
) -> None:
    payload = {
        "module": "Module 5 shared four-arm factorial extension",
        "status": FACTORIAL_EXTENSION_STATUS,
        "production_attribution": False,
        "run_id": run_id,
        "output_file": _relative_path(output_file),
        "output_dir": _relative_path(output_dir),
        "script_path": DEFAULT_FACTORIAL_EXTENSION_SCRIPT_PATH.as_posix(),
        "proposal_membership_path": _relative_path(proposal_membership_path),
        "module4_manifest_path": _relative_path(module4_manifest_path),
        "interventions_path": _relative_path(interventions_path),
        "outcome_schema_path": _relative_path(outcome_schema_path),
        "expected_replicates": plan.replicates,
        "expected_row_count": plan.expected_row_count,
        "expected_simulation_count": plan.expected_simulation_count,
        "expected_source_replicate_blocks": plan.expected_source_replicate_blocks,
        "expected_source_intervention_units": plan.expected_source_intervention_units,
        "expected_distinct_proposal_source_keys": plan.source_count,
        "expected_family_row_counts": plan.expected_family_row_counts,
        "source_count_by_family": plan.source_count_by_family,
        "source_context_count": plan.source_context_count,
        "selected_proposal_source_keys": [
            source.proposal_source_key for source in plan.sources
        ],
        "source_identity_fields": list(PROPOSAL_SOURCE_KEY_FIELDS),
        "source_identity_strategy": (
            "proposal_source_key=module4_run_id|variant_id|seed|run_dir_name|"
            "family_id|proposal_id"
        ),
        "arm_axes": list(ARM_AXES),
        "stored_contrast_axes": list(REMOVAL_AXES),
        "status_quo_executed_once_per_block": True,
        "seed_derivation": (
            "int.from_bytes(sha256(base_label|proposal_source_key|"
            "stochastic_replicate_id)[:8]) & ((1 << 63) - 1)"
        ),
        "seed_base_label": FACTORIAL_EXTENSION_SEED_BASE_LABEL,
        "common_seed_boundary": (
            "All four arms start from the same seed; state-dependent draws may "
            "consume the stream differently after trajectories diverge."
        ),
        "seed_facts": _seed_facts(plan),
        "artifact_verification": [
            artifact.to_dict() for artifact in verified_artifacts
        ],
        "artifact_verification_count": len(verified_artifacts),
        "git_sha": git_sha,
        "git_status_short": _git_status_short(),
        "python_version": sys.version.split()[0],
        "compute_host": platform.node(),
        "stochastic": stochastic,
        "workers": workers,
        "matched_outcomes_sha256": _file_sha256(output_file),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "boundary_note": (
            "This is a conditional Monte Carlo extension, not production "
            "attribution or manuscript evidence."
        ),
    }
    _write_json(output_dir / "provenance.json", payload)


def run_module5_factorial_extension(
    *,
    data_dir: Path,
    proposal_membership_path: Path = DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
    module4_manifest_path: Path = DEFAULT_MODULE4_MANIFEST_PATH,
    interventions_path: Path = DEFAULT_INTERVENTIONS_PATH,
    outcome_schema_path: Path = DEFAULT_OUTCOME_SCHEMA_PATH,
    output_dir: Path = DEFAULT_FACTORIAL_EXTENSION_OUTPUT_DIR,
    run_id: str = "local-module5-factorial-extension",
    replicates: int = DEFAULT_FACTORIAL_EXTENSION_REPLICATES,
    stochastic: bool = True,
    path_preference: str = "auto",
    plan_only: bool = False,
    overwrite: bool = False,
    workers: int = 1,
) -> Path:
    if workers < 1:
        raise ValueError("workers must be >= 1")
    data_dir = data_dir.resolve()
    proposal_membership_path = proposal_membership_path.resolve()
    module4_manifest_path = module4_manifest_path.resolve()
    interventions_path = interventions_path.resolve()
    outcome_schema_path = outcome_schema_path.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "matched_outcomes.csv"
    if output_file.exists() and not overwrite and not plan_only:
        raise FileExistsError(
            f"Refusing to overwrite existing factorial output: {output_file}"
        )

    plan = build_factorial_extension_plan(
        proposal_membership_path,
        interventions_path,
        module4_manifest_path,
        replicates=replicates,
    )
    verified_artifacts = verify_required_parameter_artifacts(
        plan.required_artifacts,
        root=Path.cwd(),
        path_preference=path_preference,
    )
    _write_preflight(output_dir, plan, verified_artifacts)
    if plan_only:
        return output_dir / "execution_plan.json"

    git_sha = _git_sha()
    tasks = _build_tasks(
        plan,
        verified_artifacts,
        data_dir=data_dir,
        interventions_path=interventions_path,
        module4_manifest_path=module4_manifest_path,
        stochastic=stochastic,
        timestamp=datetime.now(timezone.utc).isoformat(),
        git_sha=git_sha,
    )
    output_rows = _attach_uncertainty_summaries(_run_tasks(tasks, workers=workers))
    schema_columns = read_outcome_schema_columns(outcome_schema_path)
    pd.DataFrame(output_rows).loc[:, schema_columns].to_csv(output_file, index=False)
    _write_provenance(
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
        git_sha=git_sha,
    )
    return output_file
