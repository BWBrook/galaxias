"""Bounded age/sex demographic kernel for two Galaxias compartments.

The state is ``(compartment, sex, age)`` with compartment order lake/refuge,
sex order female/male, and ages 0 through ``max_age``.  Age ``max_age`` is a
terminal slot: fish in it are removed at the beginning of the following
update.  Annual breeding participation is supplied by ``m[a + 1]`` for an
age ``a`` fish; it is a participation probability, not a persistent maturity
state.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from numbers import Real
from typing import Any, Iterable

import numpy as np

from galaxias_model.recruitment_demography import RecruitmentLimits, _stable_bh


_COMPARTMENTS = ("lake", "refuge")
_SEXES = ("female", "male")


def _real(name: str, value: Any, *, minimum: float | None = None,
          maximum: float | None = None) -> float:
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


def _tuple(name: str, values: Iterable[Any], length: int,
           *, minimum: float = 0.0, maximum: float | None = None) -> tuple[float, ...]:
    try:
        result = tuple(_real(f"{name}[{i}]", value, minimum=minimum, maximum=maximum)
                       for i, value in enumerate(values))
    except TypeError as exc:
        raise ValueError(f"{name} must be a finite sequence") from exc
    if len(result) != length:
        raise ValueError(f"{name} must have length {length}")
    return result


def _hazard_matrix(name: str, values: Any, max_age: int) -> np.ndarray:
    if values is None:
        return np.zeros((2, max_age), dtype=float)
    raw = np.asarray(values)
    if raw.dtype.kind not in "iuf":
        raise ValueError(f"{name} must contain numeric values")
    array = raw.astype(float)
    if array.ndim == 0:
        array = np.full((max_age,), float(array))
    if array.shape == (max_age,):
        array = np.repeat(array[None, :], 2, axis=0)
    if array.shape != (2, max_age) or not np.all(np.isfinite(array)) or np.any(array < 0):
        raise ValueError(f"{name} must have shape (2, {max_age}) and be finite and nonnegative")
    return array.copy()


@dataclass(frozen=True)
class AgeDemography:
    """Age-specific survival, annual participation, and neutral recruitment."""

    annual_survival: tuple[float, ...]
    breeding_probability: tuple[float, ...]
    recruits_per_female: float | None = None
    lake_settlement: float = 0.5
    spawn_fraction: float = 0.75
    female_fraction: float = 0.5
    b: float | None = None

    def __post_init__(self) -> None:
        survival = tuple(self.annual_survival)
        if not survival:
            raise ValueError("annual_survival must contain at least one age")
        max_age = len(survival)
        object.__setattr__(self, "annual_survival", _tuple("annual_survival", survival, max_age,
                                                             maximum=1.0))
        object.__setattr__(self, "breeding_probability",
                           _tuple("breeding_probability", self.breeding_probability, max_age + 1,
                                  maximum=1.0))
        if self.breeding_probability[0] != 0.0 or self.breeding_probability[1] != 0.0:
            raise ValueError("breeding_probability[0:2] must be zero")
        if self.recruits_per_female is None:
            if self.b is None:
                raise ValueError("recruits_per_female must be supplied")
            object.__setattr__(self, "recruits_per_female", self.b)
        elif self.b is not None and float(self.recruits_per_female) != float(self.b):
            raise ValueError("b and recruits_per_female must agree")
        _real("recruits_per_female", self.recruits_per_female, minimum=0.0)
        _real("lake_settlement", self.lake_settlement, minimum=0.0, maximum=1.0)
        _real("spawn_fraction", self.spawn_fraction, minimum=0.0, maximum=1.0)
        _real("female_fraction", self.female_fraction, minimum=0.0, maximum=1.0)
        if self.female_fraction != 0.5:
            raise ValueError("female_fraction must be 0.5 for the neutral half-sex equilibrium")

    @property
    def max_age(self) -> int:
        return len(self.annual_survival)

    @property
    def recruitment_weights(self) -> tuple[float, float]:
        return self.lake_settlement, 1.0 - self.lake_settlement

    @property
    def lake_weight(self) -> float:
        return self.lake_settlement


@dataclass(frozen=True)
class AgeConditions:
    """Annual threats, recruitment variation, and lake-to-refuge movement."""

    old_hazard_lake: Any = None
    old_hazard_refuge: Any = None
    late_hazard_lake: Any = None
    late_hazard_refuge: Any = None
    newborn_hazard_lake: float = 0.0
    newborn_hazard_refuge: float = 0.0
    birth_hazard_fraction: float = 1.0 / 12.0
    movement_probability: float = 0.0
    recruitment_multiplier: float = 1.0
    lake_limit_multiplier: float = 1.0
    refuge_limit_multiplier: float = 1.0
    recruitment_sigma: float = 0.0
    old_hazards: Any = None
    late_hazards: Any = None

    def validate(self, max_age: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        # A single age vector is accepted independently for each compartment.
        if self.old_hazards is None:
            old = np.vstack((_hazard_matrix("old_hazard_lake", self.old_hazard_lake, max_age)[0],
                             _hazard_matrix("old_hazard_refuge", self.old_hazard_refuge, max_age)[0]))
        else:
            old = _hazard_matrix("old_hazards", self.old_hazards, max_age)
        late_lake = self.old_hazard_lake if self.late_hazard_lake is None else self.late_hazard_lake
        late_refuge = self.old_hazard_refuge if self.late_hazard_refuge is None else self.late_hazard_refuge
        if self.late_hazards is None:
            late = np.vstack((_hazard_matrix("late_hazard_lake", late_lake, max_age)[0],
                              _hazard_matrix("late_hazard_refuge", late_refuge, max_age)[0]))
        else:
            late = _hazard_matrix("late_hazards", self.late_hazards, max_age)
        _real("newborn_hazard_lake", self.newborn_hazard_lake, minimum=0.0)
        _real("newborn_hazard_refuge", self.newborn_hazard_refuge, minimum=0.0)
        _real("birth_hazard_fraction", self.birth_hazard_fraction, minimum=0.0, maximum=1.0)
        _real("movement_probability", self.movement_probability, minimum=0.0, maximum=1.0)
        _real("recruitment_multiplier", self.recruitment_multiplier, minimum=0.0)
        _real("lake_limit_multiplier", self.lake_limit_multiplier, minimum=0.0)
        _real("refuge_limit_multiplier", self.refuge_limit_multiplier, minimum=0.0)
        _real("recruitment_sigma", self.recruitment_sigma, minimum=0.0)
        return old, late, np.asarray((self.newborn_hazard_lake, self.newborn_hazard_refuge)), np.asarray(
            (self.movement_probability, self.birth_hazard_fraction))


@dataclass(frozen=True)
class CountEvent:
    """A dated removal or explicitly allocated addition of old fish."""

    event_id: int
    time: float
    compartment: int
    remove_count: int = 0
    min_start_age: int = 0
    addition: Any = None
    max_start_age: int | None = None
    # Optional known female/male component of a capture.  Values are minima
    # when an unsexed remainder is present; the remainder is drawn from the
    # residual eligible pool.  The default keeps the original pooled draw.
    sex_counts: tuple[int, int] | None = None

    def __post_init__(self) -> None:
        if isinstance(self.event_id, (bool, np.bool_)) or not isinstance(self.event_id, (int, np.integer)):
            raise ValueError("event_id must be an integer")
        _real("event time", self.time, minimum=0.0)
        if self.time >= 1.0:
            raise ValueError("event time must be in [0, 1)")
        if self.compartment not in (-1, 0, 1):
            raise ValueError("event compartment must be 0 (lake), 1 (refuge), or -1 (pooled removal)")
        if self.compartment == -1 and (self.addition is not None or self.sex_counts is not None):
            raise ValueError("pooled removals do not accept additions or sex constraints")
        if isinstance(self.remove_count, (bool, np.bool_)) or not isinstance(self.remove_count, (int, np.integer)) or self.remove_count < 0:
            raise ValueError("remove_count must be a nonnegative integer")
        if isinstance(self.min_start_age, (bool, np.bool_)) or not isinstance(self.min_start_age, (int, np.integer)) or self.min_start_age < 0:
            raise ValueError("min_start_age must be a nonnegative integer")
        if self.max_start_age is not None and (isinstance(self.max_start_age, (bool, np.bool_))
                                               or not isinstance(self.max_start_age, (int, np.integer))
                                               or self.max_start_age < self.min_start_age):
            raise ValueError("max_start_age must be an integer >= min_start_age")
        if self.sex_counts is not None:
            if len(self.sex_counts) != 2 or any(
                    isinstance(value, (bool, np.bool_))
                    or not isinstance(value, (int, np.integer)) or value < 0
                    for value in self.sex_counts):
                raise ValueError("sex_counts must contain two nonnegative integers")
            if sum(self.sex_counts) > self.remove_count:
                raise ValueError("sex_counts cannot exceed remove_count")
        if self.remove_count and self.addition is not None:
            raise ValueError("use separate event IDs for addition and removal")


def zero_state(demography: AgeDemography) -> np.ndarray:
    if not isinstance(demography, AgeDemography):
        raise TypeError("demography must be AgeDemography")
    return np.zeros((2, 2, demography.max_age + 1), dtype=float)


def _validate_state(state: Any, demography: AgeDemography, stochastic: bool) -> np.ndarray:
    raw = np.asarray(state)
    if raw.dtype.kind not in "iuf":
        raise ValueError("state must contain numeric values")
    array = raw.astype(float)
    expected = (2, 2, demography.max_age + 1)
    if array.shape != expected or not np.all(np.isfinite(array)) or np.any(array < 0):
        raise ValueError(f"state must be finite, nonnegative, and have shape {expected}")
    if stochastic and np.any(array != np.floor(array)):
        raise ValueError("stochastic advance requires integer state values")
    return array.copy()


def _keyed_rng(seed: int, year: int, site_id: Any, event_code: int, *indices: int) -> np.random.Generator:
    if isinstance(site_id, (int, np.integer)) and not isinstance(site_id, (bool, np.bool_)):
        site_words = [int(site_id) & 0xFFFFFFFF]
    else:
        digest = hashlib.blake2b(str(site_id).encode(), digest_size=8).digest()
        site_words = list(np.frombuffer(digest, dtype=np.uint32))
    words = [int(seed) & 0xFFFFFFFF, int(year) & 0xFFFFFFFF, int(event_code) & 0xFFFFFFFF]
    words.extend(site_words)
    words.extend(int(i) & 0xFFFFFFFF for i in indices)
    return np.random.default_rng(np.random.SeedSequence(words))


def _survive(value: float, probability: float, *, stochastic: bool, rng: np.random.Generator | None) -> float:
    if stochastic:
        return float(rng.binomial(int(value), probability))
    return value * probability


def _segment_survival(state: np.ndarray, start: float, end: float, demography: AgeDemography,
                      old: np.ndarray, late: np.ndarray, *, stochastic: bool,
                      seed: int, year: int, site_id: Any, segment: int,
                      nursery_boundary: float) -> np.ndarray:
    if end <= start:
        return state
    result = state.copy()
    # The interval is split at the nursery boundary so late_hazard can be
    # supplied without smearing its exposure into early-year observations.
    boundary = nursery_boundary
    pieces = [(start, min(end, boundary), old)]
    if end > boundary:
        pieces = []
        if start < boundary:
            pieces.append((start, boundary, old))
        pieces.append((max(start, boundary), end, late))
    for piece, (left, right, hazards) in enumerate(pieces):
        duration = right - left
        if duration <= 0:
            continue
        for comp in range(2):
            for sex in range(2):
                for age in range(demography.max_age):
                    probability = demography.annual_survival[age] ** duration
                    probability *= math.exp(-hazards[comp, age] * duration)
                    rng = _keyed_rng(seed, year, site_id, 10000 + segment * 10 + piece, comp, sex, age) if stochastic else None
                    result[comp, sex, age] = _survive(result[comp, sex, age], probability,
                                                       stochastic=stochastic, rng=rng)
    return result


def _event_removal(state: np.ndarray, event: CountEvent, *, stochastic: bool,
                   seed: int, year: int, site_id: Any) -> tuple[np.ndarray, dict[str, Any]]:
    comp = event.compartment
    max_age = state.shape[2] - 1
    age_start = min(event.min_start_age, max_age)
    age_end = max_age if event.max_start_age is None else min(max_age, int(event.max_start_age) + 1)
    if comp == -1:
        eligible = np.zeros((2, 2, max_age), dtype=float)
        eligible[:, :, age_start:age_end] = state[:, :, age_start:age_end]
        total = float(eligible.sum())
        if event.remove_count > total + 1e-12:
            raise ValueError(f"event {event.event_id} requests more fish than eligible")
        removed = np.zeros_like(eligible)
        if event.remove_count:
            if stochastic:
                draw = _keyed_rng(seed, year, site_id, 23000 + int(event.event_id))
                removed = draw.multivariate_hypergeometric(
                    eligible.astype(np.int64).ravel(), int(event.remove_count)
                ).reshape(eligible.shape).astype(float)
            else:
                removed = eligible * (event.remove_count / total)
            state[:, :, :max_age] -= removed
        return state, {
            "event_id": int(event.event_id), "compartment": comp, "time": float(event.time),
            "pre_event_eligible_count": total,
            "pre_event_eligible_by_sex_age": eligible.sum(axis=0),
            "pre_event_eligible_by_compartment_sex_age": eligible,
            "actual_removal_by_sex_age": removed.sum(axis=0),
            "actual_removal_by_compartment_sex_age": removed,
        }
    eligible = np.zeros((2, max_age), dtype=float)
    for sex in range(2):
        if age_start < age_end:
            eligible[sex, age_start:age_end] = state[comp, sex, age_start:age_end]
    total = float(np.sum(eligible))
    if event.remove_count > total + 1e-12:
        raise ValueError(f"event {event.event_id} requests more fish than eligible")
    removed = np.zeros_like(eligible)
    if event.remove_count:
        residual_pool = eligible.copy()
        remaining = int(event.remove_count)
        if event.sex_counts is not None:
            for sex, required in enumerate(event.sex_counts):
                if required == 0:
                    continue
                available_sex = float(residual_pool[sex].sum())
                if required > available_sex + 1e-12:
                    raise ValueError(f"event {event.event_id} requests more sex-constrained fish than eligible")
                if stochastic:
                    draw = _keyed_rng(seed, year, site_id, 21000 + int(event.event_id), comp, sex)
                    sex_removed = draw.multivariate_hypergeometric(
                        residual_pool[sex].astype(np.int64), int(required)
                    ).astype(float)
                else:
                    sex_removed = residual_pool[sex] * (required / available_sex)
                removed[sex] += sex_removed
                residual_pool[sex] -= sex_removed
                remaining -= int(required)
        if remaining:
            residual_total = float(residual_pool.sum())
            if remaining > residual_total + 1e-12:
                raise ValueError(f"event {event.event_id} requests more residual fish than eligible")
            if stochastic:
                # Retain the qualified default draw when no sex conditioning
                # is requested; new constrained residuals use their own key.
                code = 20000 if event.sex_counts is None else 22000
                draw = _keyed_rng(seed, year, site_id, code + int(event.event_id), comp)
                residual_removed = draw.multivariate_hypergeometric(
                    residual_pool.astype(np.int64).reshape(-1), remaining
                ).reshape(eligible.shape).astype(float)
            else:
                residual_removed = residual_pool * (remaining / residual_total)
            removed += residual_removed
        for sex in range(2):
            state[comp, sex, :max_age] -= removed[sex]
    return state, {
        "event_id": int(event.event_id),
        "compartment": comp,
        "time": float(event.time),
        "pre_event_eligible_count": total,
        "pre_event_eligible_by_sex_age": eligible,
        "actual_removal_by_sex_age": removed,
    }


def _apply_addition(state: np.ndarray, event: CountEvent, *, stochastic: bool) -> int:
    if event.addition is None:
        return 0
    raw = np.asarray(event.addition)
    if raw.dtype.kind not in "iuf":
        raise ValueError(f"event {event.event_id} addition must contain numeric values")
    addition = raw.astype(float)
    max_age = state.shape[2] - 1
    if addition.shape != (2, max_age + 1) or not np.all(np.isfinite(addition)) or np.any(addition < 0):
        raise ValueError(f"event {event.event_id} addition must have shape (2, {max_age + 1}) and be nonnegative")
    if stochastic and np.any(addition != np.floor(addition)):
        raise ValueError("stochastic event additions must be integer")
    # Addition columns are explicitly start-of-year cohorts.  Thus age 0 is
    # an old cohort even for an event after spawning; current-year newborns
    # are held separately until the end of this update.  The terminal class
    # has no valid continuation and is rejected rather than silently changed.
    if np.any(addition[:, max_age] > 0):
        raise ValueError(f"event {event.event_id} cannot add terminal max_age fish")
    dropped = 0
    state[event.compartment, :, :max_age] += addition[:, :max_age]
    return dropped


def advance(state: Any, demography: AgeDemography, limits: RecruitmentLimits, *,
            conditions: AgeConditions | None = None, seed: int = 0, year: int = 0,
            site_id: Any = 0, stochastic: bool = False,
            events: Iterable[CountEvent] = ()) -> tuple[np.ndarray, dict[str, Any]]:
    """Advance one year, including dated removals/additions and recruitment."""
    if not isinstance(demography, AgeDemography) or not isinstance(limits, RecruitmentLimits):
        raise TypeError("demography and limits must use the public dataclasses")
    if conditions is None:
        conditions = AgeConditions()
    if not isinstance(conditions, AgeConditions):
        raise TypeError("conditions must be AgeConditions or None")
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, (int, np.integer)) or int(seed) < 0:
        raise ValueError("seed must be a nonnegative integer")
    if isinstance(year, (bool, np.bool_)) or not isinstance(year, (int, np.integer)) or int(year) < 0:
        raise ValueError("year must be a nonnegative integer")
    old_hazard, late_hazard, newborn_hazard, misc = conditions.validate(demography.max_age)
    events = tuple(events)
    if any(not isinstance(event, CountEvent) for event in events):
        raise TypeError("events must contain CountEvent values")
    if len({event.event_id for event in events}) != len(events):
        raise ValueError("event_id values must be unique within an advance")
    events = tuple(sorted(events, key=lambda event: (event.time, event.event_id)))
    current = _validate_state(state, demography, stochastic)
    max_age = demography.max_age
    ageout = current[:, :, max_age].copy()
    current[:, :, max_age] = 0.0
    spawn = demography.spawn_fraction
    boundary = 1.0 - conditions.birth_hazard_fraction
    if not (0.0 < boundary < 1.0):
        raise ValueError("birth_hazard_fraction must be between zero and one")
    # Survival breakpoints include the supplied nursery breakpoint, spawning,
    # and every event time.  Applying events before the spawn marker handles ties.
    times = sorted({0.0, spawn, boundary, 1.0, *(event.time for event in events)})
    cursor = 0.0
    event_diagnostics: list[dict[str, Any]] = []
    segment = 0
    pre_spawn = None
    for time in times:
        if time > cursor:
            current = _segment_survival(current, cursor, time, demography, old_hazard, late_hazard,
                                        stochastic=stochastic, seed=int(seed), year=int(year),
                                        site_id=site_id, segment=segment,
                                        nursery_boundary=boundary)
            cursor = time
            segment += 1
        for event in (item for item in events if item.time == time):
            event_state = current.copy()
            dropped = _apply_addition(current, event, stochastic=stochastic)
            current, removal = _event_removal(current, event, stochastic=stochastic,
                                               seed=int(seed), year=int(year), site_id=site_id)
            removal["dropped_terminal_additions"] = dropped
            removal["pre_event_state"] = event_state
            event_diagnostics.append(removal)
        if time == spawn:
            breeders = np.zeros((2, 2, max_age), dtype=float)
            for comp in range(2):
                for sex in range(2):
                    for age in range(max_age):
                        probability = demography.breeding_probability[age + 1]
                        rng = _keyed_rng(int(seed), int(year), site_id, 30000, comp, sex, age) if stochastic else None
                        breeders[comp, sex, age] = _survive(current[comp, sex, age], probability,
                                                            stochastic=stochastic, rng=rng)
            pre_spawn = breeders
    assert pre_spawn is not None
    female_pool = float(np.sum(pre_spawn[:, 0, :]))
    male_pool = float(np.sum(pre_spawn[:, 1, :]))
    mate_consistent = male_pool >= 1.0
    gate = female_pool > 0.0 and (male_pool >= 1.0 if stochastic else male_pool > 0.0)
    weights = np.asarray(demography.recruitment_weights, dtype=float)
    raw_supply = np.zeros(2, dtype=float)
    if gate:
        # Recruitment quality/up-surges act on supply before the density
        # regulation.  The independent stochastic environmental multiplier
        # below is the only multiplier applied after Beverton--Holt.
        raw_supply[:] = (demography.recruits_per_female * female_pool * weights
                         * conditions.recruitment_multiplier)
    limits_array = np.asarray((limits.lake * conditions.lake_limit_multiplier,
                               limits.refuge * conditions.refuge_limit_multiplier), dtype=float)
    if not np.all(np.isfinite(limits_array)):
        raise ValueError("effective recruitment limits must be finite")
    bh_supply = np.asarray([_stable_bh(raw_supply[i], limits_array[i]) for i in range(2)])
    if stochastic and conditions.recruitment_sigma > 0:
        z = _keyed_rng(int(seed), int(year), site_id, 40000).normal()
        environment_multiplier = math.exp(conditions.recruitment_sigma * z - 0.5 * conditions.recruitment_sigma ** 2)
    else:
        environment_multiplier = 1.0
    expected_recruits = bh_supply * environment_multiplier
    newborn = np.zeros((2, 2), dtype=float)
    realized_recruits = np.zeros(2, dtype=float)
    for comp in range(2):
        if stochastic:
            n = float(_keyed_rng(int(seed), int(year), site_id, 41000, comp).poisson(expected_recruits[comp]))
            females = float(_keyed_rng(int(seed), int(year), site_id, 42000, comp).binomial(int(n), demography.female_fraction))
            realized_recruits[comp] = n
            newborn[comp] = (females, n - females)
        else:
            realized_recruits[comp] = expected_recruits[comp]
            newborn[comp] = expected_recruits[comp] * np.asarray((demography.female_fraction,
                                                                   1.0 - demography.female_fraction))
        birth_survival = math.exp(-newborn_hazard[comp] * conditions.birth_hazard_fraction)
        if stochastic:
            for sex in range(2):
                newborn[comp, sex] = _survive(newborn[comp, sex], birth_survival, stochastic=True,
                                               rng=_keyed_rng(int(seed), int(year), site_id, 43000, comp, sex))
        else:
            newborn[comp] *= birth_survival
    # Age surviving old cohorts, then add newborns.  Only age 1+ can move.
    next_state = np.zeros_like(current)
    next_state[:, :, 0] = newborn
    next_state[:, :, 1:] = current[:, :, :max_age]
    movement = conditions.movement_probability
    moved = np.zeros((2, max_age), dtype=float)
    for sex in range(2):
        for age in range(1, max_age + 1):
            if stochastic:
                moved[sex, age - 1] = _survive(next_state[0, sex, age], movement,
                                               stochastic=True,
                                               rng=_keyed_rng(int(seed), int(year), site_id, 50000, sex, age))
            else:
                moved[sex, age - 1] = next_state[0, sex, age] * movement
            next_state[0, sex, age] -= moved[sex, age - 1]
            next_state[1, sex, age] += moved[sex, age - 1]
    # Recruitment means condition on the realized breeder pool. Only the
    # marginal mean integrates over Z; both are before newborn threat survival.
    age1plus = next_state[:, :, 1:].sum(axis=(1, 2))
    diagnostics: dict[str, Any] = {
        "ageout": ageout,
        "ageout_total": float(ageout.sum()),
        "pre_spawn_females": female_pool,
        "pre_spawn_males": male_pool,
        "pre_spawn_females_by_compartment": pre_spawn[:, 0, :].sum(axis=1),
        "pre_spawn_males_by_compartment": pre_spawn[:, 1, :].sum(axis=1),
        "pre_spawn_by_compartment_sex": pre_spawn.sum(axis=2),
        "mate_consistent": mate_consistent,
        "breeding_gate": gate,
        "raw_supply": raw_supply.copy(),
        "marginal_recruits_before_hazard": bh_supply.copy(),
        "conditional_recruits_before_hazard": expected_recruits.copy(),
        "drawn_recruits_before_hazard": realized_recruits.copy(),
        "marginal_recruits_before_hazard_by_compartment": dict(zip(_COMPARTMENTS, bh_supply.tolist())),
        "surviving_newborns": newborn.sum(axis=1),
        "environment_multiplier": environment_multiplier,
        "age1plus_by_compartment": age1plus.copy(),
        "age1plus_total": float(age1plus.sum()),
        "movement_by_sex_age": moved,
        "event_diagnostics": event_diagnostics,
        "mean_field_breeding": not stochastic,
    }
    for i, name in enumerate(_COMPARTMENTS):
        diagnostics[f"marginal_recruits_before_hazard_{name}"] = float(bh_supply[i])
        diagnostics[f"raw_supply_{name}"] = float(raw_supply[i])
        diagnostics[f"conditional_recruits_before_hazard_{name}"] = float(expected_recruits[i])
        diagnostics[f"drawn_recruits_before_hazard_{name}"] = float(realized_recruits[i])
        diagnostics[f"age1plus_{name}"] = float(age1plus[i])
    return next_state, diagnostics


def neutral_equilibrium_from_abundance(demography: AgeDemography,
                                       lake_age1plus: float,
                                       refuge_age1plus: float) -> dict[str, Any]:
    """Construct a neutral age distribution and limits from age-1+ abundance."""
    if not isinstance(demography, AgeDemography):
        raise TypeError("demography must be AgeDemography")
    targets = np.asarray((_real("lake_age1plus", lake_age1plus, minimum=0.0),
                          _real("refuge_age1plus", refuge_age1plus, minimum=0.0)))
    survival = np.asarray((1.0, *demography.annual_survival), dtype=float)
    l = np.cumprod(survival)  # l[0]=1, l[j]=prod(s[:j])
    E = float(np.sum(l[1:demography.max_age + 1]))
    if E <= 0.0 and np.any(targets > 0.0):
        raise ValueError("positive age1+ abundance is impossible when E is zero")
    B = math.fsum(l[j - 1] * demography.annual_survival[j - 1] ** demography.spawn_fraction
                  * demography.breeding_probability[j] for j in range(1, demography.max_age + 1))
    R = targets / E if E > 0 else np.zeros(2)
    F = 0.5 * B * float(np.sum(R))
    x = demography.recruits_per_female * F * np.asarray(demography.recruitment_weights)
    limits = np.zeros(2, dtype=float)
    for i in range(2):
        if targets[i] == 0:
            limits[i] = 0.0
        elif x[i] <= R[i]:
            raise ValueError("requested neutral allocation is unachievable")
        else:
            limits[i] = R[i] * x[i] / (x[i] - R[i])
    state = zero_state(demography)
    for comp in range(2):
        state[comp, :, 0] = R[comp] * 0.5
        for age in range(1, demography.max_age + 1):
            state[comp, :, age] = R[comp] * l[age] * 0.5
    return {
        "state": state,
        "limits": RecruitmentLimits(float(limits[0]), float(limits[1])),
        "lake_limit": float(limits[0]),
        "refuge_limit": float(limits[1]),
        "R0": demography.recruits_per_female * 0.5 * B,
        "recruitment_per_female": demography.recruits_per_female,
        "l": l,
        "E": E,
        "B": B,
        "R": R,
        "F": F,
        "mature_male_pool": float(0.5 * B * np.sum(R)),
        "mate_consistent": bool(0.5 * B * np.sum(R) >= 1.0),
        "mean_field": True,
        "age1plus_targets": targets,
    }


__all__ = ["AgeConditions", "AgeDemography", "CountEvent", "RecruitmentLimits",
           "advance", "neutral_equilibrium_from_abundance", "zero_state"]
