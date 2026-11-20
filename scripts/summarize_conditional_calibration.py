#!/usr/bin/env python3
"""Compact cross-phase evidence after fixed stochastic validation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.analyze_conditional_calibration import IDENTITY, KEY, context_summary, file_hash, require


def read_analysis(directory, phase):
    manifest = json.loads((directory / "analysis_manifest.json").read_text())
    require(manifest["status"] == "complete" and manifest["phase"] == phase, "Wrong/incomplete analysis")
    for name, expected in manifest["outputs"].items():
        require(file_hash(directory / name) == expected, f"Analysis binding mismatch: {name}")
    return pd.read_csv(directory / "verified_sources.csv", float_precision="round_trip"), manifest


def summarize(screen_dir, refine_dir, validate_dir, prior_dir, output_dir):
    output_dir.mkdir(parents=True, exist_ok=False)
    tables, manifests = {}, {}
    for phase, directory in [("screen", screen_dir), ("refine", refine_dir), ("validate", validate_dir)]:
        tables[phase], manifests[phase] = read_analysis(directory, phase)
    screening_members = pd.read_csv(screen_dir / "selection_membership.csv")
    final_members = pd.read_csv(refine_dir / "selection_membership.csv")
    require(manifests["refine"]["previous_membership"] == file_hash(screen_dir / "selection_membership.csv"), "Refinement membership ancestry")
    require(manifests["validate"]["final_membership"] == file_hash(refine_dir / "selection_membership.csv"), "Validation membership ancestry")
    prior_manifest = json.loads((prior_dir / "run_manifest.json").read_text())
    for name in ("parameter_values.csv.gz", "sources.csv"):
        require(file_hash(prior_dir / name) == prior_manifest["outputs"][name], f"Prior binding mismatch: {name}")
    sources = pd.read_csv(prior_dir / "sources.csv")
    parameters = pd.read_csv(prior_dir / "parameter_values.csv.gz", float_precision="round_trip")
    contexts = pd.concat([context_summary(table, final_members) for table in tables.values()], ignore_index=True)
    contexts.to_csv(output_dir / "context_comparison.csv", index=False)
    final_members.to_csv(output_dir / "selection_membership.csv", index=False)

    metrics = ["overall_distance", "score_weight1", "early_distance", "intrinsic_distance", "late_discrepancy",
               "positive_compatible_fraction", "mean_joint_compatibility", "weight_ess", "mc_relative_se",
               "largest_weight_share", "mc_qualified", "surviving_2002_mean", "n_total_1995_mean", "n_total_1996_mean",
               "n_total_2002_mean", "compatibility_weighted_surviving_2002", "compatibility_weighted_surviving_2002_mc_se",
               "compatibility_weighted_n_total_2002", "compatibility_weighted_n_total_2002_mc_se",
               "positive_and_extinct_by_2002_count", "positive_and_all_nondetections_empty_count"]
    comparisons = final_members.copy()
    for phase, table in tables.items():
        comparisons = comparisons.merge(table[[*KEY, *metrics]].rename(columns={c: f"{phase}_{c}" for c in metrics}), on=KEY, validate="many_to_one")
    admission = screening_members.groupby(KEY).selection_rank.min().rename("screen_admission_best_rank").reset_index()
    comparisons = comparisons.merge(admission, on=KEY, validate="many_to_one")
    comparisons["validation_minus_refinement_score"] = comparisons.validate_overall_distance - comparisons.refine_overall_distance
    comparisons.to_csv(output_dir / "selected_source_comparison.csv", index=False)

    screen = tables["screen"].merge(sources[[*IDENTITY, "proposal_index"]], on=IDENTITY, validate="many_to_one")
    discovery = []
    for keys, group in screen.groupby(["search_seed", "family_id", "profile"], sort=True):
        for cutoff in (50, 100, 250, 500):
            part = group.loc[group.proposal_index.le(cutoff)]
            if len(part) == 0:
                continue
            finite = part.loc[part.finite_supported]
            discovery.append({**dict(zip(["search_seed", "family_id", "profile"], keys)), "proposal_cutoff": cutoff,
                              "n_sources": len(part), "n_sample_supported": len(finite),
                              "sample_supported_fraction": len(finite) / len(part),
                              "best_overall_distance": part.overall_distance.min(),
                              "finite_score_q10": finite.overall_distance.quantile(.1),
                              "best_score_weight1": part.score_weight1.min(),
                              "terminal_supported_sources": int(part.positive_and_extinct_by_2002_count.gt(0).sum()),
                              "all_empty_supported_sources": int(part.positive_and_all_nondetections_empty_count.gt(0).sum())})
    pd.DataFrame(discovery).to_csv(output_dir / "discovery_curves.csv", index=False)

    priors = pd.read_csv(ROOT / "data/parameter_priors.csv")
    chosen = final_members.merge(parameters, on=IDENTITY, validate="many_to_many")
    chosen = chosen.loc[chosen.sampled_flag].merge(priors[["parameter_id", "parameter_name", "lower_bound", "upper_bound"]], on="parameter_id", validate="many_to_one")
    width = chosen.upper_bound - chosen.lower_bound
    chosen["relative_position"] = (chosen.value_natural - chosen.lower_bound) / width
    chosen["near_lower"] = chosen.relative_position.le(.05)
    chosen["near_upper"] = chosen.relative_position.ge(.95)
    parameter_summary = chosen.groupby(["search_seed", "family_id", "profile", "cohort", "parameter_id", "parameter_name"], sort=True).agg(
        n_sources=("value_natural", "size"), value_min=("value_natural", "min"), value_median=("value_natural", "median"),
        value_max=("value_natural", "max"), near_lower_fraction=("near_lower", "mean"), near_upper_fraction=("near_upper", "mean")).reset_index()
    parameter_summary.to_csv(output_dir / "parameter_diagnostics.csv", index=False)
    receipt = {"status": "complete", "source": file_hash(Path(__file__)),
               "analyses": {phase: file_hash(directory / "analysis_manifest.json") for phase, directory in [("screen", screen_dir), ("refine", refine_dir), ("validate", validate_dir)]},
               "prior_manifest": file_hash(prior_dir / "run_manifest.json"),
               "counts": {"prior_sources": len(sources), "refinement_sources": len(tables["refine"][IDENTITY].drop_duplicates()),
                          "validation_sources": len(tables["validate"][IDENTITY].drop_duplicates())},
               "outputs": {path.name: file_hash(path) for path in output_dir.iterdir() if path.is_file()}}
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt["counts"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("screen_dir", "refine_dir", "validate_dir", "prior_dir", "output_dir"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    summarize(**vars(parser.parse_args()))
