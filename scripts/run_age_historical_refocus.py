#!/usr/bin/env python3
"""Fit a frozen early-history proposal, then draw a fresh linked recovery bank.

The fit command consumes the first gate only. The run command never adapts to
new outcomes. Biology, intervention dates and the original gate driver remain
unchanged; this driver records the distinct target and proposal correction.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import csv
import gzip
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
    binding, encoded, execute_source, json_value, seed_preflight, utc, verify_bindings,
    write_source_support,
)
from scripts.analyze_age_recovery import (
    _read_jsonl, _verify_generation_manifest, _verify_history_source_matches,
)
from galaxias_model.age_sources import (
    DESIGN, FORCING, cell_id, keyed_seed, make_source, runner_arguments, source_group,
)
from galaxias_model.age_demography import AgeDemography, _keyed_rng, _survive
from galaxias_model.age_historical_refocus import (
    UNIT_NAMES, draw_proposal, fit_histogram, lake_history_log_score,
    source_to_unit, source_with_unit,
)

PROTOCOL = ROOT / "docs/age_historical_refocus_protocol.md"
LAKE_DATA = ROOT / "data/age_structured_design_20260929/lake_figure6_digitised.csv"
OLD_MANIFEST = ROOT / "data/age_linked_recovery_20261001/provenance/generation_manifest.json"
MAX_GATE = 92160


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def lake_means() -> list[float]:
    with LAKE_DATA.open(newline="") as stream:
        selected = [row for row in csv.DictReader(stream)
                    if row["primary_count_block"].lower() == "true"]
    if [int(row["proposed_year"]) for row in selected] != [1976, 1977, 1978, 1979, 1980, 1983, 1986, 1989]:
        raise ValueError("unexpected primary Lake dates")
    return [float(row["mean_per_site_trip"]) for row in selected]


def bindings(extra=()) -> dict:
    # Keep the existing qualified dependency closure; unrelated newly added
    # analysis modules are not dependencies of proposal generation.
    original = json.loads(OLD_MANIFEST.read_text())["source_bindings"]
    verify_bindings(original)
    paths = [ROOT / name for name in original]
    paths += [Path(__file__), PROTOCOL, LAKE_DATA,
              ROOT / "src/galaxias_model/age_historical_refocus.py",
              ROOT / "scripts/analyze_age_recovery.py", *extra]
    return {relative(path): binding(path) for path in sorted(set(paths))}


def source_key(source: dict) -> str:
    return f"{source_group(source['cell'])}:{source['index_stratum']}"


def logmeanexp(values: list[float]) -> float:
    if not values:
        raise ValueError("an arithmetic mean needs planned attempts")
    high = max(values)
    if not math.isfinite(high):
        return -math.inf
    return high + math.log(math.fsum(math.exp(x-high) for x in values)) - math.log(len(values))


def fit(args) -> dict:
    archive = args.input_dir.resolve()
    sources = _read_jsonl(archive / "source_banks.jsonl")
    original = _verify_generation_manifest(archive, sources)
    preserved = json.loads(OLD_MANIFEST.read_text())
    if binding(archive / "run_manifest.json") != binding(OLD_MANIFEST) or original["source_bindings"] != preserved["source_bindings"]:
        raise ValueError("training must use the preserved complete first-gate manifest")
    histories = _read_jsonl(archive / "histories.jsonl.gz", compressed=True)
    _verify_history_source_matches(histories, sources, original)
    frozen = bindings()
    means = lake_means()
    utilities: dict[str, list[float]] = defaultdict(list)
    for row in histories:
        # Neither terminal occupancy nor any later endpoint is read here.
        score = -math.inf
        if row["status"] == "complete":
            score = float(lake_history_log_score(row["features"]["lake"], means))
        utilities[row["source_id"]].append(score)
    unique = {}
    for source in sources:
        sid = source["source_id"]
        if sid in unique:
            if not np.allclose(source_to_unit(unique[sid]), source_to_unit(source), rtol=0, atol=0):
                raise ValueError("paired cells differ in nuisance coordinates")
        else:
            unique[sid] = source
    groups = {}
    utility_rows = []
    for key in sorted({source_key(s) for s in unique.values()}):
        group = [s for s in unique.values() if source_key(s) == key]
        logs = np.asarray([logmeanexp(utilities[s["source_id"]]) for s in group])
        finite = np.isfinite(logs)
        weights = np.zeros(len(logs))
        if finite.any():
            weights[finite] = np.exp(logs[finite] - logs[finite].max())
        histogram = fit_histogram(np.asarray([source_to_unit(s) for s in group]), weights)
        total = weights.sum()
        groups[key] = dict(histogram=histogram, training_sources=len(group),
                           positive_utility_sources=int(finite.sum()),
                           training_source_ess=float(total*total/np.square(weights).sum()) if total else 0.,
                           source_ids=[s["source_id"] for s in group])
        for source, log_u in zip(group, logs):
            utility_rows.append(dict(group=key, source_id=source["source_id"],
                                     planned_paired_attempts=len(utilities[source["source_id"]]),
                                     log_mean_compatibility=float(log_u) if np.isfinite(log_u) else None))
    forbidden = set()
    for source in sources:
        forbidden.add(int(source["source_seed"]))
        for replicate in range(original["replicates_per_source"]):
            forbidden.add(int(runner_arguments(source, replicate, run_namespace=original["run_namespace"])["seed"]))
    result = dict(status="frozen", frozen_utc=utc(), specification=relative(PROTOCOL),
                  coordinate_names=list(UNIT_NAMES), groups=groups,
                  historical_lake_means=means, base_power=1/12, base_rho=1., base_age1=0.,
                  training_manifest=binding(archive / "run_manifest.json"),
                  training_output_bindings=original["outputs"],
                  training_namespace=original["run_namespace"],
                  training_source_ids=sorted(unique), forbidden_training_seeds=sorted(forbidden),
                  source_utilities=utility_rows, source_bindings=frozen,
                  fit_excludes_terminal_outcomes=True,
                  weight_contract="exp(historical_score) / (q/g), once per history",
                  mixture_contract="whole-vector 0.5 uniform plus 0.5 fitted product; 20% marginal uniform shrinkage")
    result = json_value(result)
    verify_bindings(frozen)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        stream.write(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return result


def build_sources(cells, truth_sources, bank_sources, namespace, proposal):
    sources = []
    for cell in cells:
        for role, count in (("truth", truth_sources), ("bank", bank_sources)):
            for index in range(count):
                source = make_source(cell, index, namespace=f"{namespace}:{role}")
                rng = np.random.default_rng(keyed_seed("age-refocus-proposal-20261002", source["source_id"], bits=128))
                unit, log_ratio, component = draw_proposal(proposal["groups"][source_key(source)]["histogram"], rng)
                source = source_with_unit(source, unit)
                source.update(cell_id=cell_id(cell), role=role,
                              proposal_log_density_ratio=float(log_ratio), proposal_component=component,
                              proposal_unit_coordinates=np.asarray(unit).tolist())
                sources.append(source)
    return sources


def reconstruct_compartment_breeders(history: dict, source: dict, process_seed: int) -> np.ndarray:
    """Recover the retained 2002 breeding draw from its exact keyed inputs.

    The original summary omitted compartment counts. The common calendar has
    a no-op Pedder checkpoint at t=.75, immediately before the breeding draw.
    Replaying only that keyed binomial draw does not advance any history.
    """
    demo = AgeDemography(**source["demography"])
    matches = [row for row in history["checkpoint_states"]["pedder"]
               if int(row["year"]) == 2002 and row["label"] == "transfer_2002_late"]
    if len(matches) != 1 or not math.isclose(float(matches[0]["time"]), demo.spawn_fraction, abs_tol=1e-12):
        raise ValueError("exact 2002 prespawning checkpoint is required for compartment reconstruction")
    current = np.asarray(matches[0]["state"], dtype=float)
    if (current.shape != (2, 2, demo.max_age+1) or not np.isfinite(current).all()
            or np.any(current < 0) or np.any(current != np.floor(current))
            or np.any(current[:, :, demo.max_age] != 0)):
        raise ValueError("reconstruction requires the stochastic pre-breeding eligible state")
    breeders = np.zeros((2, 2), dtype=float)
    for compartment in range(2):
        for sex in range(2):
            for age in range(demo.max_age):
                rng = _keyed_rng(int(process_seed), 2002, "pedder", 30000, compartment, sex, age)
                breeders[compartment, sex] += _survive(current[compartment, sex, age],
                    demo.breeding_probability[age+1], stochastic=True, rng=rng)
    values = history["per_year_diagnostics"]["pedder"]
    diag = values[2002] if 2002 in values else values["2002"]
    if not np.array_equal(breeders.sum(axis=0), [diag["pre_spawn_females"], diag["pre_spawn_males"]]):
        raise ValueError("reconstructed compartment breeders do not match the recorded pooled draw")
    return breeders


def endpoint_and_campaign_features(history: dict, source: dict | None = None, process_seed: int | None = None) -> dict:
    states = history["annual_states"]["pedder"]
    diagnostics = history["per_year_diagnostics"]["pedder"]
    def at(year):
        return np.asarray(states[year] if year in states else states[str(year)], dtype=float)
    state = at(2002)
    diag = diagnostics[2002] if 2002 in diagnostics else diagnostics["2002"]
    female, male = float(diag["pre_spawn_females"]), float(diag["pre_spawn_males"])
    if "pre_spawn_by_compartment_sex" in diag:
        by_compartment = np.asarray(diag["pre_spawn_by_compartment_sex"])
    elif source is not None and process_seed is not None:
        by_compartment = reconstruct_compartment_breeders(history, source, process_seed)
    else:
        raise ValueError("compartment endpoint requires saved diagnostics or exact keyed reconstruction inputs")
    age1plus = float(state[:, :, 1:].sum())
    electro_start = float(np.mean([at(y)[0, :, 1:].sum() for y in (1987, 1988)]))
    electro_end = float(np.mean([at(y)[0, :, 1:].sum() for y in (1988, 1989)]))
    return dict(
        terminal_pair=bool(female >= 1 and male >= 1),
        terminal_same_compartment_pair=bool(np.any(np.all(by_compartment >= 1, axis=1))),
        terminal_age1plus10=bool(age1plus >= 10),
        age1plus_2002=age1plus, breeders_female_2002=female, breeders_male_2002=male,
        breeders_by_compartment_sex_2002=by_compartment.tolist(),
        campaign_exposures=dict(electro_start=electro_start, electro_end=electro_end,
                                electro_mid=(electro_start+electro_end)/2,
                                larvae=float(np.mean([at(y)[0, :, 0].sum() for y in (1990, 1991)]))),
    )


def execute_refocused_source(task):
    source, replicates, namespace, means = task
    compact, raw = execute_source((source, replicates, namespace))
    for row, original in zip(compact, raw):
        row["proposal_log_density_ratio"] = source["proposal_log_density_ratio"]
        if row["status"] == "complete":
            row.update(endpoint_and_campaign_features(original["history"], source, row["process_seed"]))
            value = float(lake_history_log_score(row["features"]["lake"], means))
            # JSON represents impossible compatibility explicitly as null.
            row["historical_log_score_base"] = value if math.isfinite(value) else None
    return compact, raw


def run(args) -> dict:
    if not 1 <= args.workers <= 16:
        raise ValueError("workers must be in 1..16")
    if args.mode == "gate":
        if (args.truth_sources, args.bank_sources, args.replicates) != (512, 256, 2) or args.cells:
            raise ValueError("the repaired gate is exactly all20 cells x512/256 sources x2 replicates")
    elif not (1 <= args.truth_sources <= 2 and 1 <= args.bank_sources <= 2 and args.replicates == 1):
        raise ValueError("smoke is at most2 truth,2 bank,1 replicate per cell")
    proposal_path = args.proposal.resolve()
    proposal = json.loads(proposal_path.read_text())
    if proposal["status"] != "frozen":
        raise ValueError("proposal has not been frozen")
    verify_bindings(proposal["source_bindings"])
    design = json.loads(DESIGN.read_text())
    cells = design["process_cells"]
    if args.cells:
        wanted = args.cells.split(",")
        cells = [cell for cell in cells if cell_id(cell) in wanted]
        if len(set(wanted)) != len(wanted) or {cell_id(c) for c in cells} != set(wanted):
            raise ValueError("unknown or duplicate cell")
    nominal = len(cells)*(args.truth_sources+args.bank_sources)*args.replicates*3
    if nominal > MAX_GATE:
        raise ValueError("frozen repair allocation exceeded")
    frozen = bindings([proposal_path])
    sources = build_sources(cells, args.truth_sources, args.bank_sources, args.run_namespace, proposal)
    preflight = seed_preflight(sources, args.replicates, args.run_namespace)
    forbidden = set(proposal["forbidden_training_seeds"])
    for source in sources:
        if source["source_id"] in proposal["training_source_ids"]:
            raise ValueError("training source was reused")
        seeds = {int(source["source_seed"])}
        seeds.update(int(runner_arguments(source, r, run_namespace=args.run_namespace)["seed"])
                     for r in range(args.replicates))
        if seeds & forbidden:
            raise ValueError("fresh parameter/process seed collides with a training seed")
    preflight["training_seed_overlap"] = 0
    preflight["distinct_from_training_sources"] = True
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started, timer = utc(), time.monotonic()
    manifest = dict(status="running", started_utc=started, specification=relative(PROTOCOL),
                    run_namespace=args.run_namespace, mode=args.mode, cells=cells,
                    truth_sources_per_cell=args.truth_sources, bank_sources_per_cell=args.bank_sources,
                    replicates_per_source=args.replicates, source_rows=len(sources),
                    nominal_site_histories=nominal, workers=args.workers,
                    runtime=dict(python=platform.python_version(), numpy=np.__version__, platform=platform.platform()),
                    source_bindings=frozen, seed_preflight=preflight, proposal=binding(proposal_path),
                    historical_lake_means=proposal["historical_lake_means"],
                    head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                    full_design=args.mode == "gate")
    def save():
        (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    save()
    try:
        with (output / "source_banks.jsonl").open("w") as stream:
            for source in sources:
                stream.write(encoded(source) + "\n")
        tasks = [(s, args.replicates, args.run_namespace, proposal["historical_lake_means"]) for s in sources]
        counts, advance_calls, complete_sources = Counter(), 0, set()
        import hashlib
        compact_digest, raw_digest = hashlib.sha256(), hashlib.sha256()
        pool = ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn")) if args.workers > 1 else None
        try:
            results = pool.map(execute_refocused_source, tasks, chunksize=1, buffersize=2*args.workers) if pool else map(execute_refocused_source, tasks)
            with gzip.open(output / "histories.jsonl.gz", "wt") as compact_stream, gzip.open(output / "full_histories.jsonl.gz", "wt") as raw_stream:
                for index, (rows, raw_rows) in enumerate(results, 1):
                    for row, raw_row in zip(rows, raw_rows):
                        counts[row["status"]] += 1
                        advance_calls += row["advance_calls"]
                        if row["status"] == "complete":
                            complete_sources.add((row["cell_id"], row["namespace"], row["source_id"]))
                        for value, stream, digest in ((row, compact_stream, compact_digest), (raw_row, raw_stream, raw_digest)):
                            line = encoded(value) + "\n"
                            stream.write(line)
                            digest.update(line.encode())
                    if index == 1 or index % 128 == 0 or index == len(sources):
                        print(json.dumps(dict(source_rows_done=index, source_rows_total=len(sources),
                                              history_status_counts=dict(counts), elapsed_seconds=round(time.monotonic()-timer, 2))), flush=True)
        finally:
            if pool:
                pool.shutdown(wait=True, cancel_futures=True)
        verify_bindings(frozen)
        write_source_support(output / "source_support.csv", sources, complete_sources)
        # The legacy helper's CSV writer defaults to CRLF; compact new output
        # follows the repository's LF convention without altering old outputs.
        support_path = output / "source_support.csv"
        support_path.write_bytes(support_path.read_bytes().replace(b"\r\n", b"\n"))
        manifest.update(status="complete", finished_utc=utc(), elapsed_seconds=time.monotonic()-timer,
                        history_status_counts=dict(counts), actual_advance_calls=advance_calls,
                        executed_linked_histories=counts["complete"]+counts["process_infeasible"],
                        content_sha256={"histories.jsonl": compact_digest.hexdigest(), "full_histories.jsonl": raw_digest.hexdigest()},
                        outputs={p.name: binding(p) for p in sorted(output.iterdir()) if p.name != "run_manifest.json"})
        save()
        return manifest
    except BaseException as exc:
        manifest.update(status="failed", finished_utc=utc(), failure=f"{type(exc).__name__}: {exc}",
                        elapsed_seconds=time.monotonic()-timer)
        save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fit_parser = commands.add_parser("fit")
    fit_parser.add_argument("--input-dir", required=True, type=Path)
    fit_parser.add_argument("--output", required=True, type=Path)
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--proposal", required=True, type=Path)
    run_parser.add_argument("--output-dir", required=True, type=Path)
    run_parser.add_argument("--mode", choices=("smoke", "gate"), required=True)
    run_parser.add_argument("--run-namespace", required=True)
    run_parser.add_argument("--truth-sources", type=int, default=512)
    run_parser.add_argument("--bank-sources", type=int, default=256)
    run_parser.add_argument("--replicates", type=int, default=2)
    run_parser.add_argument("--workers", type=int, default=1)
    run_parser.add_argument("--cells")
    args = parser.parse_args()
    result = fit(args) if args.command == "fit" else run(args)
    print(json.dumps({key: result[key] for key in ("status", "frozen_utc", "nominal_site_histories", "elapsed_seconds") if key in result}, sort_keys=True))


if __name__ == "__main__":
    main()
