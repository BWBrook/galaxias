#!/usr/bin/env python3
"""Generate a finite, source-separated linked-history bank without selection."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from dataclasses import asdict, is_dataclass
import gzip
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from galaxias_model.age_recovery_observation import extract_features
from galaxias_model.age_runner import run_linked_history
from galaxias_model.age_sources import DESIGN, FORCING, cell_id, make_source, runner_arguments


def utc():
    return datetime.now(timezone.utc).isoformat()


def json_value(value):
    if is_dataclass(value):
        return json_value(asdict(value))
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    return value


def encoded(value):
    return json.dumps(json_value(value), separators=(",", ":"), sort_keys=True, allow_nan=False)


def binding(path):
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def source_bindings():
    paths = list((ROOT / "src/galaxias_model").glob("*.py"))
    paths += [Path(__file__), DESIGN, FORCING, ROOT / "uv.lock", ROOT / "pyproject.toml",
              ROOT / "docs/age_linked_recovery_protocol.md",
              ROOT / "docs/age_structured_protocol_candidate2.md"]
    return {str(p.relative_to(ROOT)): binding(p) for p in sorted(set(paths))}


def verify_bindings(frozen):
    for name, expected in frozen.items():
        if binding(ROOT / name) != expected:
            raise RuntimeError(f"frozen source changed during execution: {name}")


def build_sources(cells, truth_sources, bank_sources, run_namespace):
    sources = []
    for cell in cells:
        for role, count in (("truth", truth_sources), ("bank", bank_sources)):
            for index in range(count):
                source = make_source(cell, index, namespace=f"{run_namespace}:{role}")
                source.update(cell_id=cell_id(cell), role=role)
                sources.append(source)
    return sources


def seed_preflight(sources, replicates, run_namespace):
    """Allow declared cross-restriction pairing, reject accidental collisions."""
    seeds = {}
    for source in sources:
        entries = [(source["source_seed"], ("parameter", source["source_id"]))]
        entries += [(runner_arguments(source, r, run_namespace=run_namespace)["seed"],
                     ("process", source["source_id"], r)) for r in range(replicates)]
        for seed, identity in entries:
            previous = seeds.setdefault(seed, identity)
            if previous != identity:
                raise RuntimeError(f"unintended seed collision between {previous} and {identity}")
    return {"unique_parameter_and_process_seeds": len(seeds),
            "paired_restrictions_and_removal_accounts": True,
            "observation_seed_width_bits": 128,
            "checked_cross_namespace_collisions": True}


def execute_source(task):
    source, replicates, run_namespace = task
    compact, raw = [], []
    for replicate in range(replicates):
        kwargs = runner_arguments(source, replicate, run_namespace=run_namespace)
        row = {"cell_id": source["cell_id"], "namespace": source["role"],
               "source_id": source["source_id"], "replicate": replicate,
               "process_seed": kwargs["seed"], "refuge_index": source["refuge_index"],
               "index_stratum": source["index_stratum"], "march_retention": source["march_retention"],
               "ledger_timing": source["ledger_timing"], "nominal_site_histories": 3,
               "advance_calls": 0, "calendar_hash": None}
        history = None
        if not source["feasible"]:
            row.update(status="algebraically_infeasible", failure=source["failure_reason"])
        else:
            history = run_linked_history(**kwargs)
            row.update(advance_calls=history["advance_calls"], calendar_hash=history["calendar_hash"])
            if not history["valid"]:
                row.update(status="process_infeasible", failure=history["failure"])
            else:
                pedder = np.asarray(history["annual_states"]["pedder"][2002])
                row.update(status="complete", failure="", terminal_alive=bool(pedder.sum() > 0),
                           refuge_2002=float(pedder[1].sum()), lake_2002=float(pedder[0].sum()),
                           features=extract_features(history),
                           small_pool_diagnostics=small_pool_diagnostics(history))
        compact.append(row)
        raw.append({"cell_id": row["cell_id"], "namespace": row["namespace"],
                    "source_id": row["source_id"], "replicate": replicate,
                    "status": row["status"], "failure": row["failure"], "history": history})
    return compact, raw


def small_pool_diagnostics(history):
    result = {}
    for last_year in (2002, 2012):
        attempts = small_attempts = successes = small_successes = 0
        for year, diag in history["per_year_diagnostics"]["pedder"].items():
            if not 1997 <= int(year) <= last_year:
                continue
            female, male = diag["pre_spawn_females"], diag["pre_spawn_males"]
            attempt = female > 0 and male > 0
            small = female <= 2 or male <= 2
            success = np.asarray(diag["surviving_newborns"]).sum() > 0
            attempts += int(attempt); small_attempts += int(attempt and small)
            successes += int(success); small_successes += int(success and small)
        result[f"1997_{last_year}"] = dict(
            breeding_attempts=attempts, small_pool_attempts=small_attempts,
            successful_recruitment_events=successes, small_pool_successful_events=small_successes,
            fraction_small_attempts=small_attempts/attempts if attempts else None,
            fraction_small_successful_events=small_successes/successes if successes else None,
        )
    return result


def write_source_support(path, sources, complete_sources):
    rows = []
    for cell in sorted({s["cell_id"] for s in sources}):
        for role in ("truth", "bank"):
            proposed = [s for s in sources if s["cell_id"] == cell and s["role"] == role]
            subsets = {"proposed": proposed,
                       "algebraically_feasible": [s for s in proposed if s["feasible"]],
                       "at_least_one_complete_process_history": [s for s in proposed
                           if (cell, role, s["source_id"]) in complete_sources]}
            for stage, subset in subsets.items():
                above = sum(s["refuge_index"] > 1 for s in subset)
                rows.append(dict(cell_id=cell, namespace=role, stage=stage, source_count=len(subset),
                                 sources_refuge_index_above_one=above,
                                 fraction_refuge_index_above_one=above/len(subset) if subset else ""))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(args):
    if not 1 <= args.workers <= 16:
        raise ValueError("workers must be in 1..16")
    if not 1 <= args.truth_sources <= 64 or not 1 <= args.bank_sources <= 32 or not 1 <= args.replicates <= 4:
        raise ValueError("source/replicate counts exceed the frozen gate design")
    design = json.loads(DESIGN.read_text())
    cells = design["process_cells"]
    if args.cells:
        requested = args.cells.split(",")
        cells = [c for c in cells if cell_id(c) in requested]
        if set(requested) != {cell_id(c) for c in cells}:
            raise ValueError("unknown or duplicate cell selection")
    nominal = len(cells) * (args.truth_sources + args.bank_sources) * args.replicates * 3
    if nominal > 23040:
        raise ValueError("gate allocation exceeded")
    sources = build_sources(cells, args.truth_sources, args.bank_sources, args.run_namespace)
    preflight = seed_preflight(sources, args.replicates, args.run_namespace)
    frozen = source_bindings()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started, timer = utc(), time.monotonic()
    manifest = {"status": "running", "started_utc": started,
                "specification": "docs/age_linked_recovery_protocol.md",
                "run_namespace": args.run_namespace, "cells": cells,
                "truth_sources_per_cell": args.truth_sources, "bank_sources_per_cell": args.bank_sources,
                "replicates_per_source": args.replicates, "source_rows": len(sources),
                "nominal_site_histories": nominal, "workers": args.workers,
                "runtime": {"python": platform.python_version(), "numpy": np.__version__,
                            "platform": platform.platform()}, "source_bindings": frozen,
                "seed_preflight": preflight,
                "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "full_design": len(cells) == 20 and args.truth_sources == 64 and args.bank_sources == 32
                               and args.replicates == 4}
    def write_manifest():
        (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_manifest()
    try:
        with (output / "source_banks.jsonl").open("w") as handle:
            for source in sources:
                handle.write(encoded(source) + "\n")
        tasks = [(source, args.replicates, args.run_namespace) for source in sources]
        counts, advance_calls, complete_sources = Counter(), 0, set()
        compact_digest, raw_digest = hashlib.sha256(), hashlib.sha256()
        pool = ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn")) if args.workers > 1 else None
        try:
            results = pool.map(execute_source, tasks, chunksize=1, buffersize=2*args.workers) if pool else map(execute_source, tasks)
            with gzip.open(output / "histories.jsonl.gz", "wt") as compact_handle, \
                 gzip.open(output / "full_histories.jsonl.gz", "wt") as raw_handle:
                for index, (rows, raw_rows) in enumerate(results, 1):
                    for row, raw_row in zip(rows, raw_rows):
                        counts[row["status"]] += 1
                        advance_calls += row["advance_calls"]
                        if row["status"] == "complete":
                            complete_sources.add((row["cell_id"], row["namespace"], row["source_id"]))
                        for value, handle, digest in ((row, compact_handle, compact_digest),
                                                       (raw_row, raw_handle, raw_digest)):
                            line = encoded(value) + "\n"
                            handle.write(line); digest.update(line.encode())
                    if index == 1 or index % 32 == 0 or index == len(sources):
                        print(json.dumps({"source_rows_done": index, "source_rows_total": len(sources),
                                          "history_status_counts": dict(counts),
                                          "elapsed_seconds": round(time.monotonic()-timer, 2)}), flush=True)
        finally:
            if pool:
                pool.shutdown(wait=True, cancel_futures=True)
        verify_bindings(frozen)
        write_source_support(output / "source_support.csv", sources, complete_sources)
        manifest.update(status="complete", finished_utc=utc(), elapsed_seconds=time.monotonic()-timer,
                        history_status_counts=dict(counts), actual_advance_calls=advance_calls,
                        executed_linked_histories=counts["complete"]+counts["process_infeasible"],
                        content_sha256={"histories.jsonl": compact_digest.hexdigest(),
                                        "full_histories.jsonl": raw_digest.hexdigest()},
                        outputs={p.name: binding(p) for p in sorted(output.iterdir()) if p.name != "run_manifest.json"})
        write_manifest()
        return manifest
    except BaseException as exc:
        manifest.update(status="failed", finished_utc=utc(), elapsed_seconds=time.monotonic()-timer,
                        failure=f"{type(exc).__name__}: {exc}")
        write_manifest()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--truth-sources", type=int, default=64)
    parser.add_argument("--bank-sources", type=int, default=32)
    parser.add_argument("--replicates", type=int, default=4)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--cells", help="comma-separated exact cell IDs, for qualification only")
    parser.add_argument("--run-namespace", default="gate-20261001")
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({k: result[k] for k in ("status", "nominal_site_histories", "history_status_counts", "elapsed_seconds")}), flush=True)


if __name__ == "__main__":
    main()
