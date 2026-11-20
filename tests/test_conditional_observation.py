"""Detection dependence, score weighting, and held-out selection contracts."""
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

from galaxias_model.conditional_observation import (
    CONDITIONAL_PROFILES, effective_episodes, history_weights, source_summaries,
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import analyze_conditional_calibration as analysis


def features():
    return pd.DataFrame({"positive_records_compatible": [True, True, False],
                         "lake_nondetection_occupied_episodes": [2, 0, 1],
                         "natural_nondetection_occupied_episodes": [5, 0, 2],
                         "nondetection_occupied_episodes": [7, 0, 3]})


def test_shared_detection_is_one_event_per_occupied_window():
    raw = features()
    assert np.array_equal(effective_episodes(raw, "repair_shared_window_098"), [2, 0, 2])
    assert history_weights(raw, "repair_detection_098").tolist() == pytest.approx([.02**7, 1, 0])
    assert history_weights(raw, "repair_shared_window_098").tolist() == pytest.approx([.02**2, 1, 0])
    raw.loc[0, "lake_nondetection_occupied_episodes"] = 3
    with pytest.raises(ValueError, match="domain-specific"):
        effective_episodes(raw, "repair_detection_060")


def test_source_score_includes_incompatible_histories_in_denominator():
    raw = features().assign(search_seed=1, family_id="family", proposal_id="p1", stage="screen", replicate_index=[1, 2, 3], simulation_seed=[10, 11, 12], surviving_2002=[True, False, True])
    for i in range(1, 13):
        raw[f"CT{i:03d}_weighted_penalty"] = 1 if i <= 5 else 0
    result = source_summaries(raw).set_index("profile")
    assert set(result.index) == set(CONDITIONAL_PROFILES)
    assert result.loc["repair_shared_window_098", "mean_joint_compatibility"] == pytest.approx((1 + .02**2) / 3)
    assert result.loc["repair_presence_only", "overall_distance"] == pytest.approx(5 - 5 * math.log(2/3))
    assert result.loc["repair_detection_098", "compatibility_weighted_surviving_2002"] == pytest.approx(.02**7 / (1 + .02**7))
    assert result.loc["repair_shared_window_098", "compatibility_weighted_surviving_2002"] == pytest.approx(.02**2 / (1 + .02**2))
    raw.positive_records_compatible = False
    zero = source_summaries(raw)
    assert not zero.finite_supported.any()
    assert np.isinf(zero.overall_distance).all()
    assert zero.compatibility_weighted_surviving_2002.isna().all()


def test_selection_preserves_profile_membership_and_weight_sensitivity():
    rows = []
    for profile in ("repair_presence_only", "repair_detection_098"):
        for proposal, early, late in [("p1", 0, 4), ("p2", 10, 0), ("p3", 0, 0)]:
            rows.append(dict(search_seed=1, family_id="family", proposal_id=proposal, profile=profile,
                             stage="refine", finite_supported=True, early_distance=early, late_discrepancy=late,
                             intrinsic_distance=0, overall_distance=early + 5*late,
                             historical_distance=early + 5*late, historical_iqr=0))
    summary = pd.DataFrame(rows)
    previous = summary.loc[summary.proposal_id.ne("p3"), analysis.KEY]
    selected = analysis.select_membership(summary, 1, 1, previous)
    assert set(selected.loc[selected.cohort.eq("global"), "proposal_id"]) == {"p2"}
    assert set(selected.loc[selected.cohort.eq("weight1_family"), "proposal_id"]) == {"p1"}
    assert "p3" not in set(selected.proposal_id)
    with pytest.raises(ValueError, match="Validation cannot select"):
        analysis.select_membership(summary.assign(stage="validate"), 1, 1)
