#!/usr/bin/env python3
"""Generate the bounded early-Lake mechanism study archive.

The driver owns only allocation, provenance, and execution.  Biology stays in
``galaxias_model.age_early_lake`` and every planned source and process slot is
retained in the output accounting, including algebraic and runtime failures.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import sys
import time
from typing import Any, Iterable, Mapping

# Set these before importing numpy.  Spawned workers execute this module again.
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from galaxias_model.age_early_lake import (  # noqa: E402
    LAKE_SITES,
    LAKE_YEARS,
    keyed_seed,
    make_early_lake_source,
    run_early_lake_history,
)
from galaxias_model.age_runner import RESTRICTIONS  # noqa: E402


PRODUCTION_NAMESPACE = "early-lake-20261004-v1"
SMOKE_NAMESPACE = "early-lake-20261004-smoke-v1"
SMOKE_SOURCE_COUNT = 4
AGES = (6, 8)
QUALITY_REGIMES = ("neutral", "engineering")
ROLES = ("bank", "calibration", "test")
BANK_REPLICATES = 4
OTHER_REPLICATES = 1
OUTPUT_NAMES = ("sources.jsonl.gz", "features.jsonl.gz", "histories.jsonl.gz")
MANIFEST_NAME = "manifest.json"
PROTOCOL = ROOT / "docs/early_lake_mechanism_protocol.md"
DESIGN = ROOT / "data/age_structured_design_20260929/scenarios.json"
FORCING = ROOT / "data/age_linked_recovery_20261001/retained_forcing_parameters.csv"

# Freeze the repository's Python implementation modules as source inputs.  The
# binding set contains source code only; no historical observation is a runtime
# input to this driver.
MODEL_MODULES = tuple(
    str(path.relative_to(ROOT))
    for path in sorted((ROOT / "src/galaxias_model").glob("*.py"))
)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def jsonable(value: Any) -> Any:
    """Convert model output to JSON without lossy scalar coercion."""
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, np.ndarray):
        return [jsonable(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return jsonable(value.item())
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def encoded(value: Any) -> str:
    return json.dumps(jsonable(value), separators=(",", ":"), sort_keys=True,
                      allow_nan=False)


def file_binding(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def source_bindings(*, require_analyzer: bool = False) -> dict[str, dict[str, Any]]:
    """Freeze only actual runtime inputs and the analyzer when present.

    The analyzer is intentionally optional during source-only preflight while
    the parent agent is writing it.  A full run records it once available.
    """
    paths = [ROOT / name for name in MODEL_MODULES]
    paths += [Path(__file__), PROTOCOL, DESIGN, FORCING,
              ROOT / "uv.lock", ROOT / "pyproject.toml"]
    analyzer = ROOT / "scripts/analyze_age_early_lake.py"
    if analyzer.exists():
        paths.append(analyzer)
    elif require_analyzer:
        raise FileNotFoundError("missing frozen runtime input: scripts/analyze_age_early_lake.py")
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing frozen runtime input(s): " +
                                ", ".join(relative(path) for path in missing))
    return {relative(path): file_binding(path) for path in sorted(set(paths))}


def verify_bindings(bindings: Mapping[str, Mapping[str, Any]]) -> None:
    for name, expected in bindings.items():
        actual = file_binding(ROOT / name)
        if actual != dict(expected):
            raise RuntimeError(f"frozen source changed during execution: {name}")


def _strip_quality(source: Mapping[str, Any]) -> dict[str, Any]:
    result = jsonable(source)
    result.pop("quality_regime", None)
    result.pop("quality_unit", None)
    forcing = result.get("forcing_values")
    if isinstance(forcing, dict):
        forcing = dict(forcing)
        forcing.pop("PR032", None)
        result["forcing_values"] = forcing
    return result


def validate_source_pairing(sources: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Check quality pairing and unique role/age source identities."""
    rows = list(sources)
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    identity: dict[tuple[int, str, int], str] = {}
    reverse_identity: dict[str, tuple[int, str, int]] = {}
    for source in rows:
        sid = str(source["source_id"])
        grouped[sid].append(source)
        key = (int(source["maximum_age"]), str(source["role"]), int(source["source_index"]))
        previous = identity.setdefault(key, sid)
        if previous != sid:
            raise RuntimeError(f"source identity drift for {key}")
        previous_key = reverse_identity.setdefault(sid, key)
        if previous_key != key:
            raise RuntimeError(f"source ID reused across role/age identities: {sid}")
    if len(identity) * len(QUALITY_REGIMES) != len(rows):
        raise RuntimeError("source rows do not have exactly two quality regimes")
    for sid, pair in grouped.items():
        if {str(row.get("quality_regime")) for row in pair} != set(QUALITY_REGIMES) or len(pair) != 2:
            raise RuntimeError(f"source {sid} is not an exact quality pair")
        neutral = next(row for row in pair if row["quality_regime"] == "neutral")
        engineering = next(row for row in pair if row["quality_regime"] == "engineering")
        if _strip_quality(neutral) != _strip_quality(engineering):
            raise RuntimeError(f"paired source parameters differ outside PR032: {sid}")
        if neutral["forcing_values"].get("PR032") != 1.0:
            raise RuntimeError(f"neutral PR032 is not one: {sid}")
        if not 0.7 <= float(engineering["forcing_values"].get("PR032")) <= 1.8:
            raise RuntimeError(f"engineering PR032 is outside its declared support: {sid}")
        if neutral.get("source_seed") != engineering.get("source_seed"):
            raise RuntimeError(f"quality pair has different source seeds: {sid}")
    return {"source_rows": len(rows), "distinct_source_ids": len(grouped),
            "paired_quality_rows": len(grouped)}


def _replicates(role: str, *, bank_replicates: int = BANK_REPLICATES) -> int:
    if role == "bank":
        return int(bank_replicates)
    if role in ("calibration", "test"):
        return OTHER_REPLICATES
    raise ValueError(f"unknown role: {role}")


def process_seed(source: Mapping[str, Any], replicate: int) -> int:
    """A process seed independent of quality regime and restriction."""
    return keyed_seed("early-lake-process-v1", source["namespace"],
                      source["source_id"], int(replicate))


def seed_preflight(sources: Iterable[Mapping[str, Any]], *,
                   bank_replicates: int = BANK_REPLICATES) -> dict[str, Any]:
    """Reject accidental seed collisions while allowing declared pairings."""
    seen: dict[int, tuple[Any, ...]] = {}
    paired_process: dict[tuple[str, int], set[int]] = defaultdict(set)
    source_list = list(sources)
    for source in source_list:
        sid = str(source["source_id"])
        source_identity = ("source", sid)
        seed = int(source["source_seed"])
        prior = seen.setdefault(seed, source_identity)
        if prior != source_identity:
            raise RuntimeError(f"source seed collision: {prior} versus {source_identity}")
        for replicate in range(_replicates(str(source["role"]), bank_replicates=bank_replicates)):
            process_identity = ("process", sid, replicate)
            process = process_seed(source, replicate)
            prior = seen.setdefault(process, process_identity)
            if prior != process_identity:
                raise RuntimeError(f"process seed collision: {prior} versus {process_identity}")
            paired_process[(sid, replicate)].add(process)
    if any(len(values) != 1 for values in paired_process.values()):
        raise RuntimeError("process seed is not stable across quality pairs")
    source_ids = {str(source["source_id"]) for source in source_list}
    return {
        "unique_parameter_and_process_seeds": len(seen),
        "distinct_source_ids": len(source_ids),
        "bank_replicates": int(bank_replicates),
        "process_seed_excludes_quality_and_restriction": True,
        "checked_cross_namespace_collisions": True,
    }


def build_sources(namespace: str, source_count: int, *, bank_replicates: int = BANK_REPLICATES) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for age in AGES:
        for role in ROLES:
            for index in range(source_count):
                for quality in QUALITY_REGIMES:
                    sources.append(make_early_lake_source(
                        age, index, role=role, namespace=namespace,
                        quality_regime=quality,
                    ))
    validate_source_pairing(sources)
    seed_preflight(sources, bank_replicates=bank_replicates)
    return sources


def _feature_row(source: Mapping[str, Any], restriction: str, replicate: int,
                 seed: int, result: Mapping[str, Any], status: str) -> dict[str, Any]:
    exposures = result.get("lake_exposures", np.zeros((len(LAKE_YEARS), 2)))
    return {
        "source_id": source["source_id"],
        "index": int(source["source_index"]),
        "source_index": int(source["source_index"]),
        "role": source["role"],
        "maximum_age": int(source["maximum_age"]),
        "quality_regime": source["quality_regime"],
        "restriction": restriction,
        "replicate": int(replicate),
        "seed": int(seed),
        "status": status,
        "valid": bool(result.get("valid", False)),
        "lake_exposures": jsonable(exposures),
        "failure_reason": result.get("failure_reason"),
        "advance_calls": int(result.get("advance_calls", 0)),
    }


def execute_source_task(task: tuple[dict[str, Any], str] | tuple[dict[str, Any], str, int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Execute one source/quality task in stable restriction/replicate order."""
    source, namespace = task[:2]
    bank_replicates = int(task[2]) if len(task) > 2 else BANK_REPLICATES
    features: list[dict[str, Any]] = []
    raw: list[dict[str, Any]] = []
    repetitions = _replicates(str(source["role"]), bank_replicates=bank_replicates)
    for restriction in RESTRICTIONS:
        for replicate in range(repetitions):
            seed = process_seed(source, replicate)
            if not bool(source.get("feasible", True)):
                result: dict[str, Any] = {
                    "status": "algebraically_infeasible", "valid": False,
                    "failure_reason": source.get("failure_reason") or "source marked infeasible",
                    "source": dict(source), "restriction": restriction,
                    "replicate": replicate, "seed": seed,
                    "lake_exposures": np.zeros((len(LAKE_YEARS), 2)),
                    "advance_calls": 0,
                }
                status = "algebraically_infeasible"
            else:
                try:
                    result = run_early_lake_history(
                        source, restriction=restriction, seed=seed,
                        replicate=replicate, stochastic=True,
                    )
                    status = "valid" if bool(result.get("valid")) else "process_infeasible"
                except BaseException as exc:  # retain every runtime slot
                    result = {
                        "status": "runtime_failure", "valid": False,
                        "failure_reason": f"{type(exc).__name__}: {exc}",
                        "source": dict(source), "restriction": restriction,
                        "replicate": replicate, "seed": seed,
                        "lake_exposures": np.zeros((len(LAKE_YEARS), 2)),
                        "advance_calls": 0,
                    }
                    status = "runtime_failure"
            compact = _feature_row(source, restriction, replicate, seed, result, status)
            history = jsonable(result)
            raw.append({
                "source": jsonable(source),
                "history": history,
                "source_id": source["source_id"], "index": int(source["source_index"]),
                "role": source["role"], "maximum_age": int(source["maximum_age"]),
                "quality_regime": source["quality_regime"], "restriction": restriction,
                "replicate": int(replicate), "seed": seed, "status": status,
            })
            features.append(compact)
    return features, raw


class _DeterministicGzip:
    def __init__(self, path: Path):
        self.path = path
        self.raw = path.open("wb")
        self.gz = gzip.GzipFile(filename="", mode="wb", fileobj=self.raw,
                                compresslevel=9, mtime=0)
        self.text = io.TextIOWrapper(self.gz, encoding="utf-8", newline="\n")
        self.logical = hashlib.sha256()

    def write(self, value: Any) -> None:
        line = (encoded(value) + "\n").encode("utf-8")
        self.logical.update(line)
        self.text.write(line.decode("utf-8"))

    def close(self) -> str:
        self.text.flush()
        self.text.detach()
        self.gz.close()
        self.raw.close()
        return self.logical.hexdigest()


def _physical_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _map_tasks(tasks: list[tuple[dict[str, Any], str]], workers: int):
    if workers == 1:
        return map(execute_source_task, tasks)
    context = mp.get_context("spawn")
    pool = ProcessPoolExecutor(max_workers=workers, mp_context=context)
    try:
        # Python 3.14 supplies buffersize; retain compatibility with older
        # local test interpreters without changing the ordered map contract.
        try:
            values = pool.map(execute_source_task, tasks, chunksize=1,
                              buffersize=max(1, workers * 2))
        except TypeError:
            values = pool.map(execute_source_task, tasks, chunksize=1)
        return _PoolResults(pool, values)
    except BaseException:
        pool.shutdown(wait=True, cancel_futures=True)
        raise


class _PoolResults:
    def __init__(self, pool: ProcessPoolExecutor, values):
        self.pool, self.values = pool, values

    def __iter__(self):
        return iter(self.values)

    def close(self):
        self.pool.shutdown(wait=True, cancel_futures=True)


def _config(mode: str, namespace: str, source_count: int, bank_replicates: int) -> dict[str, Any]:
    return {
        "mode": mode, "namespace": namespace, "maximum_ages": list(AGES),
        "quality_regimes": list(QUALITY_REGIMES), "roles": list(ROLES),
        "restrictions": list(RESTRICTIONS), "source_count_per_role_per_age": source_count,
        "bank_replicates": bank_replicates, "calibration_replicates": OTHER_REPLICATES,
        "test_replicates": OTHER_REPLICATES, "lake_years": list(LAKE_YEARS),
        "lake_sites": LAKE_SITES,
    }


def run(args: Any) -> dict[str, Any]:
    mode = str(args.mode)
    if mode not in ("smoke", "gate"):
        raise ValueError("mode must be smoke or gate")
    workers = int(args.workers)
    if workers < 1 or workers > 64:
        raise ValueError("workers must be in 1..64")
    output = Path(args.output).resolve()
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    preflight_only = bool(getattr(args, "preflight_only", False))
    source_count = 512 if mode == "gate" else SMOKE_SOURCE_COUNT
    bank_replicates = BANK_REPLICATES if mode == "gate" else 1
    namespace = PRODUCTION_NAMESPACE if mode == "gate" else SMOKE_NAMESPACE
    config = _config(mode, namespace, source_count, bank_replicates)
    sources = build_sources(namespace, source_count, bank_replicates=bank_replicates)
    pair_check = validate_source_pairing(sources)
    seeds = seed_preflight(sources, bank_replicates=bank_replicates)
    frozen = source_bindings(require_analyzer=not preflight_only)
    output.mkdir(parents=True, exist_ok=False)
    started = utc()
    timer = time.monotonic()
    manifest: dict[str, Any] = {
        "status": "preflight_running" if preflight_only else "running",
        "mode": mode,
        "started_utc": started, "configuration": config,
        "source_bindings": frozen, "pair_preflight": pair_check,
        "seed_preflight": seeds, "source_rows": len(sources),
        "planned_history_attempts": sum(_replicates(str(s["role"]), bank_replicates=bank_replicates)
                                         for s in sources) * len(RESTRICTIONS),
        "source_status_counts": dict(Counter("feasible" if s.get("feasible", True)
                                              else "algebraically_infeasible" for s in sources)),
        "runtime": {"python": platform.python_version(), "numpy": np.__version__,
                    "platform": platform.platform(), "workers": workers,
                    "numpy_threads": 1, "multiprocessing_start_method": "spawn"},
    }

    def write_manifest() -> None:
        (output / MANIFEST_NAME).write_text(
            json.dumps(jsonable(manifest), indent=2, sort_keys=True, allow_nan=False) + "\n"
        )

    write_manifest()
    try:
        source_writer = _DeterministicGzip(output / "sources.jsonl.gz")
        for source in sources:
            source_writer.write(source)
        source_logical = source_writer.close()
        if preflight_only:
            manifest.update(
                status="preflight_complete", finished_utc=utc(),
                elapsed_seconds=time.monotonic() - timer,
                biological_simulation_started=False,
                accounting={"source_rows": len(sources), "history_rows": 0,
                            "site_count": 0, "status_counts": {}},
                history_status_counts={}, actual_history_rows=0, site_count=0,
                logical_sha256={"sources.jsonl.gz": source_logical},
            )
            manifest["physical_sha256"] = {"sources.jsonl.gz": _physical_sha(output / "sources.jsonl.gz")}
            manifest["outputs"] = {name: file_binding(output / name)
                                    for name in ("sources.jsonl.gz",)}
            write_manifest()
            verify_bindings(frozen)
            return manifest

        feature_writer = _DeterministicGzip(output / "features.jsonl.gz")
        history_writer = _DeterministicGzip(output / "histories.jsonl.gz")
        counts: Counter[str] = Counter()
        total_histories = 0
        total_sites = 0
        tasks = [(source, namespace, bank_replicates) for source in sources]
        mapped = _map_tasks(tasks, workers)
        try:
            for feature_rows, raw_rows in mapped:
                if len(feature_rows) != len(raw_rows):
                    raise RuntimeError("feature/raw history row count mismatch")
                for feature, raw in zip(feature_rows, raw_rows):
                    feature_writer.write(feature)
                    history_writer.write(raw)
                    counts[str(feature["status"])] += 1
                    total_histories += 1
                    total_sites += 1
        finally:
            if isinstance(mapped, _PoolResults):
                mapped.close()
        feature_logical = feature_writer.close()
        history_logical = history_writer.close()
        verify_bindings(frozen)
        expected = manifest["planned_history_attempts"]
        if total_histories != expected:
            raise RuntimeError(f"history accounting mismatch: {total_histories} != {expected}")
        runtime_failures = sum(counts[key] for key in ("runtime_failure", "process_infeasible"))
        manifest.update(
            status="complete" if runtime_failures == 0 else "failed",
            finished_utc=utc(), elapsed_seconds=time.monotonic() - timer,
            biological_simulation_started=True,
            accounting={"source_rows": len(sources), "history_rows": total_histories,
                        "site_count": total_sites, "status_counts": dict(counts),
                        "algebraically_infeasible": counts["algebraically_infeasible"],
                        "runtime_failures": runtime_failures},
            history_status_counts=dict(counts), actual_history_rows=total_histories,
            site_count=total_sites,
            logical_sha256={"sources.jsonl.gz": source_logical,
                            "features.jsonl.gz": feature_logical,
                            "histories.jsonl.gz": history_logical},
        )
        manifest["physical_sha256"] = {name: _physical_sha(output / name)
                                        for name in OUTPUT_NAMES}
        manifest["outputs"] = {name: file_binding(output / name) for name in OUTPUT_NAMES}
        write_manifest()
        if runtime_failures:
            raise RuntimeError("runtime failures prevent a successful production gate")
        return manifest
    except BaseException as exc:
        manifest.setdefault("status", "failed")
        if manifest.get("status") in ("running", "preflight_running"):
            manifest.update(status="failed", finished_utc=utc(),
                            elapsed_seconds=time.monotonic() - timer,
                            failure=f"{type(exc).__name__}: {exc}")
            write_manifest()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "gate"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--preflight-only", action="store_true")
    result = run(parser.parse_args())
    print(json.dumps({key: result[key] for key in
                      ("status", "source_rows", "planned_history_attempts")}, sort_keys=True))


if __name__ == "__main__":
    main()
