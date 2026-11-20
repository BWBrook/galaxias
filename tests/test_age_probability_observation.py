import math

import numpy as np
import pytest

from galaxias_model.age_observation import conditional_capture_log_probability
from galaxias_model.age_probability_observation import (
    early_creek_log_score,
    generate_remaining,
    remaining_log_likelihood,
    _gamma_pair_log_probabilities,
    _single_gamma_log_probabilities,
)


def _exposures(n=1):
    creek = np.tile(np.array([[43.0, 2.0, 3.0]]), (n, 1))
    binary = np.ones((n, 11), dtype=float)
    return creek, binary


def test_early_allocation_and_late_zero_recover_three_block_score():
    creek = np.array([[43.0, 2.0, 0.0], [4.0, 1.0, 3.0]])
    observed = np.array([68, 1, 0], dtype=np.int64)
    score = early_creek_log_score(creek)
    remaining = remaining_log_likelihood(
        creek, np.ones((2, 11)), [0], np.zeros((1, 9), dtype=bool),
        q=0.0, generator="poisson",
    )["late"]
    expected = np.array([
        conditional_capture_log_probability(observed, creek[0]),
        conditional_capture_log_probability(observed, creek[1]),
    ])
    # The early term is relative to the saturated [68, 1] allocation.
    coefficient = math.lgamma(70) - math.lgamma(69) - math.lgamma(2)
    saturated = 68.0 * math.log(68.0 / 69.0) + math.log(1.0 / 69.0)
    np.testing.assert_allclose(score + remaining[0], expected - coefficient - saturated)
    assert np.all(score <= 0)


def test_early_saturated_allocation_is_zero_and_zero_exposure_is_impossible():
    creek = np.array([[68.0, 1.0, 0.0], [0.0, 0.0, 2.0], [5.0, 0.0, 1.0]])
    score = early_creek_log_score(creek)
    assert score[0] == pytest.approx(0.0)
    assert score[1] == -math.inf
    assert score[2] == -math.inf


def test_negative_binomial_late_pmf_normalizes():
    creek, binary = _exposures()
    counts = np.arange(0, 500, dtype=np.int64)
    scores = remaining_log_likelihood(
        creek, binary, counts, np.zeros((counts.size, 9), dtype=bool),
        q=0.0, generator="poisson",
    )["late"][:, 0]
    assert math.isclose(float(np.exp(scores).sum()), 1.0, rel_tol=1e-12)


def test_gamma_quality_pair_patterns_are_analytic_and_normalized():
    a = np.array([0.2, 2.0])
    b = np.array([0.7, 3.0])
    logs = _gamma_pair_log_probabilities(a, b)
    probabilities = np.stack([np.exp(x) for x in logs])
    np.testing.assert_allclose(probabilities.sum(axis=0), 1.0)
    assert probabilities[3, 0] == pytest.approx(
        a[0] * b[0] * (2 + a[0] + b[0])
        / ((1 + a[0]) * (1 + b[0]) * (1 + a[0] + b[0]))
    )
    single = _single_gamma_log_probabilities(np.array([0.0, 2.0]))
    np.testing.assert_allclose(np.exp(single[0]) + np.exp(single[1]), 1.0)


def test_gamma_quality_generator_matches_joint_pattern_probabilities():
    n = 20000
    creek = np.tile(np.array([[1.0, 0.0, 0.0]]), (n, 1))
    binary = np.zeros((n, 11), dtype=float)
    binary[:, 4] = 0.8
    binary[:, 5] = 1.4
    result = generate_remaining(
        creek, binary, [("gamma", i) for i in range(n)],
        q=1.0, generator="gamma_binary_quality",
    )
    pair = result["insurance_observed"][:, [2, 3]]
    observed = np.array([
        np.mean(~pair[:, 0] & ~pair[:, 1]),
        np.mean(pair[:, 0] & ~pair[:, 1]),
        np.mean(~pair[:, 0] & pair[:, 1]),
        np.mean(pair[:, 0] & pair[:, 1]),
    ])
    expected = np.exp(np.array(_gamma_pair_log_probabilities(
        np.array([0.8]), np.array([1.4])
    )))[:, 0]
    np.testing.assert_allclose(observed, expected, atol=0.02)


def test_gamma_quality_shares_only_declared_visit_groups():
    n = 3000
    creek = np.tile(np.array([[1.0, 0.0, 0.0]]), (n, 1))
    binary = np.ones((n, 11), dtype=float)
    draws = generate_remaining(
        creek, binary, [("groups", i) for i in range(n)],
        q=0.4, generator="gamma_binary_quality",
    )["insurance_observed"]
    paired = np.corrcoef(draws[:, 2], draws[:, 3])[0, 1]
    unpaired = np.corrcoef(draws[:, 0], draws[:, 1])[0, 1]
    assert paired > 0.08
    assert abs(unpaired) < 0.08


def test_generation_is_identity_reproducible_and_does_not_clip_zero_late_exposure():
    creek, binary = _exposures(3)
    creek[:, 2] = 0.0
    identities = [("source", 1), ("source", 2), ("source", 3)]
    first = generate_remaining(
        creek, binary, identities, q=0.2, generator="poisson",
    )
    second = generate_remaining(
        creek, binary, identities, q=0.2, generator="poisson",
    )
    np.testing.assert_array_equal(first["late_counts"], second["late_counts"])
    np.testing.assert_array_equal(first["insurance_observed"], second["insurance_observed"])
    np.testing.assert_array_equal(first["late_counts"], np.zeros(3, dtype=np.int64))
    impossible = remaining_log_likelihood(
        creek[:1], binary[:1], [1], np.zeros((1, 9), dtype=bool),
        q=0.2, generator="poisson",
    )["late"]
    assert impossible[0, 0] == -math.inf


def test_zero_q_is_valid_and_only_positive_records_are_impossible():
    creek, binary = _exposures(2)
    generated = generate_remaining(
        creek, binary, [("q0", 1), ("q0", 2)], q=0.0, generator="gamma_binary_quality",
    )
    assert not generated["insurance_observed"].any()
    observed = np.zeros((2, 9), dtype=bool)
    observed[1, 0] = True
    score = remaining_log_likelihood(
        creek, binary, generated["late_counts"], observed,
        q=0.0, generator="gamma_binary_quality",
    )
    assert np.all(score["insurance"][0] == 0)
    assert np.all(np.isneginf(score["insurance"][1]))


def test_exposures_require_positive_early_and_finite_nonnegative_values():
    assert early_creek_log_score([[0.0, 0.0, 1.0]])[0] == -math.inf
    with pytest.raises(ValueError):
        remaining_log_likelihood(
            [[1.0, 1.0, -1.0]], np.ones((1, 11)), [0],
            np.zeros((1, 9), dtype=bool), q=0.1, generator="poisson",
        )
    with pytest.raises(ValueError):
        remaining_log_likelihood(
            [[1.0, 1.0, 1.0]], np.ones((1, 11)), [0.0],
            np.zeros((1, 9), dtype=bool), q=0.1, generator="poisson",
        )
