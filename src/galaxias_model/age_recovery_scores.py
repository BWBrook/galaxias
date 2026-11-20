"""Likelihood blocks and source-balanced recovery summaries.

The functions in this module are deliberately pure.  They operate on already
generated exposure/observation arrays and do not load data, simulate histories,
or use terminal truth labels while scoring or classifying an inference bank.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np


__all__ = ["score_blocks", "classify", "recovery_metrics"]


def _array(value: Any, name: str, ndim: int) -> np.ndarray:
    try:
        result = np.asarray(value)
    except Exception as exc:  # pragma: no cover - numpy's exception is variable
        raise ValueError(f"{name} must be an array-like value") from exc
    if result.ndim != ndim:
        raise ValueError(f"{name} must have {ndim} dimensions")
    return result


def _finite_nonnegative_array(value: Any, name: str, ndim: int) -> np.ndarray:
    result = _array(value, name, ndim)
    if result.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain real numeric values")
    result = result.astype(float, copy=False)
    if not np.isfinite(result).all() or np.any(result < 0):
        raise ValueError(f"{name} must be finite and nonnegative")
    return result


def _nonnegative_integer_array(value: Any, name: str, ndim: int) -> np.ndarray:
    result = _array(value, name, ndim)
    if result.dtype.kind not in "iu":
        raise ValueError(f"{name} must contain nonnegative integers")
    if np.any(result < 0):
        raise ValueError(f"{name} must contain nonnegative integers")
    return result.astype(np.int64, copy=False)


def _boolean_array(value: Any, name: str, ndim: int) -> np.ndarray:
    result = _array(value, name, ndim)
    if result.dtype.kind != "b":
        raise ValueError(f"{name} must be boolean")
    return result.astype(bool, copy=False)


def _power(value: Any, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.number)):
        raise ValueError(f"{name} must be a finite number in (0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 < result <= 1.0:
        raise ValueError(f"{name} must be a finite number in (0, 1]")
    return result


def _rate(value: Any, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.number)):
        raise ValueError(f"{name} must be a finite nonnegative number")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be a finite nonnegative number")
    return result


def _log_conditional_allocation(exposures: np.ndarray, equivalents: np.ndarray, power: float) -> np.ndarray:
    """Return powered conditional allocation scores for paired two-block data."""
    n_data = equivalents.shape[0]
    n_bank = exposures.shape[0]
    output = np.zeros((n_data, n_bank), dtype=float)
    for bank_index, exposure in enumerate(exposures):
        maximum = float(np.max(exposure)) if exposure.size else 0.0
        if maximum == 0.0:
            positive = np.any(equivalents > 0.0, axis=1)
            output[positive, bank_index] = -math.inf
            continue
        scaled = exposure / maximum
        denominator = math.log(maximum) + math.log(float(np.sum(scaled)))
        log_exposure = np.full(exposure.shape, -math.inf, dtype=float)
        positive_exposure = exposure > 0.0
        log_exposure[positive_exposure] = np.log(exposure[positive_exposure])
        for component in range(exposure.shape[0]):
            positive_equivalent = equivalents[:, component] > 0.0
            if not np.any(positive_equivalent):
                continue
            if not positive_exposure[component]:
                output[positive_equivalent, bank_index] = -math.inf
                continue
            output[positive_equivalent, bank_index] += (
                equivalents[positive_equivalent, component]
                * (log_exposure[component] - denominator)
            )
        output[:, bank_index] *= power
    return output


def _log_creek_multinomial(
    exposures: np.ndarray, counts: np.ndarray, power: float
) -> np.ndarray:
    """Return powered log multinomial allocation scores, omitting its constant."""
    n_data = counts.shape[0]
    n_bank = exposures.shape[0]
    output = np.zeros((n_data, n_bank), dtype=float)
    totals = np.sum(counts, axis=1)
    for bank_index, exposure in enumerate(exposures):
        maximum = float(np.max(exposure)) if exposure.size else 0.0
        positive_total = totals > 0
        if maximum == 0.0:
            output[positive_total, bank_index] = -math.inf
            continue
        denominator = math.log(maximum) + math.log(float(np.sum(exposure / maximum)))
        log_exposure = np.full(exposure.shape, -math.inf, dtype=float)
        positive_exposure = exposure > 0.0
        log_exposure[positive_exposure] = np.log(exposure[positive_exposure])
        for component in range(exposure.shape[0]):
            positive_count = counts[:, component] > 0
            if not np.any(positive_count):
                continue
            if not positive_exposure[component]:
                output[positive_count, bank_index] = -math.inf
                continue
            output[positive_count, bank_index] += (
                counts[positive_count, component]
                * (log_exposure[component] - denominator)
            )
    output *= power
    return output


def _log_binary_observations(
    exposures: np.ndarray, observed: np.ndarray, q: float
) -> np.ndarray:
    n_data, n_binary = observed.shape
    n_bank = exposures.shape[0]
    output = np.zeros((n_data, n_bank), dtype=float)
    for binary_index in range(n_binary):
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            mean = q * exposures[:, binary_index]
        positive_mean = mean > 0.0
        log_positive = np.full(n_bank, -math.inf, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            log_positive[positive_mean] = np.log(-np.expm1(-mean[positive_mean]))
        positive_rows = observed[:, binary_index]
        negative_rows = ~positive_rows
        if np.any(positive_rows):
            output[positive_rows, :] += log_positive
        if np.any(negative_rows):
            output[negative_rows, :] -= mean
    return output


def score_blocks(
    creek_exposures: Any,
    lake_exposures: Any,
    binary_exposures: Any,
    creek_counts: Any,
    lake_equivalents: Any,
    binary_observed: Any,
    *,
    q: float,
    creek_power: float,
    lake_power: float,
) -> dict[str, np.ndarray]:
    """Score observations against every inference-bank exposure history.

    Creek counts use the conditional multinomial allocation likelihood, with
    the data-only multinomial coefficient omitted.  Lake equivalents use a
    powered allocation score and are therefore not treated as exact integer
    counts.  Binary observations use ``P(Y=1)=1-exp(-q*X)`` and its exact
    complement for negatives.
    """
    creek_x = _finite_nonnegative_array(creek_exposures, "creek_exposures", 2)
    lake_x = _finite_nonnegative_array(lake_exposures, "lake_exposures", 2)
    binary_x = _finite_nonnegative_array(binary_exposures, "binary_exposures", 2)
    creek_y = _nonnegative_integer_array(creek_counts, "creek_counts", 2)
    lake_y = _finite_nonnegative_array(lake_equivalents, "lake_equivalents", 2)
    binary_y = _boolean_array(binary_observed, "binary_observed", 2)
    if creek_x.shape[1] != 3 or lake_x.shape[1] != 2 or creek_y.shape[1] != 3 or lake_y.shape[1] != 2:
        raise ValueError("creek and lake arrays must have 3 and 2 columns respectively")
    n_bank = creek_x.shape[0]
    if lake_x.shape[0] != n_bank or binary_x.shape[0] != n_bank:
        raise ValueError("all exposure arrays must have the same bank size")
    n_data = creek_y.shape[0]
    if lake_y.shape[0] != n_data or binary_y.shape[0] != n_data:
        raise ValueError("all observation arrays must have the same data size")
    if binary_x.shape[1] != binary_y.shape[1]:
        raise ValueError("binary exposure and observation columns must match")
    rate = _rate(q, "q")
    creek_tau = _power(creek_power, "creek_power")
    lake_tau = _power(lake_power, "lake_power")

    creek = _log_creek_multinomial(creek_x, creek_y, creek_tau)
    lake = _log_conditional_allocation(lake_x, lake_y, lake_tau)
    binary = _log_binary_observations(binary_x, binary_y, rate)
    total = creek + lake + binary
    for name, result in (("creek", creek), ("lake", lake), ("binary", binary), ("total", total)):
        if np.isnan(result).any():
            raise FloatingPointError(f"{name} score contains NaN")
    return {"creek": creek, "lake": lake, "binary": binary, "total": total}


def _source_key(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    try:
        hash(value)
    except TypeError as exc:
        raise ValueError("source_ids must contain hashable identifiers") from exc
    if value is None or (isinstance(value, float) and math.isnan(value)):
        raise ValueError("source_ids cannot contain missing identifiers")
    return value


def _source_groups(source_ids: np.ndarray) -> dict[Any, list[int]]:
    groups: dict[Any, list[int]] = {}
    for index, raw_value in enumerate(source_ids):
        key = _source_key(raw_value)
        groups.setdefault(key, []).append(index)
    return groups


def _logmeanexp(values: np.ndarray, axis: int = 0) -> np.ndarray:
    maximum = np.max(values, axis=axis)
    result = np.full(maximum.shape, -math.inf, dtype=float)
    finite = np.isfinite(maximum)
    if np.any(finite):
        finite_expanded = np.expand_dims(finite, axis=axis)
        with np.errstate(over="ignore", invalid="ignore"):
            shifted = np.where(
                finite_expanded,
                values - np.expand_dims(maximum, axis=axis),
                -math.inf,
            )
            result[finite] = maximum[finite] + np.log(np.sum(np.exp(shifted), axis=axis)[finite])
        result[finite] -= math.log(values.shape[axis])
    return result


def _validate_score_inputs(
    log_scores: Any, source_ids: Any, terminal_labels: Any
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    raw_scores = _array(log_scores, "log_scores", 2)
    if raw_scores.dtype.kind not in "iuf":
        raise ValueError("log_scores must contain real numeric values")
    scores = raw_scores.astype(float, copy=False)
    if np.isnan(scores).any() or np.isposinf(scores).any():
        raise ValueError("log_scores may contain finite values or -inf, but no NaN/+inf")
    ids = _array(source_ids, "source_ids", 1)
    labels = _boolean_array(terminal_labels, "terminal_labels", 1)
    if scores.shape[1] != ids.shape[0] or ids.shape[0] != labels.shape[0]:
        raise ValueError("log_scores columns, source_ids, and terminal_labels must match")
    _source_groups(ids)
    return scores, ids, labels


def _class_contributions(
    scores: np.ndarray, source_ids: np.ndarray, labels: np.ndarray
) -> tuple[list[np.ndarray], np.ndarray]:
    groups = _source_groups(source_ids)
    by_class: list[list[np.ndarray]] = [[], []]
    source_counts = np.zeros(2, dtype=int)
    for class_value in (0, 1):
        for source, indices in groups.items():
            selected = [index for index in indices if bool(labels[index]) == bool(class_value)]
            if selected:
                by_class[class_value].append(_logmeanexp(scores[:, selected], axis=1))
                source_counts[class_value] += 1
    return [
        np.column_stack(by_class[0]) if by_class[0] else np.empty((scores.shape[0], 0)),
        np.column_stack(by_class[1]) if by_class[1] else np.empty((scores.shape[0], 0)),
    ], source_counts


def _class_ess(contributions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if contributions.shape[1] == 0:
        return np.full(contributions.shape[0], -math.inf), np.zeros(contributions.shape[0])
    log_evidence = _logmeanexp(contributions, axis=1)
    ess = np.zeros(contributions.shape[0], dtype=float)
    maximum = np.max(contributions, axis=1)
    finite = np.isfinite(maximum)
    with np.errstate(over="ignore", invalid="ignore"):
        weights = np.where(
            np.expand_dims(finite, axis=1),
            np.exp(contributions - np.expand_dims(maximum, axis=1)),
            0.0,
        )
    total = np.sum(weights, axis=1)
    squared = np.sum(weights * weights, axis=1)
    valid = finite & (total > 0.0) & (squared > 0.0)
    ess[valid] = (total[valid] * total[valid]) / squared[valid]
    return log_evidence, ess


def classify(
    log_scores: Any,
    source_ids: Any,
    terminal_labels: Any,
    *,
    minimum_sources_per_class: int = 8,
    minimum_class_ess: float = 4,
) -> dict[str, np.ndarray]:
    """Classify data rows with source-balanced likelihood evidence.

    Replicates are first averaged within each source and terminal class.  The
    resulting source likelihoods are then averaged over distinct sources in
    each class, so extra bank histories from one source cannot increase its
    class weight.  A class with inadequate source coverage or source ESS is
    abstained from through the row-level ``prediction`` result.
    """
    scores, ids, labels = _validate_score_inputs(log_scores, source_ids, terminal_labels)
    if isinstance(minimum_sources_per_class, (bool, np.bool_)) or not isinstance(minimum_sources_per_class, (int, np.integer)):
        raise ValueError("minimum_sources_per_class must be a positive integer")
    minimum_sources = int(minimum_sources_per_class)
    if minimum_sources < 1:
        raise ValueError("minimum_sources_per_class must be a positive integer")
    if isinstance(minimum_class_ess, (bool, np.bool_)) or not isinstance(minimum_class_ess, (int, float, np.number)):
        raise ValueError("minimum_class_ess must be a finite positive number")
    minimum_ess = float(minimum_class_ess)
    if not math.isfinite(minimum_ess) or minimum_ess <= 0.0:
        raise ValueError("minimum_class_ess must be a finite positive number")

    contributions, source_counts = _class_contributions(scores, ids, labels)
    log_evidence = np.empty((scores.shape[0], 2), dtype=float)
    ess = np.empty((scores.shape[0], 2), dtype=float)
    for class_value in (0, 1):
        log_evidence[:, class_value], ess[:, class_value] = _class_ess(contributions[class_value])
    log_ratio = np.zeros(scores.shape[0], dtype=float)
    both_finite = np.isfinite(log_evidence[:, 0]) & np.isfinite(log_evidence[:, 1])
    log_ratio[both_finite] = log_evidence[both_finite, 1] - log_evidence[both_finite, 0]
    class0_zero = ~np.isfinite(log_evidence[:, 0])
    class1_zero = ~np.isfinite(log_evidence[:, 1])
    log_ratio[class0_zero & ~class1_zero] = math.inf
    log_ratio[~class0_zero & class1_zero] = -math.inf
    prediction = np.full(scores.shape[0], -1, dtype=np.int8)
    adequate = (
        (source_counts[0] >= minimum_sources)
        and (source_counts[1] >= minimum_sources)
    )
    if adequate:
        adequate_rows = (ess[:, 0] >= minimum_ess) & (ess[:, 1] >= minimum_ess)
        decisive = adequate_rows & ~((class0_zero & class1_zero) | (np.abs(log_ratio) <= 1e-12))
        prediction[decisive & (log_ratio > 0)] = 1
        prediction[decisive & (log_ratio < 0)] = 0
    sourcecounts = np.broadcast_to(source_counts, (scores.shape[0], 2)).copy()
    return {
        "prediction": prediction,
        "log_ratio": log_ratio,
        "ess0": ess[:, 0],
        "ess1": ess[:, 1],
        "sourcecounts": sourcecounts,
    }


def _validate_predictions(value: Any, name: str, n_data: int) -> np.ndarray:
    result = _array(value, name, 1)
    if result.shape[0] != n_data or result.dtype.kind not in "iu":
        raise ValueError(f"{name} must be an integer vector of length {n_data}")
    if np.any(~np.isin(result, (-1, 0, 1))):
        raise ValueError(f"{name} values must be -1, 0, or 1")
    return result.astype(np.int8, copy=False)


def _validate_truth_labels(value: Any, n_data: int) -> np.ndarray:
    result = _array(value, "truth_label", 1)
    if result.shape[0] != n_data or result.dtype.kind not in "biu":
        raise ValueError(f"truth_label must be a boolean or 0/1 integer vector of length {n_data}")
    if np.any((result != 0) & (result != 1)):
        raise ValueError("truth_label must contain only 0 and 1")
    return result.astype(bool, copy=False)


def _source_sensitivities(
    prediction: np.ndarray,
    truth_label: np.ndarray,
    groups: dict[Any, list[int]],
    selected_sources: list[Any] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    sources = list(groups)
    source_sensitivities = _per_source_sensitivities(prediction, truth_label, groups)
    if selected_sources is None:
        selected_indices = np.arange(len(sources), dtype=int)
    else:
        source_index = {source: index for index, source in enumerate(sources)}
        selected_indices = np.asarray([source_index[source] for source in selected_sources], dtype=int)
    selected = source_sensitivities[selected_indices]
    sensitivities = _nanmean_columns(selected)
    counts = np.sum(np.isfinite(selected), axis=0).astype(int)
    return sensitivities, counts


def _per_source_sensitivities(
    prediction: np.ndarray,
    truth_label: np.ndarray,
    groups: dict[Any, list[int]],
) -> np.ndarray:
    """Return one sensitivity pair per source, with NaN for absent classes."""
    result = np.full((len(groups), 2), np.nan, dtype=float)
    for source_index, indices in enumerate(groups.values()):
        source_truth = truth_label[indices]
        source_prediction = prediction[indices]
        for class_value in (0, 1):
            rows = source_truth == bool(class_value)
            if np.any(rows):
                result[source_index, class_value] = float(
                    np.mean(source_prediction[rows] == class_value)
                )
    return result


def _nanmean_columns(values: np.ndarray) -> np.ndarray:
    valid = np.isfinite(values)
    counts = np.sum(valid, axis=0)
    totals = np.sum(np.where(valid, values, 0.0), axis=0)
    result = np.full(values.shape[1], np.nan, dtype=float)
    present = counts > 0
    result[present] = totals[present] / counts[present]
    return result


def _nanmean_source_draws(values: np.ndarray) -> np.ndarray:
    """Average source sensitivity pairs over bootstrap draws and classes."""
    valid = np.isfinite(values)
    counts = np.sum(valid, axis=1)
    totals = np.sum(np.where(valid, values, 0.0), axis=1)
    result = np.full((values.shape[0], values.shape[2]), np.nan, dtype=float)
    present = counts > 0
    result[present] = totals[present] / counts[present]
    return result


def _confusion(prediction: np.ndarray, truth_label: np.ndarray) -> np.ndarray:
    result = np.zeros((2, 3), dtype=np.int64)
    for class_value in (0, 1):
        rows = truth_label == bool(class_value)
        result[class_value, 0] = int(np.sum(rows & (prediction == 0)))
        result[class_value, 1] = int(np.sum(rows & (prediction == 1)))
        result[class_value, 2] = int(np.sum(rows & (prediction == -1)))
    return result


def _balanced_accuracy(sensitivities: np.ndarray) -> float:
    return float(np.mean(sensitivities)) if np.isfinite(sensitivities).all() else math.nan


def _percentile_ci(values: list[float]) -> np.ndarray:
    finite = np.asarray([value for value in values if math.isfinite(value)], dtype=float)
    if finite.size == 0:
        return np.array([math.nan, math.nan], dtype=float)
    return np.percentile(finite, [2.5, 97.5])


def recovery_metrics(
    prediction: Any,
    truth_label: Any,
    truth_source_ids: Any,
    *,
    paired_prediction: Any | None = None,
    bootstrap_seed: int = 20261001,
    bootstrap_replicates: int = 1000,
) -> dict[str, Any]:
    """Summarise source-macro recovery and its source-cluster uncertainty.

    Bootstrap draws sample truth source IDs with replacement and retain every
    data row belonging to each sampled source.  If a paired prediction is
    supplied, exactly the same source draws are used for its delta interval.
    The recovery gate requires at least 16 distinct truth sources in each
    class, sensitivity at least 0.70 in each class, balanced accuracy at least
    0.75, and a bootstrap lower 95% bound above 0.5.
    """
    raw_prediction = _array(prediction, "prediction", 1)
    truth_ids = _array(truth_source_ids, "truth_source_ids", 1)
    n_data = raw_prediction.shape[0]
    pred = _validate_predictions(raw_prediction, "prediction", n_data)
    truth = _validate_truth_labels(truth_label, n_data)
    if truth_ids.shape[0] != n_data:
        raise ValueError("truth_source_ids must have the same length as prediction")
    groups = _source_groups(truth_ids)
    paired = None
    if paired_prediction is not None:
        paired = _validate_predictions(paired_prediction, "paired_prediction", n_data)
    if isinstance(bootstrap_seed, (bool, np.bool_)) or not isinstance(bootstrap_seed, (int, np.integer)):
        raise ValueError("bootstrap_seed must be an integer")
    if isinstance(bootstrap_replicates, (bool, np.bool_)) or not isinstance(bootstrap_replicates, (int, np.integer)):
        raise ValueError("bootstrap_replicates must be a positive integer")
    replicates = int(bootstrap_replicates)
    if replicates < 1:
        raise ValueError("bootstrap_replicates must be a positive integer")

    sensitivities, source_counts = _source_sensitivities(pred, truth, groups)
    balanced_accuracy = _balanced_accuracy(sensitivities)
    confusion = _confusion(pred, truth)
    source_keys = list(groups)
    rng = np.random.default_rng(int(bootstrap_seed))
    source_sensitivities = _per_source_sensitivities(pred, truth, groups)
    bootstrap_balanced_accuracy: list[float] = []
    bootstrap_delta: list[float] = []
    paired_sensitivities = np.full(2, np.nan, dtype=float)
    paired_balanced_accuracy = math.nan
    paired_source_sensitivities = None
    if paired is not None:
        paired_sensitivities, _ = _source_sensitivities(paired, truth, groups)
        paired_balanced_accuracy = _balanced_accuracy(paired_sensitivities)
        paired_source_sensitivities = _per_source_sensitivities(paired, truth, groups)
    if source_keys:
        # Keep one RNG call per replicate, with the same order as the former
        # explicit loop.  Only the reductions over the drawn source pairs are
        # vectorized; source-level definitions and draw semantics are unchanged.
        draw_indices = np.empty((replicates, len(source_keys)), dtype=int)
        for replicate in range(replicates):
            draw_indices[replicate] = rng.integers(0, len(source_keys), size=len(source_keys))
        drawn_sensitivities = _nanmean_source_draws(source_sensitivities[draw_indices])
        draw_balanced_accuracy = np.full(replicates, np.nan, dtype=float)
        valid_draws = np.isfinite(drawn_sensitivities).all(axis=1)
        draw_balanced_accuracy[valid_draws] = np.mean(drawn_sensitivities[valid_draws], axis=1)
        bootstrap_balanced_accuracy = draw_balanced_accuracy.tolist()
        if paired_source_sensitivities is not None:
            paired_draw_sensitivities = _nanmean_source_draws(paired_source_sensitivities[draw_indices])
            paired_draw_balanced_accuracy = np.full(replicates, np.nan, dtype=float)
            paired_valid_draws = np.isfinite(paired_draw_sensitivities).all(axis=1)
            paired_draw_balanced_accuracy[paired_valid_draws] = np.mean(
                paired_draw_sensitivities[paired_valid_draws], axis=1
            )
            bootstrap_delta = (draw_balanced_accuracy - paired_draw_balanced_accuracy).tolist()
    else:
        bootstrap_balanced_accuracy = [math.nan] * replicates
        if paired_source_sensitivities is not None:
            bootstrap_delta = [math.nan] * replicates
    ci95 = _percentile_ci(bootstrap_balanced_accuracy)
    delta_ci95 = _percentile_ci(bootstrap_delta) if paired is not None else None
    coverage = source_counts.astype(int, copy=True)
    insufficient_truth_coverage = bool(np.any(coverage < 16))
    gate_passed = bool(
        not insufficient_truth_coverage
        and np.isfinite(sensitivities).all()
        and sensitivities[0] >= 0.70
        and sensitivities[1] >= 0.70
        and balanced_accuracy >= 0.75
        and np.isfinite(ci95[0])
        and ci95[0] > 0.5
    )
    counts = {
        "n_data": int(n_data),
        "n_truth_loss": int(np.sum(truth == 0)),
        "n_truth_persist": int(np.sum(truth == 1)),
        "n_correct": int(confusion[0, 0] + confusion[1, 1]),
        "n_abstentions": int(np.sum(pred == -1)),
        "n_sources": int(len(source_keys)),
    }
    result: dict[str, Any] = {
        "source_macro_sensitivity": sensitivities,
        "sensitivity": sensitivities,
        "source_macro_balanced_accuracy": balanced_accuracy,
        "balanced_accuracy": balanced_accuracy,
        "source_cluster_ci95": ci95,
        "balanced_accuracy_ci95": ci95,
        "counts": counts,
        "confusion": confusion,
        "confusion_matrix": confusion,
        "distinct_source_coverage": coverage,
        "source_coverage": coverage,
        "insufficient_truth_coverage": insufficient_truth_coverage,
        "truth_coverage_sufficient": not insufficient_truth_coverage,
        "gate_passed": gate_passed,
        "bootstrap_replicates": replicates,
        "bootstrap_balanced_accuracy": np.asarray(bootstrap_balanced_accuracy, dtype=float),
    }
    if paired is not None:
        result.update(
            {
                "paired_source_macro_sensitivity": paired_sensitivities,
                "paired_balanced_accuracy": paired_balanced_accuracy,
                "paired_delta_balanced_accuracy": balanced_accuracy - paired_balanced_accuracy,
                "paired_delta_balanced_accuracy_ci95": delta_ci95,
                "paired_bootstrap_delta_balanced_accuracy": np.asarray(bootstrap_delta, dtype=float),
            }
        )
    return result
