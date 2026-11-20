#!/usr/bin/env python3
"""Compact reporting from the verified, frozen common-model production archive.

No simulation, source selection, likelihood fitting or cross-q ranking occurs.
The permissive slice is descriptive; compatibility_map.csv retains every cutoff.
"""
from pathlib import Path
import hashlib
import json
import shutil

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "outputs/remote/common_model_20260918/production"
OUT = ROOT / "data/common_model"


def hashed(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads((OUT / "retrieval_receipt.json").read_text())
    analysis = ARCHIVE / "analysis"
    names = ["compatibility_map.csv", "validated_source_profiles.csv",
             "overshoot_counterfactual_contrasts.csv"]
    for name in names:
        assert hashed(analysis / name) == receipt["files"]["analysis/" + name]["sha256"]
    m, s, contrasts = [pd.read_csv(analysis / name, float_precision="round_trip") for name in names]
    primary = m.loc[m.observation_model.isin(["homogeneous", "shared_quality"])]
    witnesses = s.loc[s.primary_profile & s.joint_mc_qualified
                      & s.early_pattern_lower95.ge(.5) & s.joint_lower95.ge(1e-6)]
    keys = ["configuration", "restriction", "q", "observation_model"]
    ranges = witnesses.groupby(keys).agg(
        source_count=("source_id", "nunique"), search_seed_count=("search_seed", "nunique"),
        K_R_min=("K_R", "min"), K_R_max=("K_R", "max"),
        PR011_min=("PR011", "min"), PR011_max=("PR011", "max"),
        K_R_over_PR011_min=("K_R_over_PR011", "min"), K_R_over_PR011_max=("K_R_over_PR011", "max"),
        PR033_min=("PR033", "min"), PR033_max=("PR033", "max"),
        factual_weighted_survival_min=("weighted_terminal_survival", "min"),
        factual_weighted_survival_max=("weighted_terminal_survival", "max"))
    ranges.to_csv(OUT / "qualified_profile_ranges.csv", float_format="%.17g")
    primary.groupby(["configuration", "restriction", "status"]).size().unstack(fill_value=0).to_csv(
        OUT / "compatibility_primary_counts.csv")
    shutil.copyfile(analysis / "compatibility_map.csv", OUT / "compatibility_map.csv")
    c = contrasts.merge(witnesses[["source_id", "q", "observation_model", "configuration"]],
                        on=["source_id", "q", "observation_model"], validate="many_to_one")
    c.groupby(["configuration", "endpoint", "contrast_status"]).agg(
        profile_count=("source_id", "size"),
        defined_estimate_count=("weighted_counterfactual_minus_factual", "count"),
        estimate_min=("weighted_counterfactual_minus_factual", "min"),
        estimate_max=("weighted_counterfactual_minus_factual", "max")).to_csv(
            OUT / "counterfactual_qualified_profile_ranges.csv", float_format="%.17g")
    result = {
        "scope": "descriptive reporting of frozen validation; no reselection or new simulation",
        "primary_map_status_counts": primary.status.value_counts().to_dict(),
        "diagnostic_map_status_counts": m.loc[m.observation_model.eq("independent_quality")].status.value_counts().to_dict(),
        "primary_capacity_labels": primary.capacity_support_label.value_counts().to_dict(),
        "permissive_cutoffs": {"early_lower95": .5, "joint_lower95": 1e-6},
        "permissive_primary_source_profiles": len(witnesses),
        "permissive_primary_unique_sources": witnesses.source_id.nunique(),
        "q_0005_primary_cells_with_witnesses": len(ranges.loc[pd.IndexSlice[:, :, .005, :], :]),
        "q_0005_primary_cells_minimum_search_seed_count": int(ranges.loc[pd.IndexSlice[:, :, .005, :], "search_seed_count"].min()),
        "q_0005_primary_cells_with_K_R_ge20": len(witnesses.loc[witnesses.q.eq(.005) & witnesses.K_R.ge(20)].groupby(keys)),
        "primary_MC_qualified_profiles_by_q_and_law": s.loc[s.primary_profile].groupby(["q", "observation_model"]).joint_mc_qualified.sum().reset_index().to_dict("records"),
        "inputs": {name: hashed(analysis / name) for name in names},
    }
    (OUT / "results_summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
