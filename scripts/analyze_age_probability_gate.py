#!/usr/bin/env python3
"""Prospective probability calibration; actual remaining records are not read."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
import gzip
import json
import math
import multiprocessing as mp
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from scripts.run_age_recovery import binding, encoded, json_value, utc, verify_bindings
from scripts.analyze_age_recovery import _read_jsonl, _verify_generation_manifest, _verify_history_source_matches
from scripts.run_age_probability_gate import PROTOCOL, early_conditioning
from galaxias_model.age_sources import keyed_seed
from galaxias_model.age_recovery_observation import decision_profiles, exposures
from galaxias_model.age_probability_observation import generate_remaining, remaining_log_likelihood
from galaxias_model.age_probability_scores import (
    bounded_ratio_interval, probability_forecasts, source_bootstrap_counts, source_halves,
)

GENERATORS = ("poisson", "gamma_binary_quality")
QUALIFIED = ("CALIBRATED_AND_INFORMATIVE", "CALIBRATED_BUT_NO_INCREMENTAL_INFORMATION")
BINDING_PATHS = (
    "scripts/analyze_age_probability_gate.py", "scripts/run_age_probability_gate.py",
    "scripts/analyze_age_recovery.py", "scripts/run_age_recovery.py",
    "src/galaxias_model/age_probability_observation.py", "src/galaxias_model/age_probability_scores.py",
    "src/galaxias_model/age_recovery_observation.py", "src/galaxias_model/age_historical_refocus.py",
    "src/galaxias_model/age_sources.py", "docs/age_probability_gate_protocol.md",
    "uv.lock", "pyproject.toml",
)


def finite_json(value):
    value = json_value(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k:finite_json(v) for k,v in value.items()}
    if isinstance(value, list):
        return [finite_json(v) for v in value]
    return value


def save_json(path, value):
    path.write_text(json.dumps(finite_json(value),indent=2,sort_keys=True,allow_nan=False)+"\n")


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=fields,lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def quantiles(values):
    x = np.asarray(values,dtype=float)
    finite = x[np.isfinite(x)]
    return np.quantile(finite,[.025,.975]) if len(finite) else np.array([math.nan,math.nan])


def normalized(log_weights):
    logs = np.asarray(log_weights,dtype=float)
    weights = np.zeros(len(logs))
    finite = np.isfinite(logs)
    if finite.any():
        weights[finite] = np.exp(logs[finite]-logs[finite].max())
        weights /= weights.sum()
    return weights


def source_array(values, indices, n_sources, replicates):
    return np.bincount(indices,weights=values,minlength=n_sources)/replicates


def role_data(all_sources, histories, role, replicates):
    sources = sorted([s for s in all_sources if s["role"] == role],key=lambda s:s["index"])
    ids = [s["source_id"] for s in sources]
    index = {sid:i for i,sid in enumerate(ids)}
    complete = [h for h in histories if h["namespace"] == role and h["status"] == "complete"
                and h["conditioning"]["total"] is not None]
    logs = np.asarray([h["conditioning"]["total"]-h["proposal_log_density_ratio"] for h in complete])
    indices = np.asarray([index[h["source_id"]] for h in complete],dtype=int)
    blocks = [f"{s['ledger_timing']}:{int(s['march_retention'])}" for s in sources]
    weights = normalized(logs)
    total_by_source = np.bincount(indices,weights=weights,minlength=len(ids))
    return dict(sources=sources,ids=ids,indices=indices,blocks=blocks,rows=complete,logs=logs,
                weights=weights,loss=np.asarray([h["loss_2002"] for h in complete],dtype=bool),
                source_ess=1/np.square(total_by_source).sum() if weights.sum() else 0.,
                largest_share=total_by_source.max() if weights.sum() else math.nan,
                planned_replicates=replicates)


def calibration_interval(truth, bootstrap_counts, probabilities, bootstrap_probabilities, mask):
    """Cluster interval with missing predictions bounded instead of dropped."""
    weights = truth["weights"]*mask
    mass = weights.sum()
    y = truth["loss"].astype(float)
    if mass <= 0:
        return dict(mass=0.,residual=math.nan,ci=np.array([math.nan,math.nan]),finite_fraction=0.,boundary=False)
    w = bootstrap_counts[:,truth["indices"]]*weights[None,:]
    denominator = w.sum(axis=1)
    valid = denominator > 0
    lower = np.full(len(denominator),np.nan)
    upper = np.full(len(denominator),np.nan)
    lower[valid] = np.sum(w[valid]*(y[None,:]-np.nan_to_num(bootstrap_probabilities[valid],nan=1.)),axis=1)/denominator[valid]
    upper[valid] = np.sum(w[valid]*(y[None,:]-np.nan_to_num(bootstrap_probabilities[valid],nan=0.)),axis=1)/denominator[valid]
    interval = np.array([quantiles(lower)[0],quantiles(upper)[1]])
    event = np.full(len(denominator),np.nan)
    event[valid] = (w[valid]@y)/denominator[valid]
    event_ci = quantiles(event)
    boundary = not np.isfinite(event_ci).all() or event_ci[0] <= 0 or event_ci[1] >= 1
    if boundary:
        # These are the absolute bounded contributions, not normalized weights.
        absolute = np.exp(truth["logs"])*mask
        n = len(truth["ids"])
        den = source_array(absolute,truth["indices"],n,truth["planned_replicates"])
        num = source_array(absolute*y,truth["indices"],n,truth["planned_replicates"])
        low_pred = source_array(absolute*np.nan_to_num(probabilities,nan=0.),truth["indices"],n,truth["planned_replicates"])
        high_pred = source_array(absolute*np.nan_to_num(probabilities,nan=1.),truth["indices"],n,truth["planned_replicates"])
        eci = bounded_ratio_interval(num,den,truth["blocks"],alpha=.05/3)
        pci_low = bounded_ratio_interval(low_pred,den,truth["blocks"],alpha=.05/3)
        pci_high = bounded_ratio_interval(high_pred,den,truth["blocks"],alpha=.05/3)
        conservative = np.array([eci[0]-pci_high[1],eci[1]-pci_low[0]])
        interval = np.array([min(interval[0],conservative[0]),max(interval[1],conservative[1])])
    residual = float(np.dot(weights,y-np.nan_to_num(probabilities,nan=.5))/mass)
    return dict(mass=float(mass),residual=residual,ci=interval,
                finite_fraction=float(valid.mean()),boundary=bool(boundary))


def log_score(y, probabilities):
    with np.errstate(divide="ignore",invalid="ignore"):
        return np.where(y,np.log(probabilities),np.log1p(-probabilities))


def proper_score_gains(truth, bootstrap_counts, forecast, baseline):
    y, weights = truth["loss"],truth["weights"]
    p,p0 = forecast["p"],float(baseline["p"][0])
    active = weights > 0
    full_log = log_score(y,p)
    base_log = log_score(y,p0)
    contradicted = bool(np.any(active & (~np.isfinite(full_log) | ~np.isfinite(base_log))))
    result = dict(log_gain=math.nan,log_gain_low=math.nan,log_gain_high=math.nan,
                  brier_gain=math.nan,brier_gain_low=math.nan,brier_gain_high=math.nan,
                  proper_score_contradiction=contradicted,positive_log_gain=False,positive_brier_gain=False)
    if contradicted:
        return result
    with np.errstate(invalid="ignore"):
        delta_log = np.where(active,full_log-base_log,0.)
        delta_brier = np.where(active,(p0-y)**2-(p-y)**2,0.)
    result.update(log_gain=float(np.dot(weights,delta_log)),brier_gain=float(np.dot(weights,delta_brier)))
    bw = bootstrap_counts[:,truth["indices"]]*weights[None,:]
    den = bw.sum(axis=1)
    pb = forecast["bootstrap_probabilities"]
    p0b = baseline["bootstrap_probabilities"][:,0,None]
    lfull,lbase = log_score(y[None,:],pb),log_score(y[None,:],p0b)
    valid = (den > 0) & np.all((bw == 0) | (np.isfinite(lfull) & np.isfinite(lbase)),axis=1)
    logs = np.full(len(den),np.nan)
    briers = np.full(len(den),np.nan)
    with np.errstate(invalid="ignore"):
        logs[valid] = np.sum(np.where(bw[valid] > 0,bw[valid]*(lfull[valid]-lbase[valid]),0.),axis=1)/den[valid]
        briers[valid] = np.sum(np.where(bw[valid] > 0,bw[valid]*((p0b[valid]-y)**2-(pb[valid]-y)**2),0.),axis=1)/den[valid]
    # Missing/contradictory bootstrap scores cannot create an information pass.
    if np.mean(valid) >= .95:
        lc,bc = quantiles(logs),quantiles(briers)
        result.update(log_gain_low=float(lc[0]),log_gain_high=float(lc[1]),
                      brier_gain_low=float(bc[0]),brier_gain_high=float(bc[1]),
                      positive_log_gain=bool(lc[0] > 0),positive_brier_gain=bool(bc[0] > 0))
    return result


def assess(truth, truth_bootstrap, forecast, baseline):
    p,weights = forecast["p"],truth["weights"]
    precision = (forecast["supported"] & (forecast["finite_fraction"] >= .95)
                 & (np.diff(forecast["interval"],axis=1)[:,0] <= .20)
                 & (forecast["half_gap"] <= .05))
    precision_mass = float(np.dot(weights,precision))
    supported_mass = float(np.dot(weights,forecast["supported"]))
    overall = calibration_interval(truth,truth_bootstrap,p,forecast["bootstrap_probabilities"],np.ones(len(p),dtype=bool))
    ci = overall["ci"]
    calibrated = bool(np.isfinite(ci).all() and ci[0] >= -.05 and ci[1] <= .05 and overall["finite_fraction"] >= .95)
    # Fixed edges keep each conditioning event independent of validation labels.
    groups = np.searchsorted(np.asarray([.25,.5,.75]),p,side="right")
    groups[~np.isfinite(p)] = -1
    reliability = []
    resolved = sum(np.sum(weights[groups == group]) > 0 for group in range(4)) > 1
    for group in range(4):
        mask = groups == group
        if not np.any(mask):
            continue
        summary = calibration_interval(truth,truth_bootstrap,p,forecast["bootstrap_probabilities"],mask)
        interval = summary["ci"]
        passed = bool(np.isfinite(interval).all() and interval[0] >= -.10 and interval[1] <= .10
                      and summary["finite_fraction"] >= .95)
        required = bool(resolved and summary["mass"] > 0)
        if required:
            calibrated &= passed
        reliability.append(dict(group=group,lower_edge=group*.25,upper_edge=(group+1)*.25,
                                truth_weight=summary["mass"],required_for_gate=required,
                                mean_forecast=float(np.dot(weights[mask],p[mask])/weights[mask].sum()),
                                observed_loss=float(np.dot(weights[mask],truth["loss"][mask])/weights[mask].sum()),
                                residual=summary["residual"],residual_low=float(interval[0]),residual_high=float(interval[1]),
                                finite_bootstrap=summary["finite_fraction"],boundary_bound=summary["boundary"],passed=passed))
    gains = proper_score_gains(truth,truth_bootstrap,forecast,baseline)
    computation = precision_mass >= .95 and supported_mass >= .95 and overall["finite_fraction"] >= .95
    positive_contradiction = np.any((weights > 0) & (((p == 0) & truth["loss"]) | ((p == 1) & ~truth["loss"])))
    computation &= not positive_contradiction and not gains["proper_score_contradiction"]
    if not computation:
        status = "UNASSESSABLE"
    elif not calibrated:
        decisive = ci[1] < -.05 or ci[0] > .05
        decisive |= any(r["required_for_gate"] and (r["residual_high"] < -.10 or r["residual_low"] > .10) for r in reliability)
        status = "CALIBRATION_FAILED" if decisive else "UNASSESSABLE_CALIBRATION_PRECISION"
    else:
        status = "CALIBRATED_AND_INFORMATIVE" if gains["positive_log_gain"] and gains["positive_brier_gain"] else "CALIBRATED_BUT_NO_INCREMENTAL_INFORMATION"
    result = dict(status=status,qualified=status in QUALIFIED,computationally_assessed=bool(computation),
                  calibration_equivalence_pass=bool(calibrated),precision_truth_weight=precision_mass,
                  supported_truth_weight=supported_mass,calibration_residual=overall["residual"],
                  calibration_low=float(ci[0]),calibration_high=float(ci[1]),
                  calibration_bootstrap_finite=overall["finite_fraction"],truth_boundary_bound=overall["boundary"],
                  conditional_calibration_resolved=resolved,occupied_forecast_groups=len(reliability),
                  required_forecast_groups=sum(r["required_for_gate"] for r in reliability),
                  low_mass_forecast_group_weight=sum(r["truth_weight"] for r in reliability if resolved and not r["required_for_gate"]),
                  forecast_boundary_bound_weight=float(np.dot(weights,forecast["boundary_bound_used"])),
                  positive_weight_zero_probability_contradiction=bool(positive_contradiction),
                  **gains)
    return result,reliability,precision


def composition(data, metadata):
    rows,w = data["rows"],data["weights"]
    def mean(field):
        return float(np.dot(w,[row[field] for row in rows])) if w.sum() else math.nan
    return dict(metadata,role=data["sources"][0]["role"],planned_sources=len(data["ids"]),
                compatible_histories=len(rows),source_ess=data["source_ess"],largest_source_share=data["largest_share"],
                loss_2002=mean("loss_2002"),lake_mean_2002=mean("lake_2002"),refuge_mean_2002=mean("refuge_2002"),
                breeding_pair=mean("terminal_pair"),same_compartment_pair=mean("terminal_same_compartment_pair"),
                age1plus10=mean("terminal_age1plus10"))


def selection_diagnostic(histories,role,metadata):
    rows = [h for h in histories if h["namespace"] == role and h.get("through_2002_diagnostic")]
    logs = np.asarray([(-math.inf if h["through_2002_diagnostic"]["log_score"] is None else
                       h["through_2002_diagnostic"]["log_score"]-h["proposal_log_density_ratio"]) for h in rows])
    weights = normalized(logs)
    excluded = np.asarray([h["status"] != "complete" for h in rows],dtype=bool)
    loss = np.asarray([h["through_2002_diagnostic"]["loss_2002"] for h in rows],dtype=bool)
    return dict(metadata,role=role,valid_through_2002=len(rows),excluded_later=int(excluded.sum()),
                raw_exclusion_fraction=float(excluded.mean()) if len(rows) else math.nan,
                E_weighted_exclusion_fraction=float(np.dot(weights,excluded)) if weights.sum() else math.nan,
                E_weighted_loss_before_future_exclusion=float(np.dot(weights,loss)) if weights.sum() else math.nan)


def analyze_group(task):
    sources,histories,profiles,n_bootstrap,replicates,means,output_dir = task
    cell = sources[0]["cell"]
    stratum = sources[0]["index_stratum"]
    metadata = dict(cell_id=sources[0]["cell_id"],index_stratum=stratum,maximum_age=cell["maximum_age"],restriction=cell["restriction"])
    truth,bank = [role_data(sources,histories,role,replicates) for role in ("truth","bank")]
    for role in (truth,bank):
        for row in role["rows"]:
            recalculated = early_conditioning(row["features"],means)["total"]
            if not math.isclose(recalculated,row["conditioning"]["total"],rel_tol=1e-12,abs_tol=1e-10):
                raise ValueError("saved conditioning differs from declared E")
    crows = [composition(data,metadata) for data in (truth,bank)]
    selection = [selection_diagnostic(histories,role,metadata) for role in ("truth","bank")]
    metrics,reliability = [],[]
    base_metadata = dict(metadata,truth_source_ess=truth["source_ess"],bank_source_ess=bank["source_ess"],
                         truth_compatible_histories=len(truth["rows"]),bank_compatible_histories=len(bank["rows"]))
    if not len(truth["rows"]) or not len(bank["rows"]):
        for profile in profiles:
            for generator in GENERATORS:
                metrics.append(dict(base_metadata,profile_id=profile["profile_id"],generator=generator,
                                    status="UNASSESSABLE_NO_COMPATIBLE_HISTORY",qualified=False))
        return metrics,reliability,crows,selection,[]
    t_counts,b_counts = [source_bootstrap_counts(data["blocks"],n_bootstrap,
                       keyed_seed("probability-bootstrap-20261003",cell["maximum_age"],stratum,role,bits=128))
                       for data,role in ((truth,"truth"),(bank,"bank"))]
    halves = source_halves(bank["ids"],bank["blocks"],keyed_seed("probability-halves-20261003",cell["maximum_age"],stratum,bits=128))
    def forecast(log_likelihood):
        return probability_forecasts(bank["logs"],log_likelihood,bank["loss"],bank["indices"],bank["blocks"],b_counts,halves,replicates=replicates)
    baseline = forecast(np.zeros((1,len(bank["rows"]))))
    details_path = Path(output_dir)/f"forecasts_{cell['maximum_age']}_{cell['restriction']}_{stratum}.jsonl.gz"
    detail_count = 0
    with gzip.open(details_path,"wt") as detail_stream:
        for profile in profiles:
            tcreek,_,tbinary = exposures([h["features"] for h in truth["rows"]],profile)
            bcreek,_,bbinary = exposures([h["features"] for h in bank["rows"]],profile)
            identities = [(h["source_id"],h["replicate"],profile["K"],profile["rho"]) for h in truth["rows"]]
            for generator in GENERATORS:
                observations = generate_remaining(tcreek,tbinary,identities,q=profile["q"],generator=generator)
                blocks = remaining_log_likelihood(bcreek,bbinary,**observations,q=profile["q"],generator=generator)
                remaining = blocks["full"]
                if np.any(remaining > 1e-10):
                    raise ValueError("remaining probability mass exceeds one")
                remaining = np.minimum(remaining,0.)
                result = forecast(remaining)
                assessed,bins,precision = assess(truth,t_counts,result,baseline)
                row = dict(base_metadata,profile_id=profile["profile_id"],generator=generator,
                           K=profile["K"],rho=profile["rho"],q=profile["q"],
                           E_only_loss=float(baseline["p"][0]),E_only_loss_low=float(baseline["interval"][0,0]),
                           E_only_loss_high=float(baseline["interval"][0,1]),**assessed)
                metrics.append(row)
                reliability.extend(dict(metadata,profile_id=profile["profile_id"],generator=generator,**b) for b in bins)
                for i,h in enumerate(truth["rows"]):
                    detail_stream.write(encoded(finite_json(dict(metadata,profile_id=profile["profile_id"],generator=generator,
                        source_id=h["source_id"],replicate=h["replicate"],loss=bool(truth["loss"][i]),
                        truth_weight=float(truth["weights"][i]),late_count=int(observations["late_counts"][i]),
                        insurance=observations["insurance_observed"][i].tolist(),probability=float(result["p"][i]),
                        probability_low=float(result["interval"][i,0]),probability_high=float(result["interval"][i,1]),
                        finite_bootstrap=float(result["finite_fraction"][i]),half_gap=float(result["half_gap"][i]),
                        bank_source_ess=float(result["source_ess"][i]),largest_source_share=float(result["largest_source_share"][i]),
                        bounded_interval_used=bool(result["boundary_bound_used"][i]),precision_assessed=bool(precision[i]))))+"\n")
                    detail_count += 1
    return metrics,reliability,crows,selection,[dict(path=details_path.name,rows=detail_count,**binding(details_path))]


def run(args):
    if not 1 <= args.workers <= 16:
        raise ValueError("workers must be in 1..16")
    input_dir = args.input_dir.resolve()
    sources = _read_jsonl(input_dir/"source_banks.jsonl")
    manifest = _verify_generation_manifest(input_dir,sources)
    if manifest["full_design"] and args.bootstrap != 2000:
        raise ValueError("the production gate requires 2000 source bootstrap draws")
    histories = _read_jsonl(input_dir/"histories.jsonl.gz",compressed=True)
    _verify_history_source_matches(histories,sources,manifest)
    if Counter(h["status"] for h in histories) != Counter(manifest["history_status_counts"]):
        raise ValueError("generation status counts disagree")
    profiles = [p for p in decision_profiles() if p["panel"] == "base"]
    if args.profiles:
        if manifest["full_design"]:
            raise ValueError("production may not select profiles")
        wanted = args.profiles.split(",")
        profiles = [p for p in profiles if p["profile_id"] in wanted]
        if len(profiles) != len(set(wanted)):
            raise ValueError("unknown profile")
    frozen = {name:binding(ROOT/name) for name in BINDING_PATHS}
    output = args.output_dir.resolve()
    output.mkdir(parents=True,exist_ok=False)
    timer = time.monotonic()
    groups = sorted({(s["cell_id"],s["index_stratum"]) for s in sources})
    tasks = []
    for cid,stratum in groups:
        group_sources = [s for s in sources if (s["cell_id"],s["index_stratum"]) == (cid,stratum)]
        group_histories = [h for h in histories if (h["cell_id"],h["index_stratum"]) == (cid,stratum)]
        tasks.append((group_sources,group_histories,profiles,args.bootstrap,manifest["replicates_per_source"],
                      manifest["historical_lake_means"],str(output)))
    metrics,reliability,compositions,selections,details = [],[],[],[],[]
    pool = ProcessPoolExecutor(max_workers=args.workers,mp_context=mp.get_context("spawn")) if args.workers > 1 else None
    try:
        results = pool.map(analyze_group,tasks,chunksize=1,buffersize=args.workers) if pool else map(analyze_group,tasks)
        for index,(m,r,c,s,d) in enumerate(results,1):
            metrics.extend(m);reliability.extend(r);compositions.extend(c);selections.extend(s);details.extend(d)
            print(json.dumps(dict(groups_done=index,groups_total=len(tasks),elapsed_seconds=round(time.monotonic()-timer,2))),flush=True)
    finally:
        if pool:
            pool.shutdown(wait=True,cancel_futures=True)
    write_csv(output/"gate_metrics.csv",metrics)
    write_csv(output/"reliability.csv",reliability)
    write_csv(output/"conditional_composition.csv",compositions)
    write_csv(output/"future_feasibility_selection.csv",selections)
    primary = [r for r in metrics if r["maximum_age"] == 6]
    qualified = [r for r in primary if r["qualified"]]
    status = ("QUALIFICATION_SMOKE_ONLY" if not manifest["full_design"] else
              "CONDITIONAL_GO_QUALIFIED_PROBABILITY_COLUMNS" if qualified else "STOP_FINAL_BOUNDED_ATTEMPT")
    receipt = dict(status=status,completed_utc=utc(),elapsed_seconds=time.monotonic()-timer,
                   generation_manifest=binding(input_dir/"run_manifest.json"),source_bindings=frozen,
                   full_design=manifest["full_design"],bootstrap_draws=args.bootstrap,profiles=len(profiles),
                   generators=list(GENERATORS),groups=len(tasks),metric_rows=len(metrics),forecast_files=details,
                   primary_status_counts=dict(Counter(r["status"] for r in primary)),
                   all_status_counts=dict(Counter(r["status"] for r in metrics)),
                   qualified_primary_columns=[{k:r[k] for k in ("cell_id","index_stratum","profile_id","generator","status")} for r in qualified],
                   actual_remaining_evidence_read=False,actual_historical_probability_computed=False,
                   outputs={p.name:binding(p) for p in sorted(output.iterdir())})
    verify_bindings(frozen)
    save_json(output/"analysis_receipt.json",receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--workers",type=int,default=1)
    parser.add_argument("--bootstrap",type=int,default=2000)
    parser.add_argument("--profiles",default="")
    result = run(parser.parse_args())
    print(json.dumps({k:result[k] for k in ("status","metric_rows","primary_status_counts","elapsed_seconds")},sort_keys=True))


if __name__ == "__main__":
    main()
