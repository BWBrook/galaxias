"""Prospective abundance-dependent observation scenarios, not fitted catchability.

The shared-quality scenario integrates one two-point quality multiplier per
declared block. Positive and negative records use the same observation law.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

Q_SCENARIOS = (0.005, 0.02, 0.05, 0.2)
POSITIVE_FIELDS = tuple(f"pos_N_R_{year}" for year in (1988, 1989, 1990, 1991, 1992, 1996))
NEGATIVE_FIELDS = ("neg_N_L_1988", "neg_N_L_1989") + tuple(
    f"neg_N_total_{year}" for year in range(1998, 2003)
)
EPISODE_FIELDS = POSITIVE_FIELDS + NEGATIVE_FIELDS
COMMON_POSITIVE_FIELDS = POSITIVE_FIELDS[:5] + ("pos_N_R_1996_january", "pos_N_R_1996_march")
COMMON_EPISODE_FIELDS = COMMON_POSITIVE_FIELDS + NEGATIVE_FIELDS
OBSERVATION_MODELS = ("homogeneous", "shared_quality", "independent_quality")
# Mixed signs stay together: refuge detections and lake misses cannot choose
# separate observation quality in the early programme.
BLOCKS = ((0, 1, 2, 3, 4, 6, 7), (5,), (8, 9, 10, 11, 12))
COMMON_BLOCKS = ((0, 1, 2, 3, 4, 7, 8), (5, 6), (9, 10, 11, 12, 13))


def _episode_log_probabilities(abundances: np.ndarray, q: float, positive_count: int) -> np.ndarray:
    logs = abundances * math.log1p(-q)
    result = logs.copy()
    with np.errstate(divide="ignore"):
        result[:, :positive_count] = np.log(-np.expm1(logs[:, :positive_count]))
    return result


def history_log_likelihood(features: pd.DataFrame, q: float, model: str = "homogeneous") -> np.ndarray:
    """One integrated log probability per history for the 13 binary records.

q is per model-count unit per annual domain programme. These scenarios do not
establish the mapping of model counts to the number of surveyed wild fish.
"""
    return _history_log_likelihood(features, q, model, EPISODE_FIELDS, len(POSITIVE_FIELDS), BLOCKS)


def common_history_log_likelihood(features: pd.DataFrame, q: float, model: str = "homogeneous") -> np.ndarray:
    """Fourteen common-model records, including both 1996 detections in all arms.

January and March share one quality block; their states differ after extraction.
Equal q per specified record is a scenario assumption, not measured effort.
"""
    return _history_log_likelihood(features, q, model, COMMON_EPISODE_FIELDS, len(COMMON_POSITIVE_FIELDS), COMMON_BLOCKS)


def _history_log_likelihood(features, q, model, fields, positive_count, blocks):
    if not math.isfinite(q) or not 0 < q < 2 / 3:
        raise ValueError("q must be finite in (0, 2/3) for the quality scenarios")
    if model not in OBSERVATION_MODELS:
        raise ValueError(f"Unknown observation model: {model}")
    values = features.loc[:, fields].to_numpy(dtype=float)
    if values.ndim != 2 or not len(values) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Episode abundances must be nonempty, finite and nonnegative")
    if model == "homogeneous":
        return _episode_log_probabilities(values, q, positive_count).sum(axis=1)
    low = _episode_log_probabilities(values, .5 * q, positive_count)
    high = _episode_log_probabilities(values, 1.5 * q, positive_count)
    if model == "independent_quality":
        return (np.logaddexp(low, high) - math.log(2)).sum(axis=1)
    return sum(np.logaddexp(low[:, block].sum(axis=1), high[:, block].sum(axis=1)) - math.log(2)
               for block in blocks)


def summarize_log_likelihood(log_likelihood: np.ndarray, endpoints: dict[str, np.ndarray]) -> dict[str, float | int | bool]:
    """All-history compatibility and ratio Monte Carlo diagnostics, without floors."""
    logs = np.asarray(log_likelihood, dtype=float)
    if logs.ndim != 1 or not len(logs) or np.isnan(logs).any() or np.isposinf(logs).any() or (logs > 1e-12).any():
        raise ValueError("Expected nonempty log probabilities in [-inf, 0]")
    n = len(logs)
    values = {name: np.asarray(value, dtype=float) for name, value in endpoints.items()}
    if any(value.shape != logs.shape or not np.isfinite(value).all() for value in values.values()):
        raise ValueError("Endpoints must be finite and aligned with histories")
    count = int(np.isfinite(logs).sum())
    result = {"replicate_count": n, "positive_supported_count": count,
              "log_mean_compatibility": -math.inf, "mean_compatibility": 0.,
              "weight_ess": 0., "mc_relative_se": math.nan,
              "largest_weight_share": math.nan, "mc_qualified": False}
    for name, value in values.items():
        result[f"unconditional_{name}"] = float(value.mean())
        result[f"weighted_{name}"] = math.nan
        result[f"weighted_{name}_mc_se"] = math.nan
    if count == 0:
        return result
    maximum = float(logs.max())
    scaled = np.exp(logs - maximum)
    weights = scaled / scaled.sum()
    ess = float(1 / np.square(weights).sum())
    relative_se = math.sqrt(max(0., (n / ess - 1) / (n - 1))) if n > 1 else math.nan
    log_mean = maximum + math.log(float(scaled.sum())) - math.log(n)
    largest = float(weights.max())
    result.update(log_mean_compatibility=log_mean, mean_compatibility=math.exp(log_mean),
                  weight_ess=ess, mc_relative_se=relative_se, largest_weight_share=largest,
                  mc_qualified=ess >= 100 and relative_se <= .1 and largest <= .05)
    for name, value in values.items():
        estimate = float(np.dot(weights, value))
        error = math.sqrt(n / (n - 1) * float(np.square(weights * (value - estimate)).sum())) if n > 1 else math.nan
        result[f"weighted_{name}"] = estimate
        result[f"weighted_{name}_mc_se"] = error
    return result
