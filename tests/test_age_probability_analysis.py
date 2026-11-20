from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_age_probability_gate import (
    assess,
    calibration_interval,
    proper_score_gains,
    role_data,
)
from galaxias_model.age_probability_scores import (
    probability_forecasts,
    source_bootstrap_counts,
    source_halves,
)


N_HISTORIES = 100
N_BOOTSTRAP = 32


def _truth(loss=None):
    if loss is None:
        loss = np.array([True] * 50 + [False] * 50)
    return {
        "weights": np.full(N_HISTORIES, 1.0 / N_HISTORIES),
        "loss": np.asarray(loss, dtype=bool),
        "indices": np.arange(N_HISTORIES, dtype=int),
        "logs": np.zeros(N_HISTORIES),
        "ids": [f"source-{i}" for i in range(N_HISTORIES)],
        "blocks": ["toy"] * N_HISTORIES,
        "planned_replicates": 1,
    }


def _forecast(probabilities):
    p = np.asarray(probabilities, dtype=float)
    return {
        "p": p,
        "supported": np.isfinite(p),
        "finite_fraction": np.ones(p.size),
        "interval": np.column_stack((p, p)),
        "half_gap": np.zeros(p.size),
        "boundary_bound_used": np.zeros(p.size, dtype=bool),
        "bootstrap_probabilities": np.tile(p, (N_BOOTSTRAP, 1)),
    }


def _baseline(value=0.5):
    return {
        "p": np.array([value]),
        "bootstrap_probabilities": np.full((N_BOOTSTRAP, 1), value),
    }


def _ones_bootstrap():
    return np.ones((N_BOOTSTRAP, N_HISTORIES), dtype=np.int64)


def test_constant_proper_forecast_is_calibrated_but_has_no_incremental_information():
    truth = _truth()
    result, _, _ = assess(truth, _ones_bootstrap(), _forecast(np.full(N_HISTORIES, 0.5)), _baseline())
    assert result["status"] == "CALIBRATED_BUT_NO_INCREMENTAL_INFORMATION"
    assert result["calibration_equivalence_pass"]
    assert not result["positive_log_gain"]
    assert not result["positive_brier_gain"]


def test_two_calibrated_forecast_bins_are_informative_against_half_baseline():
    labels = np.array([True] * 10 + [False] * 40 + [True] * 40 + [False] * 10)
    probabilities = np.array([0.2] * 50 + [0.8] * 50)
    truth = _truth(labels)
    result, reliability, _ = assess(truth, _ones_bootstrap(), _forecast(probabilities), _baseline())
    assert result["status"] == "CALIBRATED_AND_INFORMATIVE"
    assert result["calibration_equivalence_pass"]
    assert result["positive_log_gain"] and result["positive_brier_gain"]
    assert {row["group"] for row in reliability} == {0, 3}
    assert all(row["passed"] for row in reliability)


def test_miscalibrated_forecast_fails_calibration_decision():
    truth = _truth()
    result, _, _ = assess(truth, _ones_bootstrap(), _forecast(np.full(N_HISTORIES, 0.1)), _baseline())
    assert result["status"] == "CALIBRATION_FAILED"
    assert not result["calibration_equivalence_pass"]
    assert result["calibration_residual"] == pytest.approx(0.4)


def test_contradictory_zero_baseline_is_a_support_failure_without_clipping():
    truth = _truth()
    forecast = _forecast(np.full(N_HISTORIES, 0.5))
    result, _, _ = assess(truth, _ones_bootstrap(), forecast, _baseline(0.0))
    gains = proper_score_gains(truth, _ones_bootstrap(), forecast, _baseline(0.0))
    assert gains["proper_score_contradiction"]
    assert not result["computationally_assessed"]
    assert result["status"] == "UNASSESSABLE"


def test_unsupported_predictions_widen_calibration_interval_as_worst_case_mass():
    truth = _truth()
    bootstrap = _ones_bootstrap()
    supported = np.full(N_HISTORIES, 0.5)
    unsupported = supported.copy()
    unsupported[0] = np.nan
    ordinary = calibration_interval(
        truth, bootstrap, supported, np.tile(supported, (N_BOOTSTRAP, 1)), np.ones(N_HISTORIES, dtype=bool)
    )
    bounded = calibration_interval(
        truth, bootstrap, unsupported, np.tile(unsupported, (N_BOOTSTRAP, 1)), np.ones(N_HISTORIES, dtype=bool)
    )
    assert bounded["ci"][0] < ordinary["ci"][0]
    assert bounded["ci"][1] > ordinary["ci"][1]
    assert bounded["finite_fraction"] == 1.0


def test_source_universe_retains_failed_sources_and_aggregates_replicates():
    sources = [
        {"role": "truth", "index": index, "source_id": f"source-{index}",
         "ledger_timing": "early", "march_retention": False}
        for index in range(3)
    ]
    histories = [
        {"namespace": "truth", "status": "complete", "conditioning": {"total": 0.0},
         "proposal_log_density_ratio": 0.0, "source_id": "source-0", "loss_2002": False},
        {"namespace": "truth", "status": "complete", "conditioning": {"total": 0.0},
         "proposal_log_density_ratio": 0.0, "source_id": "source-0", "loss_2002": True},
        {"namespace": "truth", "status": "process_infeasible", "conditioning": {"total": None},
         "proposal_log_density_ratio": 0.0, "source_id": "source-1", "loss_2002": False},
    ]
    result = role_data(sources, histories, "truth", replicates=2)
    assert result["ids"] == ["source-0", "source-1", "source-2"]
    assert len(result["rows"]) == 2
    assert result["planned_replicates"] == 2
    assert result["source_ess"] == pytest.approx(1.0)


def test_probability_forecast_uses_natural_prevalence_and_fixed_bootstrap_fixture():
    n_sources = 4
    source_blocks = ["ledger", "ledger", "march", "march"]
    source_indices = np.repeat(np.arange(n_sources), 2)
    outcomes = np.array([False, False, False, False, True, True, False, False])
    log_weights = np.log(np.repeat([1.0, 0.5, 0.25, 0.25], 2))
    halves = source_halves(["a", "b", "c", "d"], source_blocks, seed=5)
    bootstrap = np.ones((N_BOOTSTRAP, n_sources), dtype=np.int64)
    result = probability_forecasts(
        log_weights, np.zeros((1, 8)), outcomes, source_indices, source_blocks,
        bootstrap, halves, replicates=2,
    )
    assert result["probability"][0] == pytest.approx(0.25 / 2.0)
    assert result["source_denominator"].shape == (1, n_sources)
    assert result["n_source_positive_count"][0] == n_sources
