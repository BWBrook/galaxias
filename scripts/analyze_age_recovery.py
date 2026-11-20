#!/usr/bin/env python3
"""Analyze the bounded synthetic age-model recovery bank.

This script consumes the linked runner's JSONL artifacts.  It never runs the
demographic model: only complete histories are converted to observations and
scored against complete inference-bank histories.  The default execution uses
all 540 frozen decision profiles and all three declared observation generators.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from galaxias_model.age_recovery_observation import (  # noqa: E402
    BINARY_RECORDS,
    decision_profiles,
    exposures,
    generate_observations,
)
from galaxias_model.age_recovery_scores import classify, recovery_metrics, score_blocks  # noqa: E402


GENERATORS = ("poisson", "gamma_quality", "fixed_creek_total")
BLOCKS = ("creek", "survey", "full", "feasibility")
MIN_BANK_SOURCES = 8
MIN_TRUTH_SOURCES = 16
ANALYSIS_BINDING_PATHS = (
    "scripts/analyze_age_recovery.py",
    "scripts/run_age_recovery.py",
    "src/galaxias_model/age_recovery_scores.py",
    "src/galaxias_model/age_recovery_observation.py",
    "src/galaxias_model/age_sources.py",
    "docs/age_linked_recovery_protocol.md",
    "docs/age_structured_protocol_candidate2.md",
    "data/age_structured_design_20260929/scenarios.json",
    "uv.lock",
    "pyproject.toml",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _binding(path: Path) -> dict[str, Any]:
    return {"sha256": _hash_file(path), "bytes": path.stat().st_size}


def _analysis_bindings() -> dict[str, dict[str, Any]]:
    bindings = {}
    for relative in ANALYSIS_BINDING_PATHS:
        path = ROOT / relative
        if not path.is_file():
            raise ValueError(f"analysis binding file is missing: {relative}")
        bindings[relative] = _binding(path)
    return bindings


def _verify_bindings(bindings: dict[str, dict[str, Any]], *, label: str) -> None:
    if not isinstance(bindings, dict) or not bindings:
        raise ValueError(f"{label} are missing")
    for relative, expected in bindings.items():
        path = ROOT / str(relative)
        if not path.is_file():
            raise ValueError(f"{label} file is missing: {relative}")
        if not isinstance(expected, dict) or _binding(path) != {
            "sha256": expected.get("sha256"),
            "bytes": expected.get("bytes"),
        }:
            raise ValueError(f"{label} mismatch: {relative}")


def _hash_decompressed(path: Path) -> str:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path, *, compressed: bool = False) -> list[dict[str, Any]]:
    opener = gzip.open if compressed else open
    rows: list[dict[str, Any]] = []
    with opener(path, "rt", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"JSONL row at {path}:{line_number} is not an object")
            rows.append(row)
    return rows


def _verify_generation_manifest(input_dir: Path, source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_path = input_dir / "run_manifest.json"
    if not manifest_path.is_file():
        raise ValueError("input directory must contain run_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise ValueError(f"generation manifest is not complete: {manifest.get('status')!r}")
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict):
        raise ValueError("generation manifest lacks output bindings")
    for name, expected in outputs.items():
        path = input_dir / str(name)
        if not path.is_file():
            raise ValueError(f"generation output is missing: {name}")
        if not isinstance(expected, dict) or _binding(path) != {
            "sha256": expected.get("sha256"),
            "bytes": expected.get("bytes"),
        }:
            raise ValueError(f"generation output hash/size mismatch: {name}")
    required = {"source_banks.jsonl", "histories.jsonl.gz", "full_histories.jsonl.gz"}
    if not required.issubset(outputs):
        raise ValueError(f"generation manifest does not bind required outputs: {sorted(required - set(outputs))}")
    content_hashes = manifest.get("content_sha256", {})
    if content_hashes:
        for name, expected in (
            ("histories.jsonl.gz", content_hashes.get("histories.jsonl")),
            ("full_histories.jsonl.gz", content_hashes.get("full_histories.jsonl")),
        ):
            if expected is not None and _hash_decompressed(input_dir / name) != expected:
                raise ValueError(f"generation content hash mismatch: {name}")
    _verify_bindings(manifest.get("source_bindings", {}), label="generation source bindings")
    roles = {}
    for row in source_rows:
        role = row.get("role")
        namespace = row.get("namespace")
        if role not in ("truth", "bank") or namespace != f"{manifest.get('run_namespace', '')}:{role}":
            raise ValueError("source_banks.jsonl has an invalid role/namespace binding")
        key = (str(row.get("cell_id")), role, str(row.get("source_id")))
        if key in roles:
            raise ValueError(f"duplicate source-bank identity: {key}")
        roles[key] = row
    if int(manifest.get("source_rows", len(source_rows))) != len(source_rows):
        raise ValueError("source-bank row count does not match generation manifest")
    return manifest


def _verify_history_source_matches(history_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    source_keys = {
        (str(row.get("cell_id")), str(row.get("role")), str(row.get("source_id")))
        for row in source_rows
    }
    seen: set[tuple[str, str, str, int]] = set()
    for row in history_rows:
        key = (str(row.get("cell_id")), str(row.get("namespace")), str(row.get("source_id")))
        if key not in source_keys:
            raise ValueError(f"history source identity is absent or mismatched in source_banks.jsonl: {key}")
        if row.get("namespace") not in ("truth", "bank"):
            raise ValueError("history namespace must be truth or bank")
        if row.get("cell_id") is None or row.get("source_id") is None:
            raise ValueError("history rows require cell_id and source_id")
        replicate = int(row.get("replicate", -1))
        identity = (*key, replicate)
        if identity in seen:
            raise ValueError(f"duplicate history source/replicate identity: {identity}")
        seen.add(identity)
    if "replicates_per_source" in manifest:
        expected = {
            (str(row.get("cell_id")), str(row.get("role")), str(row.get("source_id")), replicate)
            for row in source_rows
            for replicate in range(int(manifest["replicates_per_source"]))
        }
        if seen != expected:
            missing = sorted(expected - seen)[:3]
            extra = sorted(seen - expected)[:3]
            raise ValueError(f"history source coverage mismatch; missing={missing}, extra={extra}")


def _safe_name(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._")
    return result or "cell"


def _as_bool(value: Any, name: str) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)) and int(value) in (0, 1):
        return bool(value)
    raise ValueError(f"{name} must be boolean")


def _as_float(value: Any, name: str) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _complete_rows(rows: Iterable[dict[str, Any]], namespace: str) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if row.get("namespace") != namespace or row.get("status") != "complete":
            continue
        if not isinstance(row.get("features"), dict):
            raise ValueError(f"complete {namespace} row lacks feature dictionary: {row.get('source_id')}")
        if "terminal_alive" not in row:
            raise ValueError(f"complete {namespace} row lacks terminal_alive: {row.get('source_id')}")
        _as_bool(row["terminal_alive"], "terminal_alive")
        for field in ("cell_id", "source_id", "replicate", "index_stratum", "march_retention"):
            if field not in row:
                raise ValueError(f"complete history row lacks {field}")
        result.append(dict(row))
    return sorted(result, key=lambda x: (str(x["source_id"]), int(x["replicate"])))


def _select_profiles(spec: str | None) -> list[dict[str, Any]]:
    profiles = decision_profiles()
    if spec is None:
        return profiles
    path = Path(spec)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("profile_ids")
        if not isinstance(payload, list):
            raise ValueError("--profiles file must contain a list of profile IDs")
        wanted = [str(value) for value in payload]
    else:
        wanted = [part.strip() for part in spec.split(",") if part.strip()]
    by_id = {str(profile["profile_id"]): profile for profile in profiles}
    unknown = [profile_id for profile_id in wanted if profile_id not in by_id]
    if unknown:
        raise ValueError(f"unknown profile IDs: {unknown[:5]}")
    selected = [by_id[profile_id] for profile_id in wanted]
    if not selected:
        raise ValueError("--profiles selected no profiles")
    return selected


def _unique_count(values: Iterable[Any]) -> int:
    return len({str(value) for value in values})


def math_nan() -> float:
    return float("nan")


def _bank_summary(classification: dict[str, np.ndarray], bank_source_ids: list[str], bank_labels: np.ndarray) -> dict[str, Any]:
    counts = np.zeros(2, dtype=int)
    for class_value in (0, 1):
        counts[class_value] = _unique_count(
            source for source, label in zip(bank_source_ids, bank_labels) if bool(label) == bool(class_value)
        )
    ess0 = classification["ess0"]
    ess1 = classification["ess1"]
    return {
        "bank_histories": int(len(bank_source_ids)),
        "bank_sources_loss": int(counts[0]),
        "bank_sources_persist": int(counts[1]),
        "bank_coverage_sufficient": bool(np.all(counts >= MIN_BANK_SOURCES)),
        "bank_ess0_min": float(np.nanmin(ess0)) if ess0.size else math_nan(),
        "bank_ess1_min": float(np.nanmin(ess1)) if ess1.size else math_nan(),
        "bank_abstentions": int(np.sum(classification["prediction"] == -1)),
    }


def _metrics_row(
    metrics: dict[str, Any],
    classification: dict[str, np.ndarray],
    bank_source_ids: list[str],
    bank_labels: np.ndarray,
    *,
    prefix: str,
) -> dict[str, Any]:
    sensitivity = np.asarray(metrics["source_macro_sensitivity"], dtype=float)
    ci = np.asarray(metrics["source_cluster_ci95"], dtype=float)
    coverage = np.asarray(metrics["distinct_source_coverage"], dtype=int)
    counts = metrics["counts"]
    row: dict[str, Any] = {
        f"{prefix}_sensitivity_loss": float(sensitivity[0]),
        f"{prefix}_sensitivity_persist": float(sensitivity[1]),
        f"{prefix}_balanced_accuracy": float(metrics["balanced_accuracy"]),
        f"{prefix}_ci_lower95": float(ci[0]),
        f"{prefix}_ci_upper95": float(ci[1]),
        f"{prefix}_truth_sources_loss": int(coverage[0]),
        f"{prefix}_truth_sources_persist": int(coverage[1]),
        f"{prefix}_truth_coverage_sufficient": bool(metrics["truth_coverage_sufficient"]),
        f"{prefix}_abstentions": int(counts["n_abstentions"]),
        f"{prefix}_correct": int(counts["n_correct"]),
        f"{prefix}_rows": int(counts["n_data"]),
        f"{prefix}_gate_passed": bool(metrics["gate_passed"]),
    }
    row.update({f"{prefix}_{key}": value for key, value in _bank_summary(classification, bank_source_ids, bank_labels).items()})
    return row


def _recovery(
    classification: dict[str, np.ndarray],
    truth_rows: list[dict[str, Any]],
    mask: np.ndarray,
    *,
    bootstrap_replicates: int,
    paired_classification: dict[str, np.ndarray] | None = None,
) -> dict[str, Any]:
    source_ids = np.asarray([str(row["source_id"]) for row in truth_rows], dtype=str)
    truth_labels = np.asarray([_as_bool(row["terminal_alive"], "terminal_alive") for row in truth_rows], dtype=bool)
    prediction = np.asarray(classification["prediction"], dtype=np.int8)
    paired_prediction = None if paired_classification is None else np.asarray(paired_classification["prediction"], dtype=np.int8)
    selected = np.asarray(mask, dtype=bool)
    kwargs: dict[str, Any] = {
        "bootstrap_seed": 20261001,
        "bootstrap_replicates": bootstrap_replicates,
    }
    if paired_prediction is not None:
        kwargs["paired_prediction"] = paired_prediction[selected]
    return recovery_metrics(prediction[selected], truth_labels[selected], source_ids[selected], **kwargs)


def _coherence_rows(
    cell_id: str,
    profile: dict[str, Any],
    generator: str,
    truth_rows: list[dict[str, Any]],
    coherent: np.ndarray,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups: dict[tuple[str, int], list[int]] = defaultdict(list)
    for index, row in enumerate(truth_rows):
        groups[(str(row.get("index_stratum", "unknown")), int(_as_bool(row["terminal_alive"], "terminal_alive")))].append(index)
    for (stratum, class_value), indices in sorted(groups.items()):
        all_rows = [truth_rows[index] for index in indices]
        coherent_indices = [index for index in indices if bool(coherent[index])]
        coherent_rows = [truth_rows[index] for index in coherent_indices]
        row: dict[str, Any] = {
            "cell_id": cell_id,
            "profile_id": profile["profile_id"],
            "panel": profile["panel"],
            "generator": generator,
            "index_stratum": stratum,
            "terminal_class": "persist" if class_value else "loss",
            "histories": len(all_rows),
            "coherent_histories": len(coherent_rows),
            "coherence_rate": len(coherent_rows) / len(all_rows) if all_rows else math_nan(),
            "coherent_source_count": _unique_count(row["source_id"] for row in coherent_rows),
        }
        for field in ("refuge_index", "refuge_2002", "lake_2002"):
            all_values = np.asarray([_as_float(item[field], field) for item in all_rows], dtype=float)
            good_values = np.asarray([_as_float(item[field], field) for item in coherent_rows], dtype=float)
            row[f"mean_{field}_all"] = float(np.mean(all_values)) if all_values.size else math_nan()
            row[f"mean_{field}_coherent"] = float(np.mean(good_values)) if good_values.size else math_nan()
            row[f"shift_{field}_coherent_minus_all"] = (
                row[f"mean_{field}_coherent"] - row[f"mean_{field}_all"]
                if good_values.size else math_nan()
            )
        rows.append(row)
    return rows


def _process_rows(cell_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in rows:
        if row.get("status") == "complete" and "terminal_alive" in row:
            terminal_class = "persist" if _as_bool(row["terminal_alive"], "terminal_alive") else "loss"
        else:
            terminal_class = "unknown"
        counts[(str(row.get("namespace", "unknown")), str(row.get("index_stratum", "unknown")), terminal_class, str(row.get("status", "unknown")), str(row.get("failure") or ""))] += 1
    return [
        {
            "cell_id": cell_id,
            "namespace": namespace,
            "index_stratum": stratum,
            "terminal_class": terminal_class,
            "profile_id": "all",
            "generator": "all",
            "status": status,
            "failure": failure,
            "histories": count,
        }
        for (namespace, stratum, terminal_class, status, failure), count in sorted(counts.items())
    ]


def _failure_rows(cell_id: str, profile: dict[str, Any], generator: str, reasons: list[str]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for reason in reasons:
        if reason:
            for item in reason.split(";"):
                if item:
                    counts[item] += 1
    return [
        {
            "cell_id": cell_id,
            "profile_id": profile["profile_id"],
            "panel": profile["panel"],
            "generator": generator,
            "reason": reason,
            "histories": count,
        }
        for reason, count in sorted(counts.items())
    ]


def _control_feature(scale: float) -> dict[str, Any]:
    """Small complete feature vector used only by mechanical score controls."""
    return {
        "creek_early": [[3 * scale, 20 * scale]] * 20,
        "creek_feb": [2 * scale, 4 * scale],
        "creek_late": [[0.5 * scale, 2 * scale]] * 60,
        "lake": [[100 * scale, 10 * scale]] * 5 + [[0, 0]] * 3,
        "jan": [0, 8 * scale],
        "march": [0, 4 * scale],
        "ob_early": [[1 * scale, 2 * scale, 3 * scale]] * 3,
        "ob96": [1 * scale, 2 * scale, 3 * scale],
        "ob97": [1 * scale, 2 * scale, 3 * scale],
        "ob99": [1 * scale, 2 * scale, 3 * scale],
        "ob12": [1 * scale, 2 * scale, 3 * scale],
        "sg_early": [[1 * scale, 1 * scale, 3 * scale]] * 5,
        "sg08": [1 * scale, 2 * scale, 3 * scale],
        "early_minimum": 0,
    }


def _run_score_controls() -> dict[str, Any]:
    """Run score-only controls required before interpreting a recovery pass."""
    base = dict(decision_profiles()[0])
    base["q"] = 1.0
    low, high = _control_feature(1e-4), _control_feature(1.0)
    bank_features = [low] * 8 + [high] * 8
    bank_source_ids = [f"control-low-{index}" for index in range(8)] + [f"control-high-{index}" for index in range(8)]
    bank_labels = np.asarray([False] * 8 + [True] * 8, dtype=bool)
    bank_x = exposures(bank_features, base)
    binary_count = len(BINARY_RECORDS)
    observations = {
        "creek_counts": np.zeros((2, 3), dtype=np.int64),
        "lake_equivalents": np.zeros((2, 2), dtype=float),
        "binary_observed": np.asarray([[False] * binary_count, [True] * binary_count], dtype=bool),
    }
    parts = score_blocks(
        *bank_x,
        observations["creek_counts"],
        observations["lake_equivalents"],
        observations["binary_observed"],
        q=base["q"], creek_power=base["creek_power"], lake_power=base["lake_power"],
    )
    informative_scores = parts["total"]
    informative_classification = classify(informative_scores, bank_source_ids, bank_labels)
    exact_zero_features = [_control_feature(0.0)] * 8 + [high] * 8
    exact_zero_x = exposures(exact_zero_features, base)
    exact_zero_parts = score_blocks(
        *exact_zero_x,
        observations["creek_counts"],
        observations["lake_equivalents"],
        observations["binary_observed"],
        q=base["q"], creek_power=base["creek_power"], lake_power=base["lake_power"],
    )
    exact_zero_positive_scores = exact_zero_parts["total"][1, :8]
    informative_passed = bool(
        informative_classification["prediction"].tolist() == [0, 1]
        and np.all(informative_classification["ess0"] >= 4)
        and np.all(informative_classification["ess1"] >= 4)
        and np.all(np.isneginf(exact_zero_positive_scores))
    )

    identical_features = [_control_feature(1.0)] * 16
    identical_x = exposures(identical_features, base)
    identical_parts = score_blocks(
        *identical_x,
        observations["creek_counts"],
        observations["lake_equivalents"],
        observations["binary_observed"],
        q=base["q"], creek_power=base["creek_power"], lake_power=base["lake_power"],
    )
    identical_ids = [f"control-identical-{index}" for index in range(16)]
    identical_labels = np.asarray([False] * 8 + [True] * 8, dtype=bool)
    leakage_classification = classify(identical_parts["total"], identical_ids, identical_labels)
    leakage_passed = bool(
        np.all(leakage_classification["prediction"] == -1)
        and np.all(np.abs(leakage_classification["log_ratio"]) <= 1e-12)
    )
    controls = {
        "informative_high_near_zero": {
            "description": "Both supported classes use the same score map; high exposure histories are contrasted with near-zero histories, with an exact-zero positive-support check.",
            "bank_sources_per_class": 8,
            "near_zero_scale": 1e-4,
            "predictions": informative_classification["prediction"].tolist(),
            "log_ratios": informative_classification["log_ratio"].tolist(),
            "exact_zero_positive_scores_all_negative_infinity": bool(np.all(np.isneginf(exact_zero_positive_scores))),
            "passed": informative_passed,
            "control_score_only": True,
        },
        "identical_exposure_opposite_labels": {
            "description": "Identical complete feature vectors receive opposite bank labels and distinct source IDs; score evidence must remain tied.",
            "bank_sources_per_class": 8,
            "predictions": leakage_classification["prediction"].tolist(),
            "log_ratios": leakage_classification["log_ratio"].tolist(),
            "passed": leakage_passed,
            "control_score_only": True,
        },
    }
    controls["all_passed"] = bool(informative_passed and leakage_passed)
    canonical = json.dumps(controls, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    controls["sha256"] = hashlib.sha256(canonical).hexdigest()
    return controls


def _analyze_cell(payload: dict[str, Any]) -> dict[str, Any]:
    cell_id = str(payload["cell_id"])
    truth_rows = _complete_rows(payload["history_rows"], "truth")
    bank_rows = _complete_rows(payload["history_rows"], "bank")
    profiles = payload["profiles"]
    generators = payload["generators"]
    bootstrap_replicates = int(payload["bootstrap_replicates"])
    truth_features = [row["features"] for row in truth_rows]
    truth_identities = [(str(row["source_id"]), int(row["replicate"])) for row in truth_rows]
    truth_retention = [_as_bool(row["march_retention"], "march_retention") for row in truth_rows]
    strata = sorted(
        {str(row.get("index_stratum", "unknown")) for row in truth_rows}
        | {str(row.get("index_stratum", "unknown")) for row in bank_rows}
    )
    states: dict[str, dict[str, Any]] = {}
    for stratum in strata:
        truth_indices = np.asarray(
            [index for index, row in enumerate(truth_rows) if str(row.get("index_stratum", "unknown")) == stratum],
            dtype=int,
        )
        bank_indices = np.asarray(
            [index for index, row in enumerate(bank_rows) if str(row.get("index_stratum", "unknown")) == stratum],
            dtype=int,
        )
        stratum_truth = [truth_rows[index] for index in truth_indices]
        stratum_bank = [bank_rows[index] for index in bank_indices]
        states[stratum] = {
            "truth_rows": stratum_truth,
            "bank_rows": stratum_bank,
            "truth_indices": truth_indices,
            "bank_indices": bank_indices,
            "generated": {key: [] for key in ("creek_counts", "lake_equivalents", "binary_counts", "binary_observed", "coherent", "failure_reasons")},
            "predictions": {f"prediction_{block}": [] for block in BLOCKS},
            "log_ratios": {f"log_ratio_{block}": [] for block in BLOCKS},
            "ess0s": {f"ess0_{block}": [] for block in BLOCKS},
            "ess1s": {f"ess1_{block}": [] for block in BLOCKS},
            "exposure_creek": [],
            "exposure_lake": [],
            "exposure_binary": [],
        }
    gate_rows: list[dict[str, Any]] = []
    coherence_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    for generator in generators:
        for profile in profiles:
            obs = generate_observations(
                truth_features,
                truth_identities,
                truth_retention,
                profile,
                generator=generator,
            )
            coherence = np.asarray(obs["coherent"], dtype=bool)
            coherence_rows.extend(_coherence_rows(cell_id, profile, generator, truth_rows, coherence))
            failure_rows.extend(_failure_rows(cell_id, profile, generator, list(obs["failure_reasons"])))
            for stratum, state in states.items():
                truth_indices = state["truth_indices"]
                bank_rows_for_stratum = state["bank_rows"]
                bank_features = [row["features"] for row in bank_rows_for_stratum]
                bank_source_ids = [str(row["source_id"]) for row in bank_rows_for_stratum]
                bank_labels = np.asarray([_as_bool(row["terminal_alive"], "terminal_alive") for row in bank_rows_for_stratum], dtype=bool)
                creek_x, lake_x, binary_x = exposures(bank_features, profile)
                if generator == generators[0]:
                    state["exposure_creek"].append(creek_x)
                    state["exposure_lake"].append(lake_x)
                    state["exposure_binary"].append(binary_x)
                stratum_obs = {
                    "creek_counts": np.asarray(obs["creek_counts"])[truth_indices],
                    "lake_equivalents": np.asarray(obs["lake_equivalents"])[truth_indices],
                    "binary_observed": np.asarray(obs["binary_observed"])[truth_indices],
                }
                parts = score_blocks(
                    creek_x,
                    lake_x,
                    binary_x,
                    stratum_obs["creek_counts"],
                    stratum_obs["lake_equivalents"],
                    stratum_obs["binary_observed"],
                    q=profile["q"],
                    creek_power=profile["creek_power"],
                    lake_power=profile["lake_power"],
                )
                scores_by_block = {
                    "creek": parts["creek"],
                    "survey": parts["creek"] + parts["lake"],
                    "full": parts["total"],
                    "feasibility": np.zeros_like(parts["total"]),
                }
                classifications = {block: classify(scores, bank_source_ids, bank_labels) for block, scores in scores_by_block.items()}
                coherent_mask = coherence[truth_indices]
                stratum_truth_rows = state["truth_rows"]
                for key in state["generated"]:
                    value = obs["failure_reasons"] if key == "failure_reasons" else obs[key]
                    state["generated"][key].append(np.asarray(value, dtype=str)[truth_indices] if key == "failure_reasons" else np.asarray(value)[truth_indices])
                row: dict[str, Any] = {
                    "cell_id": cell_id,
                    "index_stratum": stratum,
                    "profile_id": profile["profile_id"],
                    "panel": profile["panel"],
                    "generator": generator,
                    "complete_truth_histories": len(stratum_truth_rows),
                    "coherent_truth_histories": int(np.sum(coherent_mask)),
                    "bank_histories": len(bank_rows_for_stratum),
                }
                for block in BLOCKS:
                    paired = classifications["survey"] if block == "full" else None
                    metrics = _recovery(
                        classifications[block],
                        stratum_truth_rows,
                        coherent_mask,
                        bootstrap_replicates=bootstrap_replicates,
                        paired_classification=paired,
                    )
                    row.update(_metrics_row(metrics, classifications[block], bank_source_ids, bank_labels, prefix=block))
                    if block == "full":
                        row["full_paired_delta_balanced_accuracy"] = float(metrics.get("paired_delta_balanced_accuracy", math_nan()))
                        delta_ci = metrics.get("paired_delta_balanced_accuracy_ci95")
                        row["full_paired_delta_ci_lower95"] = float(delta_ci[0]) if delta_ci is not None else math_nan()
                        row["full_paired_delta_ci_upper95"] = float(delta_ci[1]) if delta_ci is not None else math_nan()
                    state["predictions"][f"prediction_{block}"].append(classifications[block]["prediction"])
                    state["log_ratios"][f"log_ratio_{block}"].append(classifications[block]["log_ratio"])
                    state["ess0s"][f"ess0_{block}"].append(classifications[block]["ess0"])
                    state["ess1s"][f"ess1_{block}"].append(classifications[block]["ess1"])
                fail_prediction = np.where(coherent_mask, classifications["full"]["prediction"], -1).astype(np.int8)
                fail_classification = dict(classifications["full"], prediction=fail_prediction)
                metrics = _recovery(
                    fail_classification,
                    stratum_truth_rows,
                    np.ones(len(stratum_truth_rows), dtype=bool),
                    bootstrap_replicates=bootstrap_replicates,
                )
                fail_sens = np.asarray(metrics["source_macro_sensitivity"], dtype=float)
                fail_ci = np.asarray(metrics["source_cluster_ci95"], dtype=float)
                row.update(
                    {
                        "coverage_weighted_rows": int(len(stratum_truth_rows)),
                        "coverage_weighted_abstentions": int(np.sum(fail_prediction == -1)),
                        "coverage_weighted_sensitivity_loss": float(fail_sens[0]),
                        "coverage_weighted_sensitivity_persist": float(fail_sens[1]),
                        "coverage_weighted_balanced_accuracy": float(metrics["balanced_accuracy"]),
                        "coverage_weighted_ci_lower95": float(fail_ci[0]),
                        "coverage_weighted_ci_upper95": float(fail_ci[1]),
                        "coverage_weighted_gate_passed": False,
                    }
                )
                gate_rows.append(row)

    arrays_by_stratum: dict[str, dict[str, np.ndarray]] = {}
    n_generators = len(generators)
    n_profiles = len(profiles)
    for stratum, state in states.items():
        stratum_truth = state["truth_rows"]
        stratum_bank = state["bank_rows"]
        n_truth = len(stratum_truth)

        def stack(values: list[np.ndarray], dtype: Any | None = None) -> np.ndarray:
            if not values:
                return np.empty((n_generators, n_profiles, n_truth), dtype=dtype)
            result = np.asarray(values)
            if result.dtype == object and dtype is not object:
                result = result.astype(dtype)
            return result.reshape(n_generators, n_profiles, *result.shape[1:])

        arrays: dict[str, np.ndarray] = {
            "index_stratum": np.asarray([stratum], dtype=str),
            "profile_id": np.asarray([str(profile["profile_id"]) for profile in profiles], dtype=str),
            "generator": np.asarray(generators, dtype=str),
            "truth_source_id": np.asarray([str(row["source_id"]) for row in stratum_truth], dtype=str),
            "truth_replicate": np.asarray([int(row["replicate"]) for row in stratum_truth], dtype=np.int64),
            "truth_terminal_alive": np.asarray([_as_bool(row["terminal_alive"], "terminal_alive") for row in stratum_truth], dtype=bool),
            "truth_index_stratum": np.asarray([str(row.get("index_stratum", "unknown")) for row in stratum_truth], dtype=str),
            "truth_refuge_index": np.asarray([_as_float(row["refuge_index"], "refuge_index") for row in stratum_truth], dtype=float),
            "truth_refuge_2002": np.asarray([_as_float(row["refuge_2002"], "refuge_2002") for row in stratum_truth], dtype=float),
            "truth_lake_2002": np.asarray([_as_float(row["lake_2002"], "lake_2002") for row in stratum_truth], dtype=float),
            "bank_source_id": np.asarray([str(row["source_id"]) for row in stratum_bank], dtype=str),
            "bank_replicate": np.asarray([int(row["replicate"]) for row in stratum_bank], dtype=np.int64),
            "bank_terminal_alive": np.asarray([_as_bool(row["terminal_alive"], "terminal_alive") for row in stratum_bank], dtype=bool),
            "bank_index_stratum": np.asarray([str(row.get("index_stratum", "unknown")) for row in stratum_bank], dtype=str),
            "bank_refuge_index": np.asarray([_as_float(row["refuge_index"], "refuge_index") for row in stratum_bank], dtype=float),
            "bank_creek_exposures": np.asarray(state["exposure_creek"]).reshape(n_profiles, len(stratum_bank), 3),
            "bank_lake_exposures": np.asarray(state["exposure_lake"]).reshape(n_profiles, len(stratum_bank), 2),
            "bank_binary_exposures": np.asarray(state["exposure_binary"]).reshape(n_profiles, len(stratum_bank), len(BINARY_RECORDS)),
        }
        for key, values in state["generated"].items():
            arrays[key] = stack(values, dtype=str) if key == "failure_reasons" else stack(values)
        for collection in (state["predictions"], state["log_ratios"], state["ess0s"], state["ess1s"]):
            for key, values in collection.items():
                arrays[key] = stack(values)
        arrays_by_stratum[stratum] = arrays
    return {
        "cell_id": cell_id,
        "gate_rows": gate_rows,
        "coherence_rows": coherence_rows,
        "process_rows": _process_rows(cell_id, payload["history_rows"]),
        "failure_rows": failure_rows,
        "arrays_by_stratum": arrays_by_stratum,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        keys = set()
        for row in rows:
            keys.update(row)
        fieldnames = sorted(keys)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            clean = {}
            for key in fieldnames:
                value = row.get(key, "")
                if isinstance(value, (np.bool_, bool)):
                    clean[key] = int(value)
                elif isinstance(value, np.generic):
                    clean[key] = value.item()
                else:
                    clean[key] = value
            writer.writerow(clean)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=lambda value: value.item() if isinstance(value, np.generic) else str(value)) + "\n", encoding="utf-8")


def _run_analysis(
    input_dir: Path,
    output_dir: Path,
    *,
    workers: int = 1,
    bootstrap_replicates: int = 1000,
    profiles: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError(f"analysis output directory already exists: {output_dir}")
    if not input_dir.is_dir():
        raise ValueError(f"input directory does not exist: {input_dir}")
    if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= 16:
        raise ValueError("workers must be an integer in 1..16")
    if isinstance(bootstrap_replicates, bool) or not isinstance(bootstrap_replicates, int) or bootstrap_replicates < 1:
        raise ValueError("bootstrap_replicates must be a positive integer")
    source_path = input_dir / "source_banks.jsonl"
    histories_path = input_dir / "histories.jsonl.gz"
    if not source_path.is_file() or not histories_path.is_file():
        raise ValueError("input directory must contain source_banks.jsonl and histories.jsonl.gz")
    source_rows = _read_jsonl(source_path)
    history_rows = _read_jsonl(histories_path, compressed=True)
    manifest = _verify_generation_manifest(input_dir, source_rows)
    _verify_history_source_matches(history_rows, source_rows, manifest)
    # Freeze the exact implementation and design inputs used by this analysis.
    # The generation manifest is checked separately above; retaining both maps
    # makes a receipt auditable even when generation and analysis are staged.
    analysis_bindings = _analysis_bindings()
    cell_ids = sorted({str(row.get("cell_id")) for row in source_rows + history_rows if row.get("cell_id") is not None})
    if not cell_ids:
        raise ValueError("input artifacts contain no cell IDs")
    selected_profiles = decision_profiles() if profiles is None else profiles
    if not selected_profiles:
        raise ValueError("no profiles selected")
    generators = list(GENERATORS)
    by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in history_rows:
        if row.get("cell_id") is not None:
            by_cell[str(row["cell_id"])].append(row)
    payloads = [
        {
            "cell_id": cell_id,
            "history_rows": by_cell.get(cell_id, []),
            "profiles": selected_profiles,
            "generators": generators,
            "bootstrap_replicates": bootstrap_replicates,
        }
        for cell_id in cell_ids
    ]
    output_dir.mkdir(parents=True, exist_ok=False)
    arrays_dir = output_dir / "cell_arrays"
    arrays_dir.mkdir()
    started_at = _utc_now()
    try:
        if workers == 1:
            results = [_analyze_cell(payload) for payload in payloads]
        else:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                results = list(pool.map(_analyze_cell, payloads))
        gate_rows = [row for result in results for row in result["gate_rows"]]
        coherence_rows = [row for result in results for row in result["coherence_rows"]]
        process_rows = [row for result in results for row in result["process_rows"]]
        failure_rows = [row for result in results for row in result["failure_rows"]]
        _write_csv(output_dir / "gate_by_profile.csv", gate_rows)
        _write_csv(output_dir / "coherence_by_stratum.csv", coherence_rows)
        _write_csv(output_dir / "process_feasibility.csv", process_rows)
        _write_csv(output_dir / "observation_failure_reasons.csv", failure_rows)
        for result in results:
            for stratum, arrays in result["arrays_by_stratum"].items():
                np.savez_compressed(
                    arrays_dir / f"{_safe_name(result['cell_id'])}__stratum_{_safe_name(stratum)}.npz",
                    **arrays,
                )
        controls = _run_score_controls()
        _write_json(output_dir / "score_controls.json", controls)
        realistic = [
            row for row in gate_rows
            if controls["all_passed"]
            and row["panel"] == "base"
            and row["generator"] in ("poisson", "gamma_quality")
            and bool(row["full_gate_passed"])
        ]
        profile_subset = len(selected_profiles) != len(decision_profiles())
        full_generation = bool(manifest.get("full_design", False))
        if profile_subset or not full_generation:
            summary_status = "QUALIFICATION_SMOKE_ONLY"
        elif realistic:
            summary_status = "GO_CONDITIONAL"
        else:
            summary_status = "STOP_BEFORE_HISTORICAL_SEARCH"
        summary = {
            "status": summary_status,
            "conditional_go_columns": [
                {"cell_id": row["cell_id"], "index_stratum": row["index_stratum"],
                 "profile_id": row["profile_id"], "generator": row["generator"]}
                for row in realistic
            ],
            "profile_count": len(selected_profiles),
            "generator_count": len(generators),
            "full_generation_design": full_generation,
            "score_controls_passed": bool(controls["all_passed"]),
            "score_controls_sha256": controls["sha256"],
            "production_launch": False,
            "interpretation": "A pass is conditional endpoint-discrimination qualification for the declared source/world support; it is not posterior recovery, parameter identification, causal attribution, or empirical historical validation.",
            "unqualified_columns": "Non-base profiles, fixed-total controls, insufficient-support rows, and failed gates are sensitivity or diagnostic columns and do not independently authorize a historical claim.",
        }
        _write_json(output_dir / "summary.json", summary)
        (output_dir / "interpretation_limits.md").write_text(
            "# Age recovery analysis limits\n\n"
            f"Status: **{summary_status}**.\n\n"
            "This is a synthetic score-control and conditional endpoint-discrimination analysis. "
            "It does not produce a Bayesian posterior, recover empirical parameter probabilities, "
            "validate a demographic witness, estimate causal effects, or authorize production/historical search. "
            "Only a passing base-panel Poisson or gamma-quality column could receive the conditional GO label; "
            "all other columns remain unqualified diagnostics.\n",
            encoding="utf-8",
        )
        _write_json(output_dir / "reproducibility.json", {
            "profiles": [profile["profile_id"] for profile in selected_profiles],
            "generators": generators,
            "bootstrap_replicates": bootstrap_replicates,
            "workers": workers,
            "observation_seed_namespace": "age-observations-20261001",
            "bootstrap_seed": 20261001,
            "input_manifest_status": manifest.get("status"),
            "input_manifest_full_design": bool(manifest.get("full_design", False)),
            "source_input_rows": len(source_rows),
            "history_input_rows": len(history_rows),
            "analysis_bindings": analysis_bindings,
            "generation_source_bindings": manifest.get("source_bindings", {}),
        })
        _verify_bindings(analysis_bindings, label="analysis source bindings")
        outputs = {
            str(path.relative_to(output_dir)): _hash_file(path)
            for path in sorted(output_dir.rglob("*")) if path.is_file()
        }
        receipt = {
            "status": "complete",
            "started_at": started_at,
            "completed_at": _utc_now(),
            "input_dir": str(input_dir),
            "input_manifest_hash": _hash_file(input_dir / "run_manifest.json"),
            "input_hashes": {
                source_path.name: _hash_file(source_path),
                histories_path.name: _hash_file(histories_path),
                "full_histories.jsonl.gz": _hash_file(input_dir / "full_histories.jsonl.gz"),
            },
            "input_output_bindings": manifest.get("outputs", {}),
            "generation_source_bindings": manifest.get("source_bindings", {}),
            "analysis_bindings": analysis_bindings,
            "source_rows": len(source_rows),
            "history_rows": len(history_rows),
            "cells": cell_ids,
            "profiles": len(selected_profiles),
            "generators": generators,
            "outputs": outputs,
        }
        _write_json(output_dir / "analysis_receipt.json", receipt)
        return receipt
    except Exception as exc:
        _write_json(output_dir / "analysis_receipt.json", {
            "status": "failed",
            "started_at": started_at,
            "failed_at": _utc_now(),
            "error": f"{type(exc).__name__}: {exc}",
            "input_manifest_hash": _hash_file(input_dir / "run_manifest.json"),
            "input_hashes": {
                source_path.name: _hash_file(source_path),
                histories_path.name: _hash_file(histories_path),
                "full_histories.jsonl.gz": _hash_file(input_dir / "full_histories.jsonl.gz"),
            },
            "generation_source_bindings": manifest.get("source_bindings", {}),
            "analysis_bindings": analysis_bindings if "analysis_bindings" in locals() else {},
        })
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--bootstrap-replicates", type=int, default=1000)
    parser.add_argument("--profiles", help="comma-separated profile IDs or JSON file; intended for small fixtures")
    args = parser.parse_args(argv)
    selected = _select_profiles(args.profiles)
    _run_analysis(
        args.input_dir,
        args.output_dir,
        workers=args.workers,
        bootstrap_replicates=args.bootstrap_replicates,
        profiles=selected,
    )
    return 0


run_analysis = _run_analysis


if __name__ == "__main__":
    raise SystemExit(main())
