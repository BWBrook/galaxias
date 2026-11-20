"""Small observation primitives for the proposed age-structured comparison.

No data are loaded or scored here. In particular, a conditional Poisson bridge
eliminates one common catchability parameter only under its stated assumptions.
"""
from __future__ import annotations

import math
import numpy as np


def conditional_capture_log_probability(counts, exposures) -> float:
    """Conditional multinomial from independent Poisson capture blocks.

    One shared multiplicative catchability cancels after conditioning on the
    total. Effort, accessibility and relative catchability must already be in
    exposures. Counts must be observed integers, not digitized figure means.
    """
    raw = np.asarray(counts)
    x = np.asarray(exposures, dtype=float)
    if (raw.ndim != 1 or x.shape != raw.shape or len(raw) < 2
            or raw.dtype.kind not in "iu" or np.any(raw < 0)):
        raise ValueError("counts must be a nonnegative integer vector matching exposures")
    if not np.all(np.isfinite(x)) or np.any(x < 0):
        raise ValueError("exposures must be finite and nonnegative")
    total = sum(int(n) for n in raw)
    if total == 0:
        return 0.0
    if np.any((raw > 0) & (x == 0)):
        return -math.inf
    # Scale first so both huge and very small exposure units are safe.
    scaled = x / x.max()
    normalizer = math.log(math.fsum(scaled))
    result = math.lgamma(total + 1) - math.fsum(math.lgamma(int(n) + 1) for n in raw)
    return result + math.fsum(int(n) * (math.log(v) - normalizer)
                             for n, v in zip(raw, scaled) if n)


def lake_capture_log_score(early_exposure: float, late_exposure: float, *,
                           early_catch_equivalent: float, power: float,
                           late_catch_equivalent: float = 0.0) -> float:
    """Tempered allocation score for digitized early and late catch equivalents.

    This deliberately accepts a noninteger derived catch equivalent. It is not
    an exact raw-count likelihood, and power is not an estimated dispersion.
    An outcome-only multinomial coefficient is omitted. The historical late
    count is zero; synthetic recovery must allow positive simulated late counts.
    """
    if not all(math.isfinite(v) and v >= 0 for v in
               (early_exposure, late_exposure, early_catch_equivalent, late_catch_equivalent)):
        raise ValueError("exposures and catch equivalent must be finite and nonnegative")
    if not math.isfinite(power) or not 0 < power <= 1:
        raise ValueError("power must be in (0, 1]")
    if early_catch_equivalent == 0 and late_catch_equivalent == 0:
        return 0.0
    if ((early_exposure == 0 and early_catch_equivalent > 0)
            or (late_exposure == 0 and late_catch_equivalent > 0)):
        return -math.inf
    logs = [math.log(v) if v else -math.inf for v in (early_exposure, late_exposure)]
    denominator = float(np.logaddexp(*logs))
    return power * math.fsum(c * (log_x-denominator) for c, log_x in
                             zip((early_catch_equivalent, late_catch_equivalent), logs) if c)


def accessible_abundance(state: np.ndarray, compartment: int, age_weights: np.ndarray) -> float:
    array = np.asarray(state, dtype=float)
    weights = np.asarray(age_weights, dtype=float)
    if array.ndim != 3 or array.shape[:2] != (2, 2) or compartment not in (0, 1):
        raise ValueError("expected lake/refuge by female/male by age state")
    if weights.shape != (array.shape[2],) or not np.isfinite(weights).all() or np.any(weights < 0) or np.any(weights > 1):
        raise ValueError("one accessibility weight in [0, 1] is required per age")
    if not np.isfinite(array).all() or np.any(array < 0):
        raise ValueError("state must be finite and nonnegative")
    return float(np.sum(array[compartment] * weights))


def conditional_late_zero_log_probability(
    early_exposure: float, late_exposure: float, *, total_captures: int = 68,
) -> float:
    """P(all captures early | total), for two independent Poisson counts.

    Exposure is the sum of visit effort times accessible abundance. Unknown
    common catchability cancels. This is conditional evidence for the change,
    not a likelihood for absolute abundance or 68 unique fish. A declared late
    catchability ratio must multiply late_exposure before calling this function.
    """
    if isinstance(total_captures, bool) or not isinstance(total_captures, (int, np.integer)) or total_captures < 0:
        raise ValueError("total_captures must be a nonnegative integer")
    if not all(math.isfinite(x) and x >= 0 for x in (early_exposure, late_exposure)):
        raise ValueError("exposures must be finite and nonnegative")
    if total_captures == 0:
        return 0.0
    if early_exposure == 0:
        return -math.inf
    return -total_captures * math.log1p(late_exposure / early_exposure)


def at_least_one_log_probability(exposure: float, capture_rate: float) -> float:
    """Poisson positive-record contribution with explicit effort/catchability."""
    if not all(math.isfinite(x) and x >= 0 for x in (exposure, capture_rate)):
        raise ValueError("exposure and capture_rate must be finite and nonnegative")
    mean = exposure * capture_rate
    return -math.inf if mean == 0 else math.log(-math.expm1(-mean))
