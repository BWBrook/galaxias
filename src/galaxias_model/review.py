from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from typing import Any, Iterable

import numpy as np
import pandas as pd

from galaxias_model.calibration import run_module3_calibration, run_module3_calibration_stage
from galaxias_model.io import load_model_inputs, resolve_family_parameters
from galaxias_model.scoring import (
    aggregate_replicate_scores,
    aggregate_scenario_bundle_scores,
    score_family_scenario_bundle,
    score_historical_run,
    score_target,
)
from galaxias_model.simulation import get_scenario_definition, run_historical_simulation, run_scenario_simulation
from galaxias_model.types import ModelInputs, Module3Config, ScoringConfig, SimulationConfig


REVIEW_FAMILIES = [
    "habitat_only_null",
    "trout_only",
    "climbing_only",
    "persistent_joint_cause",
    "transient_perfect_storm",
]


def _format_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return "NA"
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_format_value(row.get(column)) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _regression_frames_match(
    current: pd.DataFrame,
    reference: pd.DataFrame,
    sort_columns: list[str],
) -> bool:
    current_sorted = current.sort_values(sort_columns).reset_index(drop=True).copy()
    reference_sorted = reference.sort_values(sort_columns).reset_index(drop=True).copy()
    try:
        pd.testing.assert_frame_equal(
            current_sorted,
            reference_sorted,
            check_exact=False,
            check_dtype=False,
            atol=1e-9,
            rtol=0,
        )
    except AssertionError:
        return False
    return True


def run_module1_5_review(
    model_inputs: ModelInputs,
    stochastic_seeds: Iterable[int] = range(1, 21),
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    deterministic_rows: list[dict[str, Any]] = []
    deterministic_config = SimulationConfig(stochastic=False)

    for family_id in REVIEW_FAMILIES:
        params = resolve_family_parameters(model_inputs, family_id)
        result = run_historical_simulation(params, family_id, deterministic_config, seed=1)
        row = dict(result.summary)
        row["N_total_1965"] = float(result.trajectory_table.loc[result.trajectory_table["year"] == 1965, "N_total"].iloc[0])
        row["N_total_1977"] = float(result.trajectory_table.loc[result.trajectory_table["year"] == 1977, "N_total"].iloc[0])
        row["N_total_2002"] = float(result.trajectory_table.loc[result.trajectory_table["year"] == 2002, "N_total"].iloc[0])
        deterministic_rows.append(row)

    stochastic_rows: list[dict[str, Any]] = []
    stochastic_config = SimulationConfig(stochastic=True)
    for seed in stochastic_seeds:
        params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
        result = run_historical_simulation(params, "transient_perfect_storm", stochastic_config, seed=seed)
        row = dict(result.summary)
        row["present_in_1980"] = int(
            result.trajectory_table.loc[result.trajectory_table["year"] == 1980, "total_present"].iloc[0]
        )
        stochastic_rows.append(row)

    deterministic = pd.DataFrame(deterministic_rows).sort_values("family_id").reset_index(drop=True)
    stochastic = pd.DataFrame(stochastic_rows).sort_values("seed").reset_index(drop=True)

    habitat = deterministic.loc[deterministic["family_id"] == "habitat_only_null"].iloc[0]
    transient = deterministic.loc[deterministic["family_id"] == "transient_perfect_storm"].iloc[0]
    transient_climbing_switch = transient["first_year_climbing_ratio_gt_one"]

    gates = {
        "deterministic_habitat_peak_1975_1978": 1975 <= int(habitat["peak_year_pedder_lake_index"]) <= 1978,
        "deterministic_transient_peak_1975_1978": 1975 <= int(transient["peak_year_pedder_lake_index"]) <= 1978,
        "deterministic_habitat_boom_ratio_gt_1": float(habitat["boom_ratio_1977_vs_1965"]) > 1,
        "deterministic_transient_boom_ratio_gt_1": float(transient["boom_ratio_1977_vs_1965"]) > 1,
        "deterministic_transient_final_below_habitat": float(transient["N_total_2002"]) < float(habitat["N_total_2002"]),
        "deterministic_transient_climbing_switch_1980_1984": (
            pd.notna(transient_climbing_switch)
            and 1980 <= int(transient_climbing_switch) <= 1984
        ),
        "stochastic_zero_pre1972_extinctions": int((stochastic["pre1972_min_total"] <= 0).sum()) == 0,
        "stochastic_at_least_18_present_in_1980": int(stochastic["present_in_1980"].sum()) >= 18,
        "stochastic_median_peak_1975_1978": 1975 <= float(stochastic["peak_year_pedder_lake_index"].median()) <= 1978,
    }
    gates["overall_ready_for_module2"] = all(gates.values())

    metrics = {
        "stochastic_runs": int(len(stochastic)),
        "stochastic_pre1972_extinctions": int((stochastic["pre1972_min_total"] <= 0).sum()),
        "stochastic_present_in_1980": int(stochastic["present_in_1980"].sum()),
        "stochastic_median_peak_year": float(stochastic["peak_year_pedder_lake_index"].median()),
    }

    return deterministic, stochastic, {"gates": gates, "metrics": metrics}


def render_module1_5_review(
    deterministic: pd.DataFrame,
    stochastic: pd.DataFrame,
    evaluation: dict[str, Any],
) -> str:
    gates = evaluation["gates"]
    metrics = evaluation["metrics"]
    deterministic_rows = deterministic[
        [
            "family_id",
            "peak_year_pedder_lake_index",
            "boom_ratio_1977_vs_1965",
            "first_year_climbing_ratio_gt_one",
            "N_total_2002",
            "final_to_peak_ratio",
        ]
    ].to_dict(orient="records")
    stochastic_rows = [
        {
            "metric": "stochastic_runs",
            "value": metrics["stochastic_runs"],
        },
        {
            "metric": "pre1972_extinctions",
            "value": metrics["stochastic_pre1972_extinctions"],
        },
        {
            "metric": "present_in_1980",
            "value": metrics["stochastic_present_in_1980"],
        },
        {
            "metric": "median_peak_year",
            "value": metrics["stochastic_median_peak_year"],
        },
    ]
    gate_rows = [{"gate": gate, "status": status} for gate, status in gates.items()]

    lines = [
        "# Module 1.5 Review",
        "",
        "## Summary",
        "",
        (
            "Module 1.5 reran the latent kernel after adding count-scale Pedder capacities "
            "(`PR039`) and a delayed inundation habitat-transition forcing (`PR040`)."
        ),
        (
            "This pass also keeps the post-flood boom interpretable by letting the upsurge "
            "temporarily relax lake density pressure and by applying explicit trout/climbing "
            "states as lagged annual pressures rather than as an instantaneous 1972 collapse."
        ),
        (
            "The purpose of this bundle is to decide whether the default kernel behavior is "
            "stable and qualitatively aligned with the Pedder chronology before Module 2."
        ),
        "",
        "## Acceptance Gates",
        "",
        _markdown_table(gate_rows, ["gate", "status"]),
        "",
        "## Deterministic Default Runs",
        "",
        _markdown_table(
            deterministic_rows,
            [
                "family_id",
                "peak_year_pedder_lake_index",
                "boom_ratio_1977_vs_1965",
                "first_year_climbing_ratio_gt_one",
                "N_total_2002",
                "final_to_peak_ratio",
            ],
        ),
        "",
        "## Stochastic Transient Perfect-Storm Review",
        "",
        _markdown_table(stochastic_rows, ["metric", "value"]),
        "",
        "## Interpretation",
        "",
    ]

    if gates["overall_ready_for_module2"]:
        lines.extend(
            [
                "All Module 1.5 acceptance gates passed.",
                (
                    "The default latent kernel is now stable enough and ecologically plausible enough "
                    "to support Module 2 observation scoring without the scorer being dominated by "
                    "initialization artefacts."
                ),
            ]
        )
    else:
        failed = [gate for gate, status in gates.items() if not status and gate != "overall_ready_for_module2"]
        lines.extend(
            [
                "Module 1.5 is not yet ready for Module 2.",
                "The following gates failed:",
                *[f"- `{gate}`" for gate in failed],
            ]
        )

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "- `data/module1_5_example_summary.csv`",
            "- `data/module1_5_stochastic_summary.csv`",
            "- `docs/module1_5_review.md`",
        ]
    )

    return "\n".join(lines) + "\n"


def write_module1_5_review_bundle(root: Path, output_root: Path | None = None) -> dict[str, Any]:
    data_dir = root / "data"
    target_root = output_root if output_root is not None else root
    output_data_dir = target_root / "data"
    docs_dir = target_root / "docs"
    model_inputs = load_model_inputs(data_dir)
    deterministic, stochastic, evaluation = run_module1_5_review(model_inputs)

    output_data_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    example_path = output_data_dir / "module1_5_example_summary.csv"
    stochastic_path = output_data_dir / "module1_5_stochastic_summary.csv"
    review_path = docs_dir / "module1_5_review.md"

    deterministic.to_csv(example_path, index=False)
    stochastic.to_csv(stochastic_path, index=False)
    review_path.write_text(
        render_module1_5_review(deterministic, stochastic, evaluation),
        encoding="utf-8",
    )

    return {
        "example_summary": example_path,
        "stochastic_summary": stochastic_path,
        "review_doc": review_path,
        "overall_ready_for_module2": evaluation["gates"]["overall_ready_for_module2"],
    }


def _target_details(model_inputs: ModelInputs, target_id: str) -> dict[str, Any]:
    if model_inputs.calibration_target_details is None:
        raise ValueError("ModelInputs missing calibration_target_details")
    return model_inputs.calibration_target_details[target_id]


def _target_row(model_inputs: ModelInputs, target_id: str) -> dict[str, Any]:
    if model_inputs.calibration_targets is None:
        raise ValueError("ModelInputs missing calibration_targets")
    return (
        model_inputs.calibration_targets.loc[model_inputs.calibration_targets["target_id"] == target_id]
        .iloc[0]
        .to_dict()
    )


def _synthetic_projection(target_id: str, **metadata: Any) -> dict[str, Any]:
    return {
        "target_id": target_id,
        "target_group": "historical_core",
        "comparison_type": "",
        "scenario_id": "historical_lake",
        "evaluation_status": "scored",
        "projected_primary": metadata.get("projected_primary", np.nan),
        "projected_secondary": metadata.get("projected_secondary", np.nan),
        "observed_primary": metadata.get("observed_primary", np.nan),
        "observed_secondary": metadata.get("observed_secondary", np.nan),
        "projection_metadata": metadata.get("projection_metadata", {}),
        "notes": "",
    }


def run_module2_readiness_review(
    model_inputs: ModelInputs,
    stochastic_seeds: Iterable[int] = range(1, 21),
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    scoring_config = ScoringConfig()
    deterministic_config = SimulationConfig(stochastic=False)
    deterministic_rows: list[pd.DataFrame] = []
    default_results: dict[str, Any] = {}

    for family_id in REVIEW_FAMILIES:
        params = resolve_family_parameters(model_inputs, family_id)
        simulation_result = run_historical_simulation(params, family_id, deterministic_config, seed=1)
        scoring_result = score_historical_run(simulation_result, model_inputs, scoring_config)
        default_results[family_id] = scoring_result
        deterministic_rows.append(scoring_result.target_score_table.copy())

    default_target_scores = pd.concat(deterministic_rows, ignore_index=True)

    transient_scores = []
    transient_result_list = []
    stochastic_config = SimulationConfig(stochastic=True)
    for seed in stochastic_seeds:
        params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
        simulation_result = run_historical_simulation(params, "transient_perfect_storm", stochastic_config, seed=seed)
        scoring_result = score_historical_run(simulation_result, model_inputs, scoring_config)
        transient_scores.append(scoring_result.target_score_table.copy())
        transient_result_list.append(scoring_result)

    transient_replicate_scores = pd.concat(transient_scores, ignore_index=True)
    aggregate_transient = aggregate_replicate_scores(transient_result_list, scoring_config)

    core_scores = default_target_scores.loc[default_target_scores["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])]
    finite_core_penalties = np.isfinite(core_scores["raw_penalty"].astype(float)).all()
    all_core_scored = (core_scores["evaluation_status"] == "scored").all()

    ct004 = default_target_scores.loc[default_target_scores["target_id"] == "CT004"].copy()
    trout_active = float(
        ct004.loc[ct004["family_id"].isin(["trout_only", "persistent_joint_cause", "transient_perfect_storm"]), "raw_penalty"].mean()
    )
    trout_inactive = float(
        ct004.loc[ct004["family_id"].isin(["habitat_only_null", "climbing_only"]), "raw_penalty"].mean()
    )
    ct005 = default_target_scores.loc[default_target_scores["target_id"] == "CT005"].copy()
    climbing_active = float(
        ct005.loc[ct005["family_id"].isin(["climbing_only", "persistent_joint_cause", "transient_perfect_storm"]), "raw_penalty"].mean()
    )
    climbing_inactive = float(
        ct005.loc[ct005["family_id"].isin(["habitat_only_null", "trout_only"]), "raw_penalty"].mean()
    )

    transient_params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    monotonicity = {
        "CT006": None,
        "CT007": None,
        "CT008": None,
        "CT009": None,
        "CT010": None,
    }

    ct006_better = score_target(
        _target_row(model_inputs, "CT006"),
        _target_details(model_inputs, "CT006"),
        _synthetic_projection(
            "CT006",
            projected_primary=12.0,
            projected_secondary=1.0,
            projection_metadata={
                "lake_present_mean": 0.0,
                "refuge_present_mean": 1.0,
                "expected_refuge_capture_mean": 12.0,
            },
        ),
        transient_params,
    )
    ct006_worse = score_target(
        _target_row(model_inputs, "CT006"),
        _target_details(model_inputs, "CT006"),
        _synthetic_projection(
            "CT006",
            projected_primary=40.0,
            projected_secondary=0.2,
            projection_metadata={
                "lake_present_mean": 1.0,
                "refuge_present_mean": 0.2,
                "expected_refuge_capture_mean": 40.0,
            },
        ),
        transient_params,
    )
    monotonicity["CT006"] = float(ct006_better["raw_penalty"]) < float(ct006_worse["raw_penalty"])

    ct007_better = score_target(
        _target_row(model_inputs, "CT007"),
        _target_details(model_inputs, "CT007"),
        _synthetic_projection(
            "CT007",
            projected_primary=5.0,
            projected_secondary=68.0,
            projection_metadata={
                "expected_occupied_sites": 5.0,
                "expected_refuge_capture_mean": 68.0,
            },
        ),
        transient_params,
    )
    ct007_worse = score_target(
        _target_row(model_inputs, "CT007"),
        _target_details(model_inputs, "CT007"),
        _synthetic_projection(
            "CT007",
            projected_primary=15.0,
            projected_secondary=5.0,
            projection_metadata={
                "expected_occupied_sites": 15.0,
                "expected_refuge_capture_mean": 5.0,
            },
        ),
        transient_params,
    )
    monotonicity["CT007"] = float(ct007_better["raw_penalty"]) < float(ct007_worse["raw_penalty"])

    ct008_better = score_target(
        _target_row(model_inputs, "CT008"),
        _target_details(model_inputs, "CT008"),
        _synthetic_projection(
            "CT008",
            projected_primary=8.0,
            projected_secondary=40.0,
            projection_metadata={
                "expected_natural_capture_mean": 8.0,
                "latent_total_mean": 40.0,
            },
        ),
        transient_params,
    )
    ct008_worse = score_target(
        _target_row(model_inputs, "CT008"),
        _target_details(model_inputs, "CT008"),
        _synthetic_projection(
            "CT008",
            projected_primary=30.0,
            projected_secondary=200.0,
            projection_metadata={
                "expected_natural_capture_mean": 30.0,
                "latent_total_mean": 200.0,
            },
        ),
        transient_params,
    )
    monotonicity["CT008"] = float(ct008_better["raw_penalty"]) < float(ct008_worse["raw_penalty"])

    ct009_better = score_target(
        _target_row(model_inputs, "CT009"),
        _target_details(model_inputs, "CT009"),
        _synthetic_projection("CT009", projected_primary=1996.0, projected_secondary=1997.0, projection_metadata={}),
        transient_params,
    )
    ct009_worse = score_target(
        _target_row(model_inputs, "CT009"),
        _target_details(model_inputs, "CT009"),
        _synthetic_projection("CT009", projected_primary=1992.0, projected_secondary=1993.0, projection_metadata={}),
        transient_params,
    )
    monotonicity["CT009"] = float(ct009_better["raw_penalty"]) < float(ct009_worse["raw_penalty"])

    ct010_better = score_target(
        _target_row(model_inputs, "CT010"),
        _target_details(model_inputs, "CT010"),
        _synthetic_projection(
            "CT010",
            projected_primary=0.0,
            projected_secondary=0.0,
            projection_metadata={"yearly_expected_detected_count": [0.0, 0.0, 0.0, 0.0, 0.0]},
        ),
        transient_params,
    )
    ct010_worse = score_target(
        _target_row(model_inputs, "CT010"),
        _target_details(model_inputs, "CT010"),
        _synthetic_projection(
            "CT010",
            projected_primary=10.0,
            projected_secondary=20.0,
            projection_metadata={"yearly_expected_detected_count": [2.0, 5.0, 10.0, 15.0, 20.0]},
        ),
        transient_params,
    )
    monotonicity["CT010"] = float(ct010_better["raw_penalty"]) < float(ct010_worse["raw_penalty"])

    repeat_params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    repeat_result_a = score_historical_run(
        run_historical_simulation(repeat_params, "transient_perfect_storm", stochastic_config, seed=99),
        model_inputs,
        scoring_config,
    )
    repeat_result_b = score_historical_run(
        run_historical_simulation(repeat_params, "transient_perfect_storm", stochastic_config, seed=99),
        model_inputs,
        scoring_config,
    )
    identical_seed_stable = repeat_result_a.target_score_table.equals(repeat_result_b.target_score_table)

    transient_scored = transient_replicate_scores.loc[transient_replicate_scores["evaluation_status"] == "scored"]
    finite_transient_penalties = np.isfinite(transient_scored["raw_penalty"].astype(float)).all()
    finite_aggregate_history = (
        aggregate_transient.summary["historical_core_distance_median"] is not None
        and aggregate_transient.summary["historical_core_distance_iqr"] is not None
        and np.isfinite(float(aggregate_transient.summary["historical_core_distance_median"]))
        and np.isfinite(float(aggregate_transient.summary["historical_core_distance_iqr"]))
    )

    gates = {
        "deterministic_core_targets_scored": bool(all_core_scored),
        "deterministic_core_penalties_finite": bool(finite_core_penalties),
        "ct004_discriminates_trout_active_vs_inactive": trout_active < trout_inactive,
        "ct005_discriminates_climbing_active_vs_inactive": climbing_active < climbing_inactive,
        "ct006_monotonicity": bool(monotonicity["CT006"]),
        "ct007_monotonicity": bool(monotonicity["CT007"]),
        "ct008_monotonicity": bool(monotonicity["CT008"]),
        "ct009_monotonicity": bool(monotonicity["CT009"]),
        "ct010_monotonicity": bool(monotonicity["CT010"]),
        "replicate_same_seed_stable": bool(identical_seed_stable),
        "transient_replicate_penalties_finite": bool(finite_transient_penalties),
        "aggregate_history_median_and_iqr_finite": bool(finite_aggregate_history),
    }
    gates["historical_core_ready"] = all(gates.values()) and bool(
        aggregate_transient.summary["historical_core_ready"]
    )
    gates["full_ready_for_module3"] = gates["historical_core_ready"] and bool(
        aggregate_transient.summary["full_ready_for_module3"]
    )
    gates["needs_module_2_5"] = (not gates["historical_core_ready"]) or (not gates["full_ready_for_module3"])

    evaluation = {
        "gates": gates,
        "metrics": {
            "ct004_trout_active_mean_penalty": trout_active,
            "ct004_trout_inactive_mean_penalty": trout_inactive,
            "ct005_climbing_active_mean_penalty": climbing_active,
            "ct005_climbing_inactive_mean_penalty": climbing_inactive,
            "historical_core_distance_median": aggregate_transient.summary["historical_core_distance_median"],
            "historical_core_distance_iqr": aggregate_transient.summary["historical_core_distance_iqr"],
            "deferred_target_ids": aggregate_transient.summary["deferred_target_ids"],
        },
        "aggregate_transient": aggregate_transient,
    }
    return default_target_scores, transient_replicate_scores, evaluation


def render_module2_readiness_review(
    default_target_scores: pd.DataFrame,
    transient_replicate_scores: pd.DataFrame,
    evaluation: dict[str, Any],
) -> str:
    gates = evaluation["gates"]
    metrics = evaluation["metrics"]
    aggregate_transient = evaluation["aggregate_transient"]

    gate_rows = [{"gate": key, "status": value} for key, value in gates.items()]
    default_rows = (
        default_target_scores.loc[
            default_target_scores["target_id"].isin(["CT004", "CT005", "CT011", "CT012"]),
            ["family_id", "target_id", "evaluation_status", "raw_penalty"],
        ]
        .sort_values(["target_id", "family_id"])
        .to_dict(orient="records")
    )
    transient_rows = [
        {
            "metric": "historical_core_distance_median",
            "value": metrics["historical_core_distance_median"],
        },
        {
            "metric": "historical_core_distance_iqr",
            "value": metrics["historical_core_distance_iqr"],
        },
        {
            "metric": "deferred_target_ids",
            "value": ";".join(metrics["deferred_target_ids"]) if metrics["deferred_target_ids"] else "none",
        },
        {
            "metric": "stochastic_replicate_rows",
            "value": len(transient_replicate_scores),
        },
    ]

    lines = [
        "# Module 2 Readiness Review",
        "",
        "## Summary",
        "",
        (
            "Module 2 adds the observation bridge and deterministic target scoring layer for "
            "CT001-CT012 without changing the validated latent kernel."
        ),
        (
            "Historical-core targets are now projectable and scoreable from the current "
            "`historical_lake` scenario, while the intrinsic-baseline targets remain blocked "
            "until Lake Oberon and Strathgordon scenarios are implemented in Module 2.5."
        ),
        "",
        "## Acceptance Gates",
        "",
        _markdown_table(gate_rows, ["gate", "status"]),
        "",
        "## Target Highlights",
        "",
        _markdown_table(default_rows, ["family_id", "target_id", "evaluation_status", "raw_penalty"]),
        "",
        "## Transient Replicate Summary",
        "",
        _markdown_table(transient_rows, ["metric", "value"]),
        "",
        "## Interpretation",
        "",
    ]

    if gates["historical_core_ready"]:
        lines.append("The historical-core scoring layer passed its readiness gate.")
    else:
        lines.append("The historical-core scoring layer did not pass its readiness gate.")

    if gates["full_ready_for_module3"]:
        lines.extend(
            [
                "All required targets are scored, so the project is ready to move into Module 3.",
            ]
        )
    else:
        lines.extend(
            [
                "Module 3 should not start yet.",
                (
                    "Because `CT011` and `CT012` are still `deferred_requires_scenario` under the "
                    "current `historical_lake` kernel, the correct next step is Module 2.5."
                ),
            ]
        )
        if gates["historical_core_ready"]:
            lines.append(
                "This is a baseline-scenario enablement problem, not a failure of the historical-core observation bridge."
            )
        else:
            lines.append(
                "This also signals a historical-core scoring problem, so Module 2.5 would need to begin with scorer refinement."
            )

    lines.extend(
        [
            "",
            "## Module 2.5 Trigger",
            "",
            "- Trigger if `historical_core_ready=False` because the scorer is unstable, non-monotonic, or poorly discriminative.",
            "- Trigger if `historical_core_ready=True` but `full_ready_for_module3=False` because `CT011` and `CT012` remain deferred.",
            "- In the current state, the second trigger applies.",
            "",
            "## Artifacts",
            "",
            "- `data/module2_default_target_scores.csv`",
            "- `data/module2_transient_replicate_scores.csv`",
            "- `docs/module2_readiness_review.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_module2_readiness_bundle(root: Path, output_root: Path | None = None) -> dict[str, Any]:
    data_dir = root / "data"
    target_root = output_root if output_root is not None else root
    output_data_dir = target_root / "data"
    docs_dir = target_root / "docs"
    model_inputs = load_model_inputs(data_dir)
    default_target_scores, transient_replicate_scores, evaluation = run_module2_readiness_review(model_inputs)

    output_data_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    default_path = output_data_dir / "module2_default_target_scores.csv"
    transient_path = output_data_dir / "module2_transient_replicate_scores.csv"
    review_path = docs_dir / "module2_readiness_review.md"

    default_target_scores.to_csv(default_path, index=False)
    transient_replicate_scores.to_csv(transient_path, index=False)
    review_path.write_text(
        render_module2_readiness_review(default_target_scores, transient_replicate_scores, evaluation),
        encoding="utf-8",
    )

    return {
        "default_target_scores": default_path,
        "transient_replicate_scores": transient_path,
        "review_doc": review_path,
        "historical_core_ready": evaluation["gates"]["historical_core_ready"],
        "full_ready_for_module3": evaluation["gates"]["full_ready_for_module3"],
        "needs_module_2_5": evaluation["gates"]["needs_module_2_5"],
    }


def _run_scenario_result(
    model_inputs: ModelInputs,
    params,
    family_id: str,
    scenario_id: str,
    stochastic: bool,
    seed: int,
):
    scenario_definition = get_scenario_definition(model_inputs, scenario_id)
    config = SimulationConfig(
        stochastic=stochastic,
        scenario_id=scenario_id,
        scenario_definition=scenario_definition,
        start_year=scenario_definition.start_year,
        end_year=scenario_definition.end_year,
    )
    if scenario_id == "historical_lake":
        return run_historical_simulation(params, family_id, config, seed=seed)
    return run_scenario_simulation(params, family_id, config, seed=seed)


def _bundle_rows_for_family(
    model_inputs: ModelInputs,
    family_id: str,
    historical_stochastic: bool,
    historical_seed: int,
):
    params = resolve_family_parameters(model_inputs, family_id)
    results_by_scenario = {
        "historical_lake": _run_scenario_result(
            model_inputs,
            params,
            family_id,
            "historical_lake",
            stochastic=historical_stochastic,
            seed=historical_seed,
        ),
        "lake_oberon": _run_scenario_result(
            model_inputs,
            params,
            family_id,
            "lake_oberon",
            stochastic=False,
            seed=1,
        ),
        "strathgordon": _run_scenario_result(
            model_inputs,
            params,
            family_id,
            "strathgordon",
            stochastic=False,
            seed=1,
        ),
    }
    return score_family_scenario_bundle(results_by_scenario, model_inputs, ScoringConfig())


def run_module2_5_readiness_review(
    model_inputs: ModelInputs,
    stochastic_seeds: Iterable[int] = range(1, 21),
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    default_bundles = [
        _bundle_rows_for_family(model_inputs, family_id, historical_stochastic=False, historical_seed=1)
        for family_id in REVIEW_FAMILIES
    ]
    default_bundle_scores = pd.concat(
        [bundle.bundle_target_score_table.copy() for bundle in default_bundles],
        ignore_index=True,
    )

    transient_bundles = [
        _bundle_rows_for_family(
            model_inputs,
            "transient_perfect_storm",
            historical_stochastic=True,
            historical_seed=seed,
        )
        for seed in stochastic_seeds
    ]
    transient_bundle_scores = pd.concat(
        [bundle.bundle_target_score_table.copy() for bundle in transient_bundles],
        ignore_index=True,
    )
    aggregate_transient = aggregate_scenario_bundle_scores(transient_bundles, ScoringConfig())

    module2_default = pd.read_csv(model_inputs.data_dir / "module2_default_target_scores.csv")
    module2_transient = pd.read_csv(model_inputs.data_dir / "module2_transient_replicate_scores.csv")
    current_default_hist = default_bundle_scores.loc[default_bundle_scores["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])].copy()
    current_transient_hist = transient_bundle_scores.loc[transient_bundle_scores["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])].copy()
    ref_default_hist = module2_default.loc[module2_default["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])].copy()
    ref_transient_hist = module2_transient.loc[module2_transient["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])].copy()
    regression_columns = [
        "target_id",
        "family_id",
        "seed",
        "scenario_id",
        "evaluation_status",
        "projected_primary",
        "projected_secondary",
        "observed_primary",
        "observed_secondary",
        "raw_penalty",
        "weighted_penalty",
    ]
    current_default_hist = current_default_hist[regression_columns]
    ref_default_hist = ref_default_hist[regression_columns]
    current_transient_hist = current_transient_hist[regression_columns]
    ref_transient_hist = ref_transient_hist[regression_columns]
    historical_default_regression_pass = _regression_frames_match(
        current_default_hist,
        ref_default_hist,
        ["family_id", "target_id"],
    )
    historical_transient_regression_pass = _regression_frames_match(
        current_transient_hist,
        ref_transient_hist,
        ["seed", "target_id"],
    )

    all_default_scored = (default_bundle_scores["evaluation_status"] == "scored").all()
    no_missing_default = all(not bundle.summary["missing_scenarios"] for bundle in default_bundles)
    full_ready_default = all(bundle.summary["full_ready_for_module3"] for bundle in default_bundles)
    full_ready_transient = all(bundle.summary["full_ready_for_module3"] for bundle in transient_bundles)

    smoke_rows = []
    smoke_params = resolve_family_parameters(model_inputs, "habitat_only_null")
    for scenario_id in ["lake_oberon", "strathgordon"]:
        for seed in range(1, 6):
            sim_result = _run_scenario_result(
                model_inputs,
                smoke_params,
                "habitat_only_null",
                scenario_id,
                stochastic=True,
                seed=seed,
            )
            bundle = score_family_scenario_bundle(
                {
                    "historical_lake": _run_scenario_result(
                        model_inputs,
                        smoke_params,
                        "habitat_only_null",
                        "historical_lake",
                        stochastic=False,
                        seed=1,
                    ),
                    scenario_id: sim_result,
                    "strathgordon" if scenario_id == "lake_oberon" else "lake_oberon": _run_scenario_result(
                        model_inputs,
                        smoke_params,
                        "habitat_only_null",
                        "strathgordon" if scenario_id == "lake_oberon" else "lake_oberon",
                        stochastic=False,
                        seed=1,
                    ),
                },
                model_inputs,
                ScoringConfig(),
            )
            relevant = bundle.bundle_target_score_table.loc[
                bundle.bundle_target_score_table["target_id"] == ("CT011" if scenario_id == "lake_oberon" else "CT012")
            ]
            smoke_rows.append(
                {
                    "scenario_id": scenario_id,
                    "seed": seed,
                    "raw_penalty": float(relevant["raw_penalty"].iloc[0]),
                    "weighted_penalty": float(relevant["weighted_penalty"].iloc[0]),
                }
            )
    smoke_frame = pd.DataFrame(smoke_rows)
    smoke_finite = np.isfinite(smoke_frame["raw_penalty"]).all() and np.isfinite(smoke_frame["weighted_penalty"]).all()

    gates = {
        "historical_default_regression_pass": historical_default_regression_pass,
        "historical_transient_regression_pass": historical_transient_regression_pass,
        "bundle_all_targets_scored": bool(all_default_scored),
        "bundle_no_missing_scenarios": bool(no_missing_default),
        "default_bundles_full_ready_for_module3": bool(full_ready_default),
        "transient_bundle_full_ready_for_module3": bool(full_ready_transient),
        "aggregate_history_median_and_iqr_finite": (
            aggregate_transient.summary["historical_core_distance_median"] is not None
            and aggregate_transient.summary["historical_core_distance_iqr"] is not None
            and np.isfinite(float(aggregate_transient.summary["historical_core_distance_median"]))
            and np.isfinite(float(aggregate_transient.summary["historical_core_distance_iqr"]))
        ),
    }
    gates["historical_core_ready"] = all(gates.values())
    gates["full_ready_for_module3"] = gates["historical_core_ready"] and (
        not aggregate_transient.summary["deferred_target_ids"]
        and not aggregate_transient.summary["missing_scenarios"]
    )
    gates["needs_module_2_75"] = (not gates["historical_core_ready"]) or (not gates["full_ready_for_module3"])

    evaluation = {
        "gates": gates,
        "metrics": {
            "historical_core_distance_median": aggregate_transient.summary["historical_core_distance_median"],
            "historical_core_distance_iqr": aggregate_transient.summary["historical_core_distance_iqr"],
            "intrinsic_baseline_distance_median": aggregate_transient.summary["intrinsic_baseline_distance_median"],
            "deferred_target_ids": aggregate_transient.summary["deferred_target_ids"],
            "missing_scenarios": aggregate_transient.summary["missing_scenarios"],
            "optional_stochastic_baseline_smoke_finite": bool(smoke_finite),
        },
        "aggregate_transient": aggregate_transient,
        "optional_smoke": smoke_frame,
    }
    return default_bundle_scores, transient_bundle_scores, evaluation


def render_module2_5_readiness_review(
    default_bundle_scores: pd.DataFrame,
    transient_bundle_scores: pd.DataFrame,
    evaluation: dict[str, Any],
) -> str:
    gates = evaluation["gates"]
    metrics = evaluation["metrics"]
    gate_rows = [{"gate": key, "status": value} for key, value in gates.items()]
    default_rows = (
        default_bundle_scores.loc[
            default_bundle_scores["target_id"].isin(["CT011", "CT012"]),
            ["family_id", "target_id", "scenario_id", "evaluation_status", "raw_penalty"],
        ]
        .sort_values(["target_id", "family_id"])
        .to_dict(orient="records")
    )
    transient_rows = [
        {"metric": "historical_core_distance_median", "value": metrics["historical_core_distance_median"]},
        {"metric": "historical_core_distance_iqr", "value": metrics["historical_core_distance_iqr"]},
        {"metric": "intrinsic_baseline_distance_median", "value": metrics["intrinsic_baseline_distance_median"]},
        {
            "metric": "optional_stochastic_baseline_smoke_finite",
            "value": metrics["optional_stochastic_baseline_smoke_finite"],
        },
    ]

    lines = [
        "# Module 2.5 Readiness Review",
        "",
        "## Summary",
        "",
        (
            "Module 2.5 adds explicit `lake_oberon` and `strathgordon` scenarios, then scores "
            "all twelve calibration targets through a scenario bundle rather than a single historical run."
        ),
        (
            "The historical path is checked against the tracked Module 2 outputs, while the new "
            "baseline scenarios activate `CT011` and `CT012` without introducing new free parameters."
        ),
        "",
        "## Acceptance Gates",
        "",
        _markdown_table(gate_rows, ["gate", "status"]),
        "",
        "## Baseline Target Highlights",
        "",
        _markdown_table(default_rows, ["family_id", "target_id", "scenario_id", "evaluation_status", "raw_penalty"]),
        "",
        "## Transient Bundle Summary",
        "",
        _markdown_table(transient_rows, ["metric", "value"]),
        "",
        "## Interpretation",
        "",
    ]

    if gates["full_ready_for_module3"]:
        lines.extend(
            [
                "All bundle targets now score successfully, with no missing scenarios and no deferred targets.",
                "Module 3 can proceed on top of the Module 2.5 bundle-scoring interface.",
            ]
        )
    else:
        lines.extend(
            [
                "Module 3 should not start yet.",
                "The correct next step is Module 2.75 because at least one Module 2.5 readiness gate failed.",
            ]
        )

    lines.extend(
        [
            "",
            "## Module 2.75 Trigger",
            "",
            "- Trigger if `historical_core_ready=False` after scenario enablement, which means the shared kernel/scoring contract regressed.",
            "- Trigger if `historical_core_ready=True` but `full_ready_for_module3=False`, which means the baseline scenarios or their target formulas still need refinement.",
            "",
            "## Artifacts",
            "",
            "- `data/module2_5_default_bundle_scores.csv`",
            "- `data/module2_5_transient_bundle_scores.csv`",
            "- `docs/module2_5_readiness_review.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_module2_5_readiness_bundle(root: Path, output_root: Path | None = None) -> dict[str, Any]:
    data_dir = root / "data"
    target_root = output_root if output_root is not None else root
    output_data_dir = target_root / "data"
    docs_dir = target_root / "docs"
    model_inputs = load_model_inputs(data_dir)
    default_bundle_scores, transient_bundle_scores, evaluation = run_module2_5_readiness_review(model_inputs)

    output_data_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    default_path = output_data_dir / "module2_5_default_bundle_scores.csv"
    transient_path = output_data_dir / "module2_5_transient_bundle_scores.csv"
    review_path = docs_dir / "module2_5_readiness_review.md"

    default_bundle_scores.to_csv(default_path, index=False)
    transient_bundle_scores.to_csv(transient_path, index=False)
    review_path.write_text(
        render_module2_5_readiness_review(default_bundle_scores, transient_bundle_scores, evaluation),
        encoding="utf-8",
    )

    return {
        "default_bundle_scores": default_path,
        "transient_bundle_scores": transient_path,
        "review_doc": review_path,
        "historical_core_ready": evaluation["gates"]["historical_core_ready"],
        "full_ready_for_module3": evaluation["gates"]["full_ready_for_module3"],
        "needs_module_2_75": evaluation["gates"]["needs_module_2_75"],
    }


MODULE3_REVIEW_TARGET_IDS = {f"CT{i:03d}" for i in range(1, 13)}


def _fresh_run_dir(path: Path) -> Path:
    if path.exists():
        rmtree(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _accepted_id_tuple(frame: pd.DataFrame) -> tuple[str, ...]:
    if frame.empty:
        return ()
    return tuple(frame["proposal_id"].astype(str).tolist())


def _safe_spearman(x: pd.Series, y: pd.Series) -> float:
    paired = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(paired) < 2:
        return float("nan")
    if paired["x"].nunique() < 2 or paired["y"].nunique() < 2:
        return float("nan")
    ranked = paired.rank(method="average")
    return float(ranked["x"].corr(ranked["y"], method="pearson"))


def _module3_small_repro_config(output_dir: Path, workers: int) -> Module3Config:
    return Module3Config(
        stage_a_draws_per_family=60,
        stage_a_keep_per_family=8,
        stage_b_historical_replicates=3,
        final_acceptance_fraction=0.10,
        final_acceptance_cap=5,
        workers=workers,
        batch_size=50,
        master_seed=20260410,
        stochastic_baselines=False,
        output_dir=output_dir,
        resume=False,
    )


def _module3_screen_discrimination_rows(
    proposal_summary: pd.DataFrame,
    config: Module3Config,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family_id in config.families:
        subset = proposal_summary.loc[proposal_summary["family_id"] == family_id].copy()
        retained = subset.loc[
            pd.to_numeric(subset["stage_a_rank"], errors="coerce").between(1, config.stage_a_keep_per_family),
            "deterministic_overall_distance",
        ]
        rejected = subset.loc[subset["stage_status"] == "stage_a_rejected", "deterministic_overall_distance"]
        retained_median = float(pd.to_numeric(retained, errors="coerce").median()) if not retained.empty else float("nan")
        rejected_median = float(pd.to_numeric(rejected, errors="coerce").median()) if not rejected.empty else float("nan")
        passed = bool(
            np.isfinite(retained_median)
            and np.isfinite(rejected_median)
            and retained_median <= 0.8 * rejected_median
        )
        rows.append(
            {
                "family_id": family_id,
                "retained_median": retained_median,
                "rejected_median": rejected_median,
                "pass": passed,
            }
        )
    return pd.DataFrame(rows)


def _module3_rank_consistency_rows(proposal_summary: pd.DataFrame, families: Iterable[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family_id in families:
        subset = proposal_summary.loc[
            (proposal_summary["family_id"] == family_id)
            & (proposal_summary["stage_status"].isin({"stage_b_rejected", "accepted"}))
        ].copy()
        correlation = _safe_spearman(
            subset["deterministic_overall_distance"],
            subset["stochastic_overall_distance_median"],
        )
        passed = bool(np.isfinite(correlation) and correlation >= 0.40)
        rows.append(
            {
                "family_id": family_id,
                "spearman_rank_correlation": correlation,
                "pass": passed,
            }
        )
    return pd.DataFrame(rows)


def _module3_accepted_targets_scored(
    accepted_summary: pd.DataFrame,
    target_scores: pd.DataFrame,
) -> bool:
    if accepted_summary.empty:
        return False
    for proposal_id in accepted_summary["proposal_id"].astype(str):
        subset = target_scores.loc[
            (target_scores["proposal_id"] == proposal_id)
            & (target_scores["stage"] == "stage_b")
        ].copy()
        if set(subset["target_id"].astype(str)) != MODULE3_REVIEW_TARGET_IDS:
            return False
        if not (subset["evaluation_status"] == "scored").all():
            return False
    return True


def run_module3_readiness_review(
    root: Path,
    config: Module3Config | None = None,
    repro_config: Module3Config | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    data_dir = root / "data"
    model_inputs = load_model_inputs(data_dir)

    readiness_dir = root / "outputs" / "module3"
    primary_config = config or Module3Config.readiness_defaults(
        output_dir=readiness_dir / "readiness_primary"
    )
    repeat_config = Module3Config(
        **{
            **primary_config.__dict__,
            "output_dir": readiness_dir / "readiness_repeat",
            "resume": False,
        }
    )
    serial_small_config = repro_config or _module3_small_repro_config(
        readiness_dir / "readiness_repro_workers1",
        workers=1,
    )
    parallel_small_config = Module3Config(
        **{
            **serial_small_config.__dict__,
            "workers": 2,
            "output_dir": readiness_dir / "readiness_repro_workers2",
            "resume": False,
        }
    )
    resume_stage_a_config = Module3Config(
        **{
            **serial_small_config.__dict__,
            "output_dir": readiness_dir / "readiness_resume_stage_a",
            "resume": False,
        }
    )
    resume_full_config = Module3Config(
        **{
            **serial_small_config.__dict__,
            "output_dir": readiness_dir / "readiness_resume_stage_a",
            "resume": True,
        }
    )
    clean_small_config = Module3Config(
        **{
            **serial_small_config.__dict__,
            "output_dir": readiness_dir / "readiness_resume_clean",
            "resume": False,
        }
    )

    for path in [
        primary_config.output_dir,
        repeat_config.output_dir,
        serial_small_config.output_dir,
        parallel_small_config.output_dir,
        resume_stage_a_config.output_dir,
        clean_small_config.output_dir,
    ]:
        _fresh_run_dir(path)

    primary_run = run_module3_calibration(model_inputs, primary_config)
    repeat_run = run_module3_calibration(model_inputs, repeat_config)
    serial_small_run = run_module3_calibration(model_inputs, serial_small_config)
    parallel_small_run = run_module3_calibration(model_inputs, parallel_small_config)
    run_module3_calibration_stage(model_inputs, resume_stage_a_config, stage="stage_a")
    resumed_run = run_module3_calibration_stage(model_inputs, resume_full_config, stage="all")
    clean_small_run = run_module3_calibration(model_inputs, clean_small_config)

    family_summary = primary_run.family_summary_table.copy()
    accepted_summary = primary_run.accepted_proposals_table[
        [
            "proposal_id",
            "family_id",
            "proposal_seed",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
        ]
    ].copy()

    sampler_valid_rate_pass = bool((family_summary["stage_a_valid_rate"] >= 0.70).all())

    discrimination_rows = _module3_screen_discrimination_rows(
        primary_run.proposal_summary_table,
        primary_config,
    )
    screen_discrimination_pass = bool(discrimination_rows["pass"].sum() >= 4)

    stage_b_rows = primary_run.proposal_summary_table.loc[
        primary_run.proposal_summary_table["stage_status"].isin({"stage_b_failed", "stage_b_rejected", "accepted"})
    ].copy()
    stochastic_confirmation_finite_pass = bool(
        (not stage_b_rows.empty)
        and np.isfinite(pd.to_numeric(stage_b_rows["stochastic_overall_distance_median"], errors="coerce")).all()
        and np.isfinite(pd.to_numeric(stage_b_rows["stochastic_historical_core_distance_median"], errors="coerce")).all()
        and np.isfinite(pd.to_numeric(stage_b_rows["stochastic_intrinsic_baseline_distance_median"], errors="coerce")).all()
        and np.isfinite(pd.to_numeric(stage_b_rows["stochastic_historical_core_distance_iqr"], errors="coerce")).all()
    )

    rank_rows = _module3_rank_consistency_rows(primary_run.proposal_summary_table, primary_config.families)
    rank_consistency_pass = bool(rank_rows["pass"].sum() >= 4)

    accepted_set_nonempty_pass = bool(
        (not accepted_summary.empty)
        and _module3_accepted_targets_scored(accepted_summary, primary_run.target_scores_table)
    )

    repeat_ids_match = _accepted_id_tuple(primary_run.accepted_proposals_table) == _accepted_id_tuple(
        repeat_run.accepted_proposals_table
    )
    worker_ids_match = _accepted_id_tuple(serial_small_run.accepted_proposals_table) == _accepted_id_tuple(
        parallel_small_run.accepted_proposals_table
    )
    resume_ids_match = _accepted_id_tuple(resumed_run.accepted_proposals_table) == _accepted_id_tuple(
        clean_small_run.accepted_proposals_table
    )
    reproducibility_pass = bool(repeat_ids_match and worker_ids_match and resume_ids_match)

    gates = {
        "sampler_valid_rate_pass": sampler_valid_rate_pass,
        "screen_discrimination_pass": screen_discrimination_pass,
        "stochastic_confirmation_finite_pass": stochastic_confirmation_finite_pass,
        "rank_consistency_pass": rank_consistency_pass,
        "accepted_set_nonempty_pass": accepted_set_nonempty_pass,
        "reproducibility_pass": reproducibility_pass,
    }
    gates["full_ready_for_module4"] = all(gates.values())
    gates["needs_module_3_5"] = not gates["full_ready_for_module4"]

    evaluation = {
        "gates": gates,
        "metrics": {
            "accepted_count": int(len(accepted_summary)),
            "same_seed_same_worker_identical": repeat_ids_match,
            "workers1_vs_workers2_identical": worker_ids_match,
            "resume_matches_clean_run": resume_ids_match,
        },
        "screen_discrimination": discrimination_rows,
        "rank_consistency": rank_rows,
        "primary_run": primary_run,
    }
    return family_summary, accepted_summary, evaluation


def render_module3_readiness_review(
    family_summary: pd.DataFrame,
    accepted_summary: pd.DataFrame,
    evaluation: dict[str, Any],
) -> str:
    gates = evaluation["gates"]
    metrics = evaluation["metrics"]
    discrimination_rows = evaluation["screen_discrimination"].to_dict(orient="records")
    rank_rows = evaluation["rank_consistency"].to_dict(orient="records")
    family_rows = family_summary[
        [
            "family_id",
            "stage_a_valid_rate",
            "stage_a_retained",
            "stage_b_valid",
            "final_accepted",
            "final_acceptance_rate",
        ]
    ].to_dict(orient="records")
    accepted_rows = accepted_summary.to_dict(orient="records")
    gate_rows = [{"gate": key, "status": value} for key, value in gates.items()]
    metric_rows = [{"metric": key, "value": value} for key, value in metrics.items()]

    lines = [
        "# Module 3 Readiness Review",
        "",
        "## Summary",
        "",
        (
            "Module 3 adds the first full two-stage ABC/history-matching calibration harness "
            "on top of the validated latent kernel and the Module 2.5 bundle scorer."
        ),
        (
            "Stage A screens equal proposal budgets across all five hypothesis families using "
            "deterministic scenario bundles, while Stage B confirms retained proposals against "
            "stochastic historical replicates with deterministic baselines."
        ),
        "",
        "## Acceptance Gates",
        "",
        _markdown_table(gate_rows, ["gate", "status"]),
        "",
        "## Family Summary",
        "",
        _markdown_table(
            family_rows,
            [
                "family_id",
                "stage_a_valid_rate",
                "stage_a_retained",
                "stage_b_valid",
                "final_accepted",
                "final_acceptance_rate",
            ],
        ),
        "",
        "## Screen Discrimination",
        "",
        _markdown_table(discrimination_rows, ["family_id", "retained_median", "rejected_median", "pass"]),
        "",
        "## Rank Consistency",
        "",
        _markdown_table(rank_rows, ["family_id", "spearman_rank_correlation", "pass"]),
        "",
        "## Reproducibility Checks",
        "",
        _markdown_table(metric_rows, ["metric", "value"]),
        "",
        "## Accepted Proposals",
        "",
    ]

    if accepted_rows:
        lines.append(
            _markdown_table(
                accepted_rows,
                [
                    "proposal_id",
                    "family_id",
                    "proposal_seed",
                    "stochastic_overall_distance_median",
                    "stochastic_historical_core_distance_median",
                    "stochastic_intrinsic_baseline_distance_median",
                    "stochastic_historical_core_distance_iqr",
                ],
            )
        )
    else:
        lines.append("No accepted proposals were retained in the readiness run.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )

    if gates["full_ready_for_module4"]:
        lines.extend(
            [
                "All Module 3 readiness gates passed.",
                "The retained-sample calibration harness is ready to support Module 4 posterior summaries and counterfactual analysis.",
            ]
        )
    else:
        lines.extend(
            [
                "Module 4 should not start yet.",
                "The correct next step is Module 3.5 because at least one calibration-harness readiness gate failed.",
            ]
        )

    lines.extend(
        [
            "",
            "## Module 3.5 Trigger",
            "",
            "- Trigger a sampler/constraint realignment pass if valid-rate failures or pre-simulation proposal failures dominate.",
            "- Trigger a Stage A to Stage B handoff refinement pass if rank consistency is weak or stochastic confirmation is numerically unstable.",
            "- Trigger a reproducibility repair pass if accepted proposal ids differ under the same seed or across worker counts.",
            "",
            "## Artifacts",
            "",
            "- `data/module3_readiness_family_summary.csv`",
            "- `data/module3_readiness_accepted_summary.csv`",
            "- `docs/module3_readiness_review.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_module3_readiness_bundle(root: Path, output_root: Path | None = None) -> dict[str, Any]:
    data_dir = root / "data"
    target_root = output_root if output_root is not None else root
    output_data_dir = target_root / "data"
    docs_dir = target_root / "docs"
    family_summary, accepted_summary, evaluation = run_module3_readiness_review(root)

    output_data_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    family_path = output_data_dir / "module3_readiness_family_summary.csv"
    accepted_path = output_data_dir / "module3_readiness_accepted_summary.csv"
    review_path = docs_dir / "module3_readiness_review.md"

    family_summary.to_csv(family_path, index=False)
    accepted_summary.to_csv(accepted_path, index=False)
    review_path.write_text(
        render_module3_readiness_review(family_summary, accepted_summary, evaluation),
        encoding="utf-8",
    )

    return {
        "family_summary": family_path,
        "accepted_summary": accepted_path,
        "review_doc": review_path,
        "full_ready_for_module4": evaluation["gates"]["full_ready_for_module4"],
        "needs_module_3_5": evaluation["gates"]["needs_module_3_5"],
    }


STAGE_B_FINAL_STATUSES = {"stage_b_rejected", "accepted"}


def _valid_stage_b_proposals(proposal_summary: pd.DataFrame) -> pd.DataFrame:
    valid = proposal_summary.loc[proposal_summary["stage_status"].isin(STAGE_B_FINAL_STATUSES)].copy()
    valid["stochastic_overall_distance_median"] = pd.to_numeric(
        valid["stochastic_overall_distance_median"],
        errors="coerce",
    )
    return valid.loc[np.isfinite(valid["stochastic_overall_distance_median"])].copy()


def _module3_5_sampler_failure_rows(proposal_summary: pd.DataFrame) -> pd.DataFrame:
    family_draws = proposal_summary.groupby("family_id").size().rename("family_draws").reset_index()
    failures = proposal_summary.loc[
        proposal_summary["stage_status"].isin({"sampling_failure", "constraint_failure", "stage_a_failed"})
    ].copy()
    if failures.empty:
        return pd.DataFrame(
            columns=["family_id", "stage_status", "failure_reason", "failure_count", "family_draws", "failure_rate"]
        )

    grouped = (
        failures.assign(failure_reason=failures["failure_reason"].fillna(""))
        .groupby(["family_id", "stage_status", "failure_reason"], as_index=False)
        .size()
        .rename(columns={"size": "failure_count"})
        .merge(family_draws, on="family_id", how="left")
    )
    grouped["failure_rate"] = grouped["failure_count"] / grouped["family_draws"]
    return grouped.sort_values(["family_id", "failure_count"], ascending=[True, False]).reset_index(drop=True)


def _module3_5_stage_b_frontier(proposal_summary: pd.DataFrame) -> pd.DataFrame:
    valid = _valid_stage_b_proposals(proposal_summary)
    if valid.empty:
        return pd.DataFrame()
    frontier = valid.sort_values(
        [
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
            "proposal_id",
        ]
    ).reset_index(drop=True)
    frontier["global_stage_b_rank"] = np.arange(1, len(frontier) + 1)
    return frontier[
        [
            "global_stage_b_rank",
            "proposal_id",
            "family_id",
            "stage_status",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
            "accepted_final",
        ]
    ].copy()


def _module3_5_family_best_rows(stage_b_frontier: pd.DataFrame) -> pd.DataFrame:
    if stage_b_frontier.empty:
        return pd.DataFrame()
    return (
        stage_b_frontier.sort_values("global_stage_b_rank")
        .groupby("family_id", as_index=False)
        .head(1)
        .sort_values("global_stage_b_rank")
        .reset_index(drop=True)
    )


def _module3_5_proposal_target_medians(target_scores: pd.DataFrame) -> pd.DataFrame:
    stage_b = target_scores.loc[target_scores["stage"] == "stage_b"].copy()
    if stage_b.empty:
        return pd.DataFrame(columns=["proposal_id", "family_id", "target_id", "median_weighted_penalty"])
    stage_b["weighted_penalty"] = pd.to_numeric(stage_b["weighted_penalty"], errors="coerce")
    return (
        stage_b.groupby(["proposal_id", "family_id", "target_id"], as_index=False)["weighted_penalty"]
        .median()
        .rename(columns={"weighted_penalty": "median_weighted_penalty"})
        .sort_values(["family_id", "proposal_id", "target_id"])
        .reset_index(drop=True)
    )


def _module3_5_target_leverage_rows(
    proposal_target_medians: pd.DataFrame,
    proposal_summary: pd.DataFrame,
    model_inputs: ModelInputs,
) -> pd.DataFrame:
    valid_ids = set(_valid_stage_b_proposals(proposal_summary)["proposal_id"].astype(str))
    target_medians = proposal_target_medians.loc[
        proposal_target_medians["proposal_id"].astype(str).isin(valid_ids)
    ].copy()
    if target_medians.empty:
        return pd.DataFrame()

    family_distance = (
        _valid_stage_b_proposals(proposal_summary)
        .groupby("family_id", as_index=False)["stochastic_overall_distance_median"]
        .median()
        .rename(columns={"stochastic_overall_distance_median": "family_median_stage_b_distance"})
    )
    leverage = (
        target_medians.groupby(["family_id", "target_id"], as_index=False)["median_weighted_penalty"]
        .median()
        .merge(family_distance, on="family_id", how="left")
    )
    leverage["target_share_of_family_distance"] = (
        leverage["median_weighted_penalty"] / leverage["family_median_stage_b_distance"]
    )

    target_meta = model_inputs.calibration_targets[
        ["target_id", "target_group", "comparison_type", "priority_weight"]
    ].copy()
    leverage = leverage.merge(target_meta, on="target_id", how="left")
    return leverage[
        [
            "family_id",
            "target_id",
            "target_group",
            "comparison_type",
            "priority_weight",
            "median_weighted_penalty",
            "family_median_stage_b_distance",
            "target_share_of_family_distance",
        ]
    ].sort_values(["family_id", "median_weighted_penalty"], ascending=[True, False]).reset_index(drop=True)


def _module3_5_accepted_target_penalties(
    proposal_target_medians: pd.DataFrame,
    accepted_summary: pd.DataFrame,
    model_inputs: ModelInputs,
) -> pd.DataFrame:
    accepted_ids = set(accepted_summary["proposal_id"].astype(str)) if not accepted_summary.empty else set()
    accepted = proposal_target_medians.loc[proposal_target_medians["proposal_id"].astype(str).isin(accepted_ids)].copy()
    target_meta = model_inputs.calibration_targets[
        ["target_id", "target_group", "comparison_type", "priority_weight"]
    ].copy()
    if accepted.empty:
        return pd.DataFrame(columns=[*target_meta.columns, "accepted_median_weighted_penalty"])
    rows = (
        accepted.groupby("target_id", as_index=False)["median_weighted_penalty"]
        .median()
        .rename(columns={"median_weighted_penalty": "accepted_median_weighted_penalty"})
        .merge(target_meta, on="target_id", how="left")
    )
    return rows[
        [
            "target_id",
            "target_group",
            "comparison_type",
            "priority_weight",
            "accepted_median_weighted_penalty",
        ]
    ].sort_values("accepted_median_weighted_penalty", ascending=False).reset_index(drop=True)


def _module3_5_best_proposal_target_penalties(
    proposal_target_medians: pd.DataFrame,
    family_best_rows: pd.DataFrame,
) -> pd.DataFrame:
    if proposal_target_medians.empty or family_best_rows.empty:
        return pd.DataFrame()
    best = family_best_rows[["family_id", "proposal_id", "global_stage_b_rank"]].copy()
    rows = proposal_target_medians.merge(best, on=["family_id", "proposal_id"], how="inner")
    return rows.sort_values(
        ["global_stage_b_rank", "median_weighted_penalty"],
        ascending=[True, False],
    ).reset_index(drop=True)


def _module3_5_target_omission_rows(
    proposal_target_medians: pd.DataFrame,
    proposal_summary: pd.DataFrame,
) -> pd.DataFrame:
    valid = _valid_stage_b_proposals(proposal_summary)[["proposal_id", "family_id"]].copy()
    if valid.empty or proposal_target_medians.empty:
        return pd.DataFrame(
            columns=[
                "omission_label",
                "omitted_target_ids",
                "family_id",
                "best_proposal_id",
                "adjusted_median_target_sum",
                "family_rank",
                "delta_from_winning_family",
            ]
        )

    proposal_targets = proposal_target_medians.merge(valid, on=["proposal_id", "family_id"], how="inner")
    target_ids = sorted(proposal_targets["target_id"].astype(str).unique())
    omission_specs: list[tuple[str, tuple[str, ...]]] = [
        ("none", ()),
        *[(target_id, (target_id,)) for target_id in target_ids],
        ("late_terminal_block", ("CT007", "CT009", "CT010")),
        ("causal_mechanism_block", ("CT004", "CT005")),
    ]

    rows: list[dict[str, Any]] = []
    for label, omitted_targets in omission_specs:
        keep = proposal_targets.loc[~proposal_targets["target_id"].isin(omitted_targets)].copy()
        proposal_totals = (
            keep.groupby(["proposal_id", "family_id"], as_index=False)["median_weighted_penalty"]
            .sum()
            .rename(columns={"median_weighted_penalty": "adjusted_median_target_sum"})
        )
        if proposal_totals.empty:
            continue
        best_by_family = (
            proposal_totals.sort_values(["adjusted_median_target_sum", "proposal_id"])
            .groupby("family_id", as_index=False)
            .head(1)
            .sort_values(["adjusted_median_target_sum", "family_id"])
            .reset_index(drop=True)
        )
        best_by_family["family_rank"] = np.arange(1, len(best_by_family) + 1)
        winning_distance = float(best_by_family["adjusted_median_target_sum"].iloc[0])
        for row in best_by_family.to_dict(orient="records"):
            rows.append(
                {
                    "omission_label": label,
                    "omitted_target_ids": ",".join(omitted_targets) if omitted_targets else "none",
                    "family_id": row["family_id"],
                    "best_proposal_id": row["proposal_id"],
                    "adjusted_median_target_sum": float(row["adjusted_median_target_sum"]),
                    "family_rank": int(row["family_rank"]),
                    "delta_from_winning_family": float(row["adjusted_median_target_sum"] - winning_distance),
                }
            )
    return pd.DataFrame(rows)


def run_module3_5_diagnostic_review(
    root: Path,
    config: Module3Config | None = None,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    data_dir = root / "data"
    model_inputs = load_model_inputs(data_dir)
    diagnostic_dir = root / "outputs" / "module3_5"
    diagnostic_config = config or Module3Config.readiness_defaults(
        output_dir=diagnostic_dir / "diagnostic_primary"
    )
    _fresh_run_dir(diagnostic_config.output_dir)

    run = run_module3_calibration(model_inputs, diagnostic_config)
    proposal_summary = run.proposal_summary_table.copy()
    target_scores = run.target_scores_table.copy()
    accepted_summary = run.accepted_proposals_table.copy()

    stage_b_frontier = _module3_5_stage_b_frontier(proposal_summary)
    family_best = _module3_5_family_best_rows(stage_b_frontier)
    proposal_target_medians = _module3_5_proposal_target_medians(target_scores)
    sampler_failures = _module3_5_sampler_failure_rows(proposal_summary)
    target_leverage = _module3_5_target_leverage_rows(
        proposal_target_medians,
        proposal_summary,
        model_inputs,
    )
    accepted_target_penalties = _module3_5_accepted_target_penalties(
        proposal_target_medians,
        accepted_summary,
        model_inputs,
    )
    best_proposal_targets = _module3_5_best_proposal_target_penalties(
        proposal_target_medians,
        family_best,
    )
    target_omission = _module3_5_target_omission_rows(proposal_target_medians, proposal_summary)

    valid_stage_b = _valid_stage_b_proposals(proposal_summary)
    winning_family = (
        str(stage_b_frontier.iloc[0]["family_id"]) if not stage_b_frontier.empty else ""
    )
    omitted_winners = (
        target_omission.loc[target_omission["family_rank"] == 1].copy()
        if "family_rank" in target_omission.columns
        else pd.DataFrame()
    )
    omission_flip_count = int((omitted_winners["family_id"] != winning_family).sum()) if not omitted_winners.empty else 0

    evaluation = {
        "config": {
            "stage_a_draws_per_family": diagnostic_config.stage_a_draws_per_family,
            "stage_a_keep_per_family": diagnostic_config.stage_a_keep_per_family,
            "stage_b_historical_replicates": diagnostic_config.stage_b_historical_replicates,
            "final_acceptance_fraction": diagnostic_config.final_acceptance_fraction,
            "final_acceptance_cap": diagnostic_config.final_acceptance_cap,
            "master_seed": diagnostic_config.master_seed,
            "output_dir": str(diagnostic_config.output_dir),
        },
        "metrics": {
            "stage_b_valid_proposals": int(len(valid_stage_b)),
            "accepted_count": int(len(accepted_summary)),
            "winning_family": winning_family,
            "target_omission_flip_count": omission_flip_count,
        },
        "recommended_next_step": (
            "Reparameterize constrained priors before changing biological target weights."
            if not sampler_failures.empty
            else "Run a larger remote sensitivity sweep before changing biological target weights."
        ),
    }
    tables = {
        "family_summary": run.family_summary_table.copy(),
        "sampler_failures": sampler_failures,
        "stage_b_frontier": stage_b_frontier,
        "family_best_stage_b": family_best,
        "target_leverage": target_leverage,
        "accepted_target_penalties": accepted_target_penalties,
        "best_proposal_target_penalties": best_proposal_targets,
        "target_omission_sensitivity": target_omission,
    }
    return tables, evaluation


def render_module3_5_diagnostic_review(
    tables: dict[str, pd.DataFrame],
    evaluation: dict[str, Any],
) -> str:
    metrics = [{"metric": key, "value": value} for key, value in evaluation["metrics"].items()]
    config_rows = [{"setting": key, "value": value} for key, value in evaluation["config"].items()]

    sampler_rows = tables["sampler_failures"].head(10).to_dict(orient="records")
    family_best_rows = tables["family_best_stage_b"][
        [
            "global_stage_b_rank",
            "proposal_id",
            "family_id",
            "stage_status",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_iqr",
        ]
    ].to_dict(orient="records") if not tables["family_best_stage_b"].empty else []
    accepted_target_rows = tables["accepted_target_penalties"].head(8).to_dict(orient="records")
    best_target_rows = tables["best_proposal_target_penalties"][
        [
            "family_id",
            "proposal_id",
            "target_id",
            "median_weighted_penalty",
        ]
    ].head(30).to_dict(orient="records") if not tables["best_proposal_target_penalties"].empty else []
    omission_table = tables["target_omission_sensitivity"]
    omission_winners = (
        omission_table.loc[omission_table["family_rank"] == 1].copy()
        if "family_rank" in omission_table.columns
        else pd.DataFrame()
    )
    omission_rows = omission_winners[
        [
            "omission_label",
            "omitted_target_ids",
            "family_id",
            "best_proposal_id",
            "adjusted_median_target_sum",
        ]
    ].to_dict(orient="records") if not omission_winners.empty else []

    lines = [
        "# Module 3.5 Diagnostic Review",
        "",
        "## Summary",
        "",
        (
            "Module 3.5 diagnoses why the first ABC/history-matching readiness run is not yet "
            "a sound basis for Module 4 posterior summaries."
        ),
        (
            "It reruns the Module 3 readiness-scale calibration once, then inspects sampler "
            "failures, retained-proposal target leverage, and target-omission family ranking."
        ),
        "",
        "## Run Configuration",
        "",
        _markdown_table(config_rows, ["setting", "value"]),
        "",
        "## Key Metrics",
        "",
        _markdown_table(metrics, ["metric", "value"]),
        "",
        "## Sampler Geometry",
        "",
    ]
    if sampler_rows:
        lines.append(
            _markdown_table(
                sampler_rows,
                ["family_id", "stage_status", "failure_reason", "failure_count", "failure_rate"],
            )
        )
    else:
        lines.append("No pre-simulation sampler or constraint failures were recorded.")

    lines.extend(
        [
            "",
            "## Family Ranking Frontier",
            "",
        ]
    )
    if family_best_rows:
        lines.append(
            _markdown_table(
                family_best_rows,
                [
                    "global_stage_b_rank",
                    "proposal_id",
                    "family_id",
                    "stage_status",
                    "stochastic_overall_distance_median",
                    "stochastic_historical_core_distance_iqr",
                ],
            )
        )
    else:
        lines.append("No valid Stage B proposals were available for ranking.")

    lines.extend(
        [
            "",
            "## Accepted Target Leverage",
            "",
        ]
    )
    if accepted_target_rows:
        lines.append(
            _markdown_table(
                accepted_target_rows,
                [
                    "target_id",
                    "target_group",
                    "comparison_type",
                    "priority_weight",
                    "accepted_median_weighted_penalty",
                ],
            )
        )
    else:
        lines.append("No accepted proposals were available for target-leverage summaries.")

    lines.extend(
        [
            "",
            "## Best Proposal Target Penalties",
            "",
        ]
    )
    if best_target_rows:
        lines.append(
            _markdown_table(
                best_target_rows,
                ["family_id", "proposal_id", "target_id", "median_weighted_penalty"],
            )
        )
    else:
        lines.append("No best-proposal target penalties were available.")

    lines.extend(
        [
            "",
            "## Target Omission Sensitivity",
            "",
        ]
    )
    if omission_rows:
        lines.append(
            _markdown_table(
                omission_rows,
                [
                    "omission_label",
                    "omitted_target_ids",
                    "family_id",
                    "best_proposal_id",
                    "adjusted_median_target_sum",
                ],
            )
        )
    else:
        lines.append("Target omission sensitivity could not be computed.")

    lines.extend(["", "## Interpretation", ""])
    if sampler_rows:
        lines.extend(
            [
                "The immediate blocker is sampler geometry, not numerical instability or reproducibility.",
                (
                    "Independent prior draws frequently violate ordered biological constraints, so a large "
                    "fraction of proposals never reaches simulation. The next code change should therefore "
                    "make those constrained pairs explicit in the sampling parameterisation."
                ),
            ]
        )
    else:
        lines.extend(
            [
                "The constraint-aware sampler removed the pre-simulation validity blocker.",
                (
                    "At this readiness scale the accepted frontier now includes climbing-only, persistent "
                    "joint-cause, and transient perfect-storm proposals, so the earlier climbing-only result "
                    "should not be interpreted as a stable biological conclusion."
                ),
            ]
        )
    lines.extend(
        [
            (
                "Family ranking remains sensitive to the late detection and contraction targets: omitting "
                "`CT007`, `CT010`, or the late-terminal block can move the best retained proposal toward "
                "the persistent joint-cause family."
            ),
            "",
            "## Recommended Next Step",
            "",
            evaluation["recommended_next_step"],
            "",
            "## Artifacts",
            "",
            "- `data/module3_5_family_summary.csv`",
            "- `data/module3_5_sampler_failures.csv`",
            "- `data/module3_5_stage_b_frontier.csv`",
            "- `data/module3_5_family_best_stage_b.csv`",
            "- `data/module3_5_target_leverage.csv`",
            "- `data/module3_5_accepted_target_penalties.csv`",
            "- `data/module3_5_best_proposal_target_penalties.csv`",
            "- `data/module3_5_target_omission_sensitivity.csv`",
            "- `docs/module3_5_diagnostic_review.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_module3_5_diagnostic_bundle(
    root: Path,
    output_root: Path | None = None,
    config: Module3Config | None = None,
) -> dict[str, Any]:
    target_root = output_root if output_root is not None else root
    output_data_dir = target_root / "data"
    docs_dir = target_root / "docs"
    tables, evaluation = run_module3_5_diagnostic_review(root, config=config)

    output_data_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    for name, frame in tables.items():
        path = output_data_dir / f"module3_5_{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path

    review_path = docs_dir / "module3_5_diagnostic_review.md"
    review_path.write_text(render_module3_5_diagnostic_review(tables, evaluation), encoding="utf-8")

    return {
        **paths,
        "review_doc": review_path,
        "winning_family": evaluation["metrics"]["winning_family"],
        "target_omission_flip_count": evaluation["metrics"]["target_omission_flip_count"],
        "recommended_next_step": evaluation["recommended_next_step"],
    }
