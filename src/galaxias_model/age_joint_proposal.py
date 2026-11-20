"""Joint defensive beta-kernel proposals on unit coordinates.

The proposal is fitted only from unit-coordinate rows and their caller-supplied
weights.  Each retained row is a joint kernel centre: its coordinates share a
single component weight, while the coordinates are conditionally independent
Beta variables.  A uniform whole-vector component keeps the proposal density
bounded away from zero everywhere on the unit cube.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
from typing import Any

import numpy as np


JOINT_UNIT_DIMENSION = 16
JOINT_KAPPA = 32.0
DEFAULT_JOINT_KAPPAS = (8.0, 32.0)
JOINT_MIXING_WEIGHT = 0.5


def _numeric_array(name: str, value: Any) -> np.ndarray:
    """Convert a numeric input without silently accepting object values."""
    raw = np.asarray(value)
    if raw.dtype.kind not in "biuf":
        raise ValueError(f"{name} must contain numeric values")
    result = raw.astype(float)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be finite")
    return result


def _unit_rows(value: Any) -> np.ndarray:
    rows = _numeric_array("unit_rows", value)
    if rows.ndim == 1:
        if rows.size == 0:
            raise ValueError("unit_rows must have a positive coordinate dimension")
        rows = rows[None, :]
    if rows.ndim != 2 or rows.shape[1] <= 0:
        raise ValueError("unit_rows must have shape (N, D) with D > 0")
    if np.any((rows < 0.0) | (rows > 1.0)):
        raise ValueError("unit_rows must be finite and lie in [0, 1]")
    return rows


def _weights(value: Any, n_rows: int) -> np.ndarray:
    weights = _numeric_array("weights", value)
    if weights.ndim != 1 or weights.shape[0] != n_rows:
        raise ValueError(f"weights must have shape ({n_rows},)")
    if np.any(weights < 0.0):
        raise ValueError("weights must be nonnegative")
    return weights


def _validate_kappas(kappas: Any) -> list[float]:
    values = _numeric_array("kappas", kappas)
    if values.ndim != 1 or values.size == 0 or np.any(values <= 0.0):
        raise ValueError("kappas must be a nonempty vector of positive values")
    return [float(value) for value in values]


def fit_joint_beta(
    unit_rows: Any,
    weights: Any,
    *,
    kappas: Any = DEFAULT_JOINT_KAPPAS,
    kappa: Any | None = None,
) -> dict[str, Any]:
    """Fit a weighted joint beta-kernel mixture on unit-coordinate rows.

    Positive-weighted rows are retained in their input order, including
    duplicate centres.  The returned mapping contains only plain Python
    scalars and lists so it can be serialized directly.  If all weights are
    zero (or there are no rows), the fitted proposal is the uniform fallback.
    """
    rows = _unit_rows(unit_rows)
    if kappa is not None:
        if kappas != DEFAULT_JOINT_KAPPAS:
            raise ValueError("supply either kappa or kappas, not both")
        bandwidths = _validate_kappas([kappa])
    else:
        bandwidths = _validate_kappas(kappas)
    raw_weights = _weights(weights, rows.shape[0])
    positive = raw_weights > 0.0
    if not np.any(positive):
        return {
            "dimension": int(rows.shape[1]),
            "kappas": bandwidths,
            "mixing_weight": float(JOINT_MIXING_WEIGHT),
            "centres": [],
            "weights": [],
            "fallback_uniform": True,
        }

    # Scaling before summing avoids overflow when callers provide very large
    # but finite source weights; only their relative values matter here.
    selected_weights = raw_weights[positive]
    scale = float(np.max(selected_weights))
    relative = selected_weights / scale
    normalizer = math.fsum(float(value) for value in relative)
    normalized = relative / normalizer
    # Keep every positive-weight centre represented even when a finite input
    # weight ratio is below the smallest positive float.
    normalized = np.maximum(normalized, np.nextafter(0.0, 1.0))
    normalized /= math.fsum(float(value) for value in normalized)
    return {
        "dimension": int(rows.shape[1]),
        "kappas": bandwidths,
        "mixing_weight": float(JOINT_MIXING_WEIGHT),
        "centres": [[float(value) for value in row] for row in rows[positive]],
        "weights": [float(value) for value in normalized],
        "fallback_uniform": False,
    }


def _logsumexp(values: list[float]) -> float:
    if not values:
        return -math.inf
    maximum = max(values)
    if math.isinf(maximum) and maximum < 0:
        return -math.inf
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in values))


def _logaddexp(left: float, right: float) -> float:
    if left == -math.inf:
        return right
    if right == -math.inf:
        return left
    maximum = max(left, right)
    return maximum + math.log1p(math.exp(min(left, right) - maximum))


def _log_beta_pdf(value: float, alpha: float, beta: float) -> float:
    """Evaluate a Beta density in log space, including both endpoints."""
    log_normalizer = math.lgamma(alpha) + math.lgamma(beta) - math.lgamma(alpha + beta)
    if value == 0.0:
        return -log_normalizer if alpha == 1.0 else -math.inf
    if value == 1.0:
        return -log_normalizer if beta == 1.0 else -math.inf
    return (
        (alpha - 1.0) * math.log(value)
        + (beta - 1.0) * math.log1p(-value)
        - log_normalizer
    )


def _validated_fit(fit: Mapping[str, Any]) -> tuple[int, list[float], float, list[list[float]], list[float]]:
    if not isinstance(fit, Mapping):
        raise TypeError("fit must be a mapping")
    required = {"dimension", "kappas", "mixing_weight", "centres", "weights"}
    missing = required - set(fit)
    if missing:
        raise ValueError(f"fit is missing fields: {sorted(missing)}")

    dimension_value = fit["dimension"]
    if isinstance(dimension_value, bool):
        raise ValueError("fit dimension must be a positive integer")
    try:
        dimension_float = float(dimension_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("fit dimension must be a positive integer") from exc
    if not math.isfinite(dimension_float) or dimension_float <= 0 or not dimension_float.is_integer():
        raise ValueError("fit dimension must be a positive integer")
    dimension = int(dimension_float)

    try:
        mixing_weight = float(fit["mixing_weight"])
    except (TypeError, ValueError) as exc:
        raise ValueError("fit mixing_weight must be numeric") from exc
    kappas = _validate_kappas(fit["kappas"])
    if not math.isfinite(mixing_weight) or mixing_weight != JOINT_MIXING_WEIGHT:
        raise ValueError(f"fit mixing_weight must be fixed at {JOINT_MIXING_WEIGHT:g}")

    centres_array = _numeric_array("fit centres", fit["centres"])
    if centres_array.size == 0:
        if centres_array.ndim not in (1, 2):
            raise ValueError("fit centres must have shape (K, D)")
        centres: list[list[float]] = []
    else:
        if centres_array.ndim == 1:
            if centres_array.shape[0] != dimension:
                raise ValueError("fit centres must have shape (K, D)")
            centres_array = centres_array[None, :]
        if centres_array.ndim != 2 or centres_array.shape[1] != dimension:
            raise ValueError("fit centres must have shape (K, D)")
        if np.any((centres_array < 0.0) | (centres_array > 1.0)):
            raise ValueError("fit centres must lie in [0, 1]")
        centres = [[float(value) for value in row] for row in centres_array]

    weights_array = _numeric_array("fit weights", fit["weights"])
    if weights_array.ndim != 1 or weights_array.shape[0] != len(centres):
        raise ValueError("fit weights must have one value per centre")
    if np.any(weights_array <= 0.0):
        raise ValueError("fit component weights must be positive")
    if centres and not math.isclose(float(np.sum(weights_array)), 1.0, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("fit component weights must sum to one")
    if not centres and weights_array.size:
        raise ValueError("fit weights cannot be supplied without centres")
    return dimension, kappas, mixing_weight, centres, [float(value) for value in weights_array]


def _coerce_unit(unit: Any, dimension: int) -> np.ndarray:
    result = _numeric_array("unit", unit)
    if result.shape != (dimension,) or np.any((result < 0.0) | (result > 1.0)):
        raise ValueError(f"unit must be a finite vector of {dimension} values in [0, 1]")
    return result


def joint_log_density_ratio(fit: Mapping[str, Any], unit: Any) -> float:
    """Return the exact log proposal-to-uniform density ratio at ``unit``."""
    dimension, kappas, mixing_weight, centres, weights = _validated_fit(fit)
    u = _coerce_unit(unit, dimension)
    if not centres:
        return 0.0

    component_logs: list[float] = []
    log_scale_weight = -math.log(len(kappas))
    for kappa in kappas:
        for centre, weight in zip(centres, weights):
            log_density = 0.0
            for value, coordinate in zip(u, centre):
                alpha = 1.0 + kappa * coordinate
                beta = 1.0 + kappa * (1.0 - coordinate)
                log_density += _log_beta_pdf(float(value), alpha, beta)
            component_logs.append(log_scale_weight + math.log(weight) + log_density)
    log_kernel_mixture = _logsumexp(component_logs)
    # q/g = mixing_weight + (1-mixing_weight) * kernel_mixture, with g=1.
    return float(_logaddexp(math.log(mixing_weight), math.log1p(-mixing_weight) + log_kernel_mixture))


def draw_joint_beta(
    fit: Mapping[str, Any], rng: np.random.Generator | None = None
) -> tuple[np.ndarray, float, str]:
    """Draw one defensive joint proposal and return its component label.

    The component label is ``"uniform"`` for the whole-vector uniform draw,
    or ``"beta_kappa_<scale>_centre_<index>"`` for a beta-kernel draw.
    """
    dimension, kappas, _, centres, weights = _validated_fit(fit)
    rng = np.random.default_rng() if rng is None else rng
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator")
    if not centres or float(rng.random()) < JOINT_MIXING_WEIGHT:
        unit = np.asarray(rng.random(dimension), dtype=float)
        component = "uniform"
    else:
        kappa_index = int(rng.integers(len(kappas)))
        kappa = kappas[kappa_index]
        index = int(rng.choice(len(centres), p=np.asarray(weights, dtype=float)))
        centre = centres[index]
        alpha = [1.0 + kappa * coordinate for coordinate in centre]
        beta = [1.0 + kappa * (1.0 - coordinate) for coordinate in centre]
        unit = np.asarray(rng.beta(alpha, beta), dtype=float)
        component = f"beta_kappa_{kappa:g}_centre_{index}"
    return unit, joint_log_density_ratio(fit, unit), component


__all__ = [
    "JOINT_KAPPA",
    "DEFAULT_JOINT_KAPPAS",
    "JOINT_MIXING_WEIGHT",
    "JOINT_UNIT_DIMENSION",
    "draw_joint_beta",
    "fit_joint_beta",
    "joint_log_density_ratio",
]
