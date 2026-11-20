"""Bounded two-compartment, two-stage recruitment demography.

The kernel is deliberately small and prospective.  It represents a pooled
breeding population in two compartments (lake ``L`` and refuge ``R``), with
juveniles (``J``) and next-season breeders (``A``).  Beverton--Holt density
dependence acts only on incoming juvenile establishment; existing fish are
never density-thinned.  No persistent sex or spatial-mating state is implied.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Any

import numpy as np


STATE_KEYS = ("J_L", "A_L", "J_R", "A_R")


def _validate_real(name: str, value: Any, *, minimum: float | None = None, maximum: float | None = None) -> float:
    """Validate a scalar without accepting strings or silently coercing them."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return result


@dataclass(frozen=True)
class Demography:
    """Base annual demographic probabilities and recruitment allocation."""

    juvenile_survival: float
    adult_survival: float
    maturation: float
    recruits_per_adult: float
    lake_settlement: float

    def __post_init__(self) -> None:
        _validate_real("juvenile_survival", self.juvenile_survival, minimum=0.0, maximum=1.0)
        _validate_real("adult_survival", self.adult_survival, minimum=0.0, maximum=1.0)
        _validate_real("maturation", self.maturation, minimum=0.0, maximum=1.0)
        _validate_real("recruits_per_adult", self.recruits_per_adult, minimum=0.0)
        _validate_real("lake_settlement", self.lake_settlement, minimum=0.0, maximum=1.0)


@dataclass(frozen=True)
class RecruitmentLimits:
    """Annual juvenile establishment ceilings, rather than standing capacities."""

    lake: float
    refuge: float

    def __post_init__(self) -> None:
        _validate_real("lake recruitment limit", self.lake, minimum=0.0)
        _validate_real("refuge recruitment limit", self.refuge, minimum=0.0)


@dataclass(frozen=True)
class AnnualConditions:
    """Annual multipliers, hazards, and one-way lake-to-refuge movement."""

    recruitment_multiplier: float = 1.0
    lake_limit_multiplier: float = 1.0
    refuge_limit_multiplier: float = 1.0
    juvenile_survival: float | None = None
    juvenile_lake_hazard: float = 0.0
    adult_lake_hazard: float = 0.0
    juvenile_refuge_hazard: float = 0.0
    adult_refuge_hazard: float = 0.0
    movement_probability: float = 0.0

    def __post_init__(self) -> None:
        _validate_real("recruitment_multiplier", self.recruitment_multiplier, minimum=0.0)
        _validate_real("lake_limit_multiplier", self.lake_limit_multiplier, minimum=0.0)
        _validate_real("refuge_limit_multiplier", self.refuge_limit_multiplier, minimum=0.0)
        if self.juvenile_survival is not None:
            _validate_real("juvenile_survival condition", self.juvenile_survival, minimum=0.0, maximum=1.0)
        for name in (
            "juvenile_lake_hazard",
            "adult_lake_hazard",
            "juvenile_refuge_hazard",
            "adult_refuge_hazard",
        ):
            _validate_real(name, getattr(self, name), minimum=0.0)
        _validate_real("movement_probability", self.movement_probability, minimum=0.0, maximum=1.0)


def _validate_state(state: dict[str, Any], *, stochastic: bool) -> dict[str, float]:
    if not isinstance(state, dict) or set(state) != set(STATE_KEYS):
        raise ValueError(f"state must contain exactly {STATE_KEYS}")
    result: dict[str, float] = {}
    for key in STATE_KEYS:
        value = _validate_real(f"state[{key!r}]", state[key], minimum=0.0)
        if stochastic and value != math.floor(value):
            raise ValueError("stochastic advance requires integer state values")
        result[key] = value
    return result


def _draw_binomial(rng: np.random.Generator, n: float, probability: float, stochastic: bool) -> float:
    if stochastic:
        return float(rng.binomial(int(n), probability))
    return n * probability


def _draw_poisson(rng: np.random.Generator, mean: float, stochastic: bool) -> float:
    if stochastic:
        return float(rng.poisson(mean))
    return mean


def _stable_bh(supply: float, ceiling: float) -> float:
    if supply <= 0.0 or ceiling <= 0.0:
        return 0.0
    # Avoid both the sum and product overflowing when finite inputs are near
    # the largest representable floating-point values.
    if supply <= ceiling:
        return supply / (1.0 + supply / ceiling)
    return ceiling / (1.0 + ceiling / supply)


def advance(
    state: dict[str, Any],
    demography: Demography,
    limits: RecruitmentLimits,
    *,
    conditions: AnnualConditions | None = None,
    seed: int = 0,
    year: int = 0,
    stochastic: bool = False,
    guard: bool = True,
) -> tuple[dict[str, float], dict[str, Any]]:
    """Advance one annual census interval.

    Births use pre-step breeders.  Old juveniles survive and mature before new
    recruits are added, so a newborn cannot mature or breed in the same year.
    In stochastic mode every count must be an integer and the 18 event streams
    are keyed by their historical event positions.
    """
    if not isinstance(demography, Demography) or not isinstance(limits, RecruitmentLimits):
        raise TypeError("demography and limits must use the public dataclasses")
    if conditions is None:
        conditions = AnnualConditions()
    elif not isinstance(conditions, AnnualConditions):
        raise TypeError("conditions must be AnnualConditions or None")
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, (int, np.integer)):
        raise ValueError("seed must be an integer")
    if isinstance(year, (bool, np.bool_)) or not isinstance(year, (int, np.integer)):
        raise ValueError("year must be an integer")
    if int(seed) < 0 or int(year) < 0:
        raise ValueError("seed and year must be nonnegative")
    state0 = _validate_state(state, stochastic=stochastic)

    old_j_l, old_a_l = state0["J_L"], state0["A_L"]
    old_j_r, old_a_r = state0["J_R"], state0["A_R"]
    prebreeding_a = old_a_l + old_a_r
    guard_active = bool(guard and prebreeding_a < 2.0)
    recruitment_multiplier = conditions.recruitment_multiplier
    lake_weight = demography.lake_settlement
    refuge_weight = 1.0 - lake_weight
    raw_supply = {
        "lake": demography.recruits_per_adult * prebreeding_a * recruitment_multiplier * lake_weight,
        "refuge": demography.recruits_per_adult * prebreeding_a * recruitment_multiplier * refuge_weight,
    }
    if guard_active:
        raw_supply = {"lake": 0.0, "refuge": 0.0}
    ceilings = {
        "lake": limits.lake * conditions.lake_limit_multiplier,
        "refuge": limits.refuge * conditions.refuge_limit_multiplier,
    }
    if any(not math.isfinite(value) for value in (*raw_supply.values(), *ceilings.values())):
        raise ValueError("effective recruitment supply or limit must be finite")
    mean_recruits = {compartment: _stable_bh(raw_supply[compartment], ceilings[compartment]) for compartment in ("lake", "refuge")}

    streams: list[np.random.Generator] | None = None
    if stochastic:
        children = np.random.SeedSequence([int(seed), int(year)]).spawn(18)
        streams = [np.random.default_rng(child) for child in children]
    def draw_poisson(index: int, mean: float) -> float:
        return _draw_poisson(streams[index], mean, True) if streams is not None else mean
    def draw_binomial(index: int, n: float, probability: float) -> float:
        return _draw_binomial(streams[index], n, probability, True) if streams is not None else n * probability

    realized_recruits = {
        "lake": draw_poisson(0, mean_recruits["lake"]),
        "refuge": draw_poisson(1, mean_recruits["refuge"]),
    }
    juvenile_survival = demography.juvenile_survival if conditions.juvenile_survival is None else conditions.juvenile_survival
    old_j_survived = {
        "lake": draw_binomial(2, old_j_l, juvenile_survival),
        "refuge": draw_binomial(3, old_j_r, juvenile_survival),
    }
    survived_existing_adults = {
        "lake": draw_binomial(4, old_a_l, demography.adult_survival),
        "refuge": draw_binomial(5, old_a_r, demography.adult_survival),
    }
    matured = {
        "lake": draw_binomial(6, old_j_survived["lake"], demography.maturation),
        "refuge": draw_binomial(7, old_j_survived["refuge"], demography.maturation),
    }
    juvenile = {
        "lake": old_j_survived["lake"] - matured["lake"] + realized_recruits["lake"],
        "refuge": old_j_survived["refuge"] - matured["refuge"] + realized_recruits["refuge"],
    }
    adult = {
        "lake": survived_existing_adults["lake"] + matured["lake"],
        "refuge": survived_existing_adults["refuge"] + matured["refuge"],
    }

    hazard_probabilities = {
        "juvenile_lake": math.exp(-conditions.juvenile_lake_hazard),
        "adult_lake": math.exp(-conditions.adult_lake_hazard),
        "juvenile_refuge": math.exp(-conditions.juvenile_refuge_hazard),
        "adult_refuge": math.exp(-conditions.adult_refuge_hazard),
    }
    juvenile["lake"] = draw_binomial(12, juvenile["lake"], hazard_probabilities["juvenile_lake"])
    adult["lake"] = draw_binomial(13, adult["lake"], hazard_probabilities["adult_lake"])
    juvenile["refuge"] = draw_binomial(14, juvenile["refuge"], hazard_probabilities["juvenile_refuge"])
    adult["refuge"] = draw_binomial(15, adult["refuge"], hazard_probabilities["adult_refuge"])

    movement = conditions.movement_probability
    moved_juvenile = draw_binomial(16, juvenile["lake"], movement)
    moved_adult = draw_binomial(17, adult["lake"], movement)
    juvenile["lake"] -= moved_juvenile
    juvenile["refuge"] += moved_juvenile
    adult["lake"] -= moved_adult
    adult["refuge"] += moved_adult

    next_state = {"J_L": juvenile["lake"], "A_L": adult["lake"], "J_R": juvenile["refuge"], "A_R": adult["refuge"]}
    diagnostics: dict[str, Any] = {
        "prebreeding_adults": prebreeding_a,
        "guard_active": guard_active,
        "raw_supply_lake": raw_supply["lake"],
        "raw_supply_refuge": raw_supply["refuge"],
        "mean_recruits_lake": mean_recruits["lake"],
        "mean_recruits_refuge": mean_recruits["refuge"],
        "realized_recruits_lake": realized_recruits["lake"],
        "realized_recruits_refuge": realized_recruits["refuge"],
        "baseline_adult_survival": demography.adult_survival,
        "expected_existing_adults_lake": old_a_l * demography.adult_survival,
        "expected_existing_adults_refuge": old_a_r * demography.adult_survival,
        "expected_existing_adults_total": prebreeding_a * demography.adult_survival,
        "survived_existing_adults_lake": survived_existing_adults["lake"],
        "survived_existing_adults_refuge": survived_existing_adults["refuge"],
        "survived_existing_adults_total": survived_existing_adults["lake"] + survived_existing_adults["refuge"],
    }
    return next_state, diagnostics


def neutral_equilibrium(demography: Demography, limits: RecruitmentLimits) -> dict[str, Any]:
    """Return the unguarded analytic fixed point for neutral conditions.

    The returned state is never forced above the singleton guard.  If the
    positive equilibrium would contain fewer than two adults, the metadata
    reports ``guard_consistent=False`` so callers can reject that interpretation.
    """
    if not isinstance(demography, Demography) or not isinstance(limits, RecruitmentLimits):
        raise TypeError("demography and limits must use the public dataclasses")
    s = demography.juvenile_survival
    m = demography.maturation
    a = demography.adult_survival
    if s <= 0.0 or m <= 0.0 or a >= 1.0:
        raise ValueError("neutral equilibrium requires juvenile_survival > 0, maturation > 0, and adult_survival < 1")
    critical = (1.0 - a) * (1.0 - s * (1.0 - m)) / (s * m)
    adult_fraction = s * m / (1.0 - a + s * m)
    weights = (demography.lake_settlement, 1.0 - demography.lake_settlement)
    capacities = (limits.lake, limits.refuge)
    effective_low_density = sum(
        demography.recruits_per_adult * weight
        for weight, capacity in zip(weights, capacities)
        if capacity > 0.0
    )
    metadata: dict[str, Any] = {
        "state": {key: 0.0 for key in STATE_KEYS},
        "critical_recruits_per_adult": critical,
        "adult_fraction": adult_fraction,
        "adult_total": 0.0,
        "positive": False,
        "guard_consistent": True,
        "effective_low_density_recruits_per_adult": effective_low_density,
    }
    if effective_low_density <= critical or sum(capacities) <= 0.0:
        return metadata

    total_capacity = sum(capacities)
    lower, upper = 0.0, total_capacity / critical

    def per_adult_recruitment(adult_total: float) -> float:
        return sum(
            weight * demography.recruits_per_adult
            / (1.0 + weight * demography.recruits_per_adult * adult_total / capacity)
            for weight, capacity in zip(weights, capacities)
            if capacity > 0.0 and weight > 0.0
        )

    for _ in range(80):
        midpoint = (lower + upper) / 2.0
        if per_adult_recruitment(midpoint) > critical:
            lower = midpoint
        else:
            upper = midpoint
    adult_total = (lower + upper) / 2.0
    recruitment_by_compartment = [
        _stable_bh(weight * demography.recruits_per_adult * adult_total, capacity)
        for weight, capacity in zip(weights, capacities)
    ]
    adult_lake = recruitment_by_compartment[0] / critical
    adult_refuge = recruitment_by_compartment[1] / critical
    juvenile_ratio = (1.0 - a) / (s * m)
    state = {
        "J_L": juvenile_ratio * adult_lake,
        "A_L": adult_lake,
        "J_R": juvenile_ratio * adult_refuge,
        "A_R": adult_refuge,
    }
    metadata.update(
        state=state,
        adult_total=adult_total,
        positive=True,
        guard_consistent=adult_total >= 2.0,
    )
    return metadata


__all__ = ["AnnualConditions", "Demography", "RecruitmentLimits", "advance", "neutral_equilibrium"]
