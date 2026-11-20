#!/usr/bin/env python3
"""Summarise completed linked-recovery generation and analysis artifacts.

This is accounting postprocessing only.  It verifies both upstream receipts,
keeps gate rows at cell/index-stratum resolution, and does not infer a pooled
GO decision, posterior quantity, or demographic conclusion.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_RELATIVE = "scripts/summarize_age_linked_recovery.py"


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


def _safe_child(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"bound path escapes its directory: {relative}") from exc
    return path


def _verify_generation(input_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = input_dir / "run_manifest.json"
    if not manifest_path.is_file():
        raise ValueError("generation input lacks run_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise ValueError(f"generation manifest is not complete: {manifest.get('status')!r}")
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict):
        raise ValueError("generation manifest lacks output bindings")
    required = {"source_banks.jsonl", "histories.jsonl.gz", "full_histories.jsonl.gz"}
    if not required.issubset(outputs):
        raise ValueError(f"generation manifest does not bind required outputs: {sorted(required - set(outputs))}")
    for name, expected in outputs.items():
        path = _safe_child(input_dir, str(name))
        if not path.is_file() or not isinstance(expected, dict):
            raise ValueError(f"generation output binding is invalid: {name}")
        if _binding(path) != {"sha256": expected.get("sha256"), "bytes": expected.get("bytes")}:
            raise ValueError(f"generation output hash/size mismatch: {name}")
    return manifest, {"run_manifest.json": _binding(manifest_path), **outputs}


def _verify_analysis(input_dir: Path, analysis_dir: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt_path = analysis_dir / "analysis_receipt.json"
    if not receipt_path.is_file():
        raise ValueError("analysis directory lacks analysis_receipt.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("status") != "complete":
        raise ValueError(f"analysis receipt is not complete: {receipt.get('status')!r}")
    if receipt.get("input_manifest_hash") != _hash_file(input_dir / "run_manifest.json"):
        raise ValueError("analysis receipt input manifest hash mismatch")
    expected_inputs = receipt.get("input_hashes")
    if not isinstance(expected_inputs, dict):
        raise ValueError("analysis receipt lacks input hashes")
    for name, expected_hash in expected_inputs.items():
        path = _safe_child(input_dir, str(name))
        if not path.is_file() or _hash_file(path) != expected_hash:
            raise ValueError(f"analysis receipt input hash mismatch: {name}")
    generation_bindings = receipt.get("input_output_bindings")
    if generation_bindings is not None and generation_bindings != manifest.get("outputs"):
        raise ValueError("analysis receipt generation output bindings mismatch")
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict):
        raise ValueError("analysis receipt lacks output hashes")
    for name, expected_hash in outputs.items():
        path = _safe_child(analysis_dir, str(name))
        if not path.is_file() or _hash_file(path) != expected_hash:
            raise ValueError(f"analysis output hash mismatch: {name}")
    return receipt, {"analysis_receipt.json": _binding(receipt_path), **outputs}


def _read_jsonl(path: Path, *, compressed: bool = False) -> list[dict[str, Any]]:
    opener = gzip.open if compressed else open
    rows: list[dict[str, Any]] = []
    with opener(path, "rt", encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row is not an object: {path}:{number}")
            rows.append(value)
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: Iterable[str]) -> None:
    names = list(fieldnames)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in names})


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _bool(value: str | bool | int | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _stratum(row: dict[str, Any]) -> str:
    return str(row.get("index_stratum", "unknown"))


def _failure_stage(status: str, failure: str) -> str:
    if status != "process_infeasible":
        return status
    if failure.startswith("pedder ") and "requests more" in failure:
        return "wild_removal_availability"
    if failure.startswith("oberon ") and "requests more" in failure:
        return "insurance_transfer_availability"
    if failure.startswith("linked history ") and ("held fish" in failure or "holding " in failure):
        return "captive_release_availability"
    return "other_process_failure"


def _process_summary(history_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in history_rows:
        counts[(str(row.get("cell_id")), str(row.get("namespace")), _stratum(row), str(row.get("status", "unknown")), str(row.get("failure") or ""))] += 1
    return [
        {"cell_id": cell, "namespace": namespace, "index_stratum": stratum,
         "status": status, "failure_stage": _failure_stage(status, failure),
         "failure": failure, "histories": count}
        for (cell, namespace, stratum, status, failure), count in sorted(counts.items())
    ]


def _source_class_summary(history_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, int], set[str]] = defaultdict(set)
    history_counts: Counter[tuple[str, str, str, int]] = Counter()
    for row in history_rows:
        if row.get("status") != "complete" or "terminal_alive" not in row:
            continue
        key = (str(row.get("cell_id")), str(row.get("namespace")), _stratum(row), int(bool(row["terminal_alive"])))
        groups[key].add(str(row.get("source_id")))
        history_counts[key] += 1
    result = []
    # Retain absent classes explicitly, including a cell/stratum with no
    # completed process histories. Absence is the central coverage result.
    all_keys = {(str(row.get("cell_id")), str(row.get("namespace")), _stratum(row), label)
                for row in history_rows for label in (0, 1)}
    for key in sorted(all_keys):
        cell, namespace, stratum, class_value = key
        threshold = 16 if namespace == "truth" else 8
        result.append({
            "cell_id": cell,
            "namespace": namespace,
            "index_stratum": stratum,
            "terminal_class": "persist" if class_value else "loss",
            "histories": history_counts[key],
            "distinct_sources": len(groups[key]),
            "minimum_sources": threshold,
            "source_coverage_sufficient": len(groups[key]) >= threshold,
        })
    return result


def _gate_summary(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if row.get("panel") != "base":
            continue
        truth_ok = _bool(row.get("full_truth_coverage_sufficient"))
        bank_ok = _bool(row.get("full_bank_coverage_sufficient"))
        passed = _bool(row.get("full_gate_passed")) and truth_ok and bank_ok
        if passed:
            category = "passed"
        elif not truth_ok and not bank_ok:
            category = "insufficient_truth_and_bank"
        elif not truth_ok:
            category = "insufficient_truth"
        elif not bank_ok:
            category = "insufficient_bank"
        else:
            category = "supported_but_no_gate"
        result.append({
            "cell_id": row.get("cell_id", ""),
            "index_stratum": row.get("index_stratum", "unknown"),
            "profile_id": row.get("profile_id", ""),
            "generator": row.get("generator", ""),
            "realistic_generator": row.get("generator") in ("poisson", "gamma_quality"),
            "category": category,
            "full_gate_passed": passed,
            "truth_coverage_sufficient": truth_ok,
            "bank_coverage_sufficient": bank_ok,
            "truth_sources_loss": _int(row.get("full_truth_sources_loss")),
            "truth_sources_persist": _int(row.get("full_truth_sources_persist")),
            "bank_sources_loss": _int(row.get("full_bank_sources_loss")),
            "bank_sources_persist": _int(row.get("full_bank_sources_persist")),
            "full_balanced_accuracy": row.get("full_balanced_accuracy", ""),
            "full_ci_lower95": row.get("full_ci_lower95", ""),
            "full_sensitivity_loss": row.get("full_sensitivity_loss", ""),
            "full_sensitivity_persist": row.get("full_sensitivity_persist", ""),
            "full_abstentions": _int(row.get("full_abstentions")),
        })
    return result


def _stratum_summary(class_rows: list[dict[str, Any]], gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in class_rows:
        key = (row["cell_id"], row["index_stratum"])
        state = grouped.setdefault(key, {"cell_id": key[0], "index_stratum": key[1],
                                         "complete_histories": 0, "base_panel_rows": 0})
        state[f"{row['namespace']}_{row['terminal_class']}_sources"] = row["distinct_sources"]
        state["complete_histories"] += row["histories"]
    for row in gate_rows:
        grouped[(row["cell_id"], row["index_stratum"])]["base_panel_rows"] += 1
    for state in grouped.values():
        state["truth_source_minimum_met_before_observations"] = min(
            state["truth_loss_sources"], state["truth_persist_sources"]) >= 16
        state["bank_source_minimum_met"] = min(
            state["bank_loss_sources"], state["bank_persist_sources"]) >= 8
        state["no_complete_histories"] = state["complete_histories"] == 0
    return [grouped[key] for key in sorted(grouped)]


def _small_pool_summary(history_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    periods = ("1997_2002", "1997_2012")
    aggregates: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in history_rows:
        if row.get("status") != "complete":
            continue
        diagnostics = row.get("small_pool_diagnostics")
        for period in periods:
            key = (str(row.get("cell_id")), str(row.get("namespace")), _stratum(row), period)
            state = aggregates.setdefault(key, {"histories": 0, "diagnostic_histories": 0, "sources": set(), "breeding_attempts": 0, "small_pool_attempts": 0, "successful_recruitment_events": 0, "small_pool_successful_events": 0})
            state["histories"] += 1
            state["sources"].add(str(row.get("source_id")))
            if not isinstance(diagnostics, dict) or not isinstance(diagnostics.get(period), dict):
                continue
            values = diagnostics[period]
            state["diagnostic_histories"] += 1
            for field in ("breeding_attempts", "small_pool_attempts", "successful_recruitment_events", "small_pool_successful_events"):
                state[field] += _int(values.get(field))
    result = []
    for (cell, namespace, stratum, period), state in sorted(aggregates.items()):
        attempts = state["breeding_attempts"]
        successes = state["successful_recruitment_events"]
        result.append({
            "cell_id": cell,
            "namespace": namespace,
            "index_stratum": stratum,
            "period": period,
            "histories": state["histories"],
            "diagnostic_histories": state["diagnostic_histories"],
            "distinct_sources": len(state["sources"]),
            "breeding_attempts": attempts,
            "small_pool_attempts": state["small_pool_attempts"],
            "successful_recruitment_events": successes,
            "small_pool_successful_events": state["small_pool_successful_events"],
            "fraction_small_attempts": state["small_pool_attempts"] / attempts if attempts else "",
            "fraction_small_successful_events": state["small_pool_successful_events"] / successes if successes else "",
        })
    return result


def summarize(input_dir: Path, analysis_dir: Path, output_dir: Path) -> dict[str, Any]:
    input_dir, analysis_dir, output_dir = Path(input_dir), Path(analysis_dir), Path(output_dir)
    if output_dir.exists():
        raise ValueError(f"summary output directory already exists: {output_dir}")
    if not input_dir.is_dir() or not analysis_dir.is_dir():
        raise ValueError("generation input and analysis directories must exist")
    started = _utc_now()
    own_source = _binding(ROOT / SCRIPT_RELATIVE)
    manifest, generation_bindings = _verify_generation(input_dir)
    analysis_receipt, analysis_bindings = _verify_analysis(input_dir, analysis_dir, manifest)
    history_rows = _read_jsonl(input_dir / "histories.jsonl.gz", compressed=True)
    process_rows = _process_summary(history_rows)
    class_rows = _source_class_summary(history_rows)
    gate_rows = _gate_summary(_read_csv(analysis_dir / "gate_by_profile.csv"))
    stratum_rows = _stratum_summary(class_rows, gate_rows)
    pool_rows = _small_pool_summary(history_rows)
    coherence_rows = [row for row in _read_csv(analysis_dir / "coherence_by_stratum.csv")
                      if row.get("panel") == "base"]
    coherence_totals: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for row in coherence_rows:
        total = coherence_totals[(row["generator"], row["profile_id"])]
        total[0] += _int(row["histories"])
        total[1] += _int(row["coherent_histories"])
    coherence_rates = [{"generator": key[0], "profile_id": key[1],
                        "histories": counts[0], "coherent_histories": counts[1],
                        "rate": counts[1] / counts[0] if counts[0] else ""}
                       for key, counts in sorted(coherence_totals.items())]
    support_rows = _read_csv(input_dir / "source_support.csv")
    output_dir.mkdir(parents=False, exist_ok=False)
    _write_csv(output_dir / "process_summary.csv", process_rows, ("cell_id", "namespace", "index_stratum", "status", "failure_stage", "failure", "histories"))
    _write_csv(output_dir / "source_class_coverage.csv", class_rows, ("cell_id", "namespace", "index_stratum", "terminal_class", "histories", "distinct_sources", "minimum_sources", "source_coverage_sufficient"))
    _write_csv(output_dir / "stratum_coverage.csv", stratum_rows, ("cell_id", "index_stratum", "complete_histories", "truth_loss_sources", "truth_persist_sources", "bank_loss_sources", "bank_persist_sources", "truth_source_minimum_met_before_observations", "bank_source_minimum_met", "base_panel_rows", "no_complete_histories"))
    _write_csv(output_dir / "base_gate_summary.csv", gate_rows, ("cell_id", "index_stratum", "profile_id", "generator", "realistic_generator", "category", "full_gate_passed", "truth_coverage_sufficient", "bank_coverage_sufficient", "truth_sources_loss", "truth_sources_persist", "bank_sources_loss", "bank_sources_persist", "full_balanced_accuracy", "full_ci_lower95", "full_sensitivity_loss", "full_sensitivity_persist", "full_abstentions"))
    _write_csv(output_dir / "small_sex_pool_summary.csv", pool_rows, ("cell_id", "namespace", "index_stratum", "period", "histories", "diagnostic_histories", "distinct_sources", "breeding_attempts", "small_pool_attempts", "successful_recruitment_events", "small_pool_successful_events", "fraction_small_attempts", "fraction_small_successful_events"))
    _write_csv(output_dir / "coherence_base.csv", coherence_rows, coherence_rows[0].keys() if coherence_rows else ())
    _write_csv(output_dir / "coherence_profile_summary.csv", coherence_rates,
               ("generator", "profile_id", "histories", "coherent_histories", "rate"))
    _write_csv(output_dir / "source_support.csv", support_rows, support_rows[0].keys() if support_rows else ())
    summary = {
        "status": "complete",
        "generation_status": manifest.get("status"),
        "analysis_status": analysis_receipt.get("status"),
        "generation_full_design": bool(manifest.get("full_design", False)),
        "process_rows": len(process_rows),
        "source_class_rows": len(class_rows),
        "stratum_rows": len(stratum_rows),
        "strata_without_complete_histories": sum(row["no_complete_histories"] for row in stratum_rows),
        "base_gate_rows": len(gate_rows),
        "base_gate_categories": dict(sorted(Counter(str(row["category"]) for row in gate_rows).items())),
        "small_sex_pool_rows": len(pool_rows),
        "interpretation": "Accounting summaries remain at cell and index-stratum resolution. They do not pool cells or strata, treat repeated nuisance sources as independent evidence, justify GO, or compute empirical posterior quantities.",
    }
    _write_json(output_dir / "summary.json", summary)
    output_bindings = {str(path.relative_to(output_dir)): _binding(path) for path in sorted(output_dir.rglob("*")) if path.is_file()}
    if _binding(ROOT / SCRIPT_RELATIVE) != own_source:
        raise ValueError("summarizer source changed during execution")
    receipt = {
        "status": "complete",
        "started_at": started,
        "completed_at": _utc_now(),
        "generation_input": str(input_dir),
        "analysis_input": str(analysis_dir),
        "generation_bindings": generation_bindings,
        "analysis_bindings": analysis_bindings,
        "own_source": {"path": SCRIPT_RELATIVE, **own_source},
        "outputs": output_bindings,
    }
    _write_json(output_dir / "summary_receipt.json", receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    summarize(args.input_dir, args.analysis_dir, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
