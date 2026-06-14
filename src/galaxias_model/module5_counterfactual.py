from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from galaxias_model.io import load_model_inputs, resolve_family_parameters
from galaxias_model.module5_proposals import (
    DEFAULT_DRY_RUN_OUTPUT_DIR,
    DEFAULT_DRY_RUN_REPLICATES,
    DEFAULT_DRY_RUN_SEED_BASE_LABEL,
    DEFAULT_MODULE4_MANIFEST_PATH,
    DEFAULT_PARAMETER_VALUES_PATH,
    DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
    PROPOSAL_SOURCE_KEY_FIELDS,
    SelectedProposal,
    build_proposal_source_key,
    derive_module5_seed,
    load_parameter_values_table,
    load_selected_dry_run_proposals,
    proposals_by_family,
    resolve_proposal_parameters,
    verify_parameter_values_artifact,
)
from galaxias_model.simulation import run_historical_simulation
from galaxias_model.types import ResolvedParameters, SimulationConfig, SimulationResult


DEFAULT_INTERVENTIONS_PATH = Path("data/module5_counterfactual_interventions.csv")
DEFAULT_OUTCOME_SCHEMA_PATH = Path("data/module5_counterfactual_outcome_schema.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/module5_runner_smoke")
DEFAULT_MODULE4_MANIFEST = Path("data/module4_raw_artifact_manifest.csv")
DEFAULT_SCRIPT_PATH = Path("scripts/run_module5_counterfactual_smoke.py")
DEFAULT_REAL_DRY_RUN_SCRIPT_PATH = Path("scripts/run_module5_real_proposal_dry_run.py")
REAL_DRY_RUN_STATUS = "real_proposal_local_dry_run"

TROUT_PRESSURE_PARAMETER_IDS = ("PR020", "PR021")
CLIMBING_PRESSURE_PARAMETER_IDS = ("PR027", "PR028")


def apply_module5_intervention_overrides(
    params: ResolvedParameters,
    intervention_axis: str,
) -> ResolvedParameters:
    values = dict(params.values)

    if intervention_axis == "status_quo":
        return params
    if intervention_axis == "no_trout_pressure":
        null_parameter_ids = TROUT_PRESSURE_PARAMETER_IDS
    elif intervention_axis == "no_climbing_pressure":
        null_parameter_ids = CLIMBING_PRESSURE_PARAMETER_IDS
    elif intervention_axis == "no_trout_or_climbing_pressure":
        null_parameter_ids = TROUT_PRESSURE_PARAMETER_IDS + CLIMBING_PRESSURE_PARAMETER_IDS
    else:
        raise ValueError(f"Unsupported Module 5 intervention_axis: {intervention_axis}")

    for parameter_id in null_parameter_ids:
        values[parameter_id] = 0.0

    manifest = params.manifest.copy()
    manifest.loc[manifest["parameter_id"].isin(null_parameter_ids), "effective_value"] = 0.0
    return replace(params, values=values, manifest=manifest)


def read_intervention_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_outcome_schema_columns(path: Path) -> list[str]:
    frame = pd.read_csv(path)
    return frame["column_name"].astype(str).tolist()


def _relative_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_status_short() -> str:
    try:
        return subprocess.check_output(
            ["git", "status", "--short", "--branch"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _first_absent_year(result: SimulationResult) -> float:
    trajectory = result.trajectory_table
    absent = trajectory.loc[trajectory["total_present"] == 0, "year"]
    if not absent.empty:
        return float(absent.iloc[0])
    return float(int(trajectory["year"].max()) + 1)


def _value_at_year(trajectory: pd.DataFrame, year: int, column: str) -> float:
    value = trajectory.loc[trajectory["year"] == year, column]
    if value.empty:
        return float("nan")
    return float(value.iloc[0])


def _lake_share_2002(result: SimulationResult) -> float:
    trajectory = result.trajectory_table
    total = _value_at_year(trajectory, 2002, "N_total")
    if total <= 0 or math.isnan(total):
        return 0.0
    return _value_at_year(trajectory, 2002, "N_L") / total


def _window_min_total(result: SimulationResult) -> float:
    window = result.trajectory_table.loc[result.trajectory_table["year"].between(1992, 2002), "N_total"]
    return float(window.min()) if not window.empty else float("nan")


def _terminal_persistence(result: SimulationResult, year: int) -> int:
    return int(_value_at_year(result.trajectory_table, year, "total_present") > 0)


def _detection_proxy(result: SimulationResult) -> float:
    # Smoke-only proxy: keeps the endpoint column populated without invoking a
    # production observation projection or changing observation-model defaults.
    return _value_at_year(result.trajectory_table, 2002, "N_total") * 0.01


def _pressure_summaries(result: SimulationResult) -> tuple[float, float]:
    forcing = result.forcing_table
    window = forcing.loc[forcing["year"].between(1992, 2002)]
    trout = (window["T"].astype(float) * window["P"].astype(float)).sum()
    climbing = (window["C_L"].astype(float) + window["C_R"].astype(float)).sum()
    return float(trout), float(climbing)


def _run_matched_pair(
    row: dict[str, str],
    baseline_params: ResolvedParameters,
    config: SimulationConfig,
    seed: int,
) -> tuple[SimulationResult, SimulationResult]:
    intervention_params = apply_module5_intervention_overrides(
        baseline_params,
        row["intervention_axis"],
    )
    baseline = run_historical_simulation(baseline_params, row["family_id"], config, seed=seed)
    intervention = run_historical_simulation(intervention_params, row["family_id"], config, seed=seed)
    return baseline, intervention


def _build_output_row(
    row: dict[str, str],
    baseline: SimulationResult,
    intervention: SimulationResult,
    replicate_id: int,
    proposal_seed: int,
    stochastic_seed: int,
    timestamp: str,
    interventions_path: Path,
    *,
    proposal_id: str | None = None,
    variant_id: str = "module5_smoke_default_parameters",
    source_seed: int | None = None,
    proposal_source_key: str | None = None,
    module4_run_id: str = "module5_smoke_default_parameters",
    run_dir_name: str = "module5_smoke_default_parameters",
    provenance_script: Path = DEFAULT_SCRIPT_PATH,
    module4_manifest: Path = DEFAULT_MODULE4_MANIFEST,
) -> dict[str, object]:
    family_id = row["family_id"]
    intervention_id = row["intervention_id"]
    proposal_id = proposal_id or f"smoke_default:{family_id}"
    seed_value = source_seed if source_seed is not None else proposal_seed
    proposal_source_key = proposal_source_key or build_proposal_source_key(
        module4_run_id=module4_run_id,
        variant_id=variant_id,
        seed=seed_value,
        run_dir_name=run_dir_name,
        family_id=family_id,
        proposal_id=proposal_id,
    )
    matched_pair_id = f"{proposal_source_key}|{intervention_id}|r{replicate_id}"
    baseline_extirpation = _first_absent_year(baseline)
    intervention_extirpation = _first_absent_year(intervention)
    baseline_persistence_2002 = _terminal_persistence(baseline, 2002)
    intervention_persistence_2002 = _terminal_persistence(intervention, 2002)
    baseline_persistence_1996 = _terminal_persistence(baseline, 1996)
    intervention_persistence_1996 = _terminal_persistence(intervention, 1996)
    baseline_min = _window_min_total(baseline)
    intervention_min = _window_min_total(intervention)
    baseline_share = _lake_share_2002(baseline)
    intervention_share = _lake_share_2002(intervention)
    baseline_detection = _detection_proxy(baseline)
    intervention_detection = _detection_proxy(intervention)
    trout_pressure, climbing_pressure = _pressure_summaries(intervention)

    return {
        "family_id": family_id,
        "family_role": row["module5_role"],
        "proposal_id": proposal_id,
        "proposal_source_key": proposal_source_key,
        "module4_run_id": module4_run_id,
        "variant_id": variant_id,
        "seed": seed_value,
        "run_dir_name": run_dir_name,
        "proposal_seed": proposal_seed,
        "stochastic_replicate_id": replicate_id,
        "intervention_id": intervention_id,
        "intervention_axis": row["intervention_axis"],
        "scenario_class": row["scenario_class"],
        "matched_pair_id": matched_pair_id,
        "run_id_baseline": f"{matched_pair_id}|baseline",
        "run_id_counterfactual": f"{matched_pair_id}|counterfactual",
        "baseline_stochastic_seed": stochastic_seed,
        "intervention_stochastic_seed": stochastic_seed,
        "year": 2002,
        "N_total": _value_at_year(intervention.trajectory_table, 2002, "N_total"),
        "N_lake": _value_at_year(intervention.trajectory_table, 2002, "N_L"),
        "N_refuge": _value_at_year(intervention.trajectory_table, 2002, "N_R"),
        "trout_pressure_legacy_index": trout_pressure,
        "climbing_pressure_legacy_index": climbing_pressure,
        "extirpation_year_raw": intervention_extirpation,
        "extirpation_year_contrast": intervention_extirpation - baseline_extirpation,
        "persistence_2002_baseline": baseline_persistence_2002,
        "persistence_2002_counterfactual": intervention_persistence_2002,
        "persistence_2002_contrast": intervention_persistence_2002 - baseline_persistence_2002,
        "persistence_1996_baseline": baseline_persistence_1996,
        "persistence_1996_counterfactual": intervention_persistence_1996,
        "persistence_1996_contrast": intervention_persistence_1996 - baseline_persistence_1996,
        "min_abundance_1992_2002_baseline": baseline_min,
        "min_abundance_1992_2002_counterfactual": intervention_min,
        "min_abundance_1992_2002_contrast": intervention_min - baseline_min,
        "lake_refuge_share_2002_baseline": baseline_share,
        "lake_refuge_share_2002_counterfactual": intervention_share,
        "lake_refuge_share_2002_contrast": intervention_share - baseline_share,
        "detection_summary_baseline": baseline_detection,
        "detection_summary_counterfactual": intervention_detection,
        "detection_summary_contrast": intervention_detection - baseline_detection,
        "uncertainty_n_replicates": 0,
        "uncertainty_extirpation_median": 0.0,
        "uncertainty_extirpation_ci_low": 0.0,
        "uncertainty_extirpation_ci_high": 0.0,
        "uncertainty_persistence_2002_delta_median": 0.0,
        "uncertainty_persistence_2002_ci_low": 0.0,
        "uncertainty_persistence_2002_ci_high": 0.0,
        "processing_timestamp": timestamp,
        "provenance_source_file": _relative_path(interventions_path),
        "provenance_git_sha": _git_sha(),
        "provenance_script": provenance_script.as_posix(),
        "provenance_module4_manifest": module4_manifest.as_posix(),
    }


def _attach_uncertainty_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    frame = pd.DataFrame(rows)
    group_columns = (
        ["proposal_source_key", "intervention_id"]
        if "proposal_source_key" in frame.columns
        else ["intervention_id"]
    )
    for group_key, group in frame.groupby(group_columns, sort=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        mask = pd.Series(True, index=frame.index)
        for column, value in zip(group_columns, group_key):
            mask &= frame[column] == value
        extirpation = group["extirpation_year_contrast"].astype(float)
        persistence = group["persistence_2002_contrast"].astype(float)
        frame.loc[mask, "uncertainty_n_replicates"] = len(group)
        frame.loc[mask, "uncertainty_extirpation_median"] = float(extirpation.median())
        frame.loc[mask, "uncertainty_extirpation_ci_low"] = float(np.quantile(extirpation, 0.025))
        frame.loc[mask, "uncertainty_extirpation_ci_high"] = float(np.quantile(extirpation, 0.975))
        frame.loc[mask, "uncertainty_persistence_2002_delta_median"] = float(persistence.median())
        frame.loc[mask, "uncertainty_persistence_2002_ci_low"] = float(np.quantile(persistence, 0.025))
        frame.loc[mask, "uncertainty_persistence_2002_ci_high"] = float(np.quantile(persistence, 0.975))
    return frame.to_dict(orient="records")


def _write_provenance(
    output_dir: Path,
    output_file: Path,
    interventions_path: Path,
    outcome_schema_path: Path,
    intervention_ids: Iterable[str],
    replicates: int,
    proposal_seed: int,
    stochastic: bool,
) -> None:
    payload = {
        "module": "Module 5 counterfactual runner prototype",
        "status": "tiny_local_smoke_only",
        "production_attribution": False,
        "output_file": _relative_path(output_file),
        "interventions_path": _relative_path(interventions_path),
        "outcome_schema_path": _relative_path(outcome_schema_path),
        "intervention_ids": list(intervention_ids),
        "replicates": replicates,
        "proposal_seed": proposal_seed,
        "stochastic": stochastic,
        "source_identity_fields": list(PROPOSAL_SOURCE_KEY_FIELDS),
        "source_identity_strategy": (
            "proposal_source_key=module4_run_id|variant_id|seed|run_dir_name|family_id|proposal_id"
        ),
        "git_sha": _git_sha(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "boundary_note": (
            "Default-parameter smoke rows validate runner wiring only; they are not "
            "production attribution results or manuscript evidence."
        ),
    }
    (output_dir / "provenance.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_module5_counterfactual_smoke(
    data_dir: Path,
    interventions_path: Path,
    outcome_schema_path: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    intervention_ids: tuple[str, ...] = (),
    replicates: int = 2,
    proposal_seed: int = 20260605,
    stochastic: bool = True,
) -> Path:
    if replicates < 1:
        raise ValueError("replicates must be >= 1")

    model_inputs = load_model_inputs(data_dir)
    interventions_path = interventions_path.resolve()
    outcome_schema_path = outcome_schema_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    all_rows = read_intervention_rows(interventions_path)
    wanted = set(intervention_ids)
    selected = [row for row in all_rows if not wanted or row["intervention_id"] in wanted]
    if wanted:
        found = {row["intervention_id"] for row in selected}
        missing = sorted(wanted - found)
        if missing:
            raise ValueError(f"Unknown intervention_id values: {missing}")
    if not selected:
        raise ValueError("No intervention rows selected for Module 5 smoke run")

    config = SimulationConfig(stochastic=stochastic)
    timestamp = datetime.now(timezone.utc).isoformat()
    output_rows: list[dict[str, object]] = []
    for row in selected:
        params = resolve_family_parameters(model_inputs, row["family_id"])
        for replicate_id in range(replicates):
            stochastic_seed = proposal_seed + replicate_id
            baseline, intervention = _run_matched_pair(row, params, config, seed=stochastic_seed)
            output_rows.append(
                _build_output_row(
                    row,
                    baseline,
                    intervention,
                    replicate_id,
                    proposal_seed,
                    stochastic_seed,
                    timestamp,
                    interventions_path,
                )
            )

    output_rows = _attach_uncertainty_summaries(output_rows)
    schema_columns = read_outcome_schema_columns(outcome_schema_path)
    output_file = output_dir / "matched_outcomes.csv"
    pd.DataFrame(output_rows).loc[:, schema_columns].to_csv(output_file, index=False)
    _write_provenance(
        output_dir=output_dir,
        output_file=output_file,
        interventions_path=interventions_path,
        outcome_schema_path=outcome_schema_path,
        intervention_ids=[row["intervention_id"] for row in selected],
        replicates=replicates,
        proposal_seed=proposal_seed,
        stochastic=stochastic,
    )
    return output_file


def _write_real_proposal_provenance(
    output_dir: Path,
    output_file: Path,
    proposal_membership_path: Path,
    module4_manifest_path: Path,
    parameter_values_path: Path,
    parameter_values_sha256: str,
    interventions_path: Path,
    outcome_schema_path: Path,
    selected_proposals: Iterable[SelectedProposal],
    intervention_ids: Iterable[str],
    replicates: int,
    stochastic: bool,
) -> None:
    selected = tuple(selected_proposals)
    payload = {
        "module": "Module 5 real-proposal dry run",
        "status": REAL_DRY_RUN_STATUS,
        "production_attribution": False,
        "output_file": _relative_path(output_file),
        "output_dir": _relative_path(output_dir),
        "script_path": DEFAULT_REAL_DRY_RUN_SCRIPT_PATH.as_posix(),
        "selected_proposal_ids": [proposal.proposal_id for proposal in selected],
        "selected_proposal_source_keys": [proposal.proposal_source_key for proposal in selected],
        "source_identity_fields": list(PROPOSAL_SOURCE_KEY_FIELDS),
        "source_identity_strategy": (
            "proposal_source_key=module4_run_id|variant_id|seed|run_dir_name|family_id|proposal_id"
        ),
        "selected_proposal_source_rows": [
            {
                "proposal_source_key": proposal.proposal_source_key,
                "module4_run_id": proposal.module4_run_id,
                "variant_id": proposal.variant_id,
                "seed": proposal.seed,
                "run_dir_name": proposal.run_dir_name,
                "family_id": proposal.family_id,
                "proposal_id": proposal.proposal_id,
            }
            for proposal in selected
        ],
        "proposal_source_filter": {
            "proposal_set": "family_winners",
            "variant_id": "baseline_current",
            "seed": 20260410,
        },
        "intervention_ids": list(intervention_ids),
        "interventions_path": _relative_path(interventions_path),
        "outcome_schema_path": _relative_path(outcome_schema_path),
        "proposal_membership_path": _relative_path(proposal_membership_path),
        "module4_manifest_path": _relative_path(module4_manifest_path),
        "parameter_values_path": _relative_path(parameter_values_path),
        "parameter_values_sha256": parameter_values_sha256,
        "git_sha": _git_sha(),
        "git_status_short": _git_status_short(),
        "python_version": sys.version.split()[0],
        "compute_host": platform.node(),
        "replicates": replicates,
        "stochastic": stochastic,
        "seed_derivation": "sha256(base_label|proposal_source_key|intervention_id|stochastic_replicate_id) modulo 2**32",
        "seed_base_label": DEFAULT_DRY_RUN_SEED_BASE_LABEL,
        "matched_outcomes_sha256": _file_sha256(output_file),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "boundary_note": (
            "Real-proposal local dry-run rows validate Module 5 plumbing only; "
            "they are not production attribution results and not manuscript evidence."
        ),
    }
    (output_dir / "provenance.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_module5_real_proposal_dry_run(
    data_dir: Path,
    proposal_membership_path: Path = DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
    module4_manifest_path: Path = DEFAULT_MODULE4_MANIFEST_PATH,
    parameter_values_path: Path = DEFAULT_PARAMETER_VALUES_PATH,
    interventions_path: Path = DEFAULT_INTERVENTIONS_PATH,
    outcome_schema_path: Path = DEFAULT_OUTCOME_SCHEMA_PATH,
    output_dir: Path = DEFAULT_DRY_RUN_OUTPUT_DIR,
    replicates: int = DEFAULT_DRY_RUN_REPLICATES,
    stochastic: bool = True,
) -> Path:
    if replicates < 1:
        raise ValueError("replicates must be >= 1")

    model_inputs = load_model_inputs(data_dir)
    proposal_membership_path = proposal_membership_path.resolve()
    module4_manifest_path = module4_manifest_path.resolve()
    parameter_values_path = parameter_values_path.resolve()
    interventions_path = interventions_path.resolve()
    outcome_schema_path = outcome_schema_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    proposals = load_selected_dry_run_proposals(proposal_membership_path)
    proposals_for_family = proposals_by_family(proposals)
    artifact = verify_parameter_values_artifact(module4_manifest_path, parameter_values_path)
    parameter_values = load_parameter_values_table(artifact.path)
    resolved_by_family = {
        family_id: resolve_proposal_parameters(model_inputs, proposal, parameter_values)
        for family_id, proposal in proposals_for_family.items()
    }

    all_rows = read_intervention_rows(interventions_path)
    selected_intervention_ids = [row["intervention_id"] for row in all_rows]
    config = SimulationConfig(stochastic=stochastic)
    timestamp = datetime.now(timezone.utc).isoformat()
    output_rows: list[dict[str, object]] = []

    for row in all_rows:
        family_id = row["family_id"]
        if family_id not in proposals_for_family:
            raise ValueError(f"No selected dry-run proposal for intervention family {family_id}")
        proposal = proposals_for_family[family_id]
        params = resolved_by_family[family_id]
        for replicate_id in range(replicates):
            stochastic_seed = derive_module5_seed(
                proposal.proposal_source_key,
                row["intervention_id"],
                replicate_id,
            )
            baseline, intervention = _run_matched_pair(row, params, config, seed=stochastic_seed)
            output_rows.append(
                _build_output_row(
                    row,
                    baseline,
                    intervention,
                    replicate_id,
                    proposal.proposal_seed,
                    stochastic_seed,
                    timestamp,
                    interventions_path,
                    proposal_id=proposal.proposal_id,
                    variant_id=proposal.variant_id,
                    source_seed=proposal.seed,
                    proposal_source_key=proposal.proposal_source_key,
                    module4_run_id=proposal.module4_run_id,
                    run_dir_name=proposal.run_dir_name,
                    provenance_script=DEFAULT_REAL_DRY_RUN_SCRIPT_PATH,
                    module4_manifest=module4_manifest_path,
                )
            )

    output_rows = _attach_uncertainty_summaries(output_rows)
    schema_columns = read_outcome_schema_columns(outcome_schema_path)
    output_file = output_dir / "matched_outcomes.csv"
    pd.DataFrame(output_rows).loc[:, schema_columns].to_csv(output_file, index=False)
    _write_real_proposal_provenance(
        output_dir=output_dir,
        output_file=output_file,
        proposal_membership_path=proposal_membership_path,
        module4_manifest_path=module4_manifest_path,
        parameter_values_path=parameter_values_path,
        parameter_values_sha256=artifact.sha256,
        interventions_path=interventions_path,
        outcome_schema_path=outcome_schema_path,
        selected_proposals=proposals,
        intervention_ids=selected_intervention_ids,
        replicates=replicates,
        stochastic=stochastic,
    )
    return output_file
