#!/usr/bin/env python3
"""Independent audit of the frozen early-Lake production result.

This program does not run a demographic history and does not read the actual
Lake observations.  It checks the completed synthetic archive, reconstructs
the recovery gate from saved sets with R's beta quantiles, and replays a small
deterministic sample of bank scores through the pre-existing scalar Lake score.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import heapq
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from galaxias_model.age_historical_refocus import lake_history_log_score  # noqa: E402


RESTRICTIONS = ("R_H", "R_T", "R_C", "R_J")
AGES = (6, 8)
ROLES = ("bank", "calibration", "test")
QUALITY_REGIMES = ("neutral", "engineering")
PROFILES = {
    "primary": {"age1": 0.0, "power": 1 / 12, "generator": "primary"},
    "age_accessibility": {"age1": 1.0, "power": 1 / 12, "generator": "age_accessibility"},
    "score_concentration": {"age1": 0.0, "power": 1 / 4, "generator": "primary"},
    "site_trip_quality": {"age1": 0.0, "power": 1 / 12, "generator": "site_trip_quality"},
}
BANKS = ("full", "half_a", "half_b")
INDEX_STRATA = ("below_one", "above_one")
LAKE_YEARS = (1976, 1977, 1978, 1979, 1980, 1983, 1986, 1989)
PRODUCTION_NAMESPACE = "early-lake-20261004-v1"
SOURCE_COUNT = 512
BANK_REPLICATES = 4
EXPECTED_SOURCES = 6144
EXPECTED_HISTORIES = 49152
RAW_EXPOSURE_SAMPLE = 128
FLOAT_RTOL = 1e-12
FLOAT_ATOL = 1e-8


class AuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    require(path.is_file(), f"missing required file: {path}")
    return json.loads(path.read_text())


def keyed_seed(*parts: Any, bits: int = 128) -> int:
    payload = json.dumps(parts, separators=(",", ":"), sort_keys=True, default=str).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[: bits // 8], "little")


def source_halves(source_ids: list[str]) -> dict[str, list[bool]]:
    require(len(source_ids) >= 2 and len(set(source_ids)) == len(source_ids),
            "bank IDs are not distinct")
    order = sorted(range(len(source_ids)),
                   key=lambda i: keyed_seed("early-lake-halves-v1", source_ids[i]))
    first = [False] * len(source_ids)
    for index in order[::2]:
        first[index] = True
    return {
        "full": [True] * len(source_ids),
        "half_a": first,
        "half_b": [not value for value in first],
    }


def logical_rows(path: Path) -> tuple[list[dict[str, Any]], str]:
    result: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for line in stream:
            digest.update(line)
            result.append(json.loads(line))
    return result, digest.hexdigest()


def number(value: Any) -> float:
    if value == "Infinity":
        return math.inf
    if value == "-Infinity":
        return -math.inf
    require(isinstance(value, (int, float)) and not isinstance(value, bool),
            f"expected a numeric value, received {value!r}")
    result = float(value)
    require(not math.isnan(result), "NaN in saved analysis")
    return result


def close_number(observed: Any, expected: float, where: str) -> float:
    value = number(observed)
    if math.isinf(value) or math.isinf(expected):
        require(value == expected, f"infinite value mismatch at {where}")
        return 0.0
    require(math.isclose(value, expected, rel_tol=FLOAT_RTOL, abs_tol=FLOAT_ATOL),
            f"numeric mismatch at {where}: {value} versus {expected}")
    return abs(value - expected)


def stripped_quality(source: Mapping[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(source))
    value.pop("quality_regime", None)
    forcing = dict(value["forcing_values"])
    forcing.pop("PR032", None)
    value["forcing_values"] = forcing
    return value


def expected_source_keys() -> Iterable[tuple[int, str, int, str, str]]:
    for age in AGES:
        for role in ROLES:
            for index in range(SOURCE_COUNT):
                source_id = f"{PRODUCTION_NAMESPACE}_A{age}_{role}_{index:04d}"
                for quality in QUALITY_REGIMES:
                    yield age, role, index, quality, source_id


def expected_history_keys(sources: list[dict[str, Any]]) -> Iterable[tuple[str, str, str, int]]:
    for source in sources:
        replicates = BANK_REPLICATES if source["role"] == "bank" else 1
        for restriction in RESTRICTIONS:
            for replicate in range(replicates):
                yield source["source_id"], source["quality_regime"], restriction, replicate


def fixed_config() -> dict[str, Any]:
    return {
        "mode": "gate", "namespace": PRODUCTION_NAMESPACE,
        "maximum_ages": list(AGES), "quality_regimes": list(QUALITY_REGIMES),
        "roles": list(ROLES), "restrictions": list(RESTRICTIONS),
        "source_count_per_role_per_age": SOURCE_COUNT,
        "bank_replicates": BANK_REPLICATES,
        "calibration_replicates": 1, "test_replicates": 1,
        "lake_years": list(LAKE_YEARS), "lake_sites": 12,
    }


def bound_source_names(frozen: Mapping[str, Any]) -> set[str]:
    names = {name for name in frozen["files"] if name.startswith("src/galaxias_model/")}
    names.update({
        "data/age_linked_recovery_20261001/retained_forcing_parameters.csv",
        "data/age_structured_design_20260929/scenarios.json",
        "docs/early_lake_mechanism_protocol.md", "pyproject.toml", "uv.lock",
        "scripts/analyze_age_early_lake.py", "scripts/run_age_early_lake.py",
    })
    return names


def verify_manifest(gate: Path, manifest: Mapping[str, Any], frozen: Mapping[str, Any]) -> dict[str, Any]:
    require(manifest.get("status") == "complete", "driver manifest is not complete")
    require(manifest.get("mode") == "gate" and manifest.get("configuration") == fixed_config(),
            "driver did not use the fixed production configuration")
    require(manifest.get("planned_history_attempts") == EXPECTED_HISTORIES and
            manifest.get("actual_history_rows") == EXPECTED_HISTORIES,
            "driver history accounting is not 49,152")
    require(manifest.get("source_rows") == EXPECTED_SOURCES, "driver source accounting is not 6,144")
    accounting = manifest.get("accounting", {})
    require(accounting.get("history_rows") == EXPECTED_HISTORIES and
            accounting.get("source_rows") == EXPECTED_SOURCES and
            accounting.get("site_count") == EXPECTED_HISTORIES and
            accounting.get("runtime_failures") == 0,
            "driver accounting is incomplete or contains runtime failures")
    require(manifest.get("biological_simulation_started") is True,
            "driver did not record production execution")
    archives = {"sources.jsonl.gz", "features.jsonl.gz", "histories.jsonl.gz"}
    require(set(manifest.get("physical_sha256", {})) == archives and
            set(manifest.get("logical_sha256", {})) == archives and
            set(manifest.get("outputs", {})) == archives,
            "driver does not bind all three archives")
    for name in archives:
        path = gate / name
        require(path.is_file(), f"missing production archive: {name}")
        observed = sha256(path)
        require(observed == manifest["physical_sha256"][name] ==
                manifest["outputs"][name]["sha256"], f"physical hash mismatch: {name}")
        require(path.stat().st_size == manifest["outputs"][name]["bytes"],
                f"byte count mismatch: {name}")
    bindings = manifest.get("source_bindings", {})
    expected_names = bound_source_names(frozen)
    require(set(bindings) == expected_names, "production source binding set is incomplete")
    for name, binding in bindings.items():
        require(binding["sha256"] == frozen["files"].get(name),
                f"production source differs from frozen source: {name}")
        local = ROOT / name
        require(local.is_file() and sha256(local) == binding["sha256"],
                f"current local bound source differs from production: {name}")
        require(local.stat().st_size == binding["bytes"], f"bound byte count differs: {name}")
    banned = ("lake_figure6_digitised", "historical_observation", "actual_lake")
    require(not any(any(token in name.lower() for token in banned) for name in bindings),
            "production bindings contain a historical observation input")
    return {"bound_files": len(bindings), "archives": sorted(archives)}


def verify_sources(gate: Path, manifest: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], dict[str, Any]]:
    sources, logical = logical_rows(gate / "sources.jsonl.gz")
    require(logical == manifest["logical_sha256"]["sources.jsonl.gz"],
            "source logical hash mismatch")
    require(len(sources) == EXPECTED_SOURCES, "source archive does not contain 6,144 rows")
    pairs: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    role_ids: dict[str, set[str]] = defaultdict(set)
    feasible = Counter()
    for row, (age, role, index, quality, source_id) in zip(sources, expected_source_keys(), strict=True):
        require((row["maximum_age"], row["role"], row["source_index"],
                 row["quality_regime"], row["source_id"]) ==
                (age, role, index, quality, source_id), "source archive order or identity differs")
        require(row.get("namespace") == PRODUCTION_NAMESPACE, "source namespace differs")
        expected_stratum = "below_one" if index % 2 == 0 else "above_one"
        require(row.get("index_stratum") == expected_stratum, "source index stratum differs")
        pairs[source_id][quality] = row
        role_ids[role].add(source_id)
        feasible["feasible" if row["feasible"] else "algebraically_infeasible"] += 1
    require(all(role_ids[a].isdisjoint(role_ids[b]) for i, a in enumerate(ROLES)
                for b in ROLES[i + 1:]), "source IDs overlap roles")
    require(len(pairs) == EXPECTED_SOURCES // 2 and
            all(set(pair) == set(QUALITY_REGIMES) for pair in pairs.values()),
            "quality pairs are incomplete")
    for source_id, pair in pairs.items():
        neutral, engineering = pair["neutral"], pair["engineering"]
        require(stripped_quality(neutral) == stripped_quality(engineering),
                f"quality pair differs outside PR032: {source_id}")
        require(neutral["forcing_values"]["PR032"] == 1.0 and
                0.7 <= engineering["forcing_values"]["PR032"] <= 1.8,
                f"PR032 pair is outside its contract: {source_id}")
    require(dict(feasible) == manifest.get("source_status_counts"),
            "source feasibility counts differ from manifest")
    source_map = {(row["source_id"], row["quality_regime"]): row for row in sources}
    return sources, source_map, {
        "source_rows": len(sources), "distinct_source_ids": len(pairs),
        "algebraically_feasible_source_ids": sum(pair["neutral"]["feasible"]
                                                 for pair in pairs.values()),
        "algebraically_infeasible_source_ids": sum(not pair["neutral"]["feasible"]
                                                   for pair in pairs.values()),
        "role_source_counts": {role: len(ids) for role, ids in role_ids.items()},
        "source_status_counts": dict(feasible), "logical_sha256": logical,
    }


def raw_lake_exposures(history: Mapping[str, Any]) -> list[list[float]]:
    annual = history["annual_states"]
    result = []
    for year in LAKE_YEARS:
        state = np.asarray(annual[str(year)], dtype=float)
        require(state.ndim == 3 and state.shape[0] >= 1 and state.shape[2] >= 2,
                f"unexpected annual-state shape in {year}")
        result.append([float(state[0, :, 0].sum()), float(state[0, :, 1].sum())])
    return result


def verify_histories(
    gate: Path,
    manifest: Mapping[str, Any],
    sources: list[dict[str, Any]],
    source_map: Mapping[tuple[str, str], dict[str, Any]],
) -> tuple[dict[tuple[int, str, str], list[dict[str, Any]]], dict[str, Any]]:
    feature_path, history_path = gate / "features.jsonl.gz", gate / "histories.jsonl.gz"
    feature_digest, history_digest = hashlib.sha256(), hashlib.sha256()
    status = Counter()
    groups: dict[tuple[int, str, str], list[dict[str, Any]]] = defaultdict(list)
    valid_key_scores = []
    for key in expected_history_keys(sources):
        source_id, quality, restriction, replicate = key
        if source_map[(source_id, quality)]["feasible"]:
            token = json.dumps(key, separators=(",", ":"))
            valid_key_scores.append((hashlib.sha256(token.encode()).hexdigest(), key))
    require(len(valid_key_scores) >= RAW_EXPOSURE_SAMPLE,
            "fewer valid histories than the raw-exposure audit sample")
    sampled_keys = {key for _, key in heapq.nsmallest(RAW_EXPOSURE_SAMPLE, valid_key_scores)}
    sampled = 0
    expected = iter(expected_history_keys(sources))
    with gzip.open(feature_path, "rb") as feature_stream, gzip.open(history_path, "rb") as history_stream:
        for position in range(EXPECTED_HISTORIES):
            feature_line, history_line = feature_stream.readline(), history_stream.readline()
            require(feature_line and history_line, "feature/history archive ended early")
            feature_digest.update(feature_line)
            history_digest.update(history_line)
            feature, raw = json.loads(feature_line), json.loads(history_line)
            source_id, quality, restriction, replicate = next(expected)
            key = (source_id, quality, restriction, replicate)
            observed = (feature["source_id"], feature["quality_regime"],
                        feature["restriction"], int(feature["replicate"]))
            raw_observed = (raw["source_id"], raw["quality_regime"],
                            raw["restriction"], int(raw["replicate"]))
            require(observed == key == raw_observed, "feature/history order or slot differs")
            source = source_map[(source_id, quality)]
            require(raw["source"] == source and raw["history"]["source"] == source,
                    "raw history source does not match source archive")
            require((feature["maximum_age"], feature["role"], feature["source_index"]) ==
                    (source["maximum_age"], source["role"], source["source_index"]),
                    "feature/source identity differs")
            seed = keyed_seed("early-lake-process-v1", PRODUCTION_NAMESPACE, source_id, replicate)
            require(int(feature["seed"]) == int(raw["seed"]) == seed,
                    "process seed differs from paired contract")
            expected_status = "valid" if source["feasible"] else "algebraically_infeasible"
            expected_advances = 25 if source["feasible"] else 0
            history = raw["history"]
            require(feature["status"] == raw["status"] == history["status"] == expected_status and
                    bool(feature["valid"]) is source["feasible"] and
                    bool(history["valid"]) is source["feasible"],
                    "history status differs from source feasibility")
            require(int(feature["advance_calls"]) == int(history["advance_calls"]) == expected_advances,
                    "history does not contain the prescribed 25 or zero advances")
            require(feature["lake_exposures"] == history["lake_exposures"],
                    "compact features differ from raw history exposures")
            if source["feasible"]:
                require(set(history.get("annual_states", {})) == {str(year) for year in range(1965, 1990)},
                        "valid raw history does not contain all 25 annual states")
            else:
                require(history.get("annual_states", {}) == {},
                        "algebraic failure contains annual states")
            if key in sampled_keys:
                require(raw_lake_exposures(history) == feature["lake_exposures"],
                        "features were not extracted from sampled raw annual states")
                sampled += 1
            stratum = "below_one" if int(feature["source_index"]) % 2 == 0 else "above_one"
            groups[(int(feature["maximum_age"]), quality, stratum)].append(feature)
            status[expected_status] += 1
        require(not feature_stream.readline() and not history_stream.readline(),
                "feature/history archive contains unexpected extra rows")
    require(sampled == RAW_EXPOSURE_SAMPLE, "raw exposure sample is incomplete")
    feature_logical, history_logical = feature_digest.hexdigest(), history_digest.hexdigest()
    require(feature_logical == manifest["logical_sha256"]["features.jsonl.gz"],
            "feature logical hash mismatch")
    require(history_logical == manifest["logical_sha256"]["histories.jsonl.gz"],
            "history logical hash mismatch")
    require(dict(status) == manifest["accounting"]["status_counts"],
            "raw status counts differ from manifest")
    require(len(groups) == 8 and all(len(rows) == EXPECTED_HISTORIES // 8 for rows in groups.values()),
            "age/quality/index groups are incomplete")
    return groups, {
        "feature_rows": sum(status.values()), "history_rows": sum(status.values()),
        "status_counts": dict(status), "raw_exposure_rows_recomputed": sampled,
        "features_logical_sha256": feature_logical,
        "histories_logical_sha256": history_logical,
    }


def detail_object(path: Path) -> tuple[dict[str, Any], str]:
    with gzip.open(path, "rb") as stream:
        payload = stream.read()
    return json.loads(payload), hashlib.sha256(payload).hexdigest()


def expected_detail_names() -> set[str]:
    return {
        f"A{age}_{quality}_{stratum}_{profile}.json.gz"
        for age in AGES for quality in QUALITY_REGIMES
        for stratum in INDEX_STRATA for profile in PROFILES
    }


def validate_observations(
    detail: Mapping[str, Any],
    features: list[dict[str, Any]],
    profile: str,
) -> tuple[dict[str, dict[str, dict[str, int]]], dict[str, list[dict[str, Any]]]]:
    observations: dict[str, list[dict[str, Any]]] = detail["observations"]
    selected: dict[str, list[dict[str, Any]]] = detail["scored_z1"]
    generator = PROFILES[profile]["generator"]
    counts: dict[str, dict[str, dict[str, int]]] = {role: {} for role in ("calibration", "test")}
    for role in ("calibration", "test"):
        expected_rows = [row for row in features if row["role"] == role and row["valid"]]
        require(len(observations[role]) == len(expected_rows), "observation count differs from valid features")
        for observation, row in zip(observations[role], expected_rows, strict=True):
            require((observation["source_id"], observation["source_index"], observation["role"],
                     observation["true_restriction"]) ==
                    (row["source_id"], row["source_index"], role, row["restriction"]),
                    "synthetic observation identity/order differs")
            expected_seed = keyed_seed("early-lake-observation-v1", row["source_id"], role,
                                       int(row["replicate"]), generator)
            require(int(observation["seed"]) == expected_seed, "observation seed differs")
            means = np.asarray(observation["means"], dtype=float)
            site_counts = np.asarray(observation["raw_site_counts"])
            require(means.shape == (8,) and np.isfinite(means).all() and np.all(means >= 0),
                    "synthetic means are invalid")
            require(site_counts.shape == (8, 12) and np.issubdtype(site_counts.dtype, np.integer) and
                    np.all(site_counts >= 0), "raw synthetic site counts are invalid")
            require(bool(observation["early_positive"]) == bool(np.any(means[:5] > 0)),
                    "Z=1 partition differs from first-five observed means")
        expected_selected = [row for row in observations[role] if row["early_positive"]]
        require(selected[role] == expected_selected, "saved Z=1 sample is not the declared partition")
        for label in RESTRICTIONS:
            attempted = [row for row in features if row["role"] == role and row["restriction"] == label]
            generated = [row for row in observations[role] if row["true_restriction"] == label]
            counts[role][label] = {
                "attempted": len(attempted), "valid": len(generated),
                "algebraically_infeasible": sum(row["status"] == "algebraically_infeasible"
                                                  for row in attempted),
                "unexpected_process_failure": sum(row["status"] not in
                                                  ("valid", "algebraically_infeasible")
                                                  for row in attempted),
                "z1": sum(row["early_positive"] for row in generated),
                "z0_full_set": sum(not row["early_positive"] for row in generated),
            }
    return counts, selected


def r_clopper_pearson(requests: Iterable[tuple[int, int, float]]) -> dict[tuple[int, int, float], tuple[float, float]]:
    unique = sorted(set(requests))
    require(unique, "no binomial summaries were available for R validation")
    script = r'''
x <- read.table(file("stdin"), header=FALSE, sep="\t", col.names=c("id","k","n","alpha"))
lo <- ifelse(x$k == 0, 0, qbeta(x$alpha, x$k, x$n-x$k+1))
hi <- ifelse(x$k == x$n, 1, qbeta(1-x$alpha, x$k+1, x$n-x$k))
for (i in seq_len(nrow(x))) cat(x$id[i], sprintf("%.17g", lo[i]), sprintf("%.17g", hi[i]), sep="\t", fill=TRUE)
'''
    payload = "".join(f"{i}\t{k}\t{n}\t{alpha:.17g}\n"
                      for i, (k, n, alpha) in enumerate(unique))
    try:
        run = subprocess.run(["Rscript", "--vanilla", "-e", script], input=payload,
                             text=True, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AuditError(f"independent R Clopper-Pearson calculation failed: {exc}") from exc
    result: dict[tuple[int, int, float], tuple[float, float]] = {}
    lines = [line for line in run.stdout.splitlines() if line.strip()]
    require(len(lines) == len(unique), "R returned an incomplete interval table")
    for line in lines:
        index, lower, upper = line.split("\t")
        result[unique[int(index)]] = (float(lower), float(upper))
    return result


def nonconformity(values: list[float], candidate: int) -> tuple[float, float, bool]:
    unsupported = not any(math.isfinite(value) for value in values)
    if unsupported:
        return math.inf, math.inf, True
    other = max(value for index, value in enumerate(values) if index != candidate)
    relative = other - values[candidate]
    if math.isnan(relative):
        relative = 0.0
    return relative, -values[candidate], False


def logmeanexp(scores: list[float], denominator: int) -> float:
    require(denominator > 0, "bank denominator is zero")
    finite = [value for value in scores if math.isfinite(value)]
    if not finite:
        return -math.inf
    maximum = max(finite)
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in finite)) - math.log(denominator)


def manual_bank_vector(
    rows: list[dict[str, Any]],
    source_ids: list[str],
    means: list[float],
    *, age1: float, power: float,
) -> list[float]:
    selected = set(source_ids)
    by_restriction: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["role"] == "bank" and row["source_id"] in selected:
            by_restriction[row["restriction"]].append(row)
    denominator = len(source_ids) * BANK_REPLICATES
    result = []
    for restriction in RESTRICTIONS:
        slots = by_restriction[restriction]
        require(len(slots) == denominator, "selected bank does not contain every replicate")
        scores = [
            float(lake_history_log_score(np.asarray(row["lake_exposures"], dtype=float),
                                         np.asarray(means, dtype=float), power=power, age1=age1))
            for row in slots if row["valid"]
        ]
        result.append(logmeanexp(scores, denominator))
    return result


def collect_hex_digests(value: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            result.update(collect_hex_digests(key))
            result.update(collect_hex_digests(item))
    elif isinstance(value, list):
        for item in value:
            result.update(collect_hex_digests(item))
    elif isinstance(value, str) and len(value) == 64:
        try:
            int(value, 16)
        except ValueError:
            pass
        else:
            result.add(value.lower())
    return result


def verify_execution_receipt(
    receipt_path: Path,
    exit_path: Path,
    gate_manifest_hash: str,
    analysis_report_hash: str,
    frozen_file_count: int,
    decision: str,
) -> dict[str, Any]:
    receipt = read_json(receipt_path)
    require(int(exit_path.read_text().strip()) == 0, "remote gate exit code is not zero")
    require(str(receipt.get("status", "")).lower() == "complete" and
            str(receipt.get("generation_status", "")).lower() == "complete",
            "remote execution receipt is not complete")
    require(receipt.get("analysis_decision") == decision,
            "execution receipt decision differs from reconstructed analysis")
    require(receipt.get("historical_observations_read") is False,
            "execution receipt reports a historical observation read")
    require(receipt.get("source_files_reverified") == frozen_file_count,
            "execution receipt did not reverify every frozen source file")
    require(receipt.get("manifest_sha256") == gate_manifest_hash and
            receipt.get("analysis_sha256") == analysis_report_hash,
            "execution receipt hashes differ from returned gate/analysis")
    for key, value in receipt.items():
        lowered = key.lower()
        if "exit_code" in lowered:
            require(int(value) == 0, f"nonzero execution receipt field: {key}")
        if lowered.endswith("status"):
            require(str(value).lower() not in {"failed", "failure", "error", "incomplete"},
                    f"failed execution receipt status: {key}")
    digests = collect_hex_digests(receipt)
    required = {gate_manifest_hash, analysis_report_hash}
    require(required <= digests,
            "execution receipt does not bind the gate manifest and analysis report")
    return {"sha256": sha256(receipt_path), "gate_exit_code": 0,
            "bound_required_hashes": sorted(required), "top_level_keys": sorted(receipt)}


def write_results(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def write_markdown(path: Path, audit: Mapping[str, Any]) -> None:
    gate = audit["gate"]
    score = audit["sampled_scalar_replay"]
    lines = [
        "# Independent final audit: early-Lake production gate", "",
        f"**{audit['status']} — {audit['recommendation']}**", "",
        "The audit read only the frozen synthetic production archives and analysis outputs. "
        "It did not run demographic histories or load the historical Lake observations.", "",
        "## Evidence", "",
        f"- {audit['archive']['source_rows']:,} source rows and {audit['archive']['feature_rows']:,} "
        "ordered feature/history rows were complete and hash-bound.",
        f"- Status counts: `{audit['archive']['status_counts']}`; all valid histories had 25 annual "
        "advances and all retained algebraic failures had zero.",
        f"- All {audit['analysis']['group_count']} prescribed analysis groups and "
        f"{audit['analysis']['primary_group_count']} primary age-six groups were independently reconstructed.",
        f"- R `qbeta` independently reproduced {audit['analysis']['cp_interval_count']} exact "
        "Clopper–Pearson intervals.",
        f"- The scalar Lake score replayed {score['query_count']} deterministic query vectors across "
        f"{score['bank_vector_count']} bank variants; maximum absolute score difference was "
        f"{score['maximum_absolute_ell_difference']:.3g}.",
        f"- Reconstructed decision: `{gate['decision']}`; the raw, non-qualifying directed-pair "
        f"intersection was `{gate['robust_primary_directed_pairs']}`.",
        f"- Primary failure counts: `{gate['primary_failure_reasons']}`; age-eight sensitivity "
        f"failure counts: `{audit['analysis']['sensitivity_failure_reasons']}`.", "",
        "## Interpretation", "",
        audit["interpretation"], "",
        "## Residual risk", "",
        audit["residual_risk"], "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(lines))
    temporary.replace(path)


def audit(args: argparse.Namespace) -> dict[str, Any]:
    gate, analysis = args.gate.resolve(), args.analysis.resolve()
    require(gate.is_dir() and analysis.is_dir(), "production gate or analysis directory is incomplete")
    manifest_path, report_path = gate / "manifest.json", analysis / "recovery_gate.json"
    frozen_path = args.frozen_manifest.resolve()
    manifest, report, frozen = read_json(manifest_path), read_json(report_path), read_json(frozen_path)
    require(frozen.get("production_site_history_attempts") == EXPECTED_HISTORIES,
            "frozen manifest does not authorize the fixed production size")
    manifest_check = verify_manifest(gate, manifest, frozen)
    sources, source_map, source_check = verify_sources(gate, manifest)
    feature_groups, history_check = verify_histories(gate, manifest, sources, source_map)

    expected_names = expected_detail_names()
    actual_names = {path.name for path in analysis.glob("A*.json.gz")}
    require(actual_names == expected_names, "analysis does not contain exactly 32 prescribed detail files")
    require({path.name for path in analysis.iterdir()} == expected_names | {"recovery_gate.json", "group_summary.csv"},
            "analysis directory contains missing or unexpected outputs")
    require(report.get("run_mode") == "gate" and report.get("attempted_histories") == EXPECTED_HISTORIES,
            "analysis report is not the completed production gate")
    require(report.get("historical_observations_read") is False,
            "analysis reports reading historical observations")
    require(report.get("run_manifest_sha256") == sha256(manifest_path) and
            report.get("features_sha256") == sha256(gate / "features.jsonl.gz"),
            "analysis report is not bound to the production archive")
    require(report.get("analyzer_sha256") == manifest["source_bindings"]["scripts/analyze_age_early_lake.py"]["sha256"] and
            report.get("protocol_sha256") == manifest["source_bindings"]["docs/early_lake_mechanism_protocol.md"]["sha256"],
            "analysis report is not bound to the frozen analyzer and protocol")

    report_groups = {
        (group["maximum_age"], group["quality_regime"], group["index_stratum"], group["profile"]): group
        for group in report["groups"]
    }
    require(len(report_groups) == 32, "analysis report does not contain 32 unique groups")
    contexts: dict[tuple[int, str, str, str], dict[str, Any]] = {}
    cp_requests: list[tuple[int, int, float]] = []
    primary_pair_table_count = 0
    primary_direction_count = 0
    for key in sorted(report_groups):
        age, quality, stratum, profile = key
        summary = report_groups[key]
        detail_path = analysis / summary["detail_file"]
        require(detail_path.name == f"A{age}_{quality}_{stratum}_{profile}.json.gz",
                "group detail filename differs")
        require(sha256(detail_path) == summary["detail_hashes"]["sha256"],
                "group detail physical hash differs")
        detail, content_hash = detail_object(detail_path)
        require(content_hash == summary["detail_hashes"]["content_sha256"],
                "group detail content hash differs")
        require(detail["group"] == {"maximum_age": age, "quality_regime": quality,
                                     "index_stratum": stratum, "profile": profile},
                "group detail identity differs")
        summary_without_hash = {name: value for name, value in summary.items() if name != "detail_hashes"}
        require(detail["assessment"] == summary_without_hash,
                "detail assessment differs from recovery report")
        features = feature_groups[(age, quality, stratum)]
        bank_ids = sorted({row["source_id"] for row in features if row["role"] == "bank"})
        require(len(bank_ids) == SOURCE_COUNT // 2 and detail["bank_source_ids"] == bank_ids,
                "bank source identities differ from production archive")
        masks = source_halves(bank_ids)
        require(detail["bank_masks"] == masks and sum(masks["half_a"]) == sum(masks["half_b"]) == 128,
                "bank halves do not split whole source IDs 128/128")
        counts, selected = validate_observations(detail, features, profile)
        require(counts == summary["counts"], "group Z/count accounting differs")
        expected_status_counts = dict(Counter(row["status"] for row in features if row["role"] == "bank"))
        require(expected_status_counts == summary["bank_status_counts"], "bank status counts differ")
        require(summary["bank_sources"] == len(bank_ids), "bank source count differs")
        all_nonempty = all(counts[role][label]["z1"] > 0
                           for role in counts for label in RESTRICTIONS)
        require(bool(detail["banks"]) is all_nonempty, "bank scoring presence differs from Z=1 samples")
        context = {"key": key, "summary": summary, "detail": detail, "features": features,
                   "bank_ids": bank_ids, "masks": masks, "counts": counts,
                   "selected": selected, "all_nonempty": all_nonempty}
        contexts[key] = context
        if all_nonempty:
            n_test = len(selected["test"])
            for bank in BANKS:
                saved = detail["banks"][bank]
                sets = np.asarray(saved["sets"], dtype=bool)
                supported = np.asarray(saved["supported"], dtype=bool)
                require(sets.shape == (n_test, 4) and supported.shape == (n_test,),
                        "saved restriction-set shape differs")
                require(np.all(sets[~supported]), "unsupported queries do not receive the full set")
                true_test = [row["true_restriction"] for row in selected["test"]]
                for true_index, true_label in enumerate(RESTRICTIONS):
                    selected_class = np.asarray([label == true_label for label in true_test])
                    n = int(selected_class.sum())
                    require(n > 0, "true test class is empty after all-nonempty check")
                    k = int(sets[selected_class, true_index].sum())
                    cp_requests.append((k, n, .05 / 4))
                    for false_index, false_label in enumerate(RESTRICTIONS):
                        if false_index == true_index:
                            continue
                        events = sets[selected_class, true_index] & ~sets[selected_class, false_index]
                        cp_requests.append((int(events.sum()), n, .05 / 12))
                        if age == 6:
                            primary_direction_count += 1
                if age == 6:
                    primary_pair_table_count += 1

    cp_values = r_clopper_pearson(cp_requests)
    cp_interval_checks = 0
    reconstructed_groups: dict[tuple[int, str, str, str], dict[str, Any]] = {}
    for key, context in contexts.items():
        age, quality, stratum, profile = key
        summary, detail, counts = context["summary"], context["detail"], context["counts"]
        reasons: list[str] = []
        unexpected = sum(row["status"] not in ("valid", "algebraically_infeasible")
                         for row in context["features"])
        if unexpected:
            reasons.append("unexpected_process_failure")
        if any(counts["calibration"][label]["z1"] < 39 or
               counts["test"][label]["z1"] == 0 for label in RESTRICTIONS):
            reasons.append("insufficient_conditional_sample")
        informative_pairs: list[str] = []
        bank_summaries: dict[str, Any] = {}
        stability: dict[str, Any] = {}
        if context["all_nonempty"]:
            true_test = [row["true_restriction"] for row in context["selected"]["test"]]
            predicted: dict[str, np.ndarray] = {}
            for bank in BANKS:
                saved = detail["banks"][bank]
                sets = np.asarray(saved["sets"], dtype=bool)
                supported = np.asarray(saved["supported"], dtype=bool)
                predicted[bank] = sets
                coverage, directed, support, empty = {}, {}, {}, {}
                for true_index, true_label in enumerate(RESTRICTIONS):
                    selected_class = np.asarray([label == true_label for label in true_test])
                    n = int(selected_class.sum())
                    k = int(sets[selected_class, true_index].sum())
                    lower, upper = cp_values[(k, n, .05 / 4)]
                    coverage[true_label] = {"n": n, "k": k, "rate": k / n,
                                            "lower": lower, "upper": upper}
                    support[true_label] = float(supported[selected_class].mean())
                    empty[true_label] = int((~sets[selected_class].any(axis=1)).sum())
                    for false_index, false_label in enumerate(RESTRICTIONS):
                        if false_index == true_index:
                            continue
                        events = sets[selected_class, true_index] & ~sets[selected_class, false_index]
                        event_k = int(events.sum())
                        event_lower, event_upper = cp_values[(event_k, n, .05 / 12)]
                        directed[f"{true_label}->{false_label}"] = {
                            "n": n, "k": event_k, "rate": event_k / n,
                            "lower": event_lower, "upper": event_upper,
                        }
                reconstructed = {"coverage": coverage, "directed": directed,
                                 "support_fraction": support, "empty_sets": empty,
                                 "selected_source_count": sum(context["masks"][bank])}
                bank_summaries[bank] = reconstructed
                saved_summary = summary["banks"][bank]
                require(reconstructed["selected_source_count"] == saved_summary["selected_source_count"] and
                        reconstructed["support_fraction"] == saved_summary["support_fraction"] and
                        reconstructed["empty_sets"] == saved_summary["empty_sets"],
                        "bank support/count summary differs")
                for category in ("coverage", "directed"):
                    require(set(reconstructed[category]) == set(saved_summary[category]),
                            "binomial summary labels differ")
                    for label, values in reconstructed[category].items():
                        saved_values = saved_summary[category][label]
                        require(values["n"] == saved_values["n"] and values["k"] == saved_values["k"],
                                "binomial counts differ")
                        for field in ("rate", "lower", "upper"):
                            close_number(saved_values[field], values[field],
                                         f"{key}.{bank}.{category}.{label}.{field}")
                        cp_interval_checks += 1
            for first, second in (("full", "half_a"), ("full", "half_b"), ("half_a", "half_b")):
                comparison = {}
                for true_index, true_label in enumerate(RESTRICTIONS):
                    selected_class = np.asarray([label == true_label for label in true_test])
                    a, b = predicted[first][selected_class], predicted[second][selected_class]
                    comparison[true_label] = {
                        "set_agreement": float(np.all(a == b, axis=1).mean()),
                        "coverage_gap": abs(float(a[:, true_index].mean()) -
                                            float(b[:, true_index].mean())),
                    }
                stability[f"{first}:{second}"] = comparison
            require(stability == summary["stability"], "bank-half stability summary differs")
            if any(value < .95 for bank in bank_summaries.values()
                   for value in bank["support_fraction"].values()):
                reasons.append("bank_support")
            if any(value["set_agreement"] < .90 or value["coverage_gap"] > .05 + 1e-12
                   for comparison in stability.values() for value in comparison.values()):
                reasons.append("bank_half_instability")
            coverage_values = [value for bank in bank_summaries.values()
                               for value in bank["coverage"].values()]
            if any(value["lower"] < .90 for value in coverage_values):
                reasons.append("coverage_failed" if any(value["upper"] < .90
                                                        for value in coverage_values)
                               else "coverage_precision_unassessed")
            pair_sets = [
                {label for label, value in bank_summaries[bank]["directed"].items()
                 if value["lower"] > .5}
                for bank in BANKS
            ]
            informative_pairs = sorted(set.intersection(*pair_sets))
        qualified = not reasons
        status = "COVERAGE_FAILED" if "coverage_failed" in reasons else (
            "QUALIFIED" if qualified else "UNASSESSED")
        require(summary["reasons"] == reasons and summary["qualified"] is qualified and
                summary["status"] == status and summary["informative_pairs"] == informative_pairs,
                f"reconstructed group decision differs: {key}")
        reconstructed_groups[key] = {"qualified": qualified, "reasons": reasons,
                                     "informative_pairs": informative_pairs}

    primary = [value for key, value in reconstructed_groups.items() if key[0] == 6]
    require(len(primary) == 16, "primary gate does not contain 16 groups")
    robust_pairs = sorted(set.intersection(*(set(value["informative_pairs"]) for value in primary)))
    if not all(value["qualified"] for value in primary):
        decision = "STOP_EARLY_RECOVERY_UNASSESSED"
    elif not robust_pairs:
        decision = "STOP_EARLY_RECOVERY_LOW_INFORMATION"
    else:
        decision = "GO_ELIGIBLE_EARLY_COMPARISON"
    failure_reasons = dict(Counter(reason for value in primary for reason in value["reasons"]))
    require(report["decision"] == decision and
            report["robust_primary_directed_pairs"] == robust_pairs and
            report["primary_groups"] == 16 and
            report["qualified_primary_groups"] == sum(value["qualified"] for value in primary) and
            report["primary_failure_reasons"] == failure_reasons,
            "reconstructed primary decision differs from recovery report")
    historical_permission = decision.startswith("GO_")
    require(report["historical_comparison_permitted"] is historical_permission,
            "historical permission does not follow the frozen decision")
    if not historical_permission:
        require(report["historical_comparison_permitted"] is False,
                "STOP result permits historical comparison")
    require(primary_pair_table_count == 16 * 3 and primary_direction_count == 16 * 3 * 12,
            "primary directed-pair tables are incomplete")
    sensitivity = [value for key, value in reconstructed_groups.items() if key[0] == 8]
    require(len(sensitivity) == 16, "age-eight sensitivity does not contain 16 groups")
    sensitivity_failure_reasons = dict(Counter(
        reason for value in sensitivity for reason in value["reasons"]
    ))

    # One deterministic Z=1 test query per scored group, up to the requested cap.
    candidates = []
    for key, context in contexts.items():
        if not context["all_nonempty"]:
            continue
        group_candidates = []
        for index, observation in enumerate(context["selected"]["test"]):
            token = json.dumps([key, observation["source_id"], observation["true_restriction"]],
                               separators=(",", ":"))
            group_candidates.append((hashlib.sha256(token.encode()).hexdigest(), key, index))
        candidates.append(min(group_candidates))
    chosen = heapq.nsmallest(min(args.score_samples, len(candidates)), candidates)
    require(chosen, "no scored test query is available for scalar replay")
    max_ell_difference = 0.0
    bank_vectors = 0
    rank_checks = 0
    for _, key, test_index in chosen:
        context = contexts[key]
        detail, profile = context["detail"], key[3]
        observation = context["selected"]["test"][test_index]
        for bank in BANKS:
            selected_ids = [source_id for source_id, keep in
                            zip(context["bank_ids"], context["masks"][bank], strict=True) if keep]
            ell = manual_bank_vector(context["features"], selected_ids, observation["means"],
                                     age1=PROFILES[profile]["age1"], power=PROFILES[profile]["power"])
            saved = [number(value) for value in detail["banks"][bank]["ell_test"][test_index]]
            for candidate, (value, expected) in enumerate(zip(saved, ell, strict=True)):
                max_ell_difference = max(max_ell_difference,
                                         close_number(value, expected, f"scalar.{key}.{bank}.{candidate}"))
            bank_vectors += 1
            calibration = [[number(value) for value in row]
                           for row in detail["banks"][bank]["ell_calibration"]]
            true_cal = [row["true_restriction"] for row in context["selected"]["calibration"]]
            query_nc = [nonconformity(ell, candidate) for candidate in range(4)]
            expected_set = []
            for candidate, label in enumerate(RESTRICTIONS):
                cal_rows = [row for row, true_label in zip(calibration, true_cal, strict=True)
                            if true_label == label]
                cal_nc = [nonconformity(row, candidate) for row in cal_rows]
                relative = query_nc[candidate][0]
                absolute = query_nc[candidate][1]
                p_relative = (1 + sum(value[0] >= relative for value in cal_nc)) / (len(cal_nc) + 1)
                p_absolute = (1 + sum(value[1] >= absolute for value in cal_nc)) / (len(cal_nc) + 1)
                close_number(detail["banks"][bank]["p_relative"][test_index][candidate], p_relative,
                             f"rank.relative.{key}.{bank}.{candidate}")
                close_number(detail["banks"][bank]["p_absolute"][test_index][candidate], p_absolute,
                             f"rank.absolute.{key}.{bank}.{candidate}")
                expected_set.append(p_relative > .025 and p_absolute > .025)
                rank_checks += 2
            if query_nc[0][2]:
                expected_set = [True] * 4
            require(detail["banks"][bank]["sets"][test_index] == expected_set,
                    "sampled restriction set differs from scalar rank replay")

    with (analysis / "group_summary.csv").open(newline="") as stream:
        table = list(csv.DictReader(stream))
    require(len(table) == 32 and len({(row["maximum_age"], row["quality_regime"],
                                      row["index_stratum"], row["profile"]) for row in table}) == 32,
            "group summary CSV is incomplete")

    gate_manifest_hash = sha256(manifest_path)
    report_hash = sha256(report_path)
    frozen_hash = sha256(frozen_path)
    execution = verify_execution_receipt(args.execution_receipt.resolve(),
                                         args.gate_exit_code.resolve(), gate_manifest_hash,
                                         report_hash, len(frozen["files"]), decision)
    recommendation = ("Historical comparison is eligible under the frozen procedure."
                      if historical_permission else
                      "Stop without historical scoring under the frozen procedure.")
    if decision == "GO_ELIGIBLE_EARLY_COMPARISON":
        interpretation = (
            "The synthetic set-valued rule met its fixed engineering recovery gate. This is not a "
            "posterior mechanism probability or an identified causal attribution."
        )
    elif decision == "STOP_EARLY_RECOVERY_LOW_INFORMATION":
        interpretation = (
            "The adequately covered, stable procedure had no qualifying directed exclusion. This "
            "is low information under the fixed engineering distribution, not proof of intrinsic "
            "non-identifiability, equifinality, or any historical mechanism probability."
        )
    else:
        interpretation = (
            "The synthetic result is unassessed because prespecified stability or coverage checks "
            "failed. The raw directed-pair intersection cannot qualify a contrast. This does not "
            "establish intrinsic non-identifiability, equifinality, or any historical mechanism probability."
        )
    return {
        "status": "PASS", "recommendation": recommendation,
        "historical_observations_read": False,
        "gate": {"decision": decision, "historical_comparison_permitted": historical_permission,
                 "robust_primary_directed_pairs": robust_pairs,
                 "raw_pair_intersection_is_qualifying": historical_permission,
                 "qualified_primary_groups": sum(value["qualified"] for value in primary),
                 "primary_failure_reasons": failure_reasons},
        "archive": {**source_check, **history_check, **manifest_check},
        "analysis": {"group_count": 32, "primary_group_count": 16,
                     "cp_engine": "R qbeta", "cp_interval_count": cp_interval_checks,
                     "primary_bank_pair_tables": primary_pair_table_count,
                     "primary_directed_intervals": primary_direction_count,
                     "sensitivity_group_count": len(sensitivity),
                     "qualified_sensitivity_groups": sum(value["qualified"] for value in sensitivity),
                     "sensitivity_failure_reasons": sensitivity_failure_reasons},
        "sampled_scalar_replay": {"query_count": len(chosen), "bank_vector_count": bank_vectors,
                                  "rank_component_checks": rank_checks,
                                  "maximum_absolute_ell_difference": max_ell_difference,
                                  "score_function": "lake_history_log_score scalar"},
        "bindings": {"gate_manifest_sha256": gate_manifest_hash,
                     "analysis_report_sha256": report_hash,
                     "frozen_source_manifest_sha256": frozen_hash,
                     "audit_script_sha256": sha256(Path(__file__)),
                     "execution_receipt": execution},
        "interpretation": interpretation,
        "residual_risk": (
            "The test population remains the declared conditional engineering distribution. Under this "
            "STOP there is no permitted historical comparison, and the raw pair intersection must not be "
            "reused as evidence. A different historical analysis would require a separately approved design."
            if not historical_permission else
            "The test population remains the declared conditional engineering distribution. The permitted "
            "historical comparison must preserve the conservative union and robust-pair rules; independent "
            "review of that historical-results receipt would materially affect confidence."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    base = ROOT / "outputs/remote/age_early_lake_20261004"
    record = ROOT / "data/early_lake_mechanism_20261004"
    parser.add_argument("--gate", type=Path, default=base / "gate")
    parser.add_argument("--analysis", type=Path, default=base / "analysis")
    parser.add_argument("--execution-receipt", type=Path, default=base / "execution_receipt.json")
    parser.add_argument("--gate-exit-code", type=Path, default=base / "gate_exit_code.txt")
    parser.add_argument("--frozen-manifest", type=Path,
                        default=record / "frozen_source_manifest.json")
    parser.add_argument("--output-json", type=Path, default=record / "results_audit.json")
    parser.add_argument("--output-md", type=Path, default=record / "results_audit.md")
    parser.add_argument("--score-samples", type=int, default=32)
    args = parser.parse_args()
    require(1 <= args.score_samples <= 128, "score-samples must be in 1..128")
    result = audit(args)
    write_results(args.output_json, result)
    write_markdown(args.output_md, result)
    print(json.dumps({"status": result["status"], "recommendation": result["recommendation"],
                      "decision": result["gate"]["decision"],
                      "sampled_query_vectors": result["sampled_scalar_replay"]["query_count"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
