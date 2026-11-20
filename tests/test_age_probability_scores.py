import hashlib
import math

import numpy as np
import pytest

from galaxias_model.age_probability_scores import (
    bounded_ratio_interval,
    probability_forecasts,
    source_bootstrap_counts,
    source_halves,
)


def _fixture(*, zero_event=False):
    source_ids = np.array(["a", "b", "c", "d"])
    blocks = np.array(["ledger", "ledger", "march", "march"])
    halves = source_halves(source_ids, blocks, seed=11)
    bootstrap = source_bootstrap_counts(blocks, 200, seed=22)
    # Two histories per source, with unequal natural source prevalence.
    source_indices = np.repeat(np.arange(4), 2)
    log_weights = np.log(np.repeat([1.0, 0.5, 0.25, 0.25], 2))
    likelihood = np.zeros((1, 8), dtype=float)
    outcomes = np.array([False, False, False, False, True, True, False, False])
    if zero_event:
        outcomes[:] = False
    return probability_forecasts(
        log_weights,
        likelihood,
        outcomes,
        source_indices,
        blocks,
        bootstrap,
        halves,
        replicates=2,
    )


def test_stratified_bootstrap_retains_zero_weight_positions_and_reproducibility():
    blocks = ["ledger", "ledger", "march"]
    first = source_bootstrap_counts(blocks, 20, 5)
    second = source_bootstrap_counts(blocks, 20, 5)
    np.testing.assert_array_equal(first, second)
    assert first.shape == (20, 3)
    assert np.all(first[:, :2].sum(axis=1) == 2)
    assert np.all(first[:, 2] == 1)
    assert np.any(first[:, 0] == 0) or np.any(first[:, 1] == 0)


def test_source_halves_are_hash_sorted_alternating_within_block():
    ids = ["a", "b", "c", "d", "e"]
    blocks = ["ledger", "ledger", "ledger", "march", "march"]
    actual = source_halves(ids, blocks, 17)
    expected = np.empty(5, dtype=np.int8)
    for block in ("ledger", "march"):
        indices = [i for i, value in enumerate(blocks) if value == block]
        ordered = sorted(indices, key=lambda i: hashlib.sha256(f"17|{ids[i]}".encode()).digest())
        for rank, index in enumerate(ordered):
            expected[index] = rank % 2
    np.testing.assert_array_equal(actual, expected)


def test_natural_prevalence_uses_unequal_source_weights_without_class_normalization():
    result = _fixture()
    # Source contributions are [1,.5,.25,.25], and only source c has a
    # positive outcome in both of its repeated histories: p=.25/2=.125.
    assert result["probability"][0] == pytest.approx(0.25 / 2.0)
    assert result["source_ess"][0] == pytest.approx(4.0 / (1.0 + .25 + .0625 + .0625))
    assert result["n_source_positive_count"][0] == 4


def test_same_source_repeats_do_not_inflate_source_ess_or_bootstrap_units():
    result = _fixture()
    assert result["source_denominator"].shape == (1, 4)
    assert result["source_ess"][0] < 4.0
    assert result["bootstrap_probabilities"].shape == (200, 1)


def test_half_split_is_reproducible_and_gap_is_reported():
    first = _fixture()
    second = _fixture()
    np.testing.assert_array_equal(first["half_gap"], second["half_gap"])
    assert np.isfinite(first["half_gap"]).all()


def test_impossible_likelihood_is_zero_contribution_and_no_nan():
    blocks = ["ledger", "ledger"]
    halves = source_halves(["a", "b"], blocks, 3)
    bootstrap = source_bootstrap_counts(blocks, 50, 4)
    result = probability_forecasts(
        [0.0, 0.0], [[-math.inf, -math.inf]], [True, False], [0, 1], blocks,
        bootstrap, halves, replicates=1,
    )
    assert np.isnan(result["probability"])[0]
    assert result["supported"][0] is np.False_
    assert result["interval"][0].tolist() == [0.0, 1.0]


def test_boundary_zero_event_uses_wide_bounded_interval():
    result = _fixture(zero_event=True)
    assert result["probability"][0] == 0.0
    assert result["boundary_bound_used"][0]
    assert result["interval"][0, 0] == 0.0
    assert result["interval"][0, 1] > 0.5


def test_bounded_ratio_interval_simple_case_is_independent_and_conservative():
    interval = bounded_ratio_interval([1.0, 1.0], [2.0, 2.0], ["a", "a"])
    assert interval[0] == 0.0
    assert interval[1] == 1.0
    one_block = bounded_ratio_interval([0.5, 0.5, 0.5, 0.5], [1.0, 1.0, 1.0, 1.0], ["a"] * 4)
    assert one_block[0] <= 0.5 <= one_block[1]


def test_bounded_ratio_interval_pools_independent_sources_with_theorem_11_radius():
    n = 256
    numerator = np.zeros(n)
    denominator = np.ones(n)
    blocks = np.repeat(["ledger", "march", "ledger_alt", "march_alt"], n // 4)
    interval = bounded_ratio_interval(numerator, denominator, blocks)
    log_term = math.log(8.0 / 0.05)
    radius = 7.0 * 2.0 * log_term / (3.0 * (n - 1))
    assert interval[0] == 0.0
    assert interval[1] == pytest.approx(radius / (1.0 - radius))


def test_bounded_ratio_interval_does_not_depend_on_fixed_block_labels():
    numerator = np.linspace(0.0, 0.5, 12)
    denominator = np.linspace(1.0, 1.5, 12)
    first = bounded_ratio_interval(numerator, denominator, ["a"] * 6 + ["b"] * 6)
    second = bounded_ratio_interval(numerator, denominator, ["x", "y"] * 6)
    np.testing.assert_allclose(first, second)


def test_bounded_ratio_interval_accepts_heterogeneous_source_means():
    numerator = np.array([0.0, 0.1, 0.2, 0.4, 0.6, 0.8])
    denominator = np.array([0.4, 0.6, 0.8, 1.0, 1.2, 1.4])
    interval = bounded_ratio_interval(numerator, denominator, ["ledger"] * 3 + ["march"] * 3)
    assert np.all(np.isfinite(interval))
    assert 0.0 <= interval[0] <= interval[1] <= 1.0


def test_log_underflow_preserves_point_stability_but_keeps_bound_wide():
    blocks = ["a", "a"]
    halves = source_halves(["x", "y"], blocks, 1)
    bootstrap = source_bootstrap_counts(blocks, 20, 2)
    result = probability_forecasts(
        [-1000.0, -1000.0], [[-1000.0, -1000.0]], [True, False], [0, 1],
        blocks, bootstrap, halves, replicates=1,
    )
    assert result["probability"][0] == pytest.approx(0.5)
    assert result["interval"][0, 1] > 0.5


def test_invalid_probability_inputs_rejected():
    blocks = ["a", "b"]
    halves = source_halves(["x", "y"], blocks, 1)
    bootstrap = source_bootstrap_counts(blocks, 2, 2)
    kwargs = dict(source_indices=[0, 1], source_blocks=blocks, bootstrap_counts=bootstrap, halves=halves, replicates=1)
    with pytest.raises(ValueError):
        probability_forecasts([math.log(2.0) + 1e-6, 0.0], [[0.0, 0.0]], [True, False], **kwargs)
    with pytest.raises(ValueError):
        probability_forecasts([0.0, 0.0], [[0.1, 0.0]], [True, False], **kwargs)
    with pytest.raises(ValueError):
        probability_forecasts([0.0, 0.0], [[math.nan, 0.0]], [True, False], **kwargs)
    with pytest.raises(ValueError):
        bounded_ratio_interval([1.1], [1.0], ["a"])
