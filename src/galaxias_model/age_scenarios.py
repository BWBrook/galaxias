"""Threat adapter for the age-structured candidate, not a historical fit driver.

Only common-model forcing and effect restrictions are reused. Site scales,
initial states, dated founders and observations must be supplied separately.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np

from galaxias_model import common_model
from galaxias_model.age_demography import AgeConditions, AgeDemography, CountEvent
from galaxias_model.types import ResolvedParameters


def reference_demography(max_age: int = 6) -> AgeDemography:
    """Synthetic engineering reference; these values are not fitted priors."""
    if max_age not in (6, 8):
        raise ValueError("candidate lifespan scenario must be six or eight")
    return AgeDemography(
        annual_survival=(0.35, 0.6) + (0.5,) * (max_age - 2),
        breeding_probability=(0.0, 0.0, 0.25) + (1.0,) * (max_age - 2),
        recruits_per_female=20.0,
        lake_settlement=0.95,
    )


def conditions_from_forcing(
    demography: AgeDemography,
    params: ResolvedParameters,
    forcing_row: Mapping[str, float],
    threat_row: Mapping[str, float],
    restriction: str,
    *,
    post_habitat_refuge_fraction: float,
    recruitment_sigma: float,
) -> AgeConditions:
    """Use current habitat forcing and explicitly supplied lagged invaders.

    Climbing hazard affects only nursery fish: the post-hatch month and the
    next eleven months. Habitat/trout hazards continue across cohort ages.
    Habitat also modifies spawning quality and the refuge recruitment limit.
    """
    eta = float(post_habitat_refuge_fraction)
    if not math.isfinite(eta) or not 0 < eta <= 1:
        raise ValueError("post_habitat_refuge_fraction must be in (0, 1]")
    h = float(forcing_row["H"])
    if not 0 <= h <= 1:
        raise ValueError("habitat transition must be in [0, 1]")
    effects = common_model._restricted_effects(params, restriction)
    connected = float(threat_row.get("connected", 0.0))
    refuge_exposure = 1 - params.value("PR034")
    trout = float(threat_row["T"]) * float(threat_row["P"])
    adult_lake = params.value("PR033") * h + connected * effects["PR020"] * trout
    adult_refuge = connected * effects["PR021"] * trout * refuge_exposure
    climb_lake = connected * effects["PR027"] * float(threat_row["C_L"])
    climb_refuge = connected * effects["PR028"] * float(threat_row["C_R"]) * refuge_exposure
    old_lake = np.full(demography.max_age, adult_lake)
    old_refuge = np.full(demography.max_age, adult_refuge)
    old_lake[0] += climb_lake
    old_refuge[0] += climb_refuge
    q0 = (1 - params.value("PR005")) + params.value("PR005") * params.value("PR032")
    qh = (1 - params.value("PR005")) * (1 - params.value("PR033") * h)
    qh += params.value("PR005") * params.value("PR032")
    if q0 <= 0 or qh < 0:
        raise ValueError("spawning quality requires positive neutral and nonnegative annual values")
    upsurge = 1 + params.value("PR031") * float(forcing_row["U"])
    result = AgeConditions(
        old_hazard_lake=old_lake,
        old_hazard_refuge=old_refuge,
        late_hazard_lake=np.full(demography.max_age, adult_lake),
        late_hazard_refuge=np.full(demography.max_age, adult_refuge),
        newborn_hazard_lake=adult_lake + climb_lake,
        newborn_hazard_refuge=adult_refuge + climb_refuge,
        birth_hazard_fraction=1 / 12,
        movement_probability=params.value("PR007") * (-math.expm1(-adult_lake)),
        recruitment_multiplier=qh / q0 * upsurge * float(forcing_row["spawn_habitat_multiplier"]),
        lake_limit_multiplier=upsurge,
        refuge_limit_multiplier=1 - (1 - eta) * h,
        recruitment_sigma=recruitment_sigma,
    )
    result.validate(demography.max_age)
    return result


def strathgordon_spawn_multiplier(year: int, *, pre_2007: float) -> float:
    """April 2008 juveniles follow the 2007 spawning season in this calendar.

    A small pre-2007 value is a declared habitat scenario, not a claim that
    nondetection proves no breeding. It must be supplied, never inferred here.
    """
    if not math.isfinite(pre_2007) or not 0 <= pre_2007 <= 1:
        raise ValueError("pre_2007 must be in [0, 1]")
    return pre_2007 if year < 2007 else 1.0


def complete_event_calendar(
    calendar: Sequence[CountEvent], operations: Mapping[int, CountEvent],
) -> tuple[CountEvent, ...]:
    """Materialize no-op checkpoints in every arm using a frozen calendar.

    Survival draws depend on breakpoints. Omitting a zero-effect event is not
    stream-preserving; a calendar change requires new replay qualification.
    """
    ids = {event.event_id for event in calendar}
    if len(ids) != len(calendar) or not set(operations).issubset(ids):
        raise ValueError("calendar IDs must be unique and cover every operation")
    result = []
    for point in calendar:
        if point.remove_count != 0 or point.addition is not None:
            raise ValueError("calendar entries must be no-op checkpoints")
        event = operations.get(point.event_id, point)
        if (event.event_id, event.time, event.compartment) != (point.event_id, point.time, point.compartment):
            raise ValueError("operation must retain calendar ID, time and compartment")
        result.append(event)
    return tuple(sorted(result, key=lambda event: (event.time, event.event_id)))
