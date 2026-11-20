#!/usr/bin/env python3
"""Bounded observation-repair pilot with shared histories and held-out validation."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import hashlib
import json
import math
import multiprocessing
import platform
import sys
from pathlib import Path
import subprocess
import time

import numpy as np
import pandas as pd

from galaxias_model.calibration import (
    DEFAULT_FAMILY_ORDER, STAGE_B_CODE, _derive_seed, _family_index,
    _load_inputs_cached, _prepare_parameter_table, _scenario_config,
)
from galaxias_model.observation_repair import (
    LATE_BLOCK_WEIGHT, REPAIR_PROFILES, aggregate_repaired_late_evidence,
    project_repaired_history,
)
from galaxias_model.sampling import build_resolved_parameters_from_sample
from galaxias_model.scoring import score_scenario_run
from galaxias_model.simulation import run_historical_simulation, run_scenario_simulation
from galaxias_model.types import Module3Config, ScoringConfig

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("baseline_current", *REPAIR_PROFILES)
VALIDATION_CODE = 409
TARGETS = [f"CT{i:03d}" for i in range(1, 13)]
ORDER = ["overall_distance", "historical_distance", "intrinsic_distance", "historical_iqr", "proposal_id"]
IDENTITY = ["search_seed", "family_id", "proposal_id"]


def phase_seed(search_seed, family, proposal_index, replicate_index, phase):
    if phase not in {"stage_b", "validation"}:
        raise ValueError(f"Unknown stochastic phase: {phase}")
    code = STAGE_B_CODE if phase == "stage_b" else VALIDATION_CODE
    return _derive_seed(search_seed, _family_index(family), proposal_index, replicate_index, code)


def scored_fields(result, inputs):
    scores = score_scenario_run(result, inputs, ScoringConfig()).target_score_table
    scores = scores.loc[scores.evaluation_status == "scored"]
    if not np.isfinite(scores.weighted_penalty).all():
        raise ValueError("Nonfinite legacy penalty in pilot simulation")
    return {f"{r.target_id}_{field}": getattr(r, field)
            for r in scores.itertuples(index=False)
            for field in ["raw_penalty", "weighted_penalty", "projected_primary", "projected_secondary"]}


def simulate_source(task):
    """One source/phase per job; deterministic intrinsic values are reused."""
    inputs = _load_inputs_cached(task["data_dir"])
    family = task["family_id"]
    params = build_resolved_parameters_from_sample(inputs, family, pd.DataFrame(task["parameter_rows"]))
    phase = task["phase"]
    intrinsic = dict(task.get("intrinsic", {}))
    if phase == "stage_a":
        for offset, scenario in enumerate(["lake_oberon", "strathgordon"]):
            baseline = run_scenario_simulation(params, family, _scenario_config(inputs, scenario, False), seed=task["proposal_seed"] + offset)
            intrinsic.update(scored_fields(baseline, inputs))
    rows = []
    for rep in range(0 if phase == "stage_a" else 1, 1 if phase == "stage_a" else task["replicates"] + 1):
        seed = task["proposal_seed"] if phase == "stage_a" else phase_seed(task["search_seed"], family, task["proposal_index"], rep, phase)
        history = run_historical_simulation(params, family, _scenario_config(inputs, "historical_lake", phase != "stage_a"), seed=seed)
        row = {key: task[key] for key in IDENTITY}
        row.update(stage=phase, replicate_index=rep, simulation_seed=seed)
        row.update(project_repaired_history(history))
        row.update(scored_fields(history, inputs))
        row.update(intrinsic)
        if not all(f"{target}_weighted_penalty" in row for target in TARGETS):
            raise ValueError("Incomplete legacy target coverage")
        rows.append(row)
    return rows


def source_summaries(raw, membership=None, selected=None):
    rows = []
    feature_names = [c for c in raw if c not in {*IDENTITY, "stage", "replicate_index", "simulation_seed"} and not c.startswith("CT")]
    for identity, group in raw.groupby(IDENTITY, sort=True):
        search_seed, family, proposal = identity
        intrinsic = group[[f"{t}_weighted_penalty" for t in TARGETS[10:]]].sum(axis=1)
        if not np.allclose(intrinsic, intrinsic.iloc[0]):
            raise ValueError("Deterministic intrinsic scores changed across replicates")
        early = group[[f"{t}_weighted_penalty" for t in TARGETS[:5]]].sum(axis=1)
        historical = group[[f"{t}_weighted_penalty" for t in TARGETS[:10]]].sum(axis=1)
        for profile in PROFILES:
            p = REPAIR_PROFILES.get(profile, 0.)
            late = aggregate_repaired_late_evidence(group, p)
            if profile == "baseline_current":
                overall = float((historical + intrinsic).median())
                hist = float(historical.median())
                iqr = float(historical.quantile(.75) - historical.quantile(.25))
                eligible = math.isfinite(overall)
            else:
                overall = float((early + intrinsic).median()) + LATE_BLOCK_WEIGHT * late["late_discrepancy"]
                hist = float(early.median()) + LATE_BLOCK_WEIGHT * late["late_discrepancy"]
                iqr = float(early.quantile(.75) - early.quantile(.25))
                eligible = late["sample_supported"] and math.isfinite(overall)
            key = (*identity, profile)
            rows.append({**dict(zip(IDENTITY, identity)), "stage": group.stage.iloc[0], "profile": profile,
                         "stage_a_retained": key in membership if membership is not None else False,
                         "selected": key in selected if selected is not None else False,
                         "finite_supported": eligible, "overall_distance": overall,
                         "historical_distance": hist, "intrinsic_distance": float(intrinsic.iloc[0]),
                         "historical_iqr": iqr, "diagnostic_detection_probability": p,
                         **late, **{f"{c}_{stat}": float(group[c].agg(stat)) for c in feature_names for stat in ["mean", "median"]}})
    return pd.DataFrame(rows)


def select_sources(summary, stage_a_keep=None, fraction=.1, cap=50):
    """Selection is forbidden for validation; its selected flag is inherited."""
    if summary.stage.eq("validation").any():
        raise ValueError("Independent validation must never select or rerank sources")
    result = summary.copy()
    group_keys = ["search_seed", "profile"] + (["family_id"] if stage_a_keep is not None else [])
    flag = "stage_a_retained" if stage_a_keep is not None else "selected"
    result[flag] = False
    result["selection_rank"] = np.nan
    for _, group in result.groupby(group_keys, sort=True):
        eligible = group.loc[group.finite_supported]
        if stage_a_keep is None:
            eligible = eligible.loc[eligible.stage_a_retained]
        ordered = eligible.sort_values(ORDER)
        count = min(stage_a_keep, len(ordered)) if stage_a_keep is not None else min(cap, math.ceil(fraction * len(ordered)))
        result.loc[ordered.index, "selection_rank"] = np.arange(1, len(ordered) + 1)
        result.loc[ordered.head(count).index, flag] = True
    return result


def membership_set(summary, flag):
    return set(summary.loc[summary[flag], [*IDENTITY, "profile"]].itertuples(index=False, name=None))


def execute(tasks, workers):
    if not tasks:
        return pd.DataFrame()
    if workers == 1:
        results = map(simulate_source, tasks)
        return pd.DataFrame([r for batch in results for r in batch])
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
        return pd.DataFrame([r for batch in pool.map(simulate_source, tasks, chunksize=1) for r in batch])


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def run_pilot(output_dir, *, data_dir=ROOT / "data", families=tuple(DEFAULT_FAMILY_ORDER), seeds=(20260908, 20260909), draws=100, keep=20, stage_b_replicates=20, validation_replicates=100, workers=1, acceptance_fraction=.1, acceptance_cap=50):
    output_dir, data_dir = Path(output_dir), Path(data_dir)
    integers = [draws, keep, stage_b_replicates, validation_replicates, workers, acceptance_cap]
    if any(type(x) is not int or x < 1 for x in integers) or workers > 16 or keep > draws:
        raise ValueError("Positive integer budgets required; keep <= draws; workers <= 16")
    if not 0 < acceptance_fraction <= 1 or not seeds or len(set(seeds)) != len(seeds) or any(type(s) is not int or s < 0 for s in seeds):
        raise ValueError("Invalid acceptance fraction or search seeds")
    if not families or len(set(families)) != len(families) or not set(families).issubset(DEFAULT_FAMILY_ORDER):
        raise ValueError("Unknown or duplicate families")
    if output_dir.resolve().is_relative_to(ROOT) and not output_dir.resolve().is_relative_to(ROOT / "outputs"):
        raise ValueError("Repository-local pilot outputs must be under ignored outputs/")
    # A failed/partial directory is evidence too: reruns require a new path.
    output_dir.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    inputs = _load_inputs_cached(str(data_dir.resolve()))
    tasks, parameter_tables, configs = [], [], []
    for seed in seeds:
        config = Module3Config(families=tuple(families), master_seed=seed, stage_a_draws_per_family=draws, stage_a_keep_per_family=keep, stage_b_historical_replicates=stage_b_replicates, final_acceptance_fraction=acceptance_fraction, final_acceptance_cap=acceptance_cap, workers=workers, output_dir=output_dir)
        configs.append({**asdict(config), "output_dir": "."})
        for family in families:
            parameters = _prepare_parameter_table(inputs, family, config)
            parameters["search_seed"] = seed
            parameter_tables.append(parameters)
            for proposal, group in parameters.groupby("proposal_id", sort=True):
                first = group.iloc[0]
                tasks.append({"search_seed": seed, "family_id": family, "proposal_id": proposal,
                              "proposal_index": int(first.proposal_index), "proposal_seed": int(first.proposal_seed),
                              "data_dir": str(data_dir.resolve()), "parameter_rows": group.to_dict("records"), "phase": "stage_a", "replicates": 1})
    pd.concat(parameter_tables, ignore_index=True).to_csv(output_dir / "parameter_values.csv.gz", index=False)
    deterministic = execute(tasks, workers)
    stage_a = select_sources(source_summaries(deterministic), stage_a_keep=keep)
    membership = membership_set(stage_a, "stage_a_retained")
    union_a = {key[:3] for key in membership}
    deterministic.to_csv(output_dir / "deterministic_projections.csv.gz", index=False)
    stage_a.to_csv(output_dir / "stage_a_selection.csv", index=False)
    print(f"Stage A complete: {len(tasks)} prior sources; {len(union_a)} retained across profiles", flush=True)
    det_index = deterministic.set_index(IDENTITY)
    b_tasks = []
    for task in tasks:
        identity = tuple(task[k] for k in IDENTITY)
        if identity in union_a:
            intrinsic = {c: det_index.loc[identity, c] for c in deterministic if c.startswith(("CT011_", "CT012_"))}
            b_tasks.append({**task, "phase": "stage_b", "replicates": stage_b_replicates, "intrinsic": intrinsic})
    stage_b = execute(b_tasks, workers)
    if stage_b.empty:
        raise ValueError("No Stage A-retained sources, including legacy control")
    b_summary = select_sources(source_summaries(stage_b, membership), fraction=acceptance_fraction, cap=acceptance_cap)
    selection = membership_set(b_summary, "selected")
    union_selected = {key[:3] for key in selection}
    stage_b.to_csv(output_dir / "stage_b_replicates.csv.gz", index=False)
    b_summary.to_csv(output_dir / "stage_b_source_summary.csv", index=False)
    print(f"Stage B complete: {len(stage_b)} histories; {len(union_selected)} selected sources for independent validation", flush=True)
    v_tasks = [{**task, "phase": "validation", "replicates": validation_replicates}
               for task in b_tasks if tuple(task[k] for k in IDENTITY) in union_selected]
    validation = execute(v_tasks, workers)
    v_summary = source_summaries(validation, membership, selection)
    if set(stage_b.simulation_seed) & set(validation.simulation_seed):
        raise ValueError("Stage B and validation RNG seed collision")
    for phase, table in [("stage_b", stage_b), ("validation", validation)]:
        if table.simulation_seed.duplicated().any():
            raise ValueError(f"Duplicate RNG seed within {phase}")
    validation.to_csv(output_dir / "validation_replicates.csv.gz", index=False)
    v_summary.to_csv(output_dir / "validation_source_summary.csv", index=False)
    binding_paths = sorted((ROOT / "src/galaxias_model").glob("*.py")) + [Path(__file__), ROOT / "uv.lock", ROOT / "pyproject.toml", ROOT / "docs/observation_repair_pilot.md"]
    # These are the model input files; bind existing files without generated summaries.
    binding_paths += [data_dir / name for name in ["parameter_priors.csv", "model_family_parameter_map.csv", "parameter_constraints.csv", "evidence_ledger.csv", "calibration_targets.csv", "calibration_target_details.json", "scenario_definitions.json"]]
    manifest = {"status": "complete", "scope": "bounded_observation_repair_pilot", "configs": configs,
                "runtime": {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__, "platform": platform.platform()},
                "profiles": {"baseline_current": "unchanged legacy control", **REPAIR_PROFILES}, "late_block_weight": LATE_BLOCK_WEIGHT,
                "validation_replicates": validation_replicates, "seed_codes": {"stage_b": STAGE_B_CODE, "validation": VALIDATION_CODE},
                "source_identity": IDENTITY, "selection_identity": [*IDENTITY, "profile"],
                "validation_policy": "Independent process histories at the original selected theta; selected flags inherited; no reselection. Sources are shared across all profiles; only profile-specific Stage A members may be selected.",
                "legacy_diagnostics": "Presence-only repaired late metrics are diagnostics; legacy selection uses only original CT001-CT012 penalties.",
                "unsupported_policy": "Zero positive-compatible histories are ineligible at this Monte Carlo budget, not simulation failure or proof of true zero support.",
                "counts": {"prior_sources": len(tasks), "deterministic_historical_runs": len(tasks), "deterministic_intrinsic_runs": 2 * len(tasks), "stage_b_union_sources": len(b_tasks), "stage_b_historical_runs": len(stage_b), "validation_union_sources": len(v_tasks), "validation_historical_runs": len(validation)},
                "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "source_bindings": [{"path": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name, **file_hash(p)} for p in binding_paths],
                "outputs": {p.name: file_hash(p) for p in sorted(output_dir.iterdir()) if p.is_file()},
                "elapsed_seconds": round(time.monotonic() - start, 3)}
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"counts": manifest["counts"], "elapsed_seconds": manifest["elapsed_seconds"]}), flush=True)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--families", nargs="+", choices=DEFAULT_FAMILY_ORDER, default=DEFAULT_FAMILY_ORDER)
    parser.add_argument("--seeds", nargs="+", type=int, default=[20260908, 20260909])
    parser.add_argument("--draws", type=int, default=100)
    parser.add_argument("--keep", type=int, default=20)
    parser.add_argument("--stage-b-replicates", type=int, default=20)
    parser.add_argument("--validation-replicates", type=int, default=100)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--acceptance-fraction", type=float, default=.1)
    parser.add_argument("--acceptance-cap", type=int, default=50)
    args = vars(parser.parse_args())
    run_pilot(**args)
