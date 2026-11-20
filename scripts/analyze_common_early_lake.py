#!/usr/bin/env python3
"""Describe paired early-lake endpoints from the frozen common-model archives.

This is an existing-artifact analysis.  It never simulates, reweights an
altered history, or selects a source on its counterfactual result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from galaxias_model.abundance_detection import (  # noqa: E402
    COMMON_EPISODE_FIELDS,
    OBSERVATION_MODELS,
    common_history_log_likelihood,
)
from scripts.run_common_model_comparison import file_hash, require, verify_archive  # noqa: E402


IDENTITY = ["search_seed", "configuration", "restriction", "wave", "source_index"]
PAIR_KEYS = [*IDENTITY, "source_id", "replicate_index", "simulation_seed", "environment_seed"]
Q_VALUES = (0.005, 0.02, 0.05, 0.2)
PRIMARY_MODELS = ("homogeneous", "shared_quality")
REPLICATES = 1024
Z = 1.96
PERMISSIVE_EARLY = 0.5
PERMISSIVE_JOINT = 1e-6

# The two 1980/1983 fields are recorded lake states.  The negative lake survey
# fields are proxy observations in 1988/1989, hence actual state years 1987/88.
ENDPOINTS = {
    "lake_N_L_1980": "endpoint_ct005_N_L_1980",
    "lake_N_L_1983": "endpoint_ct005_N_L_1983",
    "lake_N_L_1987": "neg_N_L_1988",
    "lake_N_L_1988": "neg_N_L_1989",
    "minimum_N_total_1972_2002": "endpoint_minimum_N_total_1972_2002",
}


def _hash(path: Path) -> dict[str, Any]:
    return file_hash(Path(path))


def _load_restricted(path: Path, columns: list[str], *, restriction: str = "R_J",
                     chunksize: int = 50_000) -> pd.DataFrame:
    """Read only the columns needed here and retain the requested restriction."""
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, usecols=columns, chunksize=chunksize,
                             float_precision="round_trip"):
        if "restriction" in chunk.columns:
            chunk = chunk.loc[chunk["restriction"].eq(restriction)]
        chunks.append(chunk)
    if not chunks:
        return pd.DataFrame(columns=columns)
    return pd.concat(chunks, ignore_index=True)


def _verify_profile_file(profile_path: Path, analysis_receipt: Path,
                         validate_manifest: dict[str, Any],
                         counterfactual_manifest: dict[str, Any]) -> dict[str, Any]:
    require(analysis_receipt.exists(), f"missing analysis receipt: {analysis_receipt}")
    receipt = json.loads(analysis_receipt.read_text(encoding="utf-8"))
    expected = receipt.get("outputs", {}).get("validated_source_profiles.csv")
    require(expected is not None, "analysis receipt lacks validated profiles hash")
    require(_hash(profile_path) == expected, "validated_source_profiles hash drift")
    require(receipt.get("validation_manifest") == _hash(Path(validate_manifest["_manifest_path"])),
            "analysis receipt validation-manifest binding drift")
    require(receipt.get("counterfactual_manifest") == _hash(Path(counterfactual_manifest["_manifest_path"])),
            "analysis receipt counterfactual-manifest binding drift")
    return receipt


def _verify_archive_with_path(directory: Path, phase: str) -> dict[str, Any]:
    manifest = verify_archive(directory, phase=phase)
    manifest = dict(manifest)
    manifest["_manifest_path"] = str(directory / "run_manifest.json")
    return manifest


def _profile_slice(profile_path: Path, analysis_receipt: Path,
                   validate_manifest: dict[str, Any],
                   counterfactual_manifest: dict[str, Any]) -> pd.DataFrame:
    _verify_profile_file(profile_path, analysis_receipt, validate_manifest, counterfactual_manifest)
    columns = [*IDENTITY, "source_id", "restriction", "q", "observation_model",
               "early_pattern_lower95", "joint_lower95", "joint_mc_qualified",
               "joint_weight_ess", "joint_mc_relative_se", "joint_largest_weight_share"]
    profiles = pd.read_csv(profile_path, usecols=columns, float_precision="round_trip")
    profiles = profiles.loc[
        profiles.restriction.eq("R_J") & profiles.observation_model.isin(PRIMARY_MODELS)
    ].copy()
    require(profiles.source_id.nunique() == 254, "validated profiles do not cover 254 R_J sources")
    require(len(profiles) == 254 * len(Q_VALUES) * len(PRIMARY_MODELS),
            "validated profiles do not have all q/law rows for R_J sources")
    require(not profiles.duplicated([*IDENTITY, "source_id", "q", "observation_model"]).any(),
            "validated profile keys duplicate")
    profiles["permissive_bounds"] = (
        profiles["early_pattern_lower95"].ge(PERMISSIVE_EARLY)
        & profiles["joint_lower95"].ge(PERMISSIVE_JOINT)
    )
    profiles["factual_compatible"] = profiles["permissive_bounds"] & profiles["joint_mc_qualified"].astype(bool)
    return profiles


def _weight_vector(part: pd.DataFrame, q: float, model: str) -> tuple[np.ndarray, np.ndarray]:
    features = part[[f"{field}_factual" for field in COMMON_EPISODE_FIELDS]].copy()
    features.columns = COMMON_EPISODE_FIELDS
    eligible = (
        part["early_early_patterns_pass_factual"].astype(bool).to_numpy()
        & part["removals_valid_factual"].astype(bool).to_numpy()
    )
    logs = common_history_log_likelihood(features, float(q), model)
    logs = np.where(eligible, logs, -math.inf)
    support = np.isfinite(logs)
    weights = np.zeros(len(logs), dtype=float)
    if support.any():
        maximum = float(logs[support].max())
        scaled = np.exp(logs[support] - maximum)
        weights[support] = scaled / scaled.sum()
    return weights, support


def _weight_stats(weights: np.ndarray) -> tuple[float, float, float, bool]:
    if weights.sum() <= 0:
        return 0.0, math.nan, math.nan, False
    n = len(weights)
    ess = float(1.0 / np.square(weights).sum())
    rse = math.sqrt(max(0.0, (n / ess - 1.0) / (n - 1))) if n > 1 else math.nan
    largest = float(weights.max())
    return ess, rse, largest, bool(ess >= 100.0 and rse <= 0.1 and largest <= 0.05)


def _contrast_row(base: dict[str, Any], endpoint: str, factual: np.ndarray,
                  altered: np.ndarray, feasible: np.ndarray, weights: np.ndarray,
                  support: np.ndarray, ess: float, rse: float, largest: float,
                  weight_qualified: bool) -> dict[str, Any]:
    invalid_removal = ~feasible
    invalid_removal_count = int((invalid_removal & support).sum())
    invalid_removal_mass = float(weights[invalid_removal].sum())
    positive_support = bool(weights.sum() > 0)
    finite_endpoints = np.isfinite(factual) & np.isfinite(altered)
    endpoint_invalid_count = int((~finite_endpoints & support).sum())
    endpoint_invalid_mass = float(weights[~finite_endpoints].sum())
    factual_mean = float(np.dot(weights, factual)) if positive_support and np.isfinite(factual).all() else math.nan

    if not positive_support:
        status = "undefined_zero_factual_support"
        counterfactual_mean = estimate = se = ci_low = ci_high = math.nan
    elif invalid_removal_count:
        status = "undefined_invalid_removal_positive_support"
        counterfactual_mean = estimate = se = ci_low = ci_high = math.nan
    elif endpoint_invalid_count:
        status = "undefined_nonfinite_endpoint_positive_support"
        counterfactual_mean = estimate = se = ci_low = ci_high = math.nan
    else:
        difference = altered - factual
        counterfactual_mean = float(np.dot(weights, altered))
        estimate = float(np.dot(weights, difference))
        n = len(weights)
        se = math.sqrt(n / (n - 1) * float(np.square(weights * (difference - estimate)).sum())) if n > 1 else math.nan
        ci_low, ci_high = estimate - Z * se, estimate + Z * se
        status = "defined_qualified" if weight_qualified else "defined_unqualified_precision"

    return {
        **base,
        "endpoint": endpoint,
        "factual_mean": factual_mean,
        "counterfactual_mean": counterfactual_mean,
        "estimate_cf_minus_factual": estimate,
        "paired_mc_se": se,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "factual_weight_ess": ess,
        "factual_weight_relative_se": rse,
        "factual_largest_weight_share": largest,
        "factual_weight_qualified": weight_qualified,
        "positive_factual_support_count": int(support.sum()),
        "invalid_removal_positive_support_count": invalid_removal_count,
        "invalid_removal_factual_weight_mass": invalid_removal_mass,
        "endpoint_nonfinite_positive_support_count": endpoint_invalid_count,
        "endpoint_nonfinite_factual_weight_mass": endpoint_invalid_mass,
        "contrast_status": status,
        "zero_effect_tol_1e-12": bool(np.isfinite(estimate) and np.isclose(estimate, 0.0, atol=1e-12, rtol=0.0)),
    }


def _summarise(contrasts: pd.DataFrame) -> pd.DataFrame:
    group = ["configuration", "q", "observation_model", "endpoint"]
    rows: list[dict[str, Any]] = []
    for key, part in contrasts.loc[contrasts.factual_compatible.astype(bool)].groupby(group, sort=True):
        defined = part.loc[part.estimate_cf_minus_factual.notna()]
        qualified = defined.loc[defined.factual_weight_qualified.astype(bool)]
        estimates = defined.estimate_cf_minus_factual
        rows.append({
            **dict(zip(group, key, strict=True)),
            "total_profile_count": int(len(part)),
            "defined_estimate_count": int(len(defined)),
            "qualified_defined_estimate_count": int(len(qualified)),
            "estimate_min": float(estimates.min()) if len(estimates) else math.nan,
            "estimate_max": float(estimates.max()) if len(estimates) else math.nan,
            "ci95_above_zero_count": int((defined.ci95_low > 0).sum()),
            "ci95_below_zero_count": int((defined.ci95_high < 0).sum()),
            "ci95_contains_zero_count": int(((defined.ci95_low <= 0) & (defined.ci95_high >= 0)).sum()),
            "zero_effect_count": int(defined["zero_effect_tol_1e-12"].sum()),
            "invalid_removal_profile_count": int((part.invalid_removal_positive_support_count > 0).sum()),
            "zero_factual_support_profile_count": int((part.contrast_status == "undefined_zero_factual_support").sum()),
        })
    return pd.DataFrame(rows)


def _check_results(contrasts: pd.DataFrame, joined: pd.DataFrame) -> dict[str, Any]:
    """One data-backed check each for formula, invalidity, and zero effect."""
    checks: dict[str, Any] = {}
    resolved = contrasts.loc[contrasts.contrast_status.str.startswith("defined_")]
    require(len(resolved) > 0, "no defined contrast available for formula check")
    row = resolved.iloc[0]
    keymask = np.ones(len(joined), dtype=bool)
    for key in [*IDENTITY, "source_id"]:
        keymask &= joined[key].eq(row[key]).to_numpy()
    keymask &= joined.replicate_index.notna().to_numpy()
    part = joined.loc[keymask]
    weights, support = _weight_vector(part, float(row.q), str(row.observation_model))
    endpoint_col = ENDPOINTS[str(row.endpoint)]
    d = part[f"{endpoint_col}_counterfactual"].to_numpy(float) - part[f"{endpoint_col}_factual"].to_numpy(float)
    estimate = float(np.dot(weights, d))
    se = math.sqrt(len(weights) / (len(weights) - 1) * float(np.square(weights * (d - estimate)).sum()))
    require(math.isclose(estimate, float(row.estimate_cf_minus_factual), rel_tol=0, abs_tol=1e-12),
            "paired estimate formula check failed")
    require(math.isclose(se, float(row.paired_mc_se), rel_tol=0, abs_tol=1e-12),
            "paired MC SE formula check failed")
    checks["paired_formula"] = {"status": "passed", "profile": str(row.source_id), "endpoint": str(row.endpoint)}

    invalid = contrasts.loc[contrasts.invalid_removal_positive_support_count > 0]
    if len(invalid):
        item = invalid.iloc[0]
        require(pd.isna(item.estimate_cf_minus_factual), "invalid-removal contrast was renormalised")
        checks["invalidity"] = {"status": "passed", "profile": str(item.source_id),
                                 "positive_support_count": int(item.invalid_removal_positive_support_count)}
    else:
        checks["invalidity"] = {"status": "no_positive_support_invalid_removal_observed"}

    zero = contrasts.loc[contrasts["zero_effect_tol_1e-12"].astype(bool)]
    if len(zero):
        item = zero.iloc[0]
        require(abs(float(item.estimate_cf_minus_factual)) <= 1e-12, "zero-effect check failed")
        checks["zero_effect"] = {"status": "passed", "profile": str(item.source_id), "endpoint": str(item.endpoint)}
    else:
        checks["zero_effect"] = {"status": "no_zero_effect_row_observed"}
    return checks


def _write_findings(output_dir: Path, contrasts: pd.DataFrame, summary: pd.DataFrame,
                    checks: dict[str, Any], pairing: dict[str, Any]) -> None:
    compatible = contrasts.loc[contrasts.factual_compatible.astype(bool)]
    defined = compatible.loc[compatible.estimate_cf_minus_factual.notna()]
    qualified = defined.loc[defined.factual_weight_qualified.astype(bool)]
    lines = [
        "# Early-lake overshoot readout",
        "",
        "This note describes paired frozen validation/counterfactual histories. It does not add histories, replay annual trajectories, or treat source extrema as model rankings.",
        "",
        f"The archive contains {pairing['source_count']} R_J sources and {pairing['replicates_per_source']} paired streams per source. The permissive factual-compatible slice contains {compatible[['source_id', 'q', 'observation_model']].drop_duplicates().shape[0]} source/profile rows; {len(defined)} of its five-endpoint rows are defined and {len(qualified)} meet the factual ESS/RSE/largest-weight criteria.",
        "",
        "Counterfactual weights are the fixed factual 14-record joint weights, multiplied by the factual early-pattern and removal eligibility flags. No counterfactual likelihood or source reselection is used. An altered invalid-removal history with positive factual support leaves the contrast undefined without renormalisation, including when its total weight is numerically tiny.",
        "",
        "The 1988/1989 negative lake fields are labelled actual state years 1987/1988 because they are observation proxies for the preceding state. The whole-period minimum endpoint cannot locate an early effect, and the archive does not supply a complete annual lake trajectory.",
        "",
        "Across profile rows, confidence intervals and paired Monte Carlo errors are descriptive. A small or sign-uncertain effect is insufficient to infer a direction; these summaries do not average across parameter sources as a population estimand.",
        "",
        f"Checks: {', '.join(f'{name}={value.get("status")}' for name, value in checks.items())}.",
    ]
    if len(defined):
        lines.extend(["", "Defined compatible estimate ranges by endpoint:"])
        for endpoint, part in defined.groupby("endpoint", sort=True):
            lines.append(f"- {endpoint}: {part.estimate_cf_minus_factual.min():.6g} to {part.estimate_cf_minus_factual.max():.6g}; CI above zero {int((part.ci95_low > 0).sum())}, below zero {int((part.ci95_high < 0).sum())}, zero {int(part['zero_effect_tol_1e-12'].sum())}.")
    (output_dir / "early_lake_findings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze(validate_dir: Path, counterfactual_dir: Path, profile_path: Path,
            analysis_receipt: Path, output_dir: Path, chunksize: int = 50_000) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    validate_manifest = _verify_archive_with_path(validate_dir, "validate")
    counterfactual_manifest = _verify_archive_with_path(counterfactual_dir, "counterfactual")
    validate_raw = validate_dir / "raw_histories.csv.gz"
    counterfactual_raw = counterfactual_dir / "counterfactual_histories.csv.gz"
    require(validate_manifest["outputs"]["raw_histories.csv.gz"] == _hash(validate_raw), "factual raw hash drift")
    require(counterfactual_manifest["outputs"]["counterfactual_histories.csv.gz"] == _hash(counterfactual_raw), "counterfactual raw hash drift")

    factual_columns = [*PAIR_KEYS, "phase", *COMMON_EPISODE_FIELDS,
                       "early_early_patterns_pass", "removals_valid", *ENDPOINTS.values()]
    counterfactual_columns = [*PAIR_KEYS, "phase", "removals_valid", *ENDPOINTS.values()]
    factual = _load_restricted(validate_raw, factual_columns, chunksize=chunksize).rename(
        columns={column: f"{column}_factual" for column in [*COMMON_EPISODE_FIELDS,
                                                             "early_early_patterns_pass", "removals_valid", *ENDPOINTS.values()]}
    )
    altered = _load_restricted(counterfactual_raw, counterfactual_columns, chunksize=chunksize).rename(
        columns={column: f"{column}_counterfactual" for column in [*ENDPOINTS.values(), "removals_valid"]}
    )
    require(len(factual) == 254 * REPLICATES and len(altered) == 254 * REPLICATES,
            "R_J raw archive does not contain 254 x 1024 histories")
    require(not factual.duplicated(PAIR_KEYS).any() and not altered.duplicated(PAIR_KEYS).any(),
            "paired raw keys duplicate")
    factual_sources = set(factual.source_id)
    altered_sources = set(altered.source_id)
    require(factual_sources == altered_sources and len(factual_sources) == 254,
            "factual/counterfactual source coverage differs")
    joined = factual.merge(altered, on=PAIR_KEYS, how="inner", suffixes=("_factual", "_counterfactual"),
                           validate="one_to_one")
    require(len(joined) == len(factual) == len(altered), "paired key coverage differs")
    require(joined.phase_factual.eq("validate").all() and joined.phase_counterfactual.eq("counterfactual").all(),
            "unexpected archive phase in paired histories")
    # The seeds are part of PAIR_KEYS; this explicit check makes the intended
    # same-stream pairing auditable rather than relying only on merge success.
    for seed in ("simulation_seed", "environment_seed"):
        require(joined[f"{seed}"].notna().all(), f"missing {seed} in paired histories")
    require(factual.groupby("source_id").size().eq(REPLICATES).all(), "factual source replicate coverage drift")
    require(altered.groupby("source_id").size().eq(REPLICATES).all(), "counterfactual source replicate coverage drift")
    factual_seed_values = set(pd.concat([factual.simulation_seed, factual.environment_seed]))
    altered_seed_values = set(pd.concat([altered.simulation_seed, altered.environment_seed]))
    require(len(factual_seed_values) == 2 * len(factual), "factual seed collision")
    require(len(altered_seed_values) == 2 * len(altered), "counterfactual seed collision")
    require(factual_seed_values == altered_seed_values, "factual/counterfactual seed domains differ")
    source_seed_count = len(factual_seed_values)

    profiles = _profile_slice(profile_path, analysis_receipt, validate_manifest, counterfactual_manifest)
    source_profile = profiles[[*IDENTITY, "source_id", "q", "observation_model", "permissive_bounds",
                               "factual_compatible",
                               "early_pattern_lower95", "joint_lower95", "joint_mc_qualified"]]
    require(set(source_profile.source_id) == factual_sources, "profiles/raw source coverage differs")
    rows: list[dict[str, Any]] = []
    for source_id, part in joined.groupby("source_id", sort=True):
        for q in Q_VALUES:
            for model in PRIMARY_MODELS:
                profile_key = source_profile.loc[
                    source_profile.source_id.eq(source_id)
                    & np.isclose(source_profile.q, q)
                    & source_profile.observation_model.eq(model)
                ]
                require(len(profile_key) == 1, "missing unique validated profile row")
                prow = profile_key.iloc[0].to_dict()
                weights, support = _weight_vector(part, q, model)
                ess, rse, largest, weight_qualified = _weight_stats(weights)
                feasible = part["removals_valid_counterfactual"].astype(bool).to_numpy()
                base = {key: prow[key] for key in [*IDENTITY, "source_id", "q", "observation_model",
                                                    "permissive_bounds", "factual_compatible", "early_pattern_lower95", "joint_lower95",
                                                    "joint_mc_qualified"]}
                base.update({"replicate_count": len(part), "factual_weight_ess": ess,
                             "factual_weight_relative_se": rse, "factual_largest_weight_share": largest,
                             "factual_weight_qualified": weight_qualified})
                for endpoint, raw_column in ENDPOINTS.items():
                    rows.append(_contrast_row(base, endpoint,
                                              part[f"{raw_column}_factual"].to_numpy(float),
                                              part[f"{raw_column}_counterfactual"].to_numpy(float),
                                              feasible, weights, support, ess, rse, largest, weight_qualified))
    contrasts = pd.DataFrame(rows)
    require(len(contrasts) == 254 * len(Q_VALUES) * len(PRIMARY_MODELS) * len(ENDPOINTS),
            "contrast row count drift")
    summary = _summarise(contrasts)
    checks = _check_results(contrasts, joined)

    profile_metrics = contrasts.drop_duplicates([*IDENTITY, "source_id", "q", "observation_model"]).copy()
    profile_metrics = profile_metrics[[*IDENTITY, "source_id", "q", "observation_model", "permissive_bounds",
                                       "factual_compatible",
                                       "early_pattern_lower95", "joint_lower95", "joint_mc_qualified",
                                       "replicate_count", "factual_weight_ess", "factual_weight_relative_se",
                                       "factual_largest_weight_share", "factual_weight_qualified",
                                       "positive_factual_support_count", "invalid_removal_positive_support_count",
                                       "invalid_removal_factual_weight_mass"]]
    contrasts.to_csv(output_dir / "early_lake_contrasts.csv", index=False, float_format="%.17g")
    profile_metrics.to_csv(output_dir / "early_lake_profile_weights.csv", index=False, float_format="%.17g")
    summary.to_csv(output_dir / "early_lake_contrast_summary.csv", index=False, float_format="%.17g")
    pairing = {
        "status": "passed", "source_count": len(factual_sources), "replicates_per_source": REPLICATES,
        "factual_rows": len(factual), "counterfactual_rows": len(altered), "paired_rows": len(joined),
        "factual_seed_unique_count": int(source_seed_count), "counterfactual_seed_unique_count": int(len(altered_seed_values)),
        "seed_columns": ["simulation_seed", "environment_seed"],
        "pair_keys": PAIR_KEYS, "new_histories": 0,
    }
    (output_dir / "early_lake_pairing_checks.json").write_text(json.dumps(pairing, indent=2) + "\n", encoding="utf-8")
    _write_findings(output_dir, contrasts, summary, checks, pairing)

    inputs = {
        "validate_manifest": _hash(validate_dir / "run_manifest.json"),
        "counterfactual_manifest": _hash(counterfactual_dir / "run_manifest.json"),
        "factual_raw_histories": _hash(validate_raw),
        "counterfactual_raw_histories": _hash(counterfactual_raw),
        "validated_source_profiles": _hash(profile_path),
        "analysis_receipt": _hash(analysis_receipt),
    }
    receipt = {
        "status": "complete", "scope": "descriptive paired early-lake overshoot endpoints",
        "analysis_script": _hash(Path(__file__)), "inputs": inputs, "new_histories": 0,
        "weighting": "fixed factual 14-record joint weights times factual early_patterns_pass and removals_valid; no counterfactual likelihood or reselection",
        "compatibility_slice": "R_J profiles joined from hash-verified validated_source_profiles; early lower95 >= 0.5, joint lower95 >= 1e-6, and existing joint_mc_qualified",
        "outputs": {}, "checks": checks,
    }
    receipt["outputs"] = {path.name: _hash(path) for path in sorted(output_dir.iterdir())
                          if path.is_file() and path.name != "early_lake_receipt.json"}
    (output_dir / "early_lake_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-dir", type=Path,
                        default=ROOT / "outputs/remote/common_model_20260918/production/validate")
    parser.add_argument("--counterfactual-dir", type=Path,
                        default=ROOT / "outputs/remote/common_model_20260918/production/counterfactual")
    parser.add_argument("--profile-path", type=Path,
                        default=ROOT / "outputs/remote/common_model_20260918/production/analysis/validated_source_profiles.csv")
    parser.add_argument("--analysis-receipt", type=Path,
                        default=ROOT / "outputs/remote/common_model_20260918/production/analysis/analysis_receipt.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/common_model/early_lake_20260920")
    parser.add_argument("--chunksize", type=int, default=50_000)
    args = parser.parse_args()
    analyze(args.validate_dir, args.counterfactual_dir, args.profile_path,
            args.analysis_receipt, args.output_dir, chunksize=args.chunksize)


if __name__ == "__main__":
    main()
