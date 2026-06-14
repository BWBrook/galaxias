from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from galaxias_model.module5_counterfactual import REAL_DRY_RUN_STATUS
from galaxias_model.module5_proposals import (
    APPROVED_DRY_RUN_PROPOSALS,
    APPROVED_DRY_RUN_PROPOSAL_IDS,
    DEFAULT_DRY_RUN_OUTPUT_DIR,
    DEFAULT_DRY_RUN_REPLICATES,
    PROPOSAL_SOURCE_KEY_FIELDS,
    build_proposal_source_key,
)


DEFAULT_OUTCOME_SCHEMA_PATH = Path("data/module5_counterfactual_outcome_schema.csv")
DEFAULT_INTERVENTIONS_PATH = Path("data/module5_counterfactual_interventions.csv")
DEFAULT_INSPECTION_DIRNAME = "inspection"


@dataclass(frozen=True)
class DryRunInspectionResult:
    all_checks_passed: bool
    inspection_dir: Path
    summary_path: Path
    checks_path: Path
    report_path: Path


def _read_schema_columns(outcome_schema_path: Path) -> list[str]:
    return pd.read_csv(outcome_schema_path)["column_name"].astype(str).tolist()


def _read_intervention_contract(interventions_path: Path) -> tuple[list[str], dict[str, str]]:
    interventions = pd.read_csv(interventions_path)
    missing = [column for column in ("intervention_id", "family_id") if column not in interventions.columns]
    if missing:
        raise ValueError(f"Intervention contract missing columns: {missing}")
    intervention_ids = interventions["intervention_id"].astype(str).tolist()
    family_by_intervention = dict(
        zip(
            interventions["intervention_id"].astype(str),
            interventions["family_id"].astype(str),
        )
    )
    return intervention_ids, family_by_intervention


def _load_inputs(dry_run_dir: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    outcomes_path = dry_run_dir / "matched_outcomes.csv"
    provenance_path = dry_run_dir / "provenance.json"
    if not outcomes_path.exists():
        raise FileNotFoundError(f"Missing Module 5 dry-run output: {outcomes_path}")
    if not provenance_path.exists():
        raise FileNotFoundError(f"Missing Module 5 dry-run provenance: {provenance_path}")
    return pd.read_csv(outcomes_path, keep_default_na=False), json.loads(
        provenance_path.read_text(encoding="utf-8")
    )


def _check_schema_columns(outcomes: pd.DataFrame, schema_columns: list[str]) -> dict[str, object]:
    actual = list(outcomes.columns)
    missing = [column for column in schema_columns if column not in actual]
    extra = [column for column in actual if column not in schema_columns]
    same_order = actual == schema_columns
    return {
        "check_name": "schema_columns",
        "passed": not missing and not extra and same_order,
        "details": f"rows={len(outcomes)} columns={len(actual)} missing={missing} extra={extra} same_order={same_order}",
    }


def _check_row_count(outcomes: pd.DataFrame, expected_count: int) -> dict[str, object]:
    return {
        "check_name": "row_count",
        "passed": len(outcomes) == expected_count,
        "details": f"rows={len(outcomes)} expected={expected_count}",
    }


def _check_proposal_ids(outcomes: pd.DataFrame) -> dict[str, object]:
    actual = set(outcomes["proposal_id"].astype(str)) if "proposal_id" in outcomes else set()
    expected = set(APPROVED_DRY_RUN_PROPOSAL_IDS)
    return {
        "check_name": "proposal_ids",
        "passed": actual == expected,
        "details": f"proposal_ids={sorted(actual)} expected={sorted(expected)}",
    }


def _check_intervention_ids(outcomes: pd.DataFrame, expected_ids: list[str]) -> dict[str, object]:
    actual = set(outcomes["intervention_id"].astype(str)) if "intervention_id" in outcomes else set()
    expected = set(expected_ids)
    return {
        "check_name": "intervention_ids",
        "passed": actual == expected,
        "details": f"intervention_ids={sorted(actual)} expected={sorted(expected)}",
    }


def _replicate_counts(group: pd.DataFrame) -> tuple[dict[int, int], list[str]]:
    replicate_values = pd.to_numeric(group["stochastic_replicate_id"], errors="coerce")
    invalid_values = [
        str(raw)
        for raw, value in zip(group["stochastic_replicate_id"], replicate_values)
        if pd.isna(value) or not float(value).is_integer()
    ]
    valid_replicates = replicate_values.dropna()
    valid_replicates = valid_replicates.loc[valid_replicates.map(lambda value: float(value).is_integer())]
    counts = valid_replicates.astype(int).value_counts().sort_index().to_dict()
    return {int(replicate_id): int(count) for replicate_id, count in counts.items()}, invalid_values


def _check_replicate_coverage(
    outcomes: pd.DataFrame,
    expected_intervention_ids: list[str],
    family_by_intervention: dict[str, str],
    expected_replicates: int,
) -> dict[str, object]:
    required = ["intervention_id", "proposal_id", "stochastic_replicate_id"]
    missing_required = [column for column in required if column not in outcomes.columns]
    if missing_required:
        return {
            "check_name": "replicate_coverage",
            "passed": False,
            "details": f"missing required columns={missing_required}",
        }

    expected_replicate_ids = set(range(expected_replicates))
    expected_proposal_by_family = dict(APPROVED_DRY_RUN_PROPOSALS)
    actual_intervention_ids = outcomes["intervention_id"].astype(str)
    unexpected_interventions = sorted(set(actual_intervention_ids) - set(expected_intervention_ids))
    failures: list[str] = []

    if unexpected_interventions:
        failures.append(f"unexpected_interventions={unexpected_interventions}")

    for intervention_id in expected_intervention_ids:
        group = outcomes.loc[actual_intervention_ids == intervention_id]
        counts, invalid_values = _replicate_counts(group)
        actual_replicate_ids = set(counts)
        duplicate_counts = {
            replicate_id: count
            for replicate_id, count in counts.items()
            if count != 1
        }
        family_id = family_by_intervention.get(intervention_id, "")
        expected_proposal = expected_proposal_by_family.get(family_id, "")
        actual_proposals = sorted(group["proposal_id"].astype(str).unique())

        if (
            len(group) != expected_replicates
            or actual_replicate_ids != expected_replicate_ids
            or duplicate_counts
            or invalid_values
            or actual_proposals != [expected_proposal]
        ):
            failures.append(
                (
                    f"{intervention_id}: rows={len(group)} expected_rows={expected_replicates} "
                    f"replicate_ids={sorted(actual_replicate_ids)} expected_replicate_ids={sorted(expected_replicate_ids)} "
                    f"replicate_counts={duplicate_counts} invalid_replicates={invalid_values} "
                    f"family_id={family_id} expected_proposal={expected_proposal} actual_proposals={actual_proposals}"
                )
            )

    return {
        "check_name": "replicate_coverage",
        "passed": not failures,
        "details": (
            f"expected_replicates={expected_replicates}; all interventions covered"
            if not failures
            else "; ".join(failures)
        ),
    }


def _check_source_identity(outcomes: pd.DataFrame, provenance: dict[str, object]) -> dict[str, object]:
    required = [
        "proposal_source_key",
        *PROPOSAL_SOURCE_KEY_FIELDS,
        "intervention_id",
        "stochastic_replicate_id",
    ]
    missing_required = [column for column in required if column not in outcomes.columns]
    if missing_required:
        return {
            "check_name": "source_identity",
            "passed": False,
            "details": f"missing required columns={missing_required}",
        }

    source_keys = outcomes["proposal_source_key"].astype(str)
    blank_source_keys = int((source_keys.str.strip() == "").sum())

    expected_keys: list[str] = []
    key_errors: list[str] = []
    for index, row in outcomes.iterrows():
        try:
            expected_keys.append(
                build_proposal_source_key(
                    module4_run_id=row["module4_run_id"],
                    variant_id=row["variant_id"],
                    seed=row["seed"],
                    run_dir_name=row["run_dir_name"],
                    family_id=row["family_id"],
                    proposal_id=row["proposal_id"],
                )
            )
        except ValueError as exc:
            expected_keys.append("")
            key_errors.append(f"row={index}: {exc}")

    expected = pd.Series(expected_keys, index=outcomes.index, dtype="string")
    key_mismatches = int((source_keys != expected.astype(str)).sum())
    grain_counts = outcomes.groupby(
        ["proposal_source_key", "intervention_id", "stochastic_replicate_id"],
        dropna=False,
    ).size()
    duplicate_source_intervention_replicates = int((grain_counts > 1).sum())

    observed_source_keys = set(source_keys)
    provenance_source_keys = set(
        str(item) for item in provenance.get("selected_proposal_source_keys", [])
    )
    provenance_keys_match = provenance_source_keys == observed_source_keys
    provenance_fields_match = list(provenance.get("source_identity_fields", [])) == list(
        PROPOSAL_SOURCE_KEY_FIELDS
    )
    passed = (
        blank_source_keys == 0
        and key_mismatches == 0
        and duplicate_source_intervention_replicates == 0
        and not key_errors
        and provenance_keys_match
        and provenance_fields_match
    )

    return {
        "check_name": "source_identity",
        "passed": passed,
        "details": (
            f"source_keys={len(observed_source_keys)} blank_source_keys={blank_source_keys} "
            f"key_mismatches={key_mismatches} "
            f"duplicate_source_intervention_replicates={duplicate_source_intervention_replicates} "
            f"provenance_keys_match={provenance_keys_match} "
            f"provenance_fields_match={provenance_fields_match} "
            f"key_errors={key_errors[:3]}"
        ),
    }


def _check_matched_pair_ids(outcomes: pd.DataFrame) -> dict[str, object]:
    required = [
        "proposal_source_key",
        "intervention_id",
        "stochastic_replicate_id",
        "matched_pair_id",
        "run_id_baseline",
        "run_id_counterfactual",
    ]
    missing_required = [column for column in required if column not in outcomes.columns]
    if missing_required:
        return {
            "check_name": "matched_pair_ids",
            "passed": False,
            "details": f"missing required columns={missing_required}",
        }

    matched_pair_ids = outcomes["matched_pair_id"].astype(str)
    expected_matched_pair_ids = (
        outcomes["proposal_source_key"].astype(str)
        + "|"
        + outcomes["intervention_id"].astype(str)
        + "|r"
        + outcomes["stochastic_replicate_id"].astype(str)
    )
    duplicate_count = int(matched_pair_ids.duplicated().sum())
    blank_count = int((matched_pair_ids.str.strip() == "").sum())
    source_context_mismatches = int((matched_pair_ids != expected_matched_pair_ids).sum())
    baseline_id_mismatches = int(
        (
            outcomes["run_id_baseline"].astype(str)
            != expected_matched_pair_ids + "|baseline"
        ).sum()
    )
    counterfactual_id_mismatches = int(
        (
            outcomes["run_id_counterfactual"].astype(str)
            != expected_matched_pair_ids + "|counterfactual"
        ).sum()
    )
    same_run_id_count = int(
        (
            outcomes["run_id_baseline"].astype(str)
            == outcomes["run_id_counterfactual"].astype(str)
        ).sum()
    )
    return {
        "check_name": "matched_pair_ids",
        "passed": (
            duplicate_count == 0
            and blank_count == 0
            and same_run_id_count == 0
            and source_context_mismatches == 0
            and baseline_id_mismatches == 0
            and counterfactual_id_mismatches == 0
        ),
        "details": (
            f"unique_pairs={matched_pair_ids.nunique()} duplicate_pairs={duplicate_count} "
            f"blank_pairs={blank_count} same_run_ids={same_run_id_count} "
            f"source_context_mismatches={source_context_mismatches} "
            f"baseline_id_mismatches={baseline_id_mismatches} "
            f"counterfactual_id_mismatches={counterfactual_id_mismatches}"
        ),
    }


def _check_seed_pairing(outcomes: pd.DataFrame) -> dict[str, object]:
    required = ["baseline_stochastic_seed", "intervention_stochastic_seed"]
    missing_required = [column for column in required if column not in outcomes.columns]
    if missing_required:
        return {
            "check_name": "common_random_seed_pairing",
            "passed": False,
            "details": f"missing required columns={missing_required}",
        }

    baseline = outcomes["baseline_stochastic_seed"].astype(str)
    intervention = outcomes["intervention_stochastic_seed"].astype(str)
    mismatch_count = int((baseline != intervention).sum())
    return {
        "check_name": "common_random_seed_pairing",
        "passed": mismatch_count == 0,
        "details": f"seed mismatches={mismatch_count}",
    }


def _check_provenance_labels(provenance: dict[str, object]) -> dict[str, object]:
    status = provenance.get("status")
    production_attribution = provenance.get("production_attribution")
    selected = set(str(item) for item in provenance.get("selected_proposal_ids", []))
    expected = set(APPROVED_DRY_RUN_PROPOSAL_IDS)
    output_file = str(provenance.get("output_file", ""))
    passed = (
        status == REAL_DRY_RUN_STATUS
        and production_attribution is False
        and selected == expected
        and output_file.endswith("matched_outcomes.csv")
    )
    return {
        "check_name": "provenance_labels",
        "passed": passed,
        "details": (
            f"status={status} production_attribution={production_attribution} "
            f"selected={sorted(selected)} output_file={output_file}"
        ),
    }


def _check_dry_run_boundary(outcomes: pd.DataFrame, provenance: dict[str, object]) -> dict[str, object]:
    note = str(provenance.get("boundary_note", "")).lower()
    variant_ok = "variant_id" in outcomes.columns and set(outcomes["variant_id"].astype(str)) == {"baseline_current"}
    proposal_ok = (
        "proposal_id" in outcomes.columns
        and not outcomes["proposal_id"].astype(str).str.startswith("smoke_default:").any()
    )
    language_ok = "not production attribution" in note and "not manuscript evidence" in note
    return {
        "check_name": "dry_run_boundary",
        "passed": bool(variant_ok and proposal_ok and language_ok),
        "details": (
            f"variant_baseline_current={bool(variant_ok)} real_proposal_ids={bool(proposal_ok)} "
            f"boundary_language={language_ok}"
        ),
    }


def build_dry_run_inspection_checks(
    outcomes: pd.DataFrame,
    provenance: dict[str, object],
    schema_columns: list[str],
    expected_intervention_ids: list[str],
    expected_row_count: int,
    expected_replicates: int,
    family_by_intervention: dict[str, str],
) -> list[dict[str, object]]:
    return [
        _check_schema_columns(outcomes, schema_columns),
        _check_row_count(outcomes, expected_row_count),
        _check_proposal_ids(outcomes),
        _check_intervention_ids(outcomes, expected_intervention_ids),
        _check_replicate_coverage(
            outcomes,
            expected_intervention_ids,
            family_by_intervention,
            expected_replicates,
        ),
        _check_source_identity(outcomes, provenance),
        _check_matched_pair_ids(outcomes),
        _check_seed_pairing(outcomes),
        _check_provenance_labels(provenance),
        _check_dry_run_boundary(outcomes, provenance),
    ]


def _write_report(
    report_path: Path,
    summary: dict[str, object],
    checks: list[dict[str, object]],
) -> None:
    lines = [
        "# Module 5 Real-Proposal Dry-Run Inspection",
        "",
        "This report inspects emitted local dry-run files from disk. It is not production attribution and not manuscript evidence.",
        "",
        "## Summary",
        "",
        f"- all_checks_passed: `{summary['all_checks_passed']}`",
        f"- row_count: `{summary['row_count']}`",
        f"- proposal_count: `{summary['proposal_count']}`",
        f"- proposal_source_key_count: `{summary['proposal_source_key_count']}`",
        f"- intervention_count: `{summary['intervention_count']}`",
        f"- expected_replicates: `{summary['expected_replicates']}`",
        f"- source_identity: `{summary['source_identity']}`",
        f"- replicate_coverage: `{summary['replicate_coverage']}`",
        f"- matched_pair_count: `{summary['matched_pair_count']}`",
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


def inspect_module5_real_proposal_dry_run(
    dry_run_dir: Path = DEFAULT_DRY_RUN_OUTPUT_DIR,
    interventions_path: Path = DEFAULT_INTERVENTIONS_PATH,
    outcome_schema_path: Path = DEFAULT_OUTCOME_SCHEMA_PATH,
    inspection_dir: Path | None = None,
    expected_replicates: int = DEFAULT_DRY_RUN_REPLICATES,
) -> DryRunInspectionResult:
    dry_run_dir = dry_run_dir.resolve()
    interventions_path = interventions_path.resolve()
    outcome_schema_path = outcome_schema_path.resolve()
    inspection_dir = (inspection_dir or dry_run_dir / DEFAULT_INSPECTION_DIRNAME).resolve()
    inspection_dir.mkdir(parents=True, exist_ok=True)

    outcomes, provenance = _load_inputs(dry_run_dir)
    schema_columns = _read_schema_columns(outcome_schema_path)
    intervention_ids, family_by_intervention = _read_intervention_contract(interventions_path)
    expected_row_count = len(intervention_ids) * expected_replicates
    checks = build_dry_run_inspection_checks(
        outcomes,
        provenance,
        schema_columns,
        intervention_ids,
        expected_row_count,
        expected_replicates,
        family_by_intervention,
    )
    all_checks_passed = all(bool(check["passed"]) for check in checks)
    check_status = {str(check["check_name"]): bool(check["passed"]) for check in checks}
    summary = {
        "all_checks_passed": all_checks_passed,
        "row_count": int(len(outcomes)),
        "column_count": int(len(outcomes.columns)),
        "proposal_count": int(outcomes["proposal_id"].nunique()) if "proposal_id" in outcomes else 0,
        "proposal_ids": sorted(outcomes["proposal_id"].astype(str).unique()) if "proposal_id" in outcomes else [],
        "proposal_source_key_count": int(outcomes["proposal_source_key"].nunique())
        if "proposal_source_key" in outcomes
        else 0,
        "proposal_source_keys": sorted(outcomes["proposal_source_key"].astype(str).unique())
        if "proposal_source_key" in outcomes
        else [],
        "intervention_count": int(outcomes["intervention_id"].nunique()) if "intervention_id" in outcomes else 0,
        "expected_replicates": int(expected_replicates),
        "source_identity": bool(check_status.get("source_identity", False)),
        "replicate_coverage": bool(check_status.get("replicate_coverage", False)),
        "matched_pair_count": int(outcomes["matched_pair_id"].nunique()) if "matched_pair_id" in outcomes else 0,
        "source_dry_run_dir": dry_run_dir.as_posix(),
        "outcome_schema_path": outcome_schema_path.as_posix(),
        "interventions_path": interventions_path.as_posix(),
        "inspected_at": datetime.now(timezone.utc).isoformat(),
    }

    summary_path = inspection_dir / "inspection_summary.json"
    checks_path = inspection_dir / "inspection_checks.csv"
    report_path = inspection_dir / "inspection_report.md"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(checks).to_csv(checks_path, index=False)
    _write_report(report_path, summary, checks)

    return DryRunInspectionResult(
        all_checks_passed=all_checks_passed,
        inspection_dir=inspection_dir,
        summary_path=summary_path,
        checks_path=checks_path,
        report_path=report_path,
    )
