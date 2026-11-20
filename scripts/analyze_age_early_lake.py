#!/usr/bin/env python3
"""Frozen synthetic recovery gate for the separate pre-1990 Lake question.

No historical observation file is loaded by this program.  Every synthetic
observation, score, rank and held-out set is saved for independent replay.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import csv
import gzip
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import sys
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from galaxias_model.age_early_lake import generate_lake_observation, keyed_seed
from galaxias_model.age_early_recovery import (
    RESTRICTIONS, bank_log_support, restriction_sets, summarise_test_sets,
)

PROFILES = {
    "primary": {"age1": 0.0, "power": 1 / 12, "generator": "primary"},
    "age_accessibility": {"age1": 1.0, "power": 1 / 12, "generator": "age_accessibility"},
    "score_concentration": {"age1": 0.0, "power": 1 / 4, "generator": "primary"},
    "site_trip_quality": {"age1": 0.0, "power": 1 / 12, "generator": "site_trip_quality"},
}
BANKS = ("full", "half_a", "half_b")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.generic):
        return jsonable(value.item())
    if isinstance(value, float) and math.isnan(value):
        raise ValueError("NaN cannot be serialized as an assessment")
    if isinstance(value, float) and not math.isfinite(value):
        return "-Infinity" if value < 0 else "Infinity"
    return value


def write_json(path, value):
    Path(path).write_text(json.dumps(jsonable(value), indent=2, sort_keys=True, allow_nan=False) + "\n")


def write_gzip_json(path, value):
    payload = (json.dumps(jsonable(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    with Path(path).open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as handle:
            handle.write(payload)
    return {"sha256": sha256(path), "content_sha256": hashlib.sha256(payload).hexdigest()}


def read_rows(path):
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle]


def source_halves(source_ids):
    """Split within an already selected index stratum, preserving whole sources."""
    if len(source_ids) < 2 or len(set(source_ids)) != len(source_ids):
        raise ValueError("bank split needs at least two distinct source identities")
    order = sorted(range(len(source_ids)), key=lambda i: keyed_seed("early-lake-halves-v1", source_ids[i]))
    first = np.zeros(len(source_ids), dtype=bool)
    first[order[::2]] = True
    return {"full": np.ones(len(source_ids), dtype=bool), "half_a": first, "half_b": ~first}


def synthetic_observation(row, profile):
    settings = PROFILES[profile]
    # Pair restrictions and PR032 regimes.  Concentration uses exactly the
    # primary observation; only its subsequent score power changes.
    seed = keyed_seed("early-lake-observation-v1", row["source_id"], row["role"],
                      int(row["replicate"]), settings["generator"])
    observation = generate_lake_observation(
        row["lake_exposures"], seed=seed, age1=settings["age1"],
        gamma_quality=settings["generator"] == "site_trip_quality",
    )
    return {
        "source_id": row["source_id"], "source_index": row["source_index"],
        "role": row["role"], "true_restriction": row["restriction"],
        "means": observation["visit_means"], "raw_site_counts": observation["raw_site_counts"],
        "seed": seed, "early_positive": bool(np.any(observation["visit_means"][:5] > 0)),
        "all_zero_exposure": bool(observation["all_zero_exposure"]),
    }


def bank_arrays(rows):
    ids = sorted({row["source_id"] for row in rows})
    positions = {source_id: i for i, source_id in enumerate(ids)}
    n_rep = max(int(row["replicate"]) for row in rows) + 1
    features = np.zeros((4, len(ids), n_rep, 8, 2))
    valid = np.zeros((4, len(ids), n_rep), dtype=bool)
    seen = set()
    for row in rows:
        key = (RESTRICTIONS.index(row["restriction"]), positions[row["source_id"]], int(row["replicate"]))
        if key in seen:
            raise ValueError("duplicate bank slot")
        seen.add(key)
        valid[key] = bool(row["valid"])
        features[key] = row["lake_exposures"]
    if len(seen) != valid.size:
        raise ValueError("missing planned bank slot")
    return ids, features, valid


def assess_group(task):
    group, rows, output_path = task
    profile = group["profile"]
    settings = PROFILES[profile]
    bank_rows = [row for row in rows if row["role"] == "bank"]
    source_ids, features, valid = bank_arrays(bank_rows)
    masks = source_halves(source_ids)
    unexpected = [row for row in rows if row["status"] not in ("valid", "algebraically_infeasible")]
    observations = {role: [synthetic_observation(row, profile) for row in rows
                           if row["role"] == role and row["valid"]]
                    for role in ("calibration", "test")}
    selected = {role: [row for row in observations[role] if row["early_positive"]] for role in observations}
    counts = {}
    for role in observations:
        counts[role] = {}
        for label in RESTRICTIONS:
            attempted = [r for r in rows if r["role"] == role and r["restriction"] == label]
            generated = [r for r in observations[role] if r["true_restriction"] == label]
            counts[role][label] = {
                "attempted": len(attempted), "valid": len(generated),
                "algebraically_infeasible": sum(r["status"] == "algebraically_infeasible" for r in attempted),
                "unexpected_process_failure": sum(r["status"] not in ("valid", "algebraically_infeasible") for r in attempted),
                "z1": sum(r["early_positive"] for r in generated),
                "z0_full_set": sum(not r["early_positive"] for r in generated),
            }
    result = {**group, "counts": counts, "bank_sources": len(source_ids),
              "bank_status_counts": dict(Counter(r["status"] for r in bank_rows)),
              "unexpected_process_failures": len(unexpected), "banks": {}, "stability": {},
              "informative_pairs": [], "reasons": []}
    if unexpected:
        result["reasons"].append("unexpected_process_failure")
    if any(counts["calibration"][r]["z1"] < 39 or counts["test"][r]["z1"] == 0 for r in RESTRICTIONS):
        result["reasons"].append("insufficient_conditional_sample")
    details = {"group": group, "bank_source_ids": source_ids, "bank_masks": masks,
               "observations": observations, "scored_z1": selected, "banks": {}}
    # Still compute scores for small but nonempty groups; mark the resulting
    # ranks unqualified, without adding sources to improve the sample size.
    all_nonempty = all(counts[role][r]["z1"] > 0 for role in counts for r in RESTRICTIONS)
    predicted = {}
    if all_nonempty:
        means_cal = np.asarray([r["means"] for r in selected["calibration"]])
        means_test = np.asarray([r["means"] for r in selected["test"]])
        true_cal = np.asarray([r["true_restriction"] for r in selected["calibration"]])
        true_test = np.asarray([r["true_restriction"] for r in selected["test"]])
        all_means = np.concatenate((means_cal, means_test))
        for bank, mask in masks.items():
            ell = bank_log_support(features, all_means, valid=valid, source_mask=mask,
                                   power=settings["power"], age1=settings["age1"], batch_size=64)
            ell_cal, ell_test = ell[:len(means_cal)], ell[len(means_cal):]
            cal_by_true = {label: ell_cal[true_cal == label] for label in RESTRICTIONS}
            evaluated = restriction_sets(cal_by_true, ell_test)
            predicted[bank] = evaluated["sets"]
            summary = summarise_test_sets({label: evaluated["sets"][true_test == label] for label in RESTRICTIONS})
            support = {label: float(evaluated["supported"][true_test == label].mean()) for label in RESTRICTIONS}
            empty = {label: int((~evaluated["sets"][true_test == label].any(axis=1)).sum()) for label in RESTRICTIONS}
            result["banks"][bank] = {"coverage": summary["coverage"], "directed": summary["directed"],
                                     "support_fraction": support, "empty_sets": empty,
                                     "selected_source_count": int(mask.sum())}
            details["banks"][bank] = {"ell_calibration": ell_cal, "ell_test": ell_test, **evaluated}
        for first, second in (("full", "half_a"), ("full", "half_b"), ("half_a", "half_b")):
            comparison = {}
            for i, label in enumerate(RESTRICTIONS):
                selected_class = true_test == label
                a, b = predicted[first][selected_class], predicted[second][selected_class]
                comparison[label] = {"set_agreement": float(np.all(a == b, axis=1).mean()),
                                     "coverage_gap": abs(float(a[:, i].mean()) - float(b[:, i].mean()))}
            result["stability"][f"{first}:{second}"] = comparison
        if any(x < .95 for bank in result["banks"].values() for x in bank["support_fraction"].values()):
            result["reasons"].append("bank_support")
        if any(x["set_agreement"] < .90 or x["coverage_gap"] > .05 + 1e-12
               for c in result["stability"].values() for x in c.values()):
            result["reasons"].append("bank_half_instability")
        coverage = [x for bank in result["banks"].values() for x in bank["coverage"].values()]
        if any(x["lower"] < .90 for x in coverage):
            result["reasons"].append("coverage_failed" if any(x["upper"] < .90 for x in coverage)
                                     else "coverage_precision_unassessed")
        pair_sets = [{key for key, value in bank["directed"].items() if value["lower"] > .5}
                     for bank in result["banks"].values()]
        result["informative_pairs"] = sorted(set.intersection(*pair_sets))
    result["qualified"] = not result["reasons"]
    result["status"] = "QUALIFIED" if result["qualified"] else "UNASSESSED"
    if "coverage_failed" in result["reasons"]:
        result["status"] = "COVERAGE_FAILED"
    details["assessment"] = result
    output = Path(output_path)
    result["detail_file"] = output.name
    result["detail_hashes"] = write_gzip_json(output, details)
    return result


def gate_decision(groups):
    primary = [g for g in groups if g["maximum_age"] == 6]
    if len(primary) != 16:
        raise ValueError("the primary gate requires exactly sixteen groups")
    pair_sets = [set(g["informative_pairs"]) for g in primary]
    robust_pairs = sorted(set.intersection(*pair_sets))
    if not all(g["qualified"] for g in primary):
        status = "STOP_EARLY_RECOVERY_UNASSESSED"
    elif not robust_pairs:
        status = "STOP_EARLY_RECOVERY_LOW_INFORMATION"
    else:
        status = "GO_ELIGIBLE_EARLY_COMPARISON"
    return {"decision": status, "robust_primary_directed_pairs": robust_pairs,
            "primary_groups": len(primary), "qualified_primary_groups": sum(g["qualified"] for g in primary),
            "primary_failure_reasons": dict(Counter(r for g in primary for r in g["reasons"])),
            "historical_observations_read": False, "historical_comparison_permitted": status.startswith("GO_")}


def validate_rows(rows):
    seen = set()
    for row in rows:
        key = (row["source_id"], row["quality_regime"], row["restriction"], int(row["replicate"]))
        if key in seen:
            raise ValueError("duplicate attempted history")
        seen.add(key)
        if row["role"] not in ("bank", "calibration", "test") or row["restriction"] not in RESTRICTIONS:
            raise ValueError("unknown role or restriction")
        if bool(row["valid"]) != (row["status"] == "valid"):
            raise ValueError("status/valid mismatch")
    return len(seen)


def verify_run_inputs(run_directory, manifest):
    from scripts.run_age_early_lake import OUTPUT_NAMES, source_bindings
    if manifest.get("status") != "complete":
        raise ValueError("a completed driver manifest is required")
    if manifest["source_bindings"] != source_bindings(require_analyzer=True):
        raise ValueError("archive does not bind the current complete implementation")
    if set(manifest["physical_sha256"]) != set(OUTPUT_NAMES):
        raise ValueError("manifest does not bind all three archives")
    for filename, expected in manifest["physical_sha256"].items():
        if sha256(Path(run_directory) / filename) != expected:
            raise ValueError(f"archive checksum mismatch: {filename}")
    for filename, expected in manifest["source_bindings"].items():
        if sha256(ROOT / filename) != expected["sha256"]:
            raise ValueError(f"frozen source changed: {filename}")


def validate_archive(rows, sources, manifest):
    from scripts.run_age_early_lake import (
        PRODUCTION_NAMESPACE, SMOKE_NAMESPACE, SMOKE_SOURCE_COUNT, _config,
        process_seed, validate_source_pairing, seed_preflight,
    )
    config = manifest["configuration"]
    mode = config["mode"]
    if mode not in ("gate", "smoke"):
        raise ValueError("unknown run mode")
    n = 512 if mode == "gate" else SMOKE_SOURCE_COUNT
    reps = 4 if mode == "gate" else 1
    namespace = PRODUCTION_NAMESPACE if mode == "gate" else SMOKE_NAMESPACE
    if config != _config(mode, namespace, n, reps):
        raise ValueError("configuration differs from the fixed allocation")
    validate_source_pairing(sources)
    seed_preflight(sources, bank_replicates=reps)
    source_map = {(s["source_id"], s["quality_regime"]): s for s in sources}
    expected_sources = {(f"{namespace}_A{age}_{role}_{i:04d}", q)
                        for age in (6, 8) for role in ("bank", "calibration", "test")
                        for i in range(n) for q in ("neutral", "engineering")}
    if len(source_map) != len(sources) or set(source_map) != expected_sources:
        raise ValueError("source archive does not contain the complete allocation")
    expected_slots = {(sid, q, r, rep) for (sid, q), s in source_map.items()
                      for r in RESTRICTIONS for rep in range(reps if s["role"] == "bank" else 1)}
    validate_rows(rows)
    observed_slots = {(r["source_id"], r["quality_regime"], r["restriction"], int(r["replicate"])) for r in rows}
    if observed_slots != expected_slots or len(rows) != manifest["planned_history_attempts"]:
        raise ValueError("history archive has missing or unexpected planned slots")
    if manifest["accounting"]["history_rows"] != len(rows):
        raise ValueError("manifest attempt accounting differs")
    for row in rows:
        source = source_map[(row["source_id"], row["quality_regime"])]
        if any(row[key] != source[key] for key in ("maximum_age", "role", "source_index")):
            raise ValueError("history/source identity mismatch")
        if row["seed"] != process_seed(source, int(row["replicate"])):
            raise ValueError("history process seed is not paired as declared")
        if not source["feasible"] and row["status"] != "algebraically_infeasible":
            raise ValueError("algebraic feasibility differs across paired histories")
        if source["feasible"] and row["status"] != "valid":
            raise ValueError("unexpected process failure blocks qualification")
        if int(row["advance_calls"]) != (25 if source["feasible"] else 0):
            raise ValueError("history does not have the prescribed annual transitions")
    return len(rows)


def run_analysis(run_directory, output, workers=1):
    started = time.monotonic()
    run_directory, output = Path(run_directory), Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    manifest_path = run_directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    verify_run_inputs(run_directory, manifest)
    features_path = run_directory / "features.jsonl.gz"
    rows = read_rows(features_path)
    sources = read_rows(run_directory / "sources.jsonl.gz")
    validate_archive(rows, sources, manifest)
    grouped = defaultdict(list)
    for row in rows:
        # Source parity declares the index stratum.  It is never used as the
        # bank-half split; source_halves hashes IDs after this grouping.
        stratum = "below_one" if int(row["source_index"]) % 2 == 0 else "above_one"
        grouped[(int(row["maximum_age"]), row["quality_regime"], stratum)].append(row)
    tasks = []
    for (age, quality, stratum), part in sorted(grouped.items()):
        for profile in PROFILES:
            group = {"maximum_age": age, "quality_regime": quality, "index_stratum": stratum, "profile": profile}
            name = f"A{age}_{quality}_{stratum}_{profile}.json.gz"
            tasks.append((group, part, str(output / name)))
    if len(tasks) != 32:
        raise ValueError("analysis requires all 32 prescribed groups")
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
            groups = list(pool.map(assess_group, tasks))
    else:
        groups = [assess_group(task) for task in tasks]
    decision = gate_decision(groups)
    report = {**decision, "groups": groups, "attempted_histories": len(rows),
              "runtime_seconds": time.monotonic() - started,
              "run_manifest_sha256": sha256(manifest_path), "features_sha256": sha256(features_path),
              "analyzer_sha256": sha256(__file__),
              "protocol_sha256": sha256(ROOT / "docs/early_lake_mechanism_protocol.md"),
              "run_mode": manifest["configuration"]["mode"],
              "analysis_workers": workers}
    if report["run_mode"] != "gate":
        report["decision"] = "QUALIFICATION_ONLY_NO_HISTORICAL_PERMISSION"
        report["historical_comparison_permitted"] = False
    write_json(output / "recovery_gate.json", report)
    flat = []
    for group in groups:
        flat.append({key: group[key] for key in ("maximum_age", "quality_regime", "index_stratum", "profile", "status", "qualified")}
                    | {"reasons": ";".join(group["reasons"]), "informative_pairs": ";".join(group["informative_pairs"]),
                       "minimum_calibration_z1": min(v["z1"] for v in group["counts"]["calibration"].values()),
                       "minimum_test_z1": min(v["z1"] for v in group["counts"]["test"].values())})
    with (output / "group_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    print(json.dumps({k: report[k] for k in decision} | {"runtime_seconds": report["runtime_seconds"]}, sort_keys=True))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.workers <= 16:
        parser.error("workers must be between one and sixteen")
    run_analysis(args.run, args.output, args.workers)


if __name__ == "__main__":
    main()
