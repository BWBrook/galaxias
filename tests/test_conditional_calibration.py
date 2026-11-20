"""Focused contracts for the bounded conditional-calibration runner."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("conditional_calibration", ROOT / "scripts" / "run_conditional_calibration.py")
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)
pilot = runner.pilot


def test_fresh_phase_seed_vector_matches_scalar_derivation_and_codes() -> None:
    for phase, code in runner.PHASE_CODES.items():
        vector = runner.source_seeds(20260912, "persistent_joint_cause", 17, 40, phase)
        scalar = [runner.phase_seed(20260912, "persistent_joint_cause", 17, rep, phase) for rep in range(1, 41)]
        assert vector.tolist() == scalar
        assert runner.PHASE_CODES[phase] == code
    assert len(np.unique(np.concatenate([
        runner.source_seeds(20260912, "persistent_joint_cause", 17, 40, phase)
        for phase in runner.PHASE_CODES
    ]))) == 120


def test_seed_preflight_rejects_an_earlier_history_collision(tmp_path: Path) -> None:
    sources = pd.DataFrame([{
        "search_seed": 20260912,
        "family_id": "persistent_joint_cause",
        "proposal_id": "persistent_joint_cause:p00001",
        "proposal_index": 1,
    }])
    old = tmp_path / "old.csv"
    old_seed = int(runner.source_seeds(20260912, "persistent_joint_cause", 1, 1, "screen")[0])
    pd.DataFrame({"simulation_seed": [old_seed]}).to_csv(old, index=False)
    with pytest.raises(ValueError, match="earlier history"):
        runner.preflight_seed_plan(sources, {"screen": 1}, old_seed_files=[old])


def test_terminal_features_keep_right_censored_event_year() -> None:
    years = np.arange(1987, 2003)
    total = np.full(len(years), 10.0)
    trajectory = pd.DataFrame({"year": years, "N_total": total, "N_L": total / 2, "N_R": total / 2})
    features = runner.terminal_screen.terminal_features(SimpleNamespace(trajectory_table=trajectory))
    assert features["surviving_2002"]
    assert np.isnan(features["first_zero_year"])
    assert features["latent_last_presence_year"] == 2002


def test_prior_is_sampling_plus_two_intrinsic_runs_and_roundtrips(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_historical(*args, **kwargs):
        raise AssertionError("prior must not run historical simulations")

    monkeypatch.setattr(runner, "run_historical_simulation", fail_if_historical)
    output = tmp_path / "prior"
    manifest = runner.run_prior(
        output,
        families=("persistent_joint_cause",),
        seeds=(20260912,),
        draws=2,
        workers=1,
    )
    assert manifest["counts"] == {
        "prior_sources": 2,
        "parameter_rows": 80,
        "historical_runs": 0,
        "deterministic_runs": 4,
    }
    parameters = pd.read_csv(output / "parameter_values.csv.gz", float_precision="round_trip")
    assert parameters.groupby(runner.IDENTITY).size().eq(40).all()
    raw = pd.read_csv(output / "raw_replicates.csv.gz")
    assert set(raw.stage) == {"prior"}
    assert set(raw.scenario_id) == set(runner.INTRINSIC_SCENARIOS)
    assert runner.verify_archive(output, phase="prior")[0]["status"] == "complete"


def test_stochastic_phases_use_frozen_ids_without_reselection_or_mutation(tmp_path: Path) -> None:
    prior = tmp_path / "prior"
    runner.run_prior(
        prior,
        families=("persistent_joint_cause",),
        seeds=(20260912,),
        draws=2,
        workers=1,
    )
    parameter_hash = runner.file_hash(prior / "parameter_values.csv.gz")
    screen = tmp_path / "screen"
    screen_manifest = runner.run_phase(prior, screen, "screen", replicates=2, workers=1)
    assert screen_manifest["counts"]["simulated_sources"] == 2
    assert screen_manifest["counts"]["historical_runs"] == 4
    screen_sources = pd.read_csv(screen / "sources.csv")
    selection = tmp_path / "selection.csv"
    screen_sources[["source_id"]].head(1).to_csv(selection, index=False)
    refine = tmp_path / "refine"
    refine_manifest = runner.run_phase(
        prior,
        refine,
        "refine",
        source_ids=selection,
        replicates=2,
        workers=1,
        previous_phase_dirs=[screen],
    )
    assert refine_manifest["counts"]["simulated_sources"] == 1
    screen_raw = pd.read_csv(screen / "raw_replicates.csv.gz")
    refine_raw = pd.read_csv(refine / "raw_replicates.csv.gz")
    assert not set(screen_raw.simulation_seed) & set(refine_raw.simulation_seed)
    assert runner.file_hash(prior / "parameter_values.csv.gz") == parameter_hash
    assert "profile" in pd.read_csv(refine / "source_summary.csv").columns
    with pytest.raises(ValueError, match="already exists"):
        runner.run_phase(prior, screen, "screen", replicates=1, workers=1)
