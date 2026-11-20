"""Focused failure modes for the archive-only audit."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


spec = importlib.util.spec_from_file_location("historical_fit_audit", Path(__file__).resolve().parents[1] / "scripts/audit_historical_fit_observation.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_median_sum_and_sum_medians_are_different_orders():
    rows = []
    for proposal, values in [("a", [[0, 100], [100, 0], [100, 100]]), ("b", [[60, 60]] * 3)]:
        for rep, pair in enumerate(values):
            for i, target in enumerate(audit.TARGETS):
                rows.append({"proposal_id": proposal, "replicate_index": rep, "target_id": target, "weighted_penalty": pair[i] if i < 2 else 0.})
    order = audit.proposal_order(pd.DataFrame(rows))
    assert order.proposal_id.tolist() == ["a", "b"]
    assert order.sort_values("target_median_sum").proposal_id.tolist() == ["b", "a"]
    assert order.iloc[0].overall == 100.
    assert order.iloc[0].target_median_sum == 200.


@pytest.mark.parametrize("variant", list(audit.OBSERVATION_BRIDGE_VARIANTS))
def test_independent_bridge_reconstruction_and_corruption(variant):
    details = {"CT006": {"expected_capture_range": {"low": 5., "high": 20.}}, "CT007": {"survey_sites": 117, "occupancy_anchor_alpha": -np.log(1 - 5 / 117) / 68, "occupied_site_range": {"low": 3., "high": 7.}, "observed_capture_count": 68.}, "CT008": {"capture_upper_bound": 10., "capture_soft_gap": 15., "latent_upper_bound": 50., "latent_soft_gap": 75.}, "CT009": {"target_year": 1996}}
    v = audit.OBSERVATION_BRIDGE_VARIANTS[variant]
    rows = []
    # Use literal independent expected penalties covering below/within/above windows.
    for rep, year in enumerate([1988., 1994., 2002.]):
        timing = abs(year - 1996) if v["ct009_mode"] == "exact_year" else [1., 0., 2.][rep]
        captures = 34.
        count = v["ct007_count_weight"] * (2 * (68 * np.log(2) - 34) / 2)
        sites = 117 * (1 - np.exp(-details["CT007"]["occupancy_anchor_alpha"] * captures))
        occupancy = v["ct007_occupancy_weight"] * (3 - sites) / 4
        for target, p, s, raw in [("CT006", 35., .5, (1 + .5 + 1) / 3), ("CT007", sites, captures, count + occupancy), ("CT008", 25., 125., 1.), ("CT009", year, year + 1, timing), ("CT010", 7., 9., 7 * v["ct010_detection_multiplier"])]:
            rows.append({"proposal_id": "a", "replicate_index": rep, "target_id": target, "projected_primary": p, "projected_secondary": s, "raw_penalty": raw, "weighted_penalty": 5 * raw})
    scores = pd.DataFrame(rows)
    parameters = pd.DataFrame([{"proposal_id": "a", "parameter_id": "PR037", "value_natural": 2.}])
    result = audit.reconstruct_late_scores(scores, parameters, variant, details, {t: 5 for t in audit.LATE_TARGETS})
    assert np.allclose(result["CT006"].lake_presence_fraction, 1)
    assert np.allclose(result["CT007"].count_weighted_component, 5 * count)
    damaged = scores.copy()
    damaged.loc[damaged.target_id == "CT007", "raw_penalty"] += 1
    with pytest.raises(ValueError, match="CT007"):
        audit.reconstruct_late_scores(damaged, parameters, variant, details, {t: 5 for t in audit.LATE_TARGETS})


def test_binding_checks_size_and_content(tmp_path):
    path = tmp_path / "archive"
    path.write_bytes(b"abc")
    binding = audit.file_binding(path)
    audit.file_binding(path, 3, binding["sha256"])
    with pytest.raises(ValueError, match="Size mismatch"):
        audit.file_binding(path, 4, binding["sha256"])
    path.write_bytes(b"abd")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        audit.file_binding(path, 3, binding["sha256"])


def test_incomplete_replicate_target_grain_fails():
    scores = pd.DataFrame([{"proposal_id": "a", "replicate_index": 0, "target_id": "CT001", "weighted_penalty": 1.}])
    with pytest.raises(ValueError, match="Incomplete"):
        audit.proposal_order(scores)
