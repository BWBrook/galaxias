import math

import numpy as np
import pytest

from galaxias_model.age_early_recovery import (
    RESTRICTIONS,
    bank_log_support,
    conformal_pvalues,
    exact_binomial_bounds,
    nonconformity,
    restriction_sets,
    summarise_test_sets,
)
from galaxias_model.age_historical_refocus import lake_history_log_score


def test_bank_support_matches_old_score_and_averages_failed_positions_as_zero():
    rng = np.random.default_rng(41)
    features = rng.uniform(0.1, 5.0, size=(4, 2, 3, 8, 2))
    means = rng.uniform(0.1, 3.0, size=(5, 8))
    valid = np.ones((4, 2, 3), dtype=bool)
    valid[1, 0, 2] = False
    features[1, 0, 2] = np.nan
    observed = bank_log_support(features, means, valid=valid, batch_size=2)
    for d, mean in enumerate(means):
        for restriction in range(4):
            values = [
                math.exp(lake_history_log_score(features[restriction, source, replicate], mean))
                if valid[restriction, source, replicate]
                else 0.0
                for source in range(2)
                for replicate in range(3)
            ]
            expected = math.log(sum(values) / 6.0)
            assert observed[d, restriction] == pytest.approx(expected)


def test_bank_source_mask_removes_whole_clusters_but_keeps_planned_denominator():
    features = np.ones((4, 2, 1, 8, 2), dtype=float)
    means = np.ones((1, 8), dtype=float)
    observed = bank_log_support(features, means, source_mask=np.array([True, False]))
    np.testing.assert_allclose(observed, 0.0)


def test_bank_support_uses_shifted_logmeanexp_for_finite_very_low_scores():
    features = np.ones((4, 1, 1, 8, 2), dtype=float)
    # A positive but subnormal exposure retains a finite old point score near
    # -9,000.  Direct exp(score) underflows; shifted log-mean-exp does not.
    features[:, 0, 0, 0, 0] = 1e-320
    means = np.ones((1, 8), dtype=float)
    observed = bank_log_support(features, means, power=1.0)
    assert np.all(np.isfinite(observed))
    assert np.all(observed < -700.0)


def test_nonconformity_preserves_infinite_ranks_without_nan():
    ell = np.array([[-np.inf, -np.inf, -np.inf, -np.inf], [0.0, -1.0, -np.inf, np.inf]])
    result = nonconformity(ell)
    assert result["unsupported"].tolist() == [True, False]
    assert np.all(np.isposinf(result["relative"][0]))
    assert not np.isnan(result["relative"]).any()
    np.testing.assert_array_equal(result["absolute"][1], [0.0, 1.0, np.inf, -np.inf])


def test_conformal_ranks_use_conservative_ties_and_keep_infinities():
    calibration = np.array([-np.inf, 0.0, np.inf])
    result = conformal_pvalues(calibration, np.array([np.inf, 0.0, -np.inf]))
    np.testing.assert_allclose(result, [0.5, 0.75, 1.0])
    with pytest.raises(ValueError):
        conformal_pvalues([0.0, np.nan], [0.0])


def test_restriction_sets_are_componentwise_and_force_unsupported_full_set():
    calibration = {
        label: np.array([[0.0, -1.0, -2.0, -3.0], [0.0, -1.0, -2.0, -3.0]])
        for label in RESTRICTIONS
    }
    test = np.array([[0.0, -1.0, -2.0, -3.0], [-np.inf, -np.inf, -np.inf, -np.inf]])
    result = restriction_sets(calibration, test)
    assert result["sets"].shape == (2, 4)
    assert np.all(result["sets"][1])
    assert result["supported"].tolist() == [True, False]
    assert np.all(result["p_relative"] > 0)


def test_exact_binomial_bounds_cover_boundaries_and_known_one_sided_cp_values():
    assert exact_binomial_bounds(0, 0, 0.05) == (0.0, 1.0)
    assert exact_binomial_bounds(0, 10, 0.05)[0] == 0.0
    assert exact_binomial_bounds(10, 10, 0.05)[1] == 1.0
    lower, upper = exact_binomial_bounds(5, 10, 0.05)
    assert lower == pytest.approx(0.2224411, abs=1e-7)
    assert upper == pytest.approx(0.7775589, abs=1e-7)


def test_set_summary_reports_four_class_and_twelve_directed_intervals():
    sets = {label: np.eye(4, dtype=bool) for label in RESTRICTIONS}
    result = summarise_test_sets(sets)
    assert set(result["coverage"]) == set(RESTRICTIONS)
    assert len(result["directed"]) == 12
    assert result["stable"] is True
    assert result["coverage"]["R_H"]["k"] == 1
    assert result["directed"]["R_H->R_T"]["k"] == 1
