"""Finite analytical/demographic qualification; never searches or scores histories."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd

from galaxias_model import common_model, mate_guard
from galaxias_model.recruitment_demography import Demography, RecruitmentLimits, advance, neutral_equilibrium
from galaxias_model.recruitment_scenarios import (
    STATE_FIELDS, reference_demography, reference_forcing_parameters,
    reference_limits, run_scenario,
)

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 1e-10
MAX_STEPS = 2000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def critical(d: Demography) -> float:
    return (1 - d.adult_survival) * (1 - d.juvenile_survival * (1 - d.maturation)) / (
        d.juvenile_survival * d.maturation
    )


def lambda_zero(d: Demography, limits: RecruitmentLimits) -> float:
    b = d.recruits_per_adult * (
        d.lake_settlement * (limits.lake > 0) + (1 - d.lake_settlement) * (limits.refuge > 0)
    )
    u = d.juvenile_survival * (1 - d.maturation)
    a = d.adult_survival
    return (u + a + math.sqrt((u - a) ** 2 + 4 * b * d.juvenile_survival * d.maturation)) / 2


def grid():
    reference = reference_demography()
    index = 0
    for s, a, m, ratio, ceiling in itertools.product(
        (.15, .35, .60), (.45, .65, .85), (.50, .70, .85), (.5, 1., 1.5, 3., 6.), (15., 150., 1500.)
    ):
        d = replace(reference, juvenile_survival=s, adult_survival=a, maturation=m)
        d = replace(d, recruits_per_adult=ratio * critical(d))
        yield f"grid{index:04d}", "main", d, RecruitmentLimits(.7 * ceiling, .3 * ceiling)
        index += 1
    for p, ceilings in itertools.product((.35, .7, .9), ((105,45),(150,0),(0,150),(149,1),(1,149),(75,75))):
        yield f"grid{index:04d}", "allocation", replace(reference, lake_settlement=p), RecruitmentLimits(*ceilings)
        index += 1


def neutral_path(d: Demography, limits: RecruitmentLimits, start: dict) -> dict:
    state = dict(start)
    previous_previous = None
    guard_years = 0
    stable_steps = 0
    residual = math.inf
    cycle_residual = math.inf
    classification = "unresolved_at_cap"
    for step in range(1, MAX_STEPS + 1):
        new, diag = advance(state, d, limits)
        guard_years += int(diag["guard_active"])
        scale = 1 + max(new.values())
        residual = max(abs(new[key] - state[key]) for key in STATE_FIELDS) / scale
        if previous_previous is not None:
            cycle_residual = max(abs(new[key] - previous_previous[key]) for key in STATE_FIELDS) / scale
        if sum(new.values()) < 1e-8:
            classification = "near_zero"
            state = new
            break
        stable_steps = stable_steps + 1 if residual < TOLERANCE else 0
        if stable_steps >= 5:
            classification = "positive_fixed_point"
            state = new
            break
        if step > 20 and cycle_residual < TOLERANCE and residual > 100 * TOLERANCE:
            classification = "period_two_candidate"
            state = new
            break
        previous_previous, state = state, new
    return {
        "classification": classification, "steps": step,
        "guard_steps": guard_years, "relative_step_residual": residual,
        "relative_two_step_residual": cycle_residual,
        **state, "N_total": sum(state.values()),
        "eligible_total": state["A_L"] + state["A_R"],
    }


def neutral_comparison() -> pd.DataFrame:
    records = []
    params = reference_forcing_parameters()
    neutral = dict(connected=0, T=0., P=0., C_L=0., C_R=0., U=0., H=0., spawn_habitat_multiplier=1.)
    effects = dict(PR020=0., PR021=0., PR027=0., PR028=0.)
    generator = np.random.default_rng(0)
    for name, module in (("archived_common", common_model), ("archived_guard", mate_guard)):
        state = module._burn_in_state(params, burn_in_years=0)
        for step in range(129):
            records.append({"kernel":name,"step":step,**state})
            if step < 128:
                state, _ = module._advance_common_state(
                    state, neutral, neutral, params, effects, iter([generator] * 18),
                    juvenile_survival=params.value("PR001"), stochastic=False, juvenile_climbing_multiplier=1.,
                )
    d = reference_demography()
    limits = reference_limits()["historical_lake"]
    for label, start in (("founder",dict(J_L=0.,A_L=31.,J_R=0.,A_R=0.)),
                         ("low",dict(J_L=0.,A_L=2.,J_R=0.,A_R=0.)),
                         ("high",dict.fromkeys(STATE_FIELDS,500.))):
        state = start
        for step in range(129):
            records.append({"kernel":f"repaired_{label}","step":step,**state})
            if step < 128:
                state, _ = advance(state, d, limits)
    frame = pd.DataFrame.from_records(records)
    frame["eligible_total"] = frame.A_L + frame.A_R
    frame["juvenile_total"] = frame.J_L + frame.J_R
    return frame


def stochastic_job(job: tuple[str, str, int]) -> pd.DataFrame:
    scenario, restriction, seed = job
    return run_scenario(reference_demography(), reference_limits(), scenario,
                        restriction=restriction, seed=seed, stochastic=True)


def write_table(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, float_format="%.17g", lineterminator="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir
    if out.exists() and any(out.iterdir()):
        raise ValueError("Output directory must be new or empty; preserve previous attempts")
    out.mkdir(parents=True, exist_ok=True)
    start_time = time.monotonic()
    source_paths = [
        "src/galaxias_model/recruitment_demography.py", "src/galaxias_model/recruitment_scenarios.py",
        "src/galaxias_model/common_model.py", "src/galaxias_model/mate_guard.py",
        "src/galaxias_model/simulation.py", "src/galaxias_model/io.py", "src/galaxias_model/types.py",
        "scripts/qualify_demographic_repair.py", "docs/demographic_repair_protocol.md",
        "data/parameter_priors.csv", "data/scenario_definitions.json", "data/model_family_parameter_map.csv",
        "data/parameter_constraints.csv", "uv.lock",
    ]
    # Fail rather than silently omit an expected source/input binding.
    source_hashes = {path: sha(ROOT / path) for path in source_paths}
    spec = {
        "started_at":datetime.now(timezone.utc).isoformat(),
        "protocol":"docs/demographic_repair_protocol.md", "source_hashes":source_hashes,
        "demography":asdict(reference_demography()),
        "scenario_limits":{key:asdict(value) for key,value in reference_limits().items()},
        "neutral_max_steps":MAX_STEPS,"neutral_relative_tolerance":TOLERANCE,
        "python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,
        "meaning":"prospective demographic qualification; no fitted priors or history-matching scores",
    }
    (out / "inputs.json").write_text(json.dumps(spec, indent=2) + "\n")
    print("Frozen qualification inputs; beginning finite deterministic grid", flush=True)
    cells, runs = [], []
    for name, group, d, limits in grid():
        eq = neutral_equilibrium(d, limits)
        after, _ = advance(eq["state"], d, limits, guard=False)
        error = max(abs(after[key] - eq["state"][key]) for key in STATE_FIELDS)
        cell = {
            "cell":name,"group":group,**asdict(d),"limit_lake":limits.lake,"limit_refuge":limits.refuge,
            "replacement_ratio":d.recruits_per_adult / critical(d),"low_density_lambda":lambda_zero(d,limits),
            "analytic_positive":eq["positive"],"guard_consistent":eq["guard_consistent"],
            "analytic_fraction":eq["adult_fraction"],"analytic_adults":eq["adult_total"],
            "analytic_total":sum(eq["state"].values()),"fixed_point_absolute_error":error,
            "fixed_point_scaled_error":error / (1+max(eq["state"].values())),
        }
        cells.append(cell)
        starts = {"founder31":dict(J_L=0.,A_L=31.,J_R=0.,A_R=0.)}
        if eq["positive"]:
            starts.update(half={key:value/2 for key,value in eq["state"].items()},
                          twice={key:value*2 for key,value in eq["state"].items()})
        else:
            starts.update(low=dict.fromkeys(STATE_FIELDS,5.),high=dict.fromkeys(STATE_FIELDS,500.))
        for label, state in starts.items():
            result = neutral_path(d, limits, state)
            eq_error = max(abs(result[key]-eq["state"][key]) for key in STATE_FIELDS)
            runs.append({"cell":name,"start":label,**result,"distance_from_analytic":eq_error})
    cells_frame, runs_frame = pd.DataFrame(cells), pd.DataFrame(runs)
    write_table(cells_frame, out / "neutral_cells.csv")
    write_table(runs_frame, out / "neutral_runs.csv")
    comparison = neutral_comparison()
    write_table(comparison, out / "neutral_reference_comparison.csv")
    print("Deterministic grid complete; checking founder scenarios and worker parity", flush=True)

    d = reference_demography()
    limits = reference_limits()
    founder_frames, founder_metrics = [], []
    for site, ratio, factor in itertools.product(("lake_oberon","strathgordon"),(1.5,3.,6.),(.1,1.,10.)):
        candidate = replace(d,recruits_per_adult=ratio*critical(d))
        scaled = dict(limits)
        scaled[site] = RecruitmentLimits(limits[site].lake*factor,limits[site].refuge*factor)
        frame = run_scenario(candidate,scaled,site)
        frame.insert(0,"replacement_ratio",ratio)
        frame.insert(1,"limit_multiplier",factor)
        founder_frames.append(frame)
        final = frame.iloc[-1]
        juv = frame.J_L + frame.J_R
        first = frame.loc[juv>0,"year"]
        founder_metrics.append({"scenario":site,"replacement_ratio":ratio,"limit_multiplier":factor,
            "final_total":final.N_total,"final_eligible":final.A_L+final.A_R,
            "founders_total":frame.founders_added.sum(),"minimum_total":frame.N_total.min(),
            "net_growth":final.N_total>frame.founders_added.sum(),
            "first_juvenile_year":None if first.empty else int(first.iloc[0])})
    write_table(pd.concat(founder_frames,ignore_index=True),out / "founder_sensitivity_trajectories.csv")
    write_table(pd.DataFrame(founder_metrics),out / "founder_sensitivity_summary.csv")
    reference_founders = pd.concat([run_scenario(d,limits,site) for site in ("lake_oberon","strathgordon")],ignore_index=True)
    write_table(reference_founders,out / "reference_founder_trajectories.csv")

    jobs = [(site,"R_J",2026092300+seed) for site in ("lake_oberon","strathgordon") for seed in range(32)]
    jobs += [("historical_lake",restriction,2026092400+seed) for restriction in common_model.RESTRICTIONS for seed in range(8)]
    serial = [stochastic_job(job) for job in jobs]
    with ProcessPoolExecutor(max_workers=2) as pool:
        parallel = list(pool.map(stochastic_job,jobs))
    for left,right in zip(serial,parallel,strict=True):
        pd.testing.assert_frame_equal(left,right,check_exact=True)
        assert left.attrs == right.attrs
    stochastic = pd.concat(serial,ignore_index=True)
    write_table(stochastic,out / "stochastic_qualification.csv")
    pre = stochastic[[f"pre_{key}" for key in STATE_FIELDS]].sum(axis=1)
    counts = stochastic[list(STATE_FIELDS)].to_numpy()
    guard = stochastic.pre_A_L + stochastic.pre_A_R < 2
    guard_recruits = stochastic.loc[guard,["realized_recruits_lake","realized_recruits_refuge"]].to_numpy()
    checks = {
        "analytic_fixed_points":bool((cells_frame.fixed_point_scaled_error<1e-10).all()),
        "no_period_two_candidates":not bool((runs_frame.classification=="period_two_candidate").any()),
        "nonnegative_finite_stochastic":bool(np.isfinite(counts).all() and (counts>=0).all()),
        "integer_stochastic":bool((counts==np.floor(counts)).all()),
        "guard_prevents_recruitment":bool((guard_recruits==0).all()),
        "no_zero_singleton_rebound":bool((stochastic.loc[pre<=1,"N_total"]<=pre.loc[pre<=1]).all()),
        "serial_parallel_exact":True,
        "source_hashes_unchanged":all(sha(ROOT/path)==value for path,value in source_hashes.items()),
    }
    ref_eq = neutral_equilibrium(d,limits["historical_lake"])
    ref_window = comparison.loc[(comparison.kernel.str.startswith("repaired")) & comparison.step.isin([99,100,101])]
    reference_error = max(abs(ref_window[key]-ref_eq["state"][key]).max() for key in STATE_FIELDS)
    tail = comparison.loc[comparison.kernel.str.startswith("repaired") & comparison.step.isin([126,127,128])]
    tail_error = max(abs(tail[key]-ref_eq["state"][key]).max() for key in STATE_FIELDS)
    checks["reference_tail_converged"] = bool(tail_error<1e-8)
    summary = {
        "status":"mechanically_qualified" if all(checks.values()) else "requires_review",
        "checks":checks,"reference_equilibrium":ref_eq,"reference_99_101_max_error":reference_error,
        "reference_99_101_within_1e8":bool(reference_error<1e-8),
        "reference_126_128_max_error":tail_error,
        "neutral_cells":len(cells),"neutral_paths":len(runs),
        "neutral_path_steps":int(runs_frame.steps.sum()),
        "neutral_classifications":{str(key):int(value) for key,value in runs_frame.classification.value_counts().items()},
        "guard_inconsistent_positive_cells":int((cells_frame.analytic_positive & ~cells_frame.guard_consistent).sum()),
        "maximum_fixed_point_error":float(cells_frame.fixed_point_scaled_error.max()),
        "founder_sensitivity_paths":len(founder_frames),
        "deterministic_paths_this_run":len(runs)+5+len(founder_frames)+2,
        "stochastic_unique_paths":len(jobs),"stochastic_executions":2*len(jobs),
        "stochastic_rows":len(stochastic),"stochastic_starting_states":[
            {"scenario":job[0],"restriction":job[1],"seed":job[2],**frame.attrs} for job,frame in zip(jobs,serial,strict=True)
        ],
        "elapsed_seconds":time.monotonic()-start_time,
        "completed_at":datetime.now(timezone.utc).isoformat(),
        "limits":"Qualification only; site limits and b are illustrative, no ecological likelihood or historical ranking.",
    }
    (out / "readout.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    hashes={path.name:sha(path) for path in sorted(out.iterdir()) if path.is_file()}
    (out / "output_hashes.json").write_text(json.dumps(hashes,indent=2)+"\n")
    print(json.dumps({key:summary[key] for key in ("status","checks","neutral_classifications","elapsed_seconds")}),flush=True)


if __name__ == "__main__":
    main()
