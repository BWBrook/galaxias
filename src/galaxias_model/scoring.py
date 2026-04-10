from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from galaxias_model.observation import project_run_to_target_space
from galaxias_model.types import (
    AggregateScenarioBundleResult,
    AggregateScoringResult,
    ModelInputs,
    ProjectionResult,
    ResolvedParameters,
    ScenarioBundleResult,
    ScoringConfig,
    ScoringResult,
    SimulationResult,
)


EPS = 1e-9
SCORED = "scored"
DEFERRED = "deferred_requires_scenario"
FAILED = "failed_projection"


def _as_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "to_dict"):
        return row.to_dict()
    return dict(row)


def count_deviance(obs: float, exp: float) -> float:
    obs = max(float(obs), 0.0)
    exp = max(float(exp), 0.0)
    if obs == 0:
        return 2.0 * exp
    exp = max(exp, EPS)
    return 2.0 * (obs * math.log(obs / exp) - (obs - exp))


def count_penalty(obs: float, exp: float, overdispersion: float) -> float:
    return count_deviance(obs, exp) / max(float(overdispersion), EPS)


def range_penalty(value: float, low: float, high: float) -> float:
    value = float(value)
    low = float(low)
    high = float(high)
    width = max(high - low, EPS)
    if low <= value <= high:
        return 0.0
    if value < low:
        return (low - value) / width
    return (value - high) / width


def upper_bound_penalty(value: float, upper_bound: float, soft_gap: float) -> float:
    value = float(value)
    upper_bound = float(upper_bound)
    soft_gap = max(float(soft_gap), EPS)
    if value <= upper_bound:
        return 0.0
    return (value - upper_bound) / soft_gap


def lower_bound_penalty(value: float, lower_bound: float, soft_gap: float) -> float:
    value = float(value)
    lower_bound = float(lower_bound)
    soft_gap = max(float(soft_gap), EPS)
    if value >= lower_bound:
        return 0.0
    return (lower_bound - value) / soft_gap


def dominance_penalty(ratio: float, target: str, scale: float) -> float:
    ratio = max(float(ratio), EPS)
    scale = max(float(scale), EPS)
    if target == "pedder_dominant":
        return max(0.0, math.log(ratio) / scale)
    if target == "climbing_dominant":
        return max(0.0, math.log(1.0 / ratio) / scale)
    raise ValueError(f"Unknown dominance target: {target}")


def _require_metadata(projection_row: dict[str, Any]) -> dict[str, Any]:
    metadata = projection_row.get("projection_metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("projection_metadata must be a dictionary")
    return metadata


def _empty_failed_row(target_row: dict[str, Any], scenario_id: str, note: str) -> dict[str, Any]:
    return {
        "target_id": str(target_row["target_id"]),
        "target_group": str(target_row["target_group"]),
        "comparison_type": str(target_row["comparison_type"]),
        "scenario_id": scenario_id,
        "evaluation_status": FAILED,
        "projected_primary": np.nan,
        "projected_secondary": np.nan,
        "observed_primary": np.nan,
        "observed_secondary": np.nan,
        "raw_penalty": np.nan,
        "weighted_penalty": np.nan,
        "priority_weight": float(target_row["priority_weight"]),
        "notes": note,
    }


def score_target(
    target_row: Any,
    target_details: dict[str, Any],
    projection_row: Any,
    resolved_parameters: ResolvedParameters,
) -> dict[str, Any]:
    row = _as_dict(target_row)
    projection = _as_dict(projection_row)
    comparison_type = str(row["comparison_type"])
    evaluation_status = str(projection["evaluation_status"])
    priority_weight = float(row["priority_weight"])

    score_row = {
        "target_id": str(row["target_id"]),
        "target_group": str(row["target_group"]),
        "comparison_type": comparison_type,
        "scenario_id": str(projection["scenario_id"]),
        "evaluation_status": evaluation_status,
        "projected_primary": projection["projected_primary"],
        "projected_secondary": projection["projected_secondary"],
        "observed_primary": projection["observed_primary"],
        "observed_secondary": projection["observed_secondary"],
        "raw_penalty": np.nan,
        "weighted_penalty": np.nan,
        "priority_weight": priority_weight,
        "notes": str(projection.get("notes", "")),
    }

    if evaluation_status != SCORED:
        return score_row

    metadata = _require_metadata(projection)
    params = resolved_parameters
    pr037 = params.value("PR037")
    pr038 = params.value("PR038")

    if comparison_type == "qualitative_state_constraint":
        raw_penalty = 1.0 - 0.5 * (
            float(metadata["lake_presence_fraction"]) + float(metadata["refuge_presence_fraction"])
        )
    elif comparison_type == "window_relative_abundance_requirement":
        pre_mean = max(float(metadata["pre_mean"]), EPS)
        boom_peak = float(metadata["boom_peak"])
        late_mean = max(float(metadata["late_mean"]), EPS)
        raw_penalty = 0.5 * (
            max(0.0, 1.0 - boom_peak / pre_mean) + max(0.0, 1.0 - boom_peak / late_mean)
        )
    elif comparison_type == "target_year_match":
        raw_penalty = abs(float(projection["projected_primary"]) - float(target_details["target_year"])) / 1.0
    elif comparison_type == "event_and_window_presence":
        conditions = [
            float(metadata["stocking_input_1972"]) > 0.0,
            float(metadata["max_trout_1973_1978"]) > float(metadata["T_1972"]),
            float(metadata["max_piscivory_1973_1978"]) > float(metadata["P_1972"]),
        ]
        raw_penalty = float(sum(not passed for passed in conditions)) / 3.0
    elif comparison_type == "windowed_dominance_switch":
        raw_penalty = 0.5 * (
            dominance_penalty(float(metadata["ratio_1980"]), "pedder_dominant", pr038)
            + dominance_penalty(float(metadata["ratio_1983"]), "climbing_dominant", pr038)
        )
    elif comparison_type == "compartment_presence_constraint":
        capture_range = target_details["expected_capture_range"]
        raw_penalty = (
            float(metadata["lake_present_mean"])
            + (1.0 - float(metadata["refuge_present_mean"]))
            + range_penalty(
                float(metadata["expected_refuge_capture_mean"]),
                float(capture_range["low"]),
                float(capture_range["high"]),
            )
        ) / 3.0
    elif comparison_type == "joint_occupancy_and_count_constraint":
        site_range = target_details["occupied_site_range"]
        raw_penalty = 0.5 * (
            range_penalty(
                float(metadata["expected_occupied_sites"]),
                float(site_range["low"]),
                float(site_range["high"]),
            )
            + count_penalty(
                obs=float(target_details["observed_capture_count"]),
                exp=float(metadata["expected_refuge_capture_mean"]),
                overdispersion=pr037,
            )
        )
    elif comparison_type == "upper_bound_count_constraint":
        raw_penalty = (
            0.75
            * upper_bound_penalty(
                float(metadata["expected_natural_capture_mean"]),
                float(target_details["capture_upper_bound"]),
                float(target_details["capture_soft_gap"]),
            )
            + 0.25
            * upper_bound_penalty(
                float(metadata["latent_total_mean"]),
                float(target_details["latent_upper_bound"]),
                float(target_details["latent_soft_gap"]),
            )
        )
    elif comparison_type == "last_occurrence_event":
        projected_year = projection["projected_primary"]
        if projected_year is None or pd.isna(projected_year):
            raw_penalty = 10.0
        else:
            raw_penalty = 0.0 if int(projected_year) == int(target_details["target_year"]) else abs(
                int(projected_year) - int(target_details["target_year"])
            )
    elif comparison_type == "zero_detection_window":
        yearly_expected = metadata["yearly_expected_detected_count"]
        raw_penalty = float(np.mean([count_penalty(0.0, value, pr037) for value in yearly_expected]))
    elif comparison_type == "baseline_growth_constraint":
        first_year = metadata["first_year_juveniles_present"]
        juvenile_penalty = 10.0 if first_year is None else upper_bound_penalty(
            float(first_year),
            float(target_details["juvenile_deadline_year"]),
            2.0,
        )
        raw_penalty = float(
            np.mean(
                [
                    juvenile_penalty,
                    lower_bound_penalty(
                        float(metadata["max_adults_2001_2004"]),
                        float(target_details["adult_floor"]),
                        float(target_details["adult_floor_soft_gap"]),
                    ),
                    lower_bound_penalty(
                        float(metadata["total_2012"]),
                        float(target_details["total_2012_floor"]),
                        float(target_details["total_2012_soft_gap"]),
                    ),
                    lower_bound_penalty(
                        float(metadata["growth_ratio_2012_vs_founders"]),
                        float(target_details["growth_ratio_floor"]),
                        float(target_details["growth_ratio_soft_gap"]),
                    ),
                ]
            )
        )
    elif comparison_type == "delayed_establishment_constraint":
        first_year = metadata["first_year_juveniles_present"]
        first_year_penalty = 10.0 if first_year is None else abs(
            int(first_year) - int(target_details["juvenile_target_year"])
        )
        raw_penalty = float(
            np.mean(
                [
                    1.0 if bool(metadata["any_juveniles_2001_2007"]) else 0.0,
                    first_year_penalty,
                    lower_bound_penalty(
                        float(metadata["juveniles_2008"]),
                        float(target_details["juvenile_2008_floor"]),
                        float(target_details["juvenile_2008_soft_gap"]),
                    ),
                    lower_bound_penalty(
                        float(metadata["total_2012"]),
                        float(target_details["total_2012_floor"]),
                        float(target_details["total_2012_soft_gap"]),
                    ),
                    lower_bound_penalty(
                        float(metadata["juveniles_2012"]),
                        float(target_details["juvenile_2012_floor"]),
                        float(target_details["juvenile_2012_soft_gap"]),
                    ),
                ]
            )
        )
    else:
        raise ValueError(f"Unsupported comparison_type: {comparison_type}")

    score_row["raw_penalty"] = float(raw_penalty)
    score_row["weighted_penalty"] = float(raw_penalty * priority_weight)
    return score_row


def _required_target_mask(target_score_table: pd.DataFrame, scoring_config: ScoringConfig) -> pd.Series:
    mask = pd.Series(False, index=target_score_table.index)
    if scoring_config.include_historical_core:
        mask = mask | (target_score_table["target_group"] == "historical_core")
    if scoring_config.include_intrinsic_baseline:
        mask = mask | (target_score_table["target_group"] == "intrinsic_baseline")
    return mask


def _distance_if_scored(rows: pd.DataFrame) -> float | None:
    if rows.empty:
        return None
    if not (rows["evaluation_status"] == SCORED).all():
        return None
    return float(rows["weighted_penalty"].sum())


def _median_or_nan(series: pd.Series) -> float:
    clean = series.dropna()
    if clean.empty:
        return float("nan")
    return float(clean.median())


def score_scenario_run(
    simulation_result: SimulationResult,
    model_inputs: ModelInputs,
    scoring_config: ScoringConfig,
) -> ScoringResult:
    if model_inputs.calibration_targets is None or model_inputs.calibration_target_details is None:
        raise ValueError("ModelInputs missing calibration target tables")

    projection_result: ProjectionResult = project_run_to_target_space(simulation_result, model_inputs)
    projection_rows = {
        row["target_id"]: row for row in projection_result.projection_table.to_dict(orient="records")
    }

    score_rows: list[dict[str, Any]] = []
    for target_row in model_inputs.calibration_targets.to_dict(orient="records"):
        target_id = str(target_row["target_id"])
        score_row = score_target(
            target_row=target_row,
            target_details=model_inputs.calibration_target_details[target_id],
            projection_row=projection_rows[target_id],
            resolved_parameters=simulation_result.resolved_parameters,
        )
        score_row["family_id"] = simulation_result.resolved_parameters.family_id
        score_row["seed"] = int(simulation_result.summary["seed"])
        score_rows.append(score_row)

    target_score_table = pd.DataFrame(score_rows)
    historical_rows = target_score_table.loc[target_score_table["target_group"] == "historical_core"].copy()
    baseline_rows = target_score_table.loc[target_score_table["target_group"] == "intrinsic_baseline"].copy()
    required_rows = target_score_table.loc[_required_target_mask(target_score_table, scoring_config)].copy()

    deferred_target_ids = sorted(
        required_rows.loc[required_rows["evaluation_status"] != SCORED, "target_id"].astype(str).tolist()
    )
    historical_core_distance = _distance_if_scored(historical_rows) if scoring_config.include_historical_core else None
    intrinsic_baseline_distance = (
        _distance_if_scored(baseline_rows) if scoring_config.include_intrinsic_baseline else None
    )
    if scoring_config.require_all_targets and deferred_target_ids:
        overall_distance = None
    else:
        overall_distance = _distance_if_scored(required_rows)

    historical_core_ready = bool(
        (historical_rows["evaluation_status"] == SCORED).all() if scoring_config.include_historical_core else True
    )
    full_ready_for_module3 = bool(
        not deferred_target_ids if scoring_config.require_all_targets else historical_core_ready
    )

    summary = {
        "family_id": simulation_result.resolved_parameters.family_id,
        "scenario_id": simulation_result.scenario_id,
        "seed": int(simulation_result.summary["seed"]),
        "historical_core_distance": historical_core_distance,
        "intrinsic_baseline_distance": intrinsic_baseline_distance,
        "overall_distance": overall_distance,
        "historical_core_ready": historical_core_ready,
        "full_ready_for_module3": full_ready_for_module3,
        "needs_module_2_5": (not historical_core_ready) or (not full_ready_for_module3),
        "deferred_target_ids": deferred_target_ids,
    }

    return ScoringResult(
        projection_table=projection_result.projection_table,
        target_score_table=target_score_table,
        summary=summary,
    )


def score_historical_run(
    simulation_result: SimulationResult,
    model_inputs: ModelInputs,
    scoring_config: ScoringConfig,
) -> ScoringResult:
    return score_scenario_run(simulation_result, model_inputs, scoring_config)


def aggregate_replicate_scores(
    scoring_results: list[ScoringResult],
    scoring_config: ScoringConfig,
) -> AggregateScoringResult:
    if not scoring_results:
        raise ValueError("aggregate_replicate_scores requires at least one scoring result")
    if scoring_config.replicate_aggregation != "median":
        raise ValueError("aggregate_replicate_scores only supports replicate_aggregation='median'")

    replicate_score_table = pd.concat(
        [result.target_score_table.copy() for result in scoring_results],
        ignore_index=True,
    )

    aggregate_rows: list[dict[str, Any]] = []
    for target_id, subset in replicate_score_table.groupby("target_id", sort=True):
        scored_subset = subset.loc[subset["evaluation_status"] == SCORED]
        row = {
            "target_id": target_id,
            "target_group": str(subset["target_group"].iloc[0]),
            "comparison_type": str(subset["comparison_type"].iloc[0]),
            "scenario_id": str(subset["scenario_id"].iloc[0]),
            "evaluation_status": SCORED if len(scored_subset) == len(subset) else str(subset["evaluation_status"].iloc[0]),
            "projected_primary": _median_or_nan(scored_subset["projected_primary"]) if not scored_subset.empty else np.nan,
            "projected_secondary": _median_or_nan(scored_subset["projected_secondary"]) if not scored_subset.empty else np.nan,
            "observed_primary": subset["observed_primary"].iloc[0],
            "observed_secondary": subset["observed_secondary"].iloc[0],
            "raw_penalty": _median_or_nan(scored_subset["raw_penalty"]) if not scored_subset.empty else np.nan,
            "weighted_penalty": _median_or_nan(scored_subset["weighted_penalty"]) if not scored_subset.empty else np.nan,
            "priority_weight": float(subset["priority_weight"].iloc[0]),
            "replicate_count": int(len(subset)),
            "notes": str(subset["notes"].iloc[0]),
        }
        aggregate_rows.append(row)

    aggregate_target_score_table = pd.DataFrame(aggregate_rows).sort_values("target_id").reset_index(drop=True)

    historical_core_distances = [
        float(result.summary["historical_core_distance"])
        for result in scoring_results
        if result.summary["historical_core_distance"] is not None
    ]
    overall_distances = [
        float(result.summary["overall_distance"])
        for result in scoring_results
        if result.summary["overall_distance"] is not None
    ]

    deferred_target_ids = sorted(
        {
            target_id
            for result in scoring_results
            for target_id in result.summary["deferred_target_ids"]
        }
    )
    historical_core_ready = all(bool(result.summary["historical_core_ready"]) for result in scoring_results)
    full_ready_for_module3 = all(bool(result.summary["full_ready_for_module3"]) for result in scoring_results)

    summary = {
        "replicate_count": len(scoring_results),
        "replicate_aggregation": scoring_config.replicate_aggregation,
        "historical_core_distance_median": (
            float(np.median(historical_core_distances)) if historical_core_distances else None
        ),
        "historical_core_distance_iqr": (
            float(np.subtract(*np.percentile(historical_core_distances, [75, 25])))
            if historical_core_distances
            else None
        ),
        "overall_distance_median": float(np.median(overall_distances)) if overall_distances else None,
        "historical_core_ready": historical_core_ready,
        "full_ready_for_module3": full_ready_for_module3,
        "needs_module_2_5": (not historical_core_ready) or (not full_ready_for_module3),
        "deferred_target_ids": deferred_target_ids,
    }

    return AggregateScoringResult(
        replicate_score_table=replicate_score_table,
        aggregate_target_score_table=aggregate_target_score_table,
        summary=summary,
    )


def score_family_scenario_bundle(
    results_by_scenario: dict[str, SimulationResult],
    model_inputs: ModelInputs,
    scoring_config: ScoringConfig,
) -> ScenarioBundleResult:
    if model_inputs.calibration_targets is None or model_inputs.calibration_target_details is None:
        raise ValueError("ModelInputs missing calibration target tables")

    scenario_results = {
        scenario_id: score_scenario_run(result, model_inputs, scoring_config)
        for scenario_id, result in results_by_scenario.items()
    }

    selected_rows: list[dict[str, Any]] = []
    missing_scenarios: list[str] = []

    for target_row in model_inputs.calibration_targets.to_dict(orient="records"):
        target_id = str(target_row["target_id"])
        required_scenario_id = str(model_inputs.calibration_target_details[target_id]["required_scenario_id"])
        if required_scenario_id not in results_by_scenario:
            selected_rows.append(
                _empty_failed_row(
                    target_row,
                    required_scenario_id,
                    f"Missing required scenario result for {required_scenario_id}.",
                )
            )
            missing_scenarios.append(required_scenario_id)
            continue

        claimed_rows = []
        for scenario_id, scoring_result in scenario_results.items():
            matches = scoring_result.target_score_table.loc[
                scoring_result.target_score_table["target_id"] == target_id
            ]
            if len(matches) != 1:
                raise ValueError(f"Scenario {scenario_id} returned {len(matches)} rows for target {target_id}")
            row = matches.iloc[0].to_dict()
            if row["evaluation_status"] == SCORED:
                claimed_rows.append((scenario_id, row))

        if len(claimed_rows) > 1:
            selected_rows.append(
                _empty_failed_row(
                    target_row,
                    required_scenario_id,
                    f"Target {target_id} was scored by more than one scenario.",
                )
            )
            continue

        chosen_row = (
            scenario_results[required_scenario_id]
            .target_score_table.loc[
                scenario_results[required_scenario_id].target_score_table["target_id"] == target_id
            ]
            .iloc[0]
            .to_dict()
        )
        if chosen_row["evaluation_status"] != SCORED:
            chosen_row["evaluation_status"] = FAILED
            chosen_row["notes"] = (
                f"Required scenario {required_scenario_id} did not produce a scored target row "
                f"for {target_id}: {chosen_row['notes']}"
            )
            chosen_row["raw_penalty"] = np.nan
            chosen_row["weighted_penalty"] = np.nan
        selected_rows.append(chosen_row)

    bundle_target_score_table = pd.DataFrame(selected_rows).sort_values("target_id").reset_index(drop=True)
    historical_rows = bundle_target_score_table.loc[bundle_target_score_table["target_group"] == "historical_core"].copy()
    baseline_rows = bundle_target_score_table.loc[bundle_target_score_table["target_group"] == "intrinsic_baseline"].copy()

    deferred_target_ids = sorted(
        bundle_target_score_table.loc[bundle_target_score_table["evaluation_status"] != SCORED, "target_id"].astype(str).tolist()
    )
    historical_core_distance = _distance_if_scored(historical_rows)
    intrinsic_baseline_distance = _distance_if_scored(baseline_rows)
    overall_distance = _distance_if_scored(bundle_target_score_table)
    historical_core_ready = bool((historical_rows["evaluation_status"] == SCORED).all())
    full_ready_for_module3 = bool((bundle_target_score_table["evaluation_status"] == SCORED).all()) and not missing_scenarios

    summary = {
        "historical_core_distance": historical_core_distance,
        "intrinsic_baseline_distance": intrinsic_baseline_distance,
        "overall_distance": overall_distance,
        "historical_core_ready": historical_core_ready,
        "full_ready_for_module3": full_ready_for_module3,
        "needs_module_2_75": (not historical_core_ready) or (not full_ready_for_module3),
        "deferred_target_ids": deferred_target_ids,
        "missing_scenarios": sorted(set(missing_scenarios)),
    }

    return ScenarioBundleResult(
        scenario_results=scenario_results,
        bundle_target_score_table=bundle_target_score_table,
        summary=summary,
    )


def aggregate_scenario_bundle_scores(
    bundle_results: list[ScenarioBundleResult],
    scoring_config: ScoringConfig,
) -> AggregateScenarioBundleResult:
    if not bundle_results:
        raise ValueError("aggregate_scenario_bundle_scores requires at least one bundle result")
    if scoring_config.replicate_aggregation != "median":
        raise ValueError("aggregate_scenario_bundle_scores only supports replicate_aggregation='median'")

    replicate_tables = []
    for bundle_index, bundle_result in enumerate(bundle_results, start=1):
        table = bundle_result.bundle_target_score_table.copy()
        table["bundle_index"] = bundle_index
        replicate_tables.append(table)
    replicate_bundle_score_table = pd.concat(replicate_tables, ignore_index=True)

    aggregate_rows: list[dict[str, Any]] = []
    for target_id, subset in replicate_bundle_score_table.groupby("target_id", sort=True):
        scored_subset = subset.loc[subset["evaluation_status"] == SCORED]
        aggregate_rows.append(
            {
                "target_id": target_id,
                "target_group": str(subset["target_group"].iloc[0]),
                "comparison_type": str(subset["comparison_type"].iloc[0]),
                "scenario_id": str(subset["scenario_id"].iloc[0]),
                "evaluation_status": SCORED if len(scored_subset) == len(subset) else str(subset["evaluation_status"].iloc[0]),
                "projected_primary": _median_or_nan(scored_subset["projected_primary"]) if not scored_subset.empty else np.nan,
                "projected_secondary": _median_or_nan(scored_subset["projected_secondary"]) if not scored_subset.empty else np.nan,
                "observed_primary": subset["observed_primary"].iloc[0],
                "observed_secondary": subset["observed_secondary"].iloc[0],
                "raw_penalty": _median_or_nan(scored_subset["raw_penalty"]) if not scored_subset.empty else np.nan,
                "weighted_penalty": _median_or_nan(scored_subset["weighted_penalty"]) if not scored_subset.empty else np.nan,
                "priority_weight": float(subset["priority_weight"].iloc[0]),
                "replicate_count": int(len(subset)),
                "notes": str(subset["notes"].iloc[0]),
            }
        )
    aggregate_target_score_table = pd.DataFrame(aggregate_rows).sort_values("target_id").reset_index(drop=True)

    historical_core_distances = [
        float(bundle_result.summary["historical_core_distance"])
        for bundle_result in bundle_results
        if bundle_result.summary["historical_core_distance"] is not None
    ]
    intrinsic_baseline_distances = [
        float(bundle_result.summary["intrinsic_baseline_distance"])
        for bundle_result in bundle_results
        if bundle_result.summary["intrinsic_baseline_distance"] is not None
    ]
    overall_distances = [
        float(bundle_result.summary["overall_distance"])
        for bundle_result in bundle_results
        if bundle_result.summary["overall_distance"] is not None
    ]

    summary = {
        "replicate_count": len(bundle_results),
        "replicate_aggregation": scoring_config.replicate_aggregation,
        "historical_core_distance_median": float(np.median(historical_core_distances)) if historical_core_distances else None,
        "historical_core_distance_iqr": (
            float(np.subtract(*np.percentile(historical_core_distances, [75, 25])))
            if historical_core_distances
            else None
        ),
        "intrinsic_baseline_distance_median": (
            float(np.median(intrinsic_baseline_distances)) if intrinsic_baseline_distances else None
        ),
        "overall_distance_median": float(np.median(overall_distances)) if overall_distances else None,
        "historical_core_ready": all(bool(bundle_result.summary["historical_core_ready"]) for bundle_result in bundle_results),
        "full_ready_for_module3": all(bool(bundle_result.summary["full_ready_for_module3"]) for bundle_result in bundle_results),
        "needs_module_2_75": any(bool(bundle_result.summary["needs_module_2_75"]) for bundle_result in bundle_results),
        "deferred_target_ids": sorted(
            {
                target_id
                for bundle_result in bundle_results
                for target_id in bundle_result.summary["deferred_target_ids"]
            }
        ),
        "missing_scenarios": sorted(
            {
                scenario_id
                for bundle_result in bundle_results
                for scenario_id in bundle_result.summary["missing_scenarios"]
            }
        ),
    }

    return AggregateScenarioBundleResult(
        replicate_bundle_score_table=replicate_bundle_score_table,
        aggregate_target_score_table=aggregate_target_score_table,
        summary=summary,
    )
