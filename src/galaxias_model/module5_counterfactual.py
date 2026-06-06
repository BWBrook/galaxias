from __future__ import annotations

import csv
import json
import math
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from galaxias_model.io import load_model_inputs, resolve_family_parameters
from galaxias_model.simulation import run_historical_simulation
from galaxias_model.types import ResolvedParameters, SimulationConfig, SimulationResult


DEFAULT_INTERVENTIONS_PATH = Path("data/module5_counterfactual_interventions.csv")
DEFAULT_OUTCOME_SCHEMA_PATH = Path("data/module5_counterfactual_outcome_schema.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/module5_runner_smoke")
DEFAULT_MODULE4_MANIFEST = Path("data/module4_raw_artifact_manifest.csv")
DEFAULT_SCRIPT_PATH = Path("scripts/run_module5_counterfactual_smoke.py")

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
) -> dict[str, object]:
    family_id = row["family_id"]
    intervention_id = row["intervention_id"]
    proposal_id = f"smoke_default:{family_id}"
    matched_pair_id = f"{proposal_id}:{intervention_id}:r{replicate_id}"
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
        "variant_id": "module5_smoke_default_parameters",
        "seed": proposal_seed,
        "proposal_seed": proposal_seed,
        "stochastic_replicate_id": replicate_id,
        "intervention_id": intervention_id,
        "intervention_axis": row["intervention_axis"],
        "scenario_class": row["scenario_class"],
        "matched_pair_id": matched_pair_id,
        "run_id_baseline": f"{matched_pair_id}:baseline",
        "run_id_counterfactual": f"{matched_pair_id}:intervention",
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
        "provenance_script": DEFAULT_SCRIPT_PATH.as_posix(),
        "provenance_module4_manifest": DEFAULT_MODULE4_MANIFEST.as_posix(),
    }


def _attach_uncertainty_summaries(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    frame = pd.DataFrame(rows)
    for intervention_id, group in frame.groupby("intervention_id", sort=False):
        mask = frame["intervention_id"] == intervention_id
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
