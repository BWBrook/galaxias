"""Experimental late-observation bridge; the production bridge is unchanged.

Detection probabilities are fixed sensitivity assumptions conditional on an
occupied survey domain. They are not estimates of field catchability. The
positive-record indicator uses early-year states (the previous recorded year).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from galaxias_model.types import SimulationResult


REPAIR_PROFILES = {
    "repair_presence_only": 0.0,
    "repair_detection_060": 0.60,
    "repair_detection_098": 0.98,
}
LATE_BLOCK_WEIGHT = 5.0
POSITIVE_REFUGE_YEARS = (1988, 1989, 1990, 1991, 1992, 1996)
LAKE_NONDETECTION_YEARS = (1988, 1989)
NATURAL_NONDETECTION_YEARS = (1998, 1999, 2000, 2001, 2002)


def project_repaired_history(result: SimulationResult) -> dict[str, float | int | bool]:
    """Extract sufficient event summaries and independent physical diagnostics.

Each year is an early-year proxy, not a reconstruction of within-year surveys.
The 1996 refuge record also covers the necessary presence condition for the last
March record. Annual records in the same domain are not counted twice.
"""
    t = result.trajectory_table.set_index("year")
    required = set(range(1987, 2003))
    if not t.index.is_unique or not required.issubset(t.index):
        raise ValueError("Repair projection requires unique annual states for 1987–2002")
    values = t.loc[sorted(required), ["N_L", "N_R", "N_total"]].to_numpy()
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Repair projection requires finite nonnegative abundances")
    if not np.allclose(values[:, 0] + values[:, 1], values[:, 2]):
        raise ValueError("Lake and refuge abundances must sum to total abundance")
    positives = t.loc[[y - 1 for y in POSITIVE_REFUGE_YEARS], "N_R"].gt(0)
    lake = t.loc[[y - 1 for y in LAKE_NONDETECTION_YEARS], "N_L"]
    natural = t.loc[[y - 1 for y in NATURAL_NONDETECTION_YEARS], "N_total"]
    return {
        "positive_records_compatible": bool(positives.all()),
        "missing_positive_record_episodes": int((~positives).sum()),
        "present_at_1996_proxy": bool(t.loc[1995, "N_total"] > 0),
        "refuge_present_at_1996_proxy": bool(t.loc[1995, "N_R"] > 0),
        "lake_nondetection_occupied_episodes": int(lake.gt(0).sum()),
        "natural_nondetection_occupied_episodes": int(natural.gt(0).sum()),
        "nondetection_occupied_episodes": int(lake.gt(0).sum() + natural.gt(0).sum()),
        "lake_observation_proxy_mean_abundance": float(lake.mean()),
        "natural_observation_proxy_mean_abundance": float(natural.mean()),
        "n_total_1995": float(t.loc[1995, "N_total"]),
        "n_total_1996": float(t.loc[1996, "N_total"]),
        "n_refuge_1995": float(t.loc[1995, "N_R"]),
        "n_total_1992_1996_mean": float(t.loc[1992:1996, "N_total"].mean()),
        "n_total_2002": float(t.loc[2002, "N_total"]),
        "surviving_2002": bool(t.loc[2002, "N_total"] > 0),
    }


def aggregate_repaired_late_evidence(features: pd.DataFrame, detection_probability: float) -> dict[str, float | int | bool]:
    """-log(mean joint compatibility), without a floor for zero sampled support.

All stochastic histories enter the mean. Zero positive-compatible histories
means ineligible at this Monte Carlo budget, not proof of zero population-model
probability. ESS and largest contribution diagnose rare-history domination.
"""
    p = float(detection_probability)
    if not math.isfinite(p) or not 0 <= p < 1:
        raise ValueError("Fixed detection probability must be in [0, 1)")
    if features.empty:
        raise ValueError("At least one historical replicate is required")
    positive = features["positive_records_compatible"]
    k = features["nondetection_occupied_episodes"].to_numpy(dtype=float)
    if not positive.isin([True, False]).all():
        raise ValueError("Positive compatibility must contain Boolean indicators")
    if not np.isfinite(k).all() or not ((k >= 0) & (k <= 7) & (k == np.floor(k))).all():
        raise ValueError("Nondetection episode counts must be integers from 0 to 7")
    n, supported = len(features), positive.to_numpy(dtype=bool)
    count = int(supported.sum())
    common = {
        "replicate_count": n,
        "positive_compatible_count": count,
        "positive_compatible_fraction": count / n,
        "sample_supported": count > 0,
    }
    if count == 0:
        return {
            **common, "late_discrepancy": math.inf,
            "positive_discrepancy": math.inf,
            "conditional_nondetection_discrepancy": math.nan,
            "mean_joint_compatibility": 0.0,
            "conditional_nondetection_compatibility": math.nan,
            "weight_ess": 0.0, "largest_weight_share": math.nan,
            "mc_relative_se": math.nan,
        }
    log_weights = k[supported] * math.log1p(-p)
    maximum = float(log_weights.max())
    scaled = np.exp(log_weights - maximum)
    total = float(scaled.sum())
    log_mean = maximum + math.log(total) - math.log(n)
    log_positive = math.log(count / n)
    ess = total**2 / float(np.square(scaled).sum())
    # Zeros for incompatible histories remain in both the mean and MC variance.
    relative_se = math.sqrt(max(0.0, (n / ess - 1) / (n - 1))) if n > 1 else math.nan
    return {
        **common,
        "late_discrepancy": -log_mean,
        "positive_discrepancy": -log_positive,
        "conditional_nondetection_discrepancy": -(log_mean - log_positive),
        "mean_joint_compatibility": math.exp(log_mean),
        "conditional_nondetection_compatibility": math.exp(log_mean - log_positive),
        "weight_ess": ess,
        "largest_weight_share": float(scaled.max() / total),
        "mc_relative_se": relative_se,
    }
