from __future__ import annotations

import math

import numpy as np
import pytest

from galaxias_model.age_demography import (
    AgeConditions,
    AgeDemography,
    CountEvent,
    RecruitmentLimits,
    advance,
    neutral_equilibrium_from_abundance,
    zero_state,
)


def demo(*, max_age: int = 4, survival: float = 1.0, b: float = 3.0,
         lake_weight: float = 0.5) -> AgeDemography:
    return AgeDemography(
        annual_survival=(survival,) * max_age,
        breeding_probability=(0.0, 0.0) + (1.0,) * (max_age - 1),
        recruits_per_female=b,
        lake_settlement=lake_weight,
    )


def test_state_shape_and_analytic_neutral_fixed_point() -> None:
    d = demo(max_age=4, survival=0.8, b=8.0, lake_weight=0.6)
    equilibrium = neutral_equilibrium_from_abundance(d, 100.0, 60.0)
    state, diagnostics = advance(equilibrium["state"], d, equilibrium["limits"])
    np.testing.assert_allclose(state, equilibrium["state"], rtol=1e-11, atol=1e-11)
    assert diagnostics["mean_field_breeding"] is True
    assert equilibrium["mate_consistent"] is True
    assert zero_state(d).shape == (2, 2, 5)


def test_breeding_delay_and_terminal_ageout() -> None:
    d = demo(max_age=4, survival=1.0, b=0.0)
    state = zero_state(d)
    state[0, :, 0] = 20.0
    first, first_diag = advance(state, d, RecruitmentLimits(0.0, 0.0))
    assert first_diag["pre_spawn_females"] == 0.0
    assert first[0, :, 1].sum() == 40.0
    second, second_diag = advance(first, d, RecruitmentLimits(0.0, 0.0))
    assert second_diag["pre_spawn_females"] == 20.0
    assert second[0, :, 2].sum() == 40.0
    terminal = second.copy()
    terminal[0, :, d.max_age] = 7.0
    after, diagnostics = advance(terminal, d, RecruitmentLimits(0.0, 0.0))
    assert diagnostics["ageout_total"] == 14.0
    assert after[:, :, d.max_age].sum() == 0.0


def test_one_sex_population_cannot_recruit_and_sexes_persist() -> None:
    d = demo(max_age=4, survival=1.0, b=10.0)
    state = zero_state(d)
    state[0, 0, 2] = 20
    result, diagnostics = advance(state, d, RecruitmentLimits(100.0, 100.0))
    assert diagnostics["breeding_gate"] is False
    assert result[:, 1, 0].sum() == 0.0
    assert result[0, 0, 3] == 20.0


def test_recruitment_multiplier_is_before_bh_and_limit_scaling_is_homogeneous() -> None:
    d = demo(max_age=4, survival=1.0, b=2.0, lake_weight=1.0)
    state = zero_state(d)
    state[0, :, 2] = (100.0, 100.0)
    baseline, base_diag = advance(state, d, RecruitmentLimits(10.0, 0.0))
    scaled, scaled_diag = advance(
        state,
        d,
        RecruitmentLimits(10.0, 0.0),
        conditions=AgeConditions(recruitment_multiplier=2.0, lake_limit_multiplier=2.0),
    )
    assert scaled_diag["raw_supply_lake"] == pytest.approx(2.0 * base_diag["raw_supply_lake"])
    assert scaled_diag["marginal_recruits_before_hazard_lake"] == pytest.approx(2.0 * base_diag["marginal_recruits_before_hazard_lake"])
    assert scaled[0, :, 0].sum() == pytest.approx(2.0 * baseline[0, :, 0].sum())


def test_stochastic_recruitment_is_reproducible_by_site_and_integer() -> None:
    d = demo(max_age=4, survival=1.0, b=4.0)
    state = zero_state(d)
    state[0, :, 2] = 20
    state[1, :, 2] = 20
    c = AgeConditions(recruitment_sigma=0.4, movement_probability=0.25)
    first, first_diag = advance(state, d, RecruitmentLimits(100.0, 100.0),
                                conditions=c, seed=19, year=3, site_id="A", stochastic=True)
    second, second_diag = advance(state, d, RecruitmentLimits(100.0, 100.0),
                                  conditions=c, seed=19, year=3, site_id="A", stochastic=True)
    other, _ = advance(state, d, RecruitmentLimits(100.0, 100.0),
                       conditions=c, seed=19, year=3, site_id="B", stochastic=True)
    np.testing.assert_array_equal(first, second)
    assert first_diag["environment_multiplier"] == second_diag["environment_multiplier"]
    assert np.all(first >= 0) and np.all(first == np.floor(first))
    assert not np.array_equal(first, other)


def test_lognormal_environment_is_mean_one_and_deterministic_is_one() -> None:
    d = demo(max_age=4, survival=1.0, b=4.0)
    state = zero_state(d)
    state[0, :, 2] = 20
    limits = RecruitmentLimits(100.0, 100.0)
    deterministic, dd = advance(state, d, limits, conditions=AgeConditions(recruitment_sigma=2.0))
    assert dd["environment_multiplier"] == 1.0
    multipliers = [advance(state, d, limits, conditions=AgeConditions(recruitment_sigma=0.3),
                           seed=i, year=0, site_id="site", stochastic=True)[1]["environment_multiplier"]
                   for i in range(300)]
    assert math.isclose(float(np.mean(multipliers)), 1.0, rel_tol=0.15)
    assert deterministic.shape == state.shape


def test_movement_conserves_sex_age_counts_and_newborns_stay() -> None:
    d = demo(max_age=4, survival=1.0, b=0.0)
    state = zero_state(d)
    state[0, :, 2] = (8, 11)
    before, _ = advance(state, d, RecruitmentLimits(0.0, 0.0),
                        conditions=AgeConditions(movement_probability=0.0))
    after, _ = advance(state, d, RecruitmentLimits(0.0, 0.0),
                       conditions=AgeConditions(movement_probability=1.0))
    assert after[:, :, 1:].sum() == pytest.approx(before[:, :, 1:].sum())
    assert after[0, :, 0].sum() == 0.0
    assert after[1, :, 3].sum() == pytest.approx(before[0, :, 3].sum())


def test_dated_event_removes_before_spawn_and_reports_pre_event_state() -> None:
    d = demo(max_age=4, survival=1.0, b=10.0)
    state = zero_state(d)
    state[0, 0, 2] = 10
    state[0, 1, 2] = 1
    event = CountEvent(7, 0.5, 0, remove_count=1, min_start_age=2)
    result, diagnostics = advance(state, d, RecruitmentLimits(100.0, 100.0), events=(event,))
    event_diag = diagnostics["event_diagnostics"][0]
    assert event_diag["pre_event_eligible_count"] > 0
    assert event_diag["pre_event_state"].shape == state.shape
    assert diagnostics["pre_spawn_males"] > 0.0
    assert result[0, :, 0].sum() > 0.0


def test_postspawn_addition_age_zero_is_start_year_cohort_and_terminal_is_rejected() -> None:
    d = demo(max_age=4)
    state = zero_state(d)
    addition = np.zeros((2, d.max_age + 1))
    addition[0, 0] = 2.0
    result, _ = advance(state, d, RecruitmentLimits(0.0, 0.0),
                        events=(CountEvent(8, 0.9, 0, addition=addition),))
    assert result[0, 0, 1] == pytest.approx(2.0)
    terminal = addition.copy()
    terminal[0, d.max_age] = 1.0
    with pytest.raises(ValueError, match="terminal"):
        advance(state, d, RecruitmentLimits(0.0, 0.0),
                events=(CountEvent(9, 0.1, 0, addition=terminal),))


def test_insufficient_removal_and_fractional_stochastic_state_are_rejected() -> None:
    d = demo()
    with pytest.raises(ValueError, match="separate event IDs"):
        CountEvent(1, .2, 0, remove_count=1, addition=np.zeros((2, d.max_age + 1)))
    with pytest.raises(ValueError, match="more fish"):
        advance(zero_state(d), d, RecruitmentLimits(0.0, 0.0),
                events=(CountEvent(1, 0.2, 0, remove_count=1),))
    state = zero_state(d)
    state[0, 0, 2] = 0.5
    with pytest.raises(ValueError, match="integer state"):
        advance(state, d, RecruitmentLimits(0.0, 0.0), stochastic=True)


def test_birth_and_next_year_nursery_hazards_sum_to_one_cohort_year() -> None:
    d = demo(max_age=4, survival=1.0, b=2.0)
    state = zero_state(d)
    state[0, :, 2] = 10
    conditions = AgeConditions(
        newborn_hazard_lake=1.0,
        old_hazard_lake=(1.0,) * d.max_age,
        late_hazard_lake=(0.0,) * d.max_age,
    )
    result, diagnostics = advance(state, d, RecruitmentLimits(100.0, 0.0), conditions=conditions)
    expected_bh = diagnostics["marginal_recruits_before_hazard_lake"]
    assert result[0, :, 0].sum() == pytest.approx(expected_bh * math.exp(-1.0 / 12.0))
    next_state, _ = advance(result, d, RecruitmentLimits(0.0, 0.0), conditions=conditions)
    assert next_state[0, :, 1].sum() == pytest.approx(result[0, :, 0].sum() * math.exp(-11.0 / 12.0))


def test_existing_adult_retention_is_independent_of_b_and_limits() -> None:
    state = zero_state(demo(max_age=4, survival=0.8))
    state[0, :, 2] = (10.0, 5.0)
    low, _ = advance(state, demo(max_age=4, survival=0.8, b=0.0), RecruitmentLimits(0.0, 0.0))
    high, _ = advance(state, demo(max_age=4, survival=0.8, b=100.0), RecruitmentLimits(1000.0, 1000.0))
    assert low[0, :, 3].sum() == pytest.approx(12.0)
    assert high[0, :, 3].sum() == pytest.approx(low[0, :, 3].sum())


@pytest.mark.parametrize("max_age", [6, 8])
def test_max_age_scenarios_have_exact_terminal_ageout(max_age: int) -> None:
    d = demo(max_age=max_age, survival=1.0, b=0.0)
    state = zero_state(d)
    state[0, :, max_age - 1] = (3.0, 4.0)
    first, _ = advance(state, d, RecruitmentLimits(0.0, 0.0))
    assert first[0, :, max_age].sum() == 7.0
    second, diagnostics = advance(first, d, RecruitmentLimits(0.0, 0.0))
    assert diagnostics["ageout_total"] == 7.0
    assert second[:, :, max_age].sum() == 0.0


def test_stochastic_zero_male_blocks_and_one_male_satisfies_gate() -> None:
    d = demo(max_age=4, survival=1.0, b=4.0)
    state = zero_state(d)
    state[0, 0, 2] = 10
    no_male, no_male_diag = advance(state, d, RecruitmentLimits(100.0, 100.0), stochastic=True, seed=1)
    assert no_male_diag["breeding_gate"] is False
    assert no_male_diag["drawn_recruits_before_hazard"].sum() == 0.0
    state[0, 1, 2] = 1
    one_male, one_male_diag = advance(state, d, RecruitmentLimits(100.0, 100.0), stochastic=True, seed=1)
    assert one_male_diag["pre_spawn_males"] == 1.0
    assert one_male_diag["breeding_gate"] is True
    assert one_male_diag["conditional_recruits_before_hazard"][0] > 0.0
    with pytest.raises(ValueError, match="unachievable"):
        neutral_equilibrium_from_abundance(demo(b=0.01), 10.0, 10.0)
