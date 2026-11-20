from __future__ import annotations

import numpy as np
import pytest

from galaxias_model.age_demography import AgeDemography
from galaxias_model.age_runner import run_linked_history


def _parameters() -> dict[str, float]:
    values = {f"PR{i:03d}": 0.0 for i in range(12, 35)}
    values.update(PR005=0.0, PR007=0.0, PR032=1.0, PR040=10.0)
    return values


def _demography() -> AgeDemography:
    return AgeDemography(
        annual_survival=(1.0,) * 6,
        breeding_probability=(0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0),
        recruits_per_female=100.0,
        lake_settlement=0.95,
    )


def _run(**kwargs):
    options = dict(
        restriction="R_J",
        eta_refuge=0.5,
        recruitment_sigma=0.0,
        strath_pre2007=0.02,
        seed=19,
        stochastic=False,
    )
    options.update(kwargs)
    return run_linked_history(
        _demography(),
        _parameters(),
        {"pedder_lake": 100_000.0, "pedder_refuge": 1_000.0,
         "oberon": 100_000.0, "strathgordon": 100_000.0},
        **options,
    )


def test_history_shapes_calendar_and_transfer_conservation():
    result = _run()
    assert result["valid"] is True
    assert set(result["annual_states"]) == {"pedder", "oberon", "strathgordon"}
    for states in result["annual_states"].values():
        assert list(states) == list(range(1965, 2013))
        assert all(state.shape == (2, 2, 7) for state in states.values())
    assert len(result["calendar"]) >= 100
    labels = [item["label"] for item in result["checkpoint_states"]["strathgordon"]]
    assert sum(label.startswith("strath_survey_") for label in labels) == 5
    assert result["advance_calls"] == 48 * 3
    assert result["nominal_site_histories"] == 3
    assert len(result["transfer_ledger"]) == 5
    assert any(item["label"] == "captive_broodstock_offspring" for item in result["addition_ledger"])
    assert sum(item["count"] for item in result["transfer_ledger"]) == 353
    for item in result["transfer_ledger"]:
        assert item["conserved"] is True
        assert item["vector"].shape == (2, 7)
        assert item["vector"].sum() == pytest.approx(item["count"])
        np.testing.assert_allclose(item["donor_by_compartment_sex_age"].sum(axis=0), item["vector"][:, :-1])
    assert sum(item["donor_by_compartment_sex_age"][1].sum() for item in result["transfer_ledger"]) > 0
    assert sum(item["donor_by_compartment_sex_age"][:, :, 0].sum() for item in result["transfer_ledger"]) > 0
    assert result["early_wild_extraction_count"] == pytest.approx(25)
    assert result["early_window_extraction_count"] == pytest.approx(23)
    assert sum(item["count"] for item in result["addition_ledger"] if item["year"] <= 1992) == pytest.approx(31)
    assert sum(item["count"] for item in result["addition_ledger"]) == pytest.approx(34)
    group_counts = {
        item["label"]: item["actual_by_sex_age"]
        for item in result["removal_ledger"]
        if item["label"] in {"captive_group_a_capture_early", "adult_capture_1991_early", "immature_capture_1991_early"}
    }
    assert group_counts["captive_group_a_capture_early"][0].sum() == pytest.approx(5)
    assert group_counts["captive_group_a_capture_early"][1].sum() == pytest.approx(7)
    assert group_counts["adult_capture_1991_early"][0].sum() == pytest.approx(5)
    assert group_counts["adult_capture_1991_early"][1].sum() == pytest.approx(5)
    assert group_counts["immature_capture_1991_early"][:, 1:].sum() == 0
    deaths = next(item for item in result["holding_ledger"] if item.get("status") == "documented_captive_deaths")
    assert deaths["vector"][0].sum() == pytest.approx(2)
    assert deaths["vector"][1].sum() == pytest.approx(3)
    captures = {item["label"]: item for item in result["removal_ledger"]}
    for label in {item["capture_label"] for item in result["holding_ledger"]}:
        outcomes = [item for item in result["holding_ledger"] if item["capture_label"] == label]
        represented = np.zeros((2, 7))
        for item in outcomes:
            if item["status"] == "released":
                assert (item["capture_year"], item["capture_time"]) < (item["release_year"], item["release_time"])
                captured = item["released_capture_cohorts"]
                represented += captured
                shifted = np.zeros((2, 7))
                delta = item["release_year"] - item["capture_year"]
                shifted[:, delta:] = captured[:, :7-delta]
                np.testing.assert_allclose(shifted, item["vector"])
                assert item["vector"][:, -1].sum() == 0
            else:
                represented += item["vector"]
        np.testing.assert_allclose(represented[:, :-1], captures[label]["actual_by_sex_age"])
    november = next(item for item in result["addition_ledger"] if item["label"] == "november_1991_release")
    np.testing.assert_allclose(november["vector"][:, 1:].sum(axis=1), [8, 9])
    assert november["vector"][:, 0].sum() == pytest.approx(1)


def test_union_calendar_and_march_retention_change_operation_only():
    early = _run(ledger_timing="early")
    late = _run(
        ledger_timing="late", march_retention=True,
        removal_account="sanger_42_early_releases_held_before_1992",
    )
    assert early["valid"] and late["valid"]
    assert early["calendar_hash"] == late["calendar_hash"]
    assert [item[:3] for item in early["calendar"]] == [item[:3] for item in late["calendar"]]
    assert any(item["label"] == "captive_group_a_capture_early" for item in early["removal_ledger"])
    assert any(item["label"] == "captive_group_a_capture_late" for item in late["removal_ledger"])
    assert not any(item["label"] == "march_1996_record" for item in early["removal_ledger"])
    assert any(item["label"] == "march_1996_record" for item in late["removal_ledger"])
    assert late["early_wild_extraction_count"] == pytest.approx(36)
    assert late["early_window_extraction_count"] == pytest.approx(34)
    assert sum(item["count"] for item in late["addition_ledger"] if item["year"] <= 1992) == pytest.approx(42)
    assert sum(item["count"] for item in late["addition_ledger"]) == pytest.approx(45)
    assert sum(item["count"] for item in late["holding_ledger"] if item["capture_label"].startswith("sanger")) == pytest.approx(11)
    february_time = next(time for year, time, label in late["calendar"] if label == "february_1992_release")
    assert sum(item["count"] for item in late["addition_ledger"]
               if item["year"] == 1992 and abs(item["time"] - february_time) < 1e-10) == pytest.approx(12)
    additional = next(item for item in late["addition_ledger"] if item["label"] == "sanger_additional_held_release")
    assert additional["time"] > february_time


def test_no_wild_removals_do_not_create_insurance_founders():
    result = _run(no_wild_removals=True)
    assert result["valid"] is True
    assert result["removal_ledger"] == []
    assert result["holding_ledger"] == []
    assert result["transfer_ledger"] == []
    for year in result["annual_states"]["oberon"]:
        np.testing.assert_array_equal(result["annual_states"]["oberon"][year], 0.0)
        np.testing.assert_array_equal(result["annual_states"]["strathgordon"][year], 0.0)


def test_stochastic_history_is_reproducible_for_same_seed():
    first = _run(stochastic=True, seed=37)
    second = _run(stochastic=True, seed=37)
    assert first["valid"] and second["valid"]
    for site in first["annual_states"]:
        for year in first["annual_states"][site]:
            np.testing.assert_array_equal(first["annual_states"][site][year], second["annual_states"][site][year])
    for left, right in zip(first["transfer_ledger"], second["transfer_ledger"]):
        assert left["year"] == right["year"] and left["count"] == right["count"]
        np.testing.assert_array_equal(left["vector"], right["vector"])


def test_missing_retained_parameter_is_a_failure():
    result = run_linked_history(
        _demography(), {},
        {"pedder_lake": 100_000.0, "pedder_refuge": 1_000.0,
         "oberon": 100_000.0, "strathgordon": 100_000.0},
        restriction="R_J", eta_refuge=0.5, recruitment_sigma=0.0,
        strath_pre2007=0.02, seed=1,
    )
    assert result["valid"] is False
    assert "missing retained parameter" in result["failure"]


def test_extended_forcing_matches_retained_common_history_through_2002():
    import json
    from galaxias_model.age_runner import _forcing_rows, _Parameters
    from galaxias_model.age_sources import DESIGN, make_source
    from galaxias_model.common_model import _common_historical_forcing, _ParameterValues
    cell = json.loads(DESIGN.read_text())["process_cells"][0]
    columns = ("connected", "U", "O", "H", "spawn_habitat_multiplier", "T", "P", "C_L", "C_R")
    for index in range(3):
        source = make_source(cell, index, namespace="forcing-qualification")
        params = _ParameterValues(source["forcing_values"])
        for removed in (False, True):
            extended = _forcing_rows(_Parameters(params), 1964, 2012, overshoot_removed=removed)
            original = _common_historical_forcing(params, overshoot_removed=removed)
            for row in original.to_dict(orient="records"):
                year = int(row["year"])
                np.testing.assert_array_equal([extended[year][key] for key in columns],
                                              [row[key] for key in columns])
