#!/usr/bin/env python3
"""Prepare compact annual-abundance replay data from a frozen validation archive.

This module is deliberately an archive reconciliation step.  It does not apply
detection weights or select sources.  Every trajectory is reconstructed at the
``simulation_seed`` recorded in the validation archive and is accepted only if
all archived diagnostics and target-score fields agree.
"""
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
from typing import Any, Iterable, Iterator, Mapping, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_conditional_calibration as calibration
from scripts import run_observation_repair_pilot as pilot
from scripts import run_terminal_history_screen as terminal_screen


IDENTITY = calibration.IDENTITY
SOURCE_NAMESPACE = calibration.SOURCE_NAMESPACE
VALIDATION_PHASE = "validate"
MAX_WORKERS = 32
DEFAULT_CHUNK_SIZE = 4096
REPLAY_RTOL = 1e-12
REPLAY_ATOL = 1e-12

COMPACT_COLUMNS = [
    *(f"pos_N_R_{year}" for year in (1988, 1989, 1990, 1991, 1992, 1996)),
    *(f"neg_N_L_{year}" for year in (1988, 1989)),
    *(f"neg_N_total_{year}" for year in (1998, 1999, 2000, 2001, 2002)),
]
OUTPUT_COLUMNS = [*IDENTITY, "source_id", "replicate_index", "simulation_seed", *COMPACT_COLUMNS, "surviving_2002", "n_total_2002"]
ROW_KEY = [*IDENTITY, "replicate_index"]
ARCHIVE_META_COLUMNS = [*IDENTITY, "source_id", "stage", "replicate_index", "simulation_seed"]
EXACT_NUMERIC_FIELDS = {
    "missing_positive_record_episodes", "lake_nondetection_occupied_episodes",
    "natural_nondetection_occupied_episodes", "nondetection_occupied_episodes",
    "n_total_1995", "n_total_1996", "n_refuge_1995", "n_total_2002",
    "latent_last_presence_year", "first_zero_year",
    "CT003_projected_primary", "CT009_projected_primary", "CT009_projected_secondary",
    "CT011_projected_secondary", "CT012_projected_secondary",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def file_hash(path: Path) -> dict[str, Any]:
    digest = calibration.file_hash(path)
    return {"bytes": int(digest["bytes"]), "sha256": str(digest["sha256"])}


def _runtime() -> dict[str, str]:
    return {
        "python": sys.version,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "platform": platform.platform(),
    }


def _replay_bindings() -> list[dict[str, Any]]:
    paths = [Path(__file__), ROOT / "docs" / "common_model_protocol.md"]
    return [{"path": str(path.relative_to(ROOT)), **file_hash(path)} for path in paths if path.exists()]


def _verify_runtime(manifest: Mapping[str, Any], label: str) -> None:
    recorded = manifest.get("runtime")
    require(isinstance(recorded, Mapping), f"{label} archive lacks a runtime binding")
    current = _runtime()
    for field in ("python", "numpy", "pandas"):
        require(recorded.get(field) == current[field], f"{label} runtime mismatch for {field}")


def _verify_archive(directory: Path, *, phase: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest, bindings = calibration.verify_archive(directory, phase=phase)
    _verify_runtime(manifest, phase)
    return manifest, bindings


def _resolve_optional_archive(validation_dir: Path, name: str) -> Path:
    candidate = validation_dir.parent / name
    require(candidate.exists(), f"Cannot resolve required {name} archive beside validation archive")
    return candidate


def _verify_ancestry(validation_dir: Path, validation_manifest: Mapping[str, Any], prior_dir: Path, prior_manifest: Mapping[str, Any], screen_dir: Path | None, refine_dir: Path | None) -> dict[str, Any]:
    prior_binding = validation_manifest.get("prior_input_binding", {}).get("run_manifest.json")
    require(prior_binding == file_hash(prior_dir / "run_manifest.json"), "Validation archive is bound to a different prior archive")
    previous = validation_manifest.get("previous_phase_bindings", [])
    require({entry.get("phase") for entry in previous} == {"screen", "refine"}, "Validation archive lacks screen/refine ancestry")
    resolved: dict[str, Any] = {"prior": file_hash(prior_dir / "run_manifest.json"), "previous": []}
    for name, directory in (("screen", screen_dir), ("refine", refine_dir)):
        require(directory is not None, f"Validation ancestry requires {name} archive")
        manifest, bindings = _verify_archive(Path(directory), phase=name)
        require(manifest.get("prior_input_binding", {}).get("run_manifest.json") == file_hash(prior_dir / "run_manifest.json"), f"{name} archive uses a different prior archive")
        expected = next((entry for entry in previous if entry.get("phase") == name), None)
        require(expected is not None and expected.get("bindings") == bindings, f"Validation ancestry binding mismatch for {name}")
        resolved["previous"].append({"phase": name, "bindings": bindings})
    return resolved


def _identity_tuple(row: Mapping[str, Any]) -> tuple[int, str, str]:
    try:
        search_seed = int(row[IDENTITY[0]])
        family_id = str(row[IDENTITY[1]])
        proposal_id = str(row[IDENTITY[2]])
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError(f"Malformed source identity: {row}") from exc
    require(family_id and proposal_id and not family_id.lower() == "nan" and not proposal_id.lower() == "nan", "Malformed source identity")
    return search_seed, family_id, proposal_id


def _integer_series(values: pd.Series, label: str, *, positive: bool = False) -> np.ndarray:
    numeric = pd.to_numeric(values, errors="coerce")
    array = numeric.to_numpy(dtype=float)
    require(np.isfinite(array).all(), f"Malformed {label}")
    require(np.equal(array, np.floor(array)).all(), f"Malformed {label}")
    require((array >= (1 if positive else 0)).all(), f"Malformed {label}")
    return array.astype(np.int64)


def _source_table(prior: pd.DataFrame, validation: pd.DataFrame) -> pd.DataFrame:
    for name, table in (("prior", prior), ("validation", validation)):
        require(set(IDENTITY + ["source_id", "proposal_index", "proposal_seed"]).issubset(table.columns), f"{name} source table lacks metadata")
        require(not table.duplicated(IDENTITY).any(), f"{name} source table has duplicate identities")
        require(not table.source_id.duplicated().any(), f"{name} source table has duplicate source IDs")
        for row in table.to_dict("records"):
            identity = _identity_tuple(row)
            require(str(row["source_id"]) == calibration.source_id(identity, SOURCE_NAMESPACE), f"{name} source ID does not match composite identity")
        _integer_series(table["proposal_index"], f"{name} proposal_index", positive=True)
        _integer_series(table["proposal_seed"], f"{name} proposal_seed")
    merged = validation.merge(prior[IDENTITY + ["source_id", "proposal_index", "proposal_seed"]], on=IDENTITY, how="left", suffixes=("", "_prior"), validate="one_to_one")
    require(merged.source_id_prior.notna().all(), "Validation source is absent from prior archive")
    require(merged.source_id.astype(str).tolist() == merged.source_id_prior.astype(str).tolist(), "Validation source_id differs from prior archive")
    for field in ("proposal_index", "proposal_seed"):
        require(np.array_equal(_integer_series(merged[field], f"validation {field}"), _integer_series(merged[f"{field}_prior"], f"prior {field}")), f"Validation {field} differs from prior archive")
    return validation.copy()


def _parameter_table(parameters: pd.DataFrame) -> pd.DataFrame:
    parameters = parameters.copy()
    require(set(IDENTITY + ["parameter_id", "proposal_index", "proposal_seed"]).issubset(parameters.columns), "Parameter table lacks source metadata")
    require(not parameters.duplicated(IDENTITY + ["parameter_id"]).any(), "Parameter table has duplicate parameter rows")
    counts = parameters.groupby(IDENTITY, sort=False).size()
    require(counts.eq(40).all(), "Each frozen source must contain exactly 40 parameters")
    _integer_series(parameters["proposal_index"], "parameter proposal_index", positive=True)
    _integer_series(parameters["proposal_seed"], "parameter proposal_seed")
    # Force the archived text representation through the exact round-trip path
    # used by the production runner before constructing worker tasks.
    require(parameters[IDENTITY].notna().all(axis=None), "Parameter table contains missing source identity")
    return parameters


def _load_membership(path: Path, validation_sources: pd.DataFrame, expected_manifest: Path) -> dict[str, Any]:
    membership = pd.read_csv(path, dtype={"family_id": str, "proposal_id": str}, float_precision="round_trip")
    require(set(IDENTITY + ["profile", "cohort"]).issubset(membership.columns), "Frozen membership lacks source identity/cohort fields")
    require(not membership[IDENTITY].isna().any(axis=None), "Frozen membership contains missing identity")
    require(not membership.duplicated([*IDENTITY, "profile", "cohort"], keep=False).any(), "Frozen membership contains duplicate source/profile/cohort rows")
    require(expected_manifest.exists(), f"Missing frozen membership manifest: {expected_manifest}")
    membership_manifest = json.loads(expected_manifest.read_text(encoding="utf-8"))
    expected = membership_manifest.get("outputs", {}).get(path.name)
    require(expected is not None, f"Frozen membership is not an output of {expected_manifest}")
    require(file_hash(path) == expected, "Frozen membership hash differs from its analysis manifest")
    member_ids = {_identity_tuple(row) for row in membership.to_dict("records")}
    validation_ids = {_identity_tuple(row) for row in validation_sources.to_dict("records")}
    require(member_ids == validation_ids, "Frozen membership union differs from validation source table")
    return {"path": str(path.resolve()), "manifest": str(expected_manifest.resolve()), **file_hash(path), "rows": int(len(membership)), "source_count": int(len(member_ids))}


def _resolve_membership_manifest(path: Path, validation_dir: Path, refine_dir: Path) -> Path:
    candidates = [path.parent / "analysis_manifest.json", refine_dir.parent / "refine_analysis" / "analysis_manifest.json", validation_dir.parent / "refine_analysis" / "analysis_manifest.json"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError("Cannot resolve frozen membership analysis manifest")


def _iter_source_frames(path: Path, *, chunksize: int = DEFAULT_CHUNK_SIZE) -> Iterator[pd.DataFrame]:
    """Yield one source at a time while retaining only a bounded chunk."""
    pending: pd.DataFrame | None = None
    pending_key: tuple[int, str, str] | None = None
    reader = pd.read_csv(path, chunksize=chunksize, float_precision="round_trip")
    for chunk in reader:
        require(set(IDENTITY + ["source_id", "stage", "replicate_index", "simulation_seed"]).issubset(chunk.columns), "Raw validation archive lacks required columns")
        row_keys = [_identity_tuple(row) for row in chunk[IDENTITY].to_dict("records")]
        block_keys = []
        for key in row_keys:
            if not block_keys or key != block_keys[-1]:
                block_keys.append(key)
        require(len(block_keys) == len(set(block_keys)), "Raw validation source rows are noncontiguous")
        for _, part in chunk.groupby(IDENTITY, sort=False, dropna=False):
            key = _identity_tuple(part.iloc[0].to_dict())
            if pending is None:
                pending, pending_key = part.copy(), key
            elif key == pending_key:
                pending = pd.concat([pending, part], ignore_index=True)
            else:
                yield pending
                pending, pending_key = part.copy(), key
    if pending is not None:
        yield pending


def _raw_schema(path: Path) -> list[str]:
    columns = pd.read_csv(path, nrows=0).columns.tolist()
    require(len(columns) == len(set(columns)), "Raw validation archive has duplicate columns")
    require(set(ARCHIVE_META_COLUMNS).issubset(columns), "Raw validation archive lacks archive metadata columns")
    return columns


def _preflight_raw(validation_dir: Path, sources: pd.DataFrame, replicates: int, columns: Sequence[str]) -> None:
    expected = [tuple(row) for row in sources.sort_values(IDENTITY)[IDENTITY].itertuples(index=False, name=None)]
    seen_seeds: set[int] = set()
    seen_keys: set[tuple[tuple[int, str, str], int]] = set()
    observed: list[tuple[int, str, str]] = []
    for frame in _iter_source_frames(validation_dir / "raw_replicates.csv.gz"):
        identity = _identity_tuple(frame.iloc[0].to_dict())
        require(identity in expected, f"Raw validation row has unknown source: {identity}")
        require(all(_identity_tuple(row) == identity for row in frame.to_dict("records")), "Source rows are not contiguous")
        require(len(frame) == replicates, f"Source {identity} has wrong replicate count")
        require(frame.stage.astype(str).eq(VALIDATION_PHASE).all(), "Raw validation archive contains a non-validation stage")
        require(frame.source_id.astype(str).eq(calibration.source_id(identity, SOURCE_NAMESPACE)).all(), f"Raw source ID mismatch for {identity}")
        reps = _integer_series(frame.replicate_index, "replicate index", positive=True)
        seeds = _integer_series(frame.simulation_seed, "simulation seed")
        require(set(reps) == set(range(1, replicates + 1)), f"Missing or duplicate replicate rows for {identity}")
        for rep, seed in zip(reps.astype(int), seeds.astype(np.int64)):
            key = (identity, int(rep))
            require(key not in seen_keys, "Duplicate source/replicate row")
            require(int(seed) not in seen_seeds, "Duplicate simulation seed")
            seen_keys.add(key)
            seen_seeds.add(int(seed))
        observed.append(identity)
    require(observed == expected, "Raw validation source order/coverage differs from frozen sources")
    require(len(seen_keys) == len(expected) * replicates, "Raw validation row count mismatch")
    require(list(columns) == list(pd.read_csv(validation_dir / "raw_replicates.csv.gz", nrows=0).columns), "Raw schema changed during preflight")


def _compact_abundance(history: Any) -> dict[str, Any]:
    trajectory = history.trajectory_table.set_index("year")
    require(trajectory.index.is_unique, "Replay trajectory has duplicate years")
    required = {year - 1 for year in (1988, 1989, 1990, 1991, 1992, 1996, 1998, 1999, 2000, 2001, 2002)} | {2002}
    require(required.issubset(set(trajectory.index)), "Replay trajectory lacks required annual state")
    values: dict[str, Any] = {}
    for year in (1988, 1989, 1990, 1991, 1992, 1996):
        values[f"pos_N_R_{year}"] = float(trajectory.loc[year - 1, "N_R"])
    for year in (1988, 1989):
        values[f"neg_N_L_{year}"] = float(trajectory.loc[year - 1, "N_L"])
    for year in (1998, 1999, 2000, 2001, 2002):
        values[f"neg_N_total_{year}"] = float(trajectory.loc[year - 1, "N_total"])
    terminal_total = float(trajectory.loc[2002, "N_total"])
    require(np.isfinite(list(values.values())).all() and np.isfinite(terminal_total) and min([*values.values(), terminal_total]) >= 0, "Replay trajectory has invalid abundance")
    values["surviving_2002"] = bool(terminal_total > 0)
    values["n_total_2002"] = terminal_total
    return values


def _compare(expected: pd.DataFrame, actual: pd.DataFrame, columns: Sequence[str]) -> dict[str, dict[str, float]]:
    require(list(actual.columns) == list(columns), "Replay row schema differs from archived raw schema")
    require(len(actual) == len(expected), "Replay row count differs from archive")
    deviations: dict[str, dict[str, float]] = {}
    for field in columns:
        left = expected[field].to_numpy()
        right = actual[field].to_numpy()
        if pd.api.types.is_bool_dtype(expected[field]) or pd.api.types.is_object_dtype(expected[field]) or field in ARCHIVE_META_COLUMNS:
            equal = True
            for left_value, right_value in zip(left, right):
                if pd.isna(left_value) and pd.isna(right_value):
                    continue
                if left_value != right_value:
                    equal = False
                    break
            require(equal, f"Replay mismatch in {field}")
            continue
        left_num = pd.to_numeric(expected[field], errors="coerce").to_numpy(dtype=float)
        right_num = pd.to_numeric(actual[field], errors="coerce").to_numpy(dtype=float)
        if field in EXACT_NUMERIC_FIELDS:
            ok = (left_num == right_num) | (np.isnan(left_num) & np.isnan(right_num))
        else:
            ok = np.isclose(left_num, right_num, rtol=REPLAY_RTOL, atol=REPLAY_ATOL, equal_nan=True)
        require(bool(ok.all()), f"Replay mismatch in {field}")
        finite = np.isfinite(left_num) & np.isfinite(right_num)
        if finite.any():
            abs_dev = np.abs(left_num[finite] - right_num[finite])
            rel_dev = abs_dev / np.maximum(np.abs(left_num[finite]), REPLAY_ATOL)
            deviations[field] = {"max_abs": float(abs_dev.max()), "max_rel": float(rel_dev.max())}
    return deviations


def _replay_source(task: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    inputs = calibration._load_inputs_cached(task["data_dir"])
    params = calibration.build_resolved_parameters_from_sample(inputs, task["family_id"], pd.DataFrame(task["parameter_rows"]))
    config = calibration._scenario_config(inputs, "historical_lake", True)
    expected = task["expected"]
    rows: list[dict[str, Any]] = []
    compact: list[dict[str, Any]] = []
    for record in expected.to_dict("records"):
        seed = int(record["simulation_seed"])
        history = calibration.run_historical_simulation(params, task["family_id"], config, seed=seed)
        row = {key: task[key] for key in IDENTITY}
        row.update(source_id=task["source_id"], stage=VALIDATION_PHASE, replicate_index=int(record["replicate_index"]), simulation_seed=seed)
        row.update(terminal_screen.terminal_features(history))
        row.update(pilot.scored_fields(history, inputs))
        row.update(task["intrinsic"])
        rows.append(row)
        values = _compact_abundance(history)
        compact.append({**{key: task[key] for key in IDENTITY}, "source_id": task["source_id"], "replicate_index": int(record["replicate_index"]), "simulation_seed": seed, **values})
    actual = pd.DataFrame(rows, columns=task["columns"])
    deviations = _compare(expected.reset_index(drop=True), actual, task["columns"])
    return compact, deviations


def _merge_deviations(total: dict[str, dict[str, float]], current: Mapping[str, Mapping[str, float]]) -> None:
    for field, values in current.items():
        prior = total.setdefault(field, {"max_abs": 0.0, "max_rel": 0.0})
        prior["max_abs"] = max(prior["max_abs"], float(values["max_abs"]))
        prior["max_rel"] = max(prior["max_rel"], float(values["max_rel"]))


def _execute(tasks: Iterable[dict[str, Any]], workers: int) -> Iterator[tuple[list[dict[str, Any]], dict[str, dict[str, float]]]]:
    if workers == 1:
        yield from map(_replay_source, tasks)
        return
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
        yield from pool.map(_replay_source, tasks, chunksize=1, buffersize=max(1, 2 * workers))


def _preflight_replay(prior_dir: Path, validation_dir: Path, membership: Path, *, screen_dir: Path | None = None, refine_dir: Path | None = None, chunk_size: int = DEFAULT_CHUNK_SIZE) -> dict[str, Any]:
    """Verify all replay inputs without creating output or simulating histories."""
    prior_dir, validation_dir, membership = map(Path, (prior_dir, validation_dir, membership))
    require(type(chunk_size) is int and chunk_size >= 1, "chunk_size must be positive")
    validation_manifest, validation_bindings = _verify_archive(validation_dir, phase=VALIDATION_PHASE)
    prior_manifest, prior_bindings = _verify_archive(prior_dir, phase="prior")
    screen_dir = _resolve_optional_archive(validation_dir, "screen") if screen_dir is None else Path(screen_dir)
    refine_dir = _resolve_optional_archive(validation_dir, "refine") if refine_dir is None else Path(refine_dir)
    ancestry = _verify_ancestry(validation_dir, validation_manifest, prior_dir, prior_manifest, screen_dir, refine_dir)
    require(validation_manifest.get("source_id_namespace") == SOURCE_NAMESPACE and validation_manifest.get("source_identity") == IDENTITY, "Validation source contract is incompatible")
    replicates = validation_manifest.get("replicates")
    require(type(replicates) is int and replicates >= 1, "Validation replicate count is malformed")

    parameters = _parameter_table(pd.read_csv(prior_dir / "parameter_values.csv.gz", float_precision="round_trip"))
    prior_sources = pd.read_csv(prior_dir / "sources.csv", float_precision="round_trip")
    validation_sources = _source_table(prior_sources, pd.read_csv(validation_dir / "sources.csv", float_precision="round_trip"))
    intrinsic = pd.read_csv(prior_dir / "source_summary.csv", float_precision="round_trip")
    require(set(IDENTITY + ["source_id"]).issubset(intrinsic.columns) and not intrinsic.duplicated(IDENTITY).any(), "Prior intrinsic cache is malformed")
    intrinsic_cols = [column for column in intrinsic.columns if column.startswith(("CT011_", "CT012_"))]
    require(intrinsic_cols, "Prior intrinsic cache is empty")
    membership_manifest = _resolve_membership_manifest(membership, validation_dir, refine_dir)
    membership_binding = _load_membership(membership, validation_sources, membership_manifest)
    columns = _raw_schema(validation_dir / "raw_replicates.csv.gz")
    _preflight_raw(validation_dir, validation_sources, replicates, columns)
    replay_bindings = _replay_bindings()

    groups = parameters.groupby(IDENTITY, sort=False)
    intrinsic_index = intrinsic.set_index(IDENTITY)
    source_index = validation_sources.set_index(IDENTITY)
    return {"prior_dir": prior_dir, "validation_dir": validation_dir, "membership": membership, "validation_manifest": validation_manifest, "validation_bindings": validation_bindings, "prior_manifest": prior_manifest, "prior_bindings": prior_bindings, "ancestry": ancestry, "replicates": replicates, "parameters": parameters, "validation_sources": validation_sources, "intrinsic": intrinsic, "intrinsic_cols": intrinsic_cols, "columns": columns, "groups": groups, "intrinsic_index": intrinsic_index, "source_index": source_index, "membership_binding": membership_binding, "replay_bindings": replay_bindings, "screen_dir": screen_dir, "refine_dir": refine_dir}


def preflight_validation(prior_dir: Path, validation_dir: Path, membership: Path, *, screen_dir: Path | None = None, refine_dir: Path | None = None, chunk_size: int = DEFAULT_CHUNK_SIZE) -> dict[str, Any]:
    """Return concise metadata after strict archive checks; never simulates or writes."""
    context = _preflight_replay(prior_dir, validation_dir, membership, screen_dir=screen_dir, refine_dir=refine_dir, chunk_size=chunk_size)
    return {"status": "preflight_complete", "source_count": int(len(context["validation_sources"])), "replicates": int(context["replicates"]), "historical_runs": int(len(context["validation_sources"]) * context["replicates"]), "inputs": {"prior": context["prior_bindings"], "validation": context["validation_bindings"], "membership": context["membership_binding"]}, "ancestry": context["ancestry"], "source_bindings": {"prior": {key: context["prior_manifest"].get(key, []) for key in ("source_files", "input_files", "spec_documents")}, "validation": {key: context["validation_manifest"].get(key, []) for key in ("source_files", "input_files", "spec_documents")}, "replay": context["replay_bindings"]}, "runtime": _runtime()}


def replay_validation(prior_dir: Path, validation_dir: Path, output_dir: Path, membership: Path, *, screen_dir: Path | None = None, refine_dir: Path | None = None, workers: int = 1, chunk_size: int = DEFAULT_CHUNK_SIZE) -> dict[str, Any]:
    """Replay and verify a complete validation archive into compact abundance rows."""
    prior_dir, validation_dir, output_dir, membership = map(Path, (prior_dir, validation_dir, output_dir, membership))
    require(type(workers) is int and 1 <= workers <= MAX_WORKERS, "workers must be in 1..32")
    require(not output_dir.exists(), "Output path already exists; choose a fresh directory")
    start = time.monotonic()
    context = _preflight_replay(prior_dir, validation_dir, membership, screen_dir=screen_dir, refine_dir=refine_dir, chunk_size=chunk_size)
    validation_manifest = context["validation_manifest"]
    validation_bindings = context["validation_bindings"]
    prior_manifest = context["prior_manifest"]
    prior_bindings = context["prior_bindings"]
    ancestry = context["ancestry"]
    replicates = context["replicates"]
    validation_sources = context["validation_sources"]
    intrinsic = context["intrinsic"]
    intrinsic_cols = context["intrinsic_cols"]
    columns = context["columns"]
    groups = context["groups"]
    intrinsic_index = context["intrinsic_index"]
    source_index = context["source_index"]
    membership_binding = context["membership_binding"]
    replay_bindings = context["replay_bindings"]

    def tasks() -> Iterator[dict[str, Any]]:
        for expected in _iter_source_frames(validation_dir / "raw_replicates.csv.gz", chunksize=chunk_size):
            identity = _identity_tuple(expected.iloc[0].to_dict())
            source = source_index.loc[identity]
            require(identity in groups.groups, f"Validation source lacks prior parameters: {identity}")
            cache = intrinsic_index.loc[identity]
            require(isinstance(cache, pd.Series), "Intrinsic cache has duplicate source")
            intrinsic_values = {field: cache[field] for field in intrinsic_cols}
            require(all(pd.notna(value) for value in intrinsic_values.values()), f"Intrinsic cache has missing fields: {identity}")
            yield {**dict(zip(IDENTITY, identity)), "source_id": str(source.source_id), "proposal_index": int(source.proposal_index), "data_dir": str((ROOT / "data").resolve()), "parameter_rows": groups.get_group(identity).to_dict("records"), "intrinsic": intrinsic_values, "expected": expected.reset_index(drop=True), "columns": columns}

    # Only after every input has passed preflight do we create the destination.
    output_dir.mkdir(parents=True, exist_ok=False)
    raw_output = output_dir / "compact_abundance_replay.csv.gz"
    max_deviations: dict[str, dict[str, float]] = {}
    completed_sources = 0
    completed_rows = 0
    with gzip.open(raw_output, "wt", encoding="utf-8", newline="") as stream:
        for compact, deviations in _execute(tasks(), workers):
            frame = pd.DataFrame(compact, columns=OUTPUT_COLUMNS)
            frame.to_csv(stream, index=False, header=completed_sources == 0, float_format="%.17g")
            _merge_deviations(max_deviations, deviations)
            completed_sources += 1
            completed_rows += len(frame)
    require(completed_sources == len(validation_sources), "Replay source count differs from validation archive")
    require(completed_rows == len(validation_sources) * replicates, "Replay row count differs from validation archive")

    manifest = {
        "status": "complete",
        "scope": "conditional_detection_replay_preparation",
        "phase": VALIDATION_PHASE,
        "source_identity": IDENTITY,
        "source_id_namespace": SOURCE_NAMESPACE,
        "replicates": replicates,
        "source_count": int(len(validation_sources)),
        "counts": {"sources": completed_sources, "historical_runs": completed_rows, "compact_columns": len(COMPACT_COLUMNS)},
        "data_dir": str((ROOT / "data").resolve()),
        "provenance_data_dir": str(prior_manifest.get("data_dir", "")),
        "inputs": {"prior": {"path": str(prior_dir.resolve()), "run_manifest": prior_bindings["run_manifest.json"], "bindings": prior_bindings}, "validation": {"path": str(validation_dir.resolve()), "bindings": validation_bindings}, "membership": membership_binding},
        "source_bindings": {"prior": {key: prior_manifest.get(key, []) for key in ("source_files", "input_files", "spec_documents")}, "validation": {key: validation_manifest.get(key, []) for key in ("source_files", "input_files", "spec_documents")}, "replay": replay_bindings},
        "source_files": [*prior_manifest.get("source_files", []), *[binding for binding in replay_bindings if binding["path"].endswith(".py")]],
        "input_files": prior_manifest.get("input_files", []),
        "spec_documents": [*prior_manifest.get("spec_documents", []), *[binding for binding in replay_bindings if binding["path"].endswith(".md")]],
        "ancestry": ancestry,
        "policies": {"seed": "Use archived validation simulation_seed verbatim; no seed derivation or detection weighting.", "parameters": "Prior parameter_values.csv.gz read with pandas float_precision=round_trip and checked at 40 rows per source.", "abundance_state": "Named abundance fields use state year-1; n_total_2002 and surviving_2002 use state 2002."},
        "tolerance": {"rtol": REPLAY_RTOL, "atol": REPLAY_ATOL},
        "max_replay_deviations": max_deviations,
        "runtime": _runtime(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "config": {"workers": workers, "chunk_size": chunk_size},
        "outputs": {raw_output.name: file_hash(raw_output)},
        "elapsed_seconds": round(time.monotonic() - start, 3),
    }
    (output_dir / "replay_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior-dir", type=Path, required=True)
    parser.add_argument("--validation-dir", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--screen-dir", type=Path)
    parser.add_argument("--refine-dir", type=Path)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    args = parser.parse_args()
    manifest = replay_validation(**vars(args))
    print(json.dumps({"status": manifest["status"], "sources": manifest["source_count"], "historical_runs": manifest["counts"]["historical_runs"], "output": str(args.output_dir / "compact_abundance_replay.csv.gz")}))


if __name__ == "__main__":
    main()
