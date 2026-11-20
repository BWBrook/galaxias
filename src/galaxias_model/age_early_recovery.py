"""Pure numerical helpers for the early-Lake recovery conformal gate.

The functions in this module consume arrays supplied by a caller.  They do
not load observations, inspect terminal outcomes, or run simulations.  In
particular, a failed bank history is represented by ``valid=False`` and
contributes zero to the unconditional source/replicate average.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
from typing import Any

import numpy as np


RESTRICTIONS = ("R_H", "R_T", "R_C", "R_J")
_DEFAULT_BATCH_SIZE = 256


def _numeric_array(value: Any, name: str, ndim: int) -> np.ndarray:
    result = np.asarray(value)
    if result.ndim != ndim or result.dtype.kind not in "biuf":
        raise ValueError(f"{name} must be a numeric array with {ndim} dimensions")
    return result.astype(float, copy=False)


def _validate_power(value: Any) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("power must be finite and in (0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 < result <= 1.0:
        raise ValueError("power must be finite and in (0, 1]")
    return result


def _validate_age1(value: Any) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("age1 must be finite and in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError("age1 must be finite and in [0, 1]")
    return result


def _validate_bank_inputs(
    features: Any,
    means: Any,
    valid: Any,
    source_mask: Any,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, int]:
    raw_features = np.asarray(features)
    if raw_features.ndim != 5 or raw_features.shape[0] != 4 or raw_features.shape[-2:] != (8, 2):
        raise ValueError("features must have shape (4, S, P, 8, 2)")
    if raw_features.dtype.kind not in "biuf":
        raise ValueError("features must contain real numeric values")
    features_array = raw_features.astype(float, copy=False)
    _, n_sources, n_replicates = features_array.shape[:3]
    if n_sources < 1 or n_replicates < 1:
        raise ValueError("features must contain at least one source and replicate")

    means_array = _numeric_array(means, "means", 2)
    if means_array.shape[1] != 8:
        raise ValueError("means must have shape (D, 8)")
    if means_array.shape[0] < 1 or not np.isfinite(means_array).all() or np.any(means_array < 0):
        raise ValueError("means must be nonempty, finite, and nonnegative")

    if valid is None:
        valid_array = np.ones((4, n_sources, n_replicates), dtype=bool)
    else:
        raw_valid = np.asarray(valid)
        if raw_valid.shape != (4, n_sources, n_replicates) or raw_valid.dtype.kind != "b":
            raise ValueError("valid must be boolean with shape (4, S, P)")
        valid_array = raw_valid.astype(bool, copy=False)

    if source_mask is None:
        source_array = np.ones(n_sources, dtype=bool)
    else:
        raw_source = np.asarray(source_mask)
        if raw_source.shape != (n_sources,) or raw_source.dtype.kind != "b":
            raise ValueError("source_mask must be boolean with shape (S,)")
        source_array = raw_source.astype(bool, copy=False)

    # Masked and failed histories are never scored.  Sanitising those entries
    # also permits a caller to retain NaN payloads from a failed simulation.
    effective_valid = valid_array & source_array[None, :, None]
    active_entries = np.broadcast_to(effective_valid[..., None, None], features_array.shape)
    if np.any(~np.isfinite(features_array[active_entries])) or np.any(features_array[active_entries] < 0):
        raise ValueError("valid features must be finite and nonnegative")
    clean_features = np.where(active_entries, features_array, 0.0)
    return clean_features, means_array, effective_valid, source_array, n_sources, n_replicates


def _vectorized_lake_scores(
    features: np.ndarray,
    means: np.ndarray,
    *,
    power: float,
    age1: float,
    batch_size: int = _DEFAULT_BATCH_SIZE,
) -> np.ndarray:
    """Return ``(D, N)`` scores matching lake_history_log_score exactly."""
    n_rows = features.shape[0]
    exposure = features[:, :, 0] + age1 * features[:, :, 1]
    exposure[:, 5:] *= 1.0
    x_total = np.sum(exposure, axis=1)
    x_positive = exposure > 0.0

    mean_totals = np.sum(means, axis=1)
    positive_means = means > 0.0
    scores = np.zeros((means.shape[0], n_rows), dtype=float)
    positive_mean_rows = mean_totals > 0.0
    if not np.any(positive_mean_rows):
        return scores

    # The old score uses counts=12*means, but their common scale cancels from
    # the normalised composition.  Keep the 12 factor in the weighted sum.
    log_p = np.full((n_rows, 8), -math.inf, dtype=float)
    positive_totals = x_total > 0.0
    with np.errstate(divide="ignore", invalid="ignore"):
        log_p[positive_totals] = np.log(exposure[positive_totals]) - np.log(x_total[positive_totals, None])
    with np.errstate(divide="ignore", invalid="ignore"):
        log_q = np.full(means.shape, -math.inf, dtype=float)
        log_q[positive_mean_rows] = np.log(means[positive_mean_rows]) - np.log(mean_totals[positive_mean_rows, None])

    for start in range(0, means.shape[0], int(batch_size)):
        stop = min(start + int(batch_size), means.shape[0])
        q_positive = positive_means[start:stop]
        q_valid = positive_mean_rows[start:stop]
        with np.errstate(invalid="ignore"):
            terms = np.where(
                q_positive[:, None, :],
                12.0 * means[start:stop, None, :] * (log_p[None, :, :] - log_q[start:stop, None, :]),
                0.0,
            )
        score = power * np.sum(terms, axis=2)
        impossible = q_valid[:, None] & (
            (~positive_totals[None, :])
            | np.any(q_positive[:, None, :] & ~x_positive[None, :, :], axis=2)
        )
        score[impossible] = -math.inf
        # Gibbs' inequality makes these scores nonpositive.  The clamp retains
        # the old helper's cross-platform zero-rounding behaviour.
        scores[start:stop] = np.minimum(score, 0.0)
    return scores


def bank_log_support(
    features: Any,
    means: Any,
    *,
    power: float = 1.0 / 12.0,
    age1: float = 0.0,
    source_mask: Any = None,
    valid: Any = None,
    batch_size: int = _DEFAULT_BATCH_SIZE,
) -> np.ndarray:
    """Compute unconditional log-mean support for every mean and restriction.

    ``features`` has shape ``(4, S, P, 8, 2)`` and ``means`` has shape
    ``(D, 8)``.  The output has shape ``(D, 4)``.  Every planned source and
    replicate of each selected source remains in the denominator
    ``selected_sources*P``; invalid selected slots contribute zero.
    """
    if isinstance(batch_size, (bool, np.bool_)) or not isinstance(batch_size, (int, np.integer)) or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    power_value = _validate_power(power)
    age1_value = _validate_age1(age1)
    clean, means_array, effective_valid, source_array, n_sources, n_replicates = _validate_bank_inputs(
        features, means, valid, source_mask
    )
    n_means = means_array.shape[0]
    flat_features = clean.reshape(4 * n_sources * n_replicates, 8, 2)
    flat_valid = effective_valid.reshape(4, n_sources * n_replicates)
    selected_sources = int(np.count_nonzero(source_array))
    if selected_sources == 0:
        return np.full((n_means, 4), -math.inf, dtype=float)
    denominator = float(selected_sources * n_replicates)
    result = np.full((n_means, 4), -math.inf, dtype=float)
    for start in range(0, n_means, int(batch_size)):
        stop = min(start + int(batch_size), n_means)
        scores = _vectorized_lake_scores(
            flat_features,
            means_array[start:stop],
            power=power_value,
            age1=age1_value,
            batch_size=int(batch_size),
        ).reshape(stop - start, 4, n_sources * n_replicates)
        # Remove failed and unselected positions before finding the maximum.
        # A shifted reduction keeps a valid but extremely small support (for
        # example log support around -10,000) finite instead of underflowing
        # its exponent to zero and appearing unsupported.
        scores = np.where(flat_valid[None, :, :], scores, -math.inf)
        with np.errstate(invalid="ignore", over="ignore", under="ignore"):
            maximum = np.max(scores, axis=2)
            shifted = np.exp(scores - maximum[:, :, None])
        shifted = np.where(np.isfinite(maximum)[:, :, None], shifted, 0.0)
        contribution_sum = shifted.sum(axis=2)
        block = np.full(maximum.shape, -math.inf, dtype=float)
        supported = np.isfinite(maximum) & (contribution_sum > 0.0)
        with np.errstate(divide="ignore"):
            block[supported] = maximum[supported] + np.log(contribution_sum[supported]) - math.log(denominator)
        result[start:stop] = block
    return result


def _validate_scores(ell: Any, name: str = "ell") -> np.ndarray:
    result = _numeric_array(ell, name, 2)
    if result.shape[1] != 4 or result.shape[0] < 1 or np.isnan(result).any():
        raise ValueError(f"{name} must have shape (N, 4) and contain no NaN")
    return result


def _safe_subtract(left: np.ndarray, right: float) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        result = left - right
    # Equal infinities have no directional evidence; use a finite tie rather
    # than allowing an undefined NaN to escape into ranks.
    return np.where(np.isnan(result), 0.0, result)


def nonconformity(ell: Any) -> dict[str, np.ndarray]:
    """Return relative and absolute nonconformity scores for four restrictions."""
    values = _validate_scores(ell)
    relative = np.empty_like(values)
    for restriction in range(4):
        other = np.delete(values, restriction, axis=1).max(axis=1)
        relative[:, restriction] = _safe_subtract(other, values[:, restriction])
    unsupported = ~np.isfinite(values).any(axis=1)
    relative[unsupported, :] = math.inf
    absolute = -values
    return {"relative": relative, "absolute": absolute, "unsupported": unsupported}


def conformal_pvalues(calibration_scores: Any, test_scores: Any) -> np.ndarray:
    """Compute conservative split-conformal ranks, retaining infinite values."""
    calibration = np.asarray(calibration_scores)
    test = np.asarray(test_scores)
    if calibration.ndim != 1 or test.ndim != 1:
        raise ValueError("calibration_scores and test_scores must be one-dimensional")
    if calibration.size < 1 or calibration.dtype.kind not in "biuf" or test.dtype.kind not in "biuf":
        raise ValueError("scores must be nonempty numeric arrays")
    calibration = calibration.astype(float, copy=False)
    test = test.astype(float, copy=False)
    if np.isnan(calibration).any() or np.isnan(test).any():
        raise ValueError("scores must not contain NaN")
    counts = np.count_nonzero(calibration[None, :] >= test[:, None], axis=1)
    return (1.0 + counts.astype(float)) / float(calibration.size + 1)


def _validate_alpha(alpha: Any) -> float:
    if isinstance(alpha, (bool, np.bool_)):
        raise ValueError("alpha must be finite and in (0, 1)")
    result = float(alpha)
    if not math.isfinite(result) or not 0.0 < result < 1.0:
        raise ValueError("alpha must be finite and in (0, 1)")
    return result


def restriction_sets(
    cal_by_true: Mapping[str, Any],
    ell_test: Any,
    *,
    alpha: float = 0.05,
    force_allzero_full_set: bool = False,
) -> dict[str, Any]:
    """Build class-conditional restriction sets from relative and absolute ranks."""
    if not isinstance(cal_by_true, Mapping) or set(cal_by_true) != set(RESTRICTIONS):
        raise ValueError(f"cal_by_true must contain exactly {RESTRICTIONS}")
    alpha_value = _validate_alpha(alpha)
    test = _validate_scores(ell_test, "ell_test")
    test_nc = nonconformity(test)
    n_test = test.shape[0]
    p_relative = np.empty((n_test, 4), dtype=float)
    p_absolute = np.empty((n_test, 4), dtype=float)
    for restriction, label in enumerate(RESTRICTIONS):
        calibration = _validate_scores(cal_by_true[label], f"cal_by_true[{label!r}]")
        calibration_nc = nonconformity(calibration)
        p_relative[:, restriction] = conformal_pvalues(
            calibration_nc["relative"][:, restriction], test_nc["relative"][:, restriction]
        )
        p_absolute[:, restriction] = conformal_pvalues(
            calibration_nc["absolute"][:, restriction], test_nc["absolute"][:, restriction]
        )
    threshold = alpha_value / 2.0
    sets = (p_relative > threshold) & (p_absolute > threshold)
    supported = np.isfinite(test).any(axis=1)
    sets[~supported, :] = True
    if force_allzero_full_set:
        sets[np.all(test == 0.0, axis=1), :] = True
    return {
        "sets": sets,
        "p_relative": p_relative,
        "p_absolute": p_absolute,
        "supported": supported,
    }


def _log_binomial_pmf(k: int, n: int, p: float) -> float:
    if p == 0.0:
        return 0.0 if k == 0 else -math.inf
    if p == 1.0:
        return 0.0 if k == n else -math.inf
    return (
        math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
        + k * math.log(p) + (n - k) * math.log1p(-p)
    )


def _logsumexp(values: list[float]) -> float:
    finite = [value for value in values if value != -math.inf]
    if not finite:
        return -math.inf
    maximum = max(finite)
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in finite))


def _log_binomial_tail(k: int, n: int, p: float, *, lower: bool) -> float:
    if lower:
        terms = [_log_binomial_pmf(index, n, p) for index in range(k, n + 1)]
    else:
        terms = [_log_binomial_pmf(index, n, p) for index in range(0, k + 1)]
    return _logsumexp(terms)


def exact_binomial_bounds(k: int, n: int, alpha: float) -> tuple[float, float]:
    """Return lower/upper one-sided exact binomial bounds at tail ``alpha``."""
    if isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    if isinstance(k, (bool, np.bool_)) or not isinstance(k, (int, np.integer)) or k < 0 or k > n:
        raise ValueError("k must be an integer in [0, n]")
    alpha_value = _validate_alpha(alpha)
    n, k = int(n), int(k)
    if n == 0:
        return 0.0, 1.0
    log_alpha = math.log(alpha_value)
    if k == 0:
        lower = 0.0
    else:
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2.0
            if _log_binomial_tail(k, n, mid, lower=True) < log_alpha:
                lo = mid
            else:
                hi = mid
        lower = (lo + hi) / 2.0
    if k == n:
        upper = 1.0
    else:
        lo, hi = 0.0, 1.0
        for _ in range(100):
            mid = (lo + hi) / 2.0
            if _log_binomial_tail(k, n, mid, lower=False) > log_alpha:
                lo = mid
            else:
                hi = mid
        upper = (lo + hi) / 2.0
    return float(lower), float(upper)


def summarise_test_sets(
    sets_by_true: Mapping[str, Any],
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Summarise class coverage and 12 directed retain/exclude rates.

    A directed event for ``true -> false`` retains the true restriction and
    excludes the specified false restriction.  Exact intervals are reported
    separately for each class and direction; ``stable`` only indicates that
    all requested summaries were computable and is not a scientific gate.
    """
    if not isinstance(sets_by_true, Mapping) or set(sets_by_true) != set(RESTRICTIONS):
        raise ValueError(f"sets_by_true must contain exactly {RESTRICTIONS}")
    alpha_value = _validate_alpha(alpha)
    arrays: dict[str, np.ndarray] = {}
    for label in RESTRICTIONS:
        raw = np.asarray(sets_by_true[label])
        if raw.ndim != 2 or raw.shape[1] != 4 or raw.dtype.kind != "b":
            raise ValueError(f"sets_by_true[{label!r}] must be boolean with shape (N, 4)")
        if raw.shape[0] < 1:
            raise ValueError("each true class must have at least one test set")
        arrays[label] = raw.astype(bool, copy=False)

    coverage: dict[str, dict[str, float | int]] = {}
    coverage_alpha = alpha_value / 4.0
    for index, label in enumerate(RESTRICTIONS):
        n = arrays[label].shape[0]
        k = int(np.count_nonzero(arrays[label][:, index]))
        lower, upper = exact_binomial_bounds(k, n, coverage_alpha)
        coverage[label] = {
            "n": n, "k": k, "rate": k / n, "lower": lower, "upper": upper,
        }

    directed: dict[str, dict[str, float | int]] = {}
    directed_alpha = alpha_value / 12.0
    for true_index, true_label in enumerate(RESTRICTIONS):
        for false_index, false_label in enumerate(RESTRICTIONS):
            if true_index == false_index:
                continue
            events = arrays[true_label][:, true_index] & ~arrays[true_label][:, false_index]
            n = events.size
            k = int(np.count_nonzero(events))
            lower, upper = exact_binomial_bounds(k, n, directed_alpha)
            directed[f"{true_label}->{false_label}"] = {
                "n": n, "k": k, "rate": k / n, "lower": lower, "upper": upper,
            }
    result = {
        "coverage": coverage,
        "coverage_per_true": coverage,
        "directed": directed,
        "directed_rates": directed,
        "stable": True,
    }
    return result


__all__ = [
    "RESTRICTIONS",
    "bank_log_support",
    "nonconformity",
    "conformal_pvalues",
    "restriction_sets",
    "exact_binomial_bounds",
    "summarise_test_sets",
]
