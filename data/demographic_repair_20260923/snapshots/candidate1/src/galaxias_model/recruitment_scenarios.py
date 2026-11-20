"""Small scenario adapter for qualification of the repaired demographic core.

The archived common model supplies only forcing, exposure and founder schedules.
No old initialization, carrying-capacity conversion or observation score is used.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import pandas as pd

from galaxias_model import common_model
from galaxias_model.recruitment_demography import (
    AnnualConditions,
    Demography,
    RecruitmentLimits,
    advance,
    neutral_equilibrium,
)
from galaxias_model.io import resolve_family_parameters
from galaxias_model.simulation import build_scenario_forcing, get_scenario_definition
from galaxias_model.types import ResolvedParameters


SCENARIOS = ("historical_lake", "lake_oberon", "strathgordon")
STATE_FIELDS = ("J_L", "A_L", "J_R", "A_R")


def reference_demography() -> Demography:
    """Engineering reference, not an empirical prior or fitted parameter set."""
    return Demography(
        juvenile_survival=0.35,
        adult_survival=0.65,
        maturation=0.7,
        recruits_per_adult=4.0,
        lake_settlement=0.7,
    )


def reference_limits() -> dict[str, RecruitmentLimits]:
    """Explicit, illustrative site values, in mean successful recruits/year."""
    return {
        "historical_lake": RecruitmentLimits(lake=105.0, refuge=45.0),
        "lake_oberon": RecruitmentLimits(lake=1050.0, refuge=450.0),
        "strathgordon": RecruitmentLimits(lake=350.0, refuge=150.0),
    }


def reference_forcing_parameters() -> ResolvedParameters:
    return resolve_family_parameters(common_model._model_inputs(), "transient_perfect_storm")


def conditions_from_forcing(
    params: ResolvedParameters,
    forcing_row: dict,
    threat_row: dict,
    restriction: str,
) -> AnnualConditions:
    """Keep common base forcing, normalizing spawning quality at neutrality.

    BH(M*x, M*C) = M*BH(x, C): applying upsurge to potential supply and
    lake recruitment limit retains a linear lake response at a fixed state.
    """
    h = float(forcing_row["H"])
    u = float(forcing_row["U"])
    q0 = (1 - params.value("PR005")) + params.value("PR005") * params.value("PR032")
    q = (1 - params.value("PR005")) * (1 - params.value("PR033") * h)
    q += params.value("PR005") * params.value("PR032")
    if q0 <= 0 or q < 0:
        raise ValueError("Spawning quality must have positive neutral and nonnegative annual values")
    upsurge = 1 + params.value("PR031") * u
    hazards = common_model._exposure_components(
        forcing_row,
        threat_row,
        params,
        common_model._restricted_effects(params, restriction),
        juvenile_climbing_multiplier=1.0,
    )
    return AnnualConditions(
        recruitment_multiplier=(q / q0) * upsurge * float(forcing_row["spawn_habitat_multiplier"]),
        lake_limit_multiplier=upsurge,
        juvenile_lake_hazard=hazards["juvenile_lake_exposure"],
        adult_lake_hazard=hazards["adult_lake_exposure"],
        juvenile_refuge_hazard=hazards["juvenile_refuge_exposure"],
        adult_refuge_hazard=hazards["adult_refuge_exposure"],
        movement_probability=hazards["move_probability"],
    )


def run_scenario(
    demography: Demography,
    limits_by_scenario: Mapping[str, RecruitmentLimits],
    scenario_id: str,
    *,
    forcing_parameters: ResolvedParameters | None = None,
    restriction: str = "R_J",
    seed: int = 0,
    stochastic: bool = False,
) -> pd.DataFrame:
    """Run one small qualification path; no compatibility score is returned.

    Historical runs use base forcing only. Founder additions occur before the
    annual update, as in the existing annual scenario definitions. These are
    coarse annual timings, not a reconstruction of individual release dates.
    """
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario_id!r}")
    if scenario_id not in limits_by_scenario:
        raise ValueError(f"Explicit recruitment limits missing for {scenario_id}")
    if restriction not in common_model.RESTRICTIONS:
        raise ValueError(f"Unknown restriction {restriction!r}")
    params = forcing_parameters if forcing_parameters is not None else reference_forcing_parameters()
    limits = limits_by_scenario[scenario_id]
    definition = get_scenario_definition(common_model._model_inputs(), scenario_id)
    if scenario_id == "historical_lake":
        forcing = common_model._common_historical_forcing(params, overshoot_removed=False)
        equilibrium = neutral_equilibrium(demography, limits)
        if not equilibrium["positive"] or not equilibrium["guard_consistent"]:
            raise ValueError("Historical initialization requires a positive, guard-consistent equilibrium")
        state = dict(equilibrium["state"])
        if stochastic:
            state = {key: float(math.floor(value + 0.5)) for key, value in state.items()}
            if state["A_L"] + state["A_R"] < 2:
                raise ValueError("Rounded historical initialization violates the breeder guard")
    else:
        forcing = build_scenario_forcing(
            definition, list(range(definition.start_year, definition.end_year + 1)), params
        ).table
        state = dict.fromkeys(STATE_FIELDS, 0.0)
    initial_state = dict(state)
    previous_threat = {"connected": 0, "T": 0.0, "P": 0.0, "C_L": 0.0, "C_R": 0.0}
    records = []
    for row in forcing.to_dict(orient="records"):
        year = int(row["year"])
        founders = float(row["founder_addition_A_L"])
        state["A_L"] += founders
        before = dict(state)
        conditions = conditions_from_forcing(params, row, previous_threat, restriction)
        state, diagnostics = advance(
            state, demography, limits, conditions=conditions,
            seed=seed, year=year, stochastic=stochastic,
        )
        records.append({
            "scenario_id": scenario_id,
            "restriction": restriction,
            "seed": seed,
            "year": year,
            "founders_added": founders,
            **{f"pre_{key}": value for key, value in before.items()},
            **state,
            "N_L": state["J_L"] + state["A_L"],
            "N_R": state["J_R"] + state["A_R"],
            "N_total": sum(state.values()),
            **diagnostics,
        })
        previous_threat = row
    result = pd.DataFrame.from_records(records)
    result.attrs["initial_state"] = initial_state
    result.attrs["initialization_rounding"] = bool(stochastic and scenario_id == "historical_lake")
    return result
