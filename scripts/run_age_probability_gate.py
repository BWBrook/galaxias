#!/usr/bin/env python3
"""Fit a joint record-directed proposal and generate the final bounded gate."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import copy
import gzip
import hashlib
import json
import math
import multiprocessing as mp
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from scripts.run_age_recovery import (
    binding, encoded, execute_source, json_value, seed_preflight, source_bindings,
    utc, verify_bindings,
)
from scripts.run_age_historical_refocus import (
    endpoint_and_campaign_features, lake_means, logmeanexp, source_key,
)
from scripts.analyze_age_recovery import (
    _read_jsonl, _verify_generation_manifest, _verify_history_source_matches,
)
from galaxias_model.age_historical_refocus import (
    lake_history_log_score, source_to_unit, source_with_unit,
)
from galaxias_model.age_joint_proposal import draw_joint_beta, fit_joint_beta
from galaxias_model.age_probability_observation import early_creek_log_score
from galaxias_model.age_recovery_observation import LAKE_YEARS
from galaxias_model.age_sources import DESIGN, cell_id, keyed_seed, make_source, runner_arguments


PROTOCOL = ROOT / "docs/age_probability_gate_protocol.md"
OLD_MANIFESTS = (
    ROOT / "data/age_linked_recovery_20261001/provenance/generation_manifest.json",
    ROOT / "outputs/remote/age_lake_refocus_20261002/gate/run_manifest.json",
)
MAX_GATE = 147456


def save_json(path, value):
    path.write_text(json.dumps(json_value(value), sort_keys=True, indent=2, allow_nan=False) + "\n")


def finite_or_none(value):
    return float(value) if math.isfinite(float(value)) else None


def bindings(extra=()):
    result = source_bindings()
    paths = [Path(__file__), PROTOCOL,
             ROOT / "scripts/analyze_age_probability_gate.py",
             ROOT / "scripts/run_age_historical_refocus.py",
             ROOT / "scripts/analyze_age_recovery.py",
             ROOT / "data/age_lake_repair_20261002/lake_evidence.csv", *extra]
    # Lake's retained CSV path is bound by the old helper's declared source set.
    from scripts.run_age_historical_refocus import bindings as old_bindings
    result.update(old_bindings())
    for path in paths:
        result[str(path.relative_to(ROOT))] = binding(path)
    return result


def broad_cells():
    cells = json.loads(DESIGN.read_text())["process_cells"]
    return [c for c in cells if c["nursery"] == "legacy_range_sensitivity"
            and c["removal_account"] == "primary_plan_31_early_releases"]


def early_conditioning(features, means):
    """Use E only; terminal state and remaining observations are never accessed."""
    march_present = float(np.sum(features["march"])) >= 1
    if not march_present:
        return dict(lake=-math.inf, creek=-math.inf, total=-math.inf, march_present=False)
    early = np.asarray(features["creek_early"], dtype=float)
    february = np.asarray(features["creek_feb"], dtype=float)
    creek = np.asarray([[43*early[:, 1].mean(), 2*february[1], 0.]])
    lake = float(lake_history_log_score(features["lake"], means))
    creek_score = float(early_creek_log_score(creek)[0])
    return dict(lake=lake, creek=creek_score, total=lake+creek_score, march_present=True)


def partial_early_conditioning(history, means):
    """Recover E for the post-2002 feasibility-selection diagnostic only."""
    states = history.get("annual_states", {}).get("pedder", {})
    if 2002 not in states and "2002" not in states:
        return None
    def at(year):
        return np.asarray(states[year] if year in states else states[str(year)], dtype=float)
    checkpoints = history["checkpoint_states"]["pedder"]
    def one(label):
        matches = [row["state"] for row in checkpoints if row["label"] == label]
        if len(matches) != 1:
            raise ValueError(f"partial conditioning requires one {label}")
        return np.asarray(matches[0], dtype=float)
    early = [np.asarray(row["state"], dtype=float) for row in checkpoints
             if row["label"].startswith("early_refuge_")]
    if len(early) != 20:
        raise ValueError("partial conditioning requires all 20 early checkpoints")
    march_present = float(one("march_1996_record")[1].sum()) >= 1
    lake = np.asarray([[at(y)[0, :, 0].sum(), at(y)[0, :, 1].sum()] for y in LAKE_YEARS])
    creek = np.asarray([[43*np.mean([state[1, :, 1:].sum() for state in early]),
                         2*one("february_1992_capture")[1, :, 1:].sum(), 0.]])
    log_score = (float(lake_history_log_score(lake, means))
                 + float(early_creek_log_score(creek)[0])) if march_present else -math.inf
    return dict(valid_through_2002=True, loss_2002=bool(at(2002).sum() == 0),
                log_score=finite_or_none(log_score), march_present=march_present)


def fit(args):
    """Fit source geometry from E; previous output labels cannot enter utility."""
    means = lake_means()
    selected_cells = {cell_id(c) for c in broad_cells()}
    frozen = bindings()
    unique, utilities, archive_receipts = {}, defaultdict(list), []
    forbidden_seeds, training_ids = set(), set()
    for archive, canonical in zip(args.input_dirs, OLD_MANIFESTS, strict=True):
        archive = archive.resolve()
        sources = _read_jsonl(archive / "source_banks.jsonl")
        manifest = _verify_generation_manifest(archive, sources)
        if binding(archive / "run_manifest.json") != binding(canonical):
            raise ValueError("training archive is not its preserved completed run")
        histories = _read_jsonl(archive / "histories.jsonl.gz", compressed=True)
        _verify_history_source_matches(histories, sources, manifest)
        for source in sources:
            training_ids.add(source["source_id"])
            forbidden_seeds.add(int(source["source_seed"]))
            for r in range(manifest["replicates_per_source"]):
                forbidden_seeds.add(int(runner_arguments(source, r, run_namespace=manifest["run_namespace"])["seed"]))
            if source["cell_id"] not in selected_cells:
                continue
            sid = source["source_id"]
            if sid in unique and not np.array_equal(source_to_unit(unique[sid]), source_to_unit(source)):
                raise ValueError("paired source coordinates disagree")
            unique.setdefault(sid, source)
        for row in histories:
            if row["cell_id"] not in selected_cells:
                continue
            log_weight = -math.inf
            if row["status"] == "complete":
                log_weight = early_conditioning(row["features"], means)["total"]
                log_weight -= float(row.get("proposal_log_density_ratio", 0.))
            utilities[row["source_id"]].append(log_weight)
        archive_receipts.append(dict(path=str(archive.relative_to(ROOT)),
                                     canonical=str(canonical.relative_to(ROOT)),
                                     manifest=binding(archive / "run_manifest.json"),
                                     run_namespace=manifest["run_namespace"],
                                     outputs=manifest["outputs"]))
    groups, utility_rows = {}, []
    for group in sorted({source_key(s) for s in unique.values()}):
        sources = [s for s in unique.values() if source_key(s) == group]
        logs = np.asarray([logmeanexp(utilities[s["source_id"]]) for s in sources])
        finite = np.isfinite(logs)
        weights = np.zeros(len(logs))
        if finite.any():
            weights[finite] = np.exp(logs[finite]-logs[finite].max())
        joint = fit_joint_beta(np.asarray([source_to_unit(s) for s in sources]), weights)
        groups[group] = dict(joint=joint, training_sources=len(sources),
                             positive_utility_sources=int(finite.sum()),
                             training_source_ess=float(weights.sum()**2/np.square(weights).sum()) if weights.sum() else 0.)
        utility_rows.extend(dict(group=group, source_id=s["source_id"],
                                 planned_attempts=len(utilities[s["source_id"]]),
                                 log_mean_compatibility=finite_or_none(log_u))
                            for s, log_u in zip(sources, logs))
    result = dict(status="frozen", frozen_utc=utc(), protocol=str(PROTOCOL.relative_to(ROOT)),
                  groups=groups, historical_lake_means=means, source_utilities=utility_rows,
                  training_archives=archive_receipts, training_source_ids=sorted(training_ids),
                  forbidden_training_seeds=sorted(forbidden_seeds), source_bindings=frozen,
                  fit_excludes_terminal_and_remaining_evidence=True,
                  conditioning="Lake8 + early creek allocation + March presence + full intervention feasibility",
                  proposal="whole-vector 0.5 uniform +0.25 joint beta kappa8 +0.25 joint beta kappa32",
                  weight_contract="exp(E)/(q/g), once; all failed planned attempts contribute zero")
    verify_bindings(frozen)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    save_json(output, result)
    return result


def build_sources(cells, truth_sources, bank_sources, namespace, proposal):
    result, cache = [], {}
    for cell in cells:
        for role, count in (("truth", truth_sources), ("bank", bank_sources)):
            for index in range(count):
                key = (cell["maximum_age"], role, index)
                if key not in cache:
                    source = make_source(cell, index, namespace=f"{namespace}:{role}")
                    rng = np.random.default_rng(keyed_seed("joint-record-proposal-20261003", source["source_id"], bits=128))
                    u, log_ratio, component = draw_joint_beta(proposal["groups"][source_key(source)]["joint"], rng)
                    source = source_with_unit(source, u)
                    source.update(role=role, proposal_log_density_ratio=float(log_ratio),
                                  proposal_component=component, proposal_unit_coordinates=np.asarray(u).tolist())
                    cache[key] = source
                source = copy.deepcopy(cache[key])
                source.update(cell=cell, cell_id=cell_id(cell))
                result.append(source)
    return result


def execute_probability_source(task):
    source, replicates, namespace, means = task
    compact, raw = execute_source((source, replicates, namespace))
    for row, original in zip(compact, raw):
        row["proposal_log_density_ratio"] = source["proposal_log_density_ratio"]
        history = original["history"]
        if history is not None:
            row["through_2002_diagnostic"] = partial_early_conditioning(history, means)
        if row["status"] == "complete":
            row.update(endpoint_and_campaign_features(history, source, row["process_seed"]))
            scores = early_conditioning(row["features"], means)
            row["conditioning"] = {k:finite_or_none(v) if k != "march_present" else v for k,v in scores.items()}
            row["loss_2002"] = not row["terminal_alive"]
            partial = row["through_2002_diagnostic"]
            if partial["log_score"] != row["conditioning"]["total"]:
                if partial["log_score"] is None or row["conditioning"]["total"] is None or not math.isclose(partial["log_score"], row["conditioning"]["total"], abs_tol=1e-10, rel_tol=1e-12):
                    raise RuntimeError("complete and partial early conditioning disagree")
    return compact, raw


def preflight(sources, replicates, namespace, proposal, qualification_manifests=()):
    check = seed_preflight(sources, replicates, namespace)
    forbidden = set(proposal["forbidden_training_seeds"])
    for name in qualification_manifests:
        directory = name.resolve().parent
        manifest = json.loads(name.read_text())
        for source in _read_jsonl(directory / "source_banks.jsonl"):
            forbidden.add(int(source["source_seed"]))
            for r in range(manifest["replicates_per_source"]):
                forbidden.add(int(runner_arguments(source, r, run_namespace=manifest["run_namespace"])["seed"]))
    for source in sources:
        if source["source_id"] in proposal["training_source_ids"]:
            raise ValueError("training source reused")
        seeds = {int(source["source_seed"])}
        seeds.update(int(runner_arguments(source, r, run_namespace=namespace)["seed"]) for r in range(replicates))
        if seeds & forbidden:
            raise ValueError("fresh parameter/process seed collides with an old or qualification seed")
    check.update(training_or_qualification_seed_overlap=0,
                 forbidden_seeds_checked=len(forbidden), simulation_calls=0)
    return check


def run(args):
    if not 1 <= args.workers <= 16:
        raise ValueError("workers must be in 1..16")
    if args.mode == "gate":
        if (args.truth_sources, args.bank_sources, args.replicates) != (512,512,6):
            raise ValueError("production is exactly 512 truth/512 bank/6 replicates in all eight broad cells")
    elif not (1 <= args.truth_sources <= 2 and 1 <= args.bank_sources <= 2 and args.replicates == 1):
        raise ValueError("smoke is at most 2 truth/2 bank/1 replicate per cell")
    proposal_path = args.proposal.resolve()
    proposal = json.loads(proposal_path.read_text())
    if proposal["status"] != "frozen":
        raise ValueError("proposal is not frozen")
    verify_bindings(proposal["source_bindings"])
    cells = broad_cells()
    nominal = len(cells)*(args.truth_sources+args.bank_sources)*args.replicates*3
    if nominal > MAX_GATE:
        raise ValueError("bounded allocation exceeded")
    frozen = bindings([proposal_path])
    sources = build_sources(cells,args.truth_sources,args.bank_sources,args.run_namespace,proposal)
    check = preflight(sources,args.replicates,args.run_namespace,proposal,args.qualification_manifest)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    timer = time.monotonic()
    manifest = dict(status="running", started_utc=utc(), mode=args.mode, full_design=args.mode == "gate",
                    specification=str(PROTOCOL.relative_to(ROOT)), run_namespace=args.run_namespace,
                    cells=cells, truth_sources_per_cell=args.truth_sources, bank_sources_per_cell=args.bank_sources,
                    replicates_per_source=args.replicates, source_rows=len(sources), nominal_site_histories=nominal,
                    source_bindings=frozen, workers=args.workers, seed_preflight=check,
                    proposal=binding(proposal_path), historical_lake_means=proposal["historical_lake_means"],
                    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                    runtime=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()))
    def save():
        save_json(output / "run_manifest.json", manifest)
    save()
    try:
        with (output / "source_banks.jsonl").open("w") as stream:
            for source in sources:
                stream.write(encoded(source)+"\n")
        tasks = [(s,args.replicates,args.run_namespace,proposal["historical_lake_means"]) for s in sources]
        counts, calls = Counter(), 0
        compact_hash, raw_hash = hashlib.sha256(), hashlib.sha256()
        pool = ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn")) if args.workers > 1 else None
        try:
            results = pool.map(execute_probability_source,tasks,chunksize=1,buffersize=2*args.workers) if pool else map(execute_probability_source,tasks)
            with gzip.open(output / "histories.jsonl.gz","wt") as compact_stream, gzip.open(output / "full_histories.jsonl.gz","wt") as raw_stream:
                for index,(rows,raw_rows) in enumerate(results,1):
                    for row,raw in zip(rows,raw_rows):
                        counts[row["status"]] += 1
                        calls += row["advance_calls"]
                        for value,stream,digest in ((row,compact_stream,compact_hash),(raw,raw_stream,raw_hash)):
                            line = encoded(value)+"\n"
                            stream.write(line)
                            digest.update(line.encode())
                    if index == 1 or index%128 == 0 or index == len(sources):
                        print(json.dumps(dict(source_rows_done=index,source_rows_total=len(sources),history_status_counts=dict(counts),elapsed_seconds=round(time.monotonic()-timer,2))),flush=True)
        finally:
            if pool:
                pool.shutdown(wait=True,cancel_futures=True)
        verify_bindings(frozen)
        manifest.update(status="complete",finished_utc=utc(),elapsed_seconds=time.monotonic()-timer,
                        history_status_counts=dict(counts),actual_advance_calls=calls,
                        executed_linked_histories=counts["complete"]+counts["process_infeasible"],
                        content_sha256={"histories.jsonl":compact_hash.hexdigest(),"full_histories.jsonl":raw_hash.hexdigest()},
                        outputs={p.name:binding(p) for p in sorted(output.iterdir()) if p.name != "run_manifest.json"})
        save()
        return manifest
    except BaseException as exc:
        manifest.update(status="failed",finished_utc=utc(),failure=f"{type(exc).__name__}: {exc}",elapsed_seconds=time.monotonic()-timer)
        save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command",required=True)
    pfit = sub.add_parser("fit")
    pfit.add_argument("--input-dirs",type=Path,nargs=2,required=True)
    pfit.add_argument("--output",type=Path,required=True)
    prun = sub.add_parser("run")
    prun.add_argument("--proposal",type=Path,required=True)
    prun.add_argument("--output-dir",type=Path,required=True)
    prun.add_argument("--mode",choices=("gate","smoke"),required=True)
    prun.add_argument("--truth-sources",type=int,default=512)
    prun.add_argument("--bank-sources",type=int,default=512)
    prun.add_argument("--replicates",type=int,default=6)
    prun.add_argument("--workers",type=int,default=1)
    prun.add_argument("--run-namespace",required=True)
    prun.add_argument("--qualification-manifest",type=Path,action="append",default=[])
    args = parser.parse_args()
    result = fit(args) if args.command == "fit" else run(args)
    print(json.dumps({k:v for k,v in result.items() if k in ("status","frozen_utc","history_status_counts","elapsed_seconds","nominal_site_histories")},sort_keys=True))


if __name__ == "__main__":
    main()
