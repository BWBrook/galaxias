#!/usr/bin/env python3
"""Describe frozen common-model witnesses; no simulation or new selection fit."""
from pathlib import Path
import hashlib
import json
import math

import numpy as np
import pandas as pd

from galaxias_model.abundance_detection import COMMON_EPISODE_FIELDS, common_history_log_likelihood

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'outputs/remote/common_model_20260918/production'
OUT = ROOT / 'data/common_model/interrogation_20260920'
KEY = ['source_id', 'q', 'observation_model']


def hashed(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return {'bytes': p.stat().st_size, 'sha256': h.hexdigest()}


def read_verified(phase, name, **kwargs):
    receipt_name = 'analysis_receipt.json' if phase == 'analysis' else 'run_manifest.json'
    receipt = json.loads((ARCHIVE / phase / receipt_name).read_text())
    p = ARCHIVE / phase / name
    assert hashed(p) == receipt['outputs'][name], p
    return pd.read_csv(p, float_precision='round_trip', **kwargs)


def weights(raw, q, model):
    logs = common_history_log_likelihood(raw[list(COMMON_EPISODE_FIELDS)], q, model)
    logs = np.where(raw.early_early_patterns_pass & raw.removals_valid, logs, -np.inf)
    finite = np.isfinite(logs)
    w = np.zeros(len(raw))
    if finite.any():
        w[finite] = np.exp(logs[finite] - logs[finite].max())
        w /= w.sum()
    return w, logs


def concentration(w):
    n = len(w)
    ess = 1 / np.square(w).sum() if w.sum() else 0.
    largest = float(w.max()) if ess else math.nan
    rse = math.sqrt(max(0., (n / ess - 1) / (n - 1))) if ess else math.nan
    return {'ess': ess, 'largest_weight': largest, 'relative_se': rse,
            'qualified': bool(ess >= 100 and largest <= .05 and rse <= .1)}


def mean_se(x, w):
    if not w.sum():
        return math.nan, math.nan
    mean = float(w @ x)
    se = math.sqrt(len(w) / (len(w) - 1) * float(np.square(w * (x - mean)).sum()))
    return mean, se


def quantiles(x, w):
    keep = w > 0
    if not keep.any():
        return [math.nan] * 3
    x, w = x[keep], w[keep]
    order = np.argsort(x, kind='stable')
    return x[order][np.minimum(np.searchsorted(np.cumsum(w[order]), [.025, .5, .975]), len(x)-1)].tolist()


def choose_cases(witnesses):
    # Treat probability-one floating-point residues as ties for illustration.
    witnesses = witnesses.assign(survival_order= witnesses.weighted_terminal_survival.clip(0,1).round(12))
    roles = []
    fixed = witnesses[witnesses.configuration.eq('base') & witnesses.q.eq(.02)
                      & witnesses.observation_model.eq('shared_quality')]
    for restriction in ['R_H', 'R_T', 'R_C', 'R_J']:
        g = fixed[fixed.restriction.eq(restriction)].sort_values(['survival_order', 'source_id'])
        assert len(g)
        for label, i in [('minimum', 0), ('middle', (len(g)-1)//2), ('maximum', len(g)-1)]:
            roles.append({'role': f'base_{restriction}_{label}', **g.iloc[i].to_dict()})
        g = witnesses[witnesses.restriction.eq(restriction) & witnesses.q.eq(.02)
                      & witnesses.observation_model.eq('shared_quality')].sort_values(['survival_order','source_id'])
        roles.append({'role': f'across_config_{restriction}_minimum', **g.iloc[0].to_dict()})
    for _, row in witnesses[witnesses.q.eq(.2) & witnesses.observation_model.eq('shared_quality')].sort_values('source_id').iterrows():
        roles.append({'role': f'high_q_{row.search_seed}', **row.to_dict()})
    return pd.DataFrame(roles)


def main():
    OUT.mkdir(exist_ok=True)
    summary = read_verified('analysis', 'validated_source_profiles.csv')
    wits = summary[summary.primary_profile & summary.joint_mc_qualified
                   & summary.early_pattern_lower95.ge(.5) & summary.joint_lower95.ge(1e-6)].copy()
    cases = choose_cases(wits)
    case_keys = set(cases[KEY].itertuples(index=False, name=None))
    columns = list(COMMON_EPISODE_FIELDS) + [
        'source_id', 'replicate_index', 'simulation_seed', 'environment_seed',
        'early_early_patterns_pass', 'removals_valid', 'endpoint_terminal_survival',
        'endpoint_N_total_2002', 'endpoint_extinction_time_censored',
        'ct005_N_L_1980', 'ct005_N_L_1983']
    wanted = set(wits.source_id)
    chunks = read_verified('validate', 'raw_histories.csv.gz', usecols=columns, chunksize=50000)
    raw = pd.concat([chunk[chunk.source_id.isin(wanted)] for chunk in chunks], ignore_index=True)
    groups = raw.groupby('source_id', sort=False)
    assert set(groups.groups) == wanted
    assert groups.size().eq(1024).all()
    assert not raw.duplicated(['source_id','replicate_index']).any()
    conditional, examples, profile_checks = [], [], []
    max_diff = 0.
    for row in wits.itertuples(index=False):
        part = groups.get_group(row.source_id).sort_values('replicate_index').reset_index(drop=True)
        w, logs = weights(part, row.q, row.observation_model)
        assert w.sum() > 0
        survive = part.endpoint_terminal_survival.to_numpy(float)
        assert set(np.unique(survive)) <= {0., 1.}
        assert np.array_equal(survive.astype(bool), part.endpoint_N_total_2002.to_numpy() > 0)
        survival = float(w @ survive)
        c = concentration(w)
        maximum = float(logs.max())
        logmean = maximum + math.log(float(np.exp(logs-maximum).sum())) - math.log(len(logs))
        diffs = [abs(survival-row.weighted_terminal_survival), abs(c['ess']-row.joint_weight_ess),
                 abs(logmean-row.log_joint_mean)]
        max_diff = max(max_diff, *diffs)
        np.testing.assert_allclose([survival,c['ess'],logmean],
                                   [row.weighted_terminal_survival,row.joint_weight_ess,row.log_joint_mean],
                                   rtol=1e-11,atol=1e-12)
        wc = w * survive
        if wc.sum(): wc /= wc.sum()
        cc = concentration(wc)
        ids = {k: getattr(row,k) for k in ['source_id','search_seed','configuration','restriction','q','observation_model']}
        for year in range(1997,2003):
            field = f'neg_N_total_{year+1}' if year < 2002 else 'endpoint_N_total_2002'
            x = part[field].to_numpy(float)
            mean, se = mean_se(x,wc)
            lo,med,hi = quantiles(x,wc)
            factual_total = float(w @ x)
            factual_refuge = float(getattr(row, f'weighted_N_R_{year}'))
            assert factual_total - factual_refuge >= -1e-8
            # Only at the terminal endpoint does total absence imply refuge=0
            # on every excluded (extinct) history. Earlier years cannot use this identity.
            endpoint_refuge = factual_refuge / survival if year == 2002 and survival > 0 else math.nan
            endpoint_lake = mean - endpoint_refuge if year == 2002 and survival > 0 else math.nan
            conditional.append({**ids,'state_year':year,'survey_year':year+1 if year<2002 else None,
                                'weighted_terminal_survival':survival,
                                'factual_weighted_total_mean':factual_total,
                                'factual_weighted_refuge_mean':factual_refuge,
                                'factual_weighted_lake_mean':max(0.,factual_total-factual_refuge),
                                'natural_total_mean_given_terminal_survival':mean,'ratio_mc_se':se,
                                'refuge_mean_given_terminal_survival_at_endpoint':endpoint_refuge,
                                'lake_mean_given_terminal_survival_at_endpoint':endpoint_lake,
                                'process_q025':lo,'process_median':med,'process_q975':hi,
                                'conditional_ess':cc['ess'],'conditional_largest_weight':cc['largest_weight'],
                                'conditional_relative_se':cc['relative_se'],'conditional_weight_qualified':cc['qualified']})
        profile_checks.append({**ids,'weighted_terminal_survival':survival,**c,
                               'survivor_conditional_ess':cc['ess'],'survivor_weight_qualified':cc['qualified']})
        if (row.source_id,row.q,row.observation_model) in case_keys:
            for outcome in [0.,1.]:
                eligible = np.isfinite(logs) & (survive == outcome)
                if not eligible.any(): continue
                # Positive log support is the support definition; rank before exponentiation.
                chosen = int(np.flatnonzero(eligible)[np.argmax(logs[eligible])])
                item = part.iloc[chosen].to_dict()
                outcome_mass = float(w[survive==outcome].sum())
                outcome_w = w * (survive == outcome)
                if outcome_w.sum(): outcome_w /= outcome_w.sum()
                outcome_c = concentration(outcome_w)
                examples.append({**ids,**{k:v for k,v in item.items() if k!='source_id'},
                                 'outcome':'survived_2002' if outcome else 'extinct_by_2002',
                                 'factual_weight':w[chosen], 'factual_log_weight_unnormalised':logs[chosen],
                                 'outcome_factual_weight_mass':outcome_mass,
                                 'outcome_conditional_ess':outcome_c['ess'],
                                 'outcome_weight_qualified':outcome_c['qualified'],
                                 'weight_within_outcome':w[chosen]/outcome_mass if outcome_mass else math.nan})
    cond = pd.DataFrame(conditional)
    cond.to_csv(OUT/'survivor_conditioned_natural_counts.csv.gz',index=False,float_format='%.17g')
    pd.DataFrame(profile_checks).to_csv(OUT/'profile_reconciliation.csv',index=False,float_format='%.17g')
    pd.DataFrame(examples).to_csv(OUT/'illustrative_histories.csv',index=False,float_format='%.17g')
    casecols = ['role',*KEY,'configuration','restriction','search_seed','K_R','PR011','PR033',
                'weighted_terminal_survival','weighted_terminal_survival_mc_se','joint_weight_ess',
                'joint_mc_relative_se','joint_largest_weight_share','early_pattern_lower95','joint_lower95']
    cases[casecols].to_csv(OUT/'selected_cases.csv',index=False,float_format='%.17g')
    annual=[]
    for row in cases.drop_duplicates(KEY).to_dict('records'):
        for year in range(1965,2003):
            annual.append({**{k:row[k] for k in KEY+['configuration','restriction']},'year':year,
                           'unconditional_refuge_mean':row[f'unconditional_N_R_{year}'],
                           'weighted_refuge_mean':row[f'weighted_N_R_{year}'],
                           'weighted_refuge_mean_mc_se':row[f'weighted_N_R_{year}_mc_se'],
                           'weighted_refuge_presence':row[f'weighted_N_R_presence_{year}']})
    pd.DataFrame(annual).to_csv(OUT/'case_annual_refuge.csv',index=False,float_format='%.17g')
    parameters=read_verified('validate','parameter_values.csv.gz')
    parameters[parameters.source_id.isin(cases.source_id)].to_csv(OUT/'case_parameters.csv',index=False,float_format='%.17g')
    # Per-scenario envelopes, not averaging across a selected parameter pool.
    cond.groupby(['configuration','restriction','q','observation_model','state_year']).agg(
        profile_count=('source_id','size'),qualified_conditional_profiles=('conditional_weight_qualified','sum'),
        conditional_mean_min=('natural_total_mean_given_terminal_survival','min'),
        conditional_mean_max=('natural_total_mean_given_terminal_survival','max'),
        conditional_ess_min=('conditional_ess','min')).to_csv(OUT/'conditional_count_envelopes.csv',float_format='%.17g')
    inputs = ['analysis/validated_source_profiles.csv','validate/raw_histories.csv.gz','validate/parameter_values.csv.gz']
    outputs = {p.name:hashed(p) for p in OUT.glob('*.csv*')}
    receipt={'status':'complete','new_histories':0,'qualified_source_profiles':len(wits),'unique_sources':len(wanted),
             'selection_roles':len(cases),'selected_source_profiles':len(cases.drop_duplicates(KEY)),
             'illustrative_histories':len(examples),'max_reconciliation_absolute_difference':max_diff,
             'survivor_conditional_qualified_profiles':int(pd.DataFrame(profile_checks).survivor_weight_qualified.sum()),
             'input_files':{name:hashed(ARCHIVE/name) for name in inputs},'outputs':outputs,
             'script':hashed(Path(__file__)),'plan':hashed(ROOT/'docs/common_model_interrogation_plan.md'),
             'interpretation':'Conditional natural-range count distributions are process spread given terminal survival and factual observations, not empirical population bounds. Original map unchanged.'}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['input_files','outputs']},indent=2))


if __name__=='__main__':
    main()
