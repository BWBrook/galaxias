from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galaxias_model import (
    Module3Config,
    build_resolved_parameters_from_sample,
    inverse_transform_parameter_value,
    load_model_inputs,
    resolve_family_parameters,
    run_module3_calibration,
    run_module3_calibration_stage,
    sample_family_parameter_table,
    transform_parameter_value,
)
from galaxias_model.review import run_module3_5_diagnostic_review, run_module3_readiness_review
from galaxias_model.types import ModelInputs


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FAMILY_IDS = [
    "habitat_only_null",
    "trout_only",
    "climbing_only",
    "persistent_joint_cause",
    "transient_perfect_storm",
]


@pytest.fixture(scope="module")
def model_inputs() -> ModelInputs:
    return load_model_inputs(DATA_DIR)


def _small_config(output_dir: Path, workers: int = 1, resume: bool = False) -> Module3Config:
    return Module3Config(
        stage_a_draws_per_family=24,
        stage_a_keep_per_family=6,
        stage_b_historical_replicates=3,
        final_acceptance_fraction=0.10,
        final_acceptance_cap=5,
        workers=workers,
        batch_size=20,
        master_seed=20260410,
        stochastic_baselines=False,
        output_dir=output_dir,
        resume=resume,
    )


@pytest.mark.parametrize("family_id", FAMILY_IDS)
def test_sampling_respects_bounds_and_transform_roundtrip(model_inputs: ModelInputs, family_id: str) -> None:
    sampled = sample_family_parameter_table(model_inputs, family_id, np.random.default_rng(77), 3)
    priors = model_inputs.parameter_priors[["parameter_id", "lower_bound", "upper_bound"]].copy()
    merged = sampled.merge(priors, on="parameter_id", how="left")

    estimate_rows = merged.loc[merged["sampled_flag"]].copy()
    assert not estimate_rows.empty
    assert estimate_rows["value_natural"].notna().all()
    assert estimate_rows["value_sampling"].notna().all()
    assert (
        pd.to_numeric(estimate_rows["value_natural"], errors="coerce")
        >= pd.to_numeric(estimate_rows["lower_bound"], errors="coerce")
    ).all()
    assert (
        pd.to_numeric(estimate_rows["value_natural"], errors="coerce")
        <= pd.to_numeric(estimate_rows["upper_bound"], errors="coerce")
    ).all()

    for row in estimate_rows.to_dict(orient="records"):
        recovered = inverse_transform_parameter_value(float(row["value_sampling"]), str(row["sampling_transform"]))
        assert recovered == pytest.approx(float(row["value_natural"]))
        transformed = transform_parameter_value(float(row["value_natural"]), str(row["sampling_transform"]))
        assert transformed == pytest.approx(float(row["value_sampling"]))

    fixed_rows = merged.loc[~merged["sampled_flag"]].copy()
    assert fixed_rows["value_sampling"].isna().all()


def test_sampled_parameter_resolution_enforces_constraints(model_inputs: ModelInputs) -> None:
    default_params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    proposal = default_params.manifest[["parameter_id", "effective_value"]].rename(
        columns={"effective_value": "value_natural"}
    )
    resolved = build_resolved_parameters_from_sample(model_inputs, "transient_perfect_storm", proposal)
    assert len(resolved.values) == 40
    assert len(resolved.manifest) == 40

    broken = proposal.copy()
    broken.loc[broken["parameter_id"] == "PR020", "value_natural"] = 0.01
    broken.loc[broken["parameter_id"] == "PR021", "value_natural"] = 0.05
    with pytest.raises(ValueError, match="PC001"):
        build_resolved_parameters_from_sample(model_inputs, "transient_perfect_storm", broken)


def test_identical_seed_reproduces_sampling_table(model_inputs: ModelInputs) -> None:
    table_a = sample_family_parameter_table(model_inputs, "transient_perfect_storm", np.random.default_rng(88), 5)
    table_b = sample_family_parameter_table(model_inputs, "transient_perfect_storm", np.random.default_rng(88), 5)
    pd.testing.assert_frame_equal(table_a, table_b)


@pytest.mark.slow
@pytest.mark.integration
def test_module3_small_run_writes_outputs_and_finite_scores(model_inputs: ModelInputs, tmp_path: Path) -> None:
    output_dir = tmp_path / "module3_small"
    config = _small_config(output_dir, workers=1, resume=False)
    result = run_module3_calibration(model_inputs, config)

    assert len(result.proposal_summary_table) == len(FAMILY_IDS) * config.stage_a_draws_per_family
    assert (output_dir / "run_manifest.json").exists()
    assert (output_dir / "proposal_summary.csv.gz").exists()
    assert (output_dir / "parameter_values.csv.gz").exists()
    assert (output_dir / "target_scores.csv.gz").exists()
    assert (output_dir / "family_summary.csv").exists()
    assert (output_dir / "accepted_proposals.csv").exists()

    deterministic = result.proposal_summary_table.loc[
        result.proposal_summary_table["stage_status"].isin(
            {"stage_a_rejected", "stage_b_failed", "stage_b_rejected", "accepted"}
        )
    ].copy()
    assert np.isfinite(pd.to_numeric(deterministic["deterministic_overall_distance"], errors="coerce")).all()

    stage_b_valid = result.proposal_summary_table.loc[
        result.proposal_summary_table["stage_status"].isin({"stage_b_rejected", "accepted"})
    ].copy()
    assert not stage_b_valid.empty
    assert np.isfinite(pd.to_numeric(stage_b_valid["stochastic_overall_distance_median"], errors="coerce")).all()
    assert np.isfinite(pd.to_numeric(stage_b_valid["stochastic_historical_core_distance_iqr"], errors="coerce")).all()

    stage_a_targets = result.target_scores_table.loc[result.target_scores_table["stage"] == "stage_a"].copy()
    assert not stage_a_targets.empty
    assert (stage_a_targets["evaluation_status"] == "scored").all()


@pytest.mark.slow
@pytest.mark.integration
def test_parallel_workers_match_serial_accepted_ids(model_inputs: ModelInputs, tmp_path: Path) -> None:
    serial = run_module3_calibration(model_inputs, _small_config(tmp_path / "serial", workers=1))
    parallel = run_module3_calibration(model_inputs, _small_config(tmp_path / "parallel", workers=2))
    assert tuple(serial.accepted_proposals_table["proposal_id"].astype(str)) == tuple(
        parallel.accepted_proposals_table["proposal_id"].astype(str)
    )


@pytest.mark.slow
@pytest.mark.integration
def test_resume_matches_clean_final_accepted_set(model_inputs: ModelInputs, tmp_path: Path) -> None:
    resume_dir = tmp_path / "resume_case"
    stage_a_config = _small_config(resume_dir, workers=1, resume=False)
    run_module3_calibration_stage(model_inputs, stage_a_config, stage="stage_a")

    resumed = run_module3_calibration_stage(
        model_inputs,
        _small_config(resume_dir, workers=1, resume=True),
        stage="all",
    )
    clean = run_module3_calibration(model_inputs, _small_config(tmp_path / "clean_case", workers=1, resume=False))

    assert tuple(resumed.accepted_proposals_table["proposal_id"].astype(str)) == tuple(
        clean.accepted_proposals_table["proposal_id"].astype(str)
    )


@pytest.mark.slow
@pytest.mark.integration
def test_module3_readiness_review_runs_with_small_override(tmp_path: Path) -> None:
    config = _small_config(ROOT / "outputs" / "module3" / "test_readiness_primary", workers=1)
    repro_config = _small_config(ROOT / "outputs" / "module3" / "test_readiness_repro", workers=1)
    family_summary, accepted_summary, evaluation = run_module3_readiness_review(
        ROOT,
        config=config,
        repro_config=repro_config,
    )
    assert not family_summary.empty
    assert set(evaluation["gates"]).issuperset(
        {
            "sampler_valid_rate_pass",
            "screen_discrimination_pass",
            "stochastic_confirmation_finite_pass",
            "rank_consistency_pass",
            "accepted_set_nonempty_pass",
            "reproducibility_pass",
            "full_ready_for_module4",
            "needs_module_3_5",
        }
    )
    assert "proposal_id" in accepted_summary.columns


@pytest.mark.slow
@pytest.mark.integration
def test_module3_5_diagnostic_review_runs_with_small_override(tmp_path: Path) -> None:
    config = _small_config(tmp_path / "module3_5_diagnostic", workers=1)
    tables, evaluation = run_module3_5_diagnostic_review(ROOT, config=config)

    assert not tables["family_summary"].empty
    assert not tables["stage_b_frontier"].empty
    assert not tables["target_omission_sensitivity"].empty
    assert set(tables["target_omission_sensitivity"]["omission_label"]).issuperset(
        {"none", "late_terminal_block", "causal_mechanism_block"}
    )
    assert set(evaluation["metrics"]).issuperset(
        {"stage_b_valid_proposals", "accepted_count", "winning_family", "target_omission_flip_count"}
    )
    assert evaluation["recommended_next_step"]
