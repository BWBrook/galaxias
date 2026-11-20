"""Bounded early-history and Lake observation adapter.

This module is deliberately separate from the linked historical runner.  It
draws paired nuisance sources, advances Pedder only through 1989, and offers
the small eight-visit observation generators used by the early-Lake method
study.  It contains no intervention ledger, rescue mechanism, terminal label,
or fitted proposal.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from galaxias_model.age_demography import AgeDemography, advance, neutral_equilibrium_from_abundance
from galaxias_model.age_runner import RESTRICTIONS, _Parameters, _forcing_rows
from galaxias_model.age_scenarios import conditions_from_forcing
from galaxias_model.age_sources import DESIGN as DEFAULT_DESIGN, FORCING as DEFAULT_FORCING
from galaxias_model.sampling import _sample_estimated_parameter


EARLY_START_YEAR = 1965
EARLY_END_YEAR = 1989
LAKE_YEARS = (1976, 1977, 1978, 1979, 1980, 1983, 1986, 1989)
LAKE_AGE1_WEIGHT = 0.0
LAKE_RHO = 1.0
LAKE_SITES = 12
LAKE_DIGITISATION_HALF_WIDTH = 0.08
LAKE_EXPECTED_TOTAL = 173.0
_EFFECTS = ("PR020", "PR021", "PR027", "PR028", "PR033")
_ROLES = ("bank", "calibration", "test")
_QUALITY_REGIMES = ("neutral", "engineering")


def keyed_seed(*parts: Any, bits: int = 128) -> int:
    """Return a stable namespace-keyed seed without process hash state."""
    if bits not in (32, 128):
        raise ValueError("seed width must be 32 or 128 bits")
    payload = json.dumps(parts, separators=(",", ":"), sort_keys=True, default=str).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[: bits // 8], "little")


def _load_design(design: Mapping[str, Any] | str | Path | None) -> dict[str, Any]:
    if design is None:
        design = DEFAULT_DESIGN
    if isinstance(design, (str, Path)):
        with Path(design).open() as handle:
            design = json.load(handle)
    if not isinstance(design, Mapping):
        raise TypeError("design must be a mapping or JSON path")
    return dict(design)


def _forcing_rows_from_path(forcing_path: str | Path) -> list[dict[str, str]]:
    with Path(forcing_path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def _uniform(rng: np.random.Generator, support: Mapping[str, Any], name: str) -> float:
    lo, hi = (float(x) for x in support[name])
    if not math.isfinite(lo) or not math.isfinite(hi) or not lo < hi:
        raise ValueError(f"invalid support interval for {name}")
    return float(rng.uniform(lo, hi))


def _log_uniform(rng: np.random.Generator, support: Mapping[str, Any], name: str) -> float:
    lo, hi = (float(x) for x in support[name])
    if not 0 < lo < hi or not math.isfinite(hi):
        raise ValueError(f"invalid positive support interval for {name}")
    return float(np.exp(rng.uniform(math.log(lo), math.log(hi))))


def make_early_lake_source(
    maximum_age: int,
    source_index: int,
    *,
    role: str,
    namespace: str,
    quality_regime: str = "neutral",
    design: Mapping[str, Any] | str | Path | None = None,
    forcing_path: str | Path = DEFAULT_FORCING,
) -> dict[str, Any]:
    """Draw one direct, paired early-Lake source.

    The source ID is shared by both quality regimes and does not contain a
    restriction or quality label.  The random draw for PR032 is consumed in
    both regimes so all other source coordinates remain paired.
    """
    if maximum_age not in (6, 8) or isinstance(maximum_age, bool):
        raise ValueError("maximum_age must be 6 or 8")
    if isinstance(source_index, bool) or not isinstance(source_index, (int, np.integer)) or source_index < 0:
        raise ValueError("source_index must be a nonnegative integer")
    if role not in _ROLES:
        raise ValueError(f"role must be one of {_ROLES}")
    if not namespace:
        raise ValueError("namespace is required")
    if quality_regime not in _QUALITY_REGIMES:
        raise ValueError(f"quality_regime must be one of {_QUALITY_REGIMES}")

    source_index = int(source_index)
    design_data = _load_design(design)
    support = design_data["search_bounds_not_empirical_priors"]
    source_id = f"{namespace}_A{maximum_age}_{role}_{source_index:04d}"
    source_seed = keyed_seed("early-lake-source-v1", namespace, maximum_age, role, source_index)
    rng = np.random.default_rng(source_seed)

    values: dict[str, float] = {}
    forcing_rows = _forcing_rows_from_path(forcing_path)
    bounds: dict[str, float] = {}
    for row in forcing_rows:
        parameter_id = row["parameter_id"]
        bounds[parameter_id] = float(row["upper_bound"])
        if parameter_id not in _EFFECTS and parameter_id != "PR032":
            values[parameter_id] = _sample_estimated_parameter(row, rng)[0]

    # These are the same ordered forcing pair and effect-mask conventions used
    # by age_sources.  There is no retry of the completed source.
    for _ in range(10000):
        t_l = float(rng.uniform(0.0, bounds["PR020"]))
        t_r = float(rng.uniform(0.0, bounds["PR021"]))
        if t_l >= t_r:
            values["PR020"], values["PR021"] = t_l, t_r
            break
    else:
        raise RuntimeError("ordered forcing-pair sampler failed")
    for parameter_id in ("PR027", "PR028", "PR033"):
        values[parameter_id] = float(rng.uniform(0.0, bounds[parameter_id]))
    # Consume one common quality unit in both regimes.  Engineering is the
    # prescribed log-uniform law; neutral fixes the same unit's output at one.
    quality_unit = float(rng.uniform())
    values["PR032"] = 1.0 if quality_regime == "neutral" else float(np.exp(
        math.log(0.7) + quality_unit * (math.log(1.8) - math.log(0.7))))

    age = int(maximum_age)
    s0 = _uniform(rng, support, "s0_uniform")
    s1 = _uniform(rng, support, "s1_uniform")
    s2plus = _uniform(rng, support, "s2plus_uniform")
    m2 = _uniform(rng, support, "breeding_age2_uniform")
    p = float(rng.uniform(0.35, 0.90))
    r_lo, r_hi = (float(x) for x in support["R0_log_uniform"])
    boundary = 1.0 / (1.0 - p)
    if source_index % 2 == 0:
        r_hi = min(r_hi, boundary * (1.0 - 1e-12))
        stratum = "below_one"
    else:
        r_lo = max(r_lo, boundary * (1.0 + 1e-12))
        stratum = "above_one"
    if r_lo >= r_hi:
        raise RuntimeError("balanced refuge-index support is empty")
    r0 = float(np.exp(rng.uniform(math.log(r_lo), math.log(r_hi))))
    proto = AgeDemography(
        (s0, s1) + (s2plus,) * (age - 2),
        (0.0, 0.0, m2) + (1.0,) * (age - 2),
        recruits_per_female=1.0,
        lake_settlement=p,
    )
    survivorship = np.cumprod([1.0, *proto.annual_survival])
    B = math.fsum(
        survivorship[j - 1] * proto.annual_survival[j - 1] ** proto.spawn_fraction
        * proto.breeding_probability[j]
        for j in range(2, age + 1)
    )
    b = 2.0 * r0 / B
    demo = AgeDemography(
        proto.annual_survival, proto.breeding_probability,
        recruits_per_female=b, lake_settlement=p,
    )
    scales = {
        "pedder_lake": _log_uniform(rng, support, "historical_lake_neutral_age1plus_log_uniform"),
        "pedder_refuge": _log_uniform(rng, support, "historical_refuge_neutral_age1plus_log_uniform"),
    }
    eta_refuge = _log_uniform(rng, support, "post_habitat_refuge_fraction_log_uniform")
    recruitment_sigma = _uniform(rng, support, "recruitment_sigma_uniform")
    result: dict[str, Any] = {
        "source_id": source_id,
        "source_seed": source_seed,
        "namespace": namespace,
        "role": role,
        "source_index": source_index,
        "maximum_age": age,
        "quality_regime": quality_regime,
        "quality_unit": quality_unit,
        "demography": asdict(demo),
        "forcing_values": values,
        "scales": scales,
        "eta_refuge": eta_refuge,
        "recruitment_sigma": recruitment_sigma,
        "R0": r0,
        "refuge_index": r0 * (1.0 - p),
        "index_stratum": stratum,
        "feasible": True,
        "failure_reason": "",
    }
    try:
        if b > float(support["derived_b_maximum"]):
            raise ValueError("derived effective recruitment exceeds declared bound")
        neutral_equilibrium_from_abundance(demo, scales["pedder_lake"], scales["pedder_refuge"])
    except (ValueError, TypeError, OverflowError) as exc:
        result["feasible"] = False
        result["failure_reason"] = str(exc)
    return result


def _source_demography(source: Mapping[str, Any]) -> AgeDemography:
    demo = source.get("demography")
    if not isinstance(demo, Mapping):
        raise ValueError("source is missing demography")
    return AgeDemography(**demo)


def run_early_lake_history(
    source: Mapping[str, Any],
    *,
    restriction: str,
    seed: int | None = None,
    replicate: int = 0,
    stochastic: bool = True,
) -> dict[str, Any]:
    """Run one Pedder-only history from 1965 through 1989 inclusive."""
    source_record = dict(source)
    source_id = str(source_record.get("source_id", "unknown"))
    result: dict[str, Any] = {
        "status": "failed", "valid": False, "source": source_record,
        "restriction": restriction, "annual_states": {}, "process_diagnostics": {},
        "lake_exposures": np.zeros((8, 2), dtype=float), "advance_calls": 0,
        "failure_reason": None,
        "metadata": {
            "start_year": EARLY_START_YEAR, "end_year": EARLY_END_YEAR,
            "annual_advances_required": 25, "no_events": True, "site_id": "pedder",
            "source_id": source_id,
        },
    }
    try:
        if restriction not in RESTRICTIONS:
            raise ValueError(f"restriction must be one of {RESTRICTIONS}")
        process_seed = int(seed) if seed is not None else keyed_seed(
            "early-lake-process-v1", source_record.get("namespace", ""), source_id, replicate,
        )
        if process_seed < 0:
            raise ValueError("seed must be nonnegative")
        result["seed"] = process_seed
        result["metadata"].update({"replicate": int(replicate), "quality_regime": source_record.get("quality_regime")})
        if not bool(source_record.get("feasible", True)):
            result["status"] = "algebraically_infeasible"
            raise ValueError(str(source_record.get("failure_reason") or "source marked infeasible"))
        demography = _source_demography(source_record)
        scales = source_record.get("scales")
        if not isinstance(scales, Mapping) or set(scales) != {"pedder_lake", "pedder_refuge"}:
            raise ValueError("early source scales must contain only pedder_lake and pedder_refuge")
        params = _Parameters(source_record["forcing_values"])
        equilibrium = neutral_equilibrium_from_abundance(
            demography, float(scales["pedder_lake"]), float(scales["pedder_refuge"]),
        )
        neutral_state = np.asarray(equilibrium["state"], dtype=float)
        state = np.floor(neutral_state + 0.5)
        result["initial_neutral_state"] = neutral_state.copy()
        result["initial_rounded_state"] = state.copy()
        result["initial_rounding_vector"] = state - neutral_state
        rows = _forcing_rows(params, EARLY_START_YEAR - 1, EARLY_END_YEAR, overshoot_removed=False)
        for year in range(EARLY_START_YEAR, EARLY_END_YEAR + 1):
            current = rows[year]
            previous = rows[year - 1]
            conditions = conditions_from_forcing(
                demography, params, current, previous, restriction,
                post_habitat_refuge_fraction=float(source_record.get("eta_refuge", 1.0)),
                recruitment_sigma=float(source_record.get("recruitment_sigma", 0.0)),
            )
            state, diagnostics = advance(
                state, demography, equilibrium["limits"], conditions=conditions,
                seed=process_seed, year=year, site_id="pedder", stochastic=stochastic,
            )
            result["advance_calls"] += 1
            result["annual_states"][year] = state.copy()
            result["process_diagnostics"][year] = {
                "pre_spawn_females": float(diagnostics["pre_spawn_females"]),
                "pre_spawn_males": float(diagnostics["pre_spawn_males"]),
                "breeding_gate": bool(diagnostics["breeding_gate"]),
                "age1plus_total": float(diagnostics["age1plus_total"]),
                "age1plus_by_compartment": np.asarray(diagnostics["age1plus_by_compartment"]).copy(),
                "surviving_newborns": np.asarray(diagnostics["surviving_newborns"]).copy(),
                "ageout_total": float(diagnostics["ageout_total"]),
            }
        result["forcing"] = rows
        result["lake_exposures"] = np.asarray([
            (result["annual_states"][year][0, :, 0].sum(), result["annual_states"][year][0, :, 1].sum())
            for year in LAKE_YEARS
        ], dtype=float)
        result["status"] = "valid"
        result["valid"] = True
    except (KeyError, TypeError, ValueError, OverflowError, RuntimeError) as exc:
        result["failure_reason"] = str(exc)
        # A source failure is retained as-is.  There is no redraw or fallback.
        if result["annual_states"]:
            result["lake_exposures"] = np.asarray([
                (result["annual_states"][year][0, :, 0].sum(), result["annual_states"][year][0, :, 1].sum())
                if year in result["annual_states"] else (0.0, 0.0)
                for year in LAKE_YEARS
            ], dtype=float)
    return result


def _observation_seed(
    *, seed: int | None, namespace: str, role: str, source_id: str,
    replicate: int, profile: str,
) -> int:
    if seed is not None:
        return int(seed)
    return keyed_seed("early-lake-observation-v1", namespace, role, source_id, replicate, profile)


def generate_lake_observation(
    exposures: Any,
    *,
    expected_total: float = LAKE_EXPECTED_TOTAL,
    generator: str = "poisson",
    age1_weight: float = LAKE_AGE1_WEIGHT,
    rho_L: float = LAKE_RHO,
    seed: int | None = None,
    namespace: str = "early-lake-observation",
    role: str = "test",
    source_id: str = "",
    replicate: int = 0,
    profile: str = "base",
    age1: float | None = None,
    gamma_quality: bool = False,
) -> dict[str, Any]:
    """Generate one 12-site-per-visit Lake observation data set.

    ``raw_site_counts`` are integer site observations.  ``visit_means`` retain
    their corresponding per-site means after the declared digitisation
    perturbation.  All-zero exposure is a valid all-zero observation.
    """
    raw_exposure = np.asarray(exposures, dtype=float)
    if raw_exposure.shape != (8, 2) or not np.all(np.isfinite(raw_exposure)) or np.any(raw_exposure < 0):
        raise ValueError("exposures must be a finite nonnegative (8, 2) array")
    expected_total = float(expected_total)
    if not math.isfinite(expected_total) or expected_total <= 0:
        raise ValueError("expected_total must be finite and positive")
    if age1 is not None:
        age1_weight = float(age1)
    if gamma_quality:
        generator = "gamma1"
    if generator not in ("poisson", "gamma1"):
        raise ValueError("generator must be poisson or gamma1")
    age1_weight, rho_L = float(age1_weight), float(rho_L)
    if not 0 <= age1_weight <= 1:
        raise ValueError("age1_weight must be in [0, 1]")
    if rho_L != 1.0:
        raise ValueError("only rho_L=1 is qualified for the early-Lake generator")
    process_seed = _observation_seed(
        seed=seed, namespace=namespace, role=role, source_id=source_id,
        replicate=replicate, profile=profile,
    )
    if process_seed < 0:
        raise ValueError("seed must be nonnegative")
    rng = np.random.default_rng(process_seed)
    exposure = raw_exposure[:, 0] + age1_weight * raw_exposure[:, 1]
    if not np.any(exposure > 0):
        zeros = np.zeros((8, LAKE_SITES), dtype=int)
        return {
            "status": "valid", "raw_site_counts": zeros, "site_counts": zeros.copy(),
            "visit_means": np.zeros(8), "means": np.zeros(8), "lake_features": np.zeros(8),
            "exposure": exposure, "expected_visit_counts": np.zeros(8),
            "expected_total": expected_total,
            "generator": generator, "seed": process_seed, "rho_L": rho_L,
            "age1_weight": age1_weight, "all_zero_exposure": True,
            "digitisation_half_width": LAKE_DIGITISATION_HALF_WIDTH,
        }
    normalized = exposure / float(exposure.sum())
    expected_visit_counts = expected_total * normalized
    site_rate = expected_visit_counts[:, None] / LAKE_SITES
    if generator == "gamma1":
        quality = rng.gamma(shape=1.0, scale=1.0, size=(8, LAKE_SITES))
        lambdas = site_rate * quality
    else:
        quality = np.ones((8, LAKE_SITES), dtype=float)
        lambdas = np.broadcast_to(site_rate, (8, LAKE_SITES))
    raw_site_counts = rng.poisson(lambdas).astype(int)
    raw_visit_means = raw_site_counts.mean(axis=1).astype(float)
    digitised_means = raw_visit_means.copy()
    positive = raw_visit_means > 0
    digitised_means[positive] = np.maximum(
        0.0, digitised_means[positive] + rng.uniform(-LAKE_DIGITISATION_HALF_WIDTH,
                                                        LAKE_DIGITISATION_HALF_WIDTH,
                                                        int(positive.sum()))
    )
    return {
        "status": "valid", "raw_site_counts": raw_site_counts,
        "site_counts": raw_site_counts.copy(), "visit_means": digitised_means,
        "means": digitised_means.copy(), "lake_features": digitised_means.copy(),
        "raw_visit_means": raw_visit_means,
        "exposure": exposure, "normalized_exposure": normalized,
        "expected_visit_counts": expected_visit_counts, "expected_total": expected_total,
        "site_trip_quality": quality, "generator": generator, "seed": process_seed,
        "rho_L": rho_L, "age1_weight": age1_weight, "all_zero_exposure": False,
        "digitisation_half_width": LAKE_DIGITISATION_HALF_WIDTH,
    }


def make_early_source(
    maximum_age: int,
    source_index: int,
    *,
    role: str,
    namespace: str,
    quality_regime: str = "neutral",
    design: Mapping[str, Any] | str | Path | None = None,
    forcing_path: str | Path = DEFAULT_FORCING,
) -> dict[str, Any]:
    """Short public name for :func:`make_early_lake_source`."""
    return make_early_lake_source(
        maximum_age, source_index, role=role, namespace=namespace,
        quality_regime=quality_regime, design=design, forcing_path=forcing_path,
    )


def run_early_history(
    source: Mapping[str, Any],
    restriction: str,
    replicate: int = 0,
    *,
    namespace: str | None = None,
    stochastic: bool = True,
) -> dict[str, Any]:
    """Short public runner contract used by the early-Lake driver."""
    run_namespace = source.get("namespace", "") if namespace is None else namespace
    process_seed = keyed_seed("early-lake-process-v1", run_namespace, source.get("source_id", ""), replicate)
    result = run_early_lake_history(
        source, restriction=restriction, replicate=replicate,
        seed=process_seed,
        stochastic=stochastic,
    )
    result["source_id"] = source.get("source_id")
    result["restriction"] = restriction
    result["replicate"] = replicate
    result["lake_features"] = result["lake_exposures"]
    result["diagnostics"] = result["process_diagnostics"]
    return result


def generate_lake_observation_profile(
    features: Any,
    *,
    seed: int,
    age1: float = 0.0,
    gamma_quality: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Compact profile API using the method-study names."""
    return generate_lake_observation(
        features, seed=seed, age1_weight=age1,
        generator="gamma1" if gamma_quality else "poisson", **kwargs,
    )


__all__ = [
    "EARLY_START_YEAR", "EARLY_END_YEAR", "LAKE_YEARS", "LAKE_EXPECTED_TOTAL",
    "keyed_seed", "make_early_lake_source", "run_early_lake_history",
    "make_early_source", "run_early_history", "generate_lake_observation",
    "generate_lake_observation_profile",
]
