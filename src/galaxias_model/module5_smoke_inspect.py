from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from galaxias_model.module5_output_checks import (
    check_matched_pair_ids,
    check_ordered_schema,
    check_seed_pairing,
    check_source_identity,
)


DEFAULT_SMOKE_DIR = Path("outputs/module5_runner_smoke")
DEFAULT_OUTCOME_SCHEMA_PATH = Path("data/module5_counterfactual_outcome_schema.csv")
DEFAULT_INSPECTION_DIRNAME = "inspection"


@dataclass(frozen=True)
class SmokeInspectionResult:
    all_checks_passed: bool
    inspection_dir: Path
    summary_path: Path
    checks_path: Path
    report_path: Path


def _read_schema_columns(outcome_schema_path: Path) -> list[str]:
    return pd.read_csv(outcome_schema_path)["column_name"].astype(str).tolist()


def _load_inputs(smoke_dir: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    outcomes_path = smoke_dir / "matched_outcomes.csv"
    provenance_path = smoke_dir / "provenance.json"
    if not outcomes_path.exists():
        raise FileNotFoundError(f"Missing Module 5 smoke output: {outcomes_path}")
    if not provenance_path.exists():
        raise FileNotFoundError(f"Missing Module 5 smoke provenance: {provenance_path}")
    return pd.read_csv(outcomes_path), json.loads(provenance_path.read_text(encoding="utf-8"))


def _check_provenance_labels(provenance: dict[str, object]) -> dict[str, object]:
    status = provenance.get("status")
    production_attribution = provenance.get("production_attribution")
    output_file = str(provenance.get("output_file", ""))
    boundary_note = str(provenance.get("boundary_note", ""))
    passed = (
        status == "tiny_local_smoke_only"
        and production_attribution is False
        and output_file.endswith("matched_outcomes.csv")
        and bool(boundary_note.strip())
    )
    return {
        "check_name": "provenance_labels",
        "passed": passed,
        "details": (
            f"status={status} production_attribution={production_attribution} "
            f"output_file={output_file}"
        ),
    }


def _check_smoke_only_boundary(outcomes: pd.DataFrame, provenance: dict[str, object]) -> dict[str, object]:
    note = str(provenance.get("boundary_note", "")).lower()
    variant_ok = "variant_id" in outcomes.columns and outcomes["variant_id"].astype(str).str.contains("smoke").all()
    proposal_ok = (
        "proposal_id" in outcomes.columns
        and outcomes["proposal_id"].astype(str).str.startswith("smoke_default:").all()
    )
    language_ok = "not production attribution" in note and "manuscript evidence" in note
    return {
        "check_name": "smoke_only_boundary",
        "passed": bool(variant_ok and proposal_ok and language_ok),
        "details": (
            f"variant_smoke={bool(variant_ok)} proposal_smoke={bool(proposal_ok)} "
            f"boundary_language={language_ok}"
        ),
    }


def build_inspection_checks(
    outcomes: pd.DataFrame,
    provenance: dict[str, object],
    schema_columns: list[str],
) -> list[dict[str, object]]:
    return [
        check_ordered_schema(outcomes, schema_columns),
        check_source_identity(outcomes, provenance),
        check_matched_pair_ids(outcomes),
        check_seed_pairing(outcomes).check,
        _check_provenance_labels(provenance),
        _check_smoke_only_boundary(outcomes, provenance),
    ]


def _write_report(
    report_path: Path,
    summary: dict[str, object],
    checks: list[dict[str, object]],
) -> None:
    lines = [
        "# Module 5 Smoke Output Inspection",
        "",
        "This report inspects emitted tiny local smoke files from disk. It is not production attribution and not manuscript evidence.",
        "",
        "## Summary",
        "",
        f"- all_checks_passed: `{summary['all_checks_passed']}`",
        f"- row_count: `{summary['row_count']}`",
        f"- intervention_count: `{summary['intervention_count']}`",
        f"- matched_pair_count: `{summary['matched_pair_count']}`",
        f"- smoke_only_boundary: `{summary['smoke_only_boundary']}`",
        "",
        "## Checks",
        "",
        "| check_name | passed | details |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        details = str(check["details"]).replace("|", "\\|")
        lines.append(f"| {check['check_name']} | {check['passed']} | {details} |")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def inspect_module5_counterfactual_smoke(
    smoke_dir: Path = DEFAULT_SMOKE_DIR,
    outcome_schema_path: Path = DEFAULT_OUTCOME_SCHEMA_PATH,
    inspection_dir: Path | None = None,
) -> SmokeInspectionResult:
    smoke_dir = smoke_dir.resolve()
    outcome_schema_path = outcome_schema_path.resolve()
    inspection_dir = (inspection_dir or smoke_dir / DEFAULT_INSPECTION_DIRNAME).resolve()
    inspection_dir.mkdir(parents=True, exist_ok=True)

    outcomes, provenance = _load_inputs(smoke_dir)
    schema_columns = _read_schema_columns(outcome_schema_path)
    checks = build_inspection_checks(outcomes, provenance, schema_columns)
    all_checks_passed = all(bool(check["passed"]) for check in checks)
    smoke_only_boundary = bool(
        next(check for check in checks if check["check_name"] == "smoke_only_boundary")["passed"]
    )
    summary = {
        "all_checks_passed": all_checks_passed,
        "row_count": int(len(outcomes)),
        "column_count": int(len(outcomes.columns)),
        "intervention_count": int(outcomes["intervention_id"].nunique()) if "intervention_id" in outcomes else 0,
        "matched_pair_count": int(outcomes["matched_pair_id"].nunique()) if "matched_pair_id" in outcomes else 0,
        "smoke_only_boundary": smoke_only_boundary,
        "source_smoke_dir": smoke_dir.as_posix(),
        "outcome_schema_path": outcome_schema_path.as_posix(),
        "inspected_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_path = inspection_dir / "inspection_summary.json"
    checks_path = inspection_dir / "inspection_checks.csv"
    report_path = inspection_dir / "inspection_report.md"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(checks).to_csv(checks_path, index=False)
    _write_report(report_path, summary, checks)

    return SmokeInspectionResult(
        all_checks_passed=all_checks_passed,
        inspection_dir=inspection_dir,
        summary_path=summary_path,
        checks_path=checks_path,
        report_path=report_path,
    )
