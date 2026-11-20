from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_mate_guard import (
    _diagnostics,
    _load_annual_diagnostics,
    _profile,
    _paired_rows,
    _weights,
    analyze,
)
from scripts.run_common_model_comparison import summarize_source
from galaxias_model.abundance_detection import COMMON_EPISODE_FIELDS


def _raw(n: int = 4, *, invalid_last: bool = False) -> pd.DataFrame:
    rows = []
    for index in range(n):
        row = {
            "search_seed": 1,
            "configuration": "base",
            "restriction": "R_J",
            "wave": 1,
            "source_index": 1,
            "source_id": "s1",
            "replicate_index": index + 1,
            "simulation_seed": 100 + index,
            "environment_seed": 200 + index,
            "early_early_patterns_pass": True,
            "removals_valid": not (invalid_last and index == n - 1),
            "endpoint_terminal_survival": float(index % 2),
            "endpoint_min_total_over_preflood_mean": 1.0 + index,
            "endpoint_extinction_time_censored": 2003.0,
            "endpoint_N_total_2002": float(index + 2),
            "endpoint_N_R_2002": float(index % 2),
            "endpoint_ct005_N_L_1980": float(index + 1),
            "endpoint_ct005_N_L_1983": float(index + 2),
            "annual_N_R_2002": float(index % 2),
        }
        row.update({field: 10.0 for field in COMMON_EPISODE_FIELDS})
        rows.append(row)
    return pd.DataFrame(rows)


def _sources(*, viable: bool = True) -> pd.DataFrame:
    return pd.DataFrame([{
        "source_ordinal": 1,
        "source_id": "s1",
        "search_seed": 1,
        "configuration": "base",
        "restriction": "R_J",
        "wave": 1,
        "source_index": 1,
        "viable": viable,
    }])


def _parameters() -> pd.DataFrame:
    return pd.DataFrame([{"source_id": "s1", "parameter_id": "PR001", "value_natural": 0.5}])


def _write_archive(directory: Path, raw: pd.DataFrame, sources: pd.DataFrame) -> None:
    directory.mkdir(parents=True)
    sources.drop(columns=["source_ordinal"]).to_csv(directory / "sources.csv", index=False)
    raw.to_csv(directory / "raw_histories.csv.gz", index=False, compression="gzip")
    _parameters().to_csv(directory / "parameter_values.csv.gz", index=False, compression="gzip")
    (directory / "run_manifest.json").write_text(json.dumps({"status": "complete"}) + "\n")


def test_weights_use_stable_logs_and_keep_zero_weight_rows() -> None:
    raw = _raw()
    weights, support, stats = _weights(raw, True, 0.02, "homogeneous")
    assert support.all()
    assert weights.sum() == pytest.approx(1.0)
    assert stats["weight_ess"] == pytest.approx(4.0)
    zeroed = raw.copy()
    zeroed.loc[0, "removals_valid"] = False
    weights, support, _ = _weights(zeroed, True, 0.02, "homogeneous")
    assert support.sum() == 3
    assert weights[0] == 0.0


def test_profile_bounds_match_established_source_summary() -> None:
    raw = _raw()
    expected = summarize_source(raw, True).set_index(["q", "observation_model"])
    for (q, law), row in expected.iterrows():
        observed = _profile(raw, True, float(q), str(law))
        assert observed["early_pattern_lower95"] == pytest.approx(row.early_pattern_lower95)
        assert observed["early_pattern_upper95"] == pytest.approx(row.early_pattern_upper95)
        assert observed["joint_lower95"] == pytest.approx(row.joint_lower95)
        assert observed["joint_upper95"] == pytest.approx(row.joint_upper95)


def test_invalid_amended_removal_makes_paired_contrast_undefined() -> None:
    old = _raw()
    new = _raw(invalid_last=True).rename(columns={c: f"{c}_new" for c in _raw(invalid_last=True).columns
                                                  if c not in {"search_seed", "configuration", "restriction", "wave", "source_index", "source_id", "replicate_index", "simulation_seed", "environment_seed"}})
    keys = ["search_seed", "configuration", "restriction", "wave", "source_index", "source_id",
            "replicate_index", "simulation_seed", "environment_seed"]
    joined = old.merge(new, on=keys, validate="one_to_one")
    paired = _paired_rows(joined, _sources(), _sources())
    invalid = paired.loc[paired.new_invalid_removal_positive_support_count > 0]
    assert len(invalid) > 0
    assert invalid.paired_difference.isna().all()
    assert invalid.status.iloc[0] == "undefined_invalid_removal_positive_support"


def test_analyze_preserves_source_failure_and_writes_receipt(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    run = tmp_path / "run"
    out = tmp_path / "out"
    sources = _sources()
    _write_archive(baseline, _raw(), sources)
    run.mkdir()
    sources.assign(original_viable=True, viable=False).to_csv(run / "sources.csv", index=False)
    _parameters().to_csv(run / "parameter_values.csv.gz", index=False, compression="gzip")
    (run / "raw").mkdir()
    _raw().to_csv(run / "raw" / "0001.csv.gz", index=False, compression="gzip")
    (run / "run_manifest.json").write_text(json.dumps({"status": "complete", "mode": "qualification"}) + "\n")
    readout = analyze(baseline, run, out)
    assert readout["source_count"] == 1
    profiles = pd.read_csv(out / "rescored_profiles.csv")
    assert profiles.viable.eq(False).all()
    assert profiles.new_weight_ess.eq(0).all()
    assert (out / "mate_guard_analysis_receipt.json").exists()


def test_annual_diagnostics_are_terminal_and_stage_aggregated(tmp_path: Path) -> None:
    run = tmp_path / "run"
    (run / "annual").mkdir(parents=True)
    annual = pd.DataFrame([
        {"replicate_index": 1, "year": 2001, "J_L": 2, "A_L": 1, "J_R": 0, "A_R": 1,
         "N_R": 1, "N_total": 4, "pre_breeding_A_total": 1.0, "mate_guard_active": True},
        {"replicate_index": 1, "year": 2002, "J_L": 2, "A_L": 1, "J_R": 0, "A_R": 0,
         "N_R": 0, "N_total": 3, "pre_breeding_A_total": 1.0, "mate_guard_active": True},
        {"replicate_index": 2, "year": 2002, "J_L": 0, "A_L": 0, "J_R": 2, "A_R": 0,
         "N_R": 2, "N_total": 2, "pre_breeding_A_total": 2.0, "mate_guard_active": False},
    ])
    annual.to_csv(run / "annual" / "0001.csv.gz", index=False, compression="gzip")
    result = _load_annual_diagnostics(run, _sources())
    assert result is not None
    assert result["lake_only_terminal_count"] == 1
    stage = result["stage_table"]
    row = stage.loc[stage.year.eq(2002)].iloc[0]
    assert row.mean_J_L == pytest.approx(1.0)
    assert row.pre_breeding_A_total_lt_2_count == 1
    raw = _raw(1)
    readout = _diagnostics(raw, result)
    assert readout["lake_only_endpoint_count"] == 1
    assert readout["guard_activation_exact"] is True
