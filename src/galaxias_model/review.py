from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from galaxias_model.io import load_model_inputs, resolve_family_parameters
from galaxias_model.simulation import run_historical_simulation
from galaxias_model.types import ModelInputs, SimulationConfig


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
