import copy
import json
import math

import numpy as np
import pytest

from galaxias_model.age_historical_refocus import (
    UNIT_NAMES,
    draw_proposal,
    endpoint_features,
    fit_histogram,
    lake_history_log_score,
    proposal_log_density_ratio,
    source_to_unit,
    source_with_unit,
)
from galaxias_model.age_sources import DESIGN, make_source


def _source(index=2, age=6, nursery="near_obligate"):
    design = json.loads(DESIGN.read_text())
    cell = next(c for c in design["process_cells"]
                if c["maximum_age"] == age and c["nursery"] == nursery)
    return make_source(cell, index, namespace="refocus-tests")


def test_lake_score_is_eight_trip_saturated_relative_and_scale_invariant():
    means = np.array([2., 3., 1., 4., 2., 0., 0., 0.])
    features = np.column_stack((means, np.zeros(8)))
    assert lake_history_log_score(features, means) == pytest.approx(0.)
    assert lake_history_log_score(features * 17, means) == pytest.approx(0.)
    assert lake_history_log_score(features, means * 9) == pytest.approx(0.)
    early = lake_history_log_score(features, means)
    late = features.copy()
    late[5:, 0] = 100
    assert lake_history_log_score(late, means) < early
    assert lake_history_log_score(np.zeros((8, 2)), means) == -math.inf


def test_lake_score_retains_zero_bins_and_digitised_noninteger_means():
    means = np.array([1.2, 0., 2.7, 0., 1.1, 0., 0., 0.])
    features = np.column_stack((means, np.zeros(8)))
    assert lake_history_log_score(features, means) == pytest.approx(0.)
    assert lake_history_log_score(features, np.zeros(8)) == pytest.approx(0.)
    with pytest.raises(ValueError):
        lake_history_log_score(features, means, age1=2.)


def test_source_unit_roundtrip_preserves_strata_and_recomputes_b():
    for age, nursery, index in ((6, "near_obligate", 2), (8, "legacy_range_sensitivity", 3)):
        source = _source(index=index, age=age, nursery=nursery)
        unit = source_to_unit(source)
        assert unit.shape == (len(UNIT_NAMES),)
        assert np.all((unit >= 0) & (unit <= 1))
        changed = source_with_unit(source, unit)
        assert changed["source_id"] == source["source_id"]
        assert changed["index_stratum"] == ("above_one" if index % 2 else "below_one")
        assert changed["R0"] == pytest.approx(source["R0"])
        assert changed["demography"]["recruits_per_female"] == pytest.approx(
            source["demography"]["recruits_per_female"]
        )


def test_source_unit_perturbation_changes_only_selected_fields():
    source = _source(index=2)
    before = copy.deepcopy(source)
    unit = source_to_unit(source)
    unit[0] = min(1., unit[0] + .05)
    unit[13] = min(1., unit[13] + .05)
    changed = source_with_unit(source, unit)
    for key in ("source_id", "namespace", "source_seed", "index", "cell", "index_stratum",
                "ledger_timing", "march_retention"):
        assert changed[key] == before[key]
    assert changed["forcing_values"]["PR027"] != before["forcing_values"]["PR027"] or changed["demography"] != before["demography"]
    assert changed["forcing_values"]["PR020"] == before["forcing_values"]["PR020"]


def test_histogram_fit_and_defensive_mixture_have_analytic_ratio():
    rows = np.full((4, len(UNIT_NAMES)), .1)
    weights = np.array([1., 0., 0., 0.])
    fit = fit_histogram(rows, weights)
    assert fit["bin_probabilities"].shape == (len(UNIT_NAMES), 4)
    expected_density = 4 * (.8 + .2 / 4)
    assert proposal_log_density_ratio(fit, rows[0]) == pytest.approx(
        math.log(.5 + .5 * expected_density ** len(UNIT_NAMES))
    )
    rng = np.random.default_rng(123)
    draws = [draw_proposal(fit, rng) for _ in range(64)]
    assert all(np.all((u >= 0) & (u <= 1)) and l >= math.log(.5) for u, l, _ in draws)


def test_histogram_empty_fit_is_uniform_and_draws_integrate_to_one():
    fit = fit_histogram(np.empty((0, len(UNIT_NAMES))), np.empty(0))
    assert fit["fallback_uniform"]
    assert np.allclose(fit["bin_probabilities"], .25)
    rng = np.random.default_rng(44)
    draws = np.array([draw_proposal(fit, rng)[0] for _ in range(10000)])
    assert np.allclose(draws.mean(axis=0), .5, atol=.02)
    assert proposal_log_density_ratio(fit, np.full(len(UNIT_NAMES), .5)) == pytest.approx(0.)


def test_endpoint_features_are_explicit_and_do_not_require_terminal_inputs():
    state = np.zeros((2, 2, 3), dtype=float)
    state[0, 0, 1] = 6
    state[1, 1, 1] = 5
    history = {
        "annual_states": {"pedder": {"2002": state}},
        "per_year_diagnostics": {"pedder": {2002: {
            "pre_spawn_females": 1., "pre_spawn_males": 1.,
            "pre_spawn_females_by_compartment": np.array([1., 0.]),
            "pre_spawn_males_by_compartment": np.array([0., 1.]),
        }}},
    }
    features = endpoint_features(history)
    assert features["Y0"] and features["Yalive"] and features["Y10"]
    assert features["Ypair"] and not features["Ysame_pair"]
    np.testing.assert_allclose(features["realised_pre_spawn_pair"], [1., 1.])
    np.testing.assert_allclose(features["same_compartment_pair"], [[1., 0.], [0., 1.]])


def test_endpoint_features_reject_missing_compartment_pair_diagnostics():
    state = np.ones((2, 2, 3), dtype=float)
    history = {
        "annual_states": {"pedder": {2002: state}},
        "per_year_diagnostics": {"pedder": {2002: {
            "pre_spawn_females": 1., "pre_spawn_males": 1.,
        }}},
    }
    with pytest.raises(ValueError, match="compartment-specific"):
        endpoint_features(history)
