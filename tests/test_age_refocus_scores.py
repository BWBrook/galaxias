import math

import numpy as np
import pytest

from galaxias_model.age_refocus_scores import weighted_classify, weighted_recovery_metrics


def test_weighted_class_normalization_handles_mixed_source_classes_analytically():
    scores = np.array([[0.0, math.log(4.0), math.log(2.0), 0.0]])
    source_ids = np.array(["a", "a", "b", "c"])
    labels = np.array([0, 1, 0, 1], dtype=bool)
    log_weights = np.log([1.0, 3.0, 2.0, 4.0])
    result = weighted_classify(
        scores,
        source_ids,
        labels,
        log_weights,
        minimum_sources_per_class=1,
        minimum_prior_ess=1,
        minimum_post_ess=1,
    )

    assert result["evidence"][0].tolist() == pytest.approx([math.log(5.0 / 3.0), math.log(16.0 / 7.0)])
    assert result["log_ratio"][0] == pytest.approx(math.log((16.0 / 7.0) / (5.0 / 3.0)))
    assert result["counts"][0].tolist() == [2, 2]
    assert result["priorESS"].tolist() == pytest.approx([(3.0**2) / (1.0**2 + 2.0**2), (7.0**2) / (3.0**2 + 4.0**2)])


def test_another_same_source_history_does_not_inflate_source_count():
    ids = np.array([f"loss-{i}" for i in range(8)] + [f"persist-{i}" for i in range(8)])
    labels = np.array([0] * 8 + [1] * 8, dtype=bool)
    scores = np.zeros((1, 16))
    weights = np.zeros(16)
    base = weighted_classify(scores, ids, labels, weights)
    extended = weighted_classify(
        np.column_stack([scores, [[0.0]]]),
        np.concatenate([ids, ["loss-0"]]),
        np.concatenate([labels, [False]]),
        np.concatenate([weights, [0.0]]),
    )
    assert base["counts"].tolist() == [[8, 8]]
    assert extended["counts"].tolist() == [[8, 8]]


def test_zero_and_matched_controls_abstain_after_class_normalization():
    ids = np.array([f"s{i}" for i in range(16)])
    labels = np.array([0] * 8 + [1] * 8, dtype=bool)
    weights = np.log(np.arange(1, 17, dtype=float))
    matched = weighted_classify(np.zeros((2, 16)), ids, labels, weights)
    assert matched["prediction"].tolist() == [-1, -1]
    assert matched["log_ratio"].tolist() == [0.0, 0.0]

    zero = weighted_classify(np.zeros((1, 16)), ids, labels, np.full(16, -math.inf))
    assert zero["prediction"].tolist() == [-1]
    assert np.isneginf(zero["evidence"]).all()
    assert not np.isnan(zero["log_ratio"]).any()


def test_class_normalization_is_invariant_to_common_log_weight_scale():
    ids = np.array([f"s{i}" for i in range(16)])
    labels = np.array([0] * 8 + [1] * 8, dtype=bool)
    scores = np.arange(16, dtype=float)[None, :] / 10.0
    weights = np.log(np.arange(1, 17, dtype=float))
    first = weighted_classify(scores, ids, labels, weights)
    second = weighted_classify(scores, ids, labels, weights + 37.0)
    np.testing.assert_allclose(first["evidence"], second["evidence"])
    np.testing.assert_allclose(first["priorESS"], second["priorESS"])
    np.testing.assert_array_equal(first["prediction"], second["prediction"])


def test_posterior_ess_uses_source_aggregates_not_raw_history_count():
    ids = np.array(["dominant"] + [f"other{i}" for i in range(7)] + [f"persist{i}" for i in range(8)])
    labels = np.array([0] * 8 + [1] * 8, dtype=bool)
    scores = np.zeros((1, 16))
    weights = np.log(np.array([100.0] + [1.0] * 15))
    result = weighted_classify(scores, ids, labels, weights, minimum_post_ess=4)
    assert result["counts"].tolist() == [[8, 8]]
    assert result["postESS"][0, 0] < 2.0
    assert result["prediction"].tolist() == [-1]


def _truth_fixture():
    ids = np.asarray([f"loss-{i}" for i in range(17)] + [f"persist-{i}" for i in range(17)])
    truth = np.asarray([0] * 17 + [1] * 17, dtype=bool)
    prediction = truth.astype(np.int8)
    paired = np.where(truth, 1, 0).astype(np.int8)
    log_weights = np.zeros(34)
    return prediction, paired, truth, ids, log_weights


def test_weighted_truth_metrics_honour_coherent_mask_and_paired_zero_difference():
    prediction, paired, truth, ids, log_weights = _truth_fixture()
    mask = np.ones(34, dtype=bool)
    mask[0] = False
    result = weighted_recovery_metrics(
        prediction,
        truth,
        ids,
        log_weights,
        coherent_mask=mask,
        paired_prediction=paired,
        bootstrap_seed=11,
        bootstrap_replicates=100,
    )
    assert result["counts"]["n_data"] == 33
    assert result["gate_passed"] is True
    assert result["balanced_accuracy"] == pytest.approx(1.0)
    assert result["paired_delta_balanced_accuracy"] == pytest.approx(0.0)
    np.testing.assert_allclose(result["paired_delta_balanced_accuracy_ci95"], [0.0, 0.0])


def test_weighted_truth_bootstrap_replays_exactly():
    prediction, paired, truth, ids, log_weights = _truth_fixture()
    first = weighted_recovery_metrics(prediction, truth, ids, log_weights, paired_prediction=paired, bootstrap_seed=23, bootstrap_replicates=100)
    second = weighted_recovery_metrics(prediction, truth, ids, log_weights, paired_prediction=paired, bootstrap_seed=23, bootstrap_replicates=100)
    np.testing.assert_array_equal(first["bootstrap_balanced_accuracy"], second["bootstrap_balanced_accuracy"])
    np.testing.assert_array_equal(first["paired"]["paired"]["delta_ci95"], second["paired"]["paired"]["delta_ci95"])


def test_repeated_histories_cluster_together_and_universe_keeps_failed_source():
    prediction, paired, truth, ids, log_weights = _truth_fixture()
    prediction = np.concatenate([prediction, [1]])  # one extra, wrong, history for loss-0
    paired = np.concatenate([paired, [1]])
    truth = np.concatenate([truth, [False]])
    ids = np.concatenate([ids, ["loss-0"]])
    log_weights = np.concatenate([log_weights, [0.0]])
    universe = np.concatenate([np.unique(ids), ["failed-planned-source"]])
    result = weighted_recovery_metrics(
        prediction,
        truth,
        ids,
        log_weights,
        truth_source_universe=universe,
        paired_prediction=paired,
        bootstrap_seed=19,
        bootstrap_replicates=50,
    )
    assert result["truth_source_counts"].tolist() == [17, 17]
    assert result["counts"]["n_sources"] == 34
    assert np.isfinite(result["bootstrap_balanced_accuracy"]).all()
    np.testing.assert_allclose(result["paired"]["paired"]["delta_ci95"], [0.0, 0.0])


def test_concentrated_truth_weights_fail_source_ess_even_with_coverage():
    prediction, paired, truth, ids, log_weights = _truth_fixture()
    log_weights[:] = -10.0
    log_weights[0] = 10.0
    result = weighted_recovery_metrics(prediction, truth, ids, log_weights, bootstrap_replicates=30)
    assert result["truth_coverage_sufficient"] is True
    assert result["source_ess_sufficient"] is False
    assert result["gate_passed"] is False


def test_weighted_metrics_reject_invalid_log_weights():
    prediction, _, truth, ids, _ = _truth_fixture()
    bad = np.zeros(32)
    bad[0] = np.inf
    with pytest.raises(ValueError):
        weighted_recovery_metrics(prediction, truth, ids, bad, bootstrap_replicates=2)
