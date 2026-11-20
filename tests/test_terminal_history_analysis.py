"""Scientific selection and precision contracts for the fixed-pool comparison."""
import importlib.util
from pathlib import Path
import sys

import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("terminal_analysis", SCRIPTS / "analyze_terminal_history_screen.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def test_equal_route_size_exposes_sources_outside_original_screen(tmp_path):
    rows = []
    for i in range(1, 26):
        rows.append({"search_seed": 1, "family_id": "family", "proposal_id": f"p{i:02}",
                     "profile": "repair_detection_098", "finite_supported": True,
                     "overall_distance": 26-i, "historical_distance": 26-i,
                     "intrinsic_distance": 0, "historical_iqr": 0,
                     "positive_and_extinct_by_2002_count": 0,
                     "positive_and_extinct_by_2002_fraction": 0})
    screen = pd.DataFrame(rows)
    original = screen[analysis.PROFILE_KEY].assign(stage_a_retained=[i < 10 for i in range(25)])
    original.to_csv(tmp_path / "stage_a_selection.csv", index=False)
    original.assign(selected=False).to_csv(tmp_path / "stage_b_source_summary.csv", index=False)
    selected = analysis.confirmation_selection(screen, tmp_path)
    full = set(selected.loc[selected.cohort.eq("full_global"), "proposal_id"])
    restricted = set(selected.loc[selected.cohort.eq("restricted_global"), "proposal_id"])
    assert len(full) == len(restricted) == 10
    assert not full & restricted
    assert set(selected.loc[selected.cohort.eq("full_family"), "proposal_id"]) == {"p25"}
    assert set(selected.loc[selected.cohort.eq("restricted_family"), "proposal_id"]) == {"p10"}


def test_extension_caps_distinct_sources_and_prioritises_zero_support():
    rows = []
    for i in range(45):
        for profile in analysis.REPAIRS:
            rows.append({"search_seed": 1, "family_id": "family", "proposal_id": f"p{i:02}",
                         "profile": profile, "sample_supported": i != 44,
                         "weight_ess": 2, "largest_weight_share": .8,
                         "mc_relative_se": i/100 if i != 44 else float("nan")})
    priority = analysis.extension_selection(pd.DataFrame(rows))
    assert len(priority) == 45 and priority.selected_for_extension.sum() == 40
    assert priority.iloc[0].proposal_id == "p44"
    assert priority.iloc[1].proposal_id == "p43"


def test_zero_events_bound_probability_without_declaring_impossibility():
    result = analysis.binomial_summary(0, 500)
    assert result["fraction"] == 0
    assert result["zero_one_sided_upper95"] == pytest.approx(0.00597355151634961)
    assert result["upper95"] > 0
    assert analysis.binomial_summary(500, 500)["lower95"] < 1


def test_frozen_sources_cannot_be_replaced_after_confirmation(tmp_path):
    path = tmp_path / "frozen.csv"
    table = pd.DataFrame({"proposal_id": ["one"]})
    analysis.freeze_csv(path, table)
    analysis.freeze_csv(path, table)
    with pytest.raises(ValueError, match="Frozen selection changed"):
        analysis.freeze_csv(path, pd.DataFrame({"proposal_id": ["two"]}))
    assert path.read_text() == "proposal_id\none\n"
