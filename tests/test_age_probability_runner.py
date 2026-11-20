import math
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from galaxias_model.age_joint_proposal import fit_joint_beta
from galaxias_model.age_sources import runner_arguments
from scripts.run_age_probability_gate import (
    broad_cells,
    early_conditioning,
    build_sources,
    partial_early_conditioning,
    run,
)


class _DeclaredFeatures(dict):
    """Feature mapping that fails if conditioning reaches outside E inputs."""

    _allowed = {"march", "creek_early", "creek_feb", "lake"}

    def __getitem__(self, key):
        if key not in self._allowed:
            raise AssertionError(f"early conditioning accessed undeclared field {key!r}")
        return super().__getitem__(key)


def _early_features(march_value=1.0, *, extra=None):
    values = _DeclaredFeatures(
        march=np.array([march_value]),
        creek_early=[[0.0, 68.0 / 43.0]] * 20,
        creek_feb=[0.0, 0.5],
        lake=[[1.0, 0.0]] * 8,
    )
    if extra:
        values.update(extra)
    return values


def test_early_conditioning_reads_only_declared_evidence_and_handles_march_gate():
    means = [1.0] * 8
    zero_march = _early_features(0.0, extra={"terminal_alive": True, "remaining": object()})
    zero = early_conditioning(zero_march, means)
    assert zero["total"] == -math.inf
    assert not zero["march_present"]

    positive_a = early_conditioning(
        _early_features(1.0, extra={"march_retention": False, "terminal_alive": False}), means
    )
    positive_b = early_conditioning(
        _early_features(17.0, extra={"march_retention": True, "terminal_alive": True}), means
    )
    assert positive_a["march_present"] and positive_b["march_present"]
    assert positive_a["total"] == pytest.approx(positive_b["total"])


def test_lake_and_creek_saturated_fixture_has_zero_early_score():
    result = early_conditioning(_early_features(), [1.0] * 8)
    assert result["lake"] == pytest.approx(0.0)
    assert result["creek"] == pytest.approx(0.0)
    assert result["total"] == pytest.approx(0.0)


def _partial_history():
    early_state = np.zeros((2, 2, 3), dtype=float)
    early_state[1, 0, 1] = 68.0 / 43.0
    february_state = np.zeros((2, 2, 3), dtype=float)
    february_state[1, 0, 1] = 0.5
    march_state = np.zeros((2, 2, 3), dtype=float)
    march_state[1, 0, 0] = 1.0
    checkpoints = [
        {"label": f"early_refuge_{index:02d}", "state": early_state}
        for index in range(20)
    ]
    checkpoints.extend([
        {"label": "february_1992_capture", "state": february_state},
        {"label": "march_1996_record", "state": march_state},
    ])
    annual = {
        year: np.array([[[1.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
                        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]])
        for year in (1976, 1977, 1978, 1979, 1980, 1983, 1986, 1989)
    }
    annual[2002] = annual[1976].copy()
    return {
        "annual_states": {"pedder": annual},
        "checkpoint_states": {"pedder": checkpoints},
    }


def test_partial_early_diagnostic_matches_complete_early_conditioning():
    history = _partial_history()
    means = [1.0] * 8
    features = _early_features()
    complete = early_conditioning(features, means)
    partial = partial_early_conditioning(history, means)
    assert partial["valid_through_2002"]
    assert partial["log_score"] == pytest.approx(complete["total"])


def _toy_joint_proposal():
    fit = fit_joint_beta(np.full((1, 16), 0.5), [1.0])
    return {"groups": {
        f"A{age}_legacy_range_sensitivity:{stratum}": {"joint": fit}
        for age in (6, 8)
        for stratum in ("above_one", "below_one")
    }}


def test_build_sources_pairs_restrictions_and_separates_roles():
    cells = broad_cells()
    sources = build_sources(cells, 2, 2, "runner-test", _toy_joint_proposal())
    assert len(sources) == len(cells) * 4

    for role in ("truth", "bank"):
        for age in (6, 8):
            for index in (0, 1):
                paired = [
                    source for source in sources
                    if source["role"] == role and source["cell"]["maximum_age"] == age
                    and source["index"] == index
                ]
                assert len({source["source_id"] for source in paired}) == 1
                assert len({source["source_seed"] for source in paired}) == 1
                assert len({tuple(source["proposal_unit_coordinates"]) for source in paired}) == 1
                assert len({source["proposal_log_density_ratio"] for source in paired}) == 1
                assert len({
                    runner_arguments(source, 0, run_namespace="runner-test")["seed"]
                    for source in paired
                }) == 1

    truth = {(source["cell"]["maximum_age"], source["index"]): source
             for source in sources if source["role"] == "truth"
             and source["cell"]["restriction"] == "R_H"}
    bank = {(source["cell"]["maximum_age"], source["index"]): source
            for source in sources if source["role"] == "bank"
            and source["cell"]["restriction"] == "R_H"}
    assert all(truth[key]["source_id"] != bank[key]["source_id"] for key in truth)
    assert all(truth[key]["source_seed"] != bank[key]["source_seed"] for key in truth)
    assert all(truth[key]["proposal_unit_coordinates"] != bank[key]["proposal_unit_coordinates"] for key in truth)


def test_run_rejects_bad_production_bounds_before_simulation(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("simulation must not start after an invalid argument guard")

    import scripts.run_age_probability_gate as runner
    monkeypatch.setattr(runner, "execute_probability_source", forbidden)
    args = SimpleNamespace(
        mode="gate", truth_sources=1, bank_sources=512, replicates=6,
        workers=1, proposal=tmp_path / "missing.json", output_dir=tmp_path / "out",
        run_namespace="invalid", qualification_manifest=[],
    )
    with pytest.raises(ValueError, match="exactly 512"):
        run(args)

    args.mode = "smoke"
    args.truth_sources = 3
    args.bank_sources = 1
    args.replicates = 1
    with pytest.raises(ValueError, match="at most 2"):
        run(args)
