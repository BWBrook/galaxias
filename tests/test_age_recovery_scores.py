import math

import numpy as np
import pytest

from galaxias_model.age_recovery_scores import classify, recovery_metrics, score_blocks


def _score_inputs(*, n_bank=1, n_data=1):
    return {
        "creek_exposures": np.ones((n_bank, 3)),
        "lake_exposures": np.ones((n_bank, 2)),
        "binary_exposures": np.ones((n_bank, 1)),
        "creek_counts": np.zeros((n_data, 3), dtype=int),
        "lake_equivalents": np.zeros((n_data, 2)),
        "binary_observed": np.zeros((n_data, 1), dtype=bool),
        "q": 1.0,
        "creek_power": 1.0,
        "lake_power": 1.0,
    }


def test_score_blocks_matches_conditional_multinomial_closed_form():
    args = _score_inputs()
    args["creek_exposures"] = np.array([[1.0, 2.0, 3.0]])
    args["creek_counts"] = np.array([[2, 1, 0]])
    args["binary_exposures"] = np.zeros((1, 0))
    args["binary_observed"] = np.zeros((1, 0), dtype=bool)
    result = score_blocks(**args)

    expected = 2.0 * math.log(1.0 / 6.0) + math.log(2.0 / 6.0)
    assert result["creek"][0, 0] == pytest.approx(expected)
    assert result["total"][0, 0] == pytest.approx(expected)


def test_score_blocks_has_stable_zero_and_impossible_positive_behaviour():
    args = _score_inputs()
    args["creek_exposures"] = np.array([[0.0, 2.0, 0.0]])
    args["creek_counts"] = np.array([[1, 0, 0]])
    args["lake_exposures"] = np.array([[0.0, 1.0]])
    args["lake_equivalents"] = np.array([[1.0, 0.0]])
    args["binary_exposures"] = np.array([[0.0]])
    args["binary_observed"] = np.array([[True]])
    result = score_blocks(**args)

    assert np.isneginf(result["creek"][0, 0])
    assert np.isneginf(result["lake"][0, 0])
    assert np.isneginf(result["binary"][0, 0])
    assert not any(np.isnan(values).any() for values in result.values())

    args["binary_exposures"] = np.array([[2.0]])
    args["binary_observed"] = np.array([[False]])
    negative = score_blocks(**args)["binary"][0, 0]
    assert negative == pytest.approx(-2.0)


def test_classify_does_not_let_duplicate_source_replicates_increase_weight():
    ids = np.array([f"loss-{i}" for i in range(8)] + [f"persist-{i}" for i in range(8)] + ["loss-0"])
    labels = np.array([False] * 8 + [True] * 8 + [False], dtype=bool)
    scores = np.array([([0.0] * 8) + ([-1.0] * 8) + [0.0]])
    result = classify(scores, ids, labels, minimum_sources_per_class=8, minimum_class_ess=4)

    assert result["prediction"].tolist() == [0]
    assert result["sourcecounts"].tolist() == [[8, 8]]
    assert result["log_ratio"][0] == pytest.approx(-1.0)


def test_classify_identical_observations_do_not_leak_bank_truth_labels():
    ids = np.array([f"source-{i}" for i in range(16)])
    labels = np.array([False] * 8 + [True] * 8, dtype=bool)
    result = classify(np.zeros((2, 16)), ids, labels)

    assert result["prediction"].tolist() == [-1, -1]
    assert result["log_ratio"].tolist() == [0.0, 0.0]


def test_classify_abstains_when_source_ess_is_insufficient():
    ids = np.array([f"loss-{i}" for i in range(8)] + [f"persist-{i}" for i in range(8)])
    labels = np.array([False] * 8 + [True] * 8, dtype=bool)
    scores = np.array([[-np.inf] * 8 + [0.0] * 8])
    scores[0, 0] = 0.0
    result = classify(scores, ids, labels, minimum_sources_per_class=8, minimum_class_ess=4)

    assert result["prediction"][0] == -1
    assert result["ess0"][0] == pytest.approx(1.0)


def test_recovery_metrics_are_source_macro_and_count_abstentions_as_errors():
    prediction = np.array([0] * 9 + [1] + [1] * 2)
    truth = np.array([0] * 10 + [1] * 2)
    source_ids = np.array(["a"] * 9 + ["b"] + ["c"] * 2)
    result = recovery_metrics(prediction, truth, source_ids, bootstrap_seed=7, bootstrap_replicates=100)

    assert result["source_macro_sensitivity"].tolist() == pytest.approx([0.5, 1.0])
    assert result["balanced_accuracy"] == pytest.approx(0.75)
    assert result["distinct_source_coverage"].tolist() == [2, 1]
    assert result["confusion"].tolist() == [[9, 1, 0], [0, 2, 0]]

    abstaining = recovery_metrics(
        np.array([-1, 1]), np.array([0, 1]), np.array(["a", "b"]), bootstrap_replicates=20
    )
    assert abstaining["counts"]["n_correct"] == 1
    assert abstaining["counts"]["n_abstentions"] == 1


def test_recovery_bootstrap_is_reproducible_and_paired_uses_same_draws():
    prediction = np.array([0, 0, 1, 1, 0, 1])
    paired = np.array([1, 0, 1, 0, 0, 1])
    truth = np.array([0, 0, 1, 1, 0, 1])
    source_ids = np.array(["a", "a", "b", "b", "c", "c"])
    first = recovery_metrics(
        prediction, truth, source_ids, paired_prediction=paired, bootstrap_seed=123, bootstrap_replicates=200
    )
    second = recovery_metrics(
        prediction, truth, source_ids, paired_prediction=paired, bootstrap_seed=123, bootstrap_replicates=200
    )

    np.testing.assert_array_equal(first["bootstrap_balanced_accuracy"], second["bootstrap_balanced_accuracy"])
    np.testing.assert_array_equal(
        first["paired_bootstrap_delta_balanced_accuracy"],
        second["paired_bootstrap_delta_balanced_accuracy"],
    )
    assert first["paired_delta_balanced_accuracy_ci95"].shape == (2,)


def test_recovery_bootstrap_matches_explicit_source_cluster_loop():
    prediction = np.array([0, 1, 0, 1, 1, 1, 0, 0])
    paired = np.array([0, 0, 0, 1, 1, 0, 0, 1])
    truth = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    source_ids = np.array(["a", "a", "b", "b", "c", "c", "d", "d"])
    seed = 31
    replicates = 40
    result = recovery_metrics(
        prediction,
        truth,
        source_ids,
        paired_prediction=paired,
        bootstrap_seed=seed,
        bootstrap_replicates=replicates,
    )
    groups = {}
    for index, source in enumerate(source_ids):
        groups.setdefault(source, []).append(index)
    source_sens = []
    paired_sens = []
    for indices in groups.values():
        source_sens.append([
            float(np.mean(prediction[[i for i in indices if truth[i] == cls]] == cls))
            if any(truth[i] == cls for i in indices) else np.nan
            for cls in (0, 1)
        ])
        paired_sens.append([
            float(np.mean(paired[[i for i in indices if truth[i] == cls]] == cls))
            if any(truth[i] == cls for i in indices) else np.nan
            for cls in (0, 1)
        ])
    rng = np.random.default_rng(seed)
    expected_ba, expected_delta = [], []
    for _ in range(replicates):
        draw = rng.integers(0, len(groups), size=len(groups))
        drawn = np.asarray(source_sens)[draw]
        drawn_pair = np.asarray(paired_sens)[draw]
        ba = np.array([
            np.mean(drawn[np.isfinite(drawn[:, cls]), cls]) if np.any(np.isfinite(drawn[:, cls])) else np.nan
            for cls in (0, 1)
        ])
        pair_ba = np.array([
            np.mean(drawn_pair[np.isfinite(drawn_pair[:, cls]), cls]) if np.any(np.isfinite(drawn_pair[:, cls])) else np.nan
            for cls in (0, 1)
        ])
        expected_ba.append(np.mean(ba) if np.isfinite(ba).all() else np.nan)
        expected_delta.append((np.mean(ba) - np.mean(pair_ba)) if np.isfinite(ba).all() and np.isfinite(pair_ba).all() else np.nan)
    np.testing.assert_allclose(result["bootstrap_balanced_accuracy"], expected_ba, equal_nan=True)
    np.testing.assert_allclose(result["paired_bootstrap_delta_balanced_accuracy"], expected_delta, equal_nan=True)


def test_score_and_classification_reject_invalid_inputs():
    args = _score_inputs()
    args["creek_counts"] = np.array([[1.0, 0.0, 0.0]])
    with pytest.raises(ValueError):
        score_blocks(**args)

    with pytest.raises(ValueError):
        classify(np.array([[0.0]]), np.array(["s"]), np.array([0], dtype=int))
