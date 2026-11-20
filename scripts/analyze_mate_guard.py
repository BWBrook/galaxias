#!/usr/bin/env python3
"""Analyse the fixed-source singleton breeding-guard sensitivity.

This module only reads completed archives.  It deliberately keeps the old
factual weights separate from the amended kernel's weights: paired contrasts
are descriptive along matched streams, while compatibility and survival are
rescored from the amended histories without source reselection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from galaxias_model.abundance_detection import (  # noqa: E402
    COMMON_EPISODE_FIELDS,
    OBSERVATION_MODELS,
    Q_SCENARIOS,
    common_history_log_likelihood,
)
from scripts.run_common_model_comparison import file_hash  # noqa: E402


Z = 1.96
Z_WILSON = 1.959963984540054
EARLY_CUTOFFS = (0.50, 0.80, 0.95)
JOINT_CUTOFFS = (1e-6, 1e-4, 1e-2)
IDENTITY = ("search_seed", "configuration", "restriction", "wave", "source_index", "source_id")
SEED_KEYS = ("replicate_index", "simulation_seed", "environment_seed")

ENDPOINTS = {
    "terminal_survival": ("endpoint_terminal_survival", "endpoint_survived_2002", "terminal_survival", "survived_2002"),
    "min_total_over_preflood_mean": ("endpoint_min_total_over_preflood_mean", "min_total_over_preflood_mean"),
    "extinction_time_censored": ("endpoint_extinction_time_censored", "extinction_time_censored"),
    "N_total_2002": ("endpoint_N_total_2002", "N_total_2002", "annual_N_total_2002"),
    "N_R_2002": ("endpoint_N_R_2002", "N_R_2002", "annual_N_R_2002"),
    "early_lake_1980": ("endpoint_ct005_N_L_1980", "ct005_N_L_1980", "early_lake_1980"),
    "early_lake_1983": ("endpoint_ct005_N_L_1983", "ct005_N_L_1983", "early_lake_1983"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _hash(path: Path) -> dict[str, Any]:
    return file_hash(Path(path))


def _manifest(directory: Path, required: Iterable[str]) -> dict[str, Any]:
    path = Path(directory) / "run_manifest.json"
    require(path.exists(), f"missing run manifest: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    require(manifest.get("status") == "complete", f"archive is not complete: {directory}")
    # Verify every declared output when a manifest carries the established
    # {bytes, sha256} binding.  This also accepts manifests that list nested
    # per-source files under a relative path.
    declared = manifest.get("outputs", {})
    for name, expected in declared.items():
        if not isinstance(expected, Mapping) or not {"bytes", "sha256"}.issubset(expected):
            continue
        output = Path(directory) / name
        require(output.exists() and _hash(output) == {"bytes": expected["bytes"], "sha256": expected["sha256"]},
                f"manifest output hash drift: {output}")
    for name in required:
        require((Path(directory) / name).exists(), f"missing required archive file: {Path(directory) / name}")
        expected = declared.get(name)
        if isinstance(expected, Mapping) and {"bytes", "sha256"}.issubset(expected):
            require(_hash(Path(directory) / name) == {"bytes": expected["bytes"], "sha256": expected["sha256"]},
                    f"manifest input hash drift: {Path(directory) / name}")
    return manifest


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, float_precision="round_trip")


def _bool_column(frame: pd.DataFrame, name: str) -> np.ndarray:
    require(name in frame, f"history rows lack {name}")
    values = frame[name]
    require(values.notna().all(), f"{name} contains missing values")
    if values.dtype == bool:
        return values.to_numpy(bool)
    numeric = pd.to_numeric(values, errors="coerce")
    require(numeric.notna().all() and numeric.isin([0, 1]).all(), f"{name} is not boolean")
    return numeric.astype(bool).to_numpy()


def _source_ordinal_sources(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "source_ordinal" not in result:
        result.insert(0, "source_ordinal", np.arange(1, len(result) + 1, dtype=int))
    result["source_ordinal"] = pd.to_numeric(result["source_ordinal"], errors="raise").astype(int)
    require(result.source_ordinal.is_unique, "source_ordinal is not unique")
    require(result.source_id.astype(str).is_unique, "source_id is not unique")
    return result


def _compare_sources(baseline: pd.DataFrame, amended: pd.DataFrame) -> pd.DataFrame:
    old = _source_ordinal_sources(baseline)
    new = _source_ordinal_sources(amended)
    require(set(new.source_id.astype(str)).issubset(set(old.source_id.astype(str))),
            "amended source identities are absent from baseline")
    old = old.loc[old.source_id.astype(str).isin(set(new.source_id.astype(str)))]
    join = old.merge(new, on="source_id", how="inner", suffixes=("_old", "_new"), validate="one_to_one")
    for column in ("search_seed", "configuration", "restriction", "wave", "source_index"):
        if f"{column}_old" in join and f"{column}_new" in join:
            require(join[f"{column}_old"].astype(str).equals(join[f"{column}_new"].astype(str)),
                    f"source identity field differs: {column}")
    if "viable_old" in join and "original_viable" in join:
        require(join["viable_old"].astype(bool).equals(join["original_viable"].astype(bool)),
                "original viability differs from baseline source table")
    # Parameter tables are immutable inputs to the paired comparison.  Check
    # exact values when both archives expose the conventional columns.
    return join


def _parameter_fingerprint(directory: Path, source_ids: set[str] | None = None) -> str:
    path = Path(directory) / "parameter_values.csv.gz"
    frame = _read(path)
    columns = [c for c in ("source_id", "parameter_id", "value_natural", "parameter_status") if c in frame]
    require({"source_id", "parameter_id", "value_natural"}.issubset(columns),
            f"parameter table lacks immutable value columns: {path}")
    frame = frame.loc[:, columns]
    if source_ids is not None:
        frame = frame.loc[frame.source_id.astype(str).isin(source_ids)]
    sort = [c for c in ("source_id", "parameter_id") if c in frame]
    if sort:
        frame = frame.sort_values(sort, kind="mergesort").reset_index(drop=True)
    return hashlib.sha256(frame.to_csv(index=False, float_format="%.17g").encode()).hexdigest()


def _raw_key_columns(old: pd.DataFrame, new: pd.DataFrame) -> list[str]:
    common = [c for c in (*IDENTITY, "source_ordinal", *SEED_KEYS) if c in old and c in new]
    required = [c for c in (*SEED_KEYS,) if c not in common]
    require(not required, f"paired histories lack seed keys: {required}")
    if "source_id" not in common and "source_ordinal" not in common:
        raise ValueError("paired histories lack source identity key")
    return common


def _pair_histories(old: pd.DataFrame, new: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    keys = _raw_key_columns(old, new)
    for frame, label in ((old, "baseline"), (new, "amended")):
        require(not frame.duplicated(keys).any(), f"{label} history keys duplicate")
    left = old.copy()
    right = new.copy()
    suffix = {c: f"{c}_old" for c in old.columns if c not in keys}
    left = left.rename(columns=suffix)
    suffix = {c: f"{c}_new" for c in new.columns if c not in keys}
    right = right.rename(columns=suffix)
    joined = left.merge(right, on=keys, how="outer", validate="one_to_one", indicator=True)
    require(joined._merge.eq("both").all(), "baseline and amended histories do not pair exactly")
    return joined.drop(columns="_merge"), keys


def _column(frame: pd.DataFrame, aliases: Iterable[str]) -> str | None:
    for name in aliases:
        if name in frame:
            return name
    return None


def _endpoints(frame: pd.DataFrame, *, require_all: bool = False) -> dict[str, np.ndarray]:
    result: dict[str, np.ndarray] = {}
    for name, aliases in ENDPOINTS.items():
        column = _column(frame, aliases)
        if column is not None:
            result[name] = pd.to_numeric(frame[column], errors="coerce").to_numpy(float)
        elif require_all and name in {"terminal_survival", "min_total_over_preflood_mean", "extinction_time_censored"}:
            raise ValueError(f"history rows lack required endpoint {name}")
    # Include all matched annual totals for late diagnostics where available.
    for prefix in ("annual_N_total_", "endpoint_N_total_"):
        for column in frame.columns:
            if column.startswith(prefix):
                year = column.removeprefix(prefix)
                name = f"late_annual_total_{year}"
                if name not in result:
                    result[name] = pd.to_numeric(frame[column], errors="coerce").to_numpy(float)
    return result


def _wilson(successes: int, trials: int) -> tuple[float, float]:
    p = successes / trials
    denominator = 1 + Z_WILSON * Z_WILSON / trials
    centre = (p + Z_WILSON * Z_WILSON / (2 * trials)) / denominator
    radius = Z_WILSON / denominator * math.sqrt(p * (1 - p) / trials + Z_WILSON * Z_WILSON / (4 * trials * trials))
    return max(0.0, centre - radius), min(1.0, centre + radius)


def _weights(raw: pd.DataFrame, viable: bool, q: float, law: str) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    require(set(COMMON_EPISODE_FIELDS).issubset(raw.columns), "history rows lack common observation fields")
    logs = common_history_log_likelihood(raw.loc[:, COMMON_EPISODE_FIELDS], float(q), law)
    eligible = _bool_column(raw, "early_early_patterns_pass") & _bool_column(raw, "removals_valid") & bool(viable)
    logs = np.where(eligible, logs, -math.inf)
    finite = np.isfinite(logs)
    weights = np.zeros(len(raw), dtype=float)
    if finite.any():
        maximum = float(logs[finite].max())
        scaled = np.exp(logs[finite] - maximum)
        weights[finite] = scaled / scaled.sum()
        log_mean = maximum + math.log(float(scaled.sum())) - math.log(len(logs))
    else:
        log_mean = -math.inf
    ess = float(1 / np.square(weights).sum()) if weights.sum() else 0.0
    rse = math.sqrt(max(0.0, (len(weights) / ess - 1) / (len(weights) - 1))) if ess and len(weights) > 1 else math.nan
    largest = float(weights.max()) if weights.sum() else math.nan
    stats = {
        "log_joint_mean": log_mean,
        "joint_mean": math.exp(log_mean) if math.isfinite(log_mean) and log_mean > -745 else 0.0,
        "positive_supported_count": int(finite.sum()),
        "weight_ess": ess,
        "weight_relative_se": rse,
        "largest_weight_share": largest,
        "weight_qualified": bool(ess >= 100 and rse <= 0.1 and largest <= 0.05),
    }
    return weights, finite, stats


def _survivor_stats(weights: np.ndarray, raw: pd.DataFrame) -> tuple[float, float, float]:
    endpoint = _column(raw, ENDPOINTS["terminal_survival"])
    if endpoint is None or not weights.sum():
        return 0.0, math.nan, math.nan
    values = pd.to_numeric(raw[endpoint], errors="coerce").to_numpy(float)
    selected = weights * (values > 0)
    if not selected.sum():
        return 0.0, math.nan, math.nan
    selected /= selected.sum()
    ess = float(1 / np.square(selected).sum())
    rse = math.sqrt(max(0.0, (len(weights) / ess - 1) / (len(weights) - 1))) if len(weights) > 1 else math.nan
    return ess, rse, float(selected.max())


def _profile(raw: pd.DataFrame, viable: bool, q: float, law: str) -> dict[str, Any]:
    weights, support, stats = _weights(raw, viable, q, law)
    early = _bool_column(raw, "early_early_patterns_pass") if viable else np.zeros(len(raw), bool)
    early_lower, early_upper = _wilson(int(early.sum()), len(raw)) if len(raw) else (0.0, 0.0)
    if not early.any() and len(raw):
        early_upper = 1 - 0.05 ** (1 / len(raw))
    logs = common_history_log_likelihood(raw.loc[:, COMMON_EPISODE_FIELDS], float(q), law)
    eligible = _bool_column(raw, "early_early_patterns_pass") & _bool_column(raw, "removals_valid") & bool(viable)
    joint_logs = np.where(eligible, logs, -math.inf)
    # The profile lower bound is the established log-mean lower bound.
    if support.any():
        maximum = float(joint_logs[support].max())
        scaled = np.zeros(len(raw)); scaled[support] = np.exp(joint_logs[support] - maximum)
        mean = math.exp(maximum) * float(scaled.mean())
        se = math.exp(maximum) * float(scaled.std(ddof=1) / math.sqrt(len(raw))) if len(raw) > 1 else math.nan
        joint_lower = max(0.0, mean - Z * se)
        joint_upper = min(1.0, mean + Z * se)
    else:
        joint_lower = 0.0
        joint_upper = 1 - 0.05 ** (1 / len(raw)) if len(raw) else 0.0
    stats.update(early_pattern_lower95=early_lower, early_pattern_upper95=early_upper,
                 joint_lower95=joint_lower, joint_upper95=joint_upper)
    return stats


def _status(profile: Mapping[str, Any], early_cutoff: float, joint_cutoff: float) -> str:
    if (profile["early_pattern_lower95"] >= early_cutoff
            and profile["joint_lower95"] >= joint_cutoff
            and profile["weight_qualified"]):
        return "qualified-compatible"
    if profile["early_pattern_upper95"] >= early_cutoff and profile["joint_upper95"] >= joint_cutoff:
        return "unresolved"
    return "notfound"


def _weighted_endpoint(weights: np.ndarray, values: np.ndarray) -> tuple[float, float]:
    valid = np.isfinite(values)
    if not weights.sum() or not valid.all():
        return math.nan, math.nan
    estimate = float(np.dot(weights, values))
    se = math.sqrt(len(weights) / (len(weights) - 1) * float(np.square(weights * (values - estimate)).sum())) if len(weights) > 1 else math.nan
    return estimate, se


def _paired_rows(joined: pd.DataFrame, old_sources: pd.DataFrame, new_sources: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    source_column = "source_id" if "source_id" in joined else "source_ordinal"
    for source_id, part in joined.groupby(source_column, sort=True):
        source_record = new_sources.loc[new_sources.source_id.astype(str).eq(str(source_id))].iloc[0]
        old_viable = bool(old_sources.loc[old_sources.source_id.astype(str).eq(str(source_id)), "original_viable"].iloc[0]) if "original_viable" in old_sources else bool(old_sources.loc[old_sources.source_id.astype(str).eq(str(source_id)), "viable"].iloc[0])
        for q in Q_SCENARIOS:
            for law in OBSERVATION_MODELS:
                old_raw = part.rename(columns={c: c.removesuffix("_old") for c in part if c.endswith("_old")})
                weights, support, stats = _weights(old_raw, old_viable, float(q), law)
                invalid = ~_bool_column(part, "removals_valid_new")
                invalid_support = int((invalid & support).sum())
                base = {"source_id": source_id, "configuration": source_record.get("configuration", ""),
                        "restriction": source_record.get("restriction", ""), "q": q, "observation_model": law,
                        "original_viable": old_viable, "old_positive_support_count": int(support.sum()),
                        "old_weight_ess": stats["weight_ess"], "old_weight_relative_se": stats["weight_relative_se"],
                        "old_largest_weight_share": stats["largest_weight_share"], "old_weight_qualified": stats["weight_qualified"],
                        "new_invalid_removal_positive_support_count": invalid_support,
                        "new_invalid_removal_old_weight_mass": float(weights[invalid].sum())}
                old_end = _endpoints(old_raw)
                new_end = {name: pd.to_numeric(part[_column(part, tuple(f"{a}_new" for a in aliases))], errors="coerce").to_numpy(float)
                           for name, aliases in ENDPOINTS.items()
                           if _column(part, tuple(f"{a}_new" for a in aliases)) is not None}
                for endpoint in sorted(set(old_end) & set(new_end)):
                    difference = new_end[endpoint] - old_end[endpoint]
                    finite = np.isfinite(old_end[endpoint]) & np.isfinite(new_end[endpoint])
                    invalid_endpoint = int((~finite & support).sum())
                    defined = bool(weights.sum() and invalid_support == 0 and invalid_endpoint == 0)
                    estimate = float(np.dot(weights, difference)) if defined else math.nan
                    se = math.sqrt(len(weights) / (len(weights) - 1) * float(np.square(weights * (difference - estimate)).sum())) if defined and len(weights) > 1 else math.nan
                    old_mean, old_se = _weighted_endpoint(weights, old_end[endpoint])
                    new_mean, new_se = _weighted_endpoint(weights, new_end[endpoint])
                    if not defined:
                        new_mean = new_se = math.nan
                    rows.append({**base, "endpoint": endpoint, "old_weighted": old_mean, "new_weighted": new_mean,
                                 "old_weighted_mc_se": old_se, "new_weighted_mc_se": new_se,
                                 "paired_difference": estimate, "paired_mc_se": se,
                                 "endpoint_nonfinite_positive_support_count": invalid_endpoint,
                                 "status": ("undefined_invalid_removal_positive_support" if invalid_support else
                                            "undefined_nonfinite_endpoint_positive_support" if invalid_endpoint else
                                            "defined" if defined else "undefined_zero_old_support")})
    return pd.DataFrame(rows)


def _load_new_raw(run_dir: Path, sources: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for row in sources.to_dict("records"):
        ordinal = int(row["source_ordinal"])
        path = Path(run_dir) / "raw" / f"{ordinal:04d}.csv.gz"
        require(path.exists(), f"missing amended source raw file: {path}")
        frame = _read(path)
        require(len(frame) > 0, f"amended source raw file is empty: {path}")
        if "source_id" not in frame:
            require("source_ordinal" in frame, f"amended raw file lacks source identity: {path}")
            frame.insert(0, "source_id", frame["source_ordinal"].map(
                dict(zip(sources.source_ordinal, sources.source_id, strict=True))))
        elif not frame.source_id.astype(str).eq(str(row["source_id"])).all():
            raise ValueError(f"amended raw source identity drift: {path}")
        frames.append(frame)
    result = pd.concat(frames, ignore_index=True)
    return result


def _rescored_rows(old_raw_by_source: dict[str, pd.DataFrame], new_raw_by_source: dict[str, pd.DataFrame],
                   old_sources: pd.DataFrame, new_sources: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    for source_id in sorted(new_raw_by_source):
        old = old_raw_by_source[str(source_id)]
        new = new_raw_by_source[str(source_id)]
        source_record = new_sources.loc[new_sources.source_id.astype(str).eq(str(source_id))].iloc[0]
        old_viable = bool(old_sources.loc[old_sources.source_id.astype(str).eq(str(source_id)), "original_viable"].iloc[0]) if "original_viable" in old_sources else bool(old_sources.loc[old_sources.source_id.astype(str).eq(str(source_id)), "viable"].iloc[0])
        new_viable = bool(new_sources.loc[new_sources.source_id.astype(str).eq(str(source_id)), "viable"].iloc[0])
        for q in Q_SCENARIOS:
            for law in OBSERVATION_MODELS:
                old_profile = _profile(old, old_viable, float(q), law)
                new_profile = _profile(new, new_viable, float(q), law)
                new_weights, _, new_stats = _weights(new, new_viable, float(q), law)
                survivor_ess, survivor_rse, survivor_largest = _survivor_stats(new_weights, new)
                row = {"source_id": source_id, "configuration": source_record.get("configuration", ""),
                       "restriction": source_record.get("restriction", ""), "q": q, "observation_model": law,
                       "original_viable": old_viable, "viable": new_viable,
                       "old_early_pattern_lower95": old_profile["early_pattern_lower95"],
                       "old_joint_lower95": old_profile["joint_lower95"],
                       "old_log_joint_mean": old_profile["log_joint_mean"],
                       "new_early_pattern_lower95": new_profile["early_pattern_lower95"],
                       "new_joint_lower95": new_profile["joint_lower95"],
                       "new_log_joint_mean": new_profile["log_joint_mean"],
                       "new_joint_mean": new_profile["joint_mean"],
                       "new_weight_ess": new_stats["weight_ess"], "new_weight_relative_se": new_stats["weight_relative_se"],
                       "new_largest_weight_share": new_stats["largest_weight_share"], "new_weight_qualified": new_stats["weight_qualified"],
                       "new_survivor_weight_ess": survivor_ess, "new_survivor_weight_relative_se": survivor_rse,
                       "new_survivor_largest_weight_share": survivor_largest}
                for endpoint, values in _endpoints(new).items():
                    estimate, se = _weighted_endpoint(new_weights, values)
                    row[f"new_weighted_{endpoint}"] = estimate
                    row[f"new_weighted_{endpoint}_mc_se"] = se
                rows.append(row)
                for early_cutoff in EARLY_CUTOFFS:
                    for joint_cutoff in JOINT_CUTOFFS:
                        transitions.append({"source_id": source_id, "configuration": source_record.get("configuration", ""),
                                            "restriction": source_record.get("restriction", ""), "q": q, "observation_model": law,
                                            "early_cutoff": early_cutoff, "joint_cutoff": joint_cutoff,
                                            "old_status": _status(old_profile, early_cutoff, joint_cutoff),
                                            "new_status": _status(new_profile, early_cutoff, joint_cutoff)})
    profiles = pd.DataFrame(rows)
    raw_transitions = pd.DataFrame(transitions)
    group = ["configuration", "restriction", "q", "observation_model", "early_cutoff", "joint_cutoff", "old_status", "new_status"]
    summary = raw_transitions.groupby(group, sort=True).size().rename("source_count").reset_index()
    summary["fixed_source_count"] = len(new_raw_by_source)
    return profiles, summary


def _diagnostics(new_raw: pd.DataFrame, annual: Mapping[str, Any] | None = None) -> dict[str, Any]:
    guard_columns = [c for c in new_raw if "mate_guard" in c.lower() or "guard_active" in c.lower()]
    presence_columns = [c for c in new_raw if c.startswith("annual_N_R_")]
    result: dict[str, Any] = {"guard_columns": guard_columns,
                               "annual_refuge_columns": presence_columns}
    if guard_columns:
        raw_values = pd.to_numeric(new_raw[guard_columns[0]], errors="coerce")
        result["raw_guard_any_history_count"] = int((raw_values.fillna(0) > 0).sum())
        result["raw_guard_any_history_available"] = True
    else:
        result["raw_guard_any_history_available"] = False
    if annual is not None and annual.get("guard_column"):
        result["guard_columns"] = [str(annual["guard_column"])]
        result["guard_activation_rows"] = int(annual["guard_activation_rows"])
        result["guard_activation_exact"] = True
        result["guard_activation_available"] = True
    elif guard_columns:
        result["guard_activation_rows"] = result["raw_guard_any_history_count"]
        result["guard_activation_exact"] = False
        result["guard_activation_available"] = True
    else:
        result["guard_activation_available"] = False
    if annual is not None and annual.get("refuge_count"):
        result["refuge_presence_fraction_by_year"] = {
            str(year): float(annual["refuge_positive"][year] / count)
            for year, count in sorted(annual["refuge_count"].items())
        }
        result["lake_only_endpoint_count"] = int(annual["lake_only_terminal_count"])
        result["annual_refuge_columns"] = ["N_R"]
        return result
    if presence_columns:
        refuge = np.column_stack([pd.to_numeric(new_raw[c], errors="coerce").to_numpy(float) for c in presence_columns])
        result["refuge_presence_fraction_by_year"] = {c.removeprefix("annual_N_R_"): float((refuge[:, i] > 0).mean()) for i, c in enumerate(presence_columns)}
        terminal = _column(new_raw, ENDPOINTS["N_total_2002"])
        refuge = _column(new_raw, ENDPOINTS["N_R_2002"])
        if terminal is not None and refuge is not None:
            result["lake_only_endpoint_count"] = int(((pd.to_numeric(new_raw[refuge], errors="coerce") <= 0)
                                                        & (pd.to_numeric(new_raw[terminal], errors="coerce") > 0)).sum())
        else:
            result["lake_only_endpoint_count"] = None
    else:
        result["refuge_presence_fraction_by_year"] = {}
        result["lake_only_endpoint_count"] = None
    return result


def _load_annual_diagnostics(run_dir: Path, sources: pd.DataFrame) -> dict[str, Any] | None:
    paths = [Path(run_dir) / "annual" / f"{int(row['source_ordinal']):04d}.csv.gz"
             for row in sources.to_dict("records")]
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    require(len(existing) == len(paths), "annual archive is incomplete")
    refuge_count: dict[int, int] = {}
    refuge_positive: dict[int, int] = {}
    lake_only_terminal_count = 0
    guard_activation_rows = 0
    guard_column: str | None = None
    stage_rows: list[dict[str, Any]] = []
    source_by_path = {Path(run_dir) / "annual" / f"{int(row['source_ordinal']):04d}.csv.gz": row
                      for row in sources.to_dict("records")}
    for path in existing:
        header = pd.read_csv(path, nrows=0).columns.tolist()
        stage_columns = ("J_L", "A_L", "J_R", "A_R", "pre_breeding_A_total")
        usecols = [name for name in ("year", "N_R", "N_total", *stage_columns, "mate_guard_active") if name in header]
        require({"year", "N_R", *stage_columns}.issubset(usecols), f"annual file lacks diagnostic stage columns: {path}")
        if "mate_guard_active" in usecols:
            guard_column = "mate_guard_active"
        for chunk in pd.read_csv(path, usecols=usecols, chunksize=100_000, float_precision="round_trip"):
            years = pd.to_numeric(chunk["year"], errors="raise").astype(int)
            refuge = pd.to_numeric(chunk["N_R"], errors="coerce")
            for year, values in refuge.groupby(years):
                count = int(values.notna().sum())
                refuge_count[int(year)] = refuge_count.get(int(year), 0) + count
                refuge_positive[int(year)] = refuge_positive.get(int(year), 0) + int((values > 0).sum())
            if "N_total" in chunk:
                total = pd.to_numeric(chunk["N_total"], errors="coerce")
                lake_only_terminal_count += int(((years == 2002) & (refuge <= 0) & (total > 0)).sum())
            if "mate_guard_active" in chunk:
                guard_activation_rows += int(pd.to_numeric(chunk["mate_guard_active"], errors="coerce").fillna(0).astype(bool).sum())
            grouped = chunk.assign(_year=years).groupby("_year", sort=True)
            for year, part in grouped:
                row: dict[str, Any] = {"source_ordinal": int(source_by_path[path]["source_ordinal"]),
                                       "source_id": source_by_path[path]["source_id"], "year": int(year),
                                       "history_count": int(len(part))}
                for column in ("J_L", "A_L", "J_R", "A_R"):
                    row[f"sum_{column}"] = float(pd.to_numeric(part[column], errors="coerce").sum())
                adult_total = pd.to_numeric(part["pre_breeding_A_total"], errors="coerce")
                row["pre_breeding_A_total_lt_2_count"] = int((adult_total < 2).sum())
                row["pre_breeding_A_total_eq_1_count"] = int(np.isclose(adult_total, 1.0, rtol=0.0, atol=1e-12).sum())
                row["mate_guard_active_count"] = int(pd.to_numeric(part.get("mate_guard_active", False), errors="coerce").fillna(0).astype(bool).sum()) if "mate_guard_active" in part else 0
                stage_rows.append(row)
    stage = pd.DataFrame(stage_rows)
    if not stage.empty:
        group = ["source_ordinal", "source_id", "year"]
        sums = [c for c in stage if c.startswith("sum_")]
        counts = [c for c in stage if c not in (*group, "history_count", *sums)]
        aggregate = stage.groupby(group, sort=True).agg({"history_count": "sum", **{c: "sum" for c in sums}, **{c: "sum" for c in counts}}).reset_index()
        for column in sums:
            aggregate[f"mean_{column.removeprefix('sum_')}"] = aggregate[column] / aggregate["history_count"]
            aggregate.drop(columns=column, inplace=True)
    else:
        aggregate = stage
    return {"guard_column": guard_column, "guard_activation_rows": guard_activation_rows,
            "refuge_count": refuge_count, "refuge_positive": refuge_positive,
            "lake_only_terminal_count": lake_only_terminal_count, "stage_table": aggregate}


def analyze(baseline_dir: Path, run_dir: Path, output_dir: Path) -> dict[str, Any]:
    baseline_dir, run_dir, output_dir = map(Path, (baseline_dir, run_dir, output_dir))
    old_manifest = _manifest(baseline_dir, ("sources.csv", "raw_histories.csv.gz", "parameter_values.csv.gz"))
    new_manifest = _manifest(run_dir, ("sources.csv", "parameter_values.csv.gz"))
    require(new_manifest.get("scope") in (None, "common_model_mate_guard"), "amended archive has wrong scope")
    old_sources = _source_ordinal_sources(_read(baseline_dir / "sources.csv"))
    new_sources = _source_ordinal_sources(_read(run_dir / "sources.csv"))
    _compare_sources(old_sources, new_sources)
    selected_ids = set(new_sources.source_id.astype(str))
    require(_parameter_fingerprint(baseline_dir, selected_ids) == _parameter_fingerprint(run_dir, selected_ids),
            "parameter values differ between archives")
    old_raw = _read(baseline_dir / "raw_histories.csv.gz")
    new_raw = _load_new_raw(run_dir, new_sources)
    old_raw = old_raw.loc[old_raw.source_id.astype(str).isin(selected_ids)].copy()
    mode = str(new_manifest.get("mode", "production"))
    if mode == "qualification":
        requested = new_raw[["source_id", "replicate_index"]].drop_duplicates()
        old_raw = old_raw.merge(requested, on=["source_id", "replicate_index"], how="inner", validate="one_to_one")
    elif mode == "production":
        require(len(new_sources) == 517, "production mate-guard run must contain 517 fixed sources")
        require(new_raw.groupby("source_id").size().eq(1024).all(),
                "production mate-guard run must contain 1,024 histories per source")
    else:
        raise ValueError(f"unknown mate-guard run mode: {mode}")
    new_annual = _load_annual_diagnostics(run_dir, new_sources)
    if new_manifest.get("source_count") is not None:
        require(int(new_manifest["source_count"]) == len(new_sources), "amended source count disagrees with manifest")
    if new_manifest.get("history_count") is not None:
        require(int(new_manifest["history_count"]) == len(new_raw), "amended history count disagrees with manifest")
    old_sources = old_sources.loc[old_sources.source_id.astype(str).isin(selected_ids)].copy()
    # Ensure all rows retain their source identity and new raw failures remain
    # in the archive even when their amended source weight is zero.
    require(set(old_raw.source_id.astype(str)) == set(old_sources.source_id.astype(str)), "baseline raw source coverage differs")
    require(set(new_raw.source_id.astype(str)) == set(new_sources.source_id.astype(str)), "amended raw source coverage differs")
    joined, keys = _pair_histories(old_raw, new_raw)
    paired = _paired_rows(joined, old_sources, new_sources)
    old_by = {str(k): v for k, v in old_raw.groupby("source_id", sort=False)}
    new_by = {str(k): v for k, v in new_raw.groupby("source_id", sort=False)}
    rescored, transitions = _rescored_rows(old_by, new_by, old_sources, new_sources)
    output_dir.mkdir(parents=True, exist_ok=True)
    annual_stage = (new_annual.get("stage_table") if new_annual is not None else None)
    if annual_stage is None:
        annual_stage = pd.DataFrame(columns=["source_ordinal", "source_id", "year", "history_count",
                                             "mean_J_L", "mean_A_L", "mean_J_R", "mean_A_R",
                                             "pre_breeding_A_total_lt_2_count", "pre_breeding_A_total_eq_1_count",
                                             "mate_guard_active_count"])
    paired.to_csv(output_dir / "paired_profiles.csv", index=False, float_format="%.17g")
    rescored.to_csv(output_dir / "rescored_profiles.csv", index=False, float_format="%.17g")
    transitions.to_csv(output_dir / "compatibility_transition_summary.csv", index=False, float_format="%.17g")
    annual_stage.to_csv(output_dir / "annual_stage_diagnostics.csv", index=False, float_format="%.17g")
    readout = {"status": "complete", "mode": mode, "baseline_manifest": _hash(baseline_dir / "run_manifest.json"),
               "amended_manifest": _hash(run_dir / "run_manifest.json"), "pair_keys": keys,
               "baseline_history_count": len(old_raw), "amended_history_count": len(new_raw),
               "source_count": len(new_sources), "q_scenarios": list(Q_SCENARIOS),
               "observation_models": list(OBSERVATION_MODELS), "paired_row_count": len(paired),
               "rescored_profile_count": len(rescored), "transition_row_count": len(transitions),
               "annual_stage_diagnostic_row_count": len(annual_stage),
               "diagnostics": _diagnostics(new_raw, new_annual),
               "interpretation_boundary": "Fixed selected sources only; paired contrasts are undefined when amended invalid removals have positive old support; no q ranking or global mechanism claim."}
    (output_dir / "readout_summary.json").write_text(json.dumps(readout, indent=2) + "\n", encoding="utf-8")
    receipt = {"status": "complete", "mode": mode, "inputs": {"baseline": str((baseline_dir / "run_manifest.json").resolve()),
                                                  "amended": str((run_dir / "run_manifest.json").resolve())},
               "input_hashes": {"baseline_manifest": readout["baseline_manifest"],
                                "amended_manifest": readout["amended_manifest"]}, "outputs": {name: _hash(output_dir / name)
                  for name in ("paired_profiles.csv", "rescored_profiles.csv", "compatibility_transition_summary.csv", "annual_stage_diagnostics.csv", "readout_summary.json")}}
    (output_dir / "mate_guard_analysis_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return readout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.baseline_dir, args.run_dir, args.output_dir)


if __name__ == "__main__":
    main()
