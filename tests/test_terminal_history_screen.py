"""Frozen-input, censoring, and phase-independence checks for fresh histories."""
from pathlib import Path
import importlib.util
from types import SimpleNamespace
import shutil

import numpy as np
import pandas as pd
import pytest

spec = importlib.util.spec_from_file_location("terminal_screen", Path(__file__).resolve().parents[1] / "scripts/run_terminal_history_screen.py")
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)
pilot = screen.pilot


def test_phase_namespaces_are_disjoint_for_all_frozen_sources_to_2500():
    identities = [(s, f, i) for s in [20260908, 20260909] for f in pilot.DEFAULT_FAMILY_ORDER for i in range(1, 101)]
    new = np.concatenate([screen.source_seeds(s, f, i, 2500, phase) for s, f, i in identities for phase in screen.PHASE_CODES])
    assert len(new) == 7500000
    ordered = np.sort(new)
    assert not np.any(np.diff(ordered) == 0)
    old = np.array([pilot.phase_seed(s, f, i, rep, phase) for s, f, i in identities for phase, count in [("stage_b", 20), ("validation", 100)] for rep in range(1, count + 1)])
    assert not np.intersect1d(new, old).size
    for phase in screen.PHASE_CODES:
        vector = screen.source_seeds(20260908, pilot.DEFAULT_FAMILY_ORDER[0], 1, 2500, phase)
        assert vector.tolist() == [screen.phase_seed(20260908, pilot.DEFAULT_FAMILY_ORDER[0], 1, rep, phase) for rep in range(1, 2501)]


def test_terminal_events_and_censoring_preserve_1996_proxy_distinction():
    year = np.arange(1987, 2003)
    total = np.where(year < 1996, 10., 0.)
    trajectory = pd.DataFrame({"year": year, "N_total": total, "N_L": total / 2, "N_R": total / 2})
    projected = screen.terminal_features(SimpleNamespace(trajectory_table=trajectory))
    assert projected["present_at_1996_proxy"] and not projected["surviving_1996"]
    assert projected["positive_and_extinct_by_2002"]
    assert projected["positive_and_all_natural_nondetections_empty"]
    assert not projected["positive_and_all_nondetections_empty"]
    assert projected["latent_last_presence_year"] == 1995
    assert projected["first_zero_year"] == 1996
    trajectory[["N_total", "N_L", "N_R"]] = [10., 5., 5.]
    censored = screen.terminal_features(SimpleNamespace(trajectory_table=trajectory))
    assert np.isnan(censored["first_zero_year"])
    assert censored["latent_last_presence_year"] == 2002
    assert not censored["extinct_by_2002"]


def test_tiny_phases_reuse_frozen_inputs_and_reject_tampering(tmp_path):
    original = tmp_path / "original"
    pilot.run_pilot(original, families=("persistent_joint_cause",), seeds=(20260908,), draws=2, keep=1, stage_b_replicates=2, validation_replicates=2)
    original_hash = pilot.file_hash(original / "parameter_values.csv.gz")
    first = tmp_path / "screen"
    receipt = screen.run_phase(original, first, "screen", replicates=2)
    assert receipt["counts"]["simulated_sources"] == 2
    assert receipt["counts"]["deterministic_runs"] == 0
    sources = pd.read_csv(first / "sources.csv")
    raw = pd.read_csv(first / "raw_replicates.csv.gz")
    original_det = pd.read_csv(original / "deterministic_projections.csv.gz").set_index(pilot.IDENTITY)
    for identity, group in raw.groupby(pilot.IDENTITY):
        for target in ["CT011", "CT012"]:
            np.testing.assert_allclose(group[f"{target}_weighted_penalty"], original_det.loc[identity, f"{target}_weighted_penalty"])
    frozen = tmp_path / "selection.csv"
    sources[pilot.IDENTITY].head(1).to_csv(frozen, index=False)
    confirmation = tmp_path / "confirm"
    screen.run_phase(original, confirmation, "confirm", selection_file=frozen, replicates=2, prior_phase_dirs=[first])
    confirmed = pd.read_csv(confirmation / "raw_replicates.csv.gz")
    assert len(confirmed) == 2 and not set(raw.simulation_seed) & set(confirmed.simulation_seed)
    assert pilot.file_hash(original / "parameter_values.csv.gz") == original_hash
    assert "selected" not in pd.read_csv(confirmation / "source_summary.csv")
    damaged = tmp_path / "damaged_original"
    shutil.copytree(original, damaged)
    with (damaged / "parameter_values.csv.gz").open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(ValueError, match="hash mismatch"):
        screen.run_phase(damaged, tmp_path / "must_not_run", "screen", replicates=1)
    assert not (tmp_path / "must_not_run").exists()
    with pytest.raises(ValueError, match="already exists"):
        screen.run_phase(original, first, "screen", replicates=1)
