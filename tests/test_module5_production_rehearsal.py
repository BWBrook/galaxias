from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from galaxias_model.module5_proposals import derive_module5_seed
from galaxias_model.module5_execution_inspect import inspect_rehearsal_output
from galaxias_model.module5_rehearsal import (
    DEFAULT_REHEARSAL_REPLICATES,
    REHEARSAL_PARTITION_ROW_COUNTS,
    REHEARSAL_STATUS,
    build_rehearsal_plan,
    verify_required_parameter_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MEMBERSHIP = DATA_DIR / "module4_5_proposal_set_membership.csv"
MANIFEST = DATA_DIR / "module4_raw_artifact_manifest.csv"
INTERVENTIONS = DATA_DIR / "module5_counterfactual_interventions.csv"
OUTCOME_SCHEMA = DATA_DIR / "module5_counterfactual_outcome_schema.csv"


def test_rehearsal_plan_matches_goal012_counts() -> None:
    plan = build_rehearsal_plan(
        proposal_membership_path=MEMBERSHIP,
        interventions_path=INTERVENTIONS,
        module4_manifest_path=MANIFEST,
        replicates=DEFAULT_REHEARSAL_REPLICATES,
    )

    assert plan.replicates == 25
    assert plan.accepted_source_count_by_family() == {
        "climbing_only": 235,
        "persistent_joint_cause": 265,
        "transient_perfect_storm": 250,
    }
    assert plan.negative_reference_source_count_by_family() == {
        "habitat_only_null": 15,
        "trout_only": 15,
    }
    assert plan.source_context_count == 15
    assert len(plan.required_artifacts) == 15
    assert plan.partition_row_counts == REHEARSAL_PARTITION_ROW_COUNTS
    assert plan.source_intervention_unit_count == 2795
    assert plan.expected_row_count == 69875
    assert plan.distinct_proposal_source_key_count == 780
    assert REHEARSAL_STATUS == "module5_matched_counterfactual_execution"


def test_rehearsal_plan_keeps_bare_proposal_collisions_source_keyed() -> None:
    plan = build_rehearsal_plan(MEMBERSHIP, INTERVENTIONS, MANIFEST)
    duplicate_sources = [
        source
        for source in plan.distinct_sources
        if source.proposal_id == "climbing_only:p00005"
    ]
    assert len(duplicate_sources) == 2

    source_keys = [source.proposal_source_key for source in duplicate_sources]
    seeds = [
        derive_module5_seed(source_key, "m5_climbing_only_status_quo", 0)
        for source_key in source_keys
    ]
    matched_pair_ids = [
        f"{source_key}|m5_climbing_only_status_quo|r0"
        for source_key in source_keys
    ]

    assert len(set(source_keys)) == 2
    assert len(set(seeds)) == 2
    assert len(set(matched_pair_ids)) == 2


def test_required_artifact_resolution_verifies_real_local_manifest_files() -> None:
    plan = build_rehearsal_plan(MEMBERSHIP, INTERVENTIONS, MANIFEST)
    verified = verify_required_parameter_artifacts(plan.required_artifacts, root=ROOT)

    assert len(verified) == 15
    assert all(item.verified for item in verified)
    assert {item.context_key for item in verified} == {
        artifact.context_key for artifact in plan.required_artifacts
    }


def test_required_artifact_resolution_fails_on_hash_mismatch(tmp_path: Path) -> None:
    artifact = build_rehearsal_plan(MEMBERSHIP, INTERVENTIONS, MANIFEST).required_artifacts[0]
    fake = tmp_path / "parameter_values.csv.gz"
    fake.write_text("not the real artifact\n", encoding="utf-8")
    modified = artifact.with_paths(local_path=fake, expected_bytes=fake.stat().st_size)

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_required_parameter_artifacts((modified,), root=ROOT)


def _minimal_outcome_row(
    *,
    source_key: str,
    intervention_id: str,
    replicate_id: int,
    partition_label: str,
) -> dict[str, object]:
    (
        module4_run_id,
        variant_id,
        seed,
        run_dir_name,
        family_id,
        proposal_id,
    ) = source_key.split("|")
    matched_pair_id = f"{source_key}|{intervention_id}|r{replicate_id}"
    return {
        "partition_label": partition_label,
        "family_id": family_id,
        "family_role": "primary",
        "proposal_id": proposal_id,
        "proposal_source_key": source_key,
        "module4_run_id": module4_run_id,
        "variant_id": variant_id,
        "seed": int(seed),
        "run_dir_name": run_dir_name,
        "proposal_seed": 1,
        "stochastic_replicate_id": replicate_id,
        "intervention_id": intervention_id,
        "intervention_axis": "status_quo",
        "scenario_class": "headline",
        "matched_pair_id": matched_pair_id,
        "run_id_baseline": f"{matched_pair_id}|baseline",
        "run_id_counterfactual": f"{matched_pair_id}|counterfactual",
        "baseline_stochastic_seed": 1000 + replicate_id,
        "intervention_stochastic_seed": 1000 + replicate_id,
        "year": 2002,
        "N_total": 1.0,
        "N_lake": 1.0,
        "N_refuge": 0.0,
        "trout_pressure_legacy_index": 0.0,
        "climbing_pressure_legacy_index": 0.0,
        "extirpation_year_raw": 2003.0,
        "extirpation_year_contrast": 0.0,
        "persistence_2002_baseline": 1,
        "persistence_2002_counterfactual": 1,
        "persistence_2002_contrast": 0.0,
        "persistence_1996_baseline": 1,
        "persistence_1996_counterfactual": 1,
        "persistence_1996_contrast": 0.0,
        "min_abundance_1992_2002_baseline": 1.0,
        "min_abundance_1992_2002_counterfactual": 1.0,
        "min_abundance_1992_2002_contrast": 0.0,
        "lake_refuge_share_2002_baseline": 1.0,
        "lake_refuge_share_2002_counterfactual": 1.0,
        "lake_refuge_share_2002_contrast": 0.0,
        "uncertainty_n_replicates": 2,
        "uncertainty_extirpation_median": 0.0,
        "uncertainty_extirpation_ci_low": 0.0,
        "uncertainty_extirpation_ci_high": 0.0,
        "uncertainty_persistence_2002_delta_median": 0.0,
        "uncertainty_persistence_2002_ci_low": 0.0,
        "uncertainty_persistence_2002_ci_high": 0.0,
        "processing_timestamp": "2026-06-13T00:00:00+00:00",
        "provenance_source_file": "data/module5_counterfactual_interventions.csv",
        "provenance_git_sha": "test",
        "provenance_script": "scripts/run_module5_25rep_rehearsal.py",
        "provenance_module4_manifest": "data/module4_raw_artifact_manifest.csv",
    }


def test_rehearsal_inspector_detects_replicate_and_identity_failures(tmp_path: Path) -> None:
    source_key = (
        "module4_observation_sensitivity_20260522T101942Z|baseline_current|20260410|"
        "baseline_current_seed20260410|persistent_joint_cause|persistent_joint_cause:p00162"
    )
    rows = [
        _minimal_outcome_row(
            source_key=source_key,
            intervention_id="m5_persistent_joint_cause_status_quo",
            replicate_id=0,
            partition_label="headline/persistent_joint_cause",
        ),
        _minimal_outcome_row(
            source_key=source_key,
            intervention_id="m5_persistent_joint_cause_status_quo",
            replicate_id=0,
            partition_label="headline/persistent_joint_cause",
        ),
    ]
    out_dir = tmp_path / "rehearsal"
    out_dir.mkdir()
    pd.DataFrame(rows).to_csv(out_dir / "matched_outcomes.csv", index=False)
    (out_dir / "provenance.json").write_text(
        json.dumps(
            {
                "status": "module5_matched_counterfactual_execution",
                "production_attribution": False,
                "expected_replicates": 2,
                "expected_row_count": 2,
                "expected_source_intervention_units": 1,
                "expected_distinct_proposal_source_keys": 1,
                "expected_partition_row_counts": {
                    "headline/persistent_joint_cause": 2,
                },
                "selected_proposal_source_keys": [source_key],
                "source_identity_fields": [
                    "module4_run_id",
                    "variant_id",
                    "seed",
                    "run_dir_name",
                    "family_id",
                    "proposal_id",
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = inspect_rehearsal_output(
        rehearsal_dir=out_dir,
        outcome_schema_path=OUTCOME_SCHEMA,
        inspection_dir=out_dir / "inspection",
    )

    assert not result.all_checks_passed
    checks = pd.read_csv(result.checks_path).set_index("check_name")
    assert not bool(checks.loc["replicate_coverage", "passed"])
    assert not bool(checks.loc["source_identity", "passed"])
    assert bool(checks.loc["provenance_labels", "passed"])
