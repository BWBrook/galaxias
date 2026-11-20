#!/usr/bin/env python3
"""Score a verified abundance replay on fixed, existing source cohorts."""
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
from scripts.run_conditional_calibration import IDENTITY, file_hash, require
from galaxias_model.abundance_detection import (
    EPISODE_FIELDS, OBSERVATION_MODELS, Q_SCENARIOS,
    history_log_likelihood, summarize_log_likelihood,
)
from galaxias_model.conditional_observation import CONDITIONAL_PROFILES


def old_profile_logs(frame, profile):
    p, dependence = CONDITIONAL_PROFILES[profile]
    abundances = frame[list(EPISODE_FIELDS)].to_numpy(dtype=float)
    positive = (abundances[:, :6] > 0).all(axis=1)
    lake = (abundances[:, 6:8] > 0).sum(axis=1)
    natural = (abundances[:, 8:] > 0).sum(axis=1)
    k = (lake > 0).astype(int) + (natural > 0).astype(int) if dependence == "shared_window" else lake + natural
    return np.where(positive, k * math.log1p(-p), -math.inf)


def summarize_cohorts(sources, members):
    global_members = members.loc[members.cohort.eq("global")]
    references = {
        "all_validated": sources[IDENTITY].drop_duplicates(),
        "global_union": global_members[IDENTITY].drop_duplicates(),
        "presence_only_global": global_members.loc[global_members.profile.eq("repair_presence_only"), IDENTITY].drop_duplicates(),
    }
    rows = []
    for name, ids in references.items():
        data = ids.merge(sources, on=IDENTITY, validate="one_to_many")
        for (seed, profile), group in data.groupby(["search_seed", "observation_profile"], sort=True):
            result = {"reference_cohort": name, "search_seed": seed, "observation_profile": profile,
                      "n_sources": len(group), "n_weight_precision_qualified": int(group.mc_qualified.sum()),
                      "weight_ess_median": group.weight_ess.median(),
                      "mc_relative_se_median": group.mc_relative_se.median()}
            for endpoint in ("surviving_2002", "n_total_2002"):
                valid = np.isfinite(group[f"weighted_{endpoint}"])
                result[f"n_supported_{endpoint}"] = int(valid.sum())
                result[f"unconditional_{endpoint}"] = group[f"unconditional_{endpoint}"].mean()
                result[f"weighted_{endpoint}"] = group.loc[valid, f"weighted_{endpoint}"].mean()
                result[f"weighted_{endpoint}_mc_se"] = (
                    math.sqrt(float(np.square(group.loc[valid, f"weighted_{endpoint}_mc_se"]).sum())) / valid.sum()
                    if valid.any() else math.nan
                )
            rows.append(result)
    return pd.DataFrame(rows)


def analyze(replay_dir, membership, output_dir):
    require(not output_dir.exists(), "Output already exists")
    manifest_path = replay_dir / "replay_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    require(manifest["status"] == "complete" and manifest["scope"] == "conditional_detection_replay_preparation", "Incomplete/wrong replay")
    for name, expected in manifest["outputs"].items():
        require(Path(name).name == name, "Replay outputs must use direct filenames")
        require(file_hash(replay_dir / name) == expected, f"Replay hash mismatch: {name}")
    expected = manifest["inputs"]["membership"]
    require(file_hash(membership) == {key: expected[key] for key in ("bytes", "sha256")}, "Frozen membership changed")
    members = pd.read_csv(membership)
    wanted = set(members[IDENTITY].itertuples(index=False, name=None))
    seen, rows = set(), []
    n = manifest["replicates"]
    require(type(n) is int and n > 0, "Invalid replay replicate count")
    for frame in pd.read_csv(replay_dir / "compact_abundance_replay.csv.gz", chunksize=n, float_precision="round_trip"):
        ids = frame[IDENTITY].drop_duplicates()
        require(len(ids) == 1 and len(frame) == n, "Replay source blocks are incomplete")
        identity = tuple(ids.iloc[0])
        require(identity in wanted and identity not in seen, "Replay source coverage mismatch")
        seen.add(identity)
        endpoints = {name: frame[name].to_numpy(dtype=float) for name in ("surviving_2002", "n_total_2002")}
        for q in Q_SCENARIOS:
            for model in OBSERVATION_MODELS:
                rows.append({**dict(zip(IDENTITY, identity)), "observation_profile": f"q_{q:g}_{model}",
                             "q": q, "observation_model": model,
                             **summarize_log_likelihood(history_log_likelihood(frame, q, model), endpoints)})
        for profile in CONDITIONAL_PROFILES:
            rows.append({**dict(zip(IDENTITY, identity)), "observation_profile": profile, "q": math.nan,
                         "observation_model": "legacy_occupancy",
                         **summarize_log_likelihood(old_profile_logs(frame, profile), endpoints)})
    require(seen == wanted and len(seen) == manifest["source_count"], "Missing replay sources")
    sources = pd.DataFrame(rows)
    cohorts = summarize_cohorts(sources, members)
    output_dir.mkdir(parents=True)
    sources.to_csv(output_dir / "source_observation_comparison.csv", index=False)
    cohorts.to_csv(output_dir / "fixed_cohort_comparison.csv", index=False)
    receipt = {"status": "complete", "scope": "fixed_source_detection_sensitivity",
               "replay_manifest": file_hash(manifest_path), "membership": file_hash(membership),
               "source_files": {str(path.relative_to(ROOT)): file_hash(path) for path in
                                (Path(__file__), ROOT / "src/galaxias_model/abundance_detection.py",
                                 ROOT / "src/galaxias_model/conditional_observation.py", ROOT / "docs/common_model_protocol.md")},
               "source_count": len(seen), "source_profile_rows": len(sources),
               "selection": "Frozen old cohorts only; no parameter reselection; no new process evidence.",
               "outputs": {path.name: file_hash(path) for path in output_dir.iterdir()}}
    (output_dir / "analysis_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"sources": len(seen), "source_profile_rows": len(sources)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("replay-dir", "membership", "output-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    analyze(**vars(parser.parse_args()))
