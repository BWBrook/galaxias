#!/usr/bin/env python3
"""Account for a completed age-historical-refocus generation and analysis.

This is a receipt-bound summarizer.  It reads compact histories and analysis
tables, verifies the generation and analysis receipts, and writes small CSV
views.  It does not import or call demographic, observation, or scoring code.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_STATUSES = {
    "QUALIFICATION_SMOKE_ONLY",
    "CONDITIONAL_GO_REQUIRES_QUALIFIED_COLUMNS",
    "STOP_BEFORE_HISTORICAL_COMPARISON",
}
CSV_ENCODING = "utf-8"
REQUIRED_GENERATION_OUTPUTS = {
    "full_histories.jsonl.gz", "histories.jsonl.gz", "source_banks.jsonl", "source_support.csv",
}
REQUIRED_GENERATION_CONTENT = {"full_histories.jsonl", "histories.jsonl"}
REQUIRED_ANALYSIS_OUTPUTS = {
    "base_gate_metrics.csv", "gate_metrics.csv", "weighted_composition.csv",
    "stratum_summary.csv", "reproducibility.json", "score_controls.json",
}
REQUIRED_ANALYSIS_SOURCES = {
    "docs/age_historical_refocus_protocol.md",
    "scripts/analyze_age_historical_refocus.py",
    "scripts/analyze_age_recovery.py",
    "src/galaxias_model/age_historical_refocus.py",
    "src/galaxias_model/age_recovery_observation.py",
    "src/galaxias_model/age_recovery_scores.py",
    "src/galaxias_model/age_refocus_scores.py",
}


def _binding(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def _verify_binding(path: Path, expected: dict[str, Any], label: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing bound file: {label}: {path}")
    actual = _binding(path)
    if actual != {"bytes": int(expected["bytes"]), "sha256": str(expected["sha256"])}:
        raise ValueError(f"binding mismatch for {label}: expected {expected}, got {actual}")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding=CSV_ENCODING) as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _read_jsonl(path: Path, compressed: bool = False) -> list[dict[str, Any]]:
    opener = gzip.open if compressed else open
    rows = []
    with opener(path, "rt", encoding=CSV_ENCODING) as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"JSONL row is not an object: {path}:{line_number}")
                rows.append(value)
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding=CSV_ENCODING) as handle:
        return list(csv.DictReader(handle))


def _iter_csv(path: Path):
    with path.open(newline="", encoding=CSV_ENCODING) as handle:
        yield from csv.DictReader(handle)


def _decompressed_sha256(path: Path) -> tuple[int, str]:
    size = 0
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    return size, digest.hexdigest()


def _verify_generation(input_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_path = input_dir / "run_manifest.json"
    manifest = _read_json(manifest_path)
    if manifest.get("status") != "complete":
        raise ValueError(f"generation receipt is not complete: {manifest.get('status')!r}")
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict) or not REQUIRED_GENERATION_OUTPUTS.issubset(outputs):
        raise ValueError(f"generation receipt lacks required output bindings: {REQUIRED_GENERATION_OUTPUTS - set(outputs or {})}")
    for name, expected in outputs.items():
        _verify_binding(input_dir / name, expected, f"generation output {name}")
    content_hashes = manifest.get("content_sha256")
    if not isinstance(content_hashes, dict) or not REQUIRED_GENERATION_CONTENT.issubset(content_hashes):
        raise ValueError(f"generation receipt lacks required decompressed content hashes: {REQUIRED_GENERATION_CONTENT - set(content_hashes or {})}")
    source_bindings = manifest.get("source_bindings")
    if not isinstance(source_bindings, dict) or not source_bindings:
        raise ValueError("generation receipt has no source bindings")
    for name, expected in source_bindings.items():
        _verify_binding(ROOT / name, expected, f"generation source {name}")
    for content_name, expected_hash in content_hashes.items():
        compressed_name = f"{content_name}.gz"
        path = input_dir / compressed_name
        if not path.is_file():
            raise ValueError(f"missing compressed content for {content_name}: {path}")
        _, actual_hash = _decompressed_sha256(path)
        if actual_hash != expected_hash:
            raise ValueError(f"decompressed content hash mismatch for {content_name}")
    sources = _read_jsonl(input_dir / "source_banks.jsonl")
    histories = _read_jsonl(input_dir / "histories.jsonl.gz", compressed=True)
    expected_source_rows = int(manifest.get("source_rows", -1))
    expected_history_rows = expected_source_rows * int(manifest.get("replicates_per_source", -1))
    if expected_source_rows < 0 or len(sources) != expected_source_rows:
        raise ValueError(f"source row count mismatch: receipt {expected_source_rows}, observed {len(sources)}")
    if expected_history_rows < 0 or len(histories) != expected_history_rows:
        raise ValueError(f"history row count mismatch: receipt {expected_history_rows}, observed {len(histories)}")
    observed_status = Counter(str(row.get("status", "")) for row in histories)
    expected_status = Counter({str(key): int(value) for key, value in manifest.get("history_status_counts", {}).items()})
    if observed_status != expected_status:
        raise ValueError(f"history status mismatch: receipt {dict(expected_status)}, observed {dict(observed_status)}")
    return manifest, sources, histories


def _verify_analysis(analysis_dir: Path, generation_manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    receipt_path = analysis_dir / "analysis_receipt.json"
    receipt = _read_json(receipt_path)
    if receipt.get("status") not in ANALYSIS_STATUSES:
        raise ValueError(f"unknown analysis status: {receipt.get('status')!r}")
    expected_generation = _binding(generation_manifest_path)
    if receipt.get("generation_manifest") != expected_generation:
        raise ValueError("analysis receipt does not bind the supplied generation manifest")
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict) or not REQUIRED_ANALYSIS_OUTPUTS.issubset(outputs):
        raise ValueError(f"analysis receipt lacks required output bindings: {REQUIRED_ANALYSIS_OUTPUTS - set(outputs or {})}")
    source_bindings = receipt.get("source_bindings")
    if not isinstance(source_bindings, dict) or not REQUIRED_ANALYSIS_SOURCES.issubset(source_bindings):
        raise ValueError(f"analysis receipt lacks required source bindings: {REQUIRED_ANALYSIS_SOURCES - set(source_bindings or {})}")
    for name, expected in source_bindings.items():
        _verify_binding(ROOT / name, expected, f"analysis source {name}")
    for name, expected in outputs.items():
        _verify_binding(analysis_dir / name, expected, f"analysis output {name}")
    base = _read_csv(analysis_dir / "base_gate_metrics.csv")
    gate_count = 0
    gate_base = []
    primary = []
    status_counts = Counter()
    for row in _iter_csv(analysis_dir / "gate_metrics.csv"):
        gate_count += 1
        if row.get("panel") == "base":
            gate_base.append(row)
        if row.get("panel") == "base" and row.get("endpoint") == "terminal_alive":
            primary.append(row)
            status_counts[row.get("status", "")] += 1
    if gate_count != int(receipt.get("metric_rows", -1)):
        raise ValueError(f"analysis metric row count mismatch: receipt {receipt.get('metric_rows')}, observed {gate_count}")
    canonical = lambda row: json.dumps(row, sort_keys=True, separators=(",", ":"))
    if sorted(map(canonical, gate_base)) != sorted(map(canonical, base)):
        raise ValueError("base_gate_metrics.csv does not equal the panel=base rows in gate_metrics.csv")
    if len(_read_csv(analysis_dir / "weighted_composition.csv")) != int(receipt.get("composition_rows", -1)):
        raise ValueError("weighted composition row count does not match analysis receipt")
    assessed = sum(_as_bool(row.get("assessed")) for row in primary)
    passed = sum(_as_bool(row.get("gate_passed")) and row.get("generator") in {"poisson", "gamma_quality"} for row in primary)
    if assessed != int(receipt.get("primary_base_assessed", -1)):
        raise ValueError(f"primary base assessed mismatch: receipt {receipt.get('primary_base_assessed')}, observed {assessed}")
    if passed != int(receipt.get("primary_base_passes", -1)):
        raise ValueError(f"primary base pass mismatch: receipt {receipt.get('primary_base_passes')}, observed {passed}")
    if dict(status_counts) != {str(k): int(v) for k, v in receipt.get("primary_base_status_counts", {}).items()}:
        raise ValueError("primary base status tally does not match analysis receipt")
    return receipt, base


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _finite_range(rows: list[dict[str, Any]], field: str, *, only_assessed: bool = False) -> tuple[Any, Any]:
    values = []
    for row in rows:
        if only_assessed and str(row.get("assessed", "")).lower() != "true":
            continue
        value = _float(row.get(field))
        if math.isfinite(value):
            values.append(value)
    return (min(values), max(values)) if values else ("", "")


def _rref_lookup(sources: list[dict[str, Any]], histories: list[dict[str, Any]]) -> dict[tuple[str, str], tuple[float, float]]:
    values: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in [*sources, *histories]:
        key = (str(row.get("cell_id", "")), str(row.get("index_stratum", "")))
        value = _float(row.get("refuge_index"))
        if math.isfinite(value):
            values[key].append(value)
    return {key: (min(items), max(items)) for key, items in values.items() if items}


def _add_rref(row: dict[str, Any], lookup: dict[tuple[str, str], tuple[float, float]]) -> dict[str, Any]:
    result = dict(row)
    minimum, maximum = lookup.get((str(row.get("cell_id", "")), str(row.get("index_stratum", ""))), ("", ""))
    result["refuge_index_min"] = minimum
    result["refuge_index_max"] = maximum
    result["refuge_index_stratum"] = row.get("index_stratum", "")
    return result


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding=CSV_ENCODING) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _sorted(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: tuple(str(row.get(field, "")) for field in fields))


def _bool_count(rows: list[dict[str, Any]], field: str) -> int:
    return sum(_as_bool(row.get(field, "")) for row in rows)


def _base_primary_rows(base: list[dict[str, str]], lookup: dict[tuple[str, str], tuple[float, float]]) -> list[dict[str, Any]]:
    rows = [_add_rref(row, lookup) for row in base if row.get("endpoint") == "terminal_alive"]
    return _sorted(rows, ("cell_id", "index_stratum", "profile_id", "generator", "endpoint"))


def _support_summary(base: list[dict[str, str]], lookup: dict[tuple[str, str], tuple[float, float]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in base:
        key = tuple(row.get(field, "") for field in ("cell_id", "index_stratum", "profile_id", "generator", "endpoint"))
        groups[key].append(row)
    result = []
    for key, rows in groups.items():
        cell_id, index_stratum, profile_id, generator, endpoint = key
        truth_false = _finite_range(rows, "truth_source_ess_false")
        truth_true = _finite_range(rows, "truth_source_ess_true")
        bank_false = _finite_range(rows, "bank_source_ess_false")
        bank_true = _finite_range(rows, "bank_source_ess_true")
        truth_assessed_false = _finite_range(rows, "truth_source_ess_false", only_assessed=True)
        truth_assessed_true = _finite_range(rows, "truth_source_ess_true", only_assessed=True)
        bank_assessed_false = _finite_range(rows, "bank_source_ess_false", only_assessed=True)
        bank_assessed_true = _finite_range(rows, "bank_source_ess_true", only_assessed=True)
        item = {
            "cell_id": cell_id, "index_stratum": index_stratum, "refuge_index_stratum": index_stratum,
            "profile_id": profile_id, "generator": generator, "endpoint": endpoint,
            "rows": len(rows), "assessed_count": sum(_as_bool(r.get("assessed", "")) for r in rows),
            "passed_count": _bool_count(rows, "gate_passed"),
            "status_counts": ";".join(f"{name}:{count}" for name, count in sorted(Counter(r.get("status", "") for r in rows).items())),
            "truth_source_ess_false_min": truth_false[0], "truth_source_ess_false_max": truth_false[1],
            "truth_source_ess_true_min": truth_true[0], "truth_source_ess_true_max": truth_true[1],
            "bank_source_ess_false_min": bank_false[0], "bank_source_ess_false_max": bank_false[1],
            "bank_source_ess_true_min": bank_true[0], "bank_source_ess_true_max": bank_true[1],
            "assessed_truth_source_ess_false_min": truth_assessed_false[0], "assessed_truth_source_ess_false_max": truth_assessed_false[1],
            "assessed_truth_source_ess_true_min": truth_assessed_true[0], "assessed_truth_source_ess_true_max": truth_assessed_true[1],
            "assessed_bank_source_ess_false_min": bank_assessed_false[0], "assessed_bank_source_ess_false_max": bank_assessed_false[1],
            "assessed_bank_source_ess_true_min": bank_assessed_true[0], "assessed_bank_source_ess_true_max": bank_assessed_true[1],
        }
        minimum, maximum = lookup.get((cell_id, index_stratum), ("", ""))
        item["refuge_index_min"], item["refuge_index_max"] = minimum, maximum
        result.append(item)
    return _sorted(result, ("cell_id", "index_stratum", "profile_id", "generator", "endpoint"))


def _composition_views(analysis_dir: Path, lookup: dict[tuple[str, str], tuple[float, float]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = _read_csv(analysis_dir / "weighted_composition.csv")
    baseline = []
    campaign = []
    for row in rows:
        target = row.get("target", "")
        if target in {"g_process_feasible", "early_lake_base"}:
            item = _add_rref(row, lookup)
            item["composition_kind"] = "process_only" if target == "g_process_feasible" else "primary_E"
            item["profile_id_selected"] = "process_only" if target == "g_process_feasible" else "base"
            item["profile_selection"] = "explicit_target"
            item["scenario"] = target
            baseline.append(item)
        elif target == "early_lake_base_plus_campaign_sensitivity":
            item = _add_rref(row, lookup)
            item["profile_id_selected"] = ""
            item["profile_selection"] = "none_campaign_sensitivity_only"
            item["scenario"] = target
            campaign.append(item)
    baseline = _sorted(baseline, ("cell_id", "index_stratum", "namespace", "composition_kind"))
    campaign = _sorted(campaign, ("cell_id", "index_stratum", "namespace", "campaign", "law", "q_electro", "q_larvae", "timing"))
    return baseline, campaign


def _source_independence(sources: list[dict[str, Any]], histories: list[dict[str, Any]], lookup: dict[tuple[str, str], tuple[float, float]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(lambda: {"sources": [], "histories": []})
    for row in sources:
        role = str(row.get("role", row.get("namespace", "")))
        groups[(str(row.get("cell_id", "")), str(row.get("index_stratum", "")), role)]["sources"].append(row)
    for row in histories:
        role = str(row.get("namespace", ""))
        groups[(str(row.get("cell_id", "")), str(row.get("index_stratum", "")), role)]["histories"].append(row)
    result = []
    for (cell_id, index_stratum, role), group in groups.items():
        source_rows, history_rows = group["sources"], group["histories"]
        source_ids = {str(row.get("source_id", "")) for row in source_rows}
        feasible_source_ids = {str(row.get("source_id", "")) for row in source_rows if row.get("feasible") is True}
        statuses = defaultdict(set)
        for row in history_rows:
            statuses[str(row.get("status", ""))].add(str(row.get("source_id", "")))
        complete = [row for row in history_rows if row.get("status") == "complete"]
        failed = [row for row in history_rows if row.get("status") != "complete"]
        complete_ids = {str(row.get("source_id", "")) for row in complete}
        failed_ids = {str(row.get("source_id", "")) for row in failed}
        alive_ids = {str(row.get("source_id", "")) for row in complete if row.get("terminal_alive") is True}
        loss_ids = {str(row.get("source_id", "")) for row in complete if row.get("terminal_alive") is False}
        minimum, maximum = lookup.get((cell_id, index_stratum), ("", ""))
        result.append({
            "cell_id": cell_id, "index_stratum": index_stratum, "refuge_index_stratum": index_stratum,
            "role": role, "refuge_index_min": minimum, "refuge_index_max": maximum,
            "source_rows": len(source_rows), "distinct_source_ids": len(source_ids),
            "feasible_source_ids": len(feasible_source_ids), "infeasible_source_ids": len(source_ids - feasible_source_ids),
            "history_rows": len(history_rows), "distinct_history_source_ids": len({str(r.get('source_id', '')) for r in history_rows}),
            "complete_history_rows": len(complete), "complete_source_ids": len(complete_ids),
            "failed_history_rows": len(failed), "failed_source_ids": len(failed_ids),
            "complete_alive_source_ids": len(alive_ids), "complete_loss_source_ids": len(loss_ids),
            "mixed_status_source_ids": len(set.intersection(complete_ids, failed_ids)),
            "status_source_counts": ";".join(f"{name}:{len(values)}" for name, values in sorted(statuses.items())),
            "independence_unit": "source_id nuisance cluster; process replicates remain within source",
        })
    return _sorted(result, ("cell_id", "index_stratum", "role"))


def _failure_rows(histories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in histories:
        status = str(row.get("status", ""))
        failure = str(row.get("failure", "") or "")
        if status == "complete":
            stage, event = "complete", "none"
        elif status == "algebraically_infeasible":
            stage, event = "algebraic", failure or "unspecified"
        elif status == "process_infeasible":
            stage, event = "process", failure or "unspecified"
        else:
            stage, event = "other", failure or "unspecified"
        key = (str(row.get("cell_id", "")), str(row.get("index_stratum", "")), str(row.get("namespace", "")), stage, event)
        groups[key].append(row)
    result = []
    for (cell_id, index_stratum, role, stage, event), rows in groups.items():
        result.append({
            "cell_id": cell_id, "index_stratum": index_stratum, "refuge_index_stratum": index_stratum,
            "role": role, "stage": stage, "event": event, "histories": len(rows),
            "distinct_source_ids": len({str(row.get("source_id", "")) for row in rows}),
            "status_counts": ";".join(f"{name}:{count}" for name, count in sorted(Counter(str(row.get("status", "")) for row in rows).items())),
        })
    return _sorted(result, ("cell_id", "index_stratum", "role", "stage", "event"))


def _output_bindings(output_dir: Path, names: list[str]) -> dict[str, dict[str, Any]]:
    return {name: _binding(output_dir / name) for name in names}


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_dir = args.input_dir.resolve()
    analysis_dir = args.analysis_dir.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"output directory is non-empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    generation_manifest_path = input_dir / "run_manifest.json"
    generation, sources, histories = _verify_generation(input_dir)
    analysis, base_rows = _verify_analysis(analysis_dir, generation_manifest_path)
    lookup = _rref_lookup(sources, histories)
    primary = _base_primary_rows(base_rows, lookup)
    support = _support_summary(base_rows, lookup)
    baseline, campaign = _composition_views(analysis_dir, lookup)
    source_counts = _source_independence(sources, histories, lookup)
    failures = _failure_rows(histories)

    _write_csv(output_dir / "base_primary_gate.csv", primary, list(primary[0].keys()) if primary else ["cell_id"])
    _write_csv(output_dir / "base_endpoint_support_summary.csv", support, [
        "cell_id", "index_stratum", "refuge_index_stratum", "refuge_index_min", "refuge_index_max", "profile_id", "generator", "endpoint", "rows", "assessed_count", "passed_count", "status_counts", "truth_source_ess_false_min", "truth_source_ess_false_max", "truth_source_ess_true_min", "truth_source_ess_true_max", "bank_source_ess_false_min", "bank_source_ess_false_max", "bank_source_ess_true_min", "bank_source_ess_true_max", "assessed_truth_source_ess_false_min", "assessed_truth_source_ess_false_max", "assessed_truth_source_ess_true_min", "assessed_truth_source_ess_true_max", "assessed_bank_source_ess_false_min", "assessed_bank_source_ess_false_max", "assessed_bank_source_ess_true_min", "assessed_bank_source_ess_true_max",
    ])
    _write_csv(output_dir / "baseline_composition.csv", baseline, list(baseline[0].keys()) if baseline else ["cell_id"])
    _write_csv(output_dir / "campaign_composition_summary.csv", campaign, list(campaign[0].keys()) if campaign else ["cell_id"])
    _write_csv(output_dir / "source_independence.csv", source_counts, list(source_counts[0].keys()) if source_counts else ["cell_id"])
    _write_csv(output_dir / "failure_summary.csv", failures, list(failures[0].keys()) if failures else ["cell_id"])

    score_controls = _read_json(analysis_dir / "score_controls.json")
    observed = {
        "generation_status": generation.get("status"),
        "generation_mode": generation.get("mode"),
        "generation_history_status_counts": generation.get("history_status_counts", {}),
        "analysis_status": analysis.get("status"),
        "analysis_metric_rows": analysis.get("metric_rows"),
        "analysis_composition_rows": analysis.get("composition_rows"),
        "analysis_primary_base_assessed": analysis.get("primary_base_assessed"),
        "analysis_primary_base_passes": analysis.get("primary_base_passes"),
        "analysis_endpoint_status_counts": analysis.get("all_endpoint_status_counts", {}),
        "score_controls_passed": bool(score_controls.get("all_passed")),
        "score_control_biology_calls": score_controls.get("biology_calls"),
        "source_rows": len(sources),
        "history_rows": len(histories),
        "complete_history_rows": sum(row.get("status") == "complete" for row in histories),
        "failure_history_rows": sum(row.get("status") != "complete" for row in histories),
        "base_primary_gate_rows": len(primary),
        "baseline_composition_rows": len(baseline),
        "campaign_composition_rows": len(campaign),
    }
    output_names = [
        "base_primary_gate.csv", "base_endpoint_support_summary.csv", "baseline_composition.csv",
        "campaign_composition_summary.csv", "source_independence.csv", "failure_summary.csv",
    ]
    audit = {
        "status": "complete",
        "qualification": "smoke_only" if generation.get("mode") == "smoke" else "receipt_bound_accounting_only",
        "diagnostic_qualification": "Accounting of observed receipt dispositions only; no prevalence, biological verdict, historical fit, posterior, or rescue-effect inference.",
        "observed_dispositions": observed,
        "input_receipts": {
            "generation_manifest": {
                "path": _relative(generation_manifest_path), "binding": _binding(generation_manifest_path),
                "declared_outputs": generation.get("outputs", {}),
                "declared_content_sha256": generation.get("content_sha256", {}),
                "declared_source_bindings": generation.get("source_bindings", {}),
            },
            "analysis_receipt": {
                "path": _relative(analysis_dir / "analysis_receipt.json"), "binding": _binding(analysis_dir / "analysis_receipt.json"),
                "declared_outputs": analysis.get("outputs", {}),
                "declared_source_bindings": analysis.get("source_bindings", {}),
            },
        },
        "verification": {
            "generation_outputs_verified": True,
            "generation_decompressed_content_hashes_verified": True,
            "generation_source_bindings_verified": True,
            "analysis_outputs_verified": True,
            "analysis_source_bindings_verified": True,
            "analysis_generation_manifest_binding_verified": True,
            "biological_calls_made_by_summarizer": 0,
        },
        "source_independence": "Counts use distinct source_id nuisance clusters; no pooling across cells or refuge-index strata and no claim of independent biological parameter sets.",
        "campaign_scope": "Campaign rows retain explicit campaign, law, q_electro, q_larvae and timing assumptions; no profile is selected for campaign sensitivity.",
        "script_binding": {"path": _relative(Path(__file__)), "binding": _binding(Path(__file__))},
        "output_bindings_excluding_audit": _output_bindings(output_dir, output_names),
    }
    audit_path = output_dir / "audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding=CSV_ENCODING)
    return {"status": "complete", "qualification": audit["qualification"], "output_dir": _relative(output_dir), "observed": observed}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
