from dataclasses import replace

import pandas as pd
import pytest

from galaxias_model import common_model
from galaxias_model.recruitment_demography import RecruitmentLimits
from galaxias_model.recruitment_scenarios import (
    conditions_from_forcing, reference_demography, reference_forcing_parameters,
    reference_limits, run_scenario,
)


def test_limits_are_explicit_and_cannot_leak_across_sites():
    d, limits = reference_demography(), reference_limits()
    with pytest.raises(ValueError, match="Explicit recruitment limits"):
        run_scenario(d, {}, "lake_oberon")
    first = run_scenario(d, limits, "lake_oberon")
    changed = dict(limits, historical_lake=RecruitmentLimits(lake=1, refuge=1))
    pd.testing.assert_frame_equal(first, run_scenario(d, changed, "lake_oberon"))
    own_changed = dict(limits, lake_oberon=RecruitmentLimits(lake=1, refuge=1))
    assert not first.equals(run_scenario(d, own_changed, "lake_oberon"))


def test_retired_fecundity_and_capacity_parameters_do_not_enter_repaired_scenarios():
    params = reference_forcing_parameters()
    values = dict(params.values)
    for key in ("PR004", "PR008", "PR009", "PR010", "PR011", "PR039"):
        values[key] *= 37
    for scenario in ("historical_lake", "lake_oberon", "strathgordon"):
        kwargs = dict(demography=reference_demography(), limits_by_scenario=reference_limits(), scenario_id=scenario)
        expected = run_scenario(**kwargs, forcing_parameters=params)
        actual = run_scenario(**kwargs, forcing_parameters=replace(params, values=values))
        pd.testing.assert_frame_equal(expected, actual)


def test_strathgordon_imposed_switch_and_founder_counts():
    frame = run_scenario(reference_demography(), reference_limits(), "strathgordon")
    assert frame["founders_added"].sum() == 353
    assert (frame.loc[frame.year < 2008, ["J_L", "J_R"]] == 0).all().all()
    assert frame.loc[frame.year == 2008, ["J_L", "J_R"]].sum(axis=1).iloc[0] > 0
    oberon = run_scenario(reference_demography(), reference_limits(), "lake_oberon")
    assert oberon["founders_added"].sum() == 34


def test_normalized_neutral_quality_and_common_null_hazards():
    params = reference_forcing_parameters()
    neutral = dict(H=0, U=0, spawn_habitat_multiplier=1, connected=0, T=0, P=0, C_L=0, C_R=0)
    conditions = conditions_from_forcing(params, neutral, neutral, "R_J")
    assert conditions.recruitment_multiplier == 1
    assert conditions.lake_limit_multiplier == 1
    row = dict(neutral, H=1, U=2, connected=1, T=2, P=3, C_L=.8, C_R=.6)
    habitat = conditions_from_forcing(params, row, row, "R_H")
    assert habitat.adult_refuge_hazard == 0
    assert habitat.adult_lake_hazard == pytest.approx(params.value("PR033"))
    for restriction in common_model.RESTRICTIONS:
        c = conditions_from_forcing(params, row, row, restriction)
        expected = common_model._exposure_components(
            row, row, params, common_model._restricted_effects(params, restriction),
            juvenile_climbing_multiplier=1,
        )
        assert c.adult_lake_hazard == expected["adult_lake_exposure"]
        assert c.adult_refuge_hazard == expected["adult_refuge_exposure"]
        assert c.movement_probability == expected["move_probability"]
