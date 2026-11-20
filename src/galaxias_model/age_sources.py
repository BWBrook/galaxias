"""Prospective, source-separated parameter worlds for age-model recovery.

The balanced refuge-index design is an engineering sampling distribution, not
an empirical prior. Infeasible allocations retain their IDs without redraws.
"""
from __future__ import annotations

import csv
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from galaxias_model.age_demography import AgeDemography, neutral_equilibrium_from_abundance
from galaxias_model.common_model import _ParameterValues
from galaxias_model.sampling import _sample_estimated_parameter


ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "data/age_structured_design_20260929/scenarios.json"
FORCING = ROOT / "data/age_linked_recovery_20261001/retained_forcing_parameters.csv"
EFFECTS = ("PR020", "PR021", "PR027", "PR028", "PR033")


def keyed_seed(*parts, bits: int = 32) -> int:
    """Stable namespaces; no process-dependent Python hash or seed arithmetic."""
    if bits not in (32, 128):
        raise ValueError("seed width must be 32 or 128 bits")
    payload = json.dumps(parts, separators=(",", ":"), sort_keys=True).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:bits // 8], "little")


def source_group(cell: dict) -> str:
    # Nuisance worlds are paired across restrictions and removal accounts.
    return f"A{cell['maximum_age']}_{cell['nursery']}"


def cell_id(cell: dict) -> str:
    return f"{source_group(cell)}_{cell['removal_account']}_{cell['restriction']}"


def make_source(cell: dict, index: int, *, namespace: str,
                design: dict | None = None, forcing_path: Path = FORCING) -> dict:
    if index < 0 or not namespace:
        raise ValueError("source index and namespace are required")
    design = json.loads(DESIGN.read_text()) if design is None else design
    seed = keyed_seed("age-recovery-20261001", namespace, source_group(cell), index)
    rng = np.random.default_rng(seed)
    with forcing_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    values = {}
    for row in rows:
        pid = row["parameter_id"]
        if pid not in EFFECTS:
            values[pid] = _sample_estimated_parameter(row, rng)[0]
    bounds = {row["parameter_id"]: float(row["upper_bound"]) for row in rows}
    # Jointly truncated pair as in the common protocol; no demographic source
    # is retried after it has been generated.
    for _ in range(10000):
        t_l = float(rng.uniform(0, bounds["PR020"]))
        t_r = float(rng.uniform(0, bounds["PR021"]))
        if t_l >= t_r:
            values.update(PR020=t_l, PR021=t_r)
            break
    else:
        raise RuntimeError("ordered forcing-pair sampler failed")
    for pid in ("PR027", "PR028", "PR033"):
        values[pid] = float(rng.uniform(0, bounds[pid]))
    support = design["search_bounds_not_empirical_priors"]
    def uniform(name):
        return float(rng.uniform(*support[name]))
    def log_uniform(name):
        lo, hi = support[name]
        return float(np.exp(rng.uniform(math.log(lo), math.log(hi))))
    age = int(cell["maximum_age"])
    s0, s1, sa = [uniform(n) for n in ("s0_uniform", "s1_uniform", "s2plus_uniform")]
    m2 = uniform("breeding_age2_uniform")
    p_lo, p_hi = design["nursery_allocation"][cell["nursery"]]
    r_lo, r_hi = support["R0_log_uniform"]
    isolated_above_one = bool(index % 2)
    if isolated_above_one:
        p_hi = min(p_hi, 1 - 1/r_hi)
    p = float(rng.uniform(p_lo, p_hi))
    r_boundary = 1/(1-p)
    if isolated_above_one:
        r_lo = max(r_lo, r_boundary)
    else:
        r_hi = min(r_hi, r_boundary)
    r0 = float(np.exp(rng.uniform(math.log(r_lo), math.log(r_hi))))
    proto = AgeDemography((s0, s1)+(sa,)*(age-2), (0, 0, m2)+(1,)*(age-2),
                          recruits_per_female=1, lake_settlement=p)
    survivorship = np.cumprod([1., *proto.annual_survival])
    B = math.fsum(survivorship[j-1]*proto.annual_survival[j-1]**proto.spawn_fraction
                  * proto.breeding_probability[j] for j in range(2, age+1))
    b = 2*r0/B
    demo = AgeDemography(proto.annual_survival, proto.breeding_probability,
                         recruits_per_female=b, lake_settlement=p)
    scales = {key: log_uniform(bound) for key, bound in (
        ("pedder_lake", "historical_lake_neutral_age1plus_log_uniform"),
        ("pedder_refuge", "historical_refuge_neutral_age1plus_log_uniform"),
        ("oberon", "oberon_neutral_age1plus_log_uniform"),
        ("strathgordon", "strathgordon_neutral_age1plus_log_uniform"))}
    result = {
        "source_id": f"{namespace}_{source_group(cell)}_{index:04d}",
        "namespace": namespace, "source_seed": seed, "index": index,
        "cell": cell, "demography": asdict(demo), "forcing_values": values,
        "scales": scales, "R0": r0, "refuge_index": r0*(1-p),
        "index_stratum": "above_one" if isolated_above_one else "below_one",
        "eta_refuge": log_uniform("post_habitat_refuge_fraction_log_uniform"),
        "recruitment_sigma": uniform("recruitment_sigma_uniform"),
        "strath_pre2007": log_uniform("strathgordon_spawn_multiplier_before_2007_log_uniform"),
        "ledger_timing": "late" if (index//2)%2 else "early",
        "march_retention": bool((index//4)%2),
        "feasible": True, "failure_reason": "",
    }
    try:
        if b > support["derived_b_maximum"]:
            raise ValueError("derived effective recruitment exceeds declared bound")
        neutral_equilibrium_from_abundance(demo, scales["pedder_lake"], scales["pedder_refuge"])
        for site in ("oberon", "strathgordon"):
            neutral_equilibrium_from_abundance(demo, p*scales[site], (1-p)*scales[site])
    except ValueError as exc:
        result.update(feasible=False, failure_reason=str(exc))
    return result


def runner_arguments(source: dict, replicate: int, *, run_namespace: str) -> dict:
    """Keep process seeds independent of truth/bank parameter and observation seeds."""
    return dict(
        demography=AgeDemography(**source["demography"]),
        params=_ParameterValues(source["forcing_values"]), scales=source["scales"],
        restriction=source["cell"]["restriction"],
        eta_refuge=source["eta_refuge"], recruitment_sigma=source["recruitment_sigma"],
        strath_pre2007=source["strath_pre2007"],
        seed=keyed_seed("age-process", run_namespace, source["source_id"], replicate),
        ledger_timing=source["ledger_timing"], march_retention=source["march_retention"],
        removal_account=source["cell"]["removal_account"],
    )
