from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from galaxias_model.module5_counterfactual import run_module5_real_proposal_dry_run
from galaxias_model.module5_dry_run_inspect import inspect_module5_real_proposal_dry_run
from galaxias_model.module5_proposals import (
    APPROVED_DRY_RUN_PROPOSAL_IDS,
    APPROVED_DRY_RUN_PROPOSALS,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MEMBERSHIP = DATA_DIR / "module4_5_proposal_set_membership.csv"
MANIFEST = DATA_DIR / "module4_raw_artifact_manifest.csv"
PARAMETER_VALUES = (
    ROOT
    / "outputs/remote/module4_observation_sensitivity_20260522T101942Z/"
    / "baseline_current_seed20260410/parameter_values.csv.gz"
)
INTERVENTIONS = DATA_DIR / "module5_counterfactual_interventions.csv"
OUTCOME_SCHEMA = DATA_DIR / "module5_counterfactual_outcome_schema.csv"


def _write_dry_run(output_dir: Path) -> None:
    run_module5_real_proposal_dry_run(
        data_dir=DATA_DIR,
        proposal_membership_path=MEMBERSHIP,
        module4_manifest_path=MANIFEST,
        parameter_values_path=PARAMETER_VALUES,
        interventions_path=INTERVENTIONS,
        outcome_schema_path=OUTCOME_SCHEMA,
        output_dir=output_dir,
        replicates=5,
        stochastic=True,
    )


def test_inspect_real_proposal_dry_run_writes_review_bundle_from_disk(tmp_path: Path) -> None:
    dry_run_dir = tmp_path / "module5_dry_run_baseline_current_20260410"
    _write_dry_run(dry_run_dir)

    result = inspect_module5_real_proposal_dry_run(
        dry_run_dir=dry_run_dir,
        interventions_path=INTERVENTIONS,
        outcome_schema_path=OUTCOME_SCHEMA,
    )

    assert result.all_checks_passed
    assert result.inspection_dir == dry_run_dir / "inspection"
    assert result.summary_path.exists()
    assert result.checks_path.exists()
    assert result.report_path.exists()

    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert summary["all_checks_passed"] is True
    assert summary["row_count"] == 65
    assert summary["proposal_count"] == 5
    assert summary["proposal_source_key_count"] == 5
    assert summary["intervention_count"] == 13
    assert summary["expected_replicates"] == 5
    assert summary["source_identity"] is True
    assert summary["replicate_coverage"] is True
    assert set(summary["proposal_ids"]) == set(APPROVED_DRY_RUN_PROPOSAL_IDS)

    checks = pd.read_csv(result.checks_path)
    assert set(checks["check_name"]) == {
        "schema_columns",
        "row_count",
        "proposal_ids",
        "intervention_ids",
        "replicate_coverage",
        "source_identity",
        "matched_pair_ids",
        "common_random_seed_pairing",
        "provenance_labels",
        "dry_run_boundary",
    }
    assert checks["passed"].all()
    report = result.report_path.read_text(encoding="utf-8")
    assert "not production attribution" in report
    assert "not manuscript evidence" in report


def test_inspect_real_proposal_dry_run_detects_broken_seed_pairing(tmp_path: Path) -> None:
    dry_run_dir = tmp_path / "module5_dry_run_baseline_current_20260410"
    _write_dry_run(dry_run_dir)
    outcomes_path = dry_run_dir / "matched_outcomes.csv"
    frame = pd.read_csv(outcomes_path)
    frame.loc[0, "intervention_stochastic_seed"] = frame.loc[0, "baseline_stochastic_seed"] + 100
    frame.to_csv(outcomes_path, index=False)

    result = inspect_module5_real_proposal_dry_run(
        dry_run_dir=dry_run_dir,
        interventions_path=INTERVENTIONS,
        outcome_schema_path=OUTCOME_SCHEMA,
    )

    assert not result.all_checks_passed
    checks = pd.read_csv(result.checks_path).set_index("check_name")
    assert not bool(checks.loc["common_random_seed_pairing", "passed"])
    assert "seed mismatches=1" in checks.loc["common_random_seed_pairing", "details"]


def test_inspect_real_proposal_dry_run_detects_broken_replicate_coverage(tmp_path: Path) -> None:
    dry_run_dir = tmp_path / "module5_dry_run_baseline_current_20260410"
    _write_dry_run(dry_run_dir)
    outcomes_path = dry_run_dir / "matched_outcomes.csv"
    frame = pd.read_csv(outcomes_path)
    target = frame.loc[
        frame["intervention_id"] == "m5_persistent_joint_cause_status_quo"
    ].index[-1]
    frame.loc[target, "stochastic_replicate_id"] = 0
    frame.to_csv(outcomes_path, index=False)

    result = inspect_module5_real_proposal_dry_run(
        dry_run_dir=dry_run_dir,
        interventions_path=INTERVENTIONS,
        outcome_schema_path=OUTCOME_SCHEMA,
    )

    assert not result.all_checks_passed
    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert summary["row_count"] == 65
    assert summary["replicate_coverage"] is False
    checks = pd.read_csv(result.checks_path).set_index("check_name")
    assert not bool(checks.loc["replicate_coverage", "passed"])
    details = checks.loc["replicate_coverage", "details"]
    assert "m5_persistent_joint_cause_status_quo" in details
    assert "replicate_ids" in details


def test_inspect_real_proposal_dry_run_detects_blank_source_identity(tmp_path: Path) -> None:
    dry_run_dir = tmp_path / "module5_dry_run_baseline_current_20260410"
    _write_dry_run(dry_run_dir)
    outcomes_path = dry_run_dir / "matched_outcomes.csv"
    frame = pd.read_csv(outcomes_path)
    assert "proposal_source_key" in frame.columns
    frame.loc[0, "proposal_source_key"] = ""
    frame.to_csv(outcomes_path, index=False)

    result = inspect_module5_real_proposal_dry_run(
        dry_run_dir=dry_run_dir,
        interventions_path=INTERVENTIONS,
        outcome_schema_path=OUTCOME_SCHEMA,
    )

    assert not result.all_checks_passed
    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert summary["source_identity"] is False
    checks = pd.read_csv(result.checks_path).set_index("check_name")
    assert not bool(checks.loc["source_identity", "passed"])
    assert "blank_source_keys=1" in checks.loc["source_identity", "details"]


def test_inspect_real_proposal_dry_run_detects_source_identity_collision(tmp_path: Path) -> None:
    dry_run_dir = tmp_path / "module5_dry_run_baseline_current_20260410"
    _write_dry_run(dry_run_dir)
    outcomes_path = dry_run_dir / "matched_outcomes.csv"
    frame = pd.read_csv(outcomes_path)
    source_columns = [
        "proposal_source_key",
        "module4_run_id",
        "variant_id",
        "seed",
        "run_dir_name",
        "family_id",
        "proposal_id",
        "intervention_id",
        "stochastic_replicate_id",
    ]
    assert set(source_columns).issubset(frame.columns)

    source = frame.iloc[0]
    target_index = frame.index[1]
    for column in source_columns:
        frame.loc[target_index, column] = source[column]
    frame.to_csv(outcomes_path, index=False)

    result = inspect_module5_real_proposal_dry_run(
        dry_run_dir=dry_run_dir,
        interventions_path=INTERVENTIONS,
        outcome_schema_path=OUTCOME_SCHEMA,
    )

    assert not result.all_checks_passed
    checks = pd.read_csv(result.checks_path).set_index("check_name")
    assert not bool(checks.loc["source_identity", "passed"])
    details = checks.loc["source_identity", "details"]
    assert "duplicate_source_intervention_replicates=1" in details


def test_inspect_real_proposal_dry_run_detects_wrong_family_proposal_mapping(tmp_path: Path) -> None:
    dry_run_dir = tmp_path / "module5_dry_run_baseline_current_20260410"
    _write_dry_run(dry_run_dir)
    outcomes_path = dry_run_dir / "matched_outcomes.csv"
    frame = pd.read_csv(outcomes_path)
    proposal_by_family = dict(APPROVED_DRY_RUN_PROPOSALS)
    mask = frame["intervention_id"] == "m5_persistent_joint_cause_status_quo"
    frame.loc[mask, "proposal_id"] = proposal_by_family["climbing_only"]
    frame.to_csv(outcomes_path, index=False)

    result = inspect_module5_real_proposal_dry_run(
        dry_run_dir=dry_run_dir,
        interventions_path=INTERVENTIONS,
        outcome_schema_path=OUTCOME_SCHEMA,
    )

    assert not result.all_checks_passed
    checks = pd.read_csv(result.checks_path).set_index("check_name")
    assert bool(checks.loc["proposal_ids", "passed"])
    assert not bool(checks.loc["replicate_coverage", "passed"])
    details = checks.loc["replicate_coverage", "details"]
    assert "m5_persistent_joint_cause_status_quo" in details
    assert "expected_proposal" in details
