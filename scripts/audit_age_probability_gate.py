#!/usr/bin/env python3
"""Independent read-only audit of the frozen age probability gate.

The numerical core in this file deliberately does not import the production
probability-observation or probability-score modules.  It reconstructs the
natural-prevalence forecast from the saved compact histories and a small,
deterministically selected set of saved synthetic observations.
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
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GENERATION = ROOT / "outputs/remote/age_probability_gate_20261003/gate"
DEFAULT_ANALYSIS = ROOT / "outputs/remote/age_probability_gate_20261003/analysis"
DEFAULT_OUTPUT = ROOT / "data/age_probability_gate_20261003/provenance/independent_result_audit.json"

EXPECTED_SOURCE_ROWS = 8_192
EXPECTED_INDEPENDENT_SOURCE_IDS = 2_048
EXPECTED_HISTORY_ROWS = 49_152
EXPECTED_NOMINAL_SITE_HISTORIES = 147_456
EXPECTED_METRIC_ROWS = 1_152
EXPECTED_PRIMARY_ROWS = 576
EXPECTED_REPLICATES = 6
EXPECTED_PROFILES = 36
GENERATORS = ("poisson", "gamma_binary_quality")
QUALIFIED = {
    "CALIBRATED_AND_INFORMATIVE",
    "CALIBRATED_BUT_NO_INCREMENTAL_INFORMATION",
}
INSURANCE_GROUPS = (2, 3, 4, 4, 5, 6, 6, 7, 8)


def sha256_file(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return {"bytes": size, "sha256": digest.hexdigest()}


def sha256_uncompressed_gzip(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    rows = 0
    with gzip.open(path, "rb") as stream:
        for line in stream:
            digest.update(line)
            rows += 1
    return digest.hexdigest(), rows


def load_json(path: Path) -> Any:
    with path.open() as stream:
        return json.load(stream)


def jsonl(path: Path, *, compressed: bool = False) -> Iterable[dict[str, Any]]:
    opener = gzip.open if compressed else open
    with opener(path, "rt") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON at {path}:{line_number}") from exc


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"not a boolean: {value!r}")


def parse_float(value: Any) -> float:
    if value is None or value == "":
        return math.nan
    return float(value)


def close(a: float, b: float, *, atol: float = 1e-11, rtol: float = 1e-11) -> bool:
    if math.isnan(a) and math.isnan(b):
        return True
    return math.isclose(a, b, abs_tol=atol, rel_tol=rtol)


def finite_or_none(value: float) -> float | None:
    return value if math.isfinite(value) else None


def value_range(values: Iterable[float]) -> list[float]:
    collected = list(values)
    return [min(collected), max(collected)] if collected else []


class Audit:
    def __init__(self) -> None:
        self.checks: dict[str, bool] = {}
        self.failures: list[str] = []

    def require(self, name: str, condition: bool, detail: str = "") -> None:
        passed = bool(condition)
        self.checks[name] = self.checks.get(name, True) and passed
        if not passed:
            self.failures.append(f"{name}: {detail}" if detail else name)


def verify_binding_map(
    audit: Audit, name: str, bindings: dict[str, dict[str, Any]], report: dict[str, Any]
) -> None:
    mismatches = []
    for declared, expected in bindings.items():
        path = ROOT / declared
        observed = sha256_file(path) if path.is_file() else None
        if observed != expected:
            mismatches.append({"path": declared, "expected": expected, "observed": observed})
        elif observed is not None:
            report[declared] = observed
    audit.require(name, not mismatches, json.dumps(mismatches[:5], sort_keys=True))


def stable_source_record(source: dict[str, Any]) -> str:
    value = {k: v for k, v in source.items() if k not in {"cell", "cell_id"}}
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def reduced_exposures(features: dict[str, Any]) -> tuple[float, float, float, tuple[float, ...]]:
    def age1(value: Any) -> float:
        return float(value[1])

    def adult(key: str) -> float:
        return float(features[key][2])

    def juvenile(key: str) -> float:
        value = features[key]
        return float(value[0] + value[1])

    early = features["creek_early"]
    late = features["creek_late"]
    x_early = 43.0 * sum(age1(value) for value in early) / len(early)
    x_february = 2.0 * age1(features["creek_feb"])
    late_mean = sum(age1(value) for value in late) / len(late)
    oberon_early = features["ob_early"]
    strath_early = features["sg_early"]
    insurance = (
        sum(sum(map(float, value)) for value in oberon_early) / len(oberon_early),
        adult("ob96"),
        adult("ob97"),
        juvenile("ob97"),
        sum(map(float, features["ob99"])),
        adult("ob12"),
        juvenile("ob12"),
        sum(float(value[0] + value[1]) for value in strath_early) / len(strath_early),
        juvenile("sg08"),
    )
    if x_early + x_february <= 0 or min(insurance, default=0.0) < 0 or late_mean < 0:
        raise ValueError("invalid independently reconstructed exposure")
    return x_early, x_february, late_mean, insurance


def nb69_log_pmf(k: int, x_early: float, x_late: float) -> float:
    if k < 0:
        raise ValueError("negative late count")
    if x_early <= 0 or x_late < 0:
        raise ValueError("invalid creek exposure")
    if x_late == 0:
        return 0.0 if k == 0 else -math.inf
    total = x_early + x_late
    return (
        math.lgamma(69 + k)
        - math.lgamma(69)
        - math.lgamma(k + 1)
        + 69 * math.log(x_early / total)
        + k * math.log(x_late / total)
    )


def log_positive(value: float) -> float:
    return math.log(value) if value > 0 else -math.inf


def gamma_single_log_probability(rate: float, observed: bool) -> float:
    return log_positive(rate) - math.log1p(rate) if observed else -math.log1p(rate)


def gamma_pair_log_probability(a: float, b: float, first: bool, second: bool) -> float:
    if not first and not second:
        return -math.log1p(a + b)
    if first and not second:
        return log_positive(a) - math.log1p(b) - math.log1p(a + b)
    if not first and second:
        return log_positive(b) - math.log1p(a) - math.log1p(a + b)
    return (
        log_positive(a)
        + log_positive(b)
        + math.log(2.0 + a + b)
        - math.log1p(a)
        - math.log1p(b)
        - math.log1p(a + b)
    )


def insurance_log_probability(
    exposures: tuple[float, ...], observed: tuple[bool, ...], q: float, generator: str
) -> float:
    if len(exposures) != 9 or len(observed) != 9 or q < 0:
        raise ValueError("invalid insurance inputs")
    rates = tuple(q * value for value in exposures)
    if generator == "poisson":
        total = 0.0
        for rate, seen in zip(rates, observed):
            if seen:
                total += math.log(-math.expm1(-rate)) if rate > 0 else -math.inf
            else:
                total -= rate
        return total
    if generator != "gamma_binary_quality":
        raise ValueError(f"unknown generator: {generator}")
    groups: dict[int, list[int]] = defaultdict(list)
    for index, group in enumerate(INSURANCE_GROUPS):
        groups[group].append(index)
    total = 0.0
    for columns in groups.values():
        if len(columns) == 1:
            index = columns[0]
            total += gamma_single_log_probability(rates[index], observed[index])
        elif len(columns) == 2:
            first, second = columns
            total += gamma_pair_log_probability(
                rates[first], rates[second], observed[first], observed[second]
            )
        else:
            raise ValueError("unexpected visit grouping")
    return total


def source_averaged_probability(
    histories: list[dict[str, Any]], planned_sources: set[str], *, late_count: int | None = None,
    insurance: tuple[bool, ...] | None = None, k_value: float = 0.0,
    rho: float = 0.0, q: float = 0.0, generator: str = "poisson",
) -> tuple[float, int]:
    log_values: list[tuple[str, float, bool]] = []
    for row in histories:
        log_value = float(row["log_weight"])
        if late_count is not None:
            x_early = row["x_early"] + row["x_february"]
            x_late = k_value * rho * row["late_mean"]
            log_value += nb69_log_pmf(late_count, x_early, x_late)
            assert insurance is not None
            log_value += insurance_log_probability(row["insurance"], insurance, q, generator)
        log_values.append((row["source_id"], log_value, bool(row["loss"])))
    finite = [value for _, value, _ in log_values if math.isfinite(value)]
    if not finite:
        return math.nan, len(planned_sources)
    scale = max(finite)
    source_denominator = {source_id: 0.0 for source_id in planned_sources}
    source_numerator = {source_id: 0.0 for source_id in planned_sources}
    for source_id, value, loss in log_values:
        contribution = math.exp(value - scale) / EXPECTED_REPLICATES if math.isfinite(value) else 0.0
        source_denominator[source_id] += contribution
        source_numerator[source_id] += contribution * loss
    denominator = sum(source_denominator.values())
    numerator = sum(source_numerator.values())
    probability = numerator / denominator if denominator > 0 else math.nan
    zero_sources = sum(value == 0.0 for value in source_denominator.values())
    return probability, zero_sources


def select_sample(heap: list[tuple[int, dict[str, Any]]], row: dict[str, Any], size: int) -> None:
    fields = (
        row["cell_id"], row["index_stratum"], row["profile_id"], row["generator"],
        row["source_id"], int(row["replicate"]),
    )
    key = "|".join(map(str, fields))
    rank = int.from_bytes(hashlib.sha256(key.encode()).digest(), "big")
    item = (-rank, row)
    if len(heap) < size:
        heapq.heappush(heap, item)
    elif rank < -heap[0][0]:
        heapq.heapreplace(heap, item)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def key_for_decision(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return row["cell_id"], row["index_stratum"], row["profile_id"], row["generator"]


def expected_decision(
    row: dict[str, str], reliability: list[dict[str, str]]
) -> tuple[str, bool, bool, bool]:
    if row["status"] == "UNASSESSABLE_NO_COMPATIBLE_HISTORY":
        no_compatible = int(row["truth_compatible_histories"]) == 0 or int(row["bank_compatible_histories"]) == 0
        return "UNASSESSABLE_NO_COMPATIBLE_HISTORY", False, False, no_compatible

    positive_log = math.isfinite(parse_float(row["log_gain_low"])) and parse_float(row["log_gain_low"]) > 0
    positive_brier = math.isfinite(parse_float(row["brier_gain_low"])) and parse_float(row["brier_gain_low"]) > 0
    computation = (
        parse_float(row["precision_truth_weight"]) >= 0.95
        and parse_float(row["supported_truth_weight"]) >= 0.95
        and parse_float(row["calibration_bootstrap_finite"]) >= 0.95
        and not parse_bool(row["positive_weight_zero_probability_contradiction"])
        and not parse_bool(row["proper_score_contradiction"])
    )
    calibrated = (
        parse_float(row["calibration_low"]) >= -0.05
        and parse_float(row["calibration_high"]) <= 0.05
        and parse_float(row["calibration_bootstrap_finite"]) >= 0.95
    )
    for bin_row in reliability:
        required = parse_bool(bin_row["required_for_gate"])
        passed = (
            parse_float(bin_row["residual_low"]) >= -0.10
            and parse_float(bin_row["residual_high"]) <= 0.10
            and parse_float(bin_row["finite_bootstrap"]) >= 0.95
        )
        if required:
            calibrated = calibrated and passed
    if not computation:
        status = "UNASSESSABLE"
    elif not calibrated:
        decisive = (
            parse_float(row["calibration_high"]) < -0.05
            or parse_float(row["calibration_low"]) > 0.05
            or any(
                parse_bool(bin_row["required_for_gate"])
                and (
                    parse_float(bin_row["residual_high"]) < -0.10
                    or parse_float(bin_row["residual_low"]) > 0.10
                )
                for bin_row in reliability
            )
        )
        status = "CALIBRATION_FAILED" if decisive else "UNASSESSABLE_CALIBRATION_PRECISION"
    else:
        status = (
            "CALIBRATED_AND_INFORMATIVE"
            if positive_log and positive_brier
            else "CALIBRATED_BUT_NO_INCREMENTAL_INFORMATION"
        )
    return status, computation, calibrated, True


def verify_previous_archives(
    audit: Audit, proposal: dict[str, Any], bindings: dict[str, Any]
) -> dict[str, Any]:
    results = []
    for archive in proposal["training_archives"]:
        canonical = ROOT / archive["canonical"]
        directory = ROOT / archive["path"]
        canonical_binding = sha256_file(canonical)
        manifest = load_json(canonical)
        output_results = {}
        outputs_match = manifest.get("outputs") == archive["outputs"]
        for filename, expected in archive["outputs"].items():
            path = directory / filename
            observed = sha256_file(path) if path.is_file() else None
            output_results[filename] = observed
            outputs_match = outputs_match and observed == expected
            if observed is not None:
                bindings[relative(path)] = observed
        audit.require(
            "earlier_completion_bindings",
            canonical_binding == archive["manifest"] and outputs_match,
            archive["path"],
        )
        bindings[relative(canonical)] = canonical_binding
        results.append(
            {
                "path": archive["path"],
                "canonical": archive["canonical"],
                "manifest": canonical_binding,
                "outputs": output_results,
                "run_namespace": archive["run_namespace"],
            }
        )
    return {"archives": results, "fit_excludes_terminal_and_remaining_evidence": proposal.get("fit_excludes_terminal_and_remaining_evidence")}


def audit_gate(generation_dir: Path, analysis_dir: Path, sample_size: int) -> dict[str, Any]:
    audit = Audit()
    bindings: dict[str, Any] = {}
    manifest_path = generation_dir / "run_manifest.json"
    receipt_path = analysis_dir / "analysis_receipt.json"
    manifest = load_json(manifest_path)
    receipt = load_json(receipt_path)
    bindings[relative(manifest_path)] = sha256_file(manifest_path)
    bindings[relative(receipt_path)] = sha256_file(receipt_path)

    run_root = generation_dir.parent
    execution_receipt_path = run_root / "execution_receipt.json"
    source_snapshot_path = run_root / "source_snapshot.json"
    exit_code_path = run_root / "gate_exit_code.txt"
    execution_receipt = load_json(execution_receipt_path)
    source_snapshot = load_json(source_snapshot_path)
    canonical_snapshot_path = ROOT / "data/age_probability_gate_20261003/provenance/source_snapshot.json"
    canonical_snapshot = load_json(canonical_snapshot_path)
    for path in (execution_receipt_path, source_snapshot_path, canonical_snapshot_path, exit_code_path):
        bindings[relative(path)] = sha256_file(path)
    audit.require(
        "top_level_execution_receipt",
        execution_receipt.get("status") == "complete"
        and execution_receipt.get("generation_status") == manifest.get("status")
        and execution_receipt.get("analysis_status") == receipt.get("status")
        and execution_receipt.get("nominal_site_histories") == EXPECTED_NOMINAL_SITE_HISTORIES
        and execution_receipt.get("actual_remaining_evidence_read") is False
        and exit_code_path.read_text().strip() == "0",
    )
    audit.require(
        "remote_source_snapshot_receipt",
        source_snapshot == canonical_snapshot
        and source_snapshot.get("file_count") == len(source_snapshot.get("files", {})) == 720
        and execution_receipt.get("source_files_reverified") == source_snapshot.get("file_count")
        and source_snapshot.get("head") == manifest.get("head"),
    )

    execution_plan_path = ROOT / "data/age_probability_gate_20261003/provenance/execution_plan.json"
    execution_plan = load_json(execution_plan_path)
    bindings[relative(execution_plan_path)] = sha256_file(execution_plan_path)
    plan_bound_paths = {
        "production_proposal": ROOT / "data/age_probability_gate_20261003/proposal.json",
        "qualification_receipt": ROOT / "data/age_probability_gate_20261003/provenance/qualification_receipt.json",
        "cross_platform_receipt": ROOT / "data/age_probability_gate_20261003/provenance/cross_platform_qualification.json",
    }
    plan_binding_mismatches = []
    for key, path in plan_bound_paths.items():
        observed = sha256_file(path)
        bindings[relative(path)] = observed
        if observed != execution_plan[key]:
            plan_binding_mismatches.append(key)
    audit.require(
        "execution_plan_bindings_and_budget",
        not plan_binding_mismatches
        and execution_plan.get("paired_cell_source_rows") == EXPECTED_SOURCE_ROWS
        and execution_plan.get("independent_source_ids") == EXPECTED_INDEPENDENT_SOURCE_IDS
        and execution_plan.get("joint_history_attempts") == EXPECTED_HISTORY_ROWS
        and execution_plan.get("nominal_site_history_attempts") == EXPECTED_NOMINAL_SITE_HISTORIES
        and execution_plan.get("post_outcome_draws_permitted") is False,
        repr(plan_binding_mismatches),
    )

    audit.require("generation_complete", manifest.get("status") == "complete")
    audit.require("full_design", manifest.get("full_design") is True and manifest.get("mode") == "gate")
    audit.require("analysis_full_design", receipt.get("full_design") is True)
    audit.require(
        "fixed_design_manifest",
        manifest.get("source_rows") == EXPECTED_SOURCE_ROWS
        and manifest.get("replicates_per_source") == EXPECTED_REPLICATES
        and manifest.get("nominal_site_histories") == EXPECTED_NOMINAL_SITE_HISTORIES
        and manifest.get("truth_sources_per_cell") == 512
        and manifest.get("bank_sources_per_cell") == 512
        and len(manifest.get("cells", [])) == 8,
    )

    generation_output_mismatches = []
    for filename, expected in manifest["outputs"].items():
        path = generation_dir / filename
        observed = sha256_file(path) if path.is_file() else None
        if observed != expected:
            generation_output_mismatches.append(filename)
        elif observed is not None:
            bindings[relative(path)] = observed
    audit.require("generation_output_bindings", not generation_output_mismatches, repr(generation_output_mismatches))
    verify_binding_map(audit, "generation_source_bindings_current", manifest["source_bindings"], bindings)
    proposal_path = ROOT / "data/age_probability_gate_20261003/proposal.json"
    proposal = load_json(proposal_path)
    proposal_binding = sha256_file(proposal_path)
    bindings[relative(proposal_path)] = proposal_binding
    audit.require("proposal_binding", proposal_binding == manifest["proposal"] == manifest["source_bindings"][relative(proposal_path)])
    verify_binding_map(audit, "proposal_source_bindings_current", proposal["source_bindings"], bindings)
    previous = verify_previous_archives(audit, proposal, bindings)

    sources = list(jsonl(generation_dir / "source_banks.jsonl"))
    source_identity = {(row["cell_id"], row["role"], int(row["index"])) for row in sources}
    source_ids = {row["source_id"] for row in sources}
    audit.require("source_row_count", len(sources) == EXPECTED_SOURCE_ROWS, str(len(sources)))
    audit.require("source_row_identity_unique", len(source_identity) == len(sources))
    audit.require("independent_source_id_count", len(source_ids) == EXPECTED_INDEPENDENT_SOURCE_IDS, str(len(source_ids)))
    id_counts = Counter(row["source_id"] for row in sources)
    audit.require("paired_restriction_source_reuse", set(id_counts.values()) == {4}, repr(Counter(id_counts.values())))
    source_versions: dict[str, set[str]] = defaultdict(set)
    for row in sources:
        source_versions[row["source_id"]].add(stable_source_record(row))
    audit.require("paired_source_parameters_identical", all(len(value) == 1 for value in source_versions.values()))
    per_cell_role = Counter((row["cell_id"], row["role"]) for row in sources)
    audit.require("source_balance_by_cell_role", set(per_cell_role.values()) == {512}, repr(per_cell_role))
    per_cell_role_stratum = Counter((row["cell_id"], row["role"], row["index_stratum"]) for row in sources)
    audit.require("source_balance_by_stratum", set(per_cell_role_stratum.values()) == {256}, repr(per_cell_role_stratum))

    source_lookup = {(row["cell_id"], row["role"], row["source_id"]): row for row in sources}
    planned_bank: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in sources:
        if row["role"] == "bank":
            planned_bank[(row["cell_id"], row["index_stratum"])].add(row["source_id"])

    histories_path = generation_dir / "histories.jsonl.gz"
    histories: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    truth_complete: set[tuple[str, str, str, int]] = set()
    history_keys: set[tuple[str, str, str, int]] = set()
    statuses: Counter[str] = Counter()
    advances = 0
    nominal_sites = 0
    compact_content = hashlib.sha256()
    history_count = 0
    with gzip.open(histories_path, "rb") as stream:
        for line_number, raw_line in enumerate(stream, 1):
            compact_content.update(raw_line)
            row = json.loads(raw_line)
            history_count += 1
            role = row["namespace"]
            key = (row["cell_id"], role, row["source_id"], int(row["replicate"]))
            history_keys.add(key)
            statuses[row["status"]] += 1
            advances += int(row["advance_calls"])
            nominal_sites += int(row["nominal_site_histories"])
            source = source_lookup.get((row["cell_id"], role, row["source_id"]))
            audit.require("history_source_match", source is not None, f"line {line_number}")
            if source is not None:
                audit.require("history_stratum_match", row["index_stratum"] == source["index_stratum"], f"line {line_number}")
                audit.require(
                    "history_proposal_ratio_match",
                    close(float(row["proposal_log_density_ratio"]), float(source["proposal_log_density_ratio"]), atol=0.0, rtol=0.0),
                    f"line {line_number}",
                )
            if row["status"] == "complete" and row["conditioning"]["total"] is not None:
                group = (row["cell_id"], row["index_stratum"])
                if role == "truth":
                    truth_complete.add((row["cell_id"], row["index_stratum"], row["source_id"], int(row["replicate"])))
                if role == "bank":
                    x_early, x_february, late_mean, insurance = reduced_exposures(row["features"])
                    histories[group].append(
                        {
                            "source_id": row["source_id"],
                            "replicate": int(row["replicate"]),
                            "log_weight": float(row["conditioning"]["total"]) - float(row["proposal_log_density_ratio"]),
                            "loss": bool(row["loss_2002"]),
                            "x_early": x_early,
                            "x_february": x_february,
                            "late_mean": late_mean,
                            "insurance": insurance,
                        }
                    )
    audit.require("history_row_count", history_count == EXPECTED_HISTORY_ROWS, str(history_count))
    audit.require("history_identity_unique", len(history_keys) == history_count, str(len(history_keys)))
    expected_history_keys = {
        (row["cell_id"], row["role"], row["source_id"], replicate)
        for row in sources for replicate in range(int(manifest["replicates_per_source"]))
    }
    audit.require(
        "complete_planned_history_universe",
        history_keys == expected_history_keys,
        f"missing={len(expected_history_keys - history_keys)}, unexpected={len(history_keys - expected_history_keys)}",
    )
    audit.require("nominal_site_history_count", nominal_sites == EXPECTED_NOMINAL_SITE_HISTORIES, str(nominal_sites))
    audit.require("generation_status_counts", dict(statuses) == manifest["history_status_counts"])
    audit.require("actual_advance_calls", advances == manifest["actual_advance_calls"])
    audit.require(
        "executed_linked_history_count",
        statuses["complete"] + statuses["process_infeasible"] == manifest["executed_linked_histories"],
    )
    audit.require(
        "compact_content_hash",
        compact_content.hexdigest() == manifest["content_sha256"]["histories.jsonl"],
    )
    full_digest, full_rows = sha256_uncompressed_gzip(generation_dir / "full_histories.jsonl.gz")
    audit.require("full_history_row_count", full_rows == EXPECTED_HISTORY_ROWS, str(full_rows))
    audit.require("full_content_hash", full_digest == manifest["content_sha256"]["full_histories.jsonl"])

    analysis_output_mismatches = []
    for filename, expected in receipt["outputs"].items():
        path = analysis_dir / filename
        observed = sha256_file(path) if path.is_file() else None
        if observed != expected:
            analysis_output_mismatches.append(filename)
        elif observed is not None:
            bindings[relative(path)] = observed
    audit.require("analysis_output_bindings", not analysis_output_mismatches, repr(analysis_output_mismatches))
    audit.require("analysis_generation_binding", receipt["generation_manifest"] == bindings[relative(manifest_path)])
    verify_binding_map(audit, "analysis_source_bindings_current", receipt["source_bindings"], bindings)

    metrics = read_csv(analysis_dir / "gate_metrics.csv")
    reliability_rows = read_csv(analysis_dir / "reliability.csv")
    audit.require("metric_row_count", len(metrics) == EXPECTED_METRIC_ROWS, str(len(metrics)))
    primary = [row for row in metrics if int(row["maximum_age"]) == 6]
    audit.require("primary_metric_row_count", len(primary) == EXPECTED_PRIMARY_ROWS, str(len(primary)))
    metric_keys = [key_for_decision(row) for row in metrics]
    audit.require("metric_identity_unique", len(set(metric_keys)) == len(metric_keys))
    decision_groups = Counter((row["cell_id"], row["index_stratum"]) for row in metrics)
    audit.require("metric_group_coverage", len(decision_groups) == 16 and set(decision_groups.values()) == {72}, repr(decision_groups))
    profile_tuples = {(parse_float(row["K"]), parse_float(row["rho"]), parse_float(row["q"]), row["profile_id"]) for row in metrics if row["status"] != "UNASSESSABLE_NO_COMPATIBLE_HISTORY"}
    expected_profile_values = {
        (k, rho, q) for k in (2.5, 5.0, 10.0, 20.0)
        for rho in (0.25, 1.0, 4.0) for q in (0.01, 0.1, 1.0)
    }
    expected_profile_ids = {
        f"K{k:g}_rho{rho:g}_q{q:g}_base"
        for k, rho, q in expected_profile_values
    }
    audit.require(
        "profile_panel_coverage",
        {row["profile_id"] for row in metrics} == expected_profile_ids
        and {row["generator"] for row in metrics} == set(GENERATORS)
        and all((k, rho, q) in expected_profile_values and profile == f"K{k:g}_rho{rho:g}_q{q:g}_base"
                for k, rho, q, profile in profile_tuples),
    )
    reliability_by_key: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in reliability_rows:
        reliability_by_key[key_for_decision(row)].append(row)

    decision_mismatches = []
    boolean_mismatches = []
    for row in metrics:
        key = key_for_decision(row)
        expected_status, expected_computation, expected_calibrated, meaningful = expected_decision(
            row, reliability_by_key[key]
        )
        if not meaningful or row["status"] != expected_status or parse_bool(row["qualified"]) != (expected_status in QUALIFIED):
            decision_mismatches.append({"key": key, "saved": row["status"], "expected": expected_status})
        if row["status"] != "UNASSESSABLE_NO_COMPATIBLE_HISTORY":
            positive_log = math.isfinite(parse_float(row["log_gain_low"])) and parse_float(row["log_gain_low"]) > 0
            positive_brier = math.isfinite(parse_float(row["brier_gain_low"])) and parse_float(row["brier_gain_low"]) > 0
            if (
                parse_bool(row["computationally_assessed"]) != expected_computation
                or parse_bool(row["calibration_equivalence_pass"]) != expected_calibrated
                or parse_bool(row["positive_log_gain"]) != positive_log
                or parse_bool(row["positive_brier_gain"]) != positive_brier
            ):
                boolean_mismatches.append(key)
            for bin_row in reliability_by_key[key]:
                expected_pass = (
                    parse_float(bin_row["residual_low"]) >= -0.10
                    and parse_float(bin_row["residual_high"]) <= 0.10
                    and parse_float(bin_row["finite_bootstrap"]) >= 0.95
                )
                if parse_bool(bin_row["passed"]) != expected_pass:
                    boolean_mismatches.append(key)
    audit.require("all_decisions_recomputed", not decision_mismatches, repr(decision_mismatches[:5]))
    audit.require("decision_component_booleans", not boolean_mismatches, repr(boolean_mismatches[:5]))

    all_status = Counter(row["status"] for row in metrics)
    primary_status = Counter(row["status"] for row in primary)
    proper_score_contradictions = sum(
        row["status"] != "UNASSESSABLE_NO_COMPATIBLE_HISTORY"
        and parse_bool(row["proper_score_contradiction"])
        for row in metrics
    )
    explicit_zero_one_contradictions = sum(
        row["status"] != "UNASSESSABLE_NO_COMPATIBLE_HISTORY"
        and parse_bool(row["positive_weight_zero_probability_contradiction"])
        for row in metrics
    )
    broader_proper_score_only = sum(
        row["status"] != "UNASSESSABLE_NO_COMPATIBLE_HISTORY"
        and parse_bool(row["proper_score_contradiction"])
        and not parse_bool(row["positive_weight_zero_probability_contradiction"])
        for row in metrics
    )
    broader_proper_score_only_blocking = sum(
        row["status"] != "UNASSESSABLE_NO_COMPATIBLE_HISTORY"
        and parse_bool(row["proper_score_contradiction"])
        and not parse_bool(row["positive_weight_zero_probability_contradiction"])
        and parse_float(row["precision_truth_weight"]) >= 0.95
        and parse_float(row["supported_truth_weight"]) >= 0.95
        and parse_float(row["calibration_bootstrap_finite"]) >= 0.95
        for row in metrics
    )
    primary_assessed = [row for row in primary if parse_bool(row["computationally_assessed"])]
    primary_proper_score_contradictions = sum(
        parse_bool(row["proper_score_contradiction"]) for row in primary
    )
    primary_explicit_zero_one_contradictions = sum(
        parse_bool(row["positive_weight_zero_probability_contradiction"]) for row in primary
    )
    primary_supported_weights = [parse_float(row["supported_truth_weight"]) for row in primary]
    audit.require("receipt_all_status_counts", dict(all_status) == receipt["all_status_counts"])
    audit.require("receipt_primary_status_counts", dict(primary_status) == receipt["primary_status_counts"])
    qualified_primary = [
        {name: row[name] for name in ("cell_id", "index_stratum", "profile_id", "generator", "status")}
        for row in primary if row["status"] in QUALIFIED
    ]
    audit.require("receipt_qualified_columns", qualified_primary == receipt["qualified_primary_columns"])
    expected_receipt_status = (
        "CONDITIONAL_GO_QUALIFIED_PROBABILITY_COLUMNS" if qualified_primary else "STOP_FINAL_BOUNDED_ATTEMPT"
    )
    audit.require("receipt_global_status", receipt["status"] == expected_receipt_status)

    baseline_mismatches = []
    e_only: dict[tuple[str, str], float] = {}
    for group in decision_groups:
        probability, _ = source_averaged_probability(histories[group], planned_bank[group])
        e_only[group] = probability
        for row in metrics:
            if (row["cell_id"], row["index_stratum"]) != group or row["status"] == "UNASSESSABLE_NO_COMPATIBLE_HISTORY":
                continue
            if not close(parse_float(row["E_only_loss"]), probability):
                baseline_mismatches.append({"group": group, "saved": row["E_only_loss"], "recomputed": probability})
    audit.require("e_only_natural_prevalence", not baseline_mismatches, repr(baseline_mismatches[:5]))

    forecast_heap: list[tuple[int, dict[str, Any]]] = []
    forecast_counts: dict[str, int] = {}
    forecast_binding_mismatches = []
    forecast_identity_mismatches = 0
    expected_forecast_files = {row["path"]: row for row in receipt["forecast_files"]}
    for filename, entry in sorted(expected_forecast_files.items()):
        path = analysis_dir / filename
        observed_binding = sha256_file(path)
        if observed_binding != {"bytes": entry["bytes"], "sha256": entry["sha256"]}:
            forecast_binding_mismatches.append(filename)
        count = 0
        for row in jsonl(path, compressed=True):
            count += 1
            identity = (row["cell_id"], row["index_stratum"], row["source_id"], int(row["replicate"]))
            if identity not in truth_complete:
                forecast_identity_mismatches += 1
            select_sample(forecast_heap, row, sample_size)
        forecast_counts[filename] = count
        if count != int(entry["rows"]):
            forecast_binding_mismatches.append(filename)
    audit.require("forecast_file_bindings_and_rows", not forecast_binding_mismatches, repr(forecast_binding_mismatches))
    audit.require("forecast_truth_identity_matches", forecast_identity_mismatches == 0, str(forecast_identity_mismatches))
    expected_detail_rows = sum(
        len([x for x in truth_complete if x[0] == cell and x[1] == stratum])
        * int(receipt["profiles"]) * len(receipt["generators"])
        for cell, stratum in decision_groups if histories[(cell, stratum)]
    )
    audit.require("forecast_total_rows", sum(forecast_counts.values()) == expected_detail_rows, f"{sum(forecast_counts.values())} != {expected_detail_rows}")

    sampled = [item[1] for item in sorted(forecast_heap, key=lambda item: -item[0])]
    forecast_mismatches = []
    sample_summary = []
    for row in sampled:
        group = (row["cell_id"], row["index_stratum"])
        probability, zero_sources = source_averaged_probability(
            histories[group], planned_bank[group],
            late_count=int(row["late_count"]), insurance=tuple(map(bool, row["insurance"])),
            k_value=float(next(metric["K"] for metric in metrics if key_for_decision(metric) == key_for_decision(row))),
            rho=float(next(metric["rho"] for metric in metrics if key_for_decision(metric) == key_for_decision(row))),
            q=float(next(metric["q"] for metric in metrics if key_for_decision(metric) == key_for_decision(row))),
            generator=row["generator"],
        )
        saved = float(row["probability"]) if row["probability"] is not None else math.nan
        matched = close(saved, probability, atol=2e-11, rtol=2e-11)
        if not matched:
            forecast_mismatches.append({"key": key_for_decision(row), "source_id": row["source_id"], "replicate": row["replicate"], "saved": saved, "recomputed": probability})
        sample_summary.append(
            {
                "cell_id": row["cell_id"], "index_stratum": row["index_stratum"],
                "profile_id": row["profile_id"], "generator": row["generator"],
                "source_id": row["source_id"], "replicate": int(row["replicate"]),
                "saved_probability": finite_or_none(saved), "recomputed_probability": finite_or_none(probability),
                "absolute_error": abs(saved - probability) if math.isfinite(saved) and math.isfinite(probability) else None,
                "planned_bank_sources": len(planned_bank[group]), "zero_contribution_bank_sources": zero_sources,
            }
        )
    audit.require("sampled_forecast_reconstruction", not forecast_mismatches, repr(forecast_mismatches[:5]))

    analyzer_text = (ROOT / "scripts/analyze_age_probability_gate.py").read_text()
    bound_python_with_actual_target = []
    for declared in receipt["source_bindings"]:
        path = ROOT / declared
        if path.suffix == ".py" and "r_actual" in path.read_text().lower():
            bound_python_with_actual_target.append(declared)
    bound_actual_data_paths = [
        declared for declared in receipt["source_bindings"]
        if any(token in declared.lower() for token in ("r_actual", "actual_remaining", "remaining_evidence"))
    ]
    no_actual = (
        receipt.get("actual_remaining_evidence_read") is False
        and receipt.get("actual_historical_probability_computed") is False
        and proposal.get("fit_excludes_terminal_and_remaining_evidence") is True
        and "R_actual" not in analyzer_text
        and not bound_python_with_actual_target
        and not bound_actual_data_paths
    )
    audit.require("no_actual_R_access_evidence", no_actual)

    result = {
        "status": "PASS" if not audit.failures else "FAIL",
        "audit_scope": "Independent read-only verification of the frozen age probability gate generation, decision table, natural-prevalence forecast calculations, and provenance bindings.",
        "checks": audit.checks,
        "failures": audit.failures,
        "source_and_history_counts": {
            "source_rows": len(sources), "independent_source_ids": len(source_ids),
            "compact_history_rows": history_count, "full_history_rows": full_rows,
            "nominal_site_histories": nominal_sites, "history_status_counts": dict(statuses),
        },
        "decision_counts": {
            "all_rows": len(metrics), "primary_age6_rows": len(primary),
            "all_status_counts": dict(all_status), "primary_status_counts": dict(primary_status),
            "qualified_primary_columns": len(qualified_primary), "global_status": receipt["status"],
            "proper_score_contradiction_rows": proper_score_contradictions,
            "explicit_zero_one_outcome_contradiction_rows": explicit_zero_one_contradictions,
            "broader_proper_score_only_rows": broader_proper_score_only,
            "broader_proper_score_only_rows_blocking_otherwise_sufficient_computation": broader_proper_score_only_blocking,
        },
        "primary_decision_diagnostics": {
            "proper_score_contradiction_rows": primary_proper_score_contradictions,
            "explicit_zero_one_outcome_contradiction_rows": primary_explicit_zero_one_contradictions,
            "broader_proper_score_only_rows": primary_proper_score_contradictions - primary_explicit_zero_one_contradictions,
            "supported_truth_weight_range": value_range(primary_supported_weights),
            "computationally_assessed_rows": len(primary_assessed),
            "computationally_assessed_cell_strata": sorted({
                f"{row['restriction']}:{row['index_stratum']}" for row in primary_assessed
            }),
            "assessed_calibration_low_range": value_range(
                parse_float(row["calibration_low"]) for row in primary_assessed
            ),
            "assessed_calibration_high_range": value_range(
                parse_float(row["calibration_high"]) for row in primary_assessed
            ),
            "assessed_truth_source_ess": sorted({parse_float(row["truth_source_ess"]) for row in primary_assessed}),
            "assessed_bank_source_ess": sorted({parse_float(row["bank_source_ess"]) for row in primary_assessed}),
        },
        "probability_reconstruction": {
            "e_only_groups": len(e_only), "sample_selection": "smallest SHA256 ranks of identifiers only; terminal outcomes, synthetic observations, and saved probabilities excluded",
            "sampled_forecasts": len(sampled), "sample_rows": sample_summary,
            "likelihoods": "independent NB(size=69) late-count PMF plus Bernoulli-Poisson or integrated shared Gamma(1,1) visit-quality binary law",
            "aggregation": "six planned replicates averaged within every planned bank source; failed attempts/sources retained as zero contributions",
        },
        "previous_completion_verification": previous,
        "execution_closure": {
            "execution_receipt": execution_receipt,
            "source_snapshot_file_count": source_snapshot["file_count"],
            "source_snapshot_head": source_snapshot["head"],
            "gate_exit_code": exit_code_path.read_text().strip(),
            "limitation": "The independent audit verifies the mirrored snapshot/receipt identity and all bound gate dependencies; the 720-file end-of-run rehash itself was executed by the frozen remote driver and is evidenced by its receipt rather than repeated against a mutable post-run local worktree.",
        },
        "no_actual_R_access": {
            "analysis_receipt_actual_remaining_evidence_read": receipt.get("actual_remaining_evidence_read"),
            "analysis_receipt_actual_historical_probability_computed": receipt.get("actual_historical_probability_computed"),
            "proposal_fit_excludes_terminal_and_remaining_evidence": proposal.get("fit_excludes_terminal_and_remaining_evidence"),
            "executable_source_names_R_actual": "R_actual" in analyzer_text,
            "bound_python_sources_naming_actual_target": bound_python_with_actual_target,
            "bound_actual_data_paths": bound_actual_data_paths,
            "limitation": "This verifies frozen source and receipt evidence, path bindings, and synthetic forecast structure; it is not an operating-system file-access trace.",
        },
        "hash_bindings": dict(sorted(bindings.items())),
        "caveats": [
            "The 8,192 cell-source rows reuse each of 2,048 independent nuisance-source IDs across four paired restrictions.",
            "Calibration here is prospective synthetic-data calibration conditional on the engineering model and E; it is not empirical model adequacy or a historical-fate estimate.",
            "The deterministic forecast audit is a bounded outcome-independent sample; every E-only probability and every recorded decision status is recomputed.",
            "The frozen proper_score_contradiction flag covers any nonfinite positive-weight log score, including an undefined forecast or comparator; it is broader than the separate explicit p=0/1 outcome-contradiction flag.",
            "A qualified primary column would authorize only the separately governed one-time actual-R step; this audit does not consume actual R.",
        ],
    }
    return result


def self_test() -> dict[str, bool]:
    checks: dict[str, bool] = {}
    checks["nb_zero_exposure"] = nb69_log_pmf(0, 69.0, 0.0) == 0.0 and nb69_log_pmf(1, 69.0, 0.0) == -math.inf
    mass = sum(math.exp(nb69_log_pmf(k, 69.0, 23.0)) for k in range(400))
    checks["nb_mass"] = close(mass, 1.0, atol=1e-12, rtol=1e-12)
    a, b = 0.7, 1.3
    pair_mass = sum(
        math.exp(gamma_pair_log_probability(a, b, first, second))
        for first in (False, True) for second in (False, True)
    )
    checks["gamma_pair_mass"] = close(pair_mass, 1.0, atol=1e-14, rtol=1e-14)
    p_seen = math.exp(insurance_log_probability((2.0,) * 9, (True,) + (False,) * 8, 0.1, "poisson"))
    expected = (1.0 - math.exp(-0.2)) * math.exp(-0.2 * 8)
    checks["poisson_binary"] = close(p_seen, expected, atol=1e-14, rtol=1e-14)
    histories = [{"source_id": "a", "log_weight": 0.0, "loss": True}]
    probability, zero = source_averaged_probability(histories, {"a", "b"})
    checks["failed_source_zero_contribution"] = probability == 1.0 and zero == 1
    return checks


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation-dir", type=Path, default=DEFAULT_GENERATION)
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sample-size", type=int, default=32)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        checks = self_test()
        print(json.dumps({"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}, sort_keys=True))
        raise SystemExit(0 if all(checks.values()) else 1)
    if args.sample_size < 1 or args.sample_size > 256:
        raise ValueError("sample-size must be in 1..256")
    result = audit_gate(args.generation_dir.resolve(), args.analysis_dir.resolve(), args.sample_size)
    save_json(args.output.resolve(), result)
    print(json.dumps({"status": result["status"], "checks": len(result["checks"]), "failures": result["failures"]}, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
