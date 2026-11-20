"""Source-balanced natural-prevalence forecasts and uncertainty bounds.

This module consumes a completed inference bank.  It does not inspect or
choose biological outcomes while constructing source weights: terminal
outcomes enter only the requested numerator after the history contributions
have been calculated.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import math
from typing import Any

import numpy as np


__all__ = [
    "bounded_ratio_interval",
    "probability_forecasts",
    "source_bootstrap_counts",
    "source_halves",
]


def _array(value: Any, name: str, ndim: int) -> np.ndarray:
    try:
        result = np.asarray(value)
    except Exception as exc:  # pragma: no cover - NumPy version dependent
        raise ValueError(f"{name} must be array-like") from exc
    if result.ndim != ndim:
        raise ValueError(f"{name} must have {ndim} dimensions")
    return result


def _integer(value: Any, name: str, *, positive: bool = False) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    result = int(value)
    if (positive and result < 1) or (not positive and result < 0):
        qualifier = "positive " if positive else "nonnegative "
        raise ValueError(f"{name} must be a {qualifier}integer")
    return result


def _seed(value: Any) -> int:
    return _integer(value, "seed")


def _blocks(value: Any, name: str, expected: int | None = None) -> np.ndarray:
    result = _array(value, name, 1)
    if expected is not None and result.size != expected:
        raise ValueError(f"{name} must have length {expected}")
    if result.size == 0:
        raise ValueError(f"{name} must not be empty")
    for item in result.tolist():
        try:
            hash(item)
        except TypeError as exc:
            raise ValueError(f"{name} must contain hashable block labels") from exc
    return result


def _block_groups(blocks: np.ndarray) -> list[np.ndarray]:
    groups: dict[Any, list[int]] = {}
    for index, block in enumerate(blocks.tolist()):
        try:
            groups.setdefault(block, []).append(index)
        except TypeError as exc:  # defensive for object arrays
            raise ValueError("block labels must be hashable") from exc
    return [np.asarray(indices, dtype=int) for indices in groups.values()]


def source_bootstrap_counts(
    blocks: Sequence[str], n_bootstrap: int, seed: int
) -> np.ndarray:
    """Draw stratified source bootstrap multiplicities.

    Each declared block is resampled independently with replacement.  The
    output retains every source-universe position, including positions whose
    count is zero in a particular bootstrap replicate.
    """
    block_array = _blocks(blocks, "blocks")
    n_draws = _integer(n_bootstrap, "n_bootstrap", positive=True)
    rng = np.random.default_rng(_seed(seed))
    output = np.zeros((n_draws, block_array.size), dtype=np.int64)
    for indices in _block_groups(block_array):
        size = int(indices.size)
        probabilities = np.full(size, 1.0 / size, dtype=float)
        output[:, indices] = rng.multinomial(size, probabilities, size=n_draws)
    return output


def _source_key(value: Any) -> str:
    if isinstance(value, np.generic):
        value = value.item()
    if value is None:
        raise ValueError("source_ids cannot contain missing identifiers")
    if isinstance(value, float) and math.isnan(value):
        raise ValueError("source_ids cannot contain missing identifiers")
    return str(value)


def source_halves(source_ids: Any, blocks: Sequence[str], seed: int) -> np.ndarray:
    """Assign source IDs to deterministic alternating within-block halves."""
    ids = _array(source_ids, "source_ids", 1)
    block_array = _blocks(blocks, "blocks", expected=ids.size)
    keys = [_source_key(value) for value in ids.tolist()]
    if len(set(keys)) != len(keys):
        raise ValueError("source_ids must be unique")
    seed_value = _seed(seed)
    result = np.empty(ids.size, dtype=np.int8)
    for indices in _block_groups(block_array):
        ordered = sorted(
            indices.tolist(),
            key=lambda index: hashlib.sha256(
                f"{seed_value}|{keys[index]}".encode("utf-8")
            ).digest(),
        )
        for rank, index in enumerate(ordered):
            result[index] = rank % 2
    return result


def _log_inputs(
    log_weights: Any, log_likelihood: Any, outcomes: Any
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    weights = _array(log_weights, "log_weights", 1)
    likelihood = _array(log_likelihood, "log_likelihood", 2)
    if weights.dtype.kind not in "iuf" or likelihood.dtype.kind not in "iuf":
        raise ValueError("log weights and likelihoods must contain real numeric values")
    weights = weights.astype(float, copy=False)
    likelihood = likelihood.astype(float, copy=False)
    if np.isnan(weights).any() or np.isposinf(weights).any():
        raise ValueError("log_weights may contain finite values or -inf, but no NaN/+inf")
    if np.isnan(likelihood).any() or np.isposinf(likelihood).any():
        raise ValueError("log_likelihood may contain finite values or -inf, but no NaN/+inf")
    if np.any(weights > math.log(2.0)):
        raise ValueError("log_weights must be at most log(2)")
    if np.any(likelihood > 0.0):
        raise ValueError("log_likelihood must be nonpositive")
    if likelihood.shape[1] != weights.size:
        raise ValueError("log_likelihood columns must match log_weights")
    labels = _array(outcomes, "outcomes", 1)
    if labels.dtype.kind != "b" or labels.size != weights.size:
        raise ValueError("outcomes must be boolean with one value per history")
    return weights, likelihood, labels.astype(bool, copy=False)


def _validate_counts(counts: Any, n_sources: int) -> np.ndarray:
    result = _array(counts, "bootstrap_counts", 2)
    if result.dtype.kind not in "iu":
        raise ValueError("bootstrap_counts must contain integers")
    result = result.astype(np.int64, copy=False)
    if result.shape[1] != n_sources or np.any(result < 0):
        raise ValueError("bootstrap_counts must be nonnegative with one column per source")
    return result


def _validate_halves(halves: Any, n_sources: int) -> np.ndarray:
    result = _array(halves, "halves", 1)
    if result.dtype.kind not in "iu" or result.size != n_sources:
        raise ValueError("halves must be an integer vector matching source_blocks")
    result = result.astype(np.int8, copy=False)
    if np.any((result != 0) & (result != 1)):
        raise ValueError("halves must contain only 0 and 1")
    return result


def _source_contributions(
    weights: np.ndarray,
    likelihood: np.ndarray,
    labels: np.ndarray,
    source_indices: np.ndarray,
    n_sources: int,
    replicates: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n_data = likelihood.shape[0]

    logs = weights[None, :] + likelihood
    scaled = np.zeros_like(logs, dtype=float)
    log_scale = np.full(n_data, -math.inf, dtype=float)
    for data_index in range(n_data):
        finite = np.isfinite(logs[data_index])
        if np.any(finite):
            scale = float(np.max(logs[data_index, finite]))
            log_scale[data_index] = scale
            scaled[data_index, finite] = np.exp(logs[data_index, finite] - scale)

    source_denominator = np.zeros((n_data, n_sources), dtype=float)
    source_numerator = np.zeros((n_data, n_sources), dtype=float)
    source_denominator_absolute = np.zeros((n_data, n_sources), dtype=float)
    source_numerator_absolute = np.zeros((n_data, n_sources), dtype=float)
    for history_index, source_index in enumerate(source_indices):
        source_denominator[:, source_index] += scaled[:, history_index] / replicates
        source_numerator[:, source_index] += scaled[:, history_index] * labels[history_index] / replicates
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            absolute = np.exp(logs[:, history_index]) / replicates
        absolute[~np.isfinite(absolute)] = 0.0
        source_denominator_absolute[:, source_index] += absolute
        source_numerator_absolute[:, source_index] += absolute * labels[history_index]
    return (
        source_denominator,
        source_numerator,
        source_denominator_absolute,
        source_numerator_absolute,
        log_scale,
    )


def _ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    result = np.full(numerator.shape, np.nan, dtype=float)
    valid = denominator > 0.0
    result[valid] = numerator[valid] / denominator[valid]
    return result


def _quantile_interval(values: np.ndarray, alpha: float) -> np.ndarray:
    result = np.full((values.shape[1], 2), np.nan, dtype=float)
    for data_index in range(values.shape[1]):
        finite = values[:, data_index][np.isfinite(values[:, data_index])]
        if finite.size:
            result[data_index] = np.quantile(finite, [alpha / 2.0, 1.0 - alpha / 2.0])
    return result


def _validate_probability_options(replicates: Any, alpha: Any) -> tuple[int, float]:
    reps = _integer(replicates, "replicates", positive=True)
    if isinstance(alpha, (bool, np.bool_)) or not isinstance(alpha, (int, float, np.number)):
        raise ValueError("alpha must be a finite number in (0, 1)")
    alpha_float = float(alpha)
    if not math.isfinite(alpha_float) or not 0.0 < alpha_float < 1.0:
        raise ValueError("alpha must be a finite number in (0, 1)")
    return reps, alpha_float


def bounded_ratio_interval(
    numerator: Any,
    denominator: Any,
    blocks: Sequence[str],
    *,
    upper_bound: float = 2.0,
    alpha: float = 0.05,
) -> np.ndarray:
    """Return a conservative empirical-Bernstein interval for a bounded ratio.

    The numerator and denominator entries are independent source-cluster
    means.  They need not be identically distributed, and are pooled across
    the supplied blocks.  The radius is Theorem 11 of Maurer and Pontil
    (2009), https://www.cs.mcgill.ca/~colt2009/papers/012.pdf, with four
    one-sided events (numerator/denominator lower and upper tails).
    """
    num = _array(numerator, "numerator", 1)
    den = _array(denominator, "denominator", 1)
    if num.size != den.size:
        raise ValueError("numerator and denominator must have equal length")
    if num.dtype.kind not in "iuf" or den.dtype.kind not in "iuf":
        raise ValueError("numerator and denominator must be numeric")
    num = num.astype(float, copy=False)
    den = den.astype(float, copy=False)
    if isinstance(upper_bound, (bool, np.bool_)) or not isinstance(upper_bound, (int, float, np.number)):
        raise ValueError("upper_bound must be finite and positive")
    bound = float(upper_bound)
    if not math.isfinite(bound) or bound <= 0.0:
        raise ValueError("upper_bound must be finite and positive")
    if not np.isfinite(num).all() or not np.isfinite(den).all() or np.any(num < 0) or np.any(den < 0):
        raise ValueError("numerator and denominator must be finite and nonnegative")
    if np.any(num > den + 1e-12) or np.any(num > bound + 1e-12) or np.any(den > bound + 1e-12):
        raise ValueError("numerator and denominator must lie in [0, upper_bound] with numerator <= denominator")
    if isinstance(alpha, (bool, np.bool_)) or not isinstance(alpha, (int, float, np.number)):
        raise ValueError("alpha must be a finite number in (0, 1)")
    alpha_float = float(alpha)
    if not math.isfinite(alpha_float) or not 0.0 < alpha_float < 1.0:
        raise ValueError("alpha must be a finite number in (0, 1)")

    block_array = _blocks(blocks, "blocks", expected=num.size)
    n = int(num.size)
    if n < 2:
        return np.array([0.0, 1.0], dtype=float)
    # Four one-sided events share the confidence budget, while Theorem 11
    # itself uses log(2 / delta) in the radius.
    delta = alpha_float / 4.0
    log_term = math.log(2.0 / delta)
    radius_num = math.sqrt(2.0 * float(np.var(num, ddof=1)) * log_term / n)
    radius_num += 7.0 * bound * log_term / (3.0 * (n - 1))
    radius_den = math.sqrt(2.0 * float(np.var(den, ddof=1)) * log_term / n)
    radius_den += 7.0 * bound * log_term / (3.0 * (n - 1))
    mean_num = float(np.mean(num))
    mean_den = float(np.mean(den))
    numerator_low = max(0.0, mean_num - radius_num)
    numerator_high = min(bound, mean_num + radius_num)
    denominator_low = max(0.0, mean_den - radius_den)
    denominator_high = min(bound, mean_den + radius_den)
    if denominator_high <= 0.0:
        return np.array([0.0, 1.0], dtype=float)
    lower = 0.0 if denominator_high <= 0.0 else numerator_low / denominator_high
    upper = 1.0 if denominator_low <= 0.0 else numerator_high / denominator_low
    return np.array([max(0.0, min(1.0, lower)), max(0.0, min(1.0, upper))], dtype=float)


def probability_forecasts(
    log_weights: Any,
    log_likelihood: Any,
    outcomes: Any,
    source_indices: Any,
    source_blocks: Sequence[str],
    bootstrap_counts: Any,
    halves: Any,
    *,
    replicates: int = 6,
    alpha: float = 0.05,
) -> dict[str, np.ndarray]:
    """Compute source-balanced natural-prevalence forecasts and diagnostics.

    ``source_denominator`` and ``source_numerator`` are per-dataset source
    contributions after an optional common exponential rescaling.  Their
    absolute scale is recorded in ``log_scale``; ratios and bootstrap
    resampling are invariant to that per-dataset scale.  The bounded interval
    uses separately retained absolute contributions internally.
    """
    weights, likelihood, labels = _log_inputs(log_weights, log_likelihood, outcomes)
    reps, alpha_float = _validate_probability_options(replicates, alpha)
    n_data, n_histories = likelihood.shape
    block_array = _blocks(source_blocks, "source_blocks")
    n_sources = int(block_array.size)
    counts = _validate_counts(bootstrap_counts, n_sources)
    half_array = _validate_halves(halves, n_sources)
    indices = _array(source_indices, "source_indices", 1)
    if indices.dtype.kind not in "iu" or indices.size != n_histories:
        raise ValueError("source_indices must be integer with one value per history")
    indices = indices.astype(np.int64, copy=False)
    if np.any(indices < 0) or np.any(indices >= n_sources):
        raise ValueError("source_indices must index source_blocks")
    for block_indices in _block_groups(block_array):
        if not np.all(np.sum(counts[:, block_indices], axis=1) == block_indices.size):
            raise ValueError("bootstrap_counts must preserve each source block size")

    source_denominator, source_numerator, absolute_denominator, absolute_numerator, log_scale = _source_contributions(
        weights, likelihood, labels, indices, n_sources, reps
    )
    point_denominator = np.sum(source_denominator, axis=1)
    point_numerator = np.sum(source_numerator, axis=1)
    point_probability = _ratio(point_numerator, point_denominator)

    bootstrap_denominator = counts @ source_denominator.T
    bootstrap_numerator = counts @ source_numerator.T
    bootstrap_probability = _ratio(bootstrap_numerator, bootstrap_denominator)
    interval = _quantile_interval(bootstrap_probability, alpha_float)

    half_probability = np.full((n_data, 2), np.nan, dtype=float)
    for half in (0, 1):
        selected = half_array == half
        half_probability[:, half] = _ratio(
            np.sum(source_numerator[:, selected], axis=1),
            np.sum(source_denominator[:, selected], axis=1),
        )
    half_gap = np.abs(half_probability[:, 0] - half_probability[:, 1])

    bounded_interval = np.empty((n_data, 2), dtype=float)
    boundary_bound_used = np.zeros(n_data, dtype=bool)
    for data_index in range(n_data):
        bounded_interval[data_index] = bounded_ratio_interval(
            absolute_numerator[data_index],
            absolute_denominator[data_index],
            block_array,
            upper_bound=2.0,
            alpha=alpha_float,
        )
        finite_bootstrap = bootstrap_probability[:, data_index][np.isfinite(bootstrap_probability[:, data_index])]
        ordinary_hits_boundary = (
            not np.all(np.isfinite(interval[data_index]))
            or point_probability[data_index] <= 0.0
            or point_probability[data_index] >= 1.0
            or (finite_bootstrap.size > 0 and (interval[data_index, 0] <= 0.0 or interval[data_index, 1] >= 1.0))
            or finite_bootstrap.size == 0
        )
        boundary_bound_used[data_index] = bool(ordinary_hits_boundary)
        if ordinary_hits_boundary:
            if np.all(np.isfinite(interval[data_index])):
                interval[data_index, 0] = min(interval[data_index, 0], bounded_interval[data_index, 0])
                interval[data_index, 1] = max(interval[data_index, 1], bounded_interval[data_index, 1])
            else:
                interval[data_index] = bounded_interval[data_index]

    finite_fraction = np.mean(np.isfinite(bootstrap_probability), axis=0)
    source_ess = np.zeros(n_data, dtype=float)
    largest_source_share = np.full(n_data, np.nan, dtype=float)
    n_source_positive_count = np.zeros(n_data, dtype=int)
    for data_index in range(n_data):
        source_values = source_denominator[data_index]
        total = float(np.sum(source_values))
        positive = source_values > 0.0
        n_source_positive_count[data_index] = int(np.count_nonzero(positive))
        if total > 0.0:
            source_ess[data_index] = total * total / float(np.sum(source_values * source_values))
            largest_source_share[data_index] = float(np.max(source_values) / total)

    supported = np.isfinite(point_probability) & (point_denominator > 0.0)
    return {
        "p": point_probability,
        "probability": point_probability,
        "interval": interval,
        "bootstrap_probabilities": bootstrap_probability,
        "finite_fraction": finite_fraction,
        "half_gap": half_gap,
        "source_ess": source_ess,
        "largest_source_share": largest_source_share,
        "n_source_positive_count": n_source_positive_count,
        "boundary_bound_used": boundary_bound_used,
        "supported": supported,
        "source_denominator": source_denominator,
        "source_numerator": source_numerator,
        "log_scale": log_scale,
        "bounded_interval": bounded_interval,
    }
