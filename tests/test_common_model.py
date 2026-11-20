from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galaxias_model.abundance_detection import COMMON_EPISODE_FIELDS
from galaxias_model.common_model import (
    CONFIGURATIONS,
    RESTRICTIONS,
    _annual_juvenile_survival,
    intrinsic_viability,
    run_common_history,
    source_exposure_table,
)
from galaxias_model.io import load_model_inputs, resolve_family_parameters


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def params():
    return resolve_family_parameters(load_model_inputs(DATA_DIR), "transient_perfect_storm")


def test_public_design_grid_and_fourteen_record_contract(params) -> None:
    assert CONFIGURATIONS == (
        "base",
        "env_rho_002",
        "env_rho_010",
        "juvenile_climbing",
        "minimum_dated_adult_first",
        "minimum_dated_juvenile_first",
    )
    assert RESTRICTIONS == ("R_H", "R_T", "R_C", "R_J")
    result = run_common_history(params, "R_J", "base", 1, 2)
    assert tuple(result.observation_features) == COMMON_EPISODE_FIELDS
    assert len(result.observation_features) == 14
    assert len(result.trajectory_table) == 38
    assert result.trajectory_table["year"].tolist() == list(range(1965, 2003))
    assert set(result.early_patterns) == {
        "pre_flood_both_compartments",
        "boom_above_pre_mean",
        "boom_above_late_mean",
        "boom_peak_year_1976_1978",
        "ct005_directional_contrast",
        "ct004_forcing",
        "historical_patterns",
        "early_patterns_pass",
    }
    assert result.summary["extinction_time_censored"] in range(1965, 2004)
    assert result.summary["terminal_survival"] == result.summary["survived_2002"]


def test_common_forcing_ignores_legacy_family_status_and_matches_restrictions(params) -> None:
    all_unused = replace(params, statuses={key: "unused" for key in params.statuses})
    reference = run_common_history(params, "R_J", "base", 12, 34)
    status_ignored = run_common_history(all_unused, "R_J", "base", 12, 34)
    pd.testing.assert_frame_equal(reference.forcing_table, status_ignored.forcing_table)
    pd.testing.assert_frame_equal(reference.trajectory_table, status_ignored.trajectory_table)
    assert (reference.forcing_table.loc[reference.forcing_table["year"] >= 1972, "T"] > 0).all()
    assert (reference.forcing_table.loc[reference.forcing_table["year"] >= 1972, "C_L"] > 0).all()

    for restriction in RESTRICTIONS:
        candidate = run_common_history(params, restriction, "base", 12, 34)
        pd.testing.assert_frame_equal(reference.forcing_table, candidate.forcing_table)


@pytest.mark.parametrize(
    ("restriction", "zero_ids"),
    [
        ("R_H", ("PR020", "PR021", "PR027", "PR028")),
        ("R_T", ("PR027", "PR028")),
        ("R_C", ("PR020", "PR021")),
    ],
)
def test_null_restrictions_are_exact_zero_effect_identities(params, restriction, zero_ids) -> None:
    values = dict(params.values)
    values.update({parameter_id: 0.0 for parameter_id in zero_ids})
    explicit_zero = replace(params, values=values)
    restricted = run_common_history(params, restriction, "base", 221, 17)
    unrestricted_zero = run_common_history(explicit_zero, "R_J", "base", 221, 17)
    pd.testing.assert_frame_equal(
        restricted.trajectory_table.drop(columns="restriction"),
        unrestricted_zero.trajectory_table.drop(columns="restriction"),
    )
    assert restricted.observation_features == unrestricted_zero.observation_features


def test_biotic_exposure_is_connected_and_not_multiplied_by_h(params) -> None:
    result = run_common_history(params, "R_J", "base", 4, 9)
    trajectory = result.trajectory_table.set_index("year")
    forcing = result.forcing_table.set_index("year")
    assert trajectory.loc[1972, "adult_lake_exposure"] == pytest.approx(0.0)

    # The 1973 transition sees lagged 1972 threats. Habitat remains current-year,
    # while the biotic sum is connectivity-gated but is not multiplied by H.
    expected = (
        params.value("PR033") * forcing.loc[1973, "H"]
        + params.value("PR020") * forcing.loc[1972, "T"] * forcing.loc[1972, "P"]
        + params.value("PR027") * forcing.loc[1972, "C_L"]
    )
    assert trajectory.loc[1973, "adult_lake_exposure"] == pytest.approx(expected)


@pytest.mark.parametrize("restriction", RESTRICTIONS)
@pytest.mark.parametrize("configuration", ("base", "juvenile_climbing"))
def test_source_exposure_table_matches_history_and_isolates_pathways(params, restriction, configuration) -> None:
    exposures = source_exposure_table(params, restriction, configuration)
    history = run_common_history(params, restriction, configuration, 19, 23).trajectory_table
    assert exposures["year"].tolist() == list(range(1965, 2003))
    for column in (
        "juvenile_lake_exposure",
        "adult_lake_exposure",
        "juvenile_refuge_exposure",
        "adult_refuge_exposure",
        "movement_lake_exposure",
        "move_probability",
    ):
        np.testing.assert_allclose(exposures[column], history[column])
    hazard_columns = [column for column in exposures if column.endswith("_hazard")]
    assert len(hazard_columns) == 12
    for hazard_column in hazard_columns:
        mortality_column = hazard_column.removesuffix("_hazard") + "_mortality"
        np.testing.assert_allclose(exposures[mortality_column], 1 - np.exp(-exposures[hazard_column]))
    if restriction == "R_H":
        assert (exposures.filter(regex="^(trout|climbing)_.*_hazard$") == 0).all().all()
    if configuration == "juvenile_climbing":
        np.testing.assert_allclose(
            exposures["climbing_lake_juvenile_hazard"],
            2 * exposures["climbing_lake_adult_hazard"],
        )


def test_ct005_descriptive_levels_are_reported_with_unchanged_pass_rule(params) -> None:
    result = run_common_history(params, "R_J", "base", 7, 11)
    summary = result.summary
    contrast = (
        summary["ct005_C_L_1983"] * summary["ct005_N_L_1980"]
        - summary["ct005_C_L_1980"] * summary["ct005_N_L_1983"]
    )
    assert summary["ct005_cross_product_contrast"] == pytest.approx(contrast)
    expected_pass = summary["ct005_N_L_1980"] > 0 and summary["ct005_C_L_1983"] > 0 and contrast > 0
    assert result.early_patterns["ct005_directional_contrast"] is expected_pass


def test_minimum_dated_removal_event_order_and_shared_evidence(params) -> None:
    base = run_common_history(params, "R_J", "base", 1, 91)
    adult_first = run_common_history(params, "R_J", "minimum_dated_adult_first", 1, 91)
    juvenile_first = run_common_history(params, "R_J", "minimum_dated_juvenile_first", 1, 91)
    assert adult_first.removals_valid and juvenile_first.removals_valid
    assert base.observation_features["pos_N_R_1996_january"] == base.observation_features["pos_N_R_1996_march"]

    for result in (adult_first, juvenile_first):
        # The 1992 detection precedes the one-adult extraction and therefore is
        # exactly the state recorded after the 1991 transition.
        n_r_1991 = float(result.trajectory_table.loc[result.trajectory_table["year"] == 1991, "N_R"].iloc[0])
        assert result.observation_features["pos_N_R_1992"] == n_r_1991
        assert result.observation_features["pos_N_R_1996_january"] - result.observation_features[
            "pos_N_R_1996_march"
        ] == pytest.approx(4.0)


def test_impossible_removal_is_flagged_without_inventing_or_negative_fish(params) -> None:
    values = dict(params.values)
    values.update(PR001=0.0, PR002=0.0, PR004=0.0)
    extinct = replace(params, values=values)
    result = run_common_history(extinct, "R_J", "minimum_dated_adult_first", 1, 2)
    assert result.removals_valid is False
    assert result.observation_features["pos_N_R_1996_january"] == 0
    assert result.observation_features["pos_N_R_1996_march"] == 0
    assert (result.trajectory_table[["J_L", "A_L", "J_R", "A_R"]] >= 0).all().all()


def test_environment_stream_is_separate_and_beta_law_preserves_mean(params) -> None:
    base_a = run_common_history(params, "R_J", "base", 99, 1)
    base_b = run_common_history(params, "R_J", "base", 99, 999)
    pd.testing.assert_frame_equal(
        base_a.trajectory_table.drop(columns="environment_seed"),
        base_b.trajectory_table.drop(columns="environment_seed"),
    )

    environment_rng = np.random.default_rng(20260918)
    draws = np.array([_annual_juvenile_survival(params, "env_rho_010", environment_rng) for _ in range(50_000)])
    assert draws.mean() == pytest.approx(params.value("PR001"), abs=0.003)
    expected_variance = params.value("PR001") * (1 - params.value("PR001")) * 0.10
    assert draws.var() == pytest.approx(expected_variance, rel=0.04)

    env_a = run_common_history(params, "R_J", "env_rho_010", 99, 1)
    env_b = run_common_history(params, "R_J", "env_rho_010", 99, 2)
    assert not env_a.trajectory_table["juvenile_survival"].equals(env_b.trajectory_table["juvenile_survival"])


def test_juvenile_climbing_doubles_only_climbing_mortality_not_movement(params) -> None:
    base = run_common_history(params, "R_J", "base", 73, 5).trajectory_table
    juvenile = run_common_history(params, "R_J", "juvenile_climbing", 73, 5).trajectory_table
    np.testing.assert_allclose(base["adult_lake_exposure"], juvenile["adult_lake_exposure"])
    np.testing.assert_allclose(base["adult_refuge_exposure"], juvenile["adult_refuge_exposure"])
    np.testing.assert_allclose(base["move_probability"], juvenile["move_probability"])
    assert (juvenile.loc[juvenile["year"] >= 1973, "juvenile_lake_exposure"] >= base.loc[
        base["year"] >= 1973, "juvenile_lake_exposure"
    ]).all()
    assert (juvenile.loc[juvenile["year"] >= 1973, "juvenile_lake_exposure"] > base.loc[
        base["year"] >= 1973, "juvenile_lake_exposure"
    ]).any()


def test_overshoot_counterfactual_changes_only_piscivory_forcing(params) -> None:
    factual = run_common_history(params, "R_J", "base", 44, 55, overshoot_removed=False)
    counterfactual = run_common_history(params, "R_J", "base", 44, 55, overshoot_removed=True)
    for column in ("T", "U", "H", "C_L", "C_R", "stocking_input"):
        np.testing.assert_allclose(factual.forcing_table[column], counterfactual.forcing_table[column])
    assert counterfactual.forcing_table.loc[counterfactual.forcing_table["year"] >= 1972, "P"].nunique() == 1
    assert float(factual.forcing_table["P"].max()) > float(counterfactual.forcing_table["P"].max())


def test_intrinsic_viability_reports_each_component_and_annual_diagnostics(params) -> None:
    diagnostics = intrinsic_viability(params)
    assert diagnostics["viable"] is True
    assert diagnostics["oberon_persisted_annually"] is True
    assert diagnostics["oberon_total_2012"] > diagnostics["oberon_founders_total"] == 34.0
    assert diagnostics["oberon_first_juvenile_year"] <= 1997
    assert diagnostics["strathgordon_no_juveniles_2001_2007"] is True
    assert diagnostics["strathgordon_juveniles_2008"] > 0
    assert diagnostics["strathgordon_total_2012"] > 0
    assert set(diagnostics["oberon_annual_total"]) == set(range(1991, 2013))
    assert set(diagnostics["strathgordon_annual_juveniles"]) == set(range(2001, 2013))
    assert diagnostics["K_R_over_PR011"] == pytest.approx(diagnostics["K_R"] / diagnostics["PR011"])


def test_cached_source_preparation_does_not_alias_returned_state(params) -> None:
    first = run_common_history(params, "R_J", "base", 8, 9)
    expected = float(first.forcing_table.loc[first.forcing_table["year"] == 1972, "T"].iloc[0])
    first.forcing_table.loc[first.forcing_table["year"] == 1972, "T"] = -999
    first.trajectory_table.loc[:, "N_total"] = -999
    second = run_common_history(params, "R_J", "base", 8, 9)
    assert float(second.forcing_table.loc[second.forcing_table["year"] == 1972, "T"].iloc[0]) == expected
    assert (second.trajectory_table["N_total"] >= 0).all()
