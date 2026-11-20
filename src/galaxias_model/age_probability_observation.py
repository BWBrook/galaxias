"""Conditional probability bridge for the remaining age observations.

The early Creek allocation and Lake history are scored elsewhere.  This
module only generates and scores the observations that remain after that
conditioning: the late Creek count and the nine insurance binary records.
All inputs are explicit exposure arrays; terminal states, labels, and source
metadata never enter these functions.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from galaxias_model.age_recovery_observation import BINARY_VISIT_GROUPS
from galaxias_model.age_sources import keyed_seed


DEFAULT_NAMESPACE = "age-probability-observations-20261003"
_NB_SIZE = 69
_INSURANCE_START = 2
_INSURANCE_STOP = 11
_INSURANCE_GROUPS = tuple(int(x) for x in BINARY_VISIT_GROUPS[_INSURANCE_START:])


def _exposure_array(value: Any, name: str, columns: int) -> np.ndarray:
    """Validate and return a finite, nonnegative exposure matrix."""
    try:
        raw = np.asarray(value)
    except Exception as exc:  # pragma: no cover - NumPy exception varies
        raise ValueError(f"{name} must be an array-like numeric matrix") from exc
    if raw.ndim != 2 or raw.shape[1] != columns:
        raise ValueError(f"{name} must have shape (n, {columns})")
    if raw.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain real numeric values")
    result = raw.astype(float, copy=False)
    if not np.all(np.isfinite(result)) or np.any(result < 0):
        raise ValueError(f"{name} must be finite and nonnegative")
    return result


def _validate_creek_and_binary(
    creek_exposures: Any, binary_exposures: Any
) -> tuple[np.ndarray, np.ndarray]:
    creek = _exposure_array(creek_exposures, "creek_exposures", 3)
    binary = _exposure_array(binary_exposures, "binary_exposures", 11)
    if creek.shape[0] != binary.shape[0]:
        raise ValueError("creek and binary exposure banks must have the same size")
    early = creek[:, 0] + creek[:, 1]
    if not np.all(np.isfinite(early)) or np.any(early <= 0):
        raise ValueError("Xearly = X_E + X_F must be finite and positive")
    return creek, binary


def _rate_array(q: Any, exposure: np.ndarray) -> np.ndarray:
    if isinstance(q, (bool, np.bool_)) or not isinstance(q, (int, float, np.number)):
        raise ValueError("q must be a finite nonnegative number")
    rate = float(q)
    if not math.isfinite(rate) or rate < 0:
        raise ValueError("q must be a finite nonnegative number")
    # An overflowing q*X would otherwise silently become an infinite rate and
    # hide a malformed configuration behind a probability of exactly one.
    with np.errstate(over="ignore", invalid="ignore"):
        result = rate * exposure
    if not np.all(np.isfinite(result)) or np.any(result < 0):
        raise FloatingPointError("q times exposure overflows the finite rate range")
    return result


def _validate_late_counts(value: Any) -> np.ndarray:
    raw = np.asarray(value)
    if raw.ndim != 1 or raw.dtype.kind not in "iu":
        raise ValueError("late_counts must be a one-dimensional integer array")
    if np.any(raw < 0):
        raise ValueError("late_counts must be nonnegative")
    if np.any(raw > np.iinfo(np.int64).max):
        raise ValueError("late_counts exceed the supported integer range")
    return raw.astype(np.int64, copy=False)


def _validate_insurance(value: Any) -> np.ndarray:
    raw = np.asarray(value)
    if raw.ndim != 2 or raw.shape[1] != 9 or raw.dtype.kind != "b":
        raise ValueError("insurance_observed must have shape (n, 9) and boolean values")
    return raw.astype(bool, copy=False)


def _validate_generator(generator: Any) -> str:
    if generator not in ("poisson", "gamma_binary_quality"):
        raise ValueError("generator must be 'poisson' or 'gamma_binary_quality'")
    return str(generator)


def _gamma_pair_log_probabilities(
    a: np.ndarray, b: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return logs for (00, 10, 01, 11) under one shared Gamma quality."""
    # a and b are finite nonnegative rates.  Working in logs avoids both
    # cancellation in P10/P01 and overflow in 2+a+b or 1+a+b.
    log_a = np.full(a.shape, -math.inf, dtype=float)
    log_b = np.full(b.shape, -math.inf, dtype=float)
    positive_a = a > 0
    positive_b = b > 0
    log_a[positive_a] = np.log(a[positive_a])
    log_b[positive_b] = np.log(b[positive_b])
    log_1pa = np.log1p(a)
    log_1pb = np.log1p(b)
    log_1plus_sum = np.logaddexp(0.0, np.logaddexp(log_a, log_b))
    log_2plus_sum = np.logaddexp(math.log(2.0), np.logaddexp(log_a, log_b))
    p00 = -log_1plus_sum
    p10 = log_a - log_1pb - log_1plus_sum
    p01 = log_b - log_1pa - log_1plus_sum
    p11 = log_a + log_b + log_2plus_sum - log_1pa - log_1pb - log_1plus_sum
    return p00, p10, p01, p11


def _single_gamma_log_probabilities(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    log_a = np.full(a.shape, -math.inf, dtype=float)
    positive = a > 0
    log_a[positive] = np.log(a[positive])
    return -np.log1p(a), log_a - np.log1p(a)


def early_creek_log_score(creek_exposures: Any) -> np.ndarray:
    """Score the observed early Creek allocation ``(68, 1)``.

    This is the saturated-relative log allocation score, so its maximum is
    zero and the data-only multinomial coefficient is omitted.  Only the
    first two Creek exposures are used; the late exposure is intentionally
    excluded from this block.
    """
    creek = _exposure_array(creek_exposures, "creek_exposures", 3)
    positive_early = creek[:, 0] > 0
    positive_february = creek[:, 1] > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        log_early_exposure = np.where(positive_early, np.log(creek[:, 0]), -math.inf)
        log_february_exposure = np.where(positive_february, np.log(creek[:, 1]), -math.inf)
    log_denominator = np.logaddexp(log_early_exposure, log_february_exposure)
    result = np.full(creek.shape[0], -math.inf, dtype=float)
    valid = positive_early & positive_february
    if np.any(valid):
        log_p = log_early_exposure[valid] - log_denominator[valid]
        log_q = log_february_exposure[valid] - log_denominator[valid]
        saturated = 68.0 * math.log(68.0 / 69.0) + math.log(1.0 / 69.0)
        result[valid] = 68.0 * log_p + log_q - saturated
        if np.any(result[valid] > 1e-12):
            raise FloatingPointError("early Creek saturated-relative score exceeds zero")
        result[valid] = np.minimum(result[valid], 0.0)
    return result


def _late_log_likelihood(creek: np.ndarray, late_counts: np.ndarray) -> np.ndarray:
    """Exact NB(69, Xearly/(Xearly+Xlate)) log PMF."""
    x_early = creek[:, 0] + creek[:, 1]
    x_late = creek[:, 2]
    n_obs = late_counts.shape[0]
    n_bank = creek.shape[0]
    result = np.empty((n_obs, n_bank), dtype=float)
    positive_late = x_late > 0
    if np.any(positive_late):
        log_early = np.log(x_early[positive_late])
        log_late = np.log(x_late[positive_late])
        log_denominator = np.logaddexp(log_early, log_late)
        log_p = log_early - log_denominator
        log_one_minus_p = log_late - log_denominator
        k = late_counts.astype(float)[:, None]
        with np.errstate(invalid="ignore"):
            result[:, positive_late] = (
                np.vectorize(math.lgamma, otypes=[float])(_NB_SIZE + k)
                - math.lgamma(_NB_SIZE)
                - np.vectorize(math.lgamma, otypes=[float])(k + 1.0)
                + _NB_SIZE * log_p[None, :]
                + k * log_one_minus_p[None, :]
            )
    if np.any(~positive_late):
        result[:, ~positive_late] = np.where(
            late_counts[:, None] == 0, 0.0, -math.inf
        )
    return result


def _insurance_log_likelihood(
    binary: np.ndarray, insurance_observed: np.ndarray, q: float, generator: str
) -> np.ndarray:
    rates = _rate_array(q, binary[:, _INSURANCE_START:_INSURANCE_STOP])
    n_obs = insurance_observed.shape[0]
    n_bank = binary.shape[0]
    result = np.zeros((n_obs, n_bank), dtype=float)
    groups: dict[int, list[int]] = {}
    for column, group in enumerate(_INSURANCE_GROUPS):
        groups.setdefault(group, []).append(column)

    if generator == "poisson":
        log_zero = -rates
        with np.errstate(divide="ignore", invalid="ignore", under="ignore"):
            log_one = np.log(-np.expm1(-rates))
        for column in range(9):
            result += np.where(
                insurance_observed[:, column, None],
                log_one[None, :, column],
                log_zero[None, :, column],
            )
        return result

    for columns in groups.values():
        if len(columns) == 1:
            log_zero, log_one = _single_gamma_log_probabilities(rates[:, columns[0]])
            observed = insurance_observed[:, columns[0], None]
            result += np.where(observed, log_one[None, :], log_zero[None, :])
            continue
        if len(columns) != 2:  # pragma: no cover - frozen mapping has pairs only
            raise ValueError("each insurance visit group must contain one or two records")
        first, second = columns
        p00, p10, p01, p11 = _gamma_pair_log_probabilities(
            rates[:, first], rates[:, second]
        )
        first_observed = insurance_observed[:, first]
        second_observed = insurance_observed[:, second]
        result += np.where(
            (~first_observed & ~second_observed)[:, None], p00[None, :], 0.0
        )
        result += np.where(
            (first_observed & ~second_observed)[:, None], p10[None, :], 0.0
        )
        result += np.where(
            (~first_observed & second_observed)[:, None], p01[None, :], 0.0
        )
        result += np.where(
            (first_observed & second_observed)[:, None], p11[None, :], 0.0
        )
    return result


def remaining_log_likelihood(
    creek_exposures: Any,
    binary_exposures: Any,
    late_counts: Any,
    insurance_observed: Any,
    *,
    q: float,
    generator: str,
) -> dict[str, np.ndarray]:
    """Score remaining observations against every exposure-bank history.

    Returns independent ``late`` and ``insurance`` blocks plus their ``full``
    sum.  The returned ``full`` block excludes the separately scored early
    Creek allocation and Lake history.
    """
    creek, binary = _validate_creek_and_binary(creek_exposures, binary_exposures)
    late = _validate_late_counts(late_counts)
    insurance = _validate_insurance(insurance_observed)
    if late.shape[0] != insurance.shape[0]:
        raise ValueError("late_counts and insurance_observed must have the same size")
    selected_generator = _validate_generator(generator)
    late_score = _late_log_likelihood(creek, late)
    insurance_score = _insurance_log_likelihood(binary, insurance, q, selected_generator)
    full = late_score + insurance_score
    for name, values in (("late", late_score), ("insurance", insurance_score), ("full", full)):
        if np.isnan(values).any():
            raise FloatingPointError(f"{name} score contains NaN")
    return {"late": late_score, "insurance": insurance_score, "full": full}


def _draw_binary_poisson(rng: np.random.Generator, rates: np.ndarray) -> np.ndarray:
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        probabilities = -np.expm1(-rates)
    return rng.random(rates.shape) < probabilities


def _draw_binary_gamma_quality(
    rng: np.random.Generator, rates: np.ndarray
) -> np.ndarray:
    observed = np.zeros(rates.shape, dtype=bool)
    for group in sorted(set(_INSURANCE_GROUPS)):
        columns = [i for i, value in enumerate(_INSURANCE_GROUPS) if value == group]
        quality = float(rng.gamma(1.0, 1.0))
        with np.errstate(over="ignore", invalid="ignore"):
            scaled = quality * rates[columns]
        if not np.all(np.isfinite(scaled)):
            raise FloatingPointError("Gamma quality times exposure overflows the finite rate range")
        observed[columns] = _draw_binary_poisson(rng, scaled)
    return observed


def _negative_binomial_draw(
    rng: np.random.Generator, x_early: float, x_late: float
) -> int:
    if x_late == 0:
        return 0
    log_p = float(np.log(x_early) - np.logaddexp(np.log(x_early), np.log(x_late)))
    if not math.isfinite(log_p) or log_p >= 0:
        if log_p == 0:
            return 0
        raise FloatingPointError("late-count NB probability is outside the finite range")
    p = math.exp(log_p)
    if p <= 0 or not math.isfinite(p):
        raise FloatingPointError("late-count NB probability underflows the finite range")
    try:
        draw = rng.negative_binomial(_NB_SIZE, p)
    except (ValueError, OverflowError) as exc:
        raise FloatingPointError("late-count NB draw overflowed for the supplied exposures") from exc
    if isinstance(draw, np.ndarray):  # pragma: no cover - scalar call returns scalar
        draw = draw.item()
    if not np.issubdtype(type(draw), np.integer) or draw < 0:
        raise FloatingPointError("late-count NB draw was not a nonnegative integer")
    return int(draw)


def generate_remaining(
    creek_exposures: Any,
    binary_exposures: Any,
    identities: Sequence[Any],
    *,
    q: float,
    generator: str,
    namespace: str = DEFAULT_NAMESPACE,
) -> dict[str, np.ndarray]:
    """Generate late counts and insurance detections by stable source identity."""
    creek, binary = _validate_creek_and_binary(creek_exposures, binary_exposures)
    selected_generator = _validate_generator(generator)
    if not isinstance(namespace, str) or not namespace:
        raise ValueError("namespace must be a nonempty string")
    try:
        identity_values = list(identities)
    except TypeError as exc:
        raise ValueError("identities must be a finite sequence") from exc
    if len(identity_values) != creek.shape[0]:
        raise ValueError("one identity is required for each exposure row")

    rates = _rate_array(q, binary[:, _INSURANCE_START:_INSURANCE_STOP])
    late_counts = np.empty(creek.shape[0], dtype=np.int64)
    insurance_observed = np.empty((creek.shape[0], 9), dtype=bool)
    for index, identity in enumerate(identity_values):
        try:
            seed = keyed_seed(namespace, identity, selected_generator, float(q), bits=128)
        except (TypeError, ValueError) as exc:
            raise ValueError("each identity must be JSON serializable") from exc
        rng = np.random.default_rng(seed)
        x_early = float(creek[index, 0] + creek[index, 1])
        x_late = float(creek[index, 2])
        if not math.isfinite(x_early) or x_early <= 0:
            raise ValueError("Xearly = X_E + X_F must be finite and positive")
        late_counts[index] = _negative_binomial_draw(rng, x_early, x_late)
        if selected_generator == "poisson":
            insurance_observed[index] = _draw_binary_poisson(rng, rates[index])
        else:
            insurance_observed[index] = _draw_binary_gamma_quality(rng, rates[index])
    return {"late_counts": late_counts, "insurance_observed": insurance_observed}


__all__ = [
    "DEFAULT_NAMESPACE",
    "early_creek_log_score",
    "remaining_log_likelihood",
    "generate_remaining",
]
