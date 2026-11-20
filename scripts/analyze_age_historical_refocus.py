#!/usr/bin/env python3
"""Assess the frozen historically refocused recovery bank without simulation."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
import hashlib
from itertools import product
import json
import math
import multiprocessing as mp
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from scripts.run_age_recovery import binding, json_value, utc, verify_bindings
from scripts.analyze_age_recovery import (
    _control_feature, _read_jsonl, _select_profiles, _verify_generation_manifest,
    _verify_history_source_matches, _write_csv,
)
from galaxias_model.age_historical_refocus import lake_history_log_score
from galaxias_model.age_recovery_observation import (
    BINARY_RECORDS, decision_profiles, exposures, generate_observations,
)
from galaxias_model.age_recovery_scores import score_blocks
from galaxias_model.age_refocus_scores import weighted_classify, weighted_recovery_metrics
from galaxias_model.age_sources import keyed_seed, source_group

ENDPOINTS = ("terminal_alive", "terminal_pair", "terminal_same_compartment_pair", "terminal_age1plus10")
GENERATORS = ("poisson", "gamma_quality", "fixed_creek_total")
BLOCKS = ("creek", "survey", "full", "feasibility")


def gate_decision(rows, *, full):
    primary = [r for r in rows if r["panel"] == "base" and r["endpoint"] == "terminal_alive"]
    passing = [r for r in primary if r["gate_passed"] and r["generator"] in ("poisson", "gamma_quality")]
    status = "QUALIFICATION_SMOKE_ONLY" if not full else "CONDITIONAL_GO_REQUIRES_QUALIFIED_COLUMNS" if passing else "STOP_BEFORE_HISTORICAL_COMPARISON"
    return dict(status=status, primary_base_passes=len(passing),
                primary_base_assessed=sum(r["assessed"] for r in primary),
                primary_base_status_counts=dict(Counter(r["status"] for r in primary)),
                conditional_go_columns=[{k:r[k] for k in ("cell_id", "index_stratum", "profile_id", "generator")} for r in passing] if full else [])


def finite_json(value):
    value = json_value(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: finite_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [finite_json(v) for v in value]
    return value


def save_json(path, value):
    path.write_text(json.dumps(finite_json(value), indent=2, sort_keys=True, allow_nan=False) + "\n")


def write_csv(path, rows):
    _write_csv(path, rows)
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def historical_weights(rows, means, profile):
    if not rows:
        return np.empty(0)
    means = np.asarray(means, dtype=float)
    adjusted = np.where(means > 0, np.maximum(0, means + .08*profile["reading_shift"]), 0.)
    features = np.asarray([row["features"]["lake"] for row in rows])
    score = lake_history_log_score(features, adjusted, power=profile["lake_power"],
                                   rho=profile["lake_rho"], age1=profile["lake_age1"])
    return score - np.asarray([row["proposal_log_density_ratio"] for row in rows])


def source_support(log_weights, source_ids, labels):
    """Class-specific source support; repeat histories never become sources."""
    ids = np.asarray(source_ids)
    labels = np.asarray(labels, dtype=bool)
    logs = np.asarray(log_weights, dtype=float)
    counts, ess, largest = np.zeros(2, dtype=int), np.zeros(2), np.zeros(2)
    for value in (0, 1):
        select = (labels == bool(value)) & np.isfinite(logs)
        if not select.any():
            continue
        unique, inverse = np.unique(ids[select], return_inverse=True)
        w = np.exp(logs[select]-logs[select].max())
        summed = np.bincount(inverse, weights=w, minlength=len(unique))
        counts[value] = len(unique)
        ess[value] = summed.sum()**2/np.square(summed).sum()
        largest[value] = summed.max()/summed.sum()
    return counts, ess, largest


def normalized(log_weights):
    values = np.asarray(log_weights, dtype=float)
    output = np.zeros(len(values))
    finite = np.isfinite(values)
    if finite.any():
        output[finite] = np.exp(values[finite]-values[finite].max())
        output /= output.sum()
    return output


def weighted_quantile(values, weights, probability):
    if not len(values) or np.sum(weights) == 0:
        return math.nan
    order = np.argsort(values, kind="stable")
    cdf = np.cumsum(np.asarray(weights)[order])/np.sum(weights)
    return float(np.asarray(values)[order][min(np.searchsorted(cdf, probability), len(order)-1)])


def composition(rows, log_weights, metadata):
    weights = normalized(log_weights)
    ids = [row["source_id"] for row in rows]
    alive = np.asarray([row["terminal_alive"] for row in rows], dtype=bool)
    counts, ess, largest = source_support(log_weights, ids, alive)
    all_ids = np.asarray(ids)
    total_source_ess = 0.
    if weights.sum():
        _, inverse = np.unique(all_ids, return_inverse=True)
        summed = np.bincount(inverse, weights=weights)
        total_source_ess = 1/np.square(summed).sum()
    def mean(values):
        return float(np.dot(weights, values)) if weights.sum() else math.nan
    lake = np.asarray([row["lake_2002"] for row in rows])
    total = lake + np.asarray([row["refuge_2002"] for row in rows])
    result = dict(metadata, complete_histories=len(rows), total_source_ess=total_source_ess,
                  positive_sources_loss=int(counts[0]), positive_sources_alive=int(counts[1]),
                  source_ess_loss=float(ess[0]), source_ess_alive=float(ess[1]),
                  largest_source_share_loss=float(largest[0]), largest_source_share_alive=float(largest[1]),
                  weighted_loss=mean(~alive), weighted_lake_present=mean(lake > 0),
                  weighted_mean_lake=mean(lake), weighted_mean_natural_total=mean(total),
                  weighted_persisting_total_median=weighted_quantile(total[alive], weights[alive], .5),
                  weighted_persisting_lake_median=weighted_quantile(lake[alive], weights[alive], .5),
                  weighted_persisting_lake_p95=weighted_quantile(lake[alive], weights[alive], .95))
    for endpoint in ENDPOINTS[1:]:
        result[f"weighted_{endpoint}"] = mean(np.asarray([row[endpoint] for row in rows], dtype=bool))
    return result


def composition_profiles():
    profiles = {}
    for profile in decision_profiles():
        key = tuple(profile[name] for name in ("lake_power", "lake_rho", "lake_age1", "reading_shift"))
        if key not in profiles:
            profiles[key] = dict(profile, profile_id=profile["panel"])
    return list(profiles.values())


def composition_rows(rows, means, metadata):
    result = [composition(rows, -np.asarray([r["proposal_log_density_ratio"] for r in rows]),
                          dict(metadata, target="g_process_feasible", campaign="none", q_electro=0., q_larvae=0., law="none", timing="none"))]
    for profile in composition_profiles():
        result.append(composition(rows, historical_weights(rows, means, profile),
                                  dict(metadata, target=f"early_lake_{profile['panel']}", campaign="none", q_electro=0., q_larvae=0., law="none", timing="none")))
    base = historical_weights(rows, means, decision_profiles()[0])
    for law in ("poisson", "gamma_quality"):
        cases = [(q, 0.) for q in (.01, .1, 1.)] + [(0., q) for q in (.01, .1, 1.)]
        cases += list(product((.01, .1, 1.), repeat=2))
        for qe, ql in cases:
            for timing in (("start", "mid", "end") if qe else ("none",)):
                xe = np.asarray([r["campaign_exposures"][f"electro_{timing}"] for r in rows]) if qe else np.zeros(len(rows))
                xl = np.asarray([r["campaign_exposures"]["larvae"] for r in rows]) if ql else np.zeros(len(rows))
                extra = -qe*xe-ql*xl if law == "poisson" else -np.log1p(qe*xe)-np.log1p(ql*xl)
                campaign = "both" if qe and ql else "electro" if qe else "larvae"
                result.append(composition(rows, base+extra,
                                          dict(metadata, target="early_lake_base_plus_campaign_sensitivity", campaign=campaign,
                                               q_electro=qe, q_larvae=ql, law=law, timing=timing)))
    return result


def weighted_controls():
    profile = dict(decision_profiles()[0], q=1.)
    labels = np.asarray([False]*8 + [True]*8)
    ids = [f"weighted-control-{i}" for i in range(16)]
    observations = (np.zeros((2, 3), dtype=np.int64), np.zeros((2, 2)),
                    np.asarray([[False]*len(BINARY_RECORDS), [True]*len(BINARY_RECORDS)]))
    features = [_control_feature(1e-4)]*8+[_control_feature(1.)]*8
    parts = score_blocks(*exposures(features, profile), *observations, q=1., creek_power=1., lake_power=1/12)
    # Unequal class masses must disappear under equal class reference weights.
    logs = np.log(np.asarray([.4]*8+[.01]*8))
    informative = weighted_classify(parts["total"], ids, labels, logs)
    identical = score_blocks(*exposures([_control_feature(1.)]*16, profile), *observations,
                             q=1., creek_power=1., lake_power=1/12)
    tied = weighted_classify(identical["total"], ids, labels, logs)
    exact = score_blocks(*exposures([_control_feature(0.)]*8+[_control_feature(1.)]*8, profile), *observations,
                         q=1., creek_power=1., lake_power=1/12)
    result = dict(informative_predictions=informative["prediction"].tolist(),
                  informative_post_ess=informative["postESS"].tolist(),
                  identical_exposure_predictions=tied["prediction"].tolist(),
                  identical_exposure_log_ratios=tied["log_ratio"].tolist(),
                  exact_zero_positive_impossible=bool(np.isneginf(exact["total"][1, :8]).all()),
                  biology_calls=0)
    result["all_passed"] = bool(result["informative_predictions"] == [0, 1]
                                and result["identical_exposure_predictions"] == [-1, -1]
                                and np.allclose(tied["log_ratio"], 0., atol=1e-12)
                                and result["exact_zero_positive_impossible"])
    return result


def analyze_stratum(task):
    cell, stratum, all_rows, all_sources, profiles, means, bootstrap = task
    rows = [r for r in all_rows if r["status"] == "complete"]
    truth = sorted([r for r in rows if r["namespace"] == "truth"], key=lambda r:(r["source_id"], r["replicate"]))
    bank = sorted([r for r in rows if r["namespace"] == "bank"], key=lambda r:(r["source_id"], r["replicate"]))
    truth_ids, bank_ids = [r["source_id"] for r in truth], [r["source_id"] for r in bank]
    truth_universe = sorted({s["source_id"] for s in all_sources if s["role"] == "truth"})
    metadata = dict(cell_id=cell, index_stratum=stratum)
    compositions = []
    for role, selected in (("truth", truth), ("bank", bank)):
        compositions.extend(composition_rows(selected, means, dict(metadata, namespace=role)))
    output, reproducibility = [], hashlib.sha256()
    truth_features, bank_features = [r["features"] for r in truth], [r["features"] for r in bank]
    group = source_group(all_sources[0]["cell"])
    for profile in profiles:
        truth_logs, bank_logs = historical_weights(truth, means, profile), historical_weights(bank, means, profile)
        bank_x = exposures(bank_features, profile)
        for generator in GENERATORS:
            obs = generate_observations(truth_features, [(r["source_id"], r["replicate"]) for r in truth],
                                        [r["march_retention"] for r in truth], profile, generator=generator)
            coherent = obs["coherent"]
            for key in ("creek_counts", "lake_equivalents", "binary_counts", "coherent"):
                reproducibility.update(np.ascontiguousarray(obs[key]).tobytes())
            parts = None
            for endpoint in ENDPOINTS:
                truth_labels = np.asarray([r[endpoint] for r in truth], dtype=bool)
                bank_labels = np.asarray([r[endpoint] for r in bank], dtype=bool)
                tcount, tess, tmax = source_support(np.where(coherent, truth_logs, -math.inf), truth_ids, truth_labels)
                bcount, bess, bmax = source_support(bank_logs, bank_ids, bank_labels)
                truth_ok = bool(np.all(tcount >= 16) and np.all(tess >= 16))
                bank_ok = bool(np.all(bcount >= 8) and np.all(bess >= 4))
                row = dict(metadata, endpoint=endpoint, profile_id=profile["profile_id"], panel=profile["panel"], generator=generator,
                           complete_truth_histories=len(truth), coherent_truth_histories=int(coherent.sum()), complete_bank_histories=len(bank),
                           truth_sources_false=int(tcount[0]), truth_sources_true=int(tcount[1]),
                           truth_source_ess_false=float(tess[0]), truth_source_ess_true=float(tess[1]),
                           bank_sources_false=int(bcount[0]), bank_sources_true=int(bcount[1]),
                           bank_source_ess_false=float(bess[0]), bank_source_ess_true=float(bess[1]),
                           truth_support_sufficient=truth_ok, bank_support_sufficient=bank_ok,
                           assessed=truth_ok and bank_ok, gate_passed=False,
                           full_minus_survey=math.nan, full_minus_survey_ci_lower95=math.nan, full_minus_survey_ci_upper95=math.nan,
                           weighted_observation_coherence=float(np.dot(normalized(truth_logs), coherent)) if np.isfinite(truth_logs).any() else math.nan)
                for block in BLOCKS:
                    row.update({f"{block}_{name}": math.nan for name in ("sensitivity_false", "sensitivity_true", "balanced_accuracy", "ci_lower95", "ci_upper95", "posterior_bank_coverage")})
                if not (truth_ok and bank_ok):
                    row["status"] = "unassessed_truth_and_bank_support" if not truth_ok and not bank_ok else "unassessed_truth_support" if not truth_ok else "unassessed_bank_support"
                    output.append(row)
                    continue
                if parts is None:
                    parts = score_blocks(*bank_x, obs["creek_counts"], obs["lake_equivalents"], obs["binary_observed"],
                                         q=profile["q"], creek_power=profile["creek_power"], lake_power=profile["lake_power"])
                matrices = dict(creek=parts["creek"], survey=parts["creek"]+parts["lake"], full=parts["total"], feasibility=np.zeros_like(parts["total"]))
                classified = {name: weighted_classify(matrix, bank_ids, bank_labels, bank_logs) for name, matrix in matrices.items()}
                metrics = weighted_recovery_metrics(classified["full"]["prediction"], truth_labels, truth_ids, truth_logs,
                    coherent_mask=coherent, truth_source_universe=truth_universe,
                    paired_predictions={name: classified[name]["prediction"] for name in ("creek", "survey", "feasibility")},
                    bootstrap_seed=keyed_seed("age-refocus-bootstrap-20261002", group, stratum, endpoint, generator),
                    bootstrap_replicates=bootstrap)
                for block in BLOCKS:
                    if block == "full":
                        values, ci = metrics, metrics["balanced_accuracy_ci95"]
                    else:
                        values = metrics["paired"][block]
                        finite = values["bootstrap_balanced_accuracy"][np.isfinite(values["bootstrap_balanced_accuracy"])]
                        ci = np.percentile(finite, [2.5, 97.5]) if len(finite) else [math.nan, math.nan]
                    row.update({f"{block}_sensitivity_false": float(values["sensitivity"][0]),
                                f"{block}_sensitivity_true": float(values["sensitivity"][1]),
                                f"{block}_balanced_accuracy": float(values["balanced_accuracy"]),
                                f"{block}_ci_lower95": float(ci[0]), f"{block}_ci_upper95": float(ci[1]),
                                f"{block}_posterior_bank_coverage": float(np.dot(normalized(np.where(coherent, truth_logs, -math.inf)), np.all(classified[block]["postESS"] >= 4, axis=1)))})
                    reproducibility.update(classified[block]["prediction"].tobytes())
                paired = metrics["paired"]["survey"]
                row.update(gate_passed=bool(metrics["gate_passed"]),
                           status="passed" if metrics["gate_passed"] else "did_not_pass",
                           full_minus_survey=float(paired["delta_balanced_accuracy"]),
                           full_minus_survey_ci_lower95=float(paired["delta_ci95"][0]),
                           full_minus_survey_ci_upper95=float(paired["delta_ci95"][1]))
                output.append(row)
    return dict(rows=output, compositions=compositions,
                digest=dict(metadata, observation_prediction_sha256=reproducibility.hexdigest()),
                process_counts=dict(Counter(r["status"] for r in all_rows)))


def run(args):
    if not 1 <= args.workers <= 16 or args.bootstrap_replicates != 1000:
        raise ValueError("use1..16 workers and the frozen1000 bootstrap replicates")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started, timer = utc(), time.monotonic()
    paths = [Path(__file__), ROOT / "src/galaxias_model/age_refocus_scores.py",
             ROOT / "src/galaxias_model/age_historical_refocus.py",
             ROOT / "src/galaxias_model/age_recovery_observation.py",
             ROOT / "src/galaxias_model/age_recovery_scores.py",
             ROOT / "scripts/analyze_age_recovery.py", ROOT / "docs/age_historical_refocus_protocol.md"]
    frozen = {str(p.relative_to(ROOT)): binding(p) for p in paths}
    sources = _read_jsonl(args.input_dir / "source_banks.jsonl")
    generation = _verify_generation_manifest(args.input_dir, sources)
    histories = _read_jsonl(args.input_dir / "histories.jsonl.gz", compressed=True)
    _verify_history_source_matches(histories, sources, generation)
    profiles = _select_profiles(args.profiles)
    controls = weighted_controls()
    save_json(output / "score_controls.json", controls)
    if not controls["all_passed"]:
        raise RuntimeError("weighted score controls failed")
    tasks = []
    for cell in generation["cells"]:
        name = next(s["cell_id"] for s in sources if s["cell"] == cell)
        for stratum in ("below_one", "above_one"):
            tasks.append((name, stratum, [r for r in histories if r["cell_id"] == name and r["index_stratum"] == stratum],
                          [s for s in sources if s["cell_id"] == name and s["index_stratum"] == stratum],
                          profiles, generation["historical_lake_means"], args.bootstrap_replicates))
    pool = ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn")) if args.workers > 1 else None
    all_rows, all_compositions, digests, strata = [], [], [], []
    try:
        results = pool.map(analyze_stratum, tasks, chunksize=1) if pool else map(analyze_stratum, tasks)
        for index, result in enumerate(results, 1):
            all_rows.extend(result["rows"])
            all_compositions.extend(result["compositions"])
            digests.append(result["digest"])
            strata.append(dict(result["digest"], **{f"process_{k}":v for k,v in result["process_counts"].items()}))
            print(json.dumps(dict(strata_done=index, strata_total=len(tasks), elapsed_seconds=round(time.monotonic()-timer, 2))), flush=True)
    finally:
        if pool:
            pool.shutdown(wait=True, cancel_futures=True)
    write_csv(output / "gate_metrics.csv", all_rows)
    write_csv(output / "weighted_composition.csv", all_compositions)
    write_csv(output / "stratum_summary.csv", strata)
    base = [r for r in all_rows if r["panel"] == "base"]
    write_csv(output / "base_gate_metrics.csv", base)
    full = generation["mode"] == "gate" and len(profiles) == 540 and len(tasks) == 40
    decision = gate_decision(all_rows, full=full)
    summary = dict(**decision, started_utc=started, finished_utc=utc(), elapsed_seconds=time.monotonic()-timer,
                   generation_manifest=binding(args.input_dir / "run_manifest.json"), source_bindings=frozen,
                   profiles=len(profiles), generators=list(GENERATORS), endpoints=list(ENDPOINTS),
                   strata=len(tasks), metric_rows=len(all_rows), composition_rows=len(all_compositions),
                   all_endpoint_status_counts=dict(Counter(r["status"] for r in all_rows)),
                   score_controls_passed=True, seed_namespace="age-refocus-bootstrap-20261002",
                   independence="Fresh truth and bank; all old histories used only for proposal training",
                   outputs={p.name: binding(p) for p in sorted(output.iterdir())})
    verify_bindings(frozen)
    save_json(output / "reproducibility.json", digests)
    summary["outputs"]["reproducibility.json"] = binding(output / "reproducibility.json")
    save_json(output / "analysis_receipt.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--profiles")
    parser.add_argument("--bootstrap-replicates", type=int, default=1000)
    args = parser.parse_args()
    result = run(args)
    print(json.dumps({k:result[k] for k in ("status", "strata", "metric_rows", "primary_base_passes", "elapsed_seconds")}))


if __name__ == "__main__":
    main()
