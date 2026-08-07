from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galaxias_model import (
    ScoringConfig,
    SimulationConfig,
    aggregate_replicate_scores,
    load_model_inputs,
    project_target,
    resolve_family_parameters,
    run_historical_simulation,
    score_historical_run,
    score_target,
)
from galaxias_model.scoring import count_deviance, count_penalty, dominance_penalty, range_penalty, upper_bound_penalty
from galaxias_model.types import ModelInputs


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
TARGET_IDS = [f"CT{i:03d}" for i in range(1, 13)]


@pytest.fixture(scope="module")
def model_inputs() -> ModelInputs:
    return load_model_inputs(DATA_DIR)


@pytest.fixture(scope="module")
def transient_deterministic_result(model_inputs: ModelInputs):
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    return run_historical_simulation(params, "transient_perfect_storm", SimulationConfig(stochastic=False), seed=1)


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


def _synthetic_projection(target_id: str, projected_primary: float, projected_secondary: float, metadata: dict[str, object]):
    return {
        "target_id": target_id,
        "target_group": "historical_core",
        "comparison_type": _target_row(load_model_inputs(DATA_DIR), target_id)["comparison_type"],
        "scenario_id": "historical_lake",
        "evaluation_status": "scored",
        "projected_primary": projected_primary,
        "projected_secondary": projected_secondary,
        "observed_primary": np.nan,
        "observed_secondary": np.nan,
        "projection_metadata": metadata,
        "notes": "",
    }


def test_model_inputs_load_target_details(model_inputs: ModelInputs) -> None:
    assert model_inputs.calibration_target_details is not None
    assert set(model_inputs.calibration_target_details) == set(TARGET_IDS)


@pytest.mark.parametrize("target_id", TARGET_IDS)
def test_project_and_score_each_comparison_type(
    model_inputs: ModelInputs,
    transient_deterministic_result,
    target_id: str,
) -> None:
    projection = project_target(target_id, transient_deterministic_result, model_inputs)
    target_row = _target_row(model_inputs, target_id)
    params = transient_deterministic_result.resolved_parameters
    score = score_target(target_row, _target_details(model_inputs, target_id), projection, params)

    assert score["comparison_type"] == target_row["comparison_type"]
    if target_id in {"CT011", "CT012"}:
        assert score["evaluation_status"] == "deferred_requires_scenario"
        assert pd.isna(score["raw_penalty"])
    else:
        assert score["evaluation_status"] == "scored"
        assert np.isfinite(float(score["raw_penalty"]))
        assert np.isfinite(float(score["weighted_penalty"]))


def test_common_penalty_helpers() -> None:
    assert count_deviance(0, 5) == pytest.approx(10.0)
    assert count_penalty(68, 68, 1.2) == pytest.approx(0.0)
    assert range_penalty(5, 3, 7) == pytest.approx(0.0)
    assert range_penalty(1, 3, 7) == pytest.approx(0.5)
    assert upper_bound_penalty(8, 10, 15) == pytest.approx(0.0)
    assert upper_bound_penalty(25, 10, 15) == pytest.approx(1.0)
    assert dominance_penalty(0.5, "pedder_dominant", 0.3) == pytest.approx(0.0)
    assert dominance_penalty(2.0, "pedder_dominant", 0.3) > 0
    assert dominance_penalty(2.0, "climbing_dominant", 0.3) == pytest.approx(0.0)


def test_scoring_does_not_require_target_text_or_notes(
    model_inputs: ModelInputs,
    transient_deterministic_result,
) -> None:
    target_id = "CT002"
    target_row = _target_row(model_inputs, target_id)
    target_row.pop("target_value_text", None)
    target_row.pop("notes", None)
    projection = project_target(target_id, transient_deterministic_result, model_inputs)
    score = score_target(target_row, _target_details(model_inputs, target_id), projection, transient_deterministic_result.resolved_parameters)
    assert score["evaluation_status"] == "scored"


def test_all_families_score_deterministically_against_historical_core(model_inputs: ModelInputs) -> None:
    scoring_config = ScoringConfig()
    for family_id in [
        "habitat_only_null",
        "trout_only",
        "climbing_only",
        "persistent_joint_cause",
        "transient_perfect_storm",
    ]:
        params = resolve_family_parameters(model_inputs, family_id)
        sim_result = run_historical_simulation(params, family_id, SimulationConfig(stochastic=False), seed=1)
        scoring_result = score_historical_run(sim_result, model_inputs, scoring_config)
        core = scoring_result.target_score_table.loc[scoring_result.target_score_table["target_id"].isin([f"CT{i:03d}" for i in range(1, 11)])]
        assert (core["evaluation_status"] == "scored").all()
        assert np.isfinite(core["raw_penalty"].astype(float)).all()


def test_ct004_and_ct005_discriminate_expected_families(model_inputs: ModelInputs) -> None:
    scoring_config = ScoringConfig()
    rows = []
    for family_id in [
        "habitat_only_null",
        "trout_only",
        "climbing_only",
        "persistent_joint_cause",
        "transient_perfect_storm",
    ]:
        params = resolve_family_parameters(model_inputs, family_id)
        sim_result = run_historical_simulation(params, family_id, SimulationConfig(stochastic=False), seed=1)
        rows.append(score_historical_run(sim_result, model_inputs, scoring_config).target_score_table)
    table = pd.concat(rows, ignore_index=True)

    ct004 = table.loc[table["target_id"] == "CT004"]
    trout_active = ct004.loc[ct004["family_id"].isin(["trout_only", "persistent_joint_cause", "transient_perfect_storm"]), "raw_penalty"].mean()
    trout_inactive = ct004.loc[ct004["family_id"].isin(["habitat_only_null", "climbing_only"]), "raw_penalty"].mean()
    assert float(trout_active) < float(trout_inactive)

    ct005 = table.loc[table["target_id"] == "CT005"]
    climbing_active = ct005.loc[ct005["family_id"].isin(["climbing_only", "persistent_joint_cause", "transient_perfect_storm"]), "raw_penalty"].mean()
    climbing_inactive = ct005.loc[ct005["family_id"].isin(["habitat_only_null", "trout_only"]), "raw_penalty"].mean()
    assert float(climbing_active) < float(climbing_inactive)


@pytest.mark.parametrize(
    ("target_id", "better_projection", "worse_projection"),
    [
        (
            "CT006",
            lambda: _synthetic_projection(
                "CT006",
                12.0,
                1.0,
                {"lake_present_mean": 0.0, "refuge_present_mean": 1.0, "expected_refuge_capture_mean": 12.0},
            ),
            lambda: _synthetic_projection(
                "CT006",
                40.0,
                0.2,
                {"lake_present_mean": 1.0, "refuge_present_mean": 0.2, "expected_refuge_capture_mean": 40.0},
            ),
        ),
        (
            "CT007",
            lambda: _synthetic_projection(
                "CT007",
                5.0,
                68.0,
                {"expected_occupied_sites": 5.0, "expected_refuge_capture_mean": 68.0},
            ),
            lambda: _synthetic_projection(
                "CT007",
                15.0,
                5.0,
                {"expected_occupied_sites": 15.0, "expected_refuge_capture_mean": 5.0},
            ),
        ),
        (
            "CT008",
            lambda: _synthetic_projection(
                "CT008",
                8.0,
                40.0,
                {"expected_natural_capture_mean": 8.0, "latent_total_mean": 40.0},
            ),
            lambda: _synthetic_projection(
                "CT008",
                30.0,
                200.0,
                {"expected_natural_capture_mean": 30.0, "latent_total_mean": 200.0},
            ),
        ),
        (
            "CT009",
            lambda: _synthetic_projection("CT009", 1996.0, 1997.0, {}),
            lambda: _synthetic_projection("CT009", 1992.0, 1993.0, {}),
        ),
        (
            "CT010",
            lambda: _synthetic_projection("CT010", 0.0, 0.0, {"yearly_expected_detected_count": [0.0, 0.0, 0.0, 0.0, 0.0]}),
            lambda: _synthetic_projection("CT010", 10.0, 20.0, {"yearly_expected_detected_count": [2.0, 5.0, 10.0, 15.0, 20.0]}),
        ),
    ],
)
def test_ct006_to_ct010_monotonicity(model_inputs: ModelInputs, target_id, better_projection, worse_projection) -> None:
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    target_row = _target_row(model_inputs, target_id)
    details = _target_details(model_inputs, target_id)
    better = score_target(target_row, details, better_projection(), params)
    worse = score_target(target_row, details, worse_projection(), params)
    assert float(better["raw_penalty"]) < float(worse["raw_penalty"])


def test_observation_bridge_variants_adjust_late_targets(model_inputs: ModelInputs) -> None:
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")

    ct007 = _target_row(model_inputs, "CT007")
    ct007_details = _target_details(model_inputs, "CT007")
    occupancy_good_count_low = _synthetic_projection(
        "CT007",
        5.0,
        10.0,
        {"expected_occupied_sites": 5.0, "expected_refuge_capture_mean": 10.0},
    )
    baseline_ct007 = score_target(ct007, ct007_details, occupancy_good_count_low, params)
    occupancy_primary_ct007 = score_target(
        ct007,
        ct007_details,
        occupancy_good_count_low,
        params,
        ScoringConfig(observation_bridge_variant="ct007_occupancy_primary"),
    )
    assert float(occupancy_primary_ct007["raw_penalty"]) < float(baseline_ct007["raw_penalty"])

    ct009 = _target_row(model_inputs, "CT009")
    ct009_details = _target_details(model_inputs, "CT009")
    late_persistence = _synthetic_projection("CT009", 2002.0, np.nan, {})
    baseline_ct009 = score_target(ct009, ct009_details, late_persistence, params)
    soft_ct009 = score_target(
        ct009,
        ct009_details,
        late_persistence,
        params,
        ScoringConfig(observation_bridge_variant="ct009_terminal_window_gap3"),
    )
    assert float(baseline_ct009["weighted_penalty"]) == pytest.approx(30.0)
    assert float(soft_ct009["weighted_penalty"]) == pytest.approx(10.0)

    ct010 = _target_row(model_inputs, "CT010")
    ct010_details = _target_details(model_inputs, "CT010")
    expected_detections = _synthetic_projection(
        "CT010",
        10.0,
        10.0,
        {"yearly_expected_detected_count": [10.0, 10.0, 10.0, 10.0, 10.0]},
    )
    baseline_ct010 = score_target(ct010, ct010_details, expected_detections, params)
    half_detection_ct010 = score_target(
        ct010,
        ct010_details,
        expected_detections,
        params,
        ScoringConfig(observation_bridge_variant="ct010_detection_half"),
    )
    assert float(half_detection_ct010["weighted_penalty"]) == pytest.approx(
        0.5 * float(baseline_ct010["weighted_penalty"])
    )


def test_identical_seed_reproduces_target_score_table(model_inputs: ModelInputs) -> None:
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    scoring_config = ScoringConfig()
    result_a = score_historical_run(
        run_historical_simulation(params, "transient_perfect_storm", SimulationConfig(stochastic=True), seed=77),
        model_inputs,
        scoring_config,
    )
    result_b = score_historical_run(
        run_historical_simulation(params, "transient_perfect_storm", SimulationConfig(stochastic=True), seed=77),
        model_inputs,
        scoring_config,
    )
    pd.testing.assert_frame_equal(result_a.target_score_table, result_b.target_score_table)


def test_transient_replicates_have_finite_scores_and_aggregate_with_median(model_inputs: ModelInputs) -> None:
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    scoring_config = ScoringConfig()
    scoring_results = []
    for seed in range(1, 21):
        sim_result = run_historical_simulation(params, "transient_perfect_storm", SimulationConfig(stochastic=True), seed=seed)
        scoring_results.append(score_historical_run(sim_result, model_inputs, scoring_config))

    replicate_scores = pd.concat([result.target_score_table for result in scoring_results], ignore_index=True)
    scored = replicate_scores.loc[replicate_scores["evaluation_status"] == "scored"]
    assert np.isfinite(scored["raw_penalty"].astype(float)).all()

    aggregate = aggregate_replicate_scores(scoring_results, scoring_config)
    assert aggregate.summary["replicate_aggregation"] == "median"
    assert np.isfinite(float(aggregate.summary["historical_core_distance_median"]))
    assert np.isfinite(float(aggregate.summary["historical_core_distance_iqr"]))


def test_scoring_summary_blocks_on_baselines(model_inputs: ModelInputs, transient_deterministic_result) -> None:
    scoring_result = score_historical_run(transient_deterministic_result, model_inputs, ScoringConfig())
    assert scoring_result.summary["historical_core_ready"] is True
    assert scoring_result.summary["full_ready_for_module3"] is False
    assert scoring_result.summary["needs_module_2_5"] is True
    assert scoring_result.summary["deferred_target_ids"] == ["CT011", "CT012"]


def test_module2_scoring_cli_writes_expected_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "scored_run"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "score_historical_run.py"),
            "--family-id",
            "transient_perfect_storm",
            "--seed",
            "5",
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
    )
    assert (output_dir / "projection.csv").exists()
    assert (output_dir / "target_scores.csv").exists()
    assert (output_dir / "summary.json").exists()
    with (output_dir / "summary.json").open(encoding="utf-8") as handle:
        summary = json.load(handle)
    assert summary["full_ready_for_module3"] is False
