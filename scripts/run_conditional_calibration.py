#!/usr/bin/env python3
"""Run the bounded conditional-calibration phases at frozen parameter sources.

The prior phase samples parameterisations and evaluates the two deterministic
intrinsic scenarios.  The subsequent phases only simulate fresh stochastic
historical trajectories at those exact parameterisations.  Source selection is
an input to ``refine`` and ``validate`` and is never performed here.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import gzip
import hashlib
import json
import multiprocessing
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_observation_repair_pilot as pilot
from scripts import run_terminal_history_screen as terminal_screen

from galaxias_model.calibration import (
    DEFAULT_FAMILY_ORDER,
    _load_inputs_cached,
    _prepare_parameter_table,
    _scenario_config,
)
from galaxias_model.simulation import run_scenario_simulation, run_historical_simulation
from galaxias_model.sampling import build_resolved_parameters_from_sample
from galaxias_model.types import Module3Config


IDENTITY = ["search_seed", "family_id", "proposal_id"]
SOURCE_NAMESPACE = "conditional_calibration"
PHASE_CODES = {"screen": 1201, "refine": 1301, "validate": 1409}
PHASES = ("prior", *PHASE_CODES)
DEFAULT_REPLICATES = {"screen": 100, "refine": 500, "validate": 2000}
DEFAULT_SEEDS = (20260912, 20260913, 20260914)
DEFAULT_DRAWS = 500
DEFAULT_SCREEN_REPLICATES = 100
MAX_PROPOSALS = 1000
MAX_REPLICATES = 5000
DEFAULT_BUFFER_SIZE = 64
INTRINSIC_SCENARIOS = ("lake_oberon", "strathgordon")
INTRINSIC_TARGETS = ("CT011", "CT012")
NULLABLE_YEARS = ("latent_last_presence_year", "first_zero_year")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def file_hash(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def source_id(identity: Sequence[Any], namespace: str = SOURCE_NAMESPACE) -> str:
    """Build the stable, manifest-namespaced source identifier."""
    require(len(identity) == 3, "Source identity has three fields")
    search_seed, family_id, proposal_id = identity
    return f"{namespace}|{int(search_seed)}|{family_id}|{proposal_id}"


def phase_seed(
    search_seed: int,
    family_id: str,
    proposal_index: int,
    replicate_index: int,
    phase: str,
) -> int:
    require(phase in PHASE_CODES, f"Unknown stochastic phase: {phase}")
    require(1 <= int(proposal_index) <= MAX_PROPOSALS, "proposal_index exceeds seed preflight bound")
    require(1 <= int(replicate_index) <= MAX_REPLICATES, "replicate_index exceeds seed preflight bound")
    return pilot._derive_seed(
        int(search_seed),
        pilot._family_index(str(family_id)),
        int(proposal_index),
        int(replicate_index),
        PHASE_CODES[phase],
    )


def source_seeds(
    search_seed: int,
    family_id: str,
    proposal_index: int,
    replicates: int,
    phase: str,
) -> np.ndarray:
    """Vectorised seed derivation with the same affine map as ``phase_seed``."""
    require(phase in PHASE_CODES, f"Unknown stochastic phase: {phase}")
    require(type(replicates) is int and 1 <= replicates <= MAX_REPLICATES, "Invalid replicate count")
    family_index = pilot._family_index(str(family_id))
    modulus = 2**32 - 5
    value = int(search_seed) % modulus
    for part in (family_index, int(proposal_index)):
        value = (value * 1664525 + 1013904223 + part * 374761393) % modulus
    reps = np.arange(1, replicates + 1, dtype=np.int64)
    values = (value * 1664525 + 1013904223 + reps * 374761393) % modulus
    values = (values * 1664525 + 1013904223 + PHASE_CODES[phase] * 374761393) % modulus
    return np.where(values == 0, 1, values).astype(np.int64, copy=False)


def _validate_families(families: Sequence[str]) -> tuple[str, ...]:
    values = tuple(families)
    require(values and len(set(values)) == len(values), "Families must be nonempty and unique")
    require(set(values).issubset(DEFAULT_FAMILY_ORDER), "Unknown family in conditional calibration")
    return values


def _validate_seeds(seeds: Sequence[int]) -> tuple[int, ...]:
    values = tuple(int(seed) for seed in seeds)
    require(values and len(set(values)) == len(values), "Search seeds must be nonempty and unique")
    require(all(seed >= 0 for seed in values), "Search seeds must be nonnegative")
    return values


def _write_csv(table: pd.DataFrame, path: Path, *, compression: str | None = None) -> None:
    table.to_csv(path, index=False, compression=compression, float_format="%.17g")


def _source_bindings(data_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    source_paths = sorted((ROOT / "src" / "galaxias_model").glob("*.py"))
    source_paths += [Path(__file__), ROOT / "scripts" / "run_observation_repair_pilot.py", ROOT / "scripts" / "run_terminal_history_screen.py", ROOT / "pyproject.toml", ROOT / "uv.lock"]
    input_names = [
        "parameter_priors.csv",
        "model_family_parameter_map.csv",
        "parameter_constraints.csv",
        "evidence_ledger.csv",
        "calibration_targets.csv",
        "calibration_target_details.json",
        "scenario_definitions.json",
    ]
    input_paths = [data_dir / name for name in input_names]
    spec_paths = [ROOT / "docs" / "conditional_calibration.md"]

    def bind(paths: Iterable[Path], *, required: bool = False) -> list[dict[str, Any]]:
        result = []
        for path in paths:
            if not path.exists():
                if required:
                    raise ValueError(f"Required bound file is missing: {path}")
                continue
            name = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
            result.append({"path": name, **file_hash(path)})
        return result

    return bind(source_paths), bind(input_paths, required=True), bind(spec_paths)


def _verify_bindings(manifest: Mapping[str, Any]) -> None:
    for key in ("source_files", "input_files", "spec_documents"):
        for binding in manifest.get(key, []):
            path = ROOT / binding["path"] if not Path(binding["path"]).is_absolute() else Path(binding["path"])
            require(path.exists(), f"Bound file is missing: {binding['path']}")
            require(file_hash(path) == {k: binding[k] for k in ("bytes", "sha256")}, f"Bound file changed: {binding['path']}")


def verify_archive(directory: Path, expected_scope: str | None = None, *, phase: str | None = None) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    directory = Path(directory)
    manifest_path = directory / "run_manifest.json"
    require(manifest_path.exists(), f"Missing run manifest: {directory}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("status") == "complete" and manifest.get("scope") == "conditional_calibration", f"Incomplete or unexpected archive: {directory}")
    if expected_scope is not None:
        require(manifest.get("scope") == expected_scope, f"Unexpected archive scope: {manifest.get('scope')}")
    if phase is not None:
        require(manifest.get("phase") == phase, f"Expected {phase} archive, got {manifest.get('phase')}")
    bindings = {"run_manifest.json": file_hash(manifest_path)}
    for name, expected in manifest.get("outputs", {}).items():
        require(Path(name).name == name, "Archive output must be a direct filename")
        path = directory / name
        require(path.exists(), f"Archive output is missing: {path}")
        bindings[name] = file_hash(path)
        require(bindings[name] == expected, f"Archive output hash mismatch: {path}")
    _verify_bindings(manifest)
    return manifest, bindings


def _parameter_table(parameters: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    require(set(IDENTITY + ["parameter_id", "proposal_index", "proposal_seed"]).issubset(parameters.columns), "Parameter table lacks source metadata")
    require(not parameters.duplicated(IDENTITY + ["parameter_id"]).any(), "Duplicate parameter row")
    counts = parameters.groupby(IDENTITY, sort=False).size()
    require(counts.eq(40).all(), "Each frozen source must contain exactly 40 parameters")
    sources = parameters[IDENTITY + ["proposal_index", "proposal_seed"]].drop_duplicates()
    require(not sources.duplicated(IDENTITY).any(), "Source metadata differs within parameter table")
    require(sources["proposal_index"].between(1, MAX_PROPOSALS).all(), "Proposal index exceeds preflight bound")
    return parameters, sources


def _build_prior_tables(
    data_dir: Path,
    families: Sequence[str],
    seeds: Sequence[int],
    draws: int,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    families = _validate_families(families)
    seeds = _validate_seeds(seeds)
    require(type(draws) is int and 1 <= draws <= MAX_PROPOSALS, "draws must be in 1..1000")
    inputs = _load_inputs_cached(str(data_dir.resolve()))
    tables: list[pd.DataFrame] = []
    configs: list[dict[str, Any]] = []
    for seed in seeds:
        config = Module3Config(
            families=families,
            master_seed=seed,
            stage_a_draws_per_family=draws,
            stage_a_keep_per_family=draws,
            stage_b_historical_replicates=1,
            workers=1,
            batch_size=DEFAULT_BUFFER_SIZE,
            output_dir=Path("."),
        )
        configs.append({**asdict(config), "output_dir": "."})
        for family_id in families:
            table = _prepare_parameter_table(inputs, family_id, config).copy()
            table.insert(0, "search_seed", seed)
            tables.append(table)
    parameters = pd.concat(tables, ignore_index=True)
    parameters, sources = _parameter_table(parameters)
    sources = sources.copy()
    sources["source_id"] = [source_id(row, SOURCE_NAMESPACE) for row in sources[IDENTITY].itertuples(index=False, name=None)]
    require(not sources.source_id.duplicated().any(), "Duplicate namespaced source ID")
    return parameters, sources, configs


def _prior_source_task(task: Mapping[str, Any]) -> list[dict[str, Any]]:
    inputs = _load_inputs_cached(task["data_dir"])
    params = build_resolved_parameters_from_sample(inputs, task["family_id"], pd.DataFrame(task["parameter_rows"]))
    rows: list[dict[str, Any]] = []
    for offset, scenario in enumerate(INTRINSIC_SCENARIOS):
        result = run_scenario_simulation(
            params,
            task["family_id"],
            _scenario_config(inputs, scenario, False),
            seed=int(task["proposal_seed"]) + offset,
        )
        scored = pilot.scored_fields(result, inputs)
        target = "CT011" if scenario == "lake_oberon" else "CT012"
        expected = {f"{target}_{field}" for field in ("raw_penalty", "weighted_penalty", "projected_primary", "projected_secondary")}
        require(expected.issubset(scored), f"Intrinsic scenario score extraction failed for {scenario}")
        row = {key: task[key] for key in IDENTITY}
        row.update(source_id=task["source_id"], stage="prior", replicate_index=0, scenario_id=scenario, simulation_seed=int(task["proposal_seed"]) + offset, intrinsic_scenario=scenario)
        row.update(scored)
        rows.append(row)
    return rows


def _execute(tasks: list[dict[str, Any]], worker, workers: int, buffer_size: int) -> Iterable[list[dict[str, Any]]]:
    if workers == 1:
        return map(worker, tasks)
    pool = ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn"))
    mapped = pool.map(worker, tasks, chunksize=1, buffersize=buffer_size)

    def close_after() -> Iterable[list[dict[str, Any]]]:
        try:
            yield from mapped
        finally:
            pool.shutdown(cancel_futures=True)

    return close_after()


def _source_tasks(parameters: pd.DataFrame, sources: pd.DataFrame, data_dir: Path, *, phase: str, replicates: int, intrinsic: pd.DataFrame) -> list[dict[str, Any]]:
    grouped = parameters.groupby(IDENTITY, sort=False)
    intrinsic_index = intrinsic.set_index(IDENTITY)
    tasks = []
    for source in sources.sort_values(IDENTITY).itertuples(index=False):
        identity = tuple(getattr(source, field) for field in IDENTITY)
        require(identity in intrinsic_index.index, f"Missing frozen intrinsic source: {identity}")
        intrinsic_row = intrinsic_index.loc[identity]
        require(isinstance(intrinsic_row, pd.Series), "Intrinsic source IDs must be unique")
        intrinsic_values = {field: intrinsic_row[field] for field in intrinsic.columns if field.startswith(("CT011_", "CT012_"))}
        require(intrinsic_values and all(pd.notna(value) for value in intrinsic_values.values()), f"Missing intrinsic scores for {identity}")
        tasks.append({
            **dict(zip(IDENTITY, identity)),
            "source_id": getattr(source, "source_id"),
            "proposal_index": int(getattr(source, "proposal_index")),
            "parameter_rows": grouped.get_group(identity).to_dict("records"),
            "intrinsic": intrinsic_values,
            "phase": phase,
            "replicates": replicates,
            "data_dir": str(data_dir.resolve()),
        })
    return tasks


def _history_source_task(task: Mapping[str, Any]) -> list[dict[str, Any]]:
    inputs = _load_inputs_cached(task["data_dir"])
    params = build_resolved_parameters_from_sample(inputs, task["family_id"], pd.DataFrame(task["parameter_rows"]))
    rows: list[dict[str, Any]] = []
    config = _scenario_config(inputs, "historical_lake", True)
    for replicate_index in range(1, int(task["replicates"]) + 1):
        seed = phase_seed(task["search_seed"], task["family_id"], task["proposal_index"], replicate_index, task["phase"])
        history = run_historical_simulation(params, task["family_id"], config, seed=seed)
        row = {key: task[key] for key in IDENTITY}
        row.update(source_id=task["source_id"], stage=task["phase"], replicate_index=replicate_index, simulation_seed=seed)
        row.update(terminal_screen.terminal_features(history))
        row.update(pilot.scored_fields(history, inputs))
        # CT011/CT012 are intrinsic scenario scores and are constant across
        # historical replicates, as in the existing pilot contract.
        row.update(task["intrinsic"])
        require(all(f"{target}_weighted_penalty" in row for target in pilot.TARGETS), "Incomplete target score coverage")
        rows.append(row)
    return rows


def simulate_source(task: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Public worker entry point retained for small smoke tests and callers."""
    return _history_source_task(task)


def _conditional_summary(raw: pd.DataFrame) -> pd.DataFrame:
    """Summarise one source chunk through the parent observation API."""
    from galaxias_model import conditional_observation

    # source_id is an archive/provenance field, not a scientific feature.
    result = conditional_observation.source_summaries(raw.drop(columns=["source_id"], errors="ignore"))
    require(isinstance(result, pd.DataFrame), "Conditional source summary must return a DataFrame")
    if "source_id" not in result.columns:
        ids = raw[IDENTITY + ["source_id"]].drop_duplicates()
        result = result.merge(ids, on=IDENTITY, how="left", validate="many_to_one")
    return result


def summarise_batch(raw: pd.DataFrame) -> pd.DataFrame:
    """Public chunk-summary entry point; profile count is deliberately unconstrained."""
    return _conditional_summary(raw)


def _read_prior(prior_dir: Path) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    manifest, _ = verify_archive(prior_dir, phase="prior")
    required = {"parameter_values.csv.gz", "sources.csv", "raw_replicates.csv.gz", "source_summary.csv"}
    require(required.issubset(manifest.get("outputs", {})), "Prior archive lacks required inputs")
    parameters = pd.read_csv(prior_dir / "parameter_values.csv.gz", float_precision="round_trip")
    sources = pd.read_csv(prior_dir / "sources.csv", float_precision="round_trip")
    intrinsic = pd.read_csv(prior_dir / "source_summary.csv", float_precision="round_trip")
    parameters, derived_sources = _parameter_table(parameters)
    require(set(sources.columns) >= set(IDENTITY + ["source_id", "proposal_index", "proposal_seed"]), "Prior source table lacks required fields")
    require(not sources.duplicated(IDENTITY).any() and not sources.source_id.duplicated().any(), "Prior source IDs are not unique")
    merged_source_metadata = derived_sources.merge(sources[IDENTITY + ["source_id", "proposal_index", "proposal_seed"]], on=IDENTITY, how="left", validate="one_to_one")
    require(merged_source_metadata.source_id.notna().all() and len(merged_source_metadata) == len(sources), "Prior source metadata mismatch")
    require(set(intrinsic.columns) >= set(IDENTITY + ["source_id"]), "Prior summary lacks source identity")
    require(not intrinsic.duplicated(IDENTITY).any(), "Prior summary has duplicate sources")
    return manifest, parameters, sources, intrinsic


def _read_seed_file(path: Path) -> np.ndarray:
    table = pd.read_csv(path, usecols=["simulation_seed"])
    return table.simulation_seed.to_numpy(dtype=np.int64)


def _archive_seeds(directory: Path) -> np.ndarray:
    values = []
    for name in ("raw_replicates.csv.gz", "stage_b_replicates.csv.gz", "validation_replicates.csv.gz"):
        path = Path(directory) / name
        if path.exists():
            values.append(_read_seed_file(path))
    return np.concatenate(values) if values else np.empty(0, dtype=np.int64)


def preflight_seed_plan(
    sources: pd.DataFrame,
    phase_replicates: Mapping[str, int],
    *,
    previous_phase_dirs: Sequence[Path] = (),
    old_seed_files: Sequence[Path] = (),
) -> dict[str, Any]:
    """Check all planned fresh seeds before any phase starts."""
    all_parts = []
    phase_counts: dict[str, int] = {}
    for phase, replicates in phase_replicates.items():
        require(phase in PHASE_CODES, f"Seed preflight does not support {phase}")
        require(type(replicates) is int and 1 <= replicates <= MAX_REPLICATES, "Replicate count exceeds seed preflight bound")
        parts = [source_seeds(int(row.search_seed), row.family_id, int(row.proposal_index), replicates, phase) for row in sources.itertuples(index=False)]
        planned = np.concatenate(parts) if parts else np.empty(0, dtype=np.int64)
        require(len(np.unique(planned)) == len(planned), f"Duplicate planned seeds within {phase}")
        all_parts.append(planned)
        phase_counts[phase] = len(planned)
    fresh = np.concatenate(all_parts) if all_parts else np.empty(0, dtype=np.int64)
    require(len(np.unique(fresh)) == len(fresh), "Fresh phase seed namespaces collide")
    old_parts = [_archive_seeds(Path(directory)) for directory in previous_phase_dirs]
    old_parts += [_read_seed_file(Path(path)) for path in old_seed_files]
    old = np.concatenate([part for part in old_parts if len(part)]) if any(len(part) for part in old_parts) else np.empty(0, dtype=np.int64)
    if len(old):
        require(not np.intersect1d(fresh, old).size, "Fresh phase seed collides with an earlier history")
    return {"fresh_history_runs": int(len(fresh)), "phase_history_runs": phase_counts, "earlier_history_runs": int(len(old))}


def run_prior(
    output_dir: Path,
    *,
    data_dir: Path = ROOT / "data",
    families: Sequence[str] = DEFAULT_FAMILY_ORDER,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    draws: int = DEFAULT_DRAWS,
    workers: int = 1,
    buffer_size: int = DEFAULT_BUFFER_SIZE,
    source_namespace: str = SOURCE_NAMESPACE,
) -> dict[str, Any]:
    """Create a fresh prior archive with deterministic intrinsic projections."""
    output_dir, data_dir = Path(output_dir), Path(data_dir)
    require(source_namespace == SOURCE_NAMESPACE, "Source namespace is fixed by the conditional-calibration contract")
    require(type(workers) is int and 1 <= workers <= 32, "workers must be in 1..32")
    require(type(buffer_size) is int and 1 <= buffer_size <= 256, "buffer_size must be in 1..256")
    require(not output_dir.exists(), "Output path already exists; choose a fresh directory")
    parameters, sources, configs = _build_prior_tables(data_dir, families, seeds, draws)
    tasks = []
    grouped = parameters.groupby(IDENTITY, sort=False)
    for row in sources.sort_values(IDENTITY).itertuples(index=False):
        identity = tuple(getattr(row, field) for field in IDENTITY)
        tasks.append({**dict(zip(IDENTITY, identity)), "source_id": row.source_id, "parameter_rows": grouped.get_group(identity).to_dict("records"), "data_dir": str(data_dir.resolve()), "proposal_seed": int(row.proposal_seed)})
    start = time.monotonic()
    output_dir.mkdir(parents=True, exist_ok=False)
    _write_csv(parameters, output_dir / "parameter_values.csv.gz", compression="gzip")
    roundtrip = pd.read_csv(output_dir / "parameter_values.csv.gz", float_precision="round_trip")
    expected_roundtrip = parameters.copy()
    for column in expected_roundtrip.select_dtypes(include=["object"]).columns:
        expected_roundtrip[column] = expected_roundtrip[column].fillna("")
        roundtrip[column] = roundtrip[column].fillna("")
    pd.testing.assert_frame_equal(expected_roundtrip, roundtrip, check_dtype=False, check_exact=True)
    sources.sort_values(IDENTITY).to_csv(output_dir / "sources.csv", index=False)
    raw_parts: list[pd.DataFrame] = []
    raw_path = output_dir / "raw_replicates.csv.gz"
    with gzip.open(raw_path, "wt", encoding="utf-8", newline="") as stream:
        for completed, batch in enumerate(_execute(tasks, _prior_source_task, workers, buffer_size), start=1):
            chunk = pd.DataFrame(batch)
            require(len(chunk) == 2, "Prior must run exactly two deterministic scenarios per source")
            chunk.to_csv(stream, index=False, header=completed == 1)
            raw_parts.append(chunk)
            if completed == 1 or completed % 25 == 0 or completed == len(tasks):
                print(f"prior: {completed}/{len(tasks)} sources; {completed * 2} deterministic runs", flush=True)
    raw = pd.concat(raw_parts, ignore_index=True)
    require(len(raw) == 2 * len(sources), "Prior must run exactly two deterministic scenarios per source")
    summary_rows = []
    for identity, group in raw.groupby(IDENTITY, sort=True):
        row = dict(zip(IDENTITY, identity))
        row["source_id"] = group.source_id.iloc[0]
        for target, scenario in zip(INTRINSIC_TARGETS, INTRINSIC_SCENARIOS):
            match = group.loc[group.scenario_id == scenario]
            require(len(match) == 1, "Prior intrinsic scenario grain mismatch")
            for field in ("raw_penalty", "weighted_penalty", "projected_primary", "projected_secondary"):
                key = f"{target}_{field}"
                require(key in match.columns, f"Missing intrinsic field {key}")
                row[key] = match.iloc[0][key]
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values(IDENTITY)
    summary.to_csv(output_dir / "source_summary.csv", index=False, float_format="%.17g")
    source_files, input_files, spec_documents = _source_bindings(data_dir)
    manifest = {
        "status": "complete", "scope": "conditional_calibration", "phase": "prior", "phase_code": None,
        "source_id_namespace": SOURCE_NAMESPACE, "source_identity": IDENTITY, "data_dir": str(data_dir.resolve()),
        "config": {"families": list(_validate_families(families)), "seeds": list(_validate_seeds(seeds)), "draws": draws, "workers": workers, "buffer_size": buffer_size}, "source_count": len(sources),
        "replicates": 0,
        "module3_sampling_configs": configs,
        "counts": {"prior_sources": len(sources), "parameter_rows": len(parameters), "historical_runs": 0, "deterministic_runs": len(raw)},
        "policies": {"sampling": "Exact _prepare_parameter_table draws; no source selection or deterministic historical gate.", "intrinsic": list(INTRINSIC_SCENARIOS), "observation_profiles": "None are bound in prior.", "source_identity": "search_seed + family_id + proposal_id under the manifest namespace."},
        "source_files": source_files, "input_files": input_files, "spec_documents": spec_documents,
        "runtime": {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__, "platform": platform.platform()},
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "outputs": {path.name: file_hash(path) for path in sorted(output_dir.iterdir()) if path.is_file()},
        "elapsed_seconds": round(time.monotonic() - start, 3),
    }
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def run_phase(
    prior_dir: Path,
    output_dir: Path,
    phase: str,
    *,
    source_ids: Path | None = None,
    replicates: int | None = None,
    workers: int = 1,
    buffer_size: int = DEFAULT_BUFFER_SIZE,
    previous_phase_dirs: Sequence[Path] = (),
    old_seed_files: Sequence[Path] = (),
) -> dict[str, Any]:
    """Run one frozen-source stochastic phase without ranking or reselection."""
    prior_dir, output_dir = Path(prior_dir), Path(output_dir)
    require(phase in PHASE_CODES, "run_phase supports screen, refine, and validate")
    replicates = DEFAULT_REPLICATES[phase] if replicates is None else replicates
    require(type(replicates) is int and 1 <= replicates <= MAX_REPLICATES, "replicates must be in 1..5000")
    require(type(workers) is int and 1 <= workers <= 32, "workers must be in 1..32")
    require(type(buffer_size) is int and 1 <= buffer_size <= 256, "buffer_size must be in 1..256")
    require(not output_dir.exists(), "Output path already exists; choose a fresh directory")
    manifest_prior, parameters, all_sources, intrinsic = _read_prior(prior_dir)
    require(manifest_prior.get("source_id_namespace") == SOURCE_NAMESPACE, "Prior source namespace is incompatible")
    if phase == "screen":
        require(source_ids is None, "Screen always uses every frozen prior source")
        sources = all_sources.copy()
        inclusion_basis = "complete_frozen_prior"
    else:
        require(source_ids is not None, f"{phase} requires an externally frozen source-ID CSV")
        selected = pd.read_csv(source_ids, dtype={"family_id": str, "proposal_id": str, "source_id": str})
        allowed = set(IDENTITY) | {"source_id", "proposal_index", "proposal_seed"}
        require(
            (set(selected.columns).issubset(allowed) and set(IDENTITY).issubset(selected.columns))
            or set(selected.columns) == {"source_id"},
            "Source-ID CSV must contain frozen identity columns",
        )
        if set(selected.columns) == {"source_id"}:
            require(selected.source_id.notna().all(), "Source-ID CSV contains missing source IDs")
            selected = selected.merge(all_sources, on="source_id", how="left", validate="one_to_one")
        else:
            if "source_id" in selected:
                expected_ids = [source_id(row, SOURCE_NAMESPACE) for row in selected[IDENTITY].itertuples(index=False, name=None)]
                require(selected.source_id.tolist() == expected_ids, "Source-ID CSV namespace or identity mismatch")
            selected = selected.merge(all_sources, on=IDENTITY, how="left", suffixes=("", "_prior"), validate="one_to_one")
            for field in ("proposal_index", "proposal_seed"):
                if field in selected.columns and f"{field}_prior" in selected.columns:
                    require(
                        pd.to_numeric(selected[field], errors="coerce").eq(pd.to_numeric(selected[f"{field}_prior"], errors="coerce")).all(),
                        f"Source-ID CSV {field} disagrees with the prior archive",
                    )
        require(not selected[[*IDENTITY, "proposal_index", "proposal_seed", "source_id"]].isna().any(axis=None), "Source-ID CSV contains unknown source")
        sources = selected[all_sources.columns].copy()
        require(not sources.duplicated(IDENTITY).any(), "Source-ID CSV contains duplicate sources")
        inclusion_basis = "frozen_source_id_csv"
    require(1 <= len(sources) <= len(all_sources), "Invalid phase source count")
    previous = []
    prior_manifest_binding = file_hash(prior_dir / "run_manifest.json")
    for directory in previous_phase_dirs:
        prior_manifest, bindings = verify_archive(Path(directory))
        require(prior_manifest.get("source_id_namespace") == SOURCE_NAMESPACE, "Previous phase namespace mismatch")
        require(prior_manifest.get("phase") != phase, "A phase namespace cannot be reused")
        require(prior_manifest.get("prior_input_binding", {}).get("run_manifest.json") == prior_manifest_binding, "Previous phase uses a different prior archive")
        previous.append({"phase": prior_manifest.get("phase"), "bindings": bindings})
    seed_check = preflight_seed_plan(sources, {phase: replicates}, previous_phase_dirs=previous_phase_dirs, old_seed_files=old_seed_files)
    tasks = _source_tasks(parameters, sources, Path(manifest_prior["data_dir"]), phase=phase, replicates=replicates, intrinsic=intrinsic)
    start = time.monotonic()
    output_dir.mkdir(parents=True, exist_ok=False)
    sources.sort_values(IDENTITY).to_csv(output_dir / "sources.csv", index=False)
    summary_parts: list[pd.DataFrame] = []
    actual_seed_parts: list[np.ndarray] = []
    tasks_iter = _execute(tasks, _history_source_task, workers, buffer_size)
    with gzip.open(output_dir / "raw_replicates.csv.gz", "wt", encoding="utf-8", newline="") as stream:
        for completed, batch in enumerate(tasks_iter, start=1):
            raw = pd.DataFrame(batch)
            require(len(raw) == replicates and not raw.duplicated(IDENTITY + ["replicate_index"]).any(), "Worker replicate count or grain mismatch")
            raw.to_csv(stream, index=False, header=completed == 1)
            summary_parts.append(summarise_batch(raw))
            actual_seed_parts.append(raw.simulation_seed.to_numpy(dtype=np.int64))
            if completed == 1 or completed % 25 == 0 or completed == len(tasks):
                print(f"{phase}: {completed}/{len(tasks)} sources; {completed * replicates} histories", flush=True)
    actual = np.concatenate(actual_seed_parts) if actual_seed_parts else np.empty(0, dtype=np.int64)
    planned = np.concatenate([source_seeds(int(row.search_seed), row.family_id, int(row.proposal_index), replicates, phase) for row in sources.itertuples(index=False)])
    require(np.array_equal(np.sort(actual), np.sort(planned)), "Executed seeds differ from preflight plan")
    summary = pd.concat(summary_parts, ignore_index=True)
    summary["source_inclusion_basis"] = inclusion_basis
    summary.to_csv(output_dir / "source_summary.csv", index=False, float_format="%.17g")
    source_files, input_files, spec_documents = _source_bindings(Path(manifest_prior["data_dir"]))
    manifest = {
        "status": "complete", "scope": "conditional_calibration", "phase": phase, "phase_code": PHASE_CODES[phase],
        "source_id_namespace": SOURCE_NAMESPACE, "source_identity": IDENTITY, "data_dir": str(Path(manifest_prior["data_dir"]).resolve()),
        "config": {"replicates": replicates, "workers": workers, "buffer_size": buffer_size, "source_count": len(sources), "source_cap": len(all_sources)}, "replicates": replicates, "source_count": len(sources),
        "counts": {"prior_sources": len(all_sources), "simulated_sources": len(sources), "historical_runs": len(actual), "deterministic_runs": 0, "source_summary_rows": len(summary)},
        "prior_input_binding": {"run_manifest.json": file_hash(prior_dir / "run_manifest.json")}, "previous_phase_bindings": previous,
        "source_selection_input": {"path": str(Path(source_ids).resolve()), **file_hash(Path(source_ids))} if source_ids is not None else None,
        "seed_preflight": seed_check,
        "policies": {"selection": "No source selection, ranking, or reselection. Refine and validate consume externally frozen source IDs.", "kernel": "Normal stochastic historical kernel; no RNG-affecting optimization.", "censoring": "terminal_screen.terminal_features is retained, including NaN first_zero_year for runs alive at 2002."},
        "source_files": source_files, "input_files": input_files, "spec_documents": spec_documents,
        "runtime": {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__, "platform": platform.platform()},
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "outputs": {path.name: file_hash(path) for path in sorted(output_dir.iterdir()) if path.is_file()},
        "elapsed_seconds": round(time.monotonic() - start, 3),
    }
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=PHASES, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prior-dir", type=Path)
    parser.add_argument("--source-ids", type=Path)
    parser.add_argument("--replicates", type=int)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--families", nargs="+", choices=DEFAULT_FAMILY_ORDER, default=DEFAULT_FAMILY_ORDER)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAWS)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--buffer-size", type=int, default=DEFAULT_BUFFER_SIZE)
    parser.add_argument("--previous-phase-dir", type=Path, action="append", default=[])
    parser.add_argument("--old-seed-file", type=Path, action="append", default=[])
    args = vars(parser.parse_args())
    phase = args.pop("phase")
    if phase == "prior":
        for name in ("prior_dir", "source_ids", "replicates", "previous_phase_dir", "old_seed_file"):
            args.pop(name, None)
        run_prior(**args)
    else:
        prior_dir = args.pop("prior_dir")
        source_ids = args.pop("source_ids")
        previous_phase_dirs = args.pop("previous_phase_dir")
        old_seed_files = args.pop("old_seed_file")
        for name in ("data_dir", "families", "seeds", "draws"):
            args.pop(name, None)
        run_phase(
            prior_dir,
            phase=phase,
            source_ids=source_ids,
            previous_phase_dirs=previous_phase_dirs,
            old_seed_files=old_seed_files,
            **args,
        )
