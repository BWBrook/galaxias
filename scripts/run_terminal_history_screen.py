#!/usr/bin/env python3
"""Fresh stochastic histories at frozen pilot parameters; never select sources."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
import multiprocessing
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# The peer runner lives in this source checkout, outside the installed package.
sys.path.insert(0, str(ROOT))
from scripts import run_observation_repair_pilot as pilot

PHASE_CODES = {"screen": 601, "confirm": 701, "extend": 809}
DEFAULT_REPLICATES = {"screen": 50, "confirm": 500, "extend": 2000}
SOURCE_CAPS = {"screen": 1000, "confirm": 245, "extend": 40}
NULLABLE_YEARS = ["latent_last_presence_year", "first_zero_year"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def phase_seed(search_seed, family_id, proposal_index, replicate_index, phase):
    return pilot._derive_seed(search_seed, pilot._family_index(family_id), proposal_index, replicate_index, PHASE_CODES[phase])


def source_seeds(search_seed, family_id, proposal_index, replicates, phase):
    """Vectorised original affine seed derivation, including its zero rule."""
    modulus = 2**32 - 5
    base = int(search_seed) % modulus
    for part in [pilot._family_index(family_id), proposal_index]:
        base = (base * 1664525 + 1013904223 + int(part) * 374761393) % modulus
    values = (base * 1664525 + 1013904223 + np.arange(1, replicates + 1, dtype=np.int64) * 374761393) % modulus
    values = (values * 1664525 + 1013904223 + PHASE_CODES[phase] * 374761393) % modulus
    return np.where(values == 0, 1, values)


def verify_archive(directory, expected_scope):
    manifest_path = directory / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    require(manifest.get("status") == "complete" and manifest.get("scope") == expected_scope, f"Incomplete or unexpected archive: {directory}")
    bindings = {"run_manifest.json": pilot.file_hash(manifest_path)}
    for name, expected in manifest["outputs"].items():
        require(Path(name).name == name, "Archive output must be a direct filename")
        bindings[name] = pilot.file_hash(directory / name)
        require(bindings[name] == expected, f"Archive size/hash mismatch: {directory / name}")
    return manifest, bindings


def terminal_features(history):
    trajectory = history.trajectory_table.set_index("year")
    require(trajectory.index.is_unique and {1996, 2002}.issubset(trajectory.index), "Terminal projection requires unique annual states through 2002")
    total = trajectory.N_total
    require(np.isfinite(total).all() and total.ge(0).all(), "Invalid total abundance")
    present, absent = trajectory.index[total.gt(0)], trajectory.index[total.eq(0)]
    features = pilot.project_repaired_history(history)
    extinct = bool(trajectory.loc[2002, "N_total"] == 0)
    features.update(
        surviving_1996=bool(trajectory.loc[1996, "N_total"] > 0),
        extinct_by_2002=extinct,
        positive_and_extinct_by_2002=bool(features["positive_records_compatible"] and extinct),
        positive_and_all_natural_nondetections_empty=bool(features["positive_records_compatible"] and features["natural_nondetection_occupied_episodes"] == 0),
        positive_and_all_nondetections_empty=bool(features["positive_records_compatible"] and features["nondetection_occupied_episodes"] == 0),
        latent_last_presence_year=float(present[-1]) if len(present) else np.nan,
        first_zero_year=float(absent[0]) if len(absent) else np.nan,
    )
    return features


def simulate_source(task):
    inputs = pilot._load_inputs_cached(task["data_dir"])
    params = pilot.build_resolved_parameters_from_sample(inputs, task["family_id"], pd.DataFrame(task["parameter_rows"]))
    config = pilot._scenario_config(inputs, "historical_lake", True)
    rows = []
    for rep in range(1, task["replicates"] + 1):
        seed = phase_seed(task["search_seed"], task["family_id"], task["proposal_index"], rep, task["phase"])
        history = pilot.run_historical_simulation(params, task["family_id"], config, seed=seed)
        row = {k: task[k] for k in pilot.IDENTITY}
        row.update(stage=task["phase"], replicate_index=rep, simulation_seed=seed)
        row.update(terminal_features(history))
        row.update(pilot.scored_fields(history, inputs))
        row.update(task["intrinsic"])
        require(all(f"{target}_weighted_penalty" in row for target in pilot.TARGETS), "Incomplete legacy score coverage")
        rows.append(row)
    return rows


def summarise_batch(raw):
    # Event-year summaries exclude censored/missing events explicitly. The peer
    # helper handles the finite physical features and all four fixed profiles.
    summary = pilot.source_summaries(raw.drop(columns=NULLABLE_YEARS)).drop(columns=["stage_a_retained", "selected"])
    for field in NULLABLE_YEARS:
        values = raw[field].dropna()
        summary[f"{field}_valid_replicates"] = len(values)
        summary[f"{field}_mean"] = values.mean() if len(values) else np.nan
        summary[f"{field}_median"] = values.median() if len(values) else np.nan
    return summary


def run_phase(pilot_dir, output_dir, phase, *, selection_file=None, replicates=None, workers=1, prior_phase_dirs=()):
    pilot_dir, output_dir = Path(pilot_dir), Path(output_dir)
    require(phase in PHASE_CODES, "Unknown phase")
    replicates = DEFAULT_REPLICATES[phase] if replicates is None else replicates
    require(type(replicates) is int and 1 <= replicates <= DEFAULT_REPLICATES[phase], "Replicates exceed the phase budget or are invalid")
    require(type(workers) is int and 1 <= workers <= 16, "Workers must be in 1..16")
    require((phase == "screen") == (selection_file is None), "Screen uses every frozen source; confirm/extend require a source-ID selection CSV")
    require(not output_dir.exists(), "Output path already exists; choose a fresh directory")
    require(not output_dir.resolve().is_relative_to(ROOT) or output_dir.resolve().is_relative_to(ROOT / "outputs"), "Repository-local raw outputs must be under ignored outputs/")
    start = time.monotonic()
    original, original_bindings = verify_archive(pilot_dir, "bounded_observation_repair_pilot")
    required = {"parameter_values.csv.gz", "deterministic_projections.csv.gz", "stage_b_replicates.csv.gz", "validation_replicates.csv.gz"}
    require(required.issubset(original_bindings), "Missing original pilot inputs")
    for bound in original["source_bindings"]:
        if bound["path"].startswith(("src/galaxias_model/", "data/")):
            require(pilot.file_hash(ROOT / bound["path"]) == {k: bound[k] for k in ["bytes", "sha256"]}, f"Scientific source/input changed since pilot: {bound['path']}")
    parameters = pd.read_csv(pilot_dir / "parameter_values.csv.gz", float_precision="round_trip")
    deterministic = pd.read_csv(pilot_dir / "deterministic_projections.csv.gz", float_precision="round_trip")
    require(not parameters.duplicated([*pilot.IDENTITY, "parameter_id"]).any() and parameters.groupby(pilot.IDENTITY).size().eq(40).all(), "Invalid frozen parameter grain")
    require(not deterministic.duplicated(pilot.IDENTITY).any(), "Duplicate deterministic source")
    source_columns = [*pilot.IDENTITY, "proposal_index", "proposal_seed"]
    sources = parameters[source_columns].drop_duplicates()
    require(not sources.duplicated(pilot.IDENTITY).any(), "Source metadata differs within parameter table")
    keys = lambda table: set(table[pilot.IDENTITY].itertuples(index=False, name=None))
    require(keys(sources) == keys(deterministic) and len(sources) == original["counts"]["prior_sources"], "Frozen source coverage/count mismatch")
    selection_binding = None
    if selection_file is not None:
        selection_file = Path(selection_file)
        selected = pd.read_csv(selection_file)
        require(set(selected.columns) == set(pilot.IDENTITY) and not selected.duplicated(pilot.IDENTITY).any() and len(selected) > 0, "Selection CSV requires unique source IDs only")
        require(keys(selected).issubset(keys(sources)), "Selection contains unknown sources")
        sources = sources.merge(selected, on=pilot.IDENTITY, validate="one_to_one")
        selection_binding = {"name": selection_file.name, **pilot.file_hash(selection_file)}
    require(1 <= len(sources) <= SOURCE_CAPS[phase], "Source count exceeds phase cap")
    old_seeds = np.concatenate([pd.read_csv(pilot_dir / name, usecols=["simulation_seed"]).simulation_seed.to_numpy(dtype=np.int64) for name in ["stage_b_replicates.csv.gz", "validation_replicates.csv.gz"]])
    previous = []
    for directory in map(Path, prior_phase_dirs):
        previous_manifest, previous_bindings = verify_archive(directory, "terminal_history_screen")
        require(previous_manifest["pilot_input_bindings"]["run_manifest.json"] == original_bindings["run_manifest.json"], "Previous phase uses a different original pilot")
        require(previous_manifest["phase"] != phase, "A phase namespace cannot be reused")
        old_seeds = np.concatenate([old_seeds, pd.read_csv(directory / "raw_replicates.csv.gz", usecols=["simulation_seed"]).simulation_seed.to_numpy(dtype=np.int64)])
        previous.append({"phase": previous_manifest["phase"], "input_bindings": previous_bindings})
    planned = np.concatenate([source_seeds(int(row.search_seed), row.family_id, int(row.proposal_index), replicates, phase) for row in sources.itertuples(index=False)])
    require(len(np.unique(planned)) == len(planned) and not np.intersect1d(planned, old_seeds).size, "RNG seed collision within phase or with earlier histories")
    det = deterministic.set_index(pilot.IDENTITY)
    grouped_params = parameters.groupby(pilot.IDENTITY, sort=False)
    tasks = []
    for row in sources.sort_values(pilot.IDENTITY).itertuples(index=False):
        identity = (row.search_seed, row.family_id, row.proposal_id)
        intrinsic = {c: det.loc[identity, c] for c in deterministic if c.startswith(("CT011_", "CT012_"))}
        tasks.append({**dict(zip(pilot.IDENTITY, identity)), "proposal_index": int(row.proposal_index), "parameter_rows": grouped_params.get_group(identity).to_dict("records"), "intrinsic": intrinsic, "phase": phase, "replicates": replicates, "data_dir": str(ROOT / "data")})
    output_dir.mkdir(parents=True, exist_ok=False)
    sources.sort_values(pilot.IDENTITY).to_csv(output_dir / "sources.csv", index=False)
    summary_parts, actual_seed_parts = [], []
    pool = ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) if workers > 1 else None
    try:
        batches = pool.map(simulate_source, tasks, chunksize=1, buffersize=2 * workers) if pool else map(simulate_source, tasks)
        with gzip.open(output_dir / "raw_replicates.csv.gz", "wt", encoding="utf-8", newline="") as stream:
            for completed, batch in enumerate(batches, start=1):
                raw = pd.DataFrame(batch)
                require(len(raw) == replicates and not raw.duplicated([*pilot.IDENTITY, "replicate_index"]).any(), "Worker replicate count/grain mismatch")
                raw.to_csv(stream, index=False, header=completed == 1)
                summary_parts.append(summarise_batch(raw))
                actual_seed_parts.append(raw.simulation_seed.to_numpy(dtype=np.int64))
                if completed == 1 or completed % 25 == 0 or completed == len(tasks):
                    print(f"{phase}: {completed}/{len(tasks)} sources; {completed * replicates} histories", flush=True)
    finally:
        if pool:
            pool.shutdown(cancel_futures=True)
    actual = np.concatenate(actual_seed_parts)
    require(np.array_equal(np.sort(actual), np.sort(planned)), "Executed seeds differ from verified plan")
    summary = pd.concat(summary_parts, ignore_index=True)
    summary["source_inclusion_basis"] = "complete_frozen_prior" if phase == "screen" else "frozen_source_id_csv"
    summary.to_csv(output_dir / "source_summary.csv", index=False)
    binding_paths = sorted((ROOT / "src/galaxias_model").glob("*.py")) + [Path(__file__), ROOT / "scripts/run_observation_repair_pilot.py", ROOT / "pyproject.toml", ROOT / "uv.lock", ROOT / "docs/terminal_history_screen.md"]
    manifest = {"status": "complete", "scope": "terminal_history_screen", "phase": phase, "phase_code": PHASE_CODES[phase], "replicates": replicates, "source_identity": pilot.IDENTITY, "source_count": len(sources),
                "config": {"replicates": replicates, "workers": workers, "source_cap": SOURCE_CAPS[phase]},
                "counts": {"frozen_prior_sources": original["counts"]["prior_sources"], "simulated_sources": len(sources), "historical_runs": len(actual), "deterministic_runs": 0, "source_profile_rows": len(summary)},
                "pilot_input_bindings": original_bindings, "selection_input_binding": selection_binding, "previous_phase_bindings": previous,
                "source_bindings": [{"path": str(p.relative_to(ROOT)), **pilot.file_hash(p)} for p in binding_paths],
                "runtime": {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__, "platform": platform.platform()},
                "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "policies": {"selection": "No parameter sampling or source selection. Sources copied from exact pilot prior or externally frozen source-ID CSV. All four profile summaries describe shared histories; legacy is diagnostic.", "censoring": "first_zero_year is missing if no zero is observed by2002; no artificial event year. Event-year mean/median are conditional on available events with valid replicate counts. surviving_1996 uses end-1996 state; present_at_1996_proxy uses prior recorded state.", "seeds": "Fresh phase namespaces checked before simulation against original pilot and supplied preceding-phase histories."},
                "outputs": {p.name: pilot.file_hash(p) for p in sorted(output_dir.iterdir()) if p.is_file()}, "elapsed_seconds": round(time.monotonic() - start, 3)}
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--phase", choices=PHASE_CODES, required=True)
    parser.add_argument("--selection-file", type=Path)
    parser.add_argument("--replicates", type=int)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--prior-phase-dir", type=Path, action="append", default=[], dest="prior_phase_dirs")
    args = parser.parse_args()
    run_phase(**vars(args))
