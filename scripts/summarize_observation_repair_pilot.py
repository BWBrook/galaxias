#!/usr/bin/env python3
"""Verify and summarise a completed pilot without simulation or reselection.

Parameter sources retain equal weight. Within-source history weights condition
on the experimental observation assumptions, not posterior parameter weights.
"""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ["search_seed", "family_id", "proposal_id"]
PROFILE_KEY = [*IDENTITY, "profile"]
ORDER = ["overall_distance", "historical_distance", "intrinsic_distance", "historical_iqr", "proposal_id"]
TARGETS = [f"CT{i:03d}" for i in range(1, 13)]
PHYSICS = ["surviving_2002", "n_total_1995", "n_total_2002", "n_total_1992_1996_mean",
           "lake_nondetection_occupied_episodes", "natural_nondetection_occupied_episodes"]
RAW_NAMES = ["parameter_values.csv.gz", "deterministic_projections.csv.gz", "stage_a_selection.csv",
             "stage_b_replicates.csv.gz", "stage_b_source_summary.csv", "validation_replicates.csv.gz",
             "validation_source_summary.csv"]
PROFILES = {"baseline_current": 0., "repair_presence_only": 0., "repair_detection_060": .6, "repair_detection_098": .98}
LATE_METRICS = ["positive_compatible_fraction", "conditional_nondetection_compatibility", "late_discrepancy",
                "positive_discrepancy", "conditional_nondetection_discrepancy", "mean_joint_compatibility",
                "weight_ess", "largest_weight_share", "mc_relative_se"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def binding(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def identities(table, columns=IDENTITY):
    return set(table[columns].itertuples(index=False, name=None))


def close(actual, expected, label):
    require(np.allclose(actual, expected, rtol=1e-9, atol=1e-10, equal_nan=True), f"Stored summary mismatch: {label}")


def conditioned_physics(group, p):
    """Stable independent recomputation of I(positive)*(1-p)^K, with no floor."""
    positive = group.positive_records_compatible
    k = group.nondetection_occupied_episodes.to_numpy(dtype=float)
    require(positive.isin([True, False]).all(), "Non-Boolean positive compatibility")
    require(np.isfinite(k).all() and ((k >= 0) & (k <= 7) & (k == np.floor(k))).all(), "Invalid occupied-episode counts")
    supported = positive.to_numpy(dtype=bool)
    n, count = len(group), int(supported.sum())
    result = {"positive_compatible_count": count, "positive_compatible_fraction": count / n, "sample_supported": count > 0}
    if count == 0:
        return {**result, "late_discrepancy": math.inf, "positive_discrepancy": math.inf,
                "conditional_nondetection_discrepancy": math.nan, "mean_joint_compatibility": 0.,
                "conditional_nondetection_compatibility": math.nan, "weight_ess": 0.,
                "largest_weight_share": math.nan, "mc_relative_se": math.nan,
                **{f"compatibility_weighted_{field}": math.nan for field in PHYSICS}}
    log_weights = k[supported] * math.log1p(-p)
    max_log = float(log_weights.max())
    scaled = np.exp(log_weights - max_log)
    normalised = scaled / scaled.sum()
    log_mean = max_log + math.log(float(scaled.sum())) - math.log(n)
    ess = float(scaled.sum())**2 / float(np.dot(scaled, scaled))
    all_scaled = np.zeros(n)
    all_scaled[supported] = scaled
    relative_se = float(all_scaled.std(ddof=1) / math.sqrt(n) / all_scaled.mean()) if n > 1 else math.nan
    return {**result, "late_discrepancy": -log_mean, "positive_discrepancy": -math.log(count / n),
            "conditional_nondetection_discrepancy": -log_mean + math.log(count / n),
            "mean_joint_compatibility": math.exp(log_mean),
            "conditional_nondetection_compatibility": math.exp(log_mean) / (count / n),
            "weight_ess": ess, "largest_weight_share": float(normalised.max()),
            "mc_relative_se": relative_se,
            **{f"compatibility_weighted_{field}": float(np.dot(normalised, group.loc[supported, field].to_numpy(dtype=float))) for field in PHYSICS}}


def verify_and_augment(raw, summary, phase):
    require(not raw.duplicated([*IDENTITY, "replicate_index"]).any(), f"Duplicate {phase} replicate grain")
    require(not summary.duplicated(PROFILE_KEY).any(), f"Duplicate {phase} source/profile grain")
    require(identities(raw) == identities(summary), f"{phase} source coverage mismatch")
    require(raw.stage.eq(phase).all() and summary.stage.eq(phase).all(), f"{phase} stage mismatch")
    require(summary.groupby(IDENTITY).profile.apply(lambda x: set(x) == set(PROFILES)).all(), f"{phase} profile coverage mismatch")
    native = [c for c in raw if c not in {*IDENTITY, "stage", "replicate_index", "simulation_seed"} and not c.startswith("CT")]
    lookup = summary.set_index(PROFILE_KEY)
    rows = []
    for identity, group in raw.groupby(IDENTITY, sort=True):
        require(np.isfinite(group[native].to_numpy(dtype=float)).all(), f"Nonfinite {phase} physical features")
        require(group.lake_nondetection_occupied_episodes.between(0, 2).all() and group.natural_nondetection_occupied_episodes.between(0, 5).all(), "Domain-specific episode bounds")
        close(group.nondetection_occupied_episodes, group.lake_nondetection_occupied_episodes + group.natural_nondetection_occupied_episodes, "occupied episode sum")
        intrinsic = group[[f"{t}_weighted_penalty" for t in TARGETS[10:]]].sum(axis=1)
        close(intrinsic, np.repeat(intrinsic.iloc[0], len(group)), "unchanged deterministic intrinsic scores")
        early = group[[f"{t}_weighted_penalty" for t in TARGETS[:5]]].sum(axis=1)
        historical = group[[f"{t}_weighted_penalty" for t in TARGETS[:10]]].sum(axis=1)
        for profile, p in PROFILES.items():
            row = lookup.loc[(*identity, profile)].to_dict()
            require(row["replicate_count"] == len(group), f"{phase} source replicate count mismatch")
            close(row["diagnostic_detection_probability"], p, "profile detection assumption")
            derived = conditioned_physics(group, p)
            for field, value in derived.items():
                if not field.startswith("compatibility_weighted_"):
                    close(row[field], value, f"{profile}/{field}")
            for field in native:
                for stat in ["mean", "median"]:
                    close(row[f"{field}_{stat}"], group[field].agg(stat), f"{field}/{stat}")
            if profile == "baseline_current":
                hist, overall = float(historical.median()), float((historical + intrinsic).median())
                hist_iqr = float(historical.quantile(.75) - historical.quantile(.25))
            else:
                hist = float(early.median()) + 5 * derived["late_discrepancy"]
                overall = float((early + intrinsic).median()) + 5 * derived["late_discrepancy"]
                hist_iqr = float(early.quantile(.75) - early.quantile(.25))
            require(bool(row["finite_supported"]) == math.isfinite(overall), "Finite-support eligibility mismatch")
            for field, value in [("overall_distance", overall), ("historical_distance", hist), ("intrinsic_distance", intrinsic.iloc[0]), ("historical_iqr", hist_iqr)]:
                close(row[field], value, field)
            rows.append({**dict(zip(IDENTITY, identity)), "profile": profile, **row, **derived,
                         "mc_ess_below_10": float(derived["weight_ess"] < 10),
                         "mc_largest_weight_above_020": float(derived["largest_weight_share"] > .2) if derived["sample_supported"] else math.nan,
                         "history_conditioning": "presence_only_diagnostic_not_legacy_likelihood" if profile == "baseline_current" else "experimental_observation_compatibility"})
    return pd.DataFrame(rows)


def context_summary(search, validation, configs):
    rows = []
    metrics = ["overall_distance", "historical_distance", "intrinsic_distance", *LATE_METRICS,
               "mc_ess_below_10", "mc_largest_weight_above_020"]
    metrics += [c for c in validation if c.endswith(("_mean", "_median")) or c.startswith("compatibility_weighted_")]
    for phase, table in [("search", search), ("validation", validation)]:
        selected = table.loc[table.selected]
        for seed, config in configs.items():
            for profile in PROFILES:
                context = selected.loc[(selected.search_seed == seed) & (selected.profile == profile)]
                for family in ["all_families", *config["families"]]:
                    group = context if family == "all_families" else context.loc[context.family_id == family]
                    for metric in metrics:
                        values = group[metric]
                        rows.append({"search_seed": seed, "profile": profile, "family_id": family, "phase": phase,
                                     "metric": metric, "n_sources": len(group), "n_supported": int(group.sample_supported.sum()),
                                     "n_sources_with_value": int(values.notna().sum()), "source_mean": values.mean(), "source_median": values.median(),
                                     "history_conditioning": "presence_only_diagnostic_not_legacy_likelihood" if profile == "baseline_current" else "experimental_observation_compatibility"})
    return pd.DataFrame(rows)


def summarise(input_dir, output_dir):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    manifest_path = input_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    require(manifest.get("status") == "complete", "Pilot manifest is not complete")
    require(manifest.get("scope") == "bounded_observation_repair_pilot", "Unexpected pilot scope")
    require(set(manifest["outputs"]) == set(RAW_NAMES), "Unexpected or missing raw outputs")
    require(set(manifest["profiles"]) == set(PROFILES) and manifest["late_block_weight"] == 5., "Unexpected profile specification")
    for profile, p in PROFILES.items():
        if profile != "baseline_current":
            close(manifest["profiles"][profile], p, "declared profile detection")
    hashes = {"run_manifest.json": binding(manifest_path)}
    for name in RAW_NAMES:
        hashes[name] = binding(input_dir / name)
        require(hashes[name] == manifest["outputs"][name], f"Raw output checksum or size mismatch: {name}")
    data = {name: pd.read_csv(input_dir / name) for name in RAW_NAMES}
    parameters, deterministic, stage_a = [data[n] for n in RAW_NAMES[:3]]
    b_raw, b = data[RAW_NAMES[3]], data[RAW_NAMES[4]]
    v_raw, v = data[RAW_NAMES[5]], data[RAW_NAMES[6]]
    configs = {int(c["master_seed"]): c for c in manifest["configs"]}
    require(len(configs) == len(manifest["configs"]) and set(deterministic.search_seed) == set(configs), "Search-seed coverage mismatch")
    require(not parameters.duplicated([*IDENTITY, "parameter_id"]).any() and parameters.groupby(IDENTITY).size().eq(40).all(), "Invalid parameter grain")
    require(identities(parameters) == identities(deterministic), "Parameters/deterministic sources differ")
    for seed, config in configs.items():
        require(not config["stochastic_baselines"], "Pilot requires deterministic intrinsic scenarios")
        d = deterministic.loc[deterministic.search_seed == seed]
        require(set(d.family_id) == set(config["families"]), "Prior family coverage differs")
        require(d.groupby("family_id").size().eq(config["stage_a_draws_per_family"]).all(), "Prior draw counts differ")
        require(d.replicate_index.eq(0).all(), "Unexpected deterministic replicate ID")
    augmented_a = verify_and_augment(deterministic, stage_a, "stage_a")
    membership = identities(stage_a.loc[stage_a.stage_a_retained], PROFILE_KEY)
    selected = identities(b.loc[b.selected], PROFILE_KEY)
    require({x[:3] for x in membership} == identities(b_raw), "Stage B union differs from Stage A membership")
    require({x[:3] for x in selected} == identities(v_raw), "Validation source union differs from original selection")
    require(identities(v.loc[v.selected], PROFILE_KEY) == selected, "Validation changed the frozen selection")
    for table in [b, v]:
        actual = identities(table.loc[table.stage_a_retained], PROFILE_KEY)
        table_sources = identities(table)
        expected = {key for key in membership if key[:3] in table_sources}
        require(actual == expected, "Stage A membership changed across stages")
        require(table.loc[table.selected].stage_a_retained.all(), "Selected source absent from profile Stage A")
    for (seed, profile, family), group in augmented_a.groupby(["search_seed", "profile", "family_id"]):
        expected_n = min(configs[seed]["stage_a_keep_per_family"], int(group.finite_supported.sum()))
        require(int(group.stage_a_retained.sum()) == expected_n, "Stage A retained count mismatch")
        expected = identities(group.loc[group.finite_supported].sort_values(ORDER).head(expected_n))
        require(identities(group.loc[group.stage_a_retained]) == expected, "Stage A retained order mismatch")
    for (seed, profile), group in b.groupby(["search_seed", "profile"]):
        eligible = group.loc[group.stage_a_retained & group.finite_supported]
        expected_n = min(configs[seed]["final_acceptance_cap"], math.ceil(configs[seed]["final_acceptance_fraction"] * len(eligible)))
        require(int(group.selected.sum()) == expected_n and group.loc[group.selected].finite_supported.all(), "Stage B selection count/eligibility mismatch")
        require(identities(group.loc[group.selected]) == identities(eligible.sort_values(ORDER).head(expected_n)), "Stage B selection order mismatch")
    for phase, raw in [("stage_b", b_raw), ("validation", v_raw)]:
        require(not raw.simulation_seed.duplicated().any(), f"Duplicate {phase} RNG seed")
        for identity, group in raw.groupby(IDENTITY):
            n = configs[identity[0]]["stage_b_historical_replicates"] if phase == "stage_b" else manifest["validation_replicates"]
            require(set(group.replicate_index) == set(range(1, n + 1)) and len(group) == n, f"{phase} replicate coverage mismatch")
    require(not set(b_raw.simulation_seed) & set(v_raw.simulation_seed), "Search/validation RNG seeds overlap")
    counts = {"prior_sources": len(deterministic), "deterministic_historical_runs": len(deterministic), "deterministic_intrinsic_runs": 2 * len(deterministic),
              "stage_b_union_sources": len(identities(b_raw)), "stage_b_historical_runs": len(b_raw), "validation_union_sources": len(identities(v_raw)), "validation_historical_runs": len(v_raw)}
    require(counts == manifest["counts"], "Declared run counts do not reconcile")
    search = verify_and_augment(b_raw, b, "stage_b")
    validation = verify_and_augment(v_raw, v, "validation")
    source_validation = search.loc[search.selected].merge(validation.loc[validation.selected], on=PROFILE_KEY, suffixes=("_search", "_validation"), validate="one_to_one")
    require(len(source_validation) == len(selected), "Selected-source join lost rows")
    contexts = context_summary(search, validation, configs)
    overlap = []
    for seed in configs:
        for a, b_profile in combinations(PROFILES, 2):
            sets = [{key[:3] for key in selected if key[0] == seed and key[3] == profile} for profile in [a, b_profile]]
            union, intersection = sets[0] | sets[1], sets[0] & sets[1]
            overlap.append({"search_seed": seed, "profile_a": a, "profile_b": b_profile, "n_selected_a": len(sets[0]), "n_selected_b": len(sets[1]), "n_intersection": len(intersection), "n_union": len(union), "jaccard_overlap": len(intersection) / len(union) if union else math.nan})
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in [("source_validation.csv", source_validation), ("context_summary.csv", contexts), ("selection_overlap.csv", pd.DataFrame(overlap))]:
        table.to_csv(output_dir / name, index=False, float_format="%.12g")
    receipt = {"scope": "completed_pilot_summary_no_simulation_no_reselection", "input_bindings": hashes, "verified_counts": counts,
               "source_validation_rows": len(source_validation), "context_summary_rows": len(contexts), "aggregation": "Originally selected source/profile rows only. Within each context every parameter source has equal weight. Both search and independent validation are reported. No cross-profile averaging or validation ranking.",
               "conditional_history_physics": "Within each source normalise I(positive_records_compatible)*(1-p)^occupied_episodes using stable log weights. Average resulting source expectations equally. These are conditional process histories under experimental assumptions, not posterior parameter/model probabilities.",
               "legacy_weighting": "baseline_current weighted physics use presence-only p=0 diagnostics, not an asserted legacy observation likelihood.",
               "unsupported": "Zero sampled support yields infinite discrepancy and missing conditional physics; no floor or fabricated weights. n_supported and n_sources_with_value disclose coverage. Means of conditional physics exclude unsupported sources.",
               "mc_warnings": "ESS <10 and largest weight share >0.2 diagnose Monte Carlo concentration, not biological fit. Largest-share warning is missing without sampled support; ESS warning includes zero-support sources.",
               "raw_source_binding_record": manifest["source_bindings"], "summariser_binding": {"path": str(Path(__file__).relative_to(ROOT)), **binding(Path(__file__))},
               "outputs": {name: binding(output_dir / name) for name in ["source_validation.csv", "context_summary.csv", "selection_overlap.csv"]}}
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"verified_counts": counts, "source_validation_rows": len(source_validation), "context_summary_rows": len(contexts)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/observation_repair_pilot")
    args = parser.parse_args()
    summarise(args.input_dir, args.output_dir)
