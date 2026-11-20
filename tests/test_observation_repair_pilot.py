"""Tiny real-kernel control parity and independent validation contracts."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galaxias_model.calibration import run_module3_calibration
from galaxias_model.io import load_model_inputs
from galaxias_model.types import Module3Config

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("repair_pilot", ROOT / "scripts/run_observation_repair_pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def test_tiny_legacy_parity_shared_histories_and_validation(tmp_path):
    out = tmp_path / "pilot"
    family, seed = "persistent_joint_cause", 20260908
    manifest = pilot.run_pilot(out, families=(family,), seeds=(seed,), draws=2, keep=1, stage_b_replicates=2, validation_replicates=3)
    original = run_module3_calibration(load_model_inputs(ROOT / "data"), Module3Config(families=(family,), master_seed=seed, stage_a_draws_per_family=2, stage_a_keep_per_family=1, stage_b_historical_replicates=2, output_dir=tmp_path / "original"))
    ours = pd.read_csv(out / "stage_b_source_summary.csv")
    legacy = ours.loc[(ours.profile == "baseline_current") & ours.stage_a_retained].set_index("proposal_id")
    expected = original.proposal_summary_table.set_index("proposal_id").loc[legacy.index]
    for ours_col, original_col in [("overall_distance", "stochastic_overall_distance_median"), ("historical_distance", "stochastic_historical_core_distance_median"), ("intrinsic_distance", "stochastic_intrinsic_baseline_distance_median"), ("historical_iqr", "stochastic_historical_core_distance_iqr")]:
        np.testing.assert_allclose(legacy[ours_col], expected[original_col], rtol=1e-10, atol=1e-10)
    assert set(legacy.loc[legacy.selected].index) == set(original.accepted_proposals_table.proposal_id)
    assert set(legacy.index) == set(original.target_scores_table.loc[original.target_scores_table.stage == "stage_b"].proposal_id)
    b = pd.read_csv(out / "stage_b_replicates.csv.gz")
    v = pd.read_csv(out / "validation_replicates.csv.gz")
    assert not set(b.simulation_seed) & set(v.simulation_seed)
    assert not b.duplicated([*pilot.IDENTITY, "replicate_index"]).any()
    assert "profile" not in b
    assert ours.groupby(pilot.IDENTITY).size().eq(4).all()
    validation = pd.read_csv(out / "validation_source_summary.csv")
    assert pilot.membership_set(validation, "selected") == pilot.membership_set(ours, "selected")
    assert validation.groupby(pilot.IDENTITY).replicate_count.first().eq(3).all()
    with pytest.raises(ValueError, match="never select"):
        pilot.select_sources(validation)
    with pytest.raises(FileExistsError):
        pilot.run_pilot(out, families=(family,), seeds=(seed,), draws=2, keep=1, stage_b_replicates=2, validation_replicates=3)
    assert manifest["counts"]["deterministic_intrinsic_runs"] == 4
    assert all(pilot.file_hash(out / name) == binding for name, binding in manifest["outputs"].items())


def test_validation_seed_namespace_is_disjoint_at_pilot_budgets():
    seeds = {phase: {pilot.phase_seed(s, family, proposal, rep, phase)
                     for s in [20260908, 20260909] for family in pilot.DEFAULT_FAMILY_ORDER
                     for proposal in range(1, 101) for rep in range(1, reps + 1)}
             for phase, reps in [("stage_b", 20), ("validation", 100)]}
    assert len(seeds["stage_b"]) == 20000
    assert len(seeds["validation"]) == 100000
    assert not seeds["stage_b"] & seeds["validation"]


def test_no_sampled_positive_support_is_preserved_but_not_repair_eligible():
    raw = pd.DataFrame([{ "search_seed": 1, "family_id": "persistent_joint_cause", "proposal_id": "a", "stage": "stage_a", "replicate_index": 0, "simulation_seed": 1,
                          "positive_records_compatible": False, "nondetection_occupied_episodes": 0,
                          **{f"{t}_weighted_penalty": 0. for t in pilot.TARGETS}}])
    summary = pilot.select_sources(pilot.source_summaries(raw), stage_a_keep=1)
    repair = summary.loc[summary.profile != "baseline_current"]
    assert len(repair) == 3
    assert not repair.sample_supported.any()
    assert np.isinf(repair.late_discrepancy).all()
    assert not repair.stage_a_retained.any()
    assert summary.loc[summary.profile == "baseline_current", "stage_a_retained"].all()
