from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from galaxias_model.types import ForcingSchedule, ResolvedParameters, SimulationConfig, SimulationResult


EPS = 1e-9


def _latent_capacities(params: ResolvedParameters) -> tuple[float, float]:
    return (
        max(params.value("PR008") * params.value("PR039"), 1.0),
        max(params.value("PR009") * params.value("PR039"), 1.0),
    )


def build_historical_forcing(years: list[int] | np.ndarray, params: ResolvedParameters) -> ForcingSchedule:
    year_values = [int(year) for year in years]

    records: list[dict[str, float | int | bool]] = []
    prev_t = 0.0
    prev_k_t = 0.0
    prev_c_l = 0.0
    prev_c_r = 0.0
    activation_year = 1972 + int(params.value("PR024"))
    trout_active = params.trout_active
    climbing_active = params.climbing_active

    for year in year_values:
        connected = 1 if year >= 1972 else 0
        if year < 1972:
            upsurge = 0.0
            overshoot = 0.0
            habitat_transition = 0.0
        elif year <= 1977:
            upsurge = params.value("PR029") * ((year - 1972) / 5)
            overshoot = (year - 1972) / 5
            habitat_transition = min((year - 1972) / max(params.value("PR040"), EPS), 1.0)
        else:
            upsurge = params.value("PR029") * math.exp(-params.value("PR030") * (year - 1977))
            overshoot = math.exp(-params.value("PR019") * (year - 1977))
            habitat_transition = min((year - 1972) / max(params.value("PR040"), EPS), 1.0)

        stocking_input = 0.0
        trout_capacity = 0.0
        trout = 0.0
        piscivory = 0.0
        if trout_active and year >= 1972:
            trout_capacity = params.value("PR015") * (1 + params.value("PR016") * upsurge)
            if year == 1972:
                stocking_input = 350000 * params.value("PR013")
                trout = params.value("PR012") + stocking_input
            else:
                trout = max(
                    0.0,
                    prev_t + params.value("PR014") * prev_t * (1 - prev_t / max(prev_k_t, EPS)),
                )
            piscivory = params.value("PR017") * (1 + max(params.value("PR018") - 1, 0) * overshoot)

        climbing_lake = 0.0
        climbing_refuge = 0.0
        if climbing_active and year >= 1972:
            if year == 1972:
                climbing_lake = params.value("PR022")
                climbing_refuge = params.value("PR023")
            elif year <= activation_year:
                climbing_lake = prev_c_l
                climbing_refuge = prev_c_r
            else:
                climbing_lake = np.clip(
                    prev_c_l + params.value("PR025") * prev_c_l * (1 - prev_c_l),
                    0.0,
                    1.0,
                ).item()
                climbing_refuge = np.clip(
                    prev_c_r + params.value("PR026") * prev_c_r * (1 - prev_c_r),
                    0.0,
                    1.0,
                ).item()

        records.append(
            {
                "year": year,
                "connected": connected,
                "U": upsurge,
                "O": overshoot,
                "H": habitat_transition,
                "stocking_input": stocking_input,
                "K_T": trout_capacity,
                "T": trout,
                "P": piscivory,
                "C_L": climbing_lake,
                "C_R": climbing_refuge,
                "trout_active": trout_active,
                "climbing_active": climbing_active,
            }
        )

        prev_t = trout
        prev_k_t = trout_capacity
        prev_c_l = climbing_lake
        prev_c_r = climbing_refuge

    forcing_table = pd.DataFrame.from_records(records)
    return ForcingSchedule(years=year_values, table=forcing_table)


def _draw_poisson(rng: np.random.Generator, lam: float, stochastic: bool) -> float:
    lam = max(lam, 0.0)
    if stochastic:
        return float(rng.poisson(lam))
    return lam


def _draw_binomial(rng: np.random.Generator, n: float, p: float, stochastic: bool) -> float:
    n = max(n, 0.0)
    p = float(np.clip(p, 0.0, 1.0))
    if stochastic:
        return float(rng.binomial(int(round(n)), p))
    return n * p


def _advance_pedder_state(
    state: dict[str, float],
    forcing_row: dict[str, Any],
    threat_row: dict[str, Any],
    params: ResolvedParameters,
    rng: np.random.Generator,
    stochastic: bool,
) -> dict[str, float]:
    upsurge = float(forcing_row["U"])
    habitat_transition = float(forcing_row["H"])
    trout = float(threat_row["T"])
    piscivory = float(threat_row["P"])
    climbing_lake = float(threat_row["C_L"])
    climbing_refuge = float(threat_row["C_R"])
    k_l_count, k_r_count = _latent_capacities(params)
    effective_k_l_count = k_l_count * (1 + params.value("PR031") * upsurge)

    spawn_quality = (1 - params.value("PR005")) * (1 - params.value("PR033") * habitat_transition) + params.value(
        "PR005"
    ) * params.value("PR032")
    total_recruits = (
        params.value("PR004")
        * (state["A_L"] + state["A_R"])
        * (1 + params.value("PR031") * upsurge)
        * max(spawn_quality, EPS)
    )

    new_j_l = _draw_poisson(rng, total_recruits * params.value("PR006"), stochastic)
    new_j_r = _draw_poisson(rng, total_recruits * (1 - params.value("PR006")), stochastic)

    surv_j_l = _draw_binomial(rng, state["J_L"], params.value("PR001"), stochastic)
    surv_j_r = _draw_binomial(rng, state["J_R"], params.value("PR001"), stochastic)
    surv_a_l = _draw_binomial(rng, state["A_L"], params.value("PR002"), stochastic)
    surv_a_r = _draw_binomial(rng, state["A_R"], params.value("PR002"), stochastic)

    mat_l = _draw_binomial(rng, surv_j_l, params.value("PR003"), stochastic)
    mat_r = _draw_binomial(rng, surv_j_r, params.value("PR003"), stochastic)

    pre_j_l = (surv_j_l - mat_l) + new_j_l
    pre_a_l = surv_a_l + mat_l
    pre_j_r = (surv_j_r - mat_r) + new_j_r
    pre_a_r = surv_a_r + mat_r

    dd_l = 1 / (1 + params.value("PR010") * (pre_j_l + pre_a_l) / max(effective_k_l_count, EPS))
    dd_r = 1 / (1 + params.value("PR011") * (pre_j_r + pre_a_r) / max(k_r_count, EPS))

    dd_j_l = _draw_binomial(rng, pre_j_l, dd_l, stochastic)
    dd_a_l = _draw_binomial(rng, pre_a_l, dd_l, stochastic)
    dd_j_r = _draw_binomial(rng, pre_j_r, dd_r, stochastic)
    dd_a_r = _draw_binomial(rng, pre_a_r, dd_r, stochastic)

    lake_biotic_pressure = habitat_transition * (
        params.value("PR020") * trout * piscivory + params.value("PR027") * climbing_lake
    )
    refuge_biotic_pressure = habitat_transition * (
        params.value("PR021") * trout * piscivory * (1 - params.value("PR034"))
        + params.value("PR028") * climbing_refuge * (1 - params.value("PR034"))
    )
    lake_exposure = (
        params.value("PR033") * habitat_transition
        + lake_biotic_pressure
    )
    refuge_exposure = refuge_biotic_pressure

    m_l = math.exp(-lake_exposure)
    m_r = math.exp(-refuge_exposure)

    lake_j = _draw_binomial(rng, dd_j_l, m_l, stochastic)
    lake_a = _draw_binomial(rng, dd_a_l, m_l, stochastic)
    refuge_j = _draw_binomial(rng, dd_j_r, m_r, stochastic)
    refuge_a = _draw_binomial(rng, dd_a_r, m_r, stochastic)

    pressure_l = 1 - math.exp(-lake_exposure)
    move_prob = min(params.value("PR007") * pressure_l, 1.0)

    move_j = _draw_binomial(rng, lake_j, move_prob, stochastic)
    move_a = _draw_binomial(rng, lake_a, move_prob, stochastic)

    return {
        "J_L": max(lake_j - move_j, 0.0),
        "A_L": max(lake_a - move_a, 0.0),
        "J_R": max(refuge_j + move_j, 0.0),
        "A_R": max(refuge_a + move_a, 0.0),
    }


def _burn_in_state(params: ResolvedParameters, burn_in_years: int) -> dict[str, float]:
    rng = np.random.default_rng(0)
    k_l_count, k_r_count = _latent_capacities(params)
    state = {
        "J_L": k_l_count,
        "A_L": k_l_count,
        "J_R": k_r_count,
        "A_R": k_r_count,
    }
    forcing_row = {
        "connected": 0,
        "T": 0.0,
        "P": 0.0,
        "C_L": 0.0,
        "C_R": 0.0,
        "U": 0.0,
        "H": 0.0,
    }
    for _ in range(burn_in_years):
        state = _advance_pedder_state(state, forcing_row, forcing_row, params, rng, stochastic=False)
    return state


def _build_record(
    year: int,
    family_id: str,
    seed: int,
    state: dict[str, float],
    forcing_row: dict[str, Any],
    params: ResolvedParameters,
) -> dict[str, float | int]:
    k_l_count, k_r_count = _latent_capacities(params)
    n_l = state["J_L"] + state["A_L"]
    n_r = state["J_R"] + state["A_R"]
    n_total = n_l + n_r
    pedder_lake_index = n_l / (n_l + k_l_count)
    pedder_refuge_index = n_r / (n_r + k_r_count)
    lake_present = int(n_l > 0)
    refuge_present = int(n_r > 0)
    total_present = int(n_total > 0)
    return {
        "year": year,
        "family_id": family_id,
        "seed": seed,
        "J_L": state["J_L"],
        "A_L": state["A_L"],
        "J_R": state["J_R"],
        "A_R": state["A_R"],
        "T": forcing_row["T"],
        "P": forcing_row["P"],
        "C_L": forcing_row["C_L"],
        "C_R": forcing_row["C_R"],
        "U": forcing_row["U"],
        "K_L_count": k_l_count,
        "K_R_count": k_r_count,
        "N_L": n_l,
        "N_R": n_r,
        "N_total": n_total,
        "pedder_lake_index": pedder_lake_index,
        "pedder_refuge_index": pedder_refuge_index,
        "climbing_to_pedder_lake_ratio": forcing_row["C_L"] / max(pedder_lake_index, EPS),
        "lake_present": lake_present,
        "refuge_present": refuge_present,
        "total_present": total_present,
    }


def run_historical_simulation(
    params: ResolvedParameters,
    family_id: str,
    config: SimulationConfig,
    seed: int,
) -> SimulationResult:
    if family_id != params.family_id:
        raise ValueError(f"family_id {family_id} does not match resolved parameter family {params.family_id}")
    if config.scenario_id != "historical_lake":
        raise ValueError("Module 1 only supports scenario_id='historical_lake'")

    years = np.arange(config.start_year, config.end_year + 1, dtype=int)
    forcing = build_historical_forcing(years, params)
    rng = np.random.default_rng(seed)
    state = _burn_in_state(params, config.burn_in_years)
    threat_row = {
        "T": 0.0,
        "P": 0.0,
        "C_L": 0.0,
        "C_R": 0.0,
    }

    records: list[dict[str, float | int]] = []
    for forcing_row in forcing.table.to_dict(orient="records"):
        year = int(forcing_row["year"])
        state = _advance_pedder_state(state, forcing_row, threat_row, params, rng, stochastic=config.stochastic)
        records.append(_build_record(year, family_id, seed, state, forcing_row, params))
        threat_row = forcing_row

    trajectory = pd.DataFrame.from_records(records)
    result = SimulationResult(
        trajectory_table=trajectory,
        resolved_parameters=params,
        forcing_table=forcing.table.copy(),
    )
    result.summary = summarize_latent_run(result)
    return result


def summarize_latent_run(simulation_result: SimulationResult) -> dict[str, Any]:
    trajectory = simulation_result.trajectory_table

    def first_year(mask: pd.Series) -> int | None:
        matches = trajectory.loc[mask, "year"]
        return int(matches.iloc[0]) if not matches.empty else None

    def last_year(mask: pd.Series) -> int | None:
        matches = trajectory.loc[mask, "year"]
        return int(matches.iloc[-1]) if not matches.empty else None

    peak_value = float(trajectory["pedder_lake_index"].max())
    peak_threshold = peak_value * 0.985 if peak_value > 0 else 0.0
    peak_lake_row = trajectory.loc[trajectory["pedder_lake_index"] >= peak_threshold].iloc[-1]
    peak_total_row = trajectory.loc[trajectory["N_total"].idxmax()]
    peak_trout_row = trajectory.loc[trajectory["T"].idxmax()]
    peak_upsurge_row = trajectory.loc[trajectory["U"].idxmax()]
    value_1965 = float(trajectory.loc[trajectory["year"] == 1965, "pedder_lake_index"].iloc[0])
    # Treat the inferred 1977 signal as a short boom window rather than a literal single-year census peak.
    boom_window = trajectory.loc[trajectory["year"].between(1975, 1977), "pedder_lake_index"]
    final_total = float(trajectory.loc[trajectory["year"] == trajectory["year"].max(), "N_total"].iloc[0])
    pre1972 = trajectory.loc[trajectory["year"] < 1972, "N_total"]

    return {
        "family_id": simulation_result.resolved_parameters.family_id,
        "family_label": simulation_result.resolved_parameters.family_label,
        "seed": int(trajectory["seed"].iloc[0]),
        "peak_year_pedder_lake_index": int(peak_lake_row["year"]),
        "peak_value_pedder_lake_index": float(peak_lake_row["pedder_lake_index"]),
        "first_year_climbing_ratio_gt_one": first_year(trajectory["climbing_to_pedder_lake_ratio"] > 1),
        "first_year_lake_absent": first_year(trajectory["lake_present"] == 0),
        "last_year_total_present": last_year(trajectory["total_present"] == 1),
        "first_year_total_absent": first_year(trajectory["total_present"] == 0),
        "peak_trout_year": int(peak_trout_row["year"]),
        "peak_upsurge_year": int(peak_upsurge_row["year"]),
        "pre1972_min_total": float(pre1972.min()) if not pre1972.empty else None,
        "boom_ratio_1977_vs_1965": float(boom_window.max()) / max(value_1965, EPS),
        "final_to_peak_ratio": final_total / max(float(peak_total_row["N_total"]), EPS),
    }
