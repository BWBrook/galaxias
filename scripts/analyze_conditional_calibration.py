#!/usr/bin/env python3
"""Verify conditional calibration archives, freeze selection, and compare phases."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_observation_repair_pilot import file_hash, IDENTITY, ORDER
from galaxias_model.conditional_observation import CONDITIONAL_PROFILES, PHYSICS

KEY = [*IDENTITY, "profile"]
EVENTS = ["positive_records_compatible", "positive_and_extinct_by_2002",
          "positive_and_all_natural_nondetections_empty", "positive_and_all_nondetections_empty"]


def require(value, message):
    if not value:
        raise ValueError(message)


def close(actual, expected, label):
    require(np.allclose(actual, expected, rtol=1e-9, atol=1e-10, equal_nan=True), f"Summary mismatch: {label}")


def verify_phase(directory):
    """Stream one source at a time; independently recompute decisive metrics."""
    manifest = json.loads((directory / "run_manifest.json").read_text())
    require(manifest["status"] == "complete", "Incomplete phase archive")
    for name, expected in manifest["outputs"].items():
        require(Path(name).name == name and file_hash(directory / name) == expected, f"Archive binding mismatch: {name}")
    summary = pd.read_csv(directory / "source_summary.csv", float_precision="round_trip")
    require(not summary.duplicated(KEY).any(), "Duplicate summary identity")
    lookup = summary.set_index(KEY)
    n = manifest["replicates"]
    seen, additions = set(), []
    for raw in pd.read_csv(directory / "raw_replicates.csv.gz", chunksize=n, float_precision="round_trip"):
        require(len(raw) == n and len(raw[IDENTITY].drop_duplicates()) == 1, "Noncontiguous or incomplete source")
        identity = tuple(raw.iloc[0][IDENTITY])
        require(identity not in seen, "Duplicate raw source")
        seen.add(identity)
        require(set(raw.replicate_index) == set(range(1, n + 1)), "Missing replicate index")
        require(raw.stage.eq(manifest["phase"]).all(), "Wrong raw phase")
        lake, natural = raw.lake_nondetection_occupied_episodes, raw.natural_nondetection_occupied_episodes
        require(lake.between(0, 2).all() and natural.between(0, 5).all(), "Invalid episode bounds")
        close(raw.nondetection_occupied_episodes, lake + natural, "episode sum")
        positive = raw.positive_records_compatible.to_numpy(dtype=bool)
        require(raw.positive_records_compatible.isin([True, False]).all(), "Nonboolean support")
        close(raw.positive_and_extinct_by_2002, positive & ~raw.surviving_2002.astype(bool), "terminal event")
        close(raw.positive_and_all_natural_nondetections_empty, positive & natural.eq(0), "empty natural surveys")
        close(raw.positive_and_all_nondetections_empty, positive & (lake + natural).eq(0), "empty all surveys")
        require((raw.first_zero_year.isna() == ~raw.extinct_by_2002.astype(bool)).all(), "First-zero censoring")
        extinct = raw.first_zero_year.notna()
        require(raw.loc[extinct, "first_zero_year"].between(1965, 2002).all(), "First-zero bounds")
        observed = extinct & raw.latent_last_presence_year.notna()
        require((raw.loc[observed, "latent_last_presence_year"] < raw.loc[observed, "first_zero_year"]).all(), "Extinction not absorbing")
        early = raw[[f"CT{i:03d}_weighted_penalty" for i in range(1, 6)]].sum(axis=1).to_numpy()
        intrinsic = raw[[f"CT{i:03d}_weighted_penalty" for i in (11, 12)]].sum(axis=1).to_numpy()
        close(intrinsic, intrinsic[0], "intrinsic cache")
        events = {}
        for event in EVENTS:
            count = int(raw[event].sum())
            events.update({f"{event}_count": count, f"{event}_fraction": count / n,
                           f"{event}_zero_upper95": -math.expm1(math.log(.05) / n) if count == 0 else math.nan})
        for profile, (p, dependence) in CONDITIONAL_PROFILES.items():
            reported = lookup.loc[(*identity, profile)]
            k = (lake.gt(0).astype(int) + natural.gt(0).astype(int)) if dependence == "shared_window" else lake + natural
            w = positive * np.power(1 - p, k.to_numpy())
            total = w.sum()
            late = -math.log(w.mean()) if total else math.inf
            ess = total**2 / np.dot(w, w) if total else 0.
            relative = w.std(ddof=1) / math.sqrt(n) / w.mean() if total and n > 1 else math.nan
            metrics = {"replicate_count": n, "late_discrepancy": late,
                       "positive_compatible_count": int(positive.sum()), "positive_compatible_fraction": positive.mean(),
                       "mean_joint_compatibility": w.mean(), "weight_ess": ess,
                       "mc_relative_se": relative, "largest_weight_share": w.max() / total if total else math.nan,
                       "early_distance": np.median(early), "intrinsic_distance": intrinsic[0],
                       "overall_distance": np.median(early + intrinsic) + 5 * late}
            for field in PHYSICS:
                metrics[f"compatibility_weighted_{field}"] = np.dot(w, raw[field]) / total if total else math.nan
            for field, value in metrics.items():
                close(reported[field], value, f"{identity}/{profile}/{field}")
            endpoint_se = {}
            for field in PHYSICS:
                estimate = metrics[f"compatibility_weighted_{field}"]
                influence = w * (raw[field].to_numpy() - estimate)
                endpoint_se[f"compatibility_weighted_{field}_mc_se"] = influence.std(ddof=1) / math.sqrt(n) / w.mean() if total and n > 1 else math.nan
            additions.append({**dict(zip(KEY, (*identity, profile))), **events, **endpoint_se,
                              "mc_qualified": bool(total > 0 and ess >= 100 and relative <= .10 and w.max() / total <= .05)})
    require(seen == set(summary[IDENTITY].itertuples(index=False, name=None)), "Raw/summary source coverage mismatch")
    require(len(seen) == manifest["source_count"] and len(summary) == len(seen) * len(CONDITIONAL_PROFILES), "Manifest source/profile counts")
    verified = summary.merge(pd.DataFrame(additions), on=KEY, validate="one_to_one")
    verified["score_weight1"] = verified.early_distance + verified.intrinsic_distance + verified.late_discrepancy
    return verified, manifest


def select_membership(summary, global_cap, family_cap, previous=None):
    """Ranks only screen/refine data, within each profile's admitted candidates."""
    require(set(summary.stage).issubset({"screen", "refine"}), "Validation cannot select sources")
    candidates = summary
    if previous is not None:
        candidates = candidates.merge(previous[KEY].drop_duplicates(), on=KEY, validate="one_to_one")
    rows = []
    for _, context in candidates.loc[candidates.finite_supported].groupby(["search_seed", "profile"], sort=True):
        ordered = context.sort_values(ORDER).copy()
        ordered["selection_rank"] = np.arange(1, len(ordered) + 1)
        alternative = context.copy()
        alternative["overall_distance"] = alternative.early_distance + alternative.intrinsic_distance + alternative.late_discrepancy
        alternative["historical_distance"] = alternative.early_distance + alternative.late_discrepancy
        alternative = alternative.sort_values(ORDER)
        alternative["selection_rank"] = np.arange(1, len(alternative) + 1)
        for cohort, chosen in [("global", ordered.head(global_cap)), ("family", ordered.groupby("family_id", sort=True).head(family_cap)),
                               ("weight1_family", alternative.groupby("family_id", sort=True).head(family_cap))]:
            for row in chosen[[*KEY, "selection_rank", "overall_distance"]].to_dict("records"):
                rows.append({**row, "cohort": cohort})
    return pd.DataFrame(rows, columns=[*KEY, "selection_rank", "overall_distance", "cohort"]).sort_values(["cohort", *KEY])


def freeze_csv(path, table):
    payload = table.to_csv(index=False, float_format="%.17g")
    if path.exists():
        require(path.read_text() == payload, f"Frozen output changed: {path}")
    else:
        path.write_text(payload)


def context_summary(summary, members):
    chosen = members[[*KEY, "cohort"]].merge(summary, on=KEY, how="left", validate="many_to_one")
    require(chosen.replicate_count.notna().all(), "Missing frozen source")
    fields = ["overall_distance", "score_weight1", "early_distance", "intrinsic_distance", "late_discrepancy",
              "positive_compatible_fraction", "mean_joint_compatibility", "weight_ess", "mc_relative_se",
              "surviving_2002_mean", "compatibility_weighted_surviving_2002", "n_total_2002_mean",
              "compatibility_weighted_n_total_2002", *[f"{event}_fraction" for event in EVENTS[1:]]]
    rows = []
    for keys, group in chosen.groupby(["search_seed", "profile", "cohort"], sort=True):
        for family in ["all_families", *sorted(group.family_id.unique())]:
            part = group if family == "all_families" else group.loc[group.family_id.eq(family)]
            row = dict(zip(["search_seed", "profile", "cohort"], keys))
            row.update(stage=part.stage.iloc[0], family_id=family, n_sources=len(part), n_supported=int(part.sample_supported.sum()), n_mc_qualified=int(part.mc_qualified.sum()))
            for field in fields:
                values = part[field]
                row.update({f"{field}_mean": values.mean(), f"{field}_median": values.median(), f"{field}_n": int(values.notna().sum())})
            for field in PHYSICS:
                errors = part[f"compatibility_weighted_{field}_mc_se"].dropna()
                row[f"compatibility_weighted_{field}_mean_mc_se"] = float(np.sqrt(np.square(errors).sum()) / len(errors)) if len(errors) else math.nan
            rows.append(row)
    return pd.DataFrame(rows)


def analyse(directory, output_dir, previous_path=None, members_path=None):
    output_dir.mkdir(parents=True, exist_ok=True)
    summary, manifest = verify_phase(directory)
    freeze_csv(output_dir / "verified_sources.csv", summary)
    phase = manifest["phase"]
    outputs = ["verified_sources.csv"]
    if phase in {"screen", "refine"}:
        previous = pd.read_csv(previous_path) if previous_path else None
        require(phase != "refine" or previous is not None, "Refinement requires profile-specific screening membership")
        members = select_membership(summary, 100 if phase == "screen" else 50, 5 if phase == "screen" else 3, previous)
        freeze_csv(output_dir / "selection_membership.csv", members)
        freeze_csv(output_dir / "candidates.csv", members[IDENTITY].drop_duplicates().sort_values(IDENTITY))
        outputs.extend(["selection_membership.csv", "candidates.csv"])
    else:
        require(phase == "validate" and members_path is not None, "Validation requires frozen final membership")
        members = pd.read_csv(members_path)
    freeze_csv(output_dir / "context_summary.csv", context_summary(summary, members))
    outputs.append("context_summary.csv")
    record = {"status": "complete", "phase": phase, "phase_manifest": file_hash(directory / "run_manifest.json"),
              "analysis_source": file_hash(Path(__file__)),
              "previous_membership": file_hash(previous_path) if previous_path else None,
              "final_membership": file_hash(members_path) if members_path else None,
              "outputs": {name: file_hash(output_dir / name) for name in outputs}}
    (output_dir / "analysis_manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"phase": phase, "verified_sources": manifest["source_count"], "selected_union": len(members[IDENTITY].drop_duplicates())}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--previous-membership", type=Path)
    parser.add_argument("--final-membership", type=Path)
    args = parser.parse_args()
    analyse(args.phase_dir, args.output_dir, args.previous_membership, args.final_membership)
