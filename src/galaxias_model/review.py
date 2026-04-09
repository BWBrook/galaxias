from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from galaxias_model.io import load_model_inputs, resolve_family_parameters
from galaxias_model.scoring import aggregate_replicate_scores, score_historical_run, score_target
from galaxias_model.simulation import run_historical_simulation
from galaxias_model.types import ModelInputs, ScoringConfig, SimulationConfig


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


def write_module1_5_review_bundle(root: Path) -> dict[str, Any]:
    data_dir = root / "data"
    docs_dir = root / "docs"
    model_inputs = load_model_inputs(data_dir)
    deterministic, stochastic, evaluation = run_module1_5_review(model_inputs)

    example_path = data_dir / "module1_5_example_summary.csv"
    stochastic_path = data_dir / "module1_5_stochastic_summary.csv"
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


def write_module2_readiness_bundle(root: Path) -> dict[str, Any]:
    data_dir = root / "data"
    docs_dir = root / "docs"
    model_inputs = load_model_inputs(data_dir)
    default_target_scores, transient_replicate_scores, evaluation = run_module2_readiness_review(model_inputs)

    default_path = data_dir / "module2_default_target_scores.csv"
    transient_path = data_dir / "module2_transient_replicate_scores.csv"
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
