from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galaxias_model import (
    ScoringConfig,
    SimulationConfig,
    aggregate_scenario_bundle_scores,
    build_scenario_forcing,
    get_scenario_definition,
    load_model_inputs,
    resolve_family_parameters,
    run_historical_simulation,
    run_scenario_simulation,
    score_family_scenario_bundle,
    score_historical_run,
    score_scenario_run,
    score_target,
)
from galaxias_model.scoring import lower_bound_penalty
from galaxias_model.types import ModelInputs


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FAMILY_IDS = [
    "habitat_only_null",
    "trout_only",
    "climbing_only",
    "persistent_joint_cause",
    "transient_perfect_storm",
]


@pytest.fixture(scope="module")
def model_inputs() -> ModelInputs:
    return load_model_inputs(DATA_DIR)


def _scenario_config(model_inputs: ModelInputs, scenario_id: str, stochastic: bool = False) -> SimulationConfig:
    scenario_definition = get_scenario_definition(model_inputs, scenario_id)
    return SimulationConfig(
        stochastic=stochastic,
        scenario_id=scenario_id,
        scenario_definition=scenario_definition,
        start_year=scenario_definition.start_year,
        end_year=scenario_definition.end_year,
    )


def _run_baseline(
    model_inputs: ModelInputs,
    family_id: str,
    scenario_id: str,
    stochastic: bool = False,
    seed: int = 1,
):
    params = resolve_family_parameters(model_inputs, family_id)
    return run_scenario_simulation(params, family_id, _scenario_config(model_inputs, scenario_id, stochastic), seed=seed)


def _target_row(model_inputs: ModelInputs, target_id: str) -> dict[str, object]:
    assert model_inputs.calibration_targets is not None
    return (
        model_inputs.calibration_targets.loc[model_inputs.calibration_targets["target_id"] == target_id]
        .iloc[0]
        .to_dict()
    )


def _target_details(model_inputs: ModelInputs, target_id: str) -> dict[str, object]:
    assert model_inputs.calibration_target_details is not None
    return model_inputs.calibration_target_details[target_id]


def _synthetic_projection(target_id: str, scenario_id: str, metadata: dict[str, object]):
    return {
        "target_id": target_id,
        "target_group": _target_row(load_model_inputs(DATA_DIR), target_id)["target_group"],
        "comparison_type": _target_row(load_model_inputs(DATA_DIR), target_id)["comparison_type"],
        "scenario_id": scenario_id,
        "evaluation_status": "scored",
        "projected_primary": np.nan,
        "projected_secondary": np.nan,
        "observed_primary": np.nan,
        "observed_secondary": np.nan,
        "projection_metadata": metadata,
        "notes": "",
    }


def test_scenario_definitions_load_and_match_expected_ids(model_inputs: ModelInputs) -> None:
    assert model_inputs.scenario_definitions is not None
    assert set(model_inputs.scenario_definitions) == {"historical_lake", "lake_oberon", "strathgordon"}
    assert get_scenario_definition(model_inputs, "lake_oberon").start_year == 1991
    assert get_scenario_definition(model_inputs, "strathgordon").end_year == 2012


def test_historical_deterministic_summaries_match_module1_5_checkpoint(model_inputs: ModelInputs) -> None:
    rows = []
    for family_id in FAMILY_IDS:
        params = resolve_family_parameters(model_inputs, family_id)
        result = run_historical_simulation(params, family_id, SimulationConfig(stochastic=False), seed=1)
        row = dict(result.summary)
        row["N_total_1965"] = float(result.trajectory_table.loc[result.trajectory_table["year"] == 1965, "N_total"].iloc[0])
        row["N_total_1977"] = float(result.trajectory_table.loc[result.trajectory_table["year"] == 1977, "N_total"].iloc[0])
        row["N_total_2002"] = float(result.trajectory_table.loc[result.trajectory_table["year"] == 2002, "N_total"].iloc[0])
        rows.append(row)
    current = pd.DataFrame(rows).sort_values("family_id").reset_index(drop=True)
    expected = pd.read_csv(DATA_DIR / "module1_5_example_summary.csv").sort_values("family_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(current[expected.columns], expected, check_exact=False, atol=1e-9, rtol=0)


def test_historical_stochastic_summaries_match_module1_5_checkpoint(model_inputs: ModelInputs) -> None:
    rows = []
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    for seed in range(1, 21):
        result = run_historical_simulation(params, "transient_perfect_storm", SimulationConfig(stochastic=True), seed=seed)
        row = dict(result.summary)
        row["present_in_1980"] = int(
            result.trajectory_table.loc[result.trajectory_table["year"] == 1980, "total_present"].iloc[0]
        )
        rows.append(row)
    current = pd.DataFrame(rows).sort_values("seed").reset_index(drop=True)
    expected = pd.read_csv(DATA_DIR / "module1_5_stochastic_summary.csv").sort_values("seed").reset_index(drop=True)
    pd.testing.assert_frame_equal(current[expected.columns], expected, check_exact=False, atol=1e-9, rtol=0)


def test_historical_score_regression_matches_module2_checkpoint(model_inputs: ModelInputs) -> None:
    scoring_config = ScoringConfig()
    default_rows = []
    for family_id in FAMILY_IDS:
        params = resolve_family_parameters(model_inputs, family_id)
        sim_result = run_historical_simulation(params, family_id, SimulationConfig(stochastic=False), seed=1)
        default_rows.append(score_historical_run(sim_result, model_inputs, scoring_config).target_score_table)
    current_default = pd.concat(default_rows, ignore_index=True)
    current_default = current_default.loc[current_default["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])]
    expected_default = pd.read_csv(DATA_DIR / "module2_default_target_scores.csv")
    expected_default = expected_default.loc[expected_default["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])]
    cols = [
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
    pd.testing.assert_frame_equal(
        current_default[cols].sort_values(["family_id", "target_id"]).reset_index(drop=True),
        expected_default[cols].sort_values(["family_id", "target_id"]).reset_index(drop=True),
        check_exact=False,
        atol=1e-9,
        rtol=0,
    )

    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    transient_rows = []
    for seed in range(1, 21):
        sim_result = run_historical_simulation(params, "transient_perfect_storm", SimulationConfig(stochastic=True), seed=seed)
        transient_rows.append(score_historical_run(sim_result, model_inputs, scoring_config).target_score_table)
    current_transient = pd.concat(transient_rows, ignore_index=True)
    current_transient = current_transient.loc[current_transient["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])]
    expected_transient = pd.read_csv(DATA_DIR / "module2_transient_replicate_scores.csv")
    expected_transient = expected_transient.loc[expected_transient["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])]
    pd.testing.assert_frame_equal(
        current_transient[cols].sort_values(["seed", "target_id"]).reset_index(drop=True),
        expected_transient[cols].sort_values(["seed", "target_id"]).reset_index(drop=True),
        check_exact=False,
        atol=1e-9,
        rtol=0,
    )


def test_scenario_definition_forcing_matches_expected_founders_and_spawn_habitat(model_inputs: ModelInputs) -> None:
    params = resolve_family_parameters(model_inputs, "habitat_only_null")
    oberon = get_scenario_definition(model_inputs, "lake_oberon")
    oberon_forcing = build_scenario_forcing(oberon, list(range(oberon.start_year, oberon.end_year + 1)), params).table
    nonzero_oberon = oberon_forcing.loc[oberon_forcing["founder_addition_A_L"] > 0, ["year", "founder_addition_A_L"]]
    assert nonzero_oberon.to_dict(orient="records") == [
        {"year": 1991, "founder_addition_A_L": 31.0},
        {"year": 1997, "founder_addition_A_L": 3.0},
    ]
    assert (oberon_forcing["spawn_habitat_multiplier"] == 1.0).all()

    strath = get_scenario_definition(model_inputs, "strathgordon")
    strath_forcing = build_scenario_forcing(strath, list(range(strath.start_year, strath.end_year + 1)), params).table
    nonzero_strath = strath_forcing.loc[strath_forcing["founder_addition_A_L"] > 0, ["year", "founder_addition_A_L"]]
    assert nonzero_strath.to_dict(orient="records") == [
        {"year": 2001, "founder_addition_A_L": 52.0},
        {"year": 2002, "founder_addition_A_L": 22.0},
        {"year": 2005, "founder_addition_A_L": 117.0},
        {"year": 2006, "founder_addition_A_L": 53.0},
        {"year": 2007, "founder_addition_A_L": 109.0},
    ]
    assert (strath_forcing.loc[strath_forcing["year"] <= 2007, "spawn_habitat_multiplier"] == 0.0).all()
    assert (strath_forcing.loc[strath_forcing["year"] >= 2008, "spawn_habitat_multiplier"] == 1.0).all()


def test_historical_forcing_honors_scenario_spawn_habitat_schedule(model_inputs: ModelInputs) -> None:
    params = resolve_family_parameters(model_inputs, "habitat_only_null")
    historical = get_scenario_definition(model_inputs, "historical_lake")
    custom_spawn = {
        year: (0.5 if year in {1977, 1978} else 1.0)
        for year in range(historical.start_year, historical.end_year + 1)
    }
    modified = replace(historical, spawn_habitat_by_year=custom_spawn)
    forcing = build_scenario_forcing(modified, list(range(modified.start_year, modified.end_year + 1)), params).table

    assert float(forcing.loc[forcing["year"] == 1976, "spawn_habitat_multiplier"].iloc[0]) == 1.0
    assert float(forcing.loc[forcing["year"] == 1977, "spawn_habitat_multiplier"].iloc[0]) == 0.5
    assert float(forcing.loc[forcing["year"] == 1978, "spawn_habitat_multiplier"].iloc[0]) == 0.5


def test_record_forcing_false_omits_forcing_table_but_keeps_trajectory(model_inputs: ModelInputs) -> None:
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    result = run_historical_simulation(
        params,
        "transient_perfect_storm",
        SimulationConfig(stochastic=False, record_forcing=False),
        seed=1,
    )

    assert result.forcing_table.empty
    assert not result.trajectory_table.empty
    assert result.summary["family_id"] == "transient_perfect_storm"


def test_baseline_kernel_invariants_hold(model_inputs: ModelInputs) -> None:
    oberon = _run_baseline(model_inputs, "habitat_only_null", "lake_oberon", stochastic=False, seed=1)
    strath = _run_baseline(model_inputs, "habitat_only_null", "strathgordon", stochastic=False, seed=1)
    for result in [oberon, strath]:
        assert (result.trajectory_table[["J_L", "A_L", "J_R", "A_R", "N_total"]] >= 0).all().all()
        assert (result.trajectory_table[["T", "P", "C_L", "C_R", "U"]] == 0).all().all()
        assert (result.forcing_table["H"] == 0).all()
    assert (result.forcing_table["stocking_input"] == 0).all()
    assert oberon.trajectory_table["year"].min() == 1991
    assert strath.trajectory_table["year"].min() == 2001
    assert float(oberon.forcing_table.loc[oberon.forcing_table["year"] == 1991, "founder_addition_A_L"].iloc[0]) == 31.0
    assert float(strath.forcing_table.loc[strath.forcing_table["year"] == 2001, "founder_addition_A_L"].iloc[0]) == 52.0
    assert float(oberon.trajectory_table.loc[oberon.trajectory_table["year"] == 1991, "N_total"].iloc[0]) > 0.0
    assert float(strath.trajectory_table.loc[strath.trajectory_table["year"] == 2001, "N_total"].iloc[0]) > 0.0


def test_baseline_deterministic_trajectories_are_identical_across_families(model_inputs: ModelInputs) -> None:
    for scenario_id in ["lake_oberon", "strathgordon"]:
        reference = _run_baseline(model_inputs, "habitat_only_null", scenario_id, stochastic=False, seed=1).trajectory_table
        for family_id in FAMILY_IDS[1:]:
            comparison = _run_baseline(model_inputs, family_id, scenario_id, stochastic=False, seed=1).trajectory_table
            pd.testing.assert_frame_equal(
                reference.drop(columns=["family_id", "seed"]),
                comparison.drop(columns=["family_id", "seed"]),
            )


def test_ct011_and_ct012_score_on_matching_scenarios(model_inputs: ModelInputs) -> None:
    oberon_result = _run_baseline(model_inputs, "habitat_only_null", "lake_oberon", stochastic=False, seed=1)
    strath_result = _run_baseline(model_inputs, "habitat_only_null", "strathgordon", stochastic=False, seed=1)
    oberon_scores = score_scenario_run(oberon_result, model_inputs, ScoringConfig()).target_score_table
    strath_scores = score_scenario_run(strath_result, model_inputs, ScoringConfig()).target_score_table

    assert oberon_scores.loc[oberon_scores["target_id"] == "CT011", "evaluation_status"].iloc[0] == "scored"
    assert strath_scores.loc[strath_scores["target_id"] == "CT012", "evaluation_status"].iloc[0] == "scored"
    assert oberon_scores.loc[oberon_scores["target_id"] == "CT012", "evaluation_status"].iloc[0] == "deferred_requires_scenario"
    assert strath_scores.loc[strath_scores["target_id"] == "CT011", "evaluation_status"].iloc[0] == "deferred_requires_scenario"


def test_bundle_scoring_returns_all_targets_scored_and_finite(model_inputs: ModelInputs) -> None:
    family_id = "transient_perfect_storm"
    params = resolve_family_parameters(model_inputs, family_id)
    bundle = score_family_scenario_bundle(
        {
            "historical_lake": run_historical_simulation(params, family_id, SimulationConfig(stochastic=False), seed=1),
            "lake_oberon": _run_baseline(model_inputs, family_id, "lake_oberon", stochastic=False, seed=1),
            "strathgordon": _run_baseline(model_inputs, family_id, "strathgordon", stochastic=False, seed=1),
        },
        model_inputs,
        ScoringConfig(),
    )
    assert len(bundle.bundle_target_score_table) == 12
    assert (bundle.bundle_target_score_table["evaluation_status"] == "scored").all()
    assert bundle.summary["missing_scenarios"] == []
    assert bundle.summary["overall_distance"] is not None
    assert bundle.summary["full_ready_for_module3"] is True


def test_ct011_and_ct012_monotonicity(model_inputs: ModelInputs) -> None:
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    ct011_better = score_target(
        _target_row(model_inputs, "CT011"),
        _target_details(model_inputs, "CT011"),
        _synthetic_projection(
            "CT011",
            "lake_oberon",
            {
                "founder_total": 34.0,
                "first_year_juveniles_present": 1997,
                "max_adults_2001_2004": 600.0,
                "total_2012": 300.0,
                "growth_ratio_2012_vs_founders": 40.0,
            },
        ),
        params,
    )
    ct011_worse = score_target(
        _target_row(model_inputs, "CT011"),
        _target_details(model_inputs, "CT011"),
        _synthetic_projection(
            "CT011",
            "lake_oberon",
            {
                "founder_total": 34.0,
                "first_year_juveniles_present": 2002,
                "max_adults_2001_2004": 100.0,
                "total_2012": 60.0,
                "growth_ratio_2012_vs_founders": 10.0,
            },
        ),
        params,
    )
    assert float(ct011_better["raw_penalty"]) < float(ct011_worse["raw_penalty"])

    ct012_better = score_target(
        _target_row(model_inputs, "CT012"),
        _target_details(model_inputs, "CT012"),
        _synthetic_projection(
            "CT012",
            "strathgordon",
            {
                "any_juveniles_2001_2007": False,
                "first_year_juveniles_present": 2008,
                "juveniles_2008": 10.0,
                "total_2012": 300.0,
                "juveniles_2012": 35.0,
            },
        ),
        params,
    )
    ct012_worse = score_target(
        _target_row(model_inputs, "CT012"),
        _target_details(model_inputs, "CT012"),
        _synthetic_projection(
            "CT012",
            "strathgordon",
            {
                "any_juveniles_2001_2007": True,
                "first_year_juveniles_present": 2006,
                "juveniles_2008": 1.0,
                "total_2012": 50.0,
                "juveniles_2012": 2.0,
            },
        ),
        params,
    )
    assert float(ct012_better["raw_penalty"]) < float(ct012_worse["raw_penalty"])
    assert lower_bound_penalty(5, 8, 4) == pytest.approx(0.75)


def test_aggregate_bundle_scores_are_finite(model_inputs: ModelInputs) -> None:
    bundles = [
        _bundle
        for _bundle in [
            score_family_scenario_bundle(
                {
                    "historical_lake": run_historical_simulation(
                        resolve_family_parameters(model_inputs, "transient_perfect_storm"),
                        "transient_perfect_storm",
                        SimulationConfig(stochastic=True),
                        seed=seed,
                    ),
                    "lake_oberon": _run_baseline(model_inputs, "transient_perfect_storm", "lake_oberon", stochastic=False, seed=1),
                    "strathgordon": _run_baseline(model_inputs, "transient_perfect_storm", "strathgordon", stochastic=False, seed=1),
                },
                model_inputs,
                ScoringConfig(),
            )
            for seed in range(1, 6)
        ]
    ]
    aggregate = aggregate_scenario_bundle_scores(bundles, ScoringConfig())
    assert np.isfinite(float(aggregate.summary["historical_core_distance_median"]))
    assert np.isfinite(float(aggregate.summary["historical_core_distance_iqr"]))
    assert aggregate.summary["full_ready_for_module3"] is True
