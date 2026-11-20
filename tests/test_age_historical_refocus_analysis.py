"""Weighted target integration and decision boundaries, without simulations."""
import math
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.analyze_age_historical_refocus import (
    gate_decision, historical_weights, source_support, weighted_controls,
)
from galaxias_model.age_recovery_observation import decision_profiles


def test_proposal_correction_and_history_score_each_enter_once():
    means = np.array([1., 5., 2., 1., 1., 0., 0., 0.])
    feature = np.column_stack((means, np.zeros(8)))
    rows = [dict(features={"lake": feature}, proposal_log_density_ratio=math.log(2.))]
    actual = historical_weights(rows, means, decision_profiles()[0])
    assert actual == pytest.approx([-math.log(2.)])
    rows[0]["features"]["lake"] = feature.copy()
    rows[0]["features"]["lake"][5:, 0] = 1.
    # The early shape matches, so only the late allocation penalty remains.
    assert historical_weights(rows, means, decision_profiles()[0]) == pytest.approx(
        [-10*math.log(1+3/10)-math.log(2.)])


def test_source_support_aggregates_repeats_and_uses_class_specific_scaling():
    counts, ess, largest = source_support([0., 0., 0., -10000., -10000.],
                                          ["a", "a", "b", "c", "d"], [0, 0, 0, 1, 1])
    assert counts.tolist() == [2, 2]
    assert ess == pytest.approx([9/5, 2])
    assert largest == pytest.approx([2/3, .5])


def test_weighted_mechanical_controls():
    assert weighted_controls()["all_passed"]


def test_fixed_total_secondary_and_smoke_cannot_authorize_go():
    row = dict(cell_id="c", index_stratum="below_one", profile_id="p", panel="base",
               endpoint="terminal_alive", generator="fixed_creek_total", gate_passed=True,
               assessed=True, status="passed")
    assert gate_decision([row], full=True)["status"].startswith("STOP")
    row.update(generator="poisson", endpoint="terminal_pair")
    assert gate_decision([row], full=True)["status"].startswith("STOP")
    row.update(endpoint="terminal_alive")
    assert gate_decision([row], full=False)["conditional_go_columns"] == []
    assert gate_decision([row], full=True)["primary_base_passes"] == 1
