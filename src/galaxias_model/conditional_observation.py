"""Conditional observation scenarios for fresh stochastic calibration.

The shared-window scenarios use one detection uniform per survey block, shared
over its occupied years. Blocks remain independent. These are sensitivity
assumptions, not estimated survey detection models.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .observation_repair import LATE_BLOCK_WEIGHT, aggregate_repaired_late_evidence

CONDITIONAL_PROFILES = {
    "repair_presence_only": (0.0, "independent"),
    "repair_detection_060": (0.60, "independent"),
    "repair_detection_098": (0.98, "independent"),
    "repair_shared_window_060": (0.60, "shared_window"),
    "repair_shared_window_098": (0.98, "shared_window"),
}
IDENTITY = ["search_seed", "family_id", "proposal_id"]
PHYSICS = ["surviving_2002", "n_total_1995", "n_total_2002",
           "n_total_1992_1996_mean", "lake_nondetection_occupied_episodes",
           "natural_nondetection_occupied_episodes"]


def effective_episodes(features, profile):
    _, dependence = CONDITIONAL_PROFILES[profile]
    lake = features.lake_nondetection_occupied_episodes.to_numpy(dtype=float)
    natural = features.natural_nondetection_occupied_episodes.to_numpy(dtype=float)
    for values, maximum in [(lake, 2), (natural, 5)]:
        if not (np.isfinite(values).all() and ((values >= 0) & (values <= maximum) & (values == np.floor(values))).all()):
            raise ValueError("Invalid domain-specific occupied episode counts")
    if not np.array_equal(lake + natural, features.nondetection_occupied_episodes.to_numpy()):
        raise ValueError("Occupied episode counts do not sum")
    return (lake > 0).astype(int) + (natural > 0).astype(int) if dependence == "shared_window" else lake + natural


def history_weights(features, profile):
    p, _ = CONDITIONAL_PROFILES[profile]
    if not features.positive_records_compatible.isin([True, False]).all():
        raise ValueError("Positive compatibility must be Boolean")
    return features.positive_records_compatible.to_numpy(dtype=bool) * np.power(1 - p, effective_episodes(features, profile))


def source_summaries(raw):
    """All-history discrepancy and equally weighted source diagnostics.

Only five early targets and two cached intrinsic targets enter the score;
legacy late penalties remain in the raw archive for provenance.
"""
    rows = []
    native = [c for c in raw if c not in {*IDENTITY, "stage", "replicate_index", "simulation_seed"} and not c.startswith("CT")]
    for identity, group in raw.groupby(IDENTITY, sort=True):
        intrinsic = group[[f"CT{i:03d}_weighted_penalty" for i in (11, 12)]].sum(axis=1)
        early = group[[f"CT{i:03d}_weighted_penalty" for i in range(1, 6)]].sum(axis=1)
        if not np.isfinite(early).all() or not np.isfinite(intrinsic).all() or not np.allclose(intrinsic, intrinsic.iloc[0]):
            raise ValueError("Invalid early scores or varying intrinsic cache")
        physical = {}
        for c in native:
            values = group[c].dropna()
            physical.update({f"{c}_{stat}": float(values.agg(stat)) if len(values) else math.nan for stat in ("mean", "median")})
        for c in ("first_zero_year", "latent_last_presence_year"):
            if c in group:
                physical[f"{c}_valid_replicates"] = int(group[c].notna().sum())
        base = {**dict(zip(IDENTITY, identity)), "stage": group.stage.iloc[0],
                "intrinsic_distance": float(intrinsic.iloc[0]),
                "early_distance": float(early.median()),
                "historical_iqr": float(early.quantile(.75) - early.quantile(.25)), **physical}
        for profile, (p, dependence) in CONDITIONAL_PROFILES.items():
            features = group[["positive_records_compatible"]].copy()
            features["nondetection_occupied_episodes"] = effective_episodes(group, profile)
            late = aggregate_repaired_late_evidence(features, p)
            weights = history_weights(group, profile)
            total = weights.sum()
            conditioned = {f"compatibility_weighted_{c}": float(np.dot(weights, group[c]) / total) if total else math.nan for c in PHYSICS if c in group}
            overall = float((early + intrinsic).median()) + LATE_BLOCK_WEIGHT * late["late_discrepancy"]
            rows.append({**base, "profile": profile, "diagnostic_detection_probability": p,
                         "detection_dependence": dependence,
                         "overall_distance": overall,
                         "historical_distance": float(early.median()) + LATE_BLOCK_WEIGHT * late["late_discrepancy"],
                         "finite_supported": math.isfinite(overall), **late, **conditioned})
    return pd.DataFrame(rows)
