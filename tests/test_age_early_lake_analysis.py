"""Numerical and archive-contract checks; no biological histories are run."""
from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import analyze_age_early_lake as analysis
from scripts import run_age_early_lake as driver


def test_profile_pairing_uses_exact_same_observations_for_score_concentration():
    row = {"source_id": "paired", "source_index": 0, "role": "test", "restriction": "R_H",
           "replicate": 0, "lake_exposures": np.column_stack((np.arange(1, 9), np.ones(8)))}
    first = analysis.synthetic_observation(row, "primary")
    second = analysis.synthetic_observation(row, "score_concentration")
    assert first["seed"] == second["seed"]
    np.testing.assert_array_equal(first["means"], second["means"])
    np.testing.assert_array_equal(first["raw_site_counts"], second["raw_site_counts"])


def test_halves_split_whole_sources_within_single_parity_stratum():
    ids = [f"bank_{i:04d}" for i in range(0, 12, 2)]
    masks = analysis.source_halves(ids)
    assert masks["half_a"].sum() == masks["half_b"].sum() == 3
    assert np.all(masks["half_a"] ^ masks["half_b"])
    again = analysis.source_halves(ids)
    np.testing.assert_array_equal(masks["half_a"], again["half_a"])


def test_gate_requires_same_directed_pair_in_every_primary_group():
    groups = [{"maximum_age": 6, "qualified": True, "reasons": [], "informative_pairs": ["R_T->R_H"]}
              for _ in range(16)]
    assert analysis.gate_decision(groups)["historical_comparison_permitted"]
    groups[-1]["informative_pairs"] = ["R_C->R_H"]
    assert analysis.gate_decision(groups)["decision"] == "STOP_EARLY_RECOVERY_LOW_INFORMATION"
    groups[-1]["qualified"] = False
    groups[-1]["reasons"] = ["bank_half_instability"]
    assert analysis.gate_decision(groups)["decision"] == "STOP_EARLY_RECOVERY_UNASSESSED"


def test_nan_is_rejected_and_infinities_remain_distinct():
    with pytest.raises(ValueError, match="NaN"):
        analysis.jsonable(float("nan"))
    assert analysis.jsonable([float("inf"), float("-inf")]) == ["Infinity", "-Infinity"]


def _fake_execution(task):
    source, _, bank_reps = task
    features, histories = [], []
    for restriction in driver.RESTRICTIONS:
        for rep in range(bank_reps if source["role"] == "bank" else 1):
            result = {"valid": source["feasible"], "lake_exposures": np.ones((8, 2)),
                      "advance_calls": 25 if source["feasible"] else 0}
            status = "valid" if source["feasible"] else "algebraically_infeasible"
            row = driver._feature_row(source, restriction, rep, driver.process_seed(source, rep), result, status)
            features.append(row)
            histories.append({"source": source, "feature": row})
    return features, histories


def test_actual_driver_archive_contract_and_fail_closed_checks(tmp_path, monkeypatch):
    monkeypatch.setattr(driver, "execute_source_task", _fake_execution)
    run = tmp_path / "mock_driver"
    manifest = driver.run(SimpleNamespace(mode="smoke", output=run, workers=1, preflight_only=False))
    rows = analysis.read_rows(run / "features.jsonl.gz")
    sources = analysis.read_rows(run / "sources.jsonl.gz")
    analysis.verify_run_inputs(run, manifest)
    assert analysis.validate_archive(rows, sources, manifest) == 192
    incomplete = copy.deepcopy(manifest)
    incomplete["status"] = "running"
    with pytest.raises(ValueError, match="completed"):
        analysis.verify_run_inputs(run, incomplete)
    omitted = copy.deepcopy(manifest)
    omitted["physical_sha256"].pop("features.jsonl.gz")
    with pytest.raises(ValueError, match="all three"):
        analysis.verify_run_inputs(run, omitted)
    replaced = copy.deepcopy(rows)
    replaced[-1]["source_id"] = "unexpected_unique_source"
    with pytest.raises(ValueError, match="planned slots"):
        analysis.validate_archive(replaced, sources, manifest)
    badseed = copy.deepcopy(rows)
    badseed[0]["seed"] += 1
    with pytest.raises(ValueError, match="seed"):
        analysis.validate_archive(badseed, sources, manifest)
    with pytest.raises(ValueError, match="planned slots"):
        analysis.validate_archive(rows[:-1], sources, manifest)
    with (run / "features.jsonl.gz").open("ab") as handle:
        handle.write(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        analysis.verify_run_inputs(run, manifest)


def test_identical_restrictions_preserve_sets_and_z0_accounting(tmp_path, monkeypatch):
    # Every class generates exactly the same observation and bank.  A forced
    # top-one classifier would invent discrimination; the set rule retains all.
    rows = []
    for role, count in (("bank", 2), ("calibration", 51), ("test", 51)):
        for i in range(count):
            for restriction in analysis.RESTRICTIONS:
                rows.append({"source_id": f"{role}_{i}", "source_index": i * 2,
                             "role": role, "restriction": restriction, "replicate": 0,
                             "valid": True, "status": "valid", "lake_exposures": np.ones((8, 2))})
    def constant_observation(row, profile):
        positive = row["source_index"] > 0
        return {"source_id": row["source_id"], "source_index": row["source_index"],
                "role": row["role"], "true_restriction": row["restriction"],
                "means": np.ones(8) if positive else np.zeros(8),
                "early_positive": positive}
    monkeypatch.setattr(analysis, "synthetic_observation", constant_observation)
    group = {"maximum_age": 6, "quality_regime": "neutral", "index_stratum": "below_one", "profile": "primary"}
    result = analysis.assess_group((group, rows, str(tmp_path / "identical.json.gz")))
    assert result["qualified"]
    assert result["informative_pairs"] == []
    for label in analysis.RESTRICTIONS:
        assert result["counts"]["test"][label]["z0_full_set"] == 1
        assert result["counts"]["test"][label]["z1"] == 50
        assert result["banks"]["full"]["coverage"][label]["rate"] == 1
    with gzip.open(tmp_path / "identical.json.gz", "rt") as handle:
        detail = json.load(handle)
    assert np.asarray(detail["banks"]["full"]["sets"]).all()
