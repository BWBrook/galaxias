"""Scientific contracts of the experimental observation bridge."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from galaxias_model.observation_repair import (
    aggregate_repaired_late_evidence,
    project_repaired_history,
)


def history():
    t = pd.DataFrame({"year": range(1965, 2003), "N_L": 10.0, "N_R": 2.0})
    t["N_total"] = t.N_L + t.N_R
    return SimpleNamespace(trajectory_table=t)


def test_early_year_positive_record_does_not_require_end_year_survival():
    h = history()
    h.trajectory_table.loc[h.trajectory_table.year >= 1996, ["N_L", "N_R", "N_total"]] = 0.0
    f = project_repaired_history(h)
    assert f["positive_records_compatible"]
    assert f["present_at_1996_proxy"]
    assert not f["surviving_2002"]
    assert f["nondetection_occupied_episodes"] == 2  # lake only, 1988 and 1989
    h.trajectory_table.loc[h.trajectory_table.year == 1995, ["N_L", "N_R", "N_total"]] = 0.0
    assert not project_repaired_history(h)["positive_records_compatible"]


def test_seven_distinct_nondetection_episodes_allow_occupied_domains():
    f = project_repaired_history(history())
    assert f["nondetection_occupied_episodes"] == 7
    assert f["lake_nondetection_occupied_episodes"] == 2
    assert f["natural_nondetection_occupied_episodes"] == 5
    result = aggregate_repaired_late_evidence(pd.DataFrame([f] * 4), .6)
    assert result["mean_joint_compatibility"] == pytest.approx(.4**7)
    assert result["late_discrepancy"] == pytest.approx(-7 * np.log(.4))
    assert result["weight_ess"] == pytest.approx(4)


def test_average_joint_support_cannot_hide_incompatible_histories():
    f = pd.DataFrame({"positive_records_compatible": [True, True, False], "nondetection_occupied_episodes": [0, 2, 0]})
    result = aggregate_repaired_late_evidence(f, .6)
    w = np.array([1, .4**2, 0])
    assert result["late_discrepancy"] == pytest.approx(-np.log(w.mean()))
    assert result["positive_discrepancy"] == pytest.approx(-np.log(2/3))
    assert result["conditional_nondetection_compatibility"] == pytest.approx((1+.4**2)/2)
    assert result["weight_ess"] == pytest.approx(w.sum()**2/(w*w).sum())
    assert result["mc_relative_se"] == pytest.approx(w.std(ddof=1)/np.sqrt(3)/w.mean())
    assert result["largest_weight_share"] == pytest.approx(1/w.sum())
    bracket = aggregate_repaired_late_evidence(f, 0)
    assert bracket["late_discrepancy"] == pytest.approx(-np.log(2/3))
    assert bracket["conditional_nondetection_discrepancy"] == pytest.approx(0)


def test_zero_sampled_positive_support_has_no_finite_floor():
    f = pd.DataFrame({"positive_records_compatible": [False, False], "nondetection_occupied_episodes": [0, 0]})
    result = aggregate_repaired_late_evidence(f, .98)
    assert not result["sample_supported"]
    assert np.isinf(result["late_discrepancy"])
    assert result["mean_joint_compatibility"] == 0


def test_fixed_detection_strength_and_no_abundance_or_nuisance_scaling():
    h = history()
    f = project_repaired_history(h)
    h.trajectory_table[["N_L", "N_R", "N_total"]] *= 100
    g = project_repaired_history(h)
    # Detection depends on occupied domains; differing counts remain diagnostics.
    assert f["n_total_2002"] != g["n_total_2002"]
    low = aggregate_repaired_late_evidence(pd.DataFrame([f, g]), .6)
    high = aggregate_repaired_late_evidence(pd.DataFrame([f, g]), .98)
    assert high["late_discrepancy"] > low["late_discrepancy"]
    assert high["mean_joint_compatibility"] == pytest.approx(.02**7, rel=1e-12, abs=0)
    assert high["weight_ess"] == pytest.approx(2)


def test_missing_or_inconsistent_states_do_not_become_false_absence():
    h = history()
    h.trajectory_table = h.trajectory_table[h.trajectory_table.year != 1995]
    with pytest.raises(ValueError, match="annual states"):
        project_repaired_history(h)
    h = history()
    h.trajectory_table.loc[h.trajectory_table.year == 1995, "N_total"] = 0
    with pytest.raises(ValueError, match="sum"):
        project_repaired_history(h)


@pytest.mark.parametrize("p,k", [(1, 2), (-.1, 2), (.6, 2.5), (.6, 8)])
def test_invalid_observation_assumptions_fail(p, k):
    with pytest.raises(ValueError):
        aggregate_repaired_late_evidence(pd.DataFrame({"positive_records_compatible": [True], "nondetection_occupied_episodes": [k]}), p)
