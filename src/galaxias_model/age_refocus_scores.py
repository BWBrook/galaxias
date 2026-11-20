"""Weighted endpoint discrimination for the prospective age-model refocus.

This module is deliberately pure.  It consumes scores, terminal classes,
source identities, and log weights supplied by a caller; it performs no data
loading, simulation, or biological interpretation.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np


__all__ = [
    "weighted_classify",
    "weighted_recovery_metrics",
]


def _array(value: Any, name: str, ndim: int) -> np.ndarray:
    try:
        result = np.asarray(value)
    except Exception as exc:  # pragma: no cover
        raise ValueError(f"{name} must be array-like") from exc
    if result.ndim != ndim:
        raise ValueError(f"{name} must have {ndim} dimensions")
    return result


def _log_values(value: Any, name: str, ndim: int) -> np.ndarray:
    result = _array(value, name, ndim)
    if result.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain real numeric values")
    result = result.astype(float, copy=False)
    if np.isnan(result).any() or np.isposinf(result).any():
        raise ValueError(f"{name} may contain finite values or -inf, but no NaN/+inf")
    return result


def _labels(value: Any, name: str) -> np.ndarray:
    result = _array(value, name, 1)
    if result.dtype.kind not in "biu":
        raise ValueError(f"{name} must be boolean or 0/1 integers")
    if np.any((result != 0) & (result != 1)):
        raise ValueError(f"{name} must contain only 0 and 1")
    return result.astype(bool, copy=False)


def _source_groups(source_ids: np.ndarray) -> dict[Any, np.ndarray]:
    groups: dict[Any, list[int]] = {}
    for index, source in enumerate(source_ids.tolist()):
        try:
            groups.setdefault(source, []).append(index)
        except TypeError as exc:
            raise ValueError("source_ids must contain hashable values") from exc
    return {source: np.asarray(indices, dtype=int) for source, indices in groups.items()}


def _logsumexp(values: np.ndarray, axis: int | None = None) -> np.ndarray:
    if values.size == 0:
        if axis is None:
            return np.asarray(-math.inf)
        shape = list(values.shape)
        shape.pop(axis)
        return np.full(shape, -math.inf, dtype=float)
    maximum = np.max(values, axis=axis)
    if axis is None:
        if not np.isfinite(maximum):
            return np.asarray(-math.inf)
        return np.asarray(maximum + math.log(float(np.sum(np.exp(values - maximum)))))
    expanded = np.expand_dims(maximum, axis=axis)
    finite = np.isfinite(maximum)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        total = np.sum(np.exp(values - expanded), axis=axis)
        result = maximum + np.log(total)
    return np.where(finite, result, -math.inf)


def _ess_from_log_contributions(log_contributions: np.ndarray) -> np.ndarray:
    """ESS along the last axis, with zero for an all-zero contribution set."""
    if log_contributions.shape[-1] == 0:
        return np.zeros(log_contributions.shape[:-1], dtype=float)
    maximum = np.max(log_contributions, axis=-1)
    finite = np.isfinite(maximum)
    with np.errstate(over="ignore", invalid="ignore"):
        weights = np.where(
            np.expand_dims(finite, axis=-1),
            np.exp(log_contributions - np.expand_dims(maximum, axis=-1)),
            0.0,
        )
    total = np.sum(weights, axis=-1)
    squared = np.sum(weights * weights, axis=-1)
    result = np.zeros_like(total, dtype=float)
    valid = finite & (total > 0.0) & (squared > 0.0)
    result[valid] = total[valid] ** 2 / squared[valid]
    return result


def _validate_classification_inputs(
    log_scores: Any,
    source_ids: Any,
    terminal_labels: Any,
    log_weights: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[Any, np.ndarray]]:
    scores = _log_values(log_scores, "log_scores", 2)
    ids = _array(source_ids, "source_ids", 1)
    labels = _labels(terminal_labels, "terminal_labels")
    weights = _log_values(log_weights, "log_weights", 1)
    if scores.shape[1] != ids.size or ids.size != labels.size or ids.size != weights.size:
        raise ValueError("bank columns, source_ids, terminal_labels, and log_weights must match")
    return scores, ids, labels, weights, _source_groups(ids)


def _class_source_logs(
    scores: np.ndarray,
    labels: np.ndarray,
    log_weights: np.ndarray,
    groups: dict[Any, np.ndarray],
    class_value: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    source_logs: list[np.ndarray] = []
    source_weight_logs: list[float] = []
    positive_sources = 0
    for indices in groups.values():
        selected = indices[(labels[indices] == bool(class_value)) & np.isfinite(log_weights[indices])]
        source_weight_logs.append(float(_logsumexp(log_weights[selected])))
        if selected.size:
            positive_sources += 1
            source_logs.append(_logsumexp(scores[:, selected] + log_weights[selected], axis=1))
        else:
            source_logs.append(np.full(scores.shape[0], -math.inf, dtype=float))
    return (
        np.column_stack(source_logs) if source_logs else np.empty((scores.shape[0], 0), dtype=float),
        np.asarray(source_weight_logs, dtype=float),
        positive_sources,
    )


def _validate_threshold(value: Any, name: str, *, integer: bool = False) -> float | int:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be positive")
    if integer:
        if not isinstance(value, (int, np.integer)) or int(value) < 1:
            raise ValueError(f"{name} must be a positive integer")
        return int(value)
    if not isinstance(value, (int, float, np.number)) or not math.isfinite(float(value)) or float(value) <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return float(value)


def weighted_classify(
    log_scores: Any,
    source_ids: Any,
    terminal_labels: Any,
    log_weights: Any,
    *,
    minimum_sources_per_class: int = 8,
    minimum_prior_ess: float = 4.0,
    minimum_post_ess: float = 4.0,
) -> dict[str, np.ndarray]:
    """Classify rows using source-weighted, class-normalized bank evidence.

    ``log_weights`` are history weights.  Replicates are retained in the
    weighted evidence, while source counts and both ESS diagnostics aggregate
    each source's contributions across its class-specific histories.  The
    returned ``evidence`` values are log class-normalized evidences.
    """
    scores, ids, labels, weights, groups = _validate_classification_inputs(
        log_scores, source_ids, terminal_labels, log_weights
    )
    minimum_sources = _validate_threshold(minimum_sources_per_class, "minimum_sources_per_class", integer=True)
    minimum_prior = _validate_threshold(minimum_prior_ess, "minimum_prior_ess")
    minimum_post = _validate_threshold(minimum_post_ess, "minimum_post_ess")
    n_data = scores.shape[0]
    evidence = np.full((n_data, 2), -math.inf, dtype=float)
    prior_ess = np.zeros(2, dtype=float)
    post_ess = np.zeros((n_data, 2), dtype=float)
    source_counts = np.zeros(2, dtype=int)
    for class_value in (0, 1):
        source_logs, source_weight_logs, positive_sources = _class_source_logs(
            scores, labels, weights, groups, class_value
        )
        source_counts[class_value] = positive_sources
        denominator = _logsumexp(source_weight_logs)
        numerator = _logsumexp(source_logs, axis=1)
        if np.isfinite(denominator):
            evidence[:, class_value] = numerator - denominator
        prior_ess[class_value] = float(_ess_from_log_contributions(source_weight_logs[None, :])[0])
        post_ess[:, class_value] = _ess_from_log_contributions(source_logs)
    log_ratio = np.zeros(n_data, dtype=float)
    both_finite = np.isfinite(evidence[:, 0]) & np.isfinite(evidence[:, 1])
    log_ratio[both_finite] = evidence[both_finite, 1] - evidence[both_finite, 0]
    only_one = np.isfinite(evidence[:, 0]) ^ np.isfinite(evidence[:, 1])
    log_ratio[only_one & np.isfinite(evidence[:, 1])] = math.inf
    log_ratio[only_one & np.isfinite(evidence[:, 0])] = -math.inf
    prediction = np.full(n_data, -1, dtype=np.int8)
    adequate_class_support = bool(np.all(source_counts >= minimum_sources))
    adequate_prior = bool(np.all(prior_ess >= minimum_prior))
    adequate_rows = np.all(post_ess >= minimum_post, axis=1)
    if adequate_class_support and adequate_prior:
        decisive = adequate_rows & (np.abs(log_ratio) > 1e-12)
        prediction[decisive & (log_ratio > 0)] = 1
        prediction[decisive & (log_ratio < 0)] = 0
    counts = np.broadcast_to(source_counts, (n_data, 2)).copy()
    return {
        "evidence": evidence,
        "log_ratio": log_ratio,
        "prediction": prediction,
        "counts": counts,
        "priorESS": prior_ess,
        "postESS": post_ess,
    }


def _validate_prediction(value: Any, name: str, n_data: int) -> np.ndarray:
    result = _array(value, name, 1)
    if result.shape[0] != n_data or result.dtype.kind not in "iu":
        raise ValueError(f"{name} must be an integer vector of length {n_data}")
    if np.any(~np.isin(result, (-1, 0, 1))):
        raise ValueError(f"{name} values must be -1, 0, or 1")
    return result.astype(np.int8, copy=False)


def _weighted_sensitivities(
    prediction: np.ndarray,
    truth: np.ndarray,
    source_ids: np.ndarray,
    log_weights: np.ndarray,
    *,
    multiplicities: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    effective_logs = np.asarray(log_weights, dtype=float).copy()
    if multiplicities is not None:
        with np.errstate(divide="ignore"):
            effective_logs = np.where(multiplicities > 0, effective_logs + np.log(multiplicities), -math.inf)
    source_groups = _source_groups(source_ids)
    sensitivity = np.full(2, math.nan, dtype=float)
    class_weight = np.zeros(2, dtype=float)
    source_weight_logs: list[np.ndarray] = []
    correct_weight = np.zeros(2, dtype=float)
    relative_weights = np.zeros(effective_logs.shape, dtype=float)
    for class_value in (0, 1):
        row_class = truth == bool(class_value)
        class_logs = effective_logs[row_class]
        finite = np.isfinite(class_logs)
        if np.any(finite):
            maximum = float(np.max(class_logs[finite]))
            relative = np.zeros(class_logs.shape, dtype=float)
            relative[finite] = np.exp(class_logs[finite] - maximum)
            class_weight[class_value] = float(np.sum(relative))
            correct_weight[class_value] = float(np.sum(relative[prediction[row_class] == class_value]))
            relative_weights[row_class] = relative
            if class_weight[class_value] > 0:
                sensitivity[class_value] = correct_weight[class_value] / class_weight[class_value]
        logs = []
        for indices in source_groups.values():
            selected = indices[row_class[indices]]
            logs.append(float(_logsumexp(effective_logs[selected])))
        source_weight_logs.append(np.asarray(logs, dtype=float))
    source_ess = np.asarray(
        [float(_ess_from_log_contributions(logs[None, :])[0]) for logs in source_weight_logs], dtype=float
    )
    return sensitivity, source_ess, class_weight, relative_weights


def _percentile(values: np.ndarray) -> np.ndarray:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.array([math.nan, math.nan], dtype=float)
    return np.percentile(finite, [2.5, 97.5])


def _source_universe(source_ids: np.ndarray, universe: Any | None) -> tuple[list[Any], np.ndarray]:
    observed = _source_groups(source_ids)
    if universe is None:
        values = list(observed)
    else:
        raw = _array(universe, "truth_source_universe", 1).tolist()
        try:
            values = list(dict.fromkeys(raw))
        except TypeError as exc:
            raise ValueError("truth_source_universe must contain hashable unique values") from exc
        if len(values) != len(raw):
            raise ValueError("truth_source_universe must not contain duplicate source IDs")
        missing = [source for source in observed if source not in set(values)]
        if missing:
            raise ValueError("truth_source_universe must include every observed source ID")
    index = {source: position for position, source in enumerate(values)}
    return values, np.asarray([index[source] for source in source_ids.tolist()], dtype=int)


def _aggregate_truth_components(
    predictions: np.ndarray,
    truth: np.ndarray,
    source_ids: np.ndarray,
    log_weights: np.ndarray,
    universe: Any | None,
) -> dict[str, np.ndarray]:
    """Aggregate class/source weights once for primary and paired predictions."""
    source_values, source_index = _source_universe(source_ids, universe)
    n_blocks, n_data = predictions.shape
    n_sources = len(source_values)
    source_weights = np.zeros((2, n_sources), dtype=float)
    correct_weights = np.zeros((n_blocks, 2, n_sources), dtype=float)
    for class_value in (0, 1):
        rows = truth == bool(class_value)
        finite = rows & np.isfinite(log_weights)
        if not np.any(finite):
            continue
        maximum = float(np.max(log_weights[finite]))
        relative = np.zeros(n_data, dtype=float)
        relative[finite] = np.exp(log_weights[finite] - maximum)
        np.add.at(source_weights[class_value], source_index[finite], relative[finite])
        for block in range(n_blocks):
            correct = finite & (predictions[block] == class_value)
            np.add.at(correct_weights[block, class_value], source_index[correct], relative[correct])
    class_weight = np.sum(source_weights, axis=1)
    sensitivity = np.full((n_blocks, 2), math.nan, dtype=float)
    for block in range(n_blocks):
        with np.errstate(divide="ignore", invalid="ignore"):
            sensitivity[block] = np.sum(correct_weights[block], axis=1) / class_weight
    source_ess = np.zeros(2, dtype=float)
    source_counts = np.sum(source_weights > 0.0, axis=1).astype(int)
    max_source_share = np.zeros(2, dtype=float)
    for class_value in (0, 1):
        if class_weight[class_value] > 0.0:
            source_ess[class_value] = class_weight[class_value] ** 2 / np.sum(source_weights[class_value] ** 2)
            max_source_share[class_value] = np.max(source_weights[class_value]) / class_weight[class_value]
    return {
        "source_values": np.asarray(source_values, dtype=object),
        "source_index": source_index,
        "source_weights": source_weights,
        "correct_weights": correct_weights,
        "class_weight": class_weight,
        "sensitivity": sensitivity,
        "source_ess": source_ess,
        "source_counts": source_counts,
        "max_source_share": max_source_share,
    }


def _paired_map(
    paired_prediction: Any | None,
    paired_predictions: Mapping[str, Any] | Any | None,
) -> dict[str, Any]:
    if paired_prediction is not None and paired_predictions is not None:
        raise ValueError("provide only one of paired_prediction and paired_predictions")
    if paired_predictions is not None:
        if isinstance(paired_predictions, Mapping):
            if not paired_predictions:
                raise ValueError("paired_predictions must be a nonempty mapping")
            return dict(paired_predictions)
        if isinstance(paired_predictions, (list, tuple)) and paired_predictions:
            return {f"paired_{index}": value for index, value in enumerate(paired_predictions)}
        raise ValueError("paired_predictions must be a nonempty mapping or sequence")
    if paired_prediction is None:
        return {}
    return {"paired": paired_prediction}


def weighted_recovery_metrics(
    prediction: Any,
    truth_label: Any,
    truth_source_ids: Any,
    log_weights: Any,
    *,
    coherent_mask: Any | None = None,
    truth_source_universe: Any | None = None,
    paired_prediction: Any | None = None,
    paired_predictions: Mapping[str, Any] | list[Any] | tuple[Any, ...] | None = None,
    bootstrap_seed: int = 20261002,
    bootstrap_replicates: int = 1000,
    minimum_sources_per_class: int = 16,
    minimum_source_ess: float = 16.0,
) -> dict[str, Any]:
    """Return source-weighted truth recovery and source-cluster uncertainty."""
    raw_prediction = _array(prediction, "prediction", 1)
    n_data = raw_prediction.size
    pred = _validate_prediction(raw_prediction, "prediction", n_data)
    truth = _labels(truth_label, "truth_label")
    ids = _array(truth_source_ids, "truth_source_ids", 1)
    weights = _log_values(log_weights, "log_weights", 1)
    if truth.size != n_data or ids.size != n_data or weights.size != n_data:
        raise ValueError("prediction, truth_label, truth_source_ids, and log_weights must match")
    if coherent_mask is None:
        mask = np.ones(n_data, dtype=bool)
    else:
        mask_array = _array(coherent_mask, "coherent_mask", 1)
        if mask_array.size != n_data or mask_array.dtype.kind != "b":
            raise ValueError("coherent_mask must be boolean and match prediction")
        mask = mask_array.astype(bool, copy=False)
    pred, truth, ids, weights = pred[mask], truth[mask], ids[mask], weights[mask]
    minimum_sources = _validate_threshold(minimum_sources_per_class, "minimum_sources_per_class", integer=True)
    minimum_ess = _validate_threshold(minimum_source_ess, "minimum_source_ess")
    if isinstance(bootstrap_seed, (bool, np.bool_)) or not isinstance(bootstrap_seed, (int, np.integer)):
        raise ValueError("bootstrap_seed must be an integer")
    if isinstance(bootstrap_replicates, (bool, np.bool_)) or not isinstance(bootstrap_replicates, (int, np.integer)) or int(bootstrap_replicates) < 1:
        raise ValueError("bootstrap_replicates must be a positive integer")
    paired_map = _paired_map(paired_prediction, paired_predictions)
    paired_arrays = {name: _validate_prediction(value, f"paired_predictions[{name}]", n_data)[mask] for name, value in paired_map.items()}
    block_names = ["primary", *paired_arrays]
    block_predictions = np.vstack([pred, *paired_arrays.values()])
    aggregate = _aggregate_truth_components(block_predictions, truth, ids, weights, truth_source_universe)
    sensitivity = aggregate["sensitivity"][0]
    source_ess = aggregate["source_ess"]
    class_weight = aggregate["class_weight"]
    distinct_counts = aggregate["source_counts"]
    source_weights = aggregate["source_weights"]
    correct_weights = aggregate["correct_weights"]
    source_values = aggregate["source_values"].tolist()
    balanced_accuracy = float(np.mean(sensitivity)) if np.isfinite(sensitivity).all() else math.nan
    n_correct = int(np.sum(pred == truth))
    n_abstentions = int(np.sum(pred == -1))
    rng = np.random.default_rng(int(bootstrap_seed))
    n_sources = len(source_values)
    bootstrap_ba = np.full(int(bootstrap_replicates), math.nan, dtype=float)
    paired_bootstrap: dict[str, np.ndarray] = {
        name: np.full(int(bootstrap_replicates), math.nan, dtype=float) for name in paired_arrays
    }
    deltas: dict[str, np.ndarray] = {
        name: np.full(int(bootstrap_replicates), math.nan, dtype=float) for name in paired_arrays
    }
    if n_sources:
        draws = rng.integers(0, n_sources, size=(int(bootstrap_replicates), n_sources))
        multiplicities = np.zeros((int(bootstrap_replicates), n_sources), dtype=float)
        row_indices = np.repeat(np.arange(int(bootstrap_replicates)), n_sources)
        np.add.at(multiplicities, (row_indices, draws.ravel()), 1.0)
        denominators = multiplicities @ source_weights.T
        numerators = np.einsum("bu,acu->bac", multiplicities, correct_weights)
        with np.errstate(divide="ignore", invalid="ignore"):
            bootstrap_sensitivity = numerators / denominators[:, None, :]
        valid = np.isfinite(bootstrap_sensitivity[:, 0]).all(axis=1)
        bootstrap_ba[valid] = np.mean(bootstrap_sensitivity[valid, 0], axis=1)
        for block_index, name in enumerate(paired_arrays, start=1):
            block_sensitivity = bootstrap_sensitivity[:, block_index]
            block_valid = np.isfinite(block_sensitivity).all(axis=1)
            paired_bootstrap[name][block_valid] = np.mean(block_sensitivity[block_valid], axis=1)
            both_valid = valid & block_valid
            deltas[name][both_valid] = bootstrap_ba[both_valid] - paired_bootstrap[name][both_valid]
    confusion = np.zeros((2, 3), dtype=np.int64)
    for class_value in (0, 1):
        rows = truth == bool(class_value)
        confusion[class_value, 0] = int(np.sum(rows & (pred == 0)))
        confusion[class_value, 1] = int(np.sum(rows & (pred == 1)))
        confusion[class_value, 2] = int(np.sum(rows & (pred == -1)))
    adequate = bool(np.all(distinct_counts >= minimum_sources) and np.all(source_ess >= minimum_ess))
    ci95 = _percentile(bootstrap_ba)
    gate_passed = bool(
        adequate
        and np.isfinite(sensitivity).all()
        and np.all(sensitivity >= 0.70)
        and balanced_accuracy >= 0.75
        and np.isfinite(ci95[0])
        and ci95[0] > 0.5
    )
    paired_results: dict[str, dict[str, Any]] = {}
    for block_index, (name, values) in enumerate(paired_arrays.items(), start=1):
        paired_sens = aggregate["sensitivity"][block_index]
        paired_ess = source_ess
        paired_class_weight = class_weight
        paired_ba = float(np.mean(paired_sens)) if np.isfinite(paired_sens).all() else math.nan
        paired_results[name] = {
            "sensitivity": paired_sens,
            "balanced_accuracy": paired_ba,
            "sourceESS": paired_ess,
            "bootstrap_balanced_accuracy": paired_bootstrap[name],
            "delta_balanced_accuracy": balanced_accuracy - paired_ba,
            "delta_ci95": _percentile(deltas[name]),
            "class_weight": paired_class_weight,
        }
    result: dict[str, Any] = {
        "sensitivity": sensitivity,
        "balanced_accuracy": balanced_accuracy,
        "source_cluster_ci95": ci95,
        "balanced_accuracy_ci95": ci95,
        "bootstrap_balanced_accuracy": bootstrap_ba,
        "truth_source_counts": distinct_counts,
        "sourceESS": source_ess,
        "class_weight": class_weight,
        "counts": {
            "n_data": int(pred.size),
            "n_truth_loss": int(np.sum(truth == 0)),
            "n_truth_persist": int(np.sum(truth == 1)),
            "n_correct": n_correct,
            "n_abstentions": n_abstentions,
            "n_sources": int(np.sum(np.any(source_weights > 0.0, axis=0))),
        },
        "confusion": confusion,
        "truth_coverage_sufficient": bool(np.all(distinct_counts >= minimum_sources)),
        "source_ess_sufficient": bool(np.all(source_ess >= minimum_ess)),
        "assessed": adequate,
        "unassessed": not adequate,
        "gate_passed": gate_passed,
        "paired": paired_results,
        "MCdiagnostics": {
            "counts": distinct_counts,
            "sourceESS": source_ess,
            "max_source_share": aggregate["max_source_share"],
        },
    }
    for name, paired_result in paired_results.items():
        if name == "paired":
            result["paired_delta_balanced_accuracy"] = paired_result["delta_balanced_accuracy"]
            result["paired_delta_balanced_accuracy_ci95"] = paired_result["delta_ci95"]
    return result
