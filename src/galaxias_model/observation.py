from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from galaxias_model.types import ModelInputs, ProjectionResult, SimulationResult


SCENARIO_ID = "historical_lake"


def _window_subset(table: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    return table.loc[table["year"].between(start, end)].copy()


def _details_for(model_inputs: ModelInputs, target_id: str) -> dict[str, Any]:
    if model_inputs.calibration_target_details is None:
        raise ValueError("ModelInputs missing calibration_target_details")
    if target_id not in model_inputs.calibration_target_details:
        raise ValueError(f"Unknown target_id in calibration_target_details: {target_id}")
    return model_inputs.calibration_target_details[target_id]


def _target_row_for(model_inputs: ModelInputs, target_id: str) -> pd.Series:
    if model_inputs.calibration_targets is None:
        raise ValueError("ModelInputs missing calibration_targets")
    matches = model_inputs.calibration_targets.loc[model_inputs.calibration_targets["target_id"] == target_id]
    if matches.empty:
        raise ValueError(f"Unknown target_id in calibration_targets: {target_id}")
    return matches.iloc[0]


def _expected_detected_count(latent_abundance: float, simulation_result: SimulationResult) -> float:
    params = simulation_result.resolved_parameters
    return params.value("PR035") * params.value("PR036") * max(float(latent_abundance), 0.0)


def project_target(target_id: str, simulation_result: SimulationResult, model_inputs: ModelInputs) -> dict[str, Any]:
    target_row = _target_row_for(model_inputs, target_id)
    details = _details_for(model_inputs, target_id)
    trajectory = simulation_result.trajectory_table
    forcing = simulation_result.forcing_table
    summary = simulation_result.summary

    base = {
        "target_id": target_id,
        "target_group": str(target_row["target_group"]),
        "comparison_type": str(target_row["comparison_type"]),
        "scenario_id": SCENARIO_ID,
        "evaluation_status": "scored",
        "projected_primary": np.nan,
        "projected_secondary": np.nan,
        "observed_primary": details["observed_primary"],
        "observed_secondary": details["observed_secondary"],
        "projection_metadata": {},
        "notes": "",
    }

    required_scenario_id = str(details["required_scenario_id"])
    if required_scenario_id != SCENARIO_ID:
        base["evaluation_status"] = "deferred_requires_scenario"
        base["notes"] = f"Requires scenario_id={required_scenario_id}, current kernel only supports historical_lake."
        return base

    if target_id == "CT001":
        window = details["window"]
        subset = _window_subset(trajectory, int(window["start"]), int(window["end"]))
        lake_presence_fraction = float(subset["lake_present"].mean())
        refuge_presence_fraction = float(subset["refuge_present"].mean())
        base["projected_primary"] = lake_presence_fraction
        base["projected_secondary"] = refuge_presence_fraction
        base["projection_metadata"] = {
            "lake_presence_fraction": lake_presence_fraction,
            "refuge_presence_fraction": refuge_presence_fraction,
        }
        return base

    if target_id == "CT002":
        pre = details["pre_window"]
        boom = details["boom_window"]
        late = details["late_window"]
        pre_mean = float(_window_subset(trajectory, int(pre["start"]), int(pre["end"]))["pedder_lake_index"].mean())
        boom_peak = float(_window_subset(trajectory, int(boom["start"]), int(boom["end"]))["pedder_lake_index"].max())
        late_mean = float(_window_subset(trajectory, int(late["start"]), int(late["end"]))["pedder_lake_index"].mean())
        base["projected_primary"] = boom_peak / max(pre_mean, 1e-9)
        base["projected_secondary"] = boom_peak / max(late_mean, 1e-9)
        base["projection_metadata"] = {
            "pre_mean": pre_mean,
            "boom_peak": boom_peak,
            "late_mean": late_mean,
        }
        return base

    if target_id == "CT003":
        base["projected_primary"] = summary["peak_year_pedder_lake_index"]
        base["projected_secondary"] = summary["peak_value_pedder_lake_index"]
        return base

    if target_id == "CT004":
        stock_year = int(details["stocking_year"])
        window = details["post_stocking_window"]
        force_stock = forcing.loc[forcing["year"] == stock_year, "stocking_input"]
        trout_window = _window_subset(trajectory, int(window["start"]), int(window["end"]))
        t_1972 = float(trajectory.loc[trajectory["year"] == stock_year, "T"].iloc[0])
        p_1972 = float(trajectory.loc[trajectory["year"] == stock_year, "P"].iloc[0])
        base["projected_primary"] = float(force_stock.iloc[0]) if not force_stock.empty else 0.0
        base["projected_secondary"] = float(trout_window["T"].max()) if not trout_window.empty else 0.0
        base["projection_metadata"] = {
            "stocking_input_1972": base["projected_primary"],
            "T_1972": t_1972,
            "P_1972": p_1972,
            "max_trout_1973_1978": base["projected_secondary"],
            "max_piscivory_1973_1978": float(trout_window["P"].max()) if not trout_window.empty else 0.0,
        }
        return base

    if target_id == "CT005":
        year_a = int(details["pedder_dominant_year"])
        year_b = int(details["climbing_dominant_year"])
        ratio_1980 = float(trajectory.loc[trajectory["year"] == year_a, "climbing_to_pedder_lake_ratio"].iloc[0])
        ratio_1983 = float(trajectory.loc[trajectory["year"] == year_b, "climbing_to_pedder_lake_ratio"].iloc[0])
        base["projected_primary"] = ratio_1980
        base["projected_secondary"] = ratio_1983
        base["projection_metadata"] = {
            "ratio_1980": ratio_1980,
            "ratio_1983": ratio_1983,
        }
        return base

    if target_id == "CT006":
        window = details["window"]
        subset = _window_subset(trajectory, int(window["start"]), int(window["end"]))
        lake_present_mean = float(subset["lake_present"].mean())
        refuge_present_mean = float(subset["refuge_present"].mean())
        expected_refuge_capture_mean = _expected_detected_count(float(subset["N_R"].mean()), simulation_result)
        base["projected_primary"] = expected_refuge_capture_mean
        base["projected_secondary"] = refuge_present_mean
        base["projection_metadata"] = {
            "lake_present_mean": lake_present_mean,
            "refuge_present_mean": refuge_present_mean,
            "expected_refuge_capture_mean": expected_refuge_capture_mean,
        }
        return base

    if target_id == "CT007":
        window = details["window"]
        subset = _window_subset(trajectory, int(window["start"]), int(window["end"]))
        expected_refuge_capture_mean = _expected_detected_count(float(subset["N_R"].mean()), simulation_result)
        expected_occupied_sites = float(
            details["survey_sites"]
            * (1 - np.exp(-float(details["occupancy_anchor_alpha"]) * expected_refuge_capture_mean))
        )
        base["projected_primary"] = expected_occupied_sites
        base["projected_secondary"] = expected_refuge_capture_mean
        base["projection_metadata"] = {
            "expected_occupied_sites": expected_occupied_sites,
            "expected_refuge_capture_mean": expected_refuge_capture_mean,
        }
        return base

    if target_id == "CT008":
        window = details["window"]
        subset = _window_subset(trajectory, int(window["start"]), int(window["end"]))
        expected_natural_capture_mean = _expected_detected_count(float(subset["N_total"].mean()), simulation_result)
        latent_total_mean = float(subset["N_total"].mean())
        base["projected_primary"] = expected_natural_capture_mean
        base["projected_secondary"] = latent_total_mean
        base["projection_metadata"] = {
            "expected_natural_capture_mean": expected_natural_capture_mean,
            "latent_total_mean": latent_total_mean,
        }
        return base

    if target_id == "CT009":
        last_year = summary["last_year_total_present"]
        base["projected_primary"] = last_year if last_year is not None else np.nan
        base["projected_secondary"] = summary["first_year_total_absent"]
        return base

    if target_id == "CT010":
        window = details["window"]
        subset = _window_subset(trajectory, int(window["start"]), int(window["end"]))
        yearly_expected = [
            _expected_detected_count(float(row["N_total"]), simulation_result)
            for row in subset.to_dict(orient="records")
        ]
        base["projected_primary"] = float(np.mean(yearly_expected)) if yearly_expected else 0.0
        base["projected_secondary"] = float(max(yearly_expected)) if yearly_expected else 0.0
        base["projection_metadata"] = {
            "yearly_expected_detected_count": yearly_expected,
        }
        return base

    raise ValueError(f"Unsupported target_id for Module 2 projection: {target_id}")


def project_run_to_target_space(simulation_result: SimulationResult, model_inputs: ModelInputs) -> ProjectionResult:
    if model_inputs.calibration_targets is None:
        raise ValueError("ModelInputs missing calibration_targets")
    rows = [
        project_target(str(target_id), simulation_result, model_inputs)
        for target_id in model_inputs.calibration_targets["target_id"]
    ]
    projection_table = pd.DataFrame(rows)
    return ProjectionResult(projection_table=projection_table)
