from __future__ import annotations

import math

import pytest

from galaxias_model.recruitment_demography import (
    AnnualConditions,
    Demography,
    RecruitmentLimits,
    advance,
    neutral_equilibrium,
)


def demo(**changes) -> Demography:
    values = dict(juvenile_survival=0.8, adult_survival=0.7, maturation=0.4, recruits_per_adult=2.0, lake_settlement=0.6)
    values.update(changes)
    return Demography(**values)


def test_existing_adult_retention_is_independent_of_fecundity_and_ceilings() -> None:
    state = {"J_L": 0.0, "A_L": 7.0, "J_R": 0.0, "A_R": 3.0}
    low, _ = advance(state, demo(recruits_per_adult=0.0), RecruitmentLimits(0.0, 0.0))
    high, _ = advance(state, demo(recruits_per_adult=100.0), RecruitmentLimits(1e6, 1e6))
    assert low["A_L"] == high["A_L"] == pytest.approx(4.9)
    assert low["A_R"] == high["A_R"] == pytest.approx(2.1)
    assert low["J_L"] == pytest.approx(0.0)
    assert low["J_R"] == pytest.approx(0.0)
    assert high["J_L"] > 0.0
    assert high["J_R"] > 0.0


def test_beverton_holt_is_monotone_and_bounded() -> None:
    limits = RecruitmentLimits(5.0, 5.0)
    d = demo(recruits_per_adult=4.0, lake_settlement=0.5)
    _, one = advance({"J_L": 0.0, "A_L": 2.0, "J_R": 0.0, "A_R": 0.0}, d, limits)
    _, two = advance({"J_L": 0.0, "A_L": 20.0, "J_R": 0.0, "A_R": 0.0}, d, limits)
    assert one["mean_recruits_lake"] < two["mean_recruits_lake"] < 5.0
    assert one["mean_recruits_refuge"] < two["mean_recruits_refuge"] < 5.0
    assert two["mean_recruits_lake"] == pytest.approx(two["mean_recruits_refuge"])


def test_analytic_equilibrium_matches_unguarded_deterministic_step() -> None:
    d = demo(recruits_per_adult=4.0)
    limits = RecruitmentLimits(25.0, 10.0)
    equilibrium = neutral_equilibrium(d, limits)
    assert equilibrium["positive"] is True
    state, diagnostics = advance(equilibrium["state"], d, limits, guard=False)
    for key in state:
        assert state[key] == pytest.approx(equilibrium["state"][key], rel=1e-10, abs=1e-10)
    assert diagnostics["guard_active"] is False


def test_unequal_ceilings_allocate_recruits_by_compartment() -> None:
    d = demo(recruits_per_adult=10.0, lake_settlement=0.5)
    _, diagnostics = advance({"J_L": 0.0, "A_L": 2.0, "J_R": 0.0, "A_R": 0.0}, d, RecruitmentLimits(1.0, 100.0))
    assert diagnostics["mean_recruits_lake"] < diagnostics["mean_recruits_refuge"]
    assert diagnostics["mean_recruits_lake"] < 1.0
    assert diagnostics["mean_recruits_refuge"] < 10.0


def test_newborns_cannot_mature_or_breed_until_two_years_later() -> None:
    d = demo(juvenile_survival=1.0, maturation=1.0, adult_survival=1.0 - 1e-9, recruits_per_adult=2.0)
    limits = RecruitmentLimits(100.0, 100.0)
    initial = {"J_L": 0.0, "A_L": 2.0, "J_R": 0.0, "A_R": 0.0}
    after_one, diag1 = advance(initial, d, limits, guard=False)
    assert after_one["A_L"] == pytest.approx(2.0)
    assert after_one["J_L"] == pytest.approx(diag1["mean_recruits_lake"])
    after_two, diag2 = advance(after_one, d, limits, guard=False, year=1)
    assert after_two["A_L"] == pytest.approx(2.0 + after_one["J_L"])
    assert diag2["prebreeding_adults"] == pytest.approx(2.0)


def test_singleton_and_zero_guard_cannot_rebound() -> None:
    d = demo(recruits_per_adult=1e6)
    limits = RecruitmentLimits(1e6, 1e6)
    singleton, singleton_diag = advance({"J_L": 0.0, "A_L": 1.0, "J_R": 0.0, "A_R": 0.0}, d, limits)
    zero, zero_diag = advance({"J_L": 0.0, "A_L": 0.0, "J_R": 0.0, "A_R": 0.0}, d, limits)
    assert singleton_diag["guard_active"] is True
    assert singleton_diag["realized_recruits_lake"] == 0.0
    assert singleton_diag["realized_recruits_refuge"] == 0.0
    assert singleton["A_L"] < 1.0
    assert all(value == 0.0 for value in zero.values())
    assert zero_diag["guard_active"] is True


def test_fractional_deterministic_closure_and_stochastic_rejection() -> None:
    fractional = {"J_L": 1.5, "A_L": 2.0, "J_R": 0.0, "A_R": 0.0}
    next_state, _ = advance(fractional, demo(), RecruitmentLimits(10.0, 10.0))
    assert all(isinstance(value, float) for value in next_state.values())
    with pytest.raises(ValueError, match="integer state"):
        advance(fractional, demo(), RecruitmentLimits(10.0, 10.0), stochastic=True)


def test_guarded_low_capacity_deterministic_closure_is_finite() -> None:
    state, diagnostics = advance(
        {"J_L": 0.0, "A_L": 2.0, "J_R": 0.0, "A_R": 0.0},
        demo(recruits_per_adult=100.0),
        RecruitmentLimits(0.01, 0.01),
    )
    assert diagnostics["guard_active"] is False
    assert diagnostics["mean_recruits_lake"] < 0.01
    assert diagnostics["mean_recruits_refuge"] < 0.01
    assert all(value >= 0.0 and math.isfinite(value) for value in state.values())


def test_subcritical_equilibrium_is_zero() -> None:
    d = demo(recruits_per_adult=0.01)
    equilibrium = neutral_equilibrium(d, RecruitmentLimits(100.0, 100.0))
    assert equilibrium["positive"] is False
    assert equilibrium["adult_total"] == 0.0
    assert all(value == 0.0 for value in equilibrium["state"].values())
    assert equilibrium["adult_fraction"] > 0.0


def test_exact_replacement_boundary_has_no_spurious_positive_equilibrium() -> None:
    s, a, m = .15, .45, .5
    threshold = (1-a) * (1-s*(1-m)) / (s*m)
    d = demo(juvenile_survival=s, adult_survival=a, maturation=m,
             recruits_per_adult=threshold, lake_settlement=.7)
    equilibrium = neutral_equilibrium(d, RecruitmentLimits(105,45))
    assert equilibrium["effective_low_density_recruits_per_adult"] == threshold
    assert equilibrium["positive"] is False
    assert equilibrium["adult_total"] == 0


def test_beverton_holt_handles_extreme_finite_inputs() -> None:
    d = demo(recruits_per_adult=1e308, lake_settlement=1.0)
    state, diagnostics = advance(
        {"J_L": 0.0, "A_L": 1.0, "J_R": 0.0, "A_R": 0.0},
        d,
        RecruitmentLimits(1e308, 0.0),
        guard=False,
    )
    assert math.isfinite(diagnostics["mean_recruits_lake"])
    assert diagnostics["mean_recruits_lake"] <= 1e308
    assert all(math.isfinite(value) and value >= 0.0 for value in state.values())


def test_stochastic_output_is_integer_nonnegative_and_reproducible() -> None:
    d = demo(recruits_per_adult=4.0)
    limits = RecruitmentLimits(20.0, 20.0)
    state = {"J_L": 10, "A_L": 8, "J_R": 7, "A_R": 4}
    conditions = AnnualConditions(juvenile_lake_hazard=0.2, movement_probability=0.25)
    first, first_diag = advance(state, d, limits, conditions=conditions, seed=42, year=3, stochastic=True, guard=False)
    second, second_diag = advance(state, d, limits, conditions=conditions, seed=42, year=3, stochastic=True, guard=False)
    assert first == second
    assert first_diag["realized_recruits_lake"] == second_diag["realized_recruits_lake"]
    assert first_diag["realized_recruits_refuge"] == second_diag["realized_recruits_refuge"]
    assert all(value >= 0 and value == math.floor(value) for value in first.values())


def test_hazard_and_movement_preserve_the_post_survival_total() -> None:
    d = demo(juvenile_survival=1.0, maturation=0.5, adult_survival=1.0 - 1e-9, recruits_per_adult=0.0)
    before = {"J_L": 10.0, "A_L": 8.0, "J_R": 5.0, "A_R": 4.0}
    no_movement, _ = advance(before, d, RecruitmentLimits(0.0, 0.0), conditions=AnnualConditions(), guard=False)
    moved, _ = advance(
        before,
        d,
        RecruitmentLimits(0.0, 0.0),
        conditions=AnnualConditions(movement_probability=0.4),
        guard=False,
    )
    assert sum(moved.values()) == pytest.approx(sum(no_movement.values()))
    assert moved["J_R"] > no_movement["J_R"]
    assert moved["A_R"] > no_movement["A_R"]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Demography(0.8, 0.7, 0.4, -1.0, 0.5),
        lambda: Demography(0.8, 0.7, 0.4, 2.0, 1.2),
        lambda: RecruitmentLimits(-1.0, 2.0),
        lambda: AnnualConditions(movement_probability=1.1),
        lambda: AnnualConditions(juvenile_lake_hazard=-1.0),
    ],
)
def test_parameter_input_failure(factory) -> None:
    with pytest.raises(ValueError):
        factory()


@pytest.mark.parametrize("seed, year", [(-1, 0), (0, -1)])
def test_seed_and_year_must_be_nonnegative(seed: int, year: int) -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        advance(
            {"J_L": 0.0, "A_L": 2.0, "J_R": 0.0, "A_R": 0.0},
            demo(),
            RecruitmentLimits(10.0, 10.0),
            seed=seed,
            year=year,
        )


@pytest.mark.parametrize(
    "d",
    [
        Demography(0.0, 0.7, 0.4, 2.0, 0.5),
        Demography(0.8, 1.0, 0.4, 2.0, 0.5),
        Demography(0.8, 0.7, 0.0, 2.0, 0.5),
    ],
)
def test_equilibrium_rejects_nonstationary_boundary_parameters(d: Demography) -> None:
    with pytest.raises(ValueError, match="neutral equilibrium"):
        neutral_equilibrium(d, RecruitmentLimits(10.0, 10.0))
