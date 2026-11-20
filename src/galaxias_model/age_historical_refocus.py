"""Small, defensive helpers for the provisional historical refocus.

This module contains no demographic simulation.  The proposal is a bounded
importance sampler over the already-defined source coordinates; the Lake
score and endpoint projection are pure functions of their explicit inputs.
In particular, fitting never inspects terminal labels or chooses a source by
its terminal outcome.
"""
from __future__ import annotations

from collections.abc import Mapping
import copy
import csv
from pathlib import Path
import json
import math
from typing import Any

import numpy as np

from galaxias_model.age_demography import AgeDemography, neutral_equilibrium_from_abundance
from galaxias_model.age_sources import DESIGN, FORCING


UNIT_NAMES = (
    "s0", "s1", "sa", "m2", "p", "conditional_log_R0", "log_eta", "sigma",
    "logscalePedderLake", "logscalePedderRefuge", "logOberon", "logStrath",
    "logStrathPre", "PR027", "PR028", "PR033",
)
UNIT_DIMENSION = len(UNIT_NAMES)

# These are part of the provisional proposal contract.  Keep them named so a
# receipt can record the proposal geometry without relying on source code text.
HISTOGRAM_BIN_COUNT = 4
HISTOGRAM_SHRINKAGE = 0.20
BASE_MIXTURE_WEIGHT = 0.50
HISTOGRAM_MIXTURE_WEIGHT = 0.50
PROPOSAL_METADATA = {
    "kind": "bounded_defensive_importance_sampler",
    "bin_count": HISTOGRAM_BIN_COUNT,
    "histogram_shrinkage": HISTOGRAM_SHRINKAGE,
    "base_uniform_mixture_weight": BASE_MIXTURE_WEIGHT,
    "histogram_mixture_weight": HISTOGRAM_MIXTURE_WEIGHT,
    "unit_dimension": UNIT_DIMENSION,
}


def _finite_array(name: str, value: Any, *, shape: tuple[int, ...] | None = None,
                  nonnegative: bool = False) -> np.ndarray:
    raw = np.asarray(value)
    if raw.dtype.kind not in "biuf":
        raise ValueError(f"{name} must contain numeric values")
    array = raw.astype(float)
    if shape is not None and array.shape != shape:
        raise ValueError(f"{name} must have shape {shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    if nonnegative and np.any(array < 0):
        raise ValueError(f"{name} must be nonnegative")
    return array


def lake_history_log_score(
    lake_features: Any,
    means: Any,
    *,
    power: float = 1.0 / 12.0,
    rho: float = 1.0,
    age1: float = 0.0,
) -> float | np.ndarray:
    """Score Lake's eight trips by their saturated relative composition.

    ``lake_features`` is one ``(8, 2)`` array or an ``(N, 8, 2)`` array.  The
    first column is age zero and the second is age one only. ``means`` is the
    supplied eight-trip digitised mean vector; it is intentionally required as
    an argument so this helper cannot silently load a primary observation.
    Zero entries remain in the eight-trip composition.  A positive observed
    count with zero model exposure is impossible and receives ``-inf``.
    """
    raw = _finite_array("lake_features", lake_features, nonnegative=True)
    scalar = raw.ndim == 2
    if scalar:
        if raw.shape != (8, 2):
            raise ValueError("lake_features must have shape (8, 2) or (N, 8, 2)")
        features = raw[None, ...]
    elif raw.ndim == 3 and raw.shape[1:] == (8, 2):
        features = raw
    else:
        raise ValueError("lake_features must have shape (8, 2) or (N, 8, 2)")
    observed = _finite_array("means", means, shape=(8,), nonnegative=True)
    power = float(power)
    rho = float(rho)
    age1 = float(age1)
    if not math.isfinite(power) or not 0 < power <= 1:
        raise ValueError("power must be finite and in (0, 1]")
    if not math.isfinite(rho) or rho < 0:
        raise ValueError("rho must be finite and nonnegative")
    if not math.isfinite(age1) or not 0 <= age1 <= 1:
        raise ValueError("age1 must be finite and in [0, 1]")

    exposure = features[:, :, 0] + age1 * features[:, :, 1]
    exposure = exposure.copy()
    exposure[:, 5:] *= rho
    counts = 12.0 * observed
    count_total = float(np.sum(counts))
    result = np.zeros(features.shape[0], dtype=float)
    if count_total > 0:
        positive_counts = counts > 0
        for row, x in enumerate(exposure):
            x_total = float(np.sum(x))
            if x_total <= 0 or np.any(positive_counts & (x <= 0)):
                result[row] = -math.inf
                continue
            # Computing the ratio after normalising both vectors avoids a
            # scale-dependent score and retains the zero-count bins.
            p = x / x_total
            q = counts / count_total
            result[row] = power * math.fsum(
                float(c) * math.log(float(pi / qi))
                for c, pi, qi in zip(counts, p, q)
                if c > 0
            )
            # The expression is nonpositive by Gibbs' inequality.  Rounding
            # can make a near-zero result positive on some BLAS/libm builds.
            if result[row] > 0:
                result[row] = 0.0
    return float(result[0]) if scalar else result


def _load_design(design: Mapping[str, Any] | None) -> dict[str, Any]:
    return json.loads(DESIGN.read_text()) if design is None else copy.deepcopy(dict(design))


def _forcing_bounds(forcingbounds: Any | None) -> dict[str, float]:
    if forcingbounds is None:
        with Path(FORCING).open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        return {str(row["parameter_id"]): float(row["upper_bound"]) for row in rows}
    if isinstance(forcingbounds, (str, Path)):
        with Path(forcingbounds).open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        return {str(row["parameter_id"]): float(row["upper_bound"]) for row in rows}
    if isinstance(forcingbounds, Mapping):
        result = {}
        for key, value in forcingbounds.items():
            if isinstance(value, Mapping):
                value = value.get("upper_bound", value.get("bound"))
            result[str(key)] = float(value)
        return result
    result = {}
    for row in forcingbounds:
        if isinstance(row, Mapping):
            key = row.get("parameter_id")
            value = row.get("upper_bound", row.get("bound"))
            if key is None or value is None:
                raise ValueError("forcingbounds rows need parameter_id and upper_bound")
            result[str(key)] = float(value)
        else:
            raise ValueError("forcingbounds must be a mapping, path, or rows")
    return result


def _support(design: Mapping[str, Any]) -> Mapping[str, Any]:
    try:
        return design["search_bounds_not_empirical_priors"]
    except KeyError as exc:
        raise ValueError("design lacks search_bounds_not_empirical_priors") from exc


def _interval(support: Mapping[str, Any], name: str) -> tuple[float, float]:
    value = support[name]
    if len(value) != 2:
        raise ValueError(f"support interval {name} must have two endpoints")
    lo, hi = map(float, value)
    if not math.isfinite(lo) or not math.isfinite(hi) or lo <= 0 or hi < lo:
        raise ValueError(f"support interval {name} is invalid")
    return lo, hi


def _stratum(source: Mapping[str, Any]) -> str:
    try:
        index = int(source["index"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("source index is required for the refuge-index stratum") from exc
    if index < 0:
        raise ValueError("source index must be nonnegative")
    return "above_one" if index % 2 else "below_one"


def _p_interval(source: Mapping[str, Any], design: Mapping[str, Any], support: Mapping[str, Any],
                stratum: str) -> tuple[float, float]:
    try:
        nursery = source["cell"]["nursery"]
        p_lo, p_hi = map(float, design["nursery_allocation"][nursery])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("source cell and design nursery allocation are required") from exc
    r_lo, r_hi = _interval(support, "R0_log_uniform")
    if stratum == "above_one":
        p_hi = min(p_hi, 1.0 - 1.0 / r_hi)
    if not 0 <= p_lo < p_hi <= 1:
        raise ValueError("conditional p interval is empty")
    return p_lo, p_hi


def _conditional_r_interval(p: float, support: Mapping[str, Any], stratum: str) -> tuple[float, float]:
    lo, hi = _interval(support, "R0_log_uniform")
    boundary = 1.0 / (1.0 - p)
    if stratum == "above_one":
        lo = max(lo, boundary)
    else:
        hi = min(hi, boundary)
    if lo > hi * (1 + 1e-12):
        raise ValueError("conditional R0 interval is empty")
    return lo, hi


def _unit_fraction(value: float, lo: float, hi: float, *, logarithmic: bool = False) -> float:
    value, lo, hi = float(value), float(lo), float(hi)
    if hi == lo:
        if not math.isclose(value, lo, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("value lies outside a degenerate support interval")
        return 0.5
    if not lo <= value <= hi:
        raise ValueError("source value lies outside its declared support")
    if logarithmic:
        return (math.log(value) - math.log(lo)) / (math.log(hi) - math.log(lo))
    return (value - lo) / (hi - lo)


def _demography_values(source: Mapping[str, Any]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    try:
        demo = source["demography"]
        survival = tuple(float(x) for x in demo["annual_survival"])
        maturity = tuple(float(x) for x in demo["breeding_probability"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("source demography is required") from exc
    if len(survival) < 2 or len(maturity) != len(survival) + 1:
        raise ValueError("source demography has inconsistent age lengths")
    return survival, maturity


def source_to_unit(source: Mapping[str, Any], design: Mapping[str, Any] | None = None,
                   forcingbounds: Any | None = None) -> np.ndarray:
    """Map a generated source into the fixed 16-dimensional unit cube."""
    design = _load_design(design)
    support = _support(design)
    bounds = _forcing_bounds(forcingbounds)
    survival, maturity = _demography_values(source)
    stratum = _stratum(source)
    p_lo, p_hi = _p_interval(source, design, support, stratum)
    p = float(source["demography"]["lake_settlement"])
    r_lo, r_hi = _conditional_r_interval(p, support, stratum)
    scales = source.get("scales", {})
    def log_scale(key: str, bound: str) -> float:
        lo, hi = _interval(support, bound)
        return _unit_fraction(float(scales[key]), lo, hi, logarithmic=True)
    def force(name: str) -> float:
        bound = float(bounds[name])
        if not math.isfinite(bound) or bound <= 0:
            raise ValueError(f"forcing bound {name} must be positive")
        return _unit_fraction(float(source["forcing_values"][name]), 0.0, bound)
    values = (
        _unit_fraction(survival[0], *_interval(support, "s0_uniform")),
        _unit_fraction(survival[1], *_interval(support, "s1_uniform")),
        _unit_fraction(survival[2], *_interval(support, "s2plus_uniform")),
        _unit_fraction(maturity[2], *_interval(support, "breeding_age2_uniform")),
        _unit_fraction(p, p_lo, p_hi),
        _unit_fraction(float(source["R0"]), r_lo, r_hi, logarithmic=True),
        _unit_fraction(float(source["eta_refuge"]), *_interval(support, "post_habitat_refuge_fraction_log_uniform"), logarithmic=True),
        _unit_fraction(float(source["recruitment_sigma"]), *_interval(support, "recruitment_sigma_uniform")),
        log_scale("pedder_lake", "historical_lake_neutral_age1plus_log_uniform"),
        log_scale("pedder_refuge", "historical_refuge_neutral_age1plus_log_uniform"),
        log_scale("oberon", "oberon_neutral_age1plus_log_uniform"),
        log_scale("strathgordon", "strathgordon_neutral_age1plus_log_uniform"),
        _unit_fraction(float(source["strath_pre2007"]), *_interval(support, "strathgordon_spawn_multiplier_before_2007_log_uniform"), logarithmic=True),
        force("PR027"), force("PR028"), force("PR033"),
    )
    result = np.asarray(values, dtype=float)
    if result.shape != (UNIT_DIMENSION,) or np.any(~np.isfinite(result)) or np.any((result < 0) | (result > 1)):
        raise ValueError("source does not map to the unit cube")
    return result


def _coerce_unit(unit: Any) -> np.ndarray:
    if isinstance(unit, Mapping):
        try:
            result = np.asarray([unit[name] for name in UNIT_NAMES], dtype=float)
        except KeyError as exc:
            raise ValueError(f"unit mapping lacks {exc.args[0]}") from exc
    else:
        result = np.asarray(unit, dtype=float)
    if result.shape != (UNIT_DIMENSION,) or not np.all(np.isfinite(result)) or np.any((result < 0) | (result > 1)):
        raise ValueError(f"unit must be a finite vector of {UNIT_DIMENSION} values in [0, 1]")
    return result


def _make_demography(source: Mapping[str, Any], s0: float, s1: float, sa: float,
                     m2: float, p: float, r0: float) -> tuple[AgeDemography, float]:
    old_survival, _ = _demography_values(source)
    age = len(old_survival)
    survival = (s0, s1) + (sa,) * (age - 2)
    maturity = (0.0, 0.0, m2) + (1.0,) * (age - 2)
    proto = AgeDemography(survival, maturity, recruits_per_female=1.0, lake_settlement=p)
    survivorship = np.cumprod([1.0, *proto.annual_survival])
    B = math.fsum(
        survivorship[j - 1] * proto.annual_survival[j - 1] ** proto.spawn_fraction
        * proto.breeding_probability[j]
        for j in range(2, age + 1)
    )
    if not math.isfinite(B) or B <= 0:
        raise ValueError("demography has no positive recruitment contribution")
    b = 2.0 * r0 / B
    return AgeDemography(survival, maturity, recruits_per_female=b, lake_settlement=p), b


def source_with_unit(source: Mapping[str, Any], unit: Any,
                     design: Mapping[str, Any] | None = None,
                     forcingbounds: Any | None = None) -> dict[str, Any]:
    """Return a deep-copied source with only the chosen coordinates changed.

    Conditional support failures and neutral-equilibrium failures are retained
    on the returned source as ``feasible=False``; no redraw or source identity
    change occurs.
    """
    design = _load_design(design)
    support = _support(design)
    bounds = _forcing_bounds(forcingbounds)
    u = _coerce_unit(unit)
    result = copy.deepcopy(dict(source))
    # Feasibility belongs to the transformed proposal.  An infeasible source
    # used as training geometry can therefore yield a feasible transformed
    # draw; if the draw fails, its failure is retained below without redraw.
    result["feasible"] = True
    result["failure_reason"] = ""
    stratum = _stratum(source)
    p_lo, p_hi = _p_interval(source, design, support, stratum)
    p = p_lo + u[4] * (p_hi - p_lo)
    r_lo, r_hi = _conditional_r_interval(p, support, stratum)
    r0 = math.exp(math.log(r_lo) + u[5] * (math.log(r_hi) - math.log(r_lo)))
    def log_value(name: str, bound: str) -> float:
        lo, hi = _interval(support, bound)
        return math.exp(math.log(lo) + u[UNIT_NAMES.index(name)] * (math.log(hi) - math.log(lo)))
    def linear_value(name: str, bound: float) -> float:
        return u[UNIT_NAMES.index(name)] * bound

    def linear_support(unit_index: int, name: str) -> float:
        lo, hi = _interval(support, name)
        return lo + u[unit_index] * (hi - lo)
    try:
        demo, b = _make_demography(
            source,
            linear_support(0, "s0_uniform"),
            linear_support(1, "s1_uniform"),
            linear_support(2, "s2plus_uniform"),
            linear_support(3, "breeding_age2_uniform"),
            p,
            r0,
        )
    except (ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
        demo, b = None, math.nan
        result["feasible"] = False
        result["failure_reason"] = str(exc)
    if demo is not None:
        result["demography"] = {
            "annual_survival": tuple(demo.annual_survival),
            "breeding_probability": tuple(demo.breeding_probability),
            "recruits_per_female": float(demo.recruits_per_female),
            "lake_settlement": float(demo.lake_settlement),
            "spawn_fraction": float(demo.spawn_fraction),
            "female_fraction": float(demo.female_fraction),
            "b": None,
        }
    result["R0"] = float(r0)
    result["refuge_index"] = float(r0 * (1.0 - p))
    result["index_stratum"] = stratum
    result["eta_refuge"] = log_value("log_eta", "post_habitat_refuge_fraction_log_uniform")
    result["recruitment_sigma"] = u[7] * (_interval(support, "recruitment_sigma_uniform")[1] - _interval(support, "recruitment_sigma_uniform")[0]) + _interval(support, "recruitment_sigma_uniform")[0]
    result["strath_pre2007"] = log_value("logStrathPre", "strathgordon_spawn_multiplier_before_2007_log_uniform")
    scales = dict(result.get("scales", {}))
    for key, unit_name, bound in (
        ("pedder_lake", "logscalePedderLake", "historical_lake_neutral_age1plus_log_uniform"),
        ("pedder_refuge", "logscalePedderRefuge", "historical_refuge_neutral_age1plus_log_uniform"),
        ("oberon", "logOberon", "oberon_neutral_age1plus_log_uniform"),
        ("strathgordon", "logStrath", "strathgordon_neutral_age1plus_log_uniform"),
    ):
        scales[key] = log_value(unit_name, bound)
    result["scales"] = scales
    forcing = dict(result.get("forcing_values", {}))
    for name in ("PR027", "PR028", "PR033"):
        bound = float(bounds[name])
        if not math.isfinite(bound) or bound <= 0:
            raise ValueError(f"forcing bound {name} must be positive")
        forcing[name] = linear_value(name, bound)
    result["forcing_values"] = forcing
    if b > float(support["derived_b_maximum"]):
        result["feasible"] = False
        result["failure_reason"] = "derived effective recruitment exceeds declared bound"
    elif demo is not None:
        try:
            neutral_equilibrium_from_abundance(demo, scales["pedder_lake"], scales["pedder_refuge"])
            for site in ("oberon", "strathgordon"):
                p_site = p * scales[site]
                neutral_equilibrium_from_abundance(demo, p_site, (1.0 - p) * scales[site])
        except (ValueError, TypeError, OverflowError) as exc:
            result["feasible"] = False
            result["failure_reason"] = str(exc)
    if result.get("feasible", True) and demo is not None:
        result["feasible"] = True
        result["failure_reason"] = ""
    return result


def _unit_rows(value: Any) -> np.ndarray:
    if isinstance(value, np.ndarray):
        rows = np.asarray(value, dtype=float)
    else:
        values = list(value)
        if not values:
            return np.empty((0, UNIT_DIMENSION), dtype=float)
        if values and isinstance(values[0], Mapping):
            rows = np.asarray([_coerce_unit(row.get("unit", row)) for row in values], dtype=float)
        else:
            rows = np.asarray(values, dtype=float)
    if rows.ndim == 1 and rows.size == UNIT_DIMENSION:
        rows = rows[None, :]
    if rows.ndim != 2 or rows.shape[1] != UNIT_DIMENSION:
        raise ValueError(f"unit_rows must have shape (N, {UNIT_DIMENSION})")
    if not np.all(np.isfinite(rows)) or np.any((rows < 0) | (rows > 1)):
        raise ValueError("unit_rows must be finite and lie in [0, 1]")
    return rows


def fit_histogram(unit_rows: Any, weights: Any | None = None) -> dict[str, Any]:
    """Fit four-bin marginal densities from caller-aggregated source weights."""
    rows = _unit_rows(unit_rows)
    if weights is None:
        w = np.ones(rows.shape[0], dtype=float)
    else:
        w = _finite_array("weights", weights, shape=(rows.shape[0],), nonnegative=True)
    total = float(np.sum(w))
    sumsq = float(np.sum(w * w))
    ess = total * total / sumsq if sumsq > 0 else 0.0
    fallback = rows.shape[0] == 0 or total <= 0 or ess <= 0
    probabilities = np.full((UNIT_DIMENSION, HISTOGRAM_BIN_COUNT), 1.0 / HISTOGRAM_BIN_COUNT)
    if not fallback:
        for j in range(UNIT_DIMENSION):
            indices = np.minimum((rows[:, j] * HISTOGRAM_BIN_COUNT).astype(int), HISTOGRAM_BIN_COUNT - 1)
            counts = np.bincount(indices, weights=w, minlength=HISTOGRAM_BIN_COUNT)
            raw = counts / total
            probabilities[j] = (1.0 - HISTOGRAM_SHRINKAGE) * raw + HISTOGRAM_SHRINKAGE / HISTOGRAM_BIN_COUNT
    densities = HISTOGRAM_BIN_COUNT * probabilities
    diagnostic = "uniform_fallback_no_evidence" if fallback else "weighted_four_bin_marginals"
    return {
        "bin_probabilities": probabilities,
        "densities": densities,
        "effective_sample_size": float(ess),
        "total_weight": total,
        "fallback_uniform": bool(fallback),
        "diagnostic": diagnostic,
        "metadata": dict(PROPOSAL_METADATA),
    }


def _fit_probabilities(fit: Mapping[str, Any]) -> np.ndarray:
    probabilities = _finite_array("fit bin_probabilities", fit["bin_probabilities"],
                                  shape=(UNIT_DIMENSION, HISTOGRAM_BIN_COUNT))
    if np.any(probabilities < 0) or not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-12):
        raise ValueError("fit bin probabilities must be nonnegative rows summing to one")
    return probabilities


def proposal_log_density_ratio(fit: Mapping[str, Any], unit: Any) -> float:
    """Return log(q/g), retaining the exact defensive mixture in q."""
    probabilities = _fit_probabilities(fit)
    u = _coerce_unit(unit)
    indices = np.minimum((u * HISTOGRAM_BIN_COUNT).astype(int), HISTOGRAM_BIN_COUNT - 1)
    product_density = float(np.prod(HISTOGRAM_BIN_COUNT * probabilities[np.arange(UNIT_DIMENSION), indices]))
    ratio = BASE_MIXTURE_WEIGHT + HISTOGRAM_MIXTURE_WEIGHT * product_density
    if not math.isfinite(ratio) or ratio < 0.5 - 1e-12 or 1.0 / ratio > 2.0 + 1e-12:
        raise ValueError("defensive proposal density-ratio invariant failed")
    return float(math.log(ratio))


def draw_proposal(fit: Mapping[str, Any], rng: np.random.Generator | None = None) -> tuple[np.ndarray, float, str]:
    """Draw one whole-vector defensive mixture proposal."""
    probabilities = _fit_probabilities(fit)
    rng = np.random.default_rng() if rng is None else rng
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator")
    if float(rng.random()) < BASE_MIXTURE_WEIGHT:
        unit = rng.random(UNIT_DIMENSION)
        component = "base_uniform"
    else:
        bins = np.asarray([rng.choice(HISTOGRAM_BIN_COUNT, p=probabilities[j]) for j in range(UNIT_DIMENSION)])
        unit = (bins + rng.random(UNIT_DIMENSION)) / HISTOGRAM_BIN_COUNT
        component = "independent_histogram_product"
    return unit, proposal_log_density_ratio(fit, unit), component


def _year_value(mapping: Mapping[Any, Any], year: int) -> Any:
    if year in mapping:
        return mapping[year]
    if str(year) in mapping:
        return mapping[str(year)]
    raise KeyError(year)


def _history_state(history: Mapping[str, Any], site: str, year: int) -> np.ndarray:
    annual = history.get("annual_states", {})
    try:
        state = _year_value(annual[site], year)
    except (KeyError, TypeError) as exc:
        raise ValueError(f"history lacks annual state for {site} {year}") from exc
    state = _finite_array(f"{site} {year} state", state, nonnegative=True)
    if state.ndim != 3 or state.shape[:2] != (2, 2) or state.shape[2] < 1:
        raise ValueError("annual state must have shape (2, 2, age)")
    return state


def endpoint_features(history: Mapping[str, Any]) -> dict[str, Any]:
    """Project finite endpoint and breeding diagnostics without viability calls."""
    if not isinstance(history, Mapping):
        raise TypeError("history must be a mapping")
    end = _history_state(history, "pedder", 2002)
    total_by_compartment = end.sum(axis=(1, 2))
    total = float(np.sum(end))
    age1plus = float(np.sum(end[:, :, 1:])) if end.shape[2] > 1 else 0.0
    # Y10 is the declared ten-fish age-1+ endpoint at end-2002, not a
    # post-2002 persistence or viability call.
    y10 = bool(age1plus >= 10.0)
    diagnostics = history.get("per_year_diagnostics", {})
    diag = {}
    if isinstance(diagnostics, Mapping):
        try:
            diag = _year_value(diagnostics.get("pedder", {}), 2002)
        except (KeyError, TypeError):
            diag = {}
    if not isinstance(diag, Mapping):
        raise ValueError("Pedder 2002 diagnostics must be a mapping")
    pooled = np.asarray((diag.get("pre_spawn_females", 0.0), diag.get("pre_spawn_males", 0.0)), dtype=float)
    if not np.all(np.isfinite(pooled)) or np.any(pooled < 0):
        raise ValueError("pre-spawn pooled pair must be finite and nonnegative")
    same = diag.get("pre_spawn_by_compartment_sex")
    if same is None:
        females = diag.get("pre_spawn_females_by_compartment")
        males = diag.get("pre_spawn_males_by_compartment")
        if females is not None and males is not None:
            same = np.column_stack((females, males))
    if same is None:
        raise ValueError(
            "history lacks compartment-specific 2002 pre-spawn diagnostics"
        )
    same = _finite_array("same-compartment pre-spawn pair", same, nonnegative=True)
    if same.shape != (2, 2):
        raise ValueError("same-compartment pre-spawn pair must have shape (2, 2)")
    result = {
        "pedder_total_2002": total,
        "pedder_lake_2002": float(total_by_compartment[0]),
        "pedder_refuge_2002": float(total_by_compartment[1]),
        "pedder_age1plus_2002": age1plus,
        "Yalive": bool(total > 0),
        "Y10": y10,
        "Y0": bool(total > 0),
        "Ypair": bool(pooled[0] >= 1.0 and pooled[1] >= 1.0),
        "Ysame_pair": bool(np.any((same[:, 0] >= 1.0) & (same[:, 1] >= 1.0))),
        "realised_pre_spawn_pair": pooled,
        "realized_pre_spawn_pair": pooled.copy(),
        "same_compartment_pair": same,
    }
    # Compact aliases keep the endpoint contract readable to callers that use
    # lowercase Python names while retaining the protocol's Yalive/Y10 labels.
    result["y_alive"] = result["Yalive"]
    result["y10"] = result["Y10"]
    return result


__all__ = [
    "UNIT_NAMES", "UNIT_DIMENSION", "HISTOGRAM_BIN_COUNT",
    "HISTOGRAM_SHRINKAGE", "BASE_MIXTURE_WEIGHT", "HISTOGRAM_MIXTURE_WEIGHT",
    "PROPOSAL_METADATA", "lake_history_log_score", "source_to_unit", "source_with_unit",
    "fit_histogram", "proposal_log_density_ratio", "draw_proposal", "endpoint_features",
]
