"""Linked historical age-structured runner.

This module joins the already-qualified age kernel across Pedder, Oberon and
Strathgordon.  It deliberately keeps the source reconstruction and calendar
assumptions explicit: a failed dated removal returns a failed history with its
reason, and no operation is replaced by a capped or fabricated count.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
import hashlib
import json
import math
from typing import Any

import numpy as np

from galaxias_model.age_demography import (
    AgeConditions,
    AgeDemography,
    CountEvent,
    RecruitmentLimits,
    advance,
    neutral_equilibrium_from_abundance,
)
from galaxias_model.age_scenarios import conditions_from_forcing, strathgordon_spawn_multiplier


SITES = ("pedder", "oberon", "strathgordon")
RESTRICTIONS = ("R_H", "R_T", "R_C", "R_J")
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class _Parameters:
    """Small .value adapter for mappings and existing ResolvedParameters."""
    def __init__(self, values: Any) -> None:
        self._values = values

    def value(self, key: str) -> float:
        if hasattr(self._values, "value"):
            return float(self._values.value(key))
        if isinstance(self._values, Mapping) and key in self._values:
            return float(self._values[key])
        raise KeyError(f"missing retained parameter {key}")

    @property
    def trout_active(self) -> bool:
        return True

    @property
    def climbing_active(self) -> bool:
        return True


@dataclass(frozen=True)
class _Date:
    year: int
    time: float
    label: str


def _time(month: int, day: int | None = None) -> float:
    if not 1 <= month <= 12:
        raise ValueError("month must be in 1..12")
    doy = sum(_DAYS[: month - 1])
    if day is None:
        day = _DAYS[month - 1] // 2
    if not 1 <= day <= _DAYS[month - 1]:
        raise ValueError("day is outside month")
    return (doy + day - 1) / 365.0


def _month_dates(start_year: int, start_month: int, end_year: int, end_month: int, prefix: str) -> list[_Date]:
    result: list[_Date] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        result.append(_Date(year, _time(month), f"{prefix}_{year:04d}_{month:02d}"))
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return result


def _forcing_rows(params: _Parameters, start_year: int, end_year: int, *, overshoot_removed: bool) -> dict[int, dict[str, float | int]]:
    """Reproduce common historical equations through 2012, including lag inputs."""
    previous_trout = previous_capacity = previous_climbing_lake = previous_climbing_refuge = 0.0
    activation_year = 1972 + int(params.value("PR024"))
    overshoot_peak = 1.0 if overshoot_removed else params.value("PR018")
    rows: dict[int, dict[str, float | int]] = {}
    for year in range(start_year, end_year + 1):
        connected = int(year >= 1972)
        if year < 1972:
            upsurge = overshoot = habitat = 0.0
        elif year <= 1977:
            upsurge = params.value("PR029") * (year - 1972) / 5
            overshoot = (year - 1972) / 5
            habitat = min((year - 1972) / max(params.value("PR040"), 1e-12), 1.0)
        else:
            upsurge = params.value("PR029") * math.exp(-params.value("PR030") * (year - 1977))
            overshoot = math.exp(-params.value("PR019") * (year - 1977))
            habitat = min((year - 1972) / max(params.value("PR040"), 1e-12), 1.0)
        trout_capacity = trout = piscivory = 0.0
        if connected and params.trout_active:
            trout_capacity = params.value("PR015") * (1 + params.value("PR016") * upsurge)
            if year == 1972:
                trout = params.value("PR012") + 350000 * params.value("PR013")
            else:
                trout = max(0.0, previous_trout + params.value("PR014") * previous_trout
                            * (1 - previous_trout / max(previous_capacity, 1e-12)))
            piscivory = params.value("PR017") * (1 + max(overshoot_peak - 1, 0) * overshoot)
        climbing_lake = climbing_refuge = 0.0
        if connected and params.climbing_active:
            if year == 1972:
                climbing_lake, climbing_refuge = params.value("PR022"), params.value("PR023")
            elif year <= activation_year:
                climbing_lake, climbing_refuge = previous_climbing_lake, previous_climbing_refuge
            else:
                climbing_lake = float(np.clip(previous_climbing_lake + params.value("PR025") * previous_climbing_lake * (1 - previous_climbing_lake), 0, 1))
                climbing_refuge = float(np.clip(previous_climbing_refuge + params.value("PR026") * previous_climbing_refuge * (1 - previous_climbing_refuge), 0, 1))
        rows[year] = {
            "year": year, "connected": connected, "U": upsurge, "O": overshoot,
            "H": habitat, "spawn_habitat_multiplier": 1.0, "T": trout, "P": piscivory,
            "C_L": climbing_lake, "C_R": climbing_refuge,
        }
        previous_trout, previous_capacity = trout, trout_capacity
        previous_climbing_lake, previous_climbing_refuge = climbing_lake, climbing_refuge
    return rows


def _calendar(start_year: int, end_year: int) -> list[_Date]:
    dates = []
    dates += _month_dates(1990, 2, 1991, 9, "early_refuge")
    dates += [_Date(1992, _time(2, 4), "february_1992_capture")]
    dates += [_Date(1996, _time(1, 1), "january_1996_pre_removal_early"),
              _Date(1996, _time(1, 31), "january_1996_pre_removal_late"),
              _Date(1996, _time(3, 6), "march_1996_record")]
    dates += _month_dates(1998, 1, 2002, 12, "late_refuge")
    dates += [_Date(y, _time(6), f"oberon_survey_{y}") for y in (1993, 1994, 1995)]
    dates += [_Date(1996, _time(2), "oberon_february_1996_adult"), _Date(1997, _time(3, 15), "oberon_march_1997_adult_juvenile"), _Date(1999, _time(6), "oberon_1999_positive"), _Date(2012, _time(3, 6), "oberon_march_2012_adult_juvenile")]
    dates += [_Date(y, _time(6), f"strath_survey_{y}") for y in range(2001, 2006)]
    dates += [_Date(2008, _time(4, 15), "strath_april_2008_juvenile"), _Date(2012, _time(6, 15), "strath_june_2012_diagnostic")]
    # Both endpoint calendars remain in the union; only the selected ledger
    # operation replaces its no-op in a particular history.
    dates += [_Date(1991, _time(11, 1), "november_1991_release"),
              _Date(1992, _time(2, 5), "february_1992_release"),
              _Date(1997, _time(5, 1), "may_1997_release_early"),
              _Date(1997, _time(5, 31), "may_1997_release_late")]
    dates += [_Date(y, 0.25, f"transfer_{y}_early") for y in (2001, 2002, 2005, 2006, 2007)]
    dates += [_Date(y, 0.75, f"transfer_{y}_late") for y in (2001, 2002, 2005, 2006, 2007)]
    # Founder sub-groups remain explicit so the two published accounts can
    # share the same dated calendar without inventing an unlinked founder.
    dates += [
        _Date(1990, _time(2, 1), "captive_group_a_capture_early"),
        _Date(1991, _time(9, 27), "captive_group_a_capture_late"),
        _Date(1991, _time(8, 29), "adult_capture_1991_early"),
        _Date(1991, _time(9, 27), "adult_capture_1991_late"),
        _Date(1991, _time(8, 29), "immature_capture_1991_early"),
        _Date(1991, _time(9, 27), "immature_capture_1991_late"),
        _Date(1990, _time(2, 1), "sanger_extra_capture_early"),
        _Date(1991, _time(9, 27), "sanger_extra_capture_late"),
        _Date(1992, _time(2, 6), "primary_extra_wild_capture_early"),
        _Date(1992, _time(11, 29), "primary_extra_wild_capture_late"),
        _Date(1992, _time(2, 7), "additional_1992_release_early"),
        _Date(1992, _time(11, 30), "additional_1992_release_late"),
    ]
    return sorted({(d.year, round(d.time, 12), d.label): d for d in dates if start_year <= d.year <= end_year}.values(), key=lambda d: (d.year, d.time, d.label))


def _event_id(site: str, date: _Date, ordinal: int) -> int:
    digest = hashlib.blake2s(f"{site}:{date.year}:{date.time:.12f}:{date.label}:{ordinal}".encode(), digest_size=4).digest()
    return int.from_bytes(digest, "little") & 0x7FFFFFFF


def _calendar_event_id(site: str, date: _Date, dates: list[_Date]) -> int:
    ordinal = sum(1 for item in dates if item.year == date.year and (item.time, item.label) < (date.time, date.label))
    return _event_id(site, date, ordinal)


def _full_vector(values: np.ndarray, max_age: int) -> np.ndarray:
    result = np.zeros((2, max_age + 1), dtype=float)
    result[:, :max_age] = values
    return result


def _holding_to(item: dict[str, Any], year: int, time: float, demography: AgeDemography) -> np.ndarray:
    """Release-eligible cohorts, conditioning on the known survivor record.

    Holding mortality is supplied by the documented survivor count. Cohorts
    still age; a fish reaching the terminal class cannot be released alive.
    The unselected capture-cohort complement is retained for death accounting.
    """
    if (year, time) <= (int(item["year"]), float(item["time"])):
        raise ValueError("capture must precede its linked release")
    years = year - int(item["year"])
    current = np.asarray(item["state"], dtype=float)
    available = np.zeros_like(current)
    for age in range(demography.max_age):
        if age + years < demography.max_age:
            available[:, age + years] = current[:, age]
    return available


def _select_vector(values: np.ndarray, count: int, *, seed: int, key: int, stochastic: bool) -> np.ndarray:
    total = int(round(float(values.sum()))) if stochastic else float(values.sum())
    if count > total + 1e-12:
        raise ValueError(f"holding {key} has only {total:g} fish; release requires {count}")
    if count == 0:
        return np.zeros_like(values)
    if stochastic:
        rng = np.random.default_rng(np.random.SeedSequence([seed, 62000, key]))
        draw = rng.multivariate_hypergeometric(values.astype(np.int64).ravel(), count)
        return draw.reshape(values.shape).astype(float)
    return values * (count / total)


def _params(params: Any) -> _Parameters:
    return params if isinstance(params, _Parameters) else _Parameters(params)


def run_linked_history(
    demography: AgeDemography,
    params: Any,
    scales: Mapping[str, float],
    *,
    restriction: str,
    eta_refuge: float,
    recruitment_sigma: float,
    strath_pre2007: float,
    seed: int,
    ledger_timing: str = "early",
    march_retention: bool = False,
    removal_account: str = "primary_plan_31_early_releases",
    no_wild_removals: bool = False,
    overshoot_removed: bool = False,
    start_year: int = 1965,
    end_year: int = 2012,
    stochastic: bool = True,
) -> dict[str, Any]:
    """Run one linked three-site history with explicit dated ledgers."""
    try:
        if not isinstance(demography, AgeDemography):
            raise TypeError("demography must be AgeDemography")
        if restriction not in RESTRICTIONS:
            raise ValueError(f"restriction must be one of {RESTRICTIONS}")
        if ledger_timing not in ("early", "late"):
            raise ValueError("ledger_timing must be early or late")
        if removal_account not in ("primary_plan_31_early_releases", "sanger_42_early_releases_held_before_1992"):
            raise ValueError("unknown removal account")
        if not isinstance(start_year, int) or not isinstance(end_year, int) or start_year > end_year:
            raise ValueError("invalid year range")
        if isinstance(seed, bool) or seed < 0:
            raise ValueError("seed must be nonnegative")
        eta_refuge = float(eta_refuge)
        recruitment_sigma = float(recruitment_sigma)
        strath_pre2007 = float(strath_pre2007)
        if not 0 < eta_refuge <= 1 or recruitment_sigma < 0 or not 0 <= strath_pre2007 <= 1:
            raise ValueError("invalid refuge, recruitment or Strathgordon parameter")
        required = {"pedder_lake", "pedder_refuge", "oberon", "strathgordon"}
        if set(scales) != required:
            raise ValueError(f"scales must contain exactly {sorted(required)}")
        if any(float(scales[name]) < 0 or not math.isfinite(float(scales[name])) for name in required):
            raise ValueError("scales must be finite and nonnegative")
        p = _params(params)
        rows = _forcing_rows(p, start_year - 1, end_year, overshoot_removed=overshoot_removed)
        dates = _calendar(start_year, end_year)
        calendar_payload = [(d.year, round(d.time, 12), d.label) for d in dates]
        calendar_hash = hashlib.sha256(json.dumps(calendar_payload, separators=(",", ":")).encode()).hexdigest()
        weights = demography.recruitment_weights
        neutral: dict[str, Any] = {}
        pedder_eq = neutral_equilibrium_from_abundance(demography, float(scales["pedder_lake"]), float(scales["pedder_refuge"]))
        neutral["pedder"] = pedder_eq
        for site in ("oberon", "strathgordon"):
            total = float(scales[site])
            neutral[site] = neutral_equilibrium_from_abundance(demography, total * weights[0], total * weights[1])
        states = {
            "pedder": (np.floor(pedder_eq["state"] + .5) if stochastic else pedder_eq["state"].copy()),
            "oberon": np.zeros_like(pedder_eq["state"]),
            "strathgordon": np.zeros_like(pedder_eq["state"]),
        }
        rounding = {site: neutral[site]["state"] - states[site] if site == "pedder" else np.zeros_like(states[site]) for site in SITES}
        limits = {site: neutral[site]["limits"] for site in SITES}
        annual_states = {site: {} for site in SITES}
        year_diagnostics = {site: {} for site in SITES}
        checkpoints = {site: [] for site in SITES}
        removal_ledger: list[dict[str, Any]] = []
        holding_ledger: list[dict[str, Any]] = []
        transfer_ledger: list[dict[str, Any]] = []
        addition_ledger: list[dict[str, Any]] = []
        failures: list[str] = []
        holdings: list[dict[str, Any]] = []
        advance_calls = 0

        def date_for(label: str) -> _Date:
            matches = [d for d in dates if d.label == label]
            if not matches:
                raise ValueError(f"calendar date missing for {label}")
            return matches[0]

        def event_map(site: str, year: int, replacements: Mapping[str, CountEvent]) -> tuple[CountEvent, ...]:
            year_dates = [d for d in dates if d.year == year]
            events = []
            for ordinal, date in enumerate(year_dates):
                expected_id = _event_id(site, date, ordinal)
                event = replacements.get(date.label, CountEvent(expected_id, date.time, 1 if site == "pedder" else 0))
                if event.event_id != expected_id:
                    event = replace(event, event_id=expected_id)
                events.append(event)
            return tuple(events)

        transfer_counts = {2001: 52, 2002: 22, 2005: 117, 2006: 53, 2007: 109}
        for year in range(start_year, end_year + 1):
            current = rows[year]
            previous = rows[year - 1]
            replacements: dict[str, CountEvent] = {}
            if not no_wild_removals:
                group_a_label = "captive_group_a_capture_early" if ledger_timing == "early" else "captive_group_a_capture_late"
                sanger_label = "sanger_extra_capture_early" if ledger_timing == "early" else "sanger_extra_capture_late"
                if year == (1990 if ledger_timing == "early" else 1991) and any(item.label == group_a_label for item in dates):
                    d = date_for(group_a_label)
                    # All twelve were recorded in spawning condition: five
                    # females and seven males. Only the released subset is
                    # conditioned to remain alive within the age ceiling.
                    replacements[group_a_label] = CountEvent(
                        _event_id("pedder", d, 1), d.time, 1,
                        remove_count=12, min_start_age=1, sex_counts=(5, 7),
                    )
                    if removal_account.startswith("sanger"):
                        s = date_for(sanger_label)
                        replacements[sanger_label] = CountEvent(
                            _event_id("pedder", s, 2), s.time, 1,
                            remove_count=11, min_start_age=0,
                            # All eleven are conditioned on the known 1992
                            # release. This constrains latent capture ages;
                            # insufficient source fish still fail, without redraw.
                            max_start_age=demography.max_age - 1 - (1992 - s.year),
                        )
                if year == 1991:
                    d = date_for(f"adult_capture_1991_{ledger_timing}")
                    replacements[d.label] = CountEvent(
                        _event_id("pedder", d, 3), d.time, 1,
                        remove_count=10, min_start_age=1, sex_counts=(5, 5),
                    )
                    d = date_for(f"immature_capture_1991_{ledger_timing}")
                    replacements[d.label] = CountEvent(
                        _event_id("pedder", d, 4), d.time, 1,
                        remove_count=1, min_start_age=0, max_start_age=0,
                    )
                if year == 1992:
                    d = date_for("february_1992_capture")
                    replacements[d.label] = CountEvent(_event_id("pedder", d, 5), d.time, 1, remove_count=1, min_start_age=1)
                    d = date_for(f"primary_extra_wild_capture_{ledger_timing}")
                    replacements[d.label] = CountEvent(_event_id("pedder", d, 6), d.time, 1, remove_count=1, min_start_age=0)
                if year == 1996:
                    d = date_for(f"january_1996_pre_removal_{ledger_timing}")
                    replacements[d.label] = CountEvent(
                        _event_id("pedder", d, 4), d.time, 1,
                        remove_count=4, min_start_age=0,
                    )
                    d = date_for("march_1996_record")
                    if march_retention:
                        replacements[d.label] = CountEvent(_event_id("pedder", d, 5), d.time, 1, remove_count=1, min_start_age=0)
            pedder_conditions = conditions_from_forcing(
                demography, p, current, previous, restriction,
                post_habitat_refuge_fraction=eta_refuge, recruitment_sigma=recruitment_sigma,
            )
            try:
                advance_calls += 1
                next_pedder, pdiag = advance(states["pedder"], demography, limits["pedder"], conditions=pedder_conditions,
                                             seed=seed, year=year, site_id="pedder", stochastic=stochastic,
                                             events=event_map("pedder", year, replacements))
            except (ValueError, TypeError) as exc:
                failures.append(f"pedder {year}: {exc}")
                return _failure_result(failures, calendar_hash, removal_ledger, holding_ledger, transfer_ledger, addition_ledger,
                                       advance_calls=advance_calls, annual_states=annual_states, checkpoints=checkpoints)
            states["pedder"] = next_pedder
            year_diagnostics["pedder"][year] = _annual_summary(pdiag)
            _record_checkpoints("pedder", year, pdiag, dates, checkpoints)
            if year == 1996:
                point = next(x for x in checkpoints["pedder"]
                             if x["label"] == f"january_1996_pre_removal_{ledger_timing}")
                checkpoints["pedder"].append({**point, "label": "january_1996_pre_removal"})
            _record_removals("pedder", year, pdiag, replacements, removal_ledger, holdings, demography, seed, stochastic)

            # Build additions from released held fish and the same-year direct captures.
            oberon_replacements: dict[str, CountEvent] = {}
            if not no_wild_removals:
                if year == 1991:
                    d = date_for("november_1991_release")
                    group_a_label = "captive_group_a_capture_early" if ledger_timing == "early" else "captive_group_a_capture_late"
                    group_a = _release_holdings(
                        holdings, year, d.time, 7, demography, seed, stochastic,
                        holding_ledger, prefix=group_a_label, sex_counts=(3, 4), min_release_age=1,
                    )
                    adult = _release_holdings(
                        holdings, year, d.time, 10, demography, seed, stochastic,
                        holding_ledger, prefix=f"adult_capture_1991_{ledger_timing}",
                        sex_counts=(5, 5), min_release_age=1,
                    )
                    immature = _release_holdings(
                        holdings, year, d.time, 1, demography, seed, stochastic,
                        holding_ledger, prefix=f"immature_capture_1991_{ledger_timing}", max_release_age=0,
                    )
                    vector = group_a + adult + immature
                    oberon_replacements[d.label] = CountEvent(_event_id("oberon", d, 10), d.time, 0, addition=vector)
                    addition_ledger.append({"site": "oberon", "year": year, "time": d.time,
                                           "label": d.label, "count": float(vector.sum()),
                                           "vector": vector.copy(), "failure": None})
                    _record_captive_deaths(holdings, group_a_label, 5, year, d.time, holding_ledger)
                if year == 1992:
                    direct = _actual_removal(pdiag, 1, time=date_for("february_1992_capture").time)
                    d = date_for("february_1992_release")
                    additions = _full_vector(direct, demography.max_age)
                    addition_ledger.append({"site": "oberon", "year": year, "time": d.time,
                                           "label": "february_1992_wild_release", "count": float(additions.sum()),
                                           "vector": additions.copy(), "failure": None})
                    offspring = np.zeros_like(additions)
                    if stochastic:
                        female_count = np.random.default_rng(np.random.SeedSequence([seed, year, 70000])).binomial(11, demography.female_fraction)
                    else:
                        female_count = 11.0 * demography.female_fraction
                    offspring[0, 0], offspring[1, 0] = female_count, 11.0 - female_count
                    additions += offspring
                    addition_ledger.append({"site": "oberon", "year": year, "time": d.time,
                                           "label": "captive_broodstock_offspring", "count": 11.0,
                                           "vector": offspring.copy(), "failure": None,
                                           "parent_identity_assumption": "stripped parents overlap documented adult captures; no additional wild removal"})
                    oberon_replacements[d.label] = CountEvent(_event_id("oberon", d, 11), d.time, 0, addition=additions)
                    extra_date = date_for(f"primary_extra_wild_capture_{ledger_timing}")
                    release_date = date_for(f"additional_1992_release_{ledger_timing}")
                    extra = _actual_removal(pdiag, 1, time=extra_date.time)
                    extra_vector = _full_vector(extra, demography.max_age)
                    addition_ledger.append({"site": "oberon", "year": year, "time": release_date.time,
                                           "label": "primary_extra_wild_release", "count": float(extra_vector.sum()),
                                           "vector": extra_vector.copy(), "failure": None})
                    if removal_account.startswith("sanger"):
                        held = _release_holdings(
                            holdings, year, release_date.time, 11, demography, seed, stochastic,
                            holding_ledger, prefix=f"sanger_extra_capture_{ledger_timing}",
                        )
                        addition_ledger.append({"site": "oberon", "year": year, "time": release_date.time,
                                               "label": "sanger_additional_held_release", "count": 11.0,
                                               "vector": held.copy(), "failure": None})
                        extra_vector += held
                    oberon_replacements[release_date.label] = CountEvent(
                        _event_id("oberon", release_date, 13), release_date.time, 0,
                        addition=extra_vector,
                    )
                if year == 1997:
                    d = date_for(f"may_1997_release_{ledger_timing}")
                    held = _release_holdings(
                        holdings, year, d.time, 3, demography, seed, stochastic,
                        holding_ledger, prefix=f"january_1996_pre_removal_{ledger_timing}",
                    )
                    oberon_replacements[d.label] = CountEvent(_event_id("oberon", d, 12), d.time, 0, addition=held)
                    addition_ledger.append({"site": "oberon", "year": year, "time": d.time,
                                           "label": d.label, "count": 3.0,
                                           "vector": held.copy(), "failure": None})
                    _record_captive_deaths(holdings, f"january_1996_pre_removal_{ledger_timing}",
                                           1, year, d.time, holding_ledger)
            if year in transfer_counts:
                label = f"transfer_{year}_{ledger_timing}"
                d = date_for(label)
                if not no_wild_removals:
                    oberon_replacements[label] = CountEvent(_event_id("oberon", d, 20 + year), d.time, -1, remove_count=transfer_counts[year])
            ob_conditions = AgeConditions(
                recruitment_sigma=recruitment_sigma,
                recruitment_multiplier=1.0,
                lake_limit_multiplier=1.0,
                refuge_limit_multiplier=1.0,
            )
            try:
                advance_calls += 1
                next_oberon, odiag = advance(states["oberon"], demography, limits["oberon"], conditions=ob_conditions,
                                              seed=seed, year=year, site_id="oberon", stochastic=stochastic,
                                              events=event_map("oberon", year, oberon_replacements))
            except (ValueError, TypeError) as exc:
                failures.append(f"oberon {year}: {exc}")
                return _failure_result(failures, calendar_hash, removal_ledger, holding_ledger, transfer_ledger, addition_ledger,
                                       advance_calls=advance_calls, annual_states=annual_states, checkpoints=checkpoints)
            states["oberon"] = next_oberon
            year_diagnostics["oberon"][year] = _annual_summary(odiag)
            _record_checkpoints("oberon", year, odiag, dates, checkpoints)
            transfer_addition: dict[str, CountEvent] = {}
            if year in transfer_counts and not no_wild_removals:
                label = f"transfer_{year}_{ledger_timing}"
                entry = _removal_entry(odiag, transfer_counts[year])
                moved = np.asarray(entry["actual_removal_by_sex_age"])
                donor = np.asarray(entry["actual_removal_by_compartment_sex_age"])
                conserved = bool(np.array_equal(donor.sum(axis=0), moved)
                                 and np.isclose(moved.sum(), transfer_counts[year]))
                if not conserved:
                    raise ValueError("donor and recipient transfer vectors do not conserve fish")
                d = date_for(label)
                transfer_addition[label] = CountEvent(_event_id("strathgordon", d, 20 + year), d.time, 0, addition=_full_vector(moved, demography.max_age))
                transfer_ledger.append({"year": year, "time": d.time, "count": transfer_counts[year],
                                        "vector": _full_vector(moved, demography.max_age).copy(),
                                        "donor_by_compartment_sex_age": donor.copy(),
                                        "pre_event_eligible_count": entry["pre_event_eligible_count"],
                                        "pre_event_eligible_by_sex_age": entry["pre_event_eligible_by_sex_age"].copy(),
                                        "fraction_removed": float(moved.sum()/entry["pre_event_eligible_count"]),
                                        "fraction_removed_by_sex": np.divide(moved.sum(axis=1),
                                            entry["pre_event_eligible_by_sex_age"].sum(axis=1),
                                            out=np.zeros(2), where=entry["pre_event_eligible_by_sex_age"].sum(axis=1) > 0),
                                        "conserved": conserved, "failure": None})
            strath_mult = strathgordon_spawn_multiplier(year, pre_2007=strath_pre2007)
            strath_conditions = AgeConditions(recruitment_sigma=recruitment_sigma, recruitment_multiplier=strath_mult)
            try:
                advance_calls += 1
                next_strath, sdiag = advance(states["strathgordon"], demography, limits["strathgordon"], conditions=strath_conditions,
                                              seed=seed, year=year, site_id="strathgordon", stochastic=stochastic,
                                              events=event_map("strathgordon", year, transfer_addition))
            except (ValueError, TypeError) as exc:
                failures.append(f"strathgordon {year}: {exc}")
                return _failure_result(failures, calendar_hash, removal_ledger, holding_ledger, transfer_ledger, addition_ledger,
                                       advance_calls=advance_calls, annual_states=annual_states, checkpoints=checkpoints)
            states["strathgordon"] = next_strath
            year_diagnostics["strathgordon"][year] = _annual_summary(sdiag)
            _record_checkpoints("strathgordon", year, sdiag, dates, checkpoints)
            for site in SITES:
                annual_states[site][year] = states[site].copy()
        early_window_extractions = [
            entry for entry in removal_ledger
            if entry.get("site") == "pedder"
            and (1990, _time(2, 1)) <= (int(entry["year"]), float(entry["time"])) <= (1991, _time(9, 30))
        ]
        early_wild_extractions = [
            entry for entry in removal_ledger
            if entry.get("site") == "pedder" and int(entry["year"]) <= 1992
        ]
        return {
            "valid": True, "failure": None, "annual_states": annual_states,
            "checkpoint_states": checkpoints, "removal_ledger": removal_ledger,
            "holding_ledger": holding_ledger, "addition_ledger": addition_ledger,
            "transfer_ledger": transfer_ledger,
            "neutral_scales": {name: float(scales[name]) for name in required},
            "neutral_limits": limits, "neutral_states": neutral,
            "neutral_refuge_index": {
                site: float(neutral[site]["R0"] * (1 - demography.lake_settlement))
                for site in SITES
            },
            "rounding": rounding, "calendar": calendar_payload, "calendar_hash": calendar_hash,
            "forcing": rows, "restriction": restriction, "seed": seed,
            "early_wild_extractions": early_wild_extractions,
            "early_wild_extraction_count": float(sum(item["actual_by_sex_age"].sum() for item in early_wild_extractions)),
            "early_window_extractions": early_window_extractions,
            "early_window_extraction_count": float(sum(item["actual_by_sex_age"].sum() for item in early_window_extractions)),
            "advance_calls": advance_calls, "nominal_site_histories": len(SITES),
            "per_year_diagnostics": year_diagnostics,
        }
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        partial = locals()
        return _failure_result(
            [f"linked history year {partial.get('year', 'setup')}: {exc}"],
            partial.get("calendar_hash", ""), partial.get("removal_ledger", []),
            partial.get("holding_ledger", []), partial.get("transfer_ledger", []),
            partial.get("addition_ledger", []), advance_calls=partial.get("advance_calls", 0),
            annual_states=partial.get("annual_states", {}), checkpoints=partial.get("checkpoints", {}),
        )


def _removal_entry(diag: Mapping[str, Any], requested: int, *, time: float | None = None) -> dict:
    entries = [entry for entry in diag.get("event_diagnostics", ())
               if abs(float(np.asarray(entry.get("actual_removal_by_sex_age", np.zeros((2, 1)))).sum()) - requested) < 1e-9]
    if time is not None:
        entries = [entry for entry in entries if abs(float(entry.get("time", -1)) - time) < 1e-12]
    if not entries:
        raise ValueError(f"removal event of {requested} fish did not produce a removal")
    return entries[-1]


def _actual_removal(diag: Mapping[str, Any], requested: int, *, time: float | None = None) -> np.ndarray:
    return np.asarray(_removal_entry(diag, requested, time=time)["actual_removal_by_sex_age"], dtype=float)


def _annual_summary(diag: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "pre_spawn_females": float(diag.get("pre_spawn_females", 0.0)),
        "pre_spawn_males": float(diag.get("pre_spawn_males", 0.0)),
        "breeding_gate": bool(diag.get("breeding_gate", False)),
        "mean_recruits": np.asarray(diag.get("marginal_recruits_before_hazard", (0.0, 0.0))).copy(),
        "realized_recruits": np.asarray(diag.get("drawn_recruits_before_hazard", (0.0, 0.0))).copy(),
        "surviving_newborns": np.asarray(diag.get("surviving_newborns", (0.0, 0.0))).copy(),
        "environment_multiplier": float(diag.get("environment_multiplier", 1.0)),
        "ageout_total": float(diag.get("ageout_total", 0.0)),
    }


def _record_checkpoints(site: str, year: int, diag: Mapping[str, Any], dates: list[_Date], output: dict[str, list[dict[str, Any]]]) -> None:
    by_id = {int(entry["event_id"]): entry for entry in diag.get("event_diagnostics", ())}
    for date in dates:
        if date.year != year:
            continue
        event_id = _calendar_event_id(site, date, dates)
        entry = by_id.get(event_id)
        if entry is not None and "pre_event_state" in entry:
            output[site].append({"label": date.label, "year": year, "time": date.time, "state": entry["pre_event_state"].copy()})


def _record_removals(site: str, year: int, diag: Mapping[str, Any], replacements: Mapping[str, CountEvent], ledger: list[dict[str, Any]], holdings: list[dict[str, Any]], demography: AgeDemography, seed: int, stochastic: bool) -> None:
    for entry in diag.get("event_diagnostics", ()):
        removed = np.asarray(entry.get("actual_removal_by_sex_age", np.zeros((2, demography.max_age))), dtype=float)
        if removed.sum() <= 0:
            continue
        label = next((name for name, event in replacements.items()
                      if abs(float(event.time) - float(entry["time"])) < 1e-12
                      and int(event.remove_count) == int(round(float(removed.sum())))), "unknown")
        pre_state = np.asarray(entry["pre_event_state"])[entry["compartment"]]
        pre_by_sex = pre_state.sum(axis=1)
        removal_by_sex = removed.sum(axis=1)
        ledger.append({"site": site, "year": year, "time": entry["time"], "label": label,
                       "requested": float(removed.sum()), "actual_by_sex_age": removed.copy(),
                       "pre_event_state": pre_state.copy(), "pre_event_total": float(pre_state.sum()),
                       "fraction_removed": float(removed.sum()/pre_state.sum()),
                       "fraction_removed_by_sex": np.divide(removal_by_sex, pre_by_sex,
                            out=np.zeros(2), where=pre_by_sex > 0), "failure": None})
        if label.startswith(("captive_group_a_capture_", "adult_capture_1991_",
                             "immature_capture_1991_", "sanger_extra_capture_",
                             "january_1996_pre_removal_")):
            holdings.append({"id": int(entry["event_id"]), "state": _full_vector(removed, demography.max_age), "year": year, "time": entry["time"], "label": label})


def _release_holdings(holdings: list[dict[str, Any]], year: int, time: float, count: int, demography: AgeDemography,
                      seed: int, stochastic: bool, ledger: list[dict[str, Any]], prefix: str | tuple[str, ...] | None = None,
                      sex_counts: tuple[int, int] | None = None, min_release_age: int = 0,
                      max_release_age: int | None = None) -> np.ndarray:
    selected = np.zeros((2, demography.max_age + 1), dtype=float)
    if prefix is None:
        candidates = list(holdings)
    elif isinstance(prefix, tuple):
        candidates = [item for item in holdings if item["label"] in prefix]
    else:
        candidates = [item for item in holdings if item["label"] == prefix]
    remaining = count
    for item in candidates:
        if remaining <= 0:
            break
        # Release records identify the surviving subset.  Condition this
        # known subset on survival while retaining the cohort-age clock and
        # terminal-age rule; do not score its holding survival again as
        # establishment evidence.
        available = _holding_to(item, year, time, demography)
        available[:, :min_release_age] = 0
        if max_release_age is not None:
            available[:, max_release_age + 1:] = 0
        if sex_counts is not None:
            required = tuple(int(value) for value in sex_counts)
            if sum(required) > count:
                raise ValueError("sex-constrained release exceeds requested count")
            # The release record constrains the combined group.  Apply those
            # constraints against the first holding item and draw any
            # unsexed remainder from the residual pool.
            target = np.zeros_like(available)
            residual = available.copy()
            for sex, needed in enumerate(required):
                if needed == 0:
                    continue
                sex_total = float(residual[sex].sum())
                if needed > sex_total + 1e-12:
                    raise ValueError(f"holding {item['id']} lacks required sex allocation")
                target[sex] = _select_vector(residual[sex:sex + 1], needed, seed=seed,
                                             key=int(item["id"]) + 100 + sex, stochastic=stochastic)[0]
                residual[sex] -= target[sex]
            residual_count = count - sum(required)
            if residual_count:
                target += _select_vector(residual, residual_count, seed=seed,
                                         key=int(item["id"]) + 200, stochastic=stochastic)
            vector = target
            take = count
        else:
            take = min(remaining, int(round(float(available.sum()))) if stochastic else remaining)
            vector = _select_vector(available, take, seed=seed, key=int(item["id"]), stochastic=stochastic)
        selected += vector
        remaining -= take
        capture_vector = np.zeros_like(vector)
        years = year - int(item["year"])
        for age in range(demography.max_age):
            if age + years < demography.max_age:
                capture_vector[:, age] = vector[:, age + years]
        residual = np.asarray(item["state"]) - capture_vector
        if np.any(residual < -1e-10) or not np.isclose(capture_vector.sum(), vector.sum()):
            raise ValueError("holding release cannot be mapped to its captured cohorts")
        item["state"] = np.maximum(residual, 0)
        ledger.append({"capture_label": item["label"], "release_year": year, "release_time": time,
                       "count": float(vector.sum()), "conditioned": True,
                       "capture_year": item["year"], "capture_time": item["time"],
                       "released_capture_cohorts": capture_vector,
                       "vector": vector.copy(), "failure": None, "status": "released"})
    if remaining:
        raise ValueError(f"insufficient held fish for release of {count}; missing {remaining}")
    return selected


def _record_captive_deaths(holdings, prefix, count, year, time, ledger):
    matches = [item for item in holdings if item["label"] == prefix]
    if len(matches) != 1 or not np.isclose(matches[0]["state"].sum(), count):
        raise ValueError("documented captive deaths do not match the captured complement")
    item = matches[0]
    ledger.append({"capture_label": prefix, "count": float(count), "conditioned": True,
                   "status": "documented_captive_deaths", "capture_year": item["year"],
                   "capture_time": item["time"], "death_before_year": year, "death_before_time": time,
                   "vector": item["state"].copy(), "age_basis": "capture_cohorts",
                   "failure": None})
    item["state"] = np.zeros_like(item["state"])


def _failure_result(failures: list[str], calendar_hash: str, removals: list[Any], holdings: list[Any], transfers: list[Any], additions: list[Any] | None = None, *, advance_calls: int = 0, annual_states: dict[str, Any] | None = None, checkpoints: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"valid": False, "failure": "; ".join(failures), "failures": failures,
            "annual_states": annual_states or {}, "checkpoint_states": checkpoints or {}, "removal_ledger": removals,
            "holding_ledger": holdings, "addition_ledger": additions or [],
            "transfer_ledger": transfers, "calendar_hash": calendar_hash,
            "advance_calls": advance_calls, "nominal_site_histories": len(SITES)}


__all__ = ["run_linked_history"]
