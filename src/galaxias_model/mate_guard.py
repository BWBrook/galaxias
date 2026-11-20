"""Versioned common-model kernel with a singleton breeding guard.

This module is deliberately separate from both the frozen common-model kernel
and :mod:`galaxias_model.simulation`.  It keeps the common-model public API and
event-keyed streams while setting recruitment to zero when the pre-breeding
adult total is below two.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pandas as pd

from galaxias_model.abundance_detection import COMMON_EPISODE_FIELDS
from galaxias_model.io import load_model_inputs
from galaxias_model.simulation import (
    _build_record,
    _draw_binomial,
    _draw_poisson,
    _latent_capacities,
    build_scenario_forcing,
    get_scenario_definition,
)
from galaxias_model.types import ResolvedParameters


CONFIGURATIONS = (
    "base",
    "env_rho_002",
    "env_rho_010",
    "juvenile_climbing",
    "minimum_dated_adult_first",
    "minimum_dated_juvenile_first",
)
RESTRICTIONS = ("R_H", "R_T", "R_C", "R_J")

_ROOT = Path(__file__).resolve().parents[2]
_EPS = 1e-9
_ENVIRONMENT_RHO = {"env_rho_002": 0.02, "env_rho_010": 0.10}
_REMOVAL_CONFIGURATIONS = {
    "minimum_dated_adult_first",
    "minimum_dated_juvenile_first",
}
KERNEL_VERSION = "mate_guard_v1"


@dataclass(frozen=True)
class CommonHistoryResult:
    trajectory_table: pd.DataFrame
    forcing_table: pd.DataFrame
    observation_features: dict[str, float]
    removals_valid: bool
    early_patterns: dict[str, bool]
    summary: dict[str, float | int | bool | None]


@lru_cache(maxsize=1)
def _model_inputs():
    """Load the repository-bound scenario definitions without mutable globals."""
    return load_model_inputs(_ROOT / "data")


@dataclass(frozen=True)
class _ParameterValues:
    values: dict[str, float]

    def value(self, parameter_id: str) -> float:
        return self.values[parameter_id]


def _parameter_key(params: ResolvedParameters) -> tuple[tuple[str, float], ...]:
    return tuple(sorted((parameter_id, float(value)) for parameter_id, value in params.values.items()))


@lru_cache(maxsize=4096)
def _prepared_source(
    parameter_key: tuple[tuple[str, float], ...], overshoot_removed: bool
) -> tuple[pd.DataFrame, tuple[float, float, float, float]]:
    """Cache source-level forcing and burn-in within each worker process.

    Callers receive copies below; neither cached pandas state nor the cached
    burn-in tuple is exposed for mutation.
    """
    params = _ParameterValues(dict(parameter_key))
    forcing = _common_historical_forcing(params, overshoot_removed=overshoot_removed)  # type: ignore[arg-type]
    burn_in = _burn_in_state(params)  # type: ignore[arg-type]
    state = (burn_in["J_L"], burn_in["A_L"], burn_in["J_R"], burn_in["A_R"])
    return forcing, state


def _restricted_effects(params: ResolvedParameters, restriction: str) -> dict[str, float]:
    if restriction not in RESTRICTIONS:
        raise ValueError(f"Unknown restriction {restriction!r}; expected one of {RESTRICTIONS}")
    effects = {parameter_id: params.value(parameter_id) for parameter_id in ("PR020", "PR021", "PR027", "PR028")}
    if restriction == "R_H":
        effects.update(PR020=0.0, PR021=0.0, PR027=0.0, PR028=0.0)
    elif restriction == "R_T":
        effects.update(PR027=0.0, PR028=0.0)
    elif restriction == "R_C":
        effects.update(PR020=0.0, PR021=0.0)
    return effects


def _common_historical_forcing(params: ResolvedParameters, *, overshoot_removed: bool) -> pd.DataFrame:
    """Build one common forcing path, independent of legacy family statuses."""
    definition = get_scenario_definition(_model_inputs(), "historical_lake")
    records: list[dict[str, float | int | bool | str]] = []
    previous_trout = 0.0
    previous_trout_capacity = 0.0
    previous_climbing_lake = 0.0
    previous_climbing_refuge = 0.0
    activation_year = 1972 + int(params.value("PR024"))
    overshoot_peak = 1.0 if overshoot_removed else params.value("PR018")

    for year in range(definition.start_year, definition.end_year + 1):
        connected = int(year >= 1972)
        if year < 1972:
            upsurge = 0.0
            overshoot = 0.0
            habitat_transition = 0.0
        elif year <= 1977:
            upsurge = params.value("PR029") * (year - 1972) / 5
            overshoot = (year - 1972) / 5
            habitat_transition = min((year - 1972) / max(params.value("PR040"), _EPS), 1.0)
        else:
            upsurge = params.value("PR029") * math.exp(-params.value("PR030") * (year - 1977))
            overshoot = math.exp(-params.value("PR019") * (year - 1977))
            habitat_transition = min((year - 1972) / max(params.value("PR040"), _EPS), 1.0)

        stocking_input = 0.0
        trout_capacity = 0.0
        trout = 0.0
        piscivory = 0.0
        if connected:
            trout_capacity = params.value("PR015") * (1 + params.value("PR016") * upsurge)
            if year == 1972:
                stocking_input = 350000 * params.value("PR013")
                trout = params.value("PR012") + stocking_input
            else:
                trout = max(
                    0.0,
                    previous_trout
                    + params.value("PR014")
                    * previous_trout
                    * (1 - previous_trout / max(previous_trout_capacity, _EPS)),
                )
            piscivory = params.value("PR017") * (1 + max(overshoot_peak - 1, 0) * overshoot)

        climbing_lake = 0.0
        climbing_refuge = 0.0
        if connected:
            if year == 1972:
                climbing_lake = params.value("PR022")
                climbing_refuge = params.value("PR023")
            elif year <= activation_year:
                climbing_lake = previous_climbing_lake
                climbing_refuge = previous_climbing_refuge
            else:
                climbing_lake = float(
                    np.clip(
                        previous_climbing_lake
                        + params.value("PR025") * previous_climbing_lake * (1 - previous_climbing_lake),
                        0.0,
                        1.0,
                    )
                )
                climbing_refuge = float(
                    np.clip(
                        previous_climbing_refuge
                        + params.value("PR026") * previous_climbing_refuge * (1 - previous_climbing_refuge),
                        0.0,
                        1.0,
                    )
                )

        records.append(
            {
                "scenario_id": definition.scenario_id,
                "year": year,
                "connected": connected,
                "U": upsurge,
                "O": overshoot,
                "H": habitat_transition,
                "spawn_habitat_multiplier": float(definition.spawn_habitat_by_year[year]),
                "founder_addition_A_L": 0.0,
                "stocking_input": stocking_input,
                "K_T": trout_capacity,
                "T": trout,
                "P": piscivory,
                "C_L": climbing_lake,
                "C_R": climbing_refuge,
                "trout_active": True,
                "climbing_active": True,
            }
        )
        previous_trout = trout
        previous_trout_capacity = trout_capacity
        previous_climbing_lake = climbing_lake
        previous_climbing_refuge = climbing_refuge
    return pd.DataFrame.from_records(records)


def _burn_in_state(params: ResolvedParameters, burn_in_years: int = 100) -> dict[str, float]:
    k_l_count, k_r_count = _latent_capacities(params)
    state = {"J_L": k_l_count, "A_L": k_l_count, "J_R": k_r_count, "A_R": k_r_count}
    neutral = {"connected": 0, "T": 0.0, "P": 0.0, "C_L": 0.0, "C_R": 0.0, "U": 0.0, "H": 0.0,
               "spawn_habitat_multiplier": 1.0}
    rng = np.random.default_rng(0)
    effects = {"PR020": 0.0, "PR021": 0.0, "PR027": 0.0, "PR028": 0.0}
    for _ in range(burn_in_years):
        state, _ = _advance_common_state(
            state, neutral, neutral, params, effects, iter((rng,) * 18), juvenile_survival=params.value("PR001"),
            stochastic=False, juvenile_climbing_multiplier=1.0,
        )
    return state


def _advance_common_state(
    state: dict[str, float],
    forcing_row: dict[str, Any],
    threat_row: dict[str, Any],
    params: ResolvedParameters,
    effects: dict[str, float],
    draw_streams: Iterator[np.random.Generator],
    *,
    juvenile_survival: float,
    stochastic: bool,
    juvenile_climbing_multiplier: float,
) -> tuple[dict[str, float], dict[str, float | bool]]:
    upsurge = float(forcing_row["U"])
    habitat_transition = float(forcing_row["H"])
    spawn_habitat_multiplier = float(forcing_row.get("spawn_habitat_multiplier", 1.0))
    k_l_count, k_r_count = _latent_capacities(params)
    effective_k_l_count = k_l_count * (1 + params.value("PR031") * upsurge)

    spawn_quality = (1 - params.value("PR005")) * (1 - params.value("PR033") * habitat_transition) + params.value(
        "PR005"
    ) * params.value("PR032")
    pre_breeding_a_l = float(state["A_L"])
    pre_breeding_a_r = float(state["A_R"])
    pre_breeding_total = pre_breeding_a_l + pre_breeding_a_r
    baseline_recruitment_mean = (
        params.value("PR004")
        * pre_breeding_total
        * (1 + params.value("PR031") * upsurge)
        * max(spawn_quality, _EPS)
        * max(spawn_habitat_multiplier, 0.0)
    )
    mate_guard_active = pre_breeding_total < 2.0
    recruitment_mean_total = 0.0 if mate_guard_active else baseline_recruitment_mean
    total_recruits = recruitment_mean_total
    new_j_l = _draw_poisson(next(draw_streams), total_recruits * params.value("PR006"), stochastic)
    new_j_r = _draw_poisson(next(draw_streams), total_recruits * (1 - params.value("PR006")), stochastic)
    surv_j_l = _draw_binomial(next(draw_streams), state["J_L"], juvenile_survival, stochastic)
    surv_j_r = _draw_binomial(next(draw_streams), state["J_R"], juvenile_survival, stochastic)
    surv_a_l = _draw_binomial(next(draw_streams), state["A_L"], params.value("PR002"), stochastic)
    surv_a_r = _draw_binomial(next(draw_streams), state["A_R"], params.value("PR002"), stochastic)
    mat_l = _draw_binomial(next(draw_streams), surv_j_l, params.value("PR003"), stochastic)
    mat_r = _draw_binomial(next(draw_streams), surv_j_r, params.value("PR003"), stochastic)

    pre_j_l = surv_j_l - mat_l + new_j_l
    pre_a_l = surv_a_l + mat_l
    pre_j_r = surv_j_r - mat_r + new_j_r
    pre_a_r = surv_a_r + mat_r
    dd_l = 1 / (1 + params.value("PR010") * (pre_j_l + pre_a_l) / max(effective_k_l_count, _EPS))
    dd_r = 1 / (1 + params.value("PR011") * (pre_j_r + pre_a_r) / max(k_r_count, _EPS))
    dd_j_l = _draw_binomial(next(draw_streams), pre_j_l, dd_l, stochastic)
    dd_a_l = _draw_binomial(next(draw_streams), pre_a_l, dd_l, stochastic)
    dd_j_r = _draw_binomial(next(draw_streams), pre_j_r, dd_r, stochastic)
    dd_a_r = _draw_binomial(next(draw_streams), pre_a_r, dd_r, stochastic)

    diagnostics = _exposure_components(
        forcing_row,
        threat_row,
        params,
        effects,
        juvenile_climbing_multiplier=juvenile_climbing_multiplier,
    )
    diagnostics.update(
        pre_breeding_A_L=pre_breeding_a_l,
        pre_breeding_A_R=pre_breeding_a_r,
        pre_breeding_A_total=pre_breeding_total,
        recruitment_mean_total=recruitment_mean_total,
        realised_recruits_L=float(new_j_l),
        realised_recruits_R=float(new_j_r),
        mate_guard_active=mate_guard_active,
    )
    adult_lake_exposure = diagnostics["adult_lake_exposure"]
    adult_refuge_exposure = diagnostics["adult_refuge_exposure"]
    juvenile_lake_exposure = diagnostics["juvenile_lake_exposure"]
    juvenile_refuge_exposure = diagnostics["juvenile_refuge_exposure"]

    lake_j = _draw_binomial(next(draw_streams), dd_j_l, math.exp(-juvenile_lake_exposure), stochastic)
    lake_a = _draw_binomial(next(draw_streams), dd_a_l, math.exp(-adult_lake_exposure), stochastic)
    refuge_j = _draw_binomial(next(draw_streams), dd_j_r, math.exp(-juvenile_refuge_exposure), stochastic)
    refuge_a = _draw_binomial(next(draw_streams), dd_a_r, math.exp(-adult_refuge_exposure), stochastic)

    # Movement retains the unmultiplied base climbing coefficient.
    move_probability = diagnostics["move_probability"]
    move_j = _draw_binomial(next(draw_streams), lake_j, move_probability, stochastic)
    move_a = _draw_binomial(next(draw_streams), lake_a, move_probability, stochastic)
    return {
        "J_L": max(lake_j - move_j, 0.0),
        "A_L": max(lake_a - move_a, 0.0),
        "J_R": max(refuge_j + move_j, 0.0),
        "A_R": max(refuge_a + move_a, 0.0),
    }, diagnostics


def _exposure_components(
    forcing_row: dict[str, Any],
    threat_row: dict[str, Any],
    params: ResolvedParameters,
    effects: dict[str, float],
    *,
    juvenile_climbing_multiplier: float,
) -> dict[str, float]:
    """Pure annual hazard decomposition under the one-year threat lag."""
    connected = float(threat_row.get("connected", 0.0))
    trout = float(threat_row["T"])
    piscivory = float(threat_row["P"])
    climbing_lake = float(threat_row["C_L"])
    climbing_refuge = float(threat_row["C_R"])
    habitat_lake = params.value("PR033") * float(forcing_row["H"])
    trout_lake = connected * effects["PR020"] * trout * piscivory
    trout_refuge = connected * effects["PR021"] * trout * piscivory * (1 - params.value("PR034"))
    climbing_lake_base = connected * effects["PR027"] * climbing_lake
    climbing_refuge_base = connected * effects["PR028"] * climbing_refuge * (1 - params.value("PR034"))
    climbing_lake_juvenile = juvenile_climbing_multiplier * climbing_lake_base
    climbing_refuge_juvenile = juvenile_climbing_multiplier * climbing_refuge_base
    adult_lake_exposure = habitat_lake + trout_lake + climbing_lake_base
    adult_refuge_exposure = trout_refuge + climbing_refuge_base
    juvenile_lake_exposure = habitat_lake + trout_lake + climbing_lake_juvenile
    juvenile_refuge_exposure = trout_refuge + climbing_refuge_juvenile
    movement_lake_exposure = adult_lake_exposure
    return {
        "habitat_lake_juvenile_hazard": habitat_lake,
        "habitat_lake_adult_hazard": habitat_lake,
        "habitat_refuge_juvenile_hazard": 0.0,
        "habitat_refuge_adult_hazard": 0.0,
        "trout_lake_juvenile_hazard": trout_lake,
        "trout_lake_adult_hazard": trout_lake,
        "trout_refuge_juvenile_hazard": trout_refuge,
        "trout_refuge_adult_hazard": trout_refuge,
        "climbing_lake_juvenile_hazard": climbing_lake_juvenile,
        "climbing_lake_adult_hazard": climbing_lake_base,
        "climbing_refuge_juvenile_hazard": climbing_refuge_juvenile,
        "climbing_refuge_adult_hazard": climbing_refuge_base,
        "juvenile_lake_exposure": juvenile_lake_exposure,
        "adult_lake_exposure": adult_lake_exposure,
        "juvenile_refuge_exposure": juvenile_refuge_exposure,
        "adult_refuge_exposure": adult_refuge_exposure,
        "movement_lake_exposure": movement_lake_exposure,
        "move_probability": min(params.value("PR007") * (1 - math.exp(-movement_lake_exposure)), 1.0),
    }


def source_exposure_table(
    params: ResolvedParameters,
    restriction: str,
    configuration: str,
) -> pd.DataFrame:
    """Return factual state-independent annual hazards for one proposal.

    Isolated mortality columns are ``1-exp(-hazard)`` and therefore support
    the protocol's below-five-percent peak descriptor without simulation.
    """
    if configuration not in CONFIGURATIONS:
        raise ValueError(f"Unknown configuration {configuration!r}; expected one of {CONFIGURATIONS}")
    effects = _restricted_effects(params, restriction)
    cached_forcing, _ = _prepared_source(_parameter_key(params), False)
    multiplier = 2.0 if configuration == "juvenile_climbing" else 1.0
    threat_row: dict[str, Any] = {"connected": 0, "T": 0.0, "P": 0.0, "C_L": 0.0, "C_R": 0.0}
    records: list[dict[str, Any]] = []
    for forcing_row in cached_forcing.to_dict(orient="records"):
        hazards = _exposure_components(
            forcing_row,
            threat_row,
            params,
            effects,
            juvenile_climbing_multiplier=multiplier,
        )
        record: dict[str, Any] = {
            "year": int(forcing_row["year"]),
            "restriction": restriction,
            "configuration": configuration,
            **hazards,
        }
        for name, hazard in hazards.items():
            if name.endswith("_hazard"):
                record[name.removesuffix("_hazard") + "_mortality"] = 1 - math.exp(-hazard)
        records.append(record)
        threat_row = forcing_row
    return pd.DataFrame.from_records(records)


def _remove_refuge(state: dict[str, float], count: float, *, adult_first: bool) -> tuple[dict[str, float], bool]:
    result = dict(state)
    if result["J_R"] + result["A_R"] < count:
        return result, False
    remaining = count
    order = ("A_R", "J_R") if adult_first else ("J_R", "A_R")
    for stage in order:
        removed = min(result[stage], remaining)
        result[stage] -= removed
        remaining -= removed
    return result, remaining <= _EPS


def _annual_juvenile_survival(
    params: ResolvedParameters,
    configuration: str,
    environment_rng: np.random.Generator,
) -> float:
    if configuration not in _ENVIRONMENT_RHO:
        return params.value("PR001")
    mean = params.value("PR001")
    if not 0 < mean < 1:
        raise ValueError("Environmental-survival configurations require PR001 strictly between zero and one")
    rho = _ENVIRONMENT_RHO[configuration]
    kappa = 1 / rho - 1
    return float(environment_rng.beta(mean * kappa, (1 - mean) * kappa))


def _source_ct004_pass(forcing: pd.DataFrame) -> bool:
    row_1972 = forcing.loc[forcing["year"] == 1972].iloc[0]
    window = forcing.loc[forcing["year"].between(1973, 1978)]
    return bool(
        row_1972["stocking_input"] > 0
        and window["T"].max() > row_1972["T"]
        and window["P"].max() > row_1972["P"]
    )


def _early_patterns(trajectory: pd.DataFrame, forcing: pd.DataFrame) -> dict[str, bool]:
    pre = trajectory.loc[trajectory["year"].between(1965, 1971)]
    boom = trajectory.loc[trajectory["year"].between(1975, 1980)]
    late = trajectory.loc[trajectory["year"].between(1988, 1991)]
    peak_index = boom["pedder_lake_index"].idxmax()
    peak_year = int(trajectory.loc[peak_index, "year"])
    n_l_1980 = float(trajectory.loc[trajectory["year"] == 1980, "N_L"].iloc[0])
    n_l_1983 = float(trajectory.loc[trajectory["year"] == 1983, "N_L"].iloc[0])
    c_l_1980 = float(forcing.loc[forcing["year"] == 1980, "C_L"].iloc[0])
    c_l_1983 = float(forcing.loc[forcing["year"] == 1983, "C_L"].iloc[0])
    components = {
        "pre_flood_both_compartments": bool((pre["N_L"] > 0).all() and (pre["N_R"] > 0).all()),
        "boom_above_pre_mean": bool(float(boom["pedder_lake_index"].max()) > float(pre["pedder_lake_index"].mean())),
        "boom_above_late_mean": bool(float(boom["pedder_lake_index"].max()) > float(late["pedder_lake_index"].mean())),
        "boom_peak_year_1976_1978": 1976 <= peak_year <= 1978,
        "ct005_directional_contrast": bool(
            n_l_1980 > 0 and c_l_1983 > 0 and c_l_1983 * n_l_1980 > c_l_1980 * n_l_1983
        ),
        "ct004_forcing": _source_ct004_pass(forcing),
    }
    components["historical_patterns"] = all(
        components[key]
        for key in (
            "pre_flood_both_compartments",
            "boom_above_pre_mean",
            "boom_above_late_mean",
            "boom_peak_year_1976_1978",
            "ct005_directional_contrast",
        )
    )
    components["early_patterns_pass"] = components["historical_patterns"] and components["ct004_forcing"]
    return components


def run_common_history(
    params: ResolvedParameters,
    restriction: str,
    configuration: str,
    seed: int,
    environment_seed: int,
    *,
    overshoot_removed: bool = False,
) -> CommonHistoryResult:
    """Run one 1965--2002 history under the signed common-model protocol."""
    if configuration not in CONFIGURATIONS:
        raise ValueError(f"Unknown configuration {configuration!r}; expected one of {CONFIGURATIONS}")
    effects = _restricted_effects(params, restriction)
    cached_forcing, cached_state = _prepared_source(_parameter_key(params), overshoot_removed)
    forcing = cached_forcing.copy(deep=True)
    environment_rng = np.random.default_rng(environment_seed)
    state = dict(zip(("J_L", "A_L", "J_R", "A_R"), cached_state, strict=True))
    threat_row: dict[str, Any] = {"connected": 0, "T": 0.0, "P": 0.0, "C_L": 0.0, "C_R": 0.0}
    records: list[dict[str, Any]] = []
    observations: dict[str, float] = {}
    removals_valid = True
    juvenile_multiplier = 2.0 if configuration == "juvenile_climbing" else 1.0

    forcing_records = forcing.to_dict(orient="records")
    for forcing_row in forcing_records:
        year = int(forcing_row["year"])
        early_n_l = state["J_L"] + state["A_L"]
        early_n_r = state["J_R"] + state["A_R"]
        early_n_total = early_n_l + early_n_r
        if 1988 <= year <= 1992:
            observations[f"pos_N_R_{year}"] = early_n_r
        if year in (1988, 1989):
            observations[f"neg_N_L_{year}"] = early_n_l
        if 1998 <= year <= 2002:
            observations[f"neg_N_total_{year}"] = early_n_total

        if year == 1992 and configuration in _REMOVAL_CONFIGURATIONS:
            if state["A_R"] < 1:
                removals_valid = False
            else:
                state = dict(state)
                state["A_R"] -= 1

        if year == 1996:
            observations["pos_N_R_1996_january"] = early_n_r
            if configuration in _REMOVAL_CONFIGURATIONS:
                state, valid = _remove_refuge(
                    state,
                    4,
                    adult_first=configuration == "minimum_dated_adult_first",
                )
                removals_valid = removals_valid and valid
            observations["pos_N_R_1996_march"] = state["J_R"] + state["A_R"]

        annual_survival = _annual_juvenile_survival(params, configuration, environment_rng)
        # One event-keyed stream per stochastic draw preserves pairing across
        # restrictions and counterfactuals even when NumPy's distribution
        # algorithms consume different amounts of random state.
        draw_streams = iter(np.random.default_rng(child) for child in np.random.SeedSequence([seed, year]).spawn(18))
        state, exposure = _advance_common_state(
            state,
            forcing_row,
            threat_row,
            params,
            effects,
            draw_streams,
            juvenile_survival=annual_survival,
            stochastic=True,
            juvenile_climbing_multiplier=juvenile_multiplier,
        )
        record = _build_record(year, params.family_id, seed, state, forcing_row, params)
        record.update(
            restriction=restriction,
            configuration=configuration,
            environment_seed=environment_seed,
            juvenile_survival=annual_survival,
            **exposure,
        )
        records.append(record)
        threat_row = forcing_row

    if tuple(observations) != COMMON_EPISODE_FIELDS:
        # Stable ordering is part of the observation-likelihood contract.
        observations = {field: observations[field] for field in COMMON_EPISODE_FIELDS}
    trajectory = pd.DataFrame.from_records(records)
    forcing = forcing.copy()
    forcing["juvenile_survival"] = trajectory["juvenile_survival"].to_numpy()
    early = _early_patterns(trajectory, forcing)
    k_l_count, k_r_count = _latent_capacities(params)
    absent = trajectory.loc[trajectory["N_total"] <= 0, "year"]
    terminal_survival = bool(trajectory.loc[trajectory["year"] == 2002, "N_total"].iloc[0] > 0)
    pre_flood_mean = float(trajectory.loc[trajectory["year"].between(1965, 1971), "N_total"].mean())
    post_flood_minimum = float(trajectory.loc[trajectory["year"].between(1972, 2002), "N_total"].min())
    n_l_1980 = float(trajectory.loc[trajectory["year"] == 1980, "N_L"].iloc[0])
    n_l_1983 = float(trajectory.loc[trajectory["year"] == 1983, "N_L"].iloc[0])
    c_l_1980 = float(forcing.loc[forcing["year"] == 1980, "C_L"].iloc[0])
    c_l_1983 = float(forcing.loc[forcing["year"] == 1983, "C_L"].iloc[0])
    terminal = trajectory.loc[trajectory["year"] == 2002].iloc[0]
    summary: dict[str, float | int | bool | None] = {
        "terminal_survival": terminal_survival,
        "survived_2002": terminal_survival,
        "N_total_2002": float(trajectory.loc[trajectory["year"] == 2002, "N_total"].iloc[0]),
        "minimum_N_total_1965_2002": float(trajectory["N_total"].min()),
        "first_year_total_absent": int(absent.iloc[0]) if not absent.empty else None,
        "extinction_time_censored": int(absent.iloc[0]) if not absent.empty else 2003,
        "preflood_mean_N_total_1965_1971": pre_flood_mean,
        "minimum_N_total_1972_2002": post_flood_minimum,
        "min_total_over_preflood_mean": post_flood_minimum / max(pre_flood_mean, _EPS),
        "ct005_N_L_1980": n_l_1980,
        "ct005_N_L_1983": n_l_1983,
        "ct005_C_L_1980": c_l_1980,
        "ct005_C_L_1983": c_l_1983,
        "ct005_cross_product_contrast": c_l_1983 * n_l_1980 - c_l_1980 * n_l_1983,
        "K_L": k_l_count,
        "K_R": k_r_count,
        "PR011": params.value("PR011"),
        "K_R_over_PR011": k_r_count / max(params.value("PR011"), _EPS),
        "PR033": params.value("PR033"),
        "low_refuge_capacity": bool(k_r_count < 20),
        "removals_valid": removals_valid,
        "terminal_N_L_2002": float(terminal["N_L"]),
        "terminal_N_R_2002": float(terminal["N_R"]),
        "terminal_lake_present_2002": bool(terminal["lake_present"]),
        "terminal_refuge_present_2002": bool(terminal["refuge_present"]),
        "mate_guard_active_years": int(trajectory["mate_guard_active"].sum()),
    }
    return CommonHistoryResult(trajectory, forcing, observations, removals_valid, early, summary)


def _run_intrinsic_scenario(params: ResolvedParameters, scenario_id: str) -> pd.DataFrame:
    definition = get_scenario_definition(_model_inputs(), scenario_id)
    years = list(range(definition.start_year, definition.end_year + 1))
    forcing = build_scenario_forcing(definition, years, params).table
    state = {"J_L": 0.0, "A_L": 0.0, "J_R": 0.0, "A_R": 0.0}
    effects = {"PR020": 0.0, "PR021": 0.0, "PR027": 0.0, "PR028": 0.0}
    neutral_threat = {"connected": 0, "T": 0.0, "P": 0.0, "C_L": 0.0, "C_R": 0.0}
    rng = np.random.default_rng(0)
    records: list[dict[str, Any]] = []
    for forcing_row in forcing.to_dict(orient="records"):
        state["A_L"] += float(forcing_row["founder_addition_A_L"])
        state, _ = _advance_common_state(
            state,
            forcing_row,
            neutral_threat,
            params,
            effects,
            iter((rng,) * 18),
            juvenile_survival=params.value("PR001"),
            stochastic=False,
            juvenile_climbing_multiplier=1.0,
        )
        records.append(_build_record(int(forcing_row["year"]), params.family_id, 0, state, forcing_row, params))
    return pd.DataFrame.from_records(records)


def intrinsic_viability(params: ResolvedParameters) -> dict[str, Any]:
    """Evaluate the signed deterministic insurance-scenario viability screen."""
    oberon = _run_intrinsic_scenario(params, "lake_oberon")
    strathgordon = _run_intrinsic_scenario(params, "strathgordon")
    oberon_juveniles = oberon["J_L"] + oberon["J_R"]
    juvenile_years = oberon.loc[oberon_juveniles > 0, "year"]
    first_juvenile = int(juvenile_years.iloc[0]) if not juvenile_years.empty else None
    oberon_persistence = bool((oberon["N_total"] > 0).all())
    oberon_total_2012 = float(oberon.loc[oberon["year"] == 2012, "N_total"].iloc[0])
    oberon_growth = oberon_total_2012 > 34
    oberon_juveniles_by_1997 = first_juvenile is not None and first_juvenile <= 1997

    strath_juveniles = strathgordon["J_L"] + strathgordon["J_R"]
    no_early_recruitment = bool((strath_juveniles.loc[strathgordon["year"].between(2001, 2007)] == 0).all())
    juveniles_2008 = float(strath_juveniles.loc[strathgordon["year"] == 2008].iloc[0])
    recruitment_2008 = juveniles_2008 > 0
    strath_total_2012 = float(strathgordon.loc[strathgordon["year"] == 2012, "N_total"].iloc[0])
    strath_positive_2012 = strath_total_2012 > 0
    k_l_count, k_r_count = _latent_capacities(params)
    viable = all(
        (
            oberon_persistence,
            oberon_growth,
            oberon_juveniles_by_1997,
            no_early_recruitment,
            recruitment_2008,
            strath_positive_2012,
        )
    )
    return {
        "viable": viable,
        "oberon_persisted_annually": oberon_persistence,
        "oberon_total_2012": oberon_total_2012,
        "oberon_founders_total": 34.0,
        "oberon_net_growth": oberon_growth,
        "oberon_first_juvenile_year": first_juvenile,
        "oberon_juveniles_by_1997": oberon_juveniles_by_1997,
        "strathgordon_no_juveniles_2001_2007": no_early_recruitment,
        "strathgordon_juveniles_2008": juveniles_2008,
        "strathgordon_recruitment_2008": recruitment_2008,
        "strathgordon_total_2012": strath_total_2012,
        "strathgordon_positive_2012": strath_positive_2012,
        "K_L": k_l_count,
        "K_R": k_r_count,
        "PR011": params.value("PR011"),
        "K_R_over_PR011": k_r_count / max(params.value("PR011"), _EPS),
        "PR033": params.value("PR033"),
        "low_refuge_capacity": bool(k_r_count < 20),
        "oberon_annual_total": {
            int(row.year): float(row.N_total) for row in oberon[["year", "N_total"]].itertuples(index=False)
        },
        "strathgordon_annual_juveniles": {
            int(year): float(value) for year, value in zip(strathgordon["year"], strath_juveniles, strict=True)
        },
    }
