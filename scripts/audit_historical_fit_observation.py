#!/usr/bin/env python3
"""Audit archived Module 4 projections; never simulate, calibrate, or replay.

Every rank probe is leverage_only_existing_screened_pool. Score zero denotes
only a nominal scoring criterion. Capture projections are capture-equivalent
indices, not effort-standardised field counts or predictive observations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from galaxias_model.scoring import OBSERVATION_BRIDGE_VARIANTS

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "outputs/remote/module4_observation_sensitivity_20260522T101942Z"
AUDIT_SCOPE = "leverage_only_existing_screened_pool"
TARGETS = [f"CT{i:03d}" for i in range(1, 13)]
LATE_TARGETS = TARGETS[5:10]
SEEDS = {20260410, 20260411, 20260412}
FAMILIES = {"habitat_only_null", "trout_only", "climbing_only", "persistent_joint_cause", "transient_perfect_storm"}
KEY = ["proposal_id", "replicate_index"]
RTOL, ATOL = 1e-9, 1e-8


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected, label):
    require(np.allclose(actual, expected, rtol=RTOL, atol=ATOL, equal_nan=True), f"Reconstruction mismatch: {label}")


def file_binding(path, expected_size=None, expected_hash=None):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    result = {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}
    if expected_size is not None:
        require(result["bytes"] == int(expected_size), f"Size mismatch: {path}")
    if expected_hash is not None:
        require(result["sha256"] == expected_hash, f"SHA256 mismatch: {path}")
    return result


def range_cost(x, low, high):
    return np.maximum(np.maximum(low - x, x - high), 0) / (high - low)


def reconstruct_late_scores(stage_b, parameters, variant, details, weights):
    """Independent vector algebra from stored projections, not score_target."""
    phi = parameters.loc[parameters.parameter_id == "PR037"].set_index("proposal_id").value_natural
    cfg = OBSERVATION_BRIDGE_VARIANTS[variant]
    result = {}
    for target in LATE_TARGETS:
        d = stage_b.loc[stage_b.target_id == target].set_index(KEY).sort_index().copy()
        p, s = d.projected_primary, d.projected_secondary
        q = d.index.get_level_values("proposal_id").map(phi).to_numpy()
        require(np.isfinite(q).all() and (q > 0).all(), "Missing/invalid PR037")
        d["pr037"] = q
        if target == "CT006":
            bounds = details[target]["expected_capture_range"]
            d["lake_presence_fraction"] = 3 * d.raw_penalty - (1 - s) - range_cost(p, bounds["low"], bounds["high"])
            require(d.lake_presence_fraction.between(-ATOL, 1 + ATOL).all(), "CT006 inferred presence outside [0,1]")
            d["lake_presence_fraction"] = d.lake_presence_fraction.clip(0, 1)
        elif target == "CT007":
            spec = details[target]
            close(p, spec["survey_sites"] * -np.expm1(-spec["occupancy_anchor_alpha"] * s), "CT007 occupancy map")
            occupancy = cfg["ct007_occupancy_weight"] * range_cost(p, spec["occupied_site_range"]["low"], spec["occupied_site_range"]["high"])
            exp = np.maximum(s, 1e-9)
            obs = spec["observed_capture_count"]
            d["count_raw_component"] = cfg["ct007_count_weight"] * 2 * (obs * np.log(obs / exp) - (obs - exp)) / q
            raw = occupancy + d.count_raw_component
            close(d.raw_penalty, raw, target)
            d["count_weighted_component"] = d.count_raw_component * weights[target]
            d["count_contribution_share"] = d.count_raw_component / raw.where(raw > 0)
        elif target == "CT008":
            spec = details[target]
            raw = 0.75 * np.maximum(p - spec["capture_upper_bound"], 0) / spec["capture_soft_gap"] + 0.25 * np.maximum(s - spec["latent_upper_bound"], 0) / spec["latent_soft_gap"]
            close(d.raw_penalty, raw, target)
        elif target == "CT009":
            if cfg["ct009_mode"] == "exact_year":
                raw = np.abs(p - details[target]["target_year"])
            else:
                raw = np.where(p < cfg["ct009_low_year"], (cfg["ct009_low_year"] - p) / cfg["ct009_early_gap"], np.maximum(p - cfg["ct009_high_year"], 0) / cfg["ct009_late_gap"])
            raw = np.where(p.isna(), 10.0, raw)
            close(d.raw_penalty, raw, target)
        else:
            close(d.raw_penalty, 2 * p * cfg["ct010_detection_multiplier"] / q, target)
        close(d.weighted_penalty, d.raw_penalty * weights[target], target + " weighted")
        result[target] = d
    return result


def proposal_order(scores):
    """Current calibration order: median(sum), historical, intrinsic, IQR, ID."""
    wide = scores.pivot(index=KEY, columns="target_id", values="weighted_penalty")
    require(set(wide.columns) == set(TARGETS) and np.isfinite(wide.to_numpy()).all(), "Incomplete/nonfinite target scores")
    replicate = pd.DataFrame({"overall": wide.sum(axis=1), "historical": wide[TARGETS[:10]].sum(axis=1), "intrinsic": wide[TARGETS[10:]].sum(axis=1)})
    grouped = replicate.groupby(level="proposal_id")
    order = grouped.median()
    order["historical_iqr"] = grouped.historical.quantile(0.75) - grouped.historical.quantile(0.25)
    order["target_median_sum"] = wide.groupby(level="proposal_id").median().sum(axis=1)
    return order.reset_index().sort_values(["overall", "historical", "intrinsic", "historical_iqr", "proposal_id"])


def validate_grain(proposals, parameters, targets):
    require(len(proposals) == 5000 and proposals.proposal_id.is_unique, "Expected 5000 unique proposals")
    require(set(proposals.family_id) == FAMILIES, "Unexpected families")
    require(len(parameters) == 200000 and not parameters.duplicated(["proposal_id", "parameter_id"]).any(), "Invalid parameter grain")
    require(set(parameters.proposal_id) == set(proposals.proposal_id), "Parameter/proposal ID mismatch")
    require(parameters.groupby("proposal_id").parameter_id.nunique().eq(40).all(), "Expected 40 parameters per proposal")
    require(len(targets) == 180000 and not targets.duplicated(["proposal_id", "stage", "replicate_index", "target_id"]).any(), "Invalid target grain")
    require(targets.evaluation_status.eq("scored").all(), "Unscored archived targets")
    require(set(targets.stage) == {"stage_a", "stage_b"}, "Unexpected stages")
    a = targets.loc[targets.stage == "stage_a"]
    require(len(a) == 60000 and a.replicate_index.eq(0).all() and set(a.proposal_id) == set(proposals.proposal_id), "Invalid Stage A coverage")
    b = targets.loc[targets.stage == "stage_b"].copy()
    require(len(b) == 120000 and b.proposal_id.nunique() == 500, "Expected 500 Stage B sources")
    require(b.groupby("proposal_id").replicate_index.nunique().eq(20).all(), "Expected 20 replicates per source")
    require(set(b.replicate_index) == set(range(1, 21)), "Unexpected replicate IDs")
    require(b.groupby(KEY).target_id.apply(lambda x: set(x) == set(TARGETS)).all(), "Incomplete target coverage")
    eligible = proposals.loc[proposals.stochastic_full_ready_for_module3 & np.isfinite(proposals.stochastic_overall_distance_median)].copy()
    require(set(eligible.proposal_id) == set(b.proposal_id), "Stage B eligibility mismatch")
    require(eligible.groupby("family_id").size().eq(100).all(), "Expected 100 sources per family")
    require(int(proposals.accepted_final.sum()) == 50 and proposals.loc[proposals.accepted_final].proposal_id.isin(eligible.proposal_id).all(), "Expected 50 accepted eligible sources")
    mapped = targets.proposal_id.map(proposals.set_index("proposal_id").family_id)
    require(mapped.eq(targets.family_id).all(), "Target family mismatch")
    return eligible, b


def fit_metrics(late, stage_b):
    """Series at replicate grain, with the specified within-source statistic."""
    metrics = []
    def add(target, metric, values, reduction="median", interpretation="native_or_projected_metric"):
        metrics.append((target, metric, values, reduction, interpretation))
    for target, d in late.items():
        add(target, "raw_penalty", d.raw_penalty)
        add(target, "weighted_penalty", d.weighted_penalty)
        add(target, "zero_penalty_fraction", d.raw_penalty.abs().le(ATOL).astype(float), "mean", "nominal_scoring_criterion_only")
    d = late["CT006"]
    add("CT006", "capture_equivalent_index", d.projected_primary)
    add("CT006", "refuge_presence_fraction", d.projected_secondary)
    add("CT006", "lake_presence_fraction_inferred", d.lake_presence_fraction)
    add("CT006", "capture_index_in_5_to_20_fraction", d.projected_primary.between(5, 20).astype(float), "mean", "nominal_scoring_criterion_only")
    d = late["CT007"]
    add("CT007", "projected_occupied_sites", d.projected_primary)
    add("CT007", "capture_equivalent_index", d.projected_secondary)
    add("CT007", "occupancy_in_3_to_7_fraction", d.projected_primary.between(3, 7).astype(float), "mean", "nominal_scoring_criterion_only")
    add("CT007", "count_contribution_share", d.count_contribution_share, "mean", "score_decomposition")
    add("CT007", "pr037_division_only_nuisance", d.pr037)
    d = late["CT008"]
    add("CT008", "capture_equivalent_index", d.projected_primary)
    add("CT008", "latent_total_window_mean", d.projected_secondary)
    add("CT008", "capture_index_le_10_fraction", d.projected_primary.le(10).astype(float), "mean", "nominal_scoring_criterion_only")
    add("CT008", "latent_total_le_50_fraction", d.projected_secondary.le(50).astype(float), "mean", "nominal_scoring_criterion_only")
    d = late["CT009"]
    add("CT009", "latent_last_presence_year", d.projected_primary)
    add("CT009", "latent_first_absence_year_when_observed", d.projected_secondary)
    for metric, flag in [("surviving_2002_fraction", d.projected_primary.eq(2002)), ("present_through_1996_fraction", d.projected_primary.ge(1996)), ("last_presence_before_1996_fraction", d.projected_primary.lt(1996)), ("last_presence_exact_1996_fraction", d.projected_primary.eq(1996)), ("last_presence_after_1996_fraction", d.projected_primary.gt(1996))]:
        add("CT009", metric, flag.astype(float), "mean", "latent_state_fraction_not_detection")
    d = late["CT010"]
    add("CT010", "mean_capture_equivalent_index", d.projected_primary)
    add("CT010", "maximum_capture_equivalent_index", d.projected_secondary)
    add("CT010", "pr037_division_only_nuisance", d.pr037)
    total = stage_b.groupby(KEY).weighted_penalty.sum()
    for target, d in late.items():
        add(target, "weighted_score_share_all_12", d.weighted_penalty / total.where(total > 0), "mean", "score_decomposition")
    combined = stage_b.loc[stage_b.target_id.isin(LATE_TARGETS)].groupby(KEY).weighted_penalty.sum()
    add("CT006_CT010", "weighted_score_share_all_12", combined / total.where(total > 0), "mean", "score_decomposition")
    return metrics


def summarize_fit(metrics, eligible, variant, seed):
    rows = []
    for population, selected in [("all_eligible_stage_b", eligible), ("accepted", eligible.loc[eligible.accepted_final])]:
        for family in ["all_families", *sorted(FAMILIES)]:
            group = selected if family == "all_families" else selected.loc[selected.family_id == family]
            ids = set(group.proposal_id)
            for target, metric, values, reduction, interpretation in metrics:
                v = values.loc[values.index.get_level_values("proposal_id").isin(ids)]
                per_source = v.groupby(level="proposal_id").agg(reduction).dropna()
                rows.append({"variant_id": variant, "seed": seed, "population": population, "family_id": family, "target_id": target, "metric": metric, "within_source_statistic": reduction, "interpretation": interpretation, "n_sources": len(ids), "n_replicates": len(ids) * 20, "n_sources_with_value": len(per_source), "n_replicates_with_value": int(v.notna().sum()), "source_mean": per_source.mean(), "source_q10": per_source.quantile(.1), "source_median": per_source.median(), "source_q90": per_source.quantile(.9)})
    return rows


def rank_probes(stage_b, late, eligible, variant, seed):
    rows = []
    accepted = set(eligible.loc[eligible.accepted_final].proposal_id)
    family_map = eligible.set_index("proposal_id").family_id
    for probe in ["as_scored", "omit_ct009", "omit_ct007_count_component", "omit_both", "omit_ct006_through_ct010", "fixed_pr037_default"]:
        adjusted = stage_b.copy()
        if probe in {"omit_ct009", "omit_both"}:
            adjusted.loc[adjusted.target_id == "CT009", "weighted_penalty"] = 0.
        if probe in {"omit_ct007_count_component", "omit_both", "fixed_pr037_default"}:
            mask = adjusted.target_id == "CT007"
            lookup = pd.MultiIndex.from_frame(adjusted.loc[mask, KEY])
            component = late["CT007"].loc[lookup, "count_weighted_component"].to_numpy()
            factor = late["CT007"].loc[lookup, "pr037"].to_numpy() / 1.2 - 1 if probe == "fixed_pr037_default" else -1
            adjusted.loc[mask, "weighted_penalty"] += component * factor
        if probe == "omit_ct006_through_ct010":
            adjusted.loc[adjusted.target_id.isin(LATE_TARGETS), "weighted_penalty"] = 0.
        if probe == "fixed_pr037_default":
            mask = adjusted.target_id == "CT010"
            lookup = pd.MultiIndex.from_frame(adjusted.loc[mask, KEY])
            adjusted.loc[mask, "weighted_penalty"] *= late["CT010"].loc[lookup, "pr037"].to_numpy() / 1.2
        order = proposal_order(adjusted)
        order["family_id"] = order.proposal_id.map(family_map)
        selected = set(order.head(50).proposal_id)
        if probe == "as_scored":
            require(selected == accepted, "Recomputed acceptance differs from archive")
            stored = eligible.set_index("proposal_id").loc[order.proposal_id]
            for computed, original in [("overall", "stochastic_overall_distance_median"), ("historical", "stochastic_historical_core_distance_median"), ("intrinsic", "stochastic_intrinsic_baseline_distance_median"), ("historical_iqr", "stochastic_historical_core_distance_iqr")]:
                close(order[computed], stored[original], original)
        stochastic_winner = order.iloc[0].family_id
        target_order = order.sort_values(["target_median_sum", "proposal_id"])
        target_winner = target_order.iloc[0].family_id
        for family in sorted(FAMILIES):
            f = order.loc[order.family_id == family]
            best_target = f.sort_values(["target_median_sum", "proposal_id"]).iloc[0]
            family_ids = set(f.proposal_id)
            rows.append({"variant_id": variant, "seed": seed, "probe": probe, "scope": AUDIT_SCOPE, "family_id": family, "n_sources": len(f), "selected_count": len(selected & family_ids), "accepted_overlap_count": len(selected & accepted & family_ids), "context_accepted_overlap_count": len(selected & accepted), "selection_cutoff": order.iloc[49].overall, "best_median_replicate_total": f.iloc[0].overall, "best_median_replicate_total_proposal_id": f.iloc[0].proposal_id, "best_target_median_sum": best_target.target_median_sum, "best_target_median_sum_proposal_id": best_target.proposal_id, "winner_median_replicate_total": family == stochastic_winner, "winner_target_median_sum": family == target_winner})
    return rows


def reconcile_evidence(rank_rows, variant, seed, evidence):
    rows = pd.DataFrame(rank_rows).query("probe == 'as_scored'").set_index("family_id")
    for name, table in evidence.items():
        e = table.loc[(table.variant_id == variant) & (table.seed == seed)].set_index("family_id")
        require(set(e.index) == FAMILIES, f"Missing evidence families: {name}")
        if name == "distance_audit":
            close(rows.loc[e.index, "best_median_replicate_total"], e.best_stochastic_distance, name)
            close(rows.loc[e.index, "selected_count"], e.accepted_count, name + " accepted")
            close(rows.loc[e.index, "best_target_median_sum"], e.best_target_sum, name + " target sum")
        else:
            close(rows.loc[e.index, "best_target_median_sum"], e.median_target_sum, name)
            require(rows.loc[e.index, "best_target_median_sum_proposal_id"].eq(e.proposal_id).all(), "Published target-sum proposal mismatch")


def algebra_probes(details):
    spec = details["CT007"]
    alpha = spec["occupancy_anchor_alpha"]
    close(spec["survey_sites"] * -np.expm1(-alpha * 68), 5, "CT007 anchor")
    rows = [{"probe": "ct007_capture_68_maps_to_sites", "input_value": 68., "output_value": spec["survey_sites"] * -np.expm1(-alpha * 68), "interpretation": "deterministic_bridge_identity"}]
    for sites in [3., 7.]:
        capture = -np.log1p(-sites / spec["survey_sites"]) / alpha
        rows.append({"probe": "ct007_sites_to_capture_equivalent", "input_value": sites, "output_value": capture, "interpretation": "same_q_as_ct006_imposes_increase_above_ct006_upper_20"})
    sites_at_20 = spec["survey_sites"] * -np.expm1(-alpha * 20)
    lower_capture = -np.log1p(-3 / spec["survey_sites"]) / alpha
    rows.extend([
        {"probe": "ct007_capture_20_maps_to_sites", "input_value": 20., "output_value": sites_at_20, "interpretation": "deterministic_bridge_identity"},
        {"probe": "capture_68_over_observed_11_ratio", "input_value": 11., "output_value": 68 / 11, "interpretation": "implied_rebound_with_shared_q_and_comparable_windows_only"},
        {"probe": "ct007_lower_site_threshold_over_ct006_upper_ratio", "input_value": 20., "output_value": lower_capture / 20, "interpretation": "implied_minimum_rebound_with_shared_q_only"},
    ])
    for variant in ["baseline_current", "ct007_occupancy_primary"]:
        cfg = OBSERVATION_BRIDGE_VARIANTS[variant]
        count_component = cfg["ct007_count_weight"] * 2 * (68 * np.log(68 / 20) - (68 - 20)) / 4
        occupancy_component = cfg["ct007_occupancy_weight"] * (3 - sites_at_20) / 4
        rows.append({"probe": f"ct007_count_share_capture20_phi4_{variant}", "input_value": 20., "output_value": count_component / (count_component + occupancy_component), "interpretation": "illustrative_fixed_projection_score_share_at_prior_upper_phi"})
    priors = pd.read_csv(ROOT / "data/parameter_priors.csv")
    p = priors.set_index("parameter_id").loc["PR037"]
    # Bind these values to the maintained prior rather than invent sensitivity endpoints.
    require(float(p["lower_bound"]) == .2 and float(p["upper_bound"]) == 4. and float(p["default_value"]) == 1.2, "PR037 prior changed")
    for phi in [.2, 1.2, 4.]:
        rows.append({"probe": "pr037_division_only_score_multiplier", "input_value": phi, "output_value": 1 / phi, "interpretation": "fixed_projection_penalty_decreases_monotonically_with_phi"})
    return rows


def run(module4_root, output_dir, manifest_path):
    started = time.monotonic()
    manifest = pd.read_csv(manifest_path)
    contexts = manifest[["variant_id", "seed", "run_dir_name"]].drop_duplicates()
    require(set(map(tuple, contexts[["variant_id", "seed"]].to_numpy())) == {(v, s) for v in OBSERVATION_BRIDGE_VARIANTS for s in SEEDS} and len(contexts) == 15, "Expected five variants by three seeds")
    details = json.loads((ROOT / "data/calibration_target_details.json").read_text())
    weights = pd.read_csv(ROOT / "data/calibration_targets.csv").set_index("target_id").priority_weight.to_dict()
    evidence_paths = {"distance_audit": ROOT / "data/module4_5_distance_audit.csv", "family_winners": ROOT / "data/module4_family_winners.csv"}
    evidence = {name: pd.read_csv(path) for name, path in evidence_paths.items()}
    bindings, fit, ranks, selection = [], [], [], []
    for context in contexts.sort_values(["variant_id", "seed"]).itertuples(index=False):
        variant, seed, directory = context
        subset = manifest.loc[(manifest.variant_id == variant) & (manifest.seed == seed)]
        paths = {}
        for role in ["proposal_summary", "target_scores", "parameter_values", "run_manifest"]:
            rows = subset.loc[subset.file_role == role]
            require(len(rows) == 1, f"Missing/duplicate role {role}")
            row = rows.iloc[0]
            path = module4_root / directory / row.file_name
            bound = file_binding(path, row.local_bytes, row.local_sha256)
            bindings.append({"variant_id": variant, "seed": int(seed), "role": role, "archive_relative_path": f"{directory}/{row.file_name}", **bound})
            paths[role] = path
        config = json.loads(paths["run_manifest"].read_text())["config"]
        require(config["observation_bridge_variant"] == variant and config["master_seed"] == seed and config["stage_b_historical_replicates"] == 20 and config["final_acceptance_cap"] == 50 and config["final_acceptance_fraction"] == .1 and not config["stochastic_baselines"], "Run configuration mismatch")
        proposals = pd.read_csv(paths["proposal_summary"])
        parameters = pd.read_csv(paths["parameter_values"])
        targets = pd.read_csv(paths["target_scores"])
        eligible, stage_b = validate_grain(proposals, parameters, targets)
        late = reconstruct_late_scores(stage_b, parameters, variant, details, weights)
        fit.extend(summarize_fit(fit_metrics(late, stage_b), eligible, variant, seed))
        rank = rank_probes(stage_b, late, eligible, variant, seed)
        reconcile_evidence(rank, variant, seed, evidence)
        ranks.extend(rank)
        for row in rank:
            if row["probe"] == "as_scored":
                selection.append({k: row[k] for k in ["variant_id", "seed", "family_id", "n_sources", "selected_count", "selection_cutoff", "best_median_replicate_total", "best_target_median_sum", "winner_median_replicate_total", "winner_target_median_sum"]})
        print(f"Verified {variant} seed {seed}: 500 eligible, 50 accepted, 120000 Stage B target rows", flush=True)
    fit = pd.DataFrame(fit)
    keys = ["variant_id", "population", "family_id", "target_id", "metric", "within_source_statistic", "interpretation"]
    numeric = ["n_sources", "n_replicates", "n_sources_with_value", "n_replicates_with_value", "source_mean", "source_q10", "source_median", "source_q90"]
    variants = fit.groupby(keys, dropna=False)[numeric].agg(["mean", "min", "max", "count"])
    variants.columns = [f"{col}_context_{stat}" for col, stat in variants.columns]
    variants = variants.reset_index()
    rank_table = pd.DataFrame(ranks)
    winner_counts = rank_table.loc[(rank_table.probe == "as_scored") & rank_table.winner_target_median_sum].family_id.value_counts().to_dict()
    require(winner_counts == {"persistent_joint_cause": 12, "climbing_only": 3}, "Published 12/3 tally mismatch")
    probes = algebra_probes(details)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in {"context_fit_summary": fit, "variant_fit_summary": variants, "context_selection_summary": pd.DataFrame(selection), "rank_leverage": rank_table, "bridge_algebra_probes": pd.DataFrame(probes)}.items():
        table.to_csv(output_dir / f"{name}.csv", index=False, float_format="%.12g")
    bind_paths = [manifest_path, *evidence_paths.values(), ROOT / "data/calibration_target_details.json", ROOT / "data/calibration_targets.csv", ROOT / "data/parameter_priors.csv", ROOT / "src/galaxias_model/scoring.py", Path(__file__)]
    metadata = {"scope": "archive_only_observation_and_historical_fit_audit", "rank_probe_scope": AUDIT_SCOPE, "simulations_run": 0, "context_count": 15, "verified_raw_file_count": len(bindings), "verified_raw_bytes": sum(x["bytes"] for x in bindings), "stage_b_sources_per_context": 500, "accepted_sources_per_context": 50, "replicates_per_source": 20, "stage_b_target_rows_total": 1800000, "published_target_sum_winner_counts": winner_counts, "summary_rule": "Each source has equal weight within its family/context; numeric metrics use per-source replicate medians, criterion and score-share fractions use per-source replicate means. Variant outputs use equal-seed context mean/min/max. Empty accepted families are explicit; no cross-variant mean.", "missing_first_absence": "Surviving trajectories have missing first-absence year; conditional medians exclude these and counts disclose coverage. Terminal persistence is last_presence_year == 2002.", "criterion_interpretation": "Zero penalty is a nominal scoring criterion only, not empirical goodness-of-fit; no predictive probabilities or count tolerance introduced.", "rank_order": "median of replicate total; median historical sum; median intrinsic sum; historical sum IQR; proposal ID. Secondary reporting order is sum of target medians.", "fixed_pr037_default": "Leverage-only rescaling of CT007 count component and CT010 by archived PR037/1.2; fixed ecology, not a proposed scoring revision.", "numeric_tolerance": {"rtol": RTOL, "atol": ATOL}, "bindings": bindings, "audit_input_bindings": [{"path": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name, **file_binding(p)} for p in bind_paths], "elapsed_seconds": round(time.monotonic() - started, 3)}
    (output_dir / "audit_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({k: metadata[k] for k in ["context_count", "verified_raw_bytes", "published_target_sum_winner_counts", "elapsed_seconds"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module4-root", type=Path, default=RAW_ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/historical_fit_observation_audit")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/module4_raw_artifact_manifest.csv")
    args = parser.parse_args()
    run(args.module4_root, args.output_dir, args.manifest)
