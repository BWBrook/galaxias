#!/usr/bin/env python3
"""Verify staged terminal-history evidence and freeze the next phase's sources."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from summarize_observation_repair_pilot import (
    IDENTITY, PROFILE_KEY, ORDER, PROFILES, binding, close, identities,
    require, verify_and_augment,
)

ROOT = Path(__file__).resolve().parents[1]
REPAIRS = [p for p in PROFILES if p != "baseline_current"]
NULLABLE_YEARS = ["first_zero_year", "latent_last_presence_year"]
EVENTS = ["positive_records_compatible", "positive_and_extinct_by_2002",
          "positive_and_all_natural_nondetections_empty",
          "positive_and_all_nondetections_empty"]
METRICS = ["overall_distance", "intrinsic_distance", "late_discrepancy",
           "positive_compatible_fraction", "conditional_nondetection_compatibility",
           "mean_joint_compatibility", "weight_ess", "largest_weight_share",
           "mc_relative_se", "mc_ess_below_10", "mc_largest_weight_above_020",
           "surviving_2002_mean", "n_total_2002_mean",
           "compatibility_weighted_surviving_2002",
           "compatibility_weighted_n_total_2002"]


def binomial_summary(successes, n):
    """Pointwise Wilson 95% interval; exact one-sided upper bound for zero."""
    require(n > 0 and 0 <= successes <= n, "Invalid event denominator")
    p, z = successes / n, 1.959963984540054
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return {"count": successes, "fraction": p, "lower95": max(0., centre - half),
            "upper95": min(1., centre + half),
            "zero_one_sided_upper95": -math.expm1(math.log(.05) / n) if successes == 0 else math.nan}


def read_phase(directory, phase):
    manifest = json.loads((directory / "run_manifest.json").read_text())
    require(manifest["phase"] == phase and manifest["status"] == "complete", "Incomplete/wrong phase")
    for name, expected in manifest["outputs"].items():
        require(binding(directory / name) == expected, f"Phase binding mismatch: {name}")
    raw = pd.read_csv(directory / "raw_replicates.csv.gz")
    summary = pd.read_csv(directory / "source_summary.csv")
    require(not raw.simulation_seed.duplicated().any(), "Duplicated phase RNG seed")
    counts = raw.groupby(IDENTITY).replicate_index.agg(list)
    require(len(counts) == manifest["source_count"], "Phase source count mismatch")
    require(all(set(v) == set(range(1, manifest["replicates"] + 1)) and len(v) == manifest["replicates"] for v in counts), "Incomplete replicate coverage")
    # The first zero is censored when no zero occurs; the older helper requires
    # its numeric physical columns to be finite. Check this nullable field here.
    if "first_zero_year" in raw:
        require((raw.first_zero_year.isna() == ~raw.extinct_by_2002.astype(bool)).all(), "First-zero censoring mismatch")
        observed = raw.first_zero_year.notna()
        require(raw.loc[observed, "first_zero_year"].between(1965, 2002).all(), "First-zero year outside history")
        previously_present = observed & raw.latent_last_presence_year.notna()
        require((raw.loc[previously_present, "latent_last_presence_year"] < raw.loc[previously_present, "first_zero_year"]).all(), "Nonabsorbing total extinction")
        year_summary = summary.set_index(IDENTITY).sort_index()
        for field in NULLABLE_YEARS:
            for identity, group in raw.groupby(IDENTITY):
                reported, values = year_summary.loc[identity], group[field].dropna()
                close(reported[f"{field}_valid_replicates"], len(values), f"{field} denominator")
                close(reported[f"{field}_mean"], values.mean() if len(values) else math.nan, f"{field} mean")
                close(reported[f"{field}_median"], values.median() if len(values) else math.nan, f"{field} median")
    close(raw.positive_and_extinct_by_2002, raw.positive_records_compatible & ~raw.surviving_2002.astype(bool), "Terminal event")
    close(raw.positive_and_all_natural_nondetections_empty, raw.positive_records_compatible & raw.natural_nondetection_occupied_episodes.eq(0), "Empty natural surveys")
    close(raw.positive_and_all_nondetections_empty, raw.positive_records_compatible & raw.nondetection_occupied_episodes.eq(0), "Empty all surveys")
    clean_raw = raw.drop(columns=NULLABLE_YEARS, errors="ignore")
    clean_summary = summary.drop(columns=[f"{field}_{stat}" for field in NULLABLE_YEARS for stat in ["mean", "median", "valid_replicates"]], errors="ignore")
    verified = verify_and_augment(clean_raw, clean_summary, phase)
    event_rows = []
    for identity, group in raw.groupby(IDENTITY, sort=True):
        row = dict(zip(IDENTITY, identity))
        for event in EVENTS:
            row.update({f"{event}_{key}": value for key, value in binomial_summary(int(group[event].sum()), len(group)).items()})
        event_rows.append(row)
    verified = verified.merge(pd.DataFrame(event_rows), on=IDENTITY, validate="many_to_one")
    return raw, verified, manifest


def confirmation_selection(screen, pilot_dir):
    """Select only on the new screening histories; deterministic membership frozen."""
    original = pd.read_csv(pilot_dir / "stage_a_selection.csv")
    membership = identities(original.loc[original.stage_a_retained], PROFILE_KEY)
    selected = []
    for (seed, profile), context in screen.loc[screen.profile.isin(REPAIRS)].groupby(["search_seed", "profile"]):
        finite = context.loc[context.finite_supported].sort_values(ORDER)
        for route in ("full", "restricted"):
            candidates = finite if route == "full" else finite.loc[
                [tuple(row) in membership for row in finite[PROFILE_KEY].itertuples(index=False, name=None)]]
            for scope, chosen in [("global", candidates.head(10)),
                                  ("family", candidates.groupby("family_id", sort=True).head(1))]:
                selected.extend({**dict(zip(PROFILE_KEY, row)), "cohort": f"{route}_{scope}"}
                                for row in chosen[PROFILE_KEY].itertuples(index=False, name=None))
    event_candidates = screen.loc[screen.profile.eq(REPAIRS[0]) & screen.positive_and_extinct_by_2002_count.gt(0)]
    event_candidates = event_candidates.sort_values(["positive_and_extinct_by_2002_fraction", "proposal_id"], ascending=[False, True]).groupby(["search_seed", "family_id"], sort=True).head(1)
    for row in event_candidates[IDENTITY].itertuples(index=False, name=None):
        selected.extend({**dict(zip(IDENTITY, row)), "profile": p, "cohort": "terminal_event"} for p in REPAIRS)
    previous = pd.read_csv(pilot_dir / "stage_b_source_summary.csv")
    selected.extend({**dict(zip(PROFILE_KEY, row)), "cohort": "previous_pilot"}
                    for row in previous.loc[previous.selected, PROFILE_KEY].itertuples(index=False, name=None))
    result = pd.DataFrame(selected).sort_values(["cohort", *PROFILE_KEY]).reset_index(drop=True)
    require(not result.duplicated(["cohort", *PROFILE_KEY]).any(), "Duplicated selection membership")
    return result


def extension_selection(confirmation):
    candidates = confirmation.loc[confirmation.profile.isin(REPAIRS)].copy()
    candidates["flagged"] = (~candidates.sample_supported | candidates.weight_ess.lt(10) | candidates.largest_weight_share.gt(.20))
    candidates["no_support"] = ~candidates.sample_supported
    grouped = candidates.groupby(IDENTITY).agg(flagged=("flagged", "any"),
                                               no_support=("no_support", "any"),
                                               worst_relative_se=("mc_relative_se", "max")).reset_index()
    grouped = grouped.loc[grouped.flagged].sort_values(
        ["no_support", "worst_relative_se", *IDENTITY], ascending=[False, False, True, True, True], na_position="last")
    grouped["extension_priority"] = range(1, len(grouped) + 1)
    grouped["selected_for_extension"] = grouped.extension_priority.le(40)
    return grouped


def freeze_csv(path, table):
    """Selections cannot silently change after a later phase has begun."""
    payload = table.to_csv(index=False, float_format="%.12g")
    if path.exists():
        require(path.read_text() == payload, f"Frozen selection changed: {path.name}")
    else:
        path.write_text(payload)


def route_summary(table, members, phase):
    chosen = members.merge(table, on=PROFILE_KEY, how="left", validate="many_to_one")
    require(chosen.replicate_count.notna().all(), "Missing selected source in phase")
    rows = []
    fields = [*METRICS, *[f"{event}_fraction" for event in EVENTS]]
    for (seed, profile, cohort), group in chosen.groupby(["search_seed", "profile", "cohort"], sort=True):
        for family in ["all_families", *sorted(group.family_id.unique())]:
            subset = group if family == "all_families" else group.loc[group.family_id.eq(family)]
            row = {"phase": phase, "search_seed": seed, "profile": profile, "cohort": cohort,
                   "family_id": family, "n_sources": len(subset), "n_supported": int(subset.sample_supported.sum()),
                   "minimum_replicates": int(subset.replicate_count.min()),
                   "maximum_replicates": int(subset.replicate_count.max()),
                   "n_sources_extended": int(subset["extended_source"].sum()) if "extended_source" in subset else 0}
            for field in fields:
                row[field] = subset[field].mean()
                row[f"{field}_n"] = int(subset[field].notna().sum())
            rows.append(row)
    return pd.DataFrame(rows)


def analyse(screen_dir, pilot_dir, output_dir, confirm_dir=None, extend_dir=None):
    output_dir.mkdir(parents=True, exist_ok=True)
    pilot_manifest = json.loads((pilot_dir / "run_manifest.json").read_text())
    for name in ["stage_a_selection.csv", "stage_b_source_summary.csv", "parameter_values.csv.gz"]:
        require(binding(pilot_dir / name) == pilot_manifest["outputs"][name], f"Original pilot binding changed: {name}")
    screen_raw, screen, screen_manifest = read_phase(screen_dir, "screen")
    require(screen_manifest["pilot_input_bindings"]["run_manifest.json"] == binding(pilot_dir / "run_manifest.json"), "Screen used different pilot archive")
    prior_parameters = pd.read_csv(pilot_dir / "parameter_values.csv.gz", usecols=IDENTITY)
    require(identities(screen) == identities(prior_parameters), "Screen does not cover exact prior pool")
    members = confirmation_selection(screen, pilot_dir)
    candidates = members[IDENTITY].drop_duplicates().sort_values(IDENTITY).reset_index(drop=True)
    freeze_csv(output_dir / "selection_membership.csv", members)
    freeze_csv(output_dir / "confirmation_candidates.csv", candidates)
    outputs = ["selection_membership.csv", "confirmation_candidates.csv"]
    routes = [route_summary(screen, members, "screen")]
    phase_tables = [("screen", screen)]
    input_bindings = {"pilot_manifest": binding(pilot_dir / "run_manifest.json"), "screen_manifest": binding(screen_dir / "run_manifest.json")}
    original_a = pd.read_csv(pilot_dir / "stage_a_selection.csv")
    a_keys = identities(original_a.loc[original_a.stage_a_retained], PROFILE_KEY)
    support = screen.loc[screen.profile.isin(REPAIRS)].copy()
    support["outside_original_stage_a"] = [tuple(row) not in a_keys for row in support[PROFILE_KEY].itertuples(index=False, name=None)]
    support_rows = []
    for keys, group in support.groupby(["search_seed", "family_id", "profile", "outside_original_stage_a"], sort=True):
        row = dict(zip(["search_seed", "family_id", "profile", "outside_original_stage_a"], keys))
        row["n_sources"] = len(group)
        for event in EVENTS:
            row[f"{event}_sources_observed"] = int(group[f"{event}_count"].gt(0).sum())
            row[f"{event}_mean_frequency"] = group[f"{event}_fraction"].mean()
        support_rows.append(row)
    pd.DataFrame(support_rows).to_csv(output_dir / "screen_family_support.csv", index=False, float_format="%.12g")
    outputs.append("screen_family_support.csv")
    overlap_rows = []
    for (seed, profile), group in members.loc[members.cohort.isin(["full_global", "restricted_global"])].groupby(["search_seed", "profile"]):
        full = identities(group.loc[group.cohort.eq("full_global")])
        restricted = identities(group.loc[group.cohort.eq("restricted_global")])
        overlap_rows.append({"search_seed": seed, "profile": profile, "n_full": len(full), "n_restricted": len(restricted),
                             "n_shared": len(full & restricted), "full_outside_original_stage_a": sum((*key, profile) not in a_keys for key in full)})
    pd.DataFrame(overlap_rows).to_csv(output_dir / "route_overlap.csv", index=False)
    outputs.append("route_overlap.csv")
    if confirm_dir:
        confirm_raw, confirm, confirm_manifest = read_phase(confirm_dir, "confirm")
        require(confirm_manifest["pilot_input_bindings"] == screen_manifest["pilot_input_bindings"], "Confirmation used different pilot inputs")
        require(confirm_manifest["source_bindings"] == screen_manifest["source_bindings"], "Scientific execution snapshot changed after screening")
        require(identities(confirm) == identities(candidates), "Confirmation selection mismatch")
        require(not set(confirm_raw.simulation_seed) & set(screen_raw.simulation_seed), "Screen/confirmation seed overlap")
        input_bindings["confirm_manifest"] = binding(confirm_dir / "run_manifest.json")
        routes.append(route_summary(confirm, members, "confirm"))
        phase_tables.append(("confirm", confirm))
        extension = extension_selection(confirm)
        freeze_csv(output_dir / "extension_priority.csv", extension)
        extension_ids = extension.loc[extension.selected_for_extension, IDENTITY].sort_values(IDENTITY).reset_index(drop=True)
        freeze_csv(output_dir / "extension_candidates.csv", extension_ids)
        outputs += ["extension_priority.csv", "extension_candidates.csv"]
        if extend_dir:
            extend_raw, extend, extend_manifest = read_phase(extend_dir, "extend")
            require(extend_manifest["pilot_input_bindings"] == screen_manifest["pilot_input_bindings"], "Extension used different pilot inputs")
            require(extend_manifest["source_bindings"] == screen_manifest["source_bindings"], "Scientific execution snapshot changed before extension")
            require(identities(extend) == identities(extension_ids), "Extension selection mismatch")
            require(not set(extend_raw.simulation_seed) & (set(screen_raw.simulation_seed) | set(confirm_raw.simulation_seed)), "Extension seed overlap")
            input_bindings["extend_manifest"] = binding(extend_dir / "run_manifest.json")
            phase_tables.append(("extend", extend))
            # Preserve initial 500 as primary. Pool only extended sources, with
            # sequentially relabelled indices for summary verification.
            from run_observation_repair_pilot import source_summaries
            ext_keys = identities(extension_ids)
            initial = confirm_raw.loc[[tuple(row) in ext_keys for row in confirm_raw[IDENTITY].itertuples(index=False, name=None)]]
            pooled_raw = pd.concat([initial, extend_raw], ignore_index=True)
            pooled_raw["stage"] = "pooled_adaptive"
            pooled_raw["replicate_index"] = pooled_raw.groupby(IDENTITY).cumcount() + 1
            pooled_clean = pooled_raw.drop(columns=NULLABLE_YEARS, errors="ignore")
            pooled_summary = source_summaries(pooled_clean)
            pooled = verify_and_augment(pooled_clean, pooled_summary, "pooled_adaptive")
            event_rows = []
            for identity, group in pooled_raw.groupby(IDENTITY):
                row = dict(zip(IDENTITY, identity))
                for event in EVENTS:
                    # Adaptive pooled intervals are deliberately not labelled
                    # fixed-sample confidence intervals.
                    row[f"{event}_count"] = int(group[event].sum())
                    row[f"{event}_fraction"] = group[event].mean()
                event_rows.append(row)
            pooled = pooled.merge(pd.DataFrame(event_rows), on=IDENTITY, validate="many_to_one")
            phase_tables.append(("pooled_adaptive", pooled))
            unchanged = confirm.loc[[tuple(row) not in ext_keys for row in confirm[IDENTITY].itertuples(index=False, name=None)]].assign(extended_source=False)
            for label, refined in [("extension_substitution_sensitivity", extend),
                                   ("pooled_substitution_sensitivity", pooled)]:
                mixed = pd.concat([unchanged, refined.assign(extended_source=True)], ignore_index=True)
                require(not mixed.duplicated(PROFILE_KEY).any() and identities(mixed, PROFILE_KEY) == identities(confirm, PROFILE_KEY), "Sensitivity substitution changed source coverage")
                routes.append(route_summary(mixed, members, label))
    compact = []
    for phase, table in phase_tables:
        fields = [*PROFILE_KEY, "replicate_count", "sample_supported", *METRICS,
                  *[c for c in table if any(c.startswith(f"{event}_") for event in EVENTS) and not c.endswith(("_mean", "_median"))]]
        compact.append(table[list(dict.fromkeys(fields))].assign(phase=phase))
    pd.concat(compact, ignore_index=True).to_csv(output_dir / "source_metrics.csv", index=False, float_format="%.12g")
    pd.concat(routes, ignore_index=True).to_csv(output_dir / "route_summary.csv", index=False, float_format="%.12g")
    outputs += ["source_metrics.csv", "route_summary.csv"]
    receipt = {"scope": "fixed_prior_pool_screen_and_independent_process_confirmation", "inputs": input_bindings,
               "analysis_bindings": {name: binding(ROOT / "scripts" / name) for name in
                   [Path(__file__).name, "summarize_observation_repair_pilot.py", "run_observation_repair_pilot.py"]},
               "confirmation_sources": len(candidates),
               "phases": [phase for phase, _ in phase_tables],
               "interpretation": "Uniform initial confirmation is primary. Extension-only and adaptive pooled results retain original selections. Source means are equal-weight conditional scenarios, not posterior probabilities. High ESS does not exclude unseen rare histories.",
               "outputs": {name: binding(output_dir / name) for name in outputs}}
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ["confirmation_sources", "phases"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-dir", type=Path, required=True)
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/terminal_history_screen")
    parser.add_argument("--confirm-dir", type=Path)
    parser.add_argument("--extend-dir", type=Path)
    analyse(**vars(parser.parse_args()))
