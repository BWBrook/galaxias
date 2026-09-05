from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from galaxias_model.module5_counterfactual import (
    DEFAULT_OUTCOME_SCHEMA_PATH,
    read_outcome_schema_columns,
)
from galaxias_model.module5_output_checks import (
    check_matched_pair_ids,
    check_ordered_schema,
    check_seed_pairing,
    check_source_identity,
)
from galaxias_model.module5_partitions import INTERVENTION_TO_PARTITION
from galaxias_model.module5_rehearsal import (
    DEFAULT_REHEARSAL_OUTPUT_DIR,
    DEFAULT_REHEARSAL_REPLICATES,
    REHEARSAL_STATUS,
)


@dataclass(frozen=True)
class RehearsalInspectionResult:
    all_checks_passed: bool
    inspection_dir: Path
    summary_path: Path
    checks_path: Path
    report_path: Path


def _read_inputs(rehearsal_dir: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    outcomes_path = rehearsal_dir / "matched_outcomes.csv"
    provenance_path = rehearsal_dir / "provenance.json"
    if not outcomes_path.exists():
        raise FileNotFoundError(f"Missing rehearsal matched outcomes: {outcomes_path}")
    if not provenance_path.exists():
        raise FileNotFoundError(f"Missing rehearsal provenance: {provenance_path}")
    return pd.read_csv(outcomes_path, keep_default_na=False), json.loads(
        provenance_path.read_text(encoding="utf-8")
    )


def _partition_labels_for(outcomes: pd.DataFrame) -> pd.Series:
    if "partition_label" in outcomes.columns:
        return outcomes["partition_label"].astype(str)
    return (
        outcomes["intervention_id"]
        .astype(str)
        .map(INTERVENTION_TO_PARTITION)
        .fillna("unknown")
    )


def _check_partition_counts(
    outcomes: pd.DataFrame,
    expected_partition_rows: dict[str, int],
) -> tuple[dict[str, object], pd.Series]:
    labels = _partition_labels_for(outcomes)
    actual = {
        str(key): int(value)
        for key, value in labels.value_counts().sort_index().to_dict().items()
    }
    return (
        {
            "check_name": "partition_counts",
            "passed": actual == expected_partition_rows,
            "details": f"partition_rows={actual} expected={expected_partition_rows}",
        },
        labels,
    )


def _check_replicate_coverage(
    outcomes: pd.DataFrame,
    expected_replicates: int,
    expected_units: int,
) -> dict[str, object]:
    required = ["proposal_source_key", "intervention_id", "stochastic_replicate_id"]
    missing = [column for column in required if column not in outcomes.columns]
    if missing:
        return {
            "check_name": "replicate_coverage",
            "passed": False,
            "details": f"missing required columns={missing}",
        }
    expected_ids = set(range(expected_replicates))
    failures: list[str] = []
    unit_count = 0
    for (source_key, intervention_id), group in outcomes.groupby(
        ["proposal_source_key", "intervention_id"],
        sort=False,
    ):
        unit_count += 1
        replicate_values = pd.to_numeric(
            group["stochastic_replicate_id"], errors="coerce"
        )
        replicate_ids = set(replicate_values.dropna())
        if (
            len(group) != expected_replicates
            or replicate_values.isna().any()
            or replicate_ids != expected_ids
        ):
            failures.append(
                f"{source_key}|{intervention_id}: rows={len(group)} "
                f"replicate_ids={sorted(replicate_ids)}"
            )
            if len(failures) >= 5:
                break
    passed = unit_count == expected_units and not failures
    return {
        "check_name": "replicate_coverage",
        "passed": passed,
        "details": (
            f"units={unit_count} expected_units={expected_units} "
            f"expected_replicates={expected_replicates}"
            if passed
            else f"units={unit_count} expected_units={expected_units} failures={failures}"
        ),
    }


def _check_provenance(provenance: dict[str, object]) -> dict[str, object]:
    status = provenance.get("status")
    production_attribution = provenance.get("production_attribution")
    passed = status == REHEARSAL_STATUS and production_attribution is False
    return {
        "check_name": "provenance_labels",
        "passed": passed,
        "details": f"status={status} production_attribution={production_attribution}",
    }


def _write_report(
    report_path: Path,
    summary: dict[str, object],
    checks: list[dict[str, object]],
) -> None:
    lines = [
        "# Module 5 Matched-Counterfactual Execution Inspection",
        "",
        "This report inspects matched-counterfactual outputs from disk. It is not production attribution or manuscript evidence.",
        "",
        "## Summary",
        "",
    ]
    for key in [
        "all_checks_passed",
        "row_count",
        "column_count",
        "expected_replicates",
        "source_intervention_units",
        "distinct_proposal_source_keys",
        "source_identity",
        "replicate_coverage",
        "seed_mismatches",
        "production_attribution",
    ]:
        lines.append(f"- {key}: `{summary[key]}`")
    lines.extend(
        [
            "",
            "## Checks",
            "",
            "| check_name | passed | details |",
            "| --- | --- | --- |",
        ]
    )
    for check in checks:
        details = str(check["details"]).replace("|", "\\|")
        lines.append(f"| {check['check_name']} | {check['passed']} | {details} |")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def inspect_rehearsal_output(
    *,
    rehearsal_dir: Path = DEFAULT_REHEARSAL_OUTPUT_DIR,
    outcome_schema_path: Path = DEFAULT_OUTCOME_SCHEMA_PATH,
    inspection_dir: Path | None = None,
) -> RehearsalInspectionResult:
    rehearsal_dir = rehearsal_dir.resolve()
    outcome_schema_path = outcome_schema_path.resolve()
    inspection_dir = (inspection_dir or rehearsal_dir / "inspection").resolve()
    inspection_dir.mkdir(parents=True, exist_ok=True)

    outcomes, provenance = _read_inputs(rehearsal_dir)
    schema_columns = read_outcome_schema_columns(outcome_schema_path)
    expected_replicates = int(
        provenance.get("expected_replicates", DEFAULT_REHEARSAL_REPLICATES)
    )
    expected_rows = int(provenance.get("expected_row_count", 0))
    expected_units = int(provenance.get("expected_source_intervention_units", 0))
    expected_distinct_keys = int(
        provenance.get("expected_distinct_proposal_source_keys", 0)
    )
    expected_partition_rows = {
        str(key): int(value)
        for key, value in dict(
            provenance.get("expected_partition_row_counts", {})
        ).items()
    }

    partition_check, labels = _check_partition_counts(
        outcomes, expected_partition_rows
    )
    seed_result = check_seed_pairing(outcomes)
    unit_count = outcomes.groupby(
        ["proposal_source_key", "intervention_id"]
    ).ngroups
    source_key_count = int(outcomes["proposal_source_key"].nunique())
    checks = [
        check_ordered_schema(outcomes, schema_columns),
        {
            "check_name": "row_count",
            "passed": len(outcomes) == expected_rows,
            "details": f"rows={len(outcomes)} expected={expected_rows}",
        },
        partition_check,
        {
            "check_name": "source_intervention_units",
            "passed": unit_count == expected_units,
            "details": f"units={unit_count} expected={expected_units}",
        },
        {
            "check_name": "distinct_proposal_source_keys",
            "passed": source_key_count == expected_distinct_keys,
            "details": f"source_keys={source_key_count} expected={expected_distinct_keys}",
        },
        _check_replicate_coverage(outcomes, expected_replicates, expected_units),
        check_source_identity(outcomes, provenance),
        check_matched_pair_ids(outcomes),
        seed_result.check,
        _check_provenance(provenance),
    ]
    all_checks_passed = all(bool(check["passed"]) for check in checks)
    check_status = {
        str(check["check_name"]): bool(check["passed"]) for check in checks
    }
    summary = {
        "all_checks_passed": all_checks_passed,
        "row_count": int(len(outcomes)),
        "column_count": int(len(outcomes.columns)),
        "expected_replicates": expected_replicates,
        "replicate_ids": f"0..{expected_replicates - 1}",
        "source_intervention_units": unit_count,
        "expected_source_intervention_units": expected_units,
        "distinct_proposal_source_keys": source_key_count,
        "expected_distinct_proposal_source_keys": expected_distinct_keys,
        "partition_row_counts": {
            str(key): int(value)
            for key, value in labels.value_counts().sort_index().to_dict().items()
        },
        "expected_partition_row_counts": expected_partition_rows,
        "seed_mismatches": seed_result.mismatch_count,
        "source_identity": bool(check_status.get("source_identity", False)),
        "replicate_coverage": bool(check_status.get("replicate_coverage", False)),
        "matched_pair_ids": bool(check_status.get("matched_pair_ids", False)),
        "schema_columns": bool(check_status.get("schema_columns", False)),
        "production_attribution": bool(provenance.get("production_attribution")),
        "status": provenance.get("status"),
        "run_id": provenance.get("run_id"),
        "inspected_at": datetime.now(timezone.utc).isoformat(),
        "rehearsal_dir": rehearsal_dir.as_posix(),
        "outcome_schema_path": outcome_schema_path.as_posix(),
    }

    summary_path = inspection_dir / "inspection_summary.json"
    checks_path = inspection_dir / "inspection_checks.csv"
    report_path = inspection_dir / "inspection_report.md"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(checks).to_csv(checks_path, index=False)
    _write_report(report_path, summary, checks)
    return RehearsalInspectionResult(
        all_checks_passed=all_checks_passed,
        inspection_dir=inspection_dir,
        summary_path=summary_path,
        checks_path=checks_path,
        report_path=report_path,
    )
