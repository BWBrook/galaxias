#!/usr/bin/env python3
"""Build the conditional compatibility map from a frozen validation archive."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import sys
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from galaxias_model.abundance_detection import COMMON_EPISODE_FIELDS, OBSERVATION_MODELS, common_history_log_likelihood
from galaxias_model.common_model import CONFIGURATIONS, RESTRICTIONS
from scripts.run_common_model_comparison import (
    IDENTITY,
    PRIMARY_MODELS,
    file_hash,
    require_archive_input_binding,
    require_runtime_match,
    verify_archive,
)

EARLY_CUTOFFS = (0.50, 0.80, 0.95)
JOINT_CUTOFFS = (1e-6, 1e-4, 1e-2)
PAIRED_ENDPOINTS = ("terminal_survival", "min_total_over_preflood_mean", "extinction_time_censored")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def add_q_specific_reference(summary: pd.DataFrame) -> pd.DataFrame:
    """Normalise only within fixed q, observation law and configuration."""
    frame = summary.copy()
    group = ["configuration", "q", "observation_model"]
    if frame.empty:
        frame["reference_source_id"] = pd.Series(dtype=str)
        frame["reference_log_joint_mean"] = pd.Series(dtype=float)
        frame["reference_joint_mc_se"] = pd.Series(dtype=float)
        frame["reference_joint_mc_relative_se"] = pd.Series(dtype=float)
        frame["delta_log_W"] = pd.Series(dtype=float)
        return frame
    reference_rows = []
    for key, part in frame.groupby(group, sort=True):
        finite = part.loc[np.isfinite(part.log_joint_mean)]
        if finite.empty:
            reference_rows.append((*key, None, -math.inf, math.nan, math.nan))
            continue
        top = finite.sort_values(["log_joint_mean", "source_id"], ascending=[False, True]).iloc[0]
        reference_rows.append((*key, top.source_id, float(top.log_joint_mean),
                               float(top.joint_mc_se), float(top.joint_mc_relative_se)))
    references = pd.DataFrame(reference_rows, columns=group + ["reference_source_id", "reference_log_joint_mean",
                                                               "reference_joint_mc_se", "reference_joint_mc_relative_se"])
    frame = frame.merge(references, on=group, how="left", validate="many_to_one")
    frame["delta_log_W"] = frame.log_joint_mean - frame.reference_log_joint_mean
    both_negative = np.isneginf(frame.log_joint_mean) & np.isneginf(frame.reference_log_joint_mean)
    frame.loc[both_negative, "delta_log_W"] = np.nan
    return frame


def compatibility_map(summary: pd.DataFrame, ledger: pd.DataFrame | None = None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group = ["configuration", "restriction", "q", "observation_model"]
    for key, part in summary.groupby(group, sort=True):
        for early_cutoff in EARLY_CUTOFFS:
            for joint_cutoff in JOINT_CUTOFFS:
                witnesses = part.loc[
                    part.early_pattern_lower95.ge(early_cutoff)
                    & part.joint_lower95.ge(joint_cutoff)
                    & part.joint_mc_qualified.astype(bool)
                ]
                possible = part.loc[
                    part.early_pattern_upper95.ge(early_cutoff)
                    & part.joint_upper95.ge(joint_cutoff)
                ]
                if len(witnesses):
                    status = "compatible_witness_found"
                elif len(possible):
                    status = "unresolved_at_cap"
                else:
                    status = "not_found_at_cap"
                low = witnesses.loc[witnesses.K_R.lt(20)] if "K_R" in witnesses else witnesses.iloc[:0]
                high = witnesses.loc[witnesses.K_R.ge(20)] if "K_R" in witnesses else witnesses.iloc[:0]
                if len(low) and not len(high):
                    capacity_label = "low-refuge-capacity-dependent support"
                elif len(high):
                    capacity_label = "support at K_R>=20"
                else:
                    capacity_label = "no qualified witness"
                best = part.sort_values(["log_joint_mean", "source_id"], ascending=[False, True]).iloc[0]
                rows.append({**dict(zip(group, key, strict=True)), "early_cutoff": early_cutoff,
                             "joint_cutoff": joint_cutoff, "status": status,
                             "source_count": len(part), "viable_source_count": int(part.viable.sum()),
                             "qualified_witness_count": len(witnesses),
                             "witness_K_R_lt20_count": len(low), "witness_K_R_ge20_count": len(high),
                             "capacity_support_label": capacity_label,
                             "best_source_id": best.source_id,
                             "best_early_probability": best.early_pattern_probability,
                             "best_joint_mean": best.joint_mean,
                             "best_log_joint_mean": best.log_joint_mean,
                             "best_joint_mc_qualified": best.joint_mc_qualified,
                             "finite_search_interpretation": (
                                 "A failure to find a witness at the fixed cap does not exclude unsampled parameter regions "
                                 "or establish causal necessity. Cutoffs are declared numerical sensitivities.")})
    if ledger is not None:
        present = set(summary[group].itertuples(index=False, name=None))
        for item in ledger.to_dict("records"):
            key = tuple(item[column] for column in group)
            if key in present:
                continue
            for early_cutoff in EARLY_CUTOFFS:
                for joint_cutoff in JOINT_CUTOFFS:
                    rows.append({**{column: item[column] for column in group},
                                 "early_cutoff": early_cutoff, "joint_cutoff": joint_cutoff,
                                 "status": "not_found_at_cap", "source_count": 0,
                                 "viable_source_count": 0, "qualified_witness_count": 0,
                                 "witness_K_R_lt20_count": 0, "witness_K_R_ge20_count": 0,
                                 "capacity_support_label": "no qualified witness",
                                 "best_source_id": "", "best_early_probability": math.nan,
                                 "best_joint_mean": math.nan, "best_log_joint_mean": -math.inf,
                                 "best_joint_mc_qualified": False,
                                 "finite_search_interpretation": (
                                     "No validated candidate reached this declared cell. This is not causal exclusion; "
                                     "the finite search may have found no viable or retained source.")})
    return pd.DataFrame(rows)


def build_cell_ledger(search_summary: pd.DataFrame, refine_summary: pd.DataFrame,
                      validate_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for configuration in CONFIGURATIONS:
        for restriction in RESTRICTIONS:
            for q in (0.005, 0.02, 0.05, 0.2):
                for model in ("homogeneous", "shared_quality", "independent_quality"):
                    key = ((search_summary.configuration == configuration)
                           & (search_summary.restriction == restriction)
                           & np.isclose(search_summary.q, q)
                           & (search_summary.observation_model == model))
                    search = search_summary.loc[key]
                    rkey = ((refine_summary.configuration == configuration)
                            & (refine_summary.restriction == restriction)
                            & np.isclose(refine_summary.q, q)
                            & (refine_summary.observation_model == model))
                    vkey = ((validate_summary.configuration == configuration)
                            & (validate_summary.restriction == restriction)
                            & np.isclose(validate_summary.q, q)
                            & (validate_summary.observation_model == model))
                    rows.append({"configuration": configuration, "restriction": restriction,
                                 "q": q, "observation_model": model,
                                 "search_source_count": search.source_id.nunique(),
                                 "search_viable_source_count": search.loc[search.viable.astype(bool)].source_id.nunique(),
                                 "refine_source_count": refine_summary.loc[rkey].source_id.nunique(),
                                 "validate_source_count": validate_summary.loc[vkey].source_id.nunique(),
                                 "cell_status": ("validated" if validate_summary.loc[vkey].source_id.nunique()
                                                 else "no_validated_candidate")})
    return pd.DataFrame(rows)


def search_curves(search_summary: pd.DataFrame, search_sources: pd.DataFrame) -> pd.DataFrame:
    frame = search_summary.merge(search_sources[["source_id", "proposal_kind"]], on="source_id",
                                 how="left", validate="many_to_one")
    group = ["configuration", "restriction", "search_seed", "wave", "proposal_kind", "q", "observation_model"]
    rows = []
    for key, part in frame.groupby(group, sort=True, dropna=False):
        finite = part.loc[np.isfinite(part.log_joint_mean), "log_joint_mean"]
        rows.append({**dict(zip(group, key, strict=True)), "source_count": part.source_id.nunique(),
                     "viable_fraction": float(part.viable.mean()),
                     "finite_joint_support_fraction": float(np.isfinite(part.log_joint_mean).mean()),
                     "best_log_joint_mean": float(finite.max()) if len(finite) else -math.inf,
                     "median_log_joint_mean_finite": float(finite.median()) if len(finite) else -math.inf,
                     "q90_log_joint_mean_finite": float(finite.quantile(.9)) if len(finite) else -math.inf,
                     "best_early_pattern_probability": float(part.early_pattern_probability.max())})
    return pd.DataFrame(rows)


def capacity_summary(summary: pd.DataFrame) -> pd.DataFrame:
    group = ["configuration", "restriction", "search_seed", "q", "observation_model"]
    rows = []
    for key, part in summary.groupby(group, sort=True):
        # Ordinary means may underflow; finite log mean is the support test.
        supported = part.loc[np.isfinite(part.log_joint_mean)]
        rows.append({**dict(zip(group, key, strict=True)), "source_count": len(part),
                     "K_R_lt20_count": int(part.K_R.lt(20).sum()),
                     "positive_support_K_R_lt20_count": int(supported.K_R.lt(20).sum()),
                     "positive_support_K_R_ge20_count": int(supported.K_R.ge(20).sum()),
                     "K_L_median": part.K_L.median(), "K_R_median": part.K_R.median(),
                     "K_R_min": part.K_R.min(), "K_R_max": part.K_R.max(),
                     "PR011_median": part.PR011.median(), "PR033_median": part.PR033.median(),
                     "K_R_over_PR011_median": part.K_R_over_PR011.median()})
    columns = [*group, "source_count", "K_R_lt20_count", "positive_support_K_R_lt20_count",
               "positive_support_K_R_ge20_count", "K_L_median", "K_R_median", "K_R_min",
               "K_R_max", "PR011_median", "PR033_median", "K_R_over_PR011_median"]
    return pd.DataFrame(rows, columns=columns)


def annual_refuge_profiles(summary: pd.DataFrame) -> pd.DataFrame:
    suffixes = [column.removeprefix("weighted_N_R_") for column in summary
                if column.startswith("weighted_N_R_") and not column.endswith("_mc_se")]
    years = sorted(int(suffix) for suffix in suffixes if suffix.isdigit())
    rows = []
    for item in summary.to_dict("records"):
        witness_any = (item["early_pattern_lower95"] >= min(EARLY_CUTOFFS)
                       and item["joint_lower95"] >= min(JOINT_CUTOFFS)
                       and bool(item["joint_mc_qualified"]))
        base = {key: item[key] for key in (*IDENTITY, "source_id", "q", "observation_model")}
        for year in years:
            rows.append({**base, "year": year,
                         "unconditional_N_R_mean": item.get(f"unconditional_N_R_{year}"),
                         "factual_joint_weighted_N_R_mean": item.get(f"weighted_N_R_{year}"),
                         "factual_joint_weighted_N_R_mc_se": item.get(f"weighted_N_R_{year}_mc_se"),
                         "unconditional_refuge_presence": item.get(f"unconditional_N_R_presence_{year}"),
                         "factual_joint_weighted_refuge_presence": item.get(f"weighted_N_R_presence_{year}"),
                         "factual_joint_weighted_refuge_presence_mc_se": item.get(
                             f"weighted_N_R_presence_{year}_mc_se"),
                         "observed_joint_support": math.isfinite(item["log_joint_mean"]),
                         "qualified_at_least_permissive_grid_cell": witness_any})
    columns = [*IDENTITY, "source_id", "q", "observation_model", "year",
               "unconditional_N_R_mean", "factual_joint_weighted_N_R_mean",
               "factual_joint_weighted_N_R_mc_se", "unconditional_refuge_presence",
               "factual_joint_weighted_refuge_presence",
               "factual_joint_weighted_refuge_presence_mc_se", "observed_joint_support",
               "qualified_at_least_permissive_grid_cell"]
    return pd.DataFrame(rows, columns=columns)


def _component_summary(raw_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    totals: dict[str, dict[str, Any]] = {}
    for chunk in pd.read_csv(raw_path, chunksize=50_000, float_precision="round_trip"):
        component_columns = [column for column in chunk if column.startswith("early_")]
        require("early_ct005_directional_contrast" in component_columns,
                "validation histories lack CT005 component")
        for source_id, part in chunk.groupby("source_id", sort=False):
            target = totals.setdefault(str(source_id), {"replicate_count": 0})
            target["replicate_count"] += len(part)
            for column in component_columns:
                target[column] = target.get(column, 0) + int(part[column].astype(bool).sum())
            for field in COMMON_EPISODE_FIELDS:
                target[f"mean_{field}"] = target.get(f"mean_{field}", 0.0) + float(part[field].sum())
            for field in [column for column in part if column.startswith("ct005_")]:
                target[f"mean_{field}"] = target.get(f"mean_{field}", 0.0) + float(part[field].sum())
    rows = []
    for source_id, values in totals.items():
        n = values.pop("replicate_count")
        row = {"source_id": source_id, "replicate_count": n}
        for key, value in values.items():
            row[key.replace("early_", "") + "_fraction" if key.startswith("early_") else key] = value / n
        rows.append(row)
    components = pd.DataFrame(rows)
    if components.empty:
        components = pd.DataFrame(columns=["source_id", "replicate_count",
                                           "ct005_directional_contrast_fraction",
                                           "mean_ct005_N_L_1980", "mean_ct005_C_L_1980",
                                           "mean_ct005_N_L_1983", "mean_ct005_C_L_1983",
                                           "mean_ct005_cross_product_change"])
    ct_columns = [column for column in components if column.startswith("mean_ct005_")]
    ct005 = components[["source_id", "replicate_count", "ct005_directional_contrast_fraction", *ct_columns]].copy()
    return components, ct005


def _factual_weights(part: pd.DataFrame, q: float, model: str) -> tuple[np.ndarray, np.ndarray]:
    features = part[[f"{field}_factual" for field in COMMON_EPISODE_FIELDS]].copy()
    features.columns = COMMON_EPISODE_FIELDS
    eligible = (part["early_early_patterns_pass_factual"].astype(bool).to_numpy()
                & part["removals_valid_factual"].astype(bool).to_numpy())
    logs = common_history_log_likelihood(features, float(q), model)
    logs = np.where(eligible, logs, -math.inf)
    finite = np.isfinite(logs)
    weights = np.zeros(len(logs))
    if finite.any():
        maximum = float(logs[finite].max())
        weights[finite] = np.exp(logs[finite] - maximum)
        weights /= weights.sum()
    return weights, finite


def counterfactual_summary(validate_dir: Path, counterfactual_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    verify_archive(counterfactual_dir, phase="counterfactual")
    factual = pd.read_csv(validate_dir / "raw_histories.csv.gz", float_precision="round_trip")
    factual = factual.loc[factual.restriction.eq("R_J")]
    altered = pd.read_csv(counterfactual_dir / "counterfactual_histories.csv.gz", float_precision="round_trip")
    contrast_columns = ["source_id", "q", "observation_model", "counterfactual_infeasible_factual_weight_mass",
                        "counterfactual_infeasible_positive_factual_support_count",
                        "factual_weight_ess", "factual_largest_weight_share", "factual_weight_relative_se",
                        "weight_precision_qualified", "contrast_status", "endpoint", "endpoint_nonfinite_or_invalid_weight_mass",
                        "endpoint_nonfinite_or_invalid_positive_support_count",
                        "weighted_counterfactual_minus_factual", "paired_mc_se"]
    feasibility_columns = contrast_columns[:10]
    if factual.empty and altered.empty:
        return pd.DataFrame(columns=contrast_columns), pd.DataFrame(columns=feasibility_columns)
    keys = [*IDENTITY, "source_id", "replicate_index", "simulation_seed", "environment_seed"]
    require(not factual.duplicated(keys).any() and not altered.duplicated(keys).any(), "counterfactual pairing keys duplicate")
    joined = factual.merge(altered, on=keys, suffixes=("_factual", "_counterfactual"), how="left", validate="one_to_one")
    require(len(joined) == len(factual) and joined.filter(like="_counterfactual").notna().any(axis=1).all(),
            "counterfactual does not exactly cover frozen R_J validation histories")
    available_endpoints = {
        column.removeprefix("endpoint_").removesuffix("_factual")
        for column in joined if column.startswith("endpoint_") and column.endswith("_factual")
        and f"{column.removesuffix('_factual')}_counterfactual" in joined
    }
    endpoint_names = [name for name in PAIRED_ENDPOINTS if name in available_endpoints]
    require(set(endpoint_names) == set(PAIRED_ENDPOINTS), "counterfactual lacks a prespecified endpoint")
    rows = []
    infeasible_rows = []
    for source_id, part in joined.groupby("source_id", sort=True):
        feasible = part["removals_valid_counterfactual"].astype(bool).to_numpy()
        for q in sorted(part.get("q", pd.Series(dtype=float)).unique()) if "q" in part else (0.005, 0.02, 0.05, 0.2):
            for model in OBSERVATION_MODELS:
                weights, finite_support = _factual_weights(part, float(q), model)
                ess = float(1 / np.square(weights).sum()) if weights.sum() else 0.0
                largest = float(weights.max()) if weights.sum() else math.nan
                relative_se = (math.sqrt(max(0.0, (len(weights) / ess - 1) / (len(weights) - 1)))
                               if ess > 0 and len(weights) > 1 else math.nan)
                precision = bool(ess >= 100 and relative_se <= .1 and largest <= .05)
                missing_mass = float(weights[~feasible].sum())
                invalid_positive_support_count = int((~feasible & finite_support).sum())
                base = {"source_id": source_id, "q": q, "observation_model": model,
                        "counterfactual_infeasible_factual_weight_mass": missing_mass,
                        "counterfactual_infeasible_positive_factual_support_count": invalid_positive_support_count,
                        "factual_weight_ess": ess, "factual_largest_weight_share": largest,
                        "factual_weight_relative_se": relative_se,
                        "weight_precision_qualified": precision,
                        "contrast_status": ("resolved" if invalid_positive_support_count == 0 and weights.sum() > 0 and precision
                                            else "unresolved_precision" if invalid_positive_support_count == 0 and weights.sum() > 0
                                            else "unresolved_support_or_validity")}
                infeasible_rows.append(base)
                for endpoint in endpoint_names:
                    factual_values = part[f"endpoint_{endpoint}_factual"].to_numpy(float)
                    counter_values = part[f"endpoint_{endpoint}_counterfactual"].to_numpy(float)
                    valid = feasible & np.isfinite(factual_values) & np.isfinite(counter_values)
                    endpoint_missing_mass = float(weights[~valid].sum())
                    endpoint_invalid_positive_support_count = int((~valid & finite_support).sum())
                    difference = np.where(valid, counter_values - factual_values, 0.0)
                    estimate = float(np.dot(weights, difference))
                    mc_se = (math.sqrt(len(weights) / (len(weights) - 1)
                                       * float(np.square(weights * (difference - estimate)).sum()))
                             if len(weights) > 1 else math.nan)
                    valid_contrast = (invalid_positive_support_count == 0 and weights.sum() > 0
                                      and endpoint_invalid_positive_support_count == 0)
                    rows.append({**base, "endpoint": endpoint,
                                 "endpoint_nonfinite_or_invalid_weight_mass": endpoint_missing_mass,
                                 "endpoint_nonfinite_or_invalid_positive_support_count": endpoint_invalid_positive_support_count,
                                 "weighted_counterfactual_minus_factual": estimate if valid_contrast else math.nan,
                                 "paired_mc_se": mc_se if valid_contrast else math.nan,
                                 "contrast_status": (base["contrast_status"] if valid_contrast
                                                     else "unresolved_support_or_validity")})
    return pd.DataFrame(rows), pd.DataFrame(infeasible_rows).drop_duplicates()


def paired_toggle_summary(validate_dir: Path, toggle_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    manifest = verify_archive(toggle_dir, phase="paired_toggle")
    n = int(manifest["replicates_per_toggle"])
    factual = pd.read_csv(validate_dir / "raw_histories.csv.gz", float_precision="round_trip")
    factual = factual.loc[factual.restriction.eq("R_J") & factual.replicate_index.le(n)]
    toggles = pd.read_csv(toggle_dir / "paired_toggle_histories.csv.gz", float_precision="round_trip")
    contrast_columns = ["source_id", "evaluated_restriction", "q", "observation_model", "replicate_count",
                        "factual_weight_ess", "primary_mc_qualified", "diagnostic_precision_qualified",
                        "factual_largest_weight_share",
                        "factual_weight_relative_se", "toggle_invalid_factual_weight_mass", "contrast_status",
                        "toggle_invalid_positive_factual_support_count",
                        "interpretation", "endpoint", "endpoint_nonfinite_or_invalid_weight_mass",
                        "endpoint_nonfinite_or_invalid_positive_support_count",
                        "weighted_toggle_minus_factual", "paired_mc_se"]
    feasibility_columns = [column for column in contrast_columns
                           if column not in {"endpoint", "endpoint_nonfinite_or_invalid_weight_mass",
                                             "endpoint_nonfinite_or_invalid_positive_support_count",
                                             "weighted_toggle_minus_factual", "paired_mc_se"}]
    if factual.empty and toggles.empty:
        return pd.DataFrame(columns=contrast_columns), pd.DataFrame(columns=feasibility_columns)
    factual_keys = ["search_seed", "configuration", "wave", "source_index", "source_id",
                    "replicate_index", "simulation_seed", "environment_seed"]
    require(not factual.duplicated(factual_keys).any(), "factual toggle keys duplicate")
    require(not toggles.duplicated(factual_keys + ["evaluated_restriction"]).any(), "toggle keys duplicate")
    joined = factual.merge(toggles, on=factual_keys, suffixes=("_factual", "_toggle"),
                           how="inner", validate="one_to_many")
    require(len(joined) == len(factual) * 3, "paired toggles do not cover every factual history three times")
    available_endpoints = {
        column.removeprefix("endpoint_").removesuffix("_factual")
        for column in joined if column.startswith("endpoint_") and column.endswith("_factual")
        and f"{column.removesuffix('_factual')}_toggle" in joined
    }
    endpoint_names = [name for name in PAIRED_ENDPOINTS if name in available_endpoints]
    require(set(endpoint_names) == set(PAIRED_ENDPOINTS), "paired toggle lacks a prespecified endpoint")
    rows = []; feasibility = []
    for (source_id, evaluated), part in joined.groupby(["source_id", "evaluated_restriction"], sort=True):
        feasible = part["removals_valid_toggle"].astype(bool).to_numpy()
        for q in (0.005, 0.02, 0.05, 0.2):
            for model in OBSERVATION_MODELS:
                weights, finite_support = _factual_weights(part, q, model)
                ess = float(1 / np.square(weights).sum()) if weights.sum() else 0.0
                largest = float(weights.max()) if weights.sum() else math.nan
                relative_se = (math.sqrt(max(0.0, (len(weights) / ess - 1) / (len(weights) - 1)))
                               if ess > 0 and len(weights) > 1 else math.nan)
                diagnostic_precision = bool(relative_se <= .1 and largest <= .05)
                missing_mass = float(weights[~feasible].sum())
                invalid_positive_support_count = int((~feasible & finite_support).sum())
                status = ("resolved" if weights.sum() and invalid_positive_support_count == 0 and diagnostic_precision
                          else "unresolved_precision" if weights.sum() and invalid_positive_support_count == 0
                          else "unresolved_support_or_validity")
                base = {"source_id": source_id, "evaluated_restriction": evaluated,
                        "q": q, "observation_model": model, "replicate_count": len(part),
                        "factual_weight_ess": ess, "primary_mc_qualified": False,
                        "diagnostic_precision_qualified": diagnostic_precision,
                        "factual_largest_weight_share": largest,
                        "factual_weight_relative_se": relative_se,
                        "toggle_invalid_factual_weight_mass": missing_mass,
                        "toggle_invalid_positive_factual_support_count": invalid_positive_support_count,
                        "contrast_status": status,
                        "interpretation": "fixed-R_J-parameter paired diagnostic; not a compatibility witness"}
                feasibility.append(base)
                for endpoint in endpoint_names:
                    factual_values = part[f"endpoint_{endpoint}_factual"].to_numpy(float)
                    toggle_values = part[f"endpoint_{endpoint}_toggle"].to_numpy(float)
                    valid = feasible & np.isfinite(factual_values) & np.isfinite(toggle_values)
                    endpoint_missing_mass = float(weights[~valid].sum())
                    endpoint_invalid_positive_support_count = int((~valid & finite_support).sum())
                    difference = np.where(valid, toggle_values - factual_values, 0.0)
                    estimate = float(np.dot(weights, difference))
                    mc_se = (math.sqrt(len(weights) / (len(weights) - 1)
                                       * float(np.square(weights * (difference - estimate)).sum()))
                             if len(weights) > 1 else math.nan)
                    valid_contrast = (weights.sum() > 0 and invalid_positive_support_count == 0
                                      and endpoint_invalid_positive_support_count == 0)
                    rows.append({**base, "endpoint": endpoint,
                                 "endpoint_nonfinite_or_invalid_weight_mass": endpoint_missing_mass,
                                 "endpoint_nonfinite_or_invalid_positive_support_count": endpoint_invalid_positive_support_count,
                                 "weighted_toggle_minus_factual": estimate if valid_contrast else math.nan,
                                 "paired_mc_se": mc_se if valid_contrast else math.nan,
                                 "contrast_status": (status if valid_contrast
                                                     else "unresolved_support_or_validity")})
    return pd.DataFrame(rows), pd.DataFrame(feasibility).drop_duplicates()


def analyze(search_dir: Path, refine_dir: Path, validate_dir: Path, output_dir: Path, *, counterfactual_dir: Path | None = None,
            paired_toggle_dir: Path | None = None) -> dict[str, Any]:
    search_dir, refine_dir = Path(search_dir), Path(refine_dir)
    validate_dir, output_dir = Path(validate_dir), Path(output_dir)
    search_manifest = verify_archive(search_dir, phase="search")
    refine_manifest = verify_archive(refine_dir, phase="refine")
    manifest = verify_archive(validate_dir, phase="validate")
    require_runtime_match(search_manifest, refine_manifest, manifest)
    require_archive_input_binding(refine_manifest, search_dir)
    require_archive_input_binding(manifest, search_dir)
    require_archive_input_binding(manifest, refine_dir)
    require(not output_dir.exists(), "analysis output directory already exists")
    output_dir.mkdir(parents=True, exist_ok=False)
    summary = pd.read_csv(validate_dir / "source_summary.csv", float_precision="round_trip")
    search_summary = pd.read_csv(search_dir / "source_summary.csv", float_precision="round_trip")
    refine_summary = pd.read_csv(refine_dir / "source_summary.csv", float_precision="round_trip")
    search_sources = pd.read_csv(search_dir / "sources.csv", float_precision="round_trip")
    sources = pd.read_csv(validate_dir / "sources.csv", float_precision="round_trip")
    require(not summary.duplicated(["source_id", "q", "observation_model"]).any(),
            "validation summary grain is not source/profile")
    source_columns = [column for column in ("source_id", "K_L", "K_R", "PR011", "K_R_over_PR011", "PR033")
                      if column in sources]
    summary = summary.merge(sources[source_columns], on="source_id", how="left", validate="many_to_one",
                            suffixes=("", "_source"))
    for column in ("K_L", "K_R", "PR011", "K_R_over_PR011", "PR033"):
        if f"{column}_source" in summary:
            summary[column] = summary[column].fillna(summary[f"{column}_source"])
            summary.drop(columns=f"{column}_source", inplace=True)
    referenced = add_q_specific_reference(summary)
    ledger = build_cell_ledger(search_summary, refine_summary, referenced)
    compatibility = compatibility_map(referenced, ledger)
    curves = search_curves(search_summary, search_sources)
    capacities = capacity_summary(referenced)
    annual_refuge = annual_refuge_profiles(referenced)
    components, ct005 = _component_summary(validate_dir / "raw_histories.csv.gz")
    identity = sources[[*IDENTITY, "source_id"]]
    components = components.merge(identity, on="source_id", how="left", validate="one_to_one")
    ct005 = ct005.merge(identity, on="source_id", how="left", validate="one_to_one")
    outputs = {
        "validated_source_profiles.csv": referenced,
        "cell_ledger.csv": ledger,
        "compatibility_map.csv": compatibility,
        "search_curves.csv": curves,
        "capacity_stratified_support.csv": capacities,
        "annual_refuge_by_profile.csv.gz": annual_refuge,
        "early_component_summary.csv": components,
        "ct005_summary.csv": ct005,
    }
    for name, frame in outputs.items():
        frame.to_csv(output_dir / name, index=False, float_format="%.17g",
                     compression="gzip" if name.endswith(".gz") else None)
    ancestry_parts = []
    for phase_name, path in (("refine", search_dir / "refine_selection_membership.csv"),
                             ("validate", refine_dir / "validate_selection_membership.csv")):
        membership = pd.read_csv(path)
        membership.insert(0, "selection_for_phase", phase_name)
        ancestry_parts.append(membership)
    pd.concat(ancestry_parts, ignore_index=True).to_csv(output_dir / "selection_ancestry.csv", index=False)
    if counterfactual_dir is not None:
        counter_manifest = verify_archive(Path(counterfactual_dir), phase="counterfactual")
        require_runtime_match(counter_manifest)
        require_archive_input_binding(counter_manifest, search_dir)
        require_archive_input_binding(counter_manifest, validate_dir)
        contrasts, infeasible = counterfactual_summary(validate_dir, Path(counterfactual_dir))
        contrasts.to_csv(output_dir / "overshoot_counterfactual_contrasts.csv", index=False, float_format="%.17g")
        infeasible.to_csv(output_dir / "overshoot_counterfactual_feasibility.csv", index=False, float_format="%.17g")
    if paired_toggle_dir is not None:
        toggle_manifest = verify_archive(Path(paired_toggle_dir), phase="paired_toggle")
        require_runtime_match(toggle_manifest)
        require_archive_input_binding(toggle_manifest, search_dir)
        require_archive_input_binding(toggle_manifest, validate_dir)
        toggles, toggle_feasibility = paired_toggle_summary(validate_dir, Path(paired_toggle_dir))
        toggles.to_csv(output_dir / "paired_toggle_contrasts.csv", index=False, float_format="%.17g")
        toggle_feasibility.to_csv(output_dir / "paired_toggle_feasibility.csv", index=False, float_format="%.17g")
    report = (
        "# Common-model conditional compatibility map\n\n"
        "This analysis uses the frozen validation sources without reselection. A compatible witness is conditional "
        "on the declared numerical cutoffs, q scenario, observation representation, structural configuration and "
        "finite search. `not_found_at_cap` does not exclude an unsampled region or establish causal necessity. "
        "Absolute joint weights are not compared across q values. Capacity below 20 is a diagnostic stratum, not "
        "an empirical inadequacy rule. The minimum dated removals arm does not test the broader removal hypothesis.\n"
    )
    (output_dir / "interpretation_limits.md").write_text(report, encoding="utf-8")
    receipt = {"status": "complete", "scope": "common_model_comparison_analysis",
               "validation_manifest": file_hash(validate_dir / "run_manifest.json"),
               "search_manifest": file_hash(search_dir / "run_manifest.json"),
               "refine_manifest": file_hash(refine_dir / "run_manifest.json"),
               "counterfactual_manifest": (file_hash(Path(counterfactual_dir) / "run_manifest.json")
                                               if counterfactual_dir is not None else None),
               "paired_toggle_manifest": (file_hash(Path(paired_toggle_dir) / "run_manifest.json")
                                             if paired_toggle_dir is not None else None),
               "validation_reselection": False,
               "runtime": {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__,
                           "platform": platform.platform()},
               "normalisation": "within fixed q, observation_model, configuration only",
               "cutoffs": {"early": EARLY_CUTOFFS, "joint": JOINT_CUTOFFS},
               "outputs": {path.name: file_hash(path) for path in output_dir.iterdir() if path.is_file()}}
    (output_dir / "analysis_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-dir", type=Path, required=True)
    parser.add_argument("--refine-dir", type=Path, required=True)
    parser.add_argument("--validate-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--counterfactual-dir", type=Path)
    parser.add_argument("--paired-toggle-dir", type=Path)
    args = parser.parse_args()
    analyze(args.search_dir, args.refine_dir, args.validate_dir, args.output_dir,
            counterfactual_dir=args.counterfactual_dir,
            paired_toggle_dir=args.paired_toggle_dir)
