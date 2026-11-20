#!/usr/bin/env python3
"""Descriptive fixed-witness readout, with every q/law/configuration kept separate."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_common_model_comparison import file_hash

KEY=['source_id','q','observation_model']
CELL=['configuration','restriction','q','observation_model']

def read(p):return pd.read_csv(p,float_precision='round_trip')

def summarize(freeze_dir,run_dir,analysis_dir,output_dir):
    receipt_path=analysis_dir/'mate_guard_analysis_receipt.json'
    receipt=json.loads(receipt_path.read_text())
    assert receipt['status']=='complete' and receipt['mode']=='production'
    for name,h in receipt['outputs'].items():assert file_hash(analysis_dir/name)==h
    assert receipt['input_hashes']['amended_manifest']==file_hash(run_dir/'run_manifest.json')
    freeze=json.loads((freeze_dir/'freeze_manifest.json').read_text())
    assert file_hash(freeze_dir/'selected_profiles.csv')==freeze['outputs']['selected_profiles.csv']
    sources=read(run_dir/'sources.csv')
    selected=read(freeze_dir/'selected_profiles.csv')
    rescored=read(analysis_dir/'rescored_profiles.csv')
    paired=read(analysis_dir/'paired_profiles.csv')
    terminal=paired.loc[paired.endpoint.eq('terminal_survival')].copy()
    assert len(sources)==517 and len(selected)==1527 and len(rescored)==6204 and len(terminal)==6204
    all_profiles=rescored.merge(sources[['source_id','K_R']],on='source_id',validate='many_to_one')
    all_profiles=all_profiles.merge(terminal[KEY+['old_weighted','old_weighted_mc_se','new_weighted','new_weighted_mc_se','paired_difference','paired_mc_se','status','old_weight_qualified','new_invalid_removal_positive_support_count']],on=KEY,validate='one_to_one')
    all_profiles['old_compatible']=(all_profiles.old_early_pattern_lower95.ge(.5)&all_profiles.old_joint_lower95.ge(1e-6)&all_profiles.old_weight_qualified)
    all_profiles['new_compatible']=(all_profiles.new_early_pattern_lower95.ge(.5)&all_profiles.new_joint_lower95.ge(1e-6)&all_profiles.new_weight_qualified)
    all_profiles['new_survivor_qualified']=(all_profiles.new_survivor_weight_ess.ge(100)&all_profiles.new_survivor_weight_relative_se.le(.1)&all_profiles.new_survivor_largest_weight_share.le(.05))
    all_profiles['capacity_stratum']=all_profiles.K_R.lt(20).map({True:'K_R<20',False:'K_R>=20'})
    retained=selected[KEY].merge(all_profiles,on=KEY,validate='one_to_one')
    transitions=read(analysis_dir/'compatibility_transition_summary.csv')
    transition_slice=transitions.loc[transitions.early_cutoff.eq(.5)&transitions.joint_cutoff.eq(1e-6)&~transitions.observation_model.eq('independent_quality')&transitions.old_status.eq('qualified-compatible')]
    status_counts={str(k):int(v) for k,v in transition_slice.groupby('new_status').source_count.sum().items()}
    assert sum(status_counts.values())==1527
    assert status_counts.get('qualified-compatible',0)==int(retained.new_compatible.sum())
    assert len(retained)==1527
    def cells(frame):
        result=[]
        for key,group in frame.groupby(CELL,sort=True):
            compatible=group.loc[group.new_compatible]
            tail=compatible.loc[compatible.new_survivor_qualified]
            defined=group.loc[group.status.eq('defined')]
            result.append(dict(zip(CELL,key),**{
                'fixed_profile_count':len(group),'old_compatible_profiles':int(group.old_compatible.sum()),
                'retained_compatible_profiles':int((group.old_compatible&group.new_compatible).sum()),
                'lost_compatible_profiles':int((group.old_compatible&~group.new_compatible).sum()),
                'gained_compatible_profiles':int((~group.old_compatible&group.new_compatible).sum()),
                'new_viable_profiles':int(group.viable.sum()),
                'new_compatible_profiles':len(compatible),'new_compatible_K_R_below20':int(compatible.K_R.lt(20).sum()),
                'new_compatible_K_R_at_least20':int(compatible.K_R.ge(20).sum()),
                'new_compatible_survivor_qualified_profiles':len(tail),
                'undefined_paired_profiles':int((~group.status.eq('defined')).sum()),
                'paired_survival_difference_min':defined.paired_difference.min(),
                'paired_survival_difference_max':defined.paired_difference.max(),
                'own_survival_min_compatible':compatible.new_weighted_terminal_survival.min(),
                'own_survival_max_compatible':compatible.new_weighted_terminal_survival.max(),
                'own_survival_min_compatible_tail_qualified':tail.new_weighted_terminal_survival.min(),
                'own_survival_max_compatible_tail_qualified':tail.new_weighted_terminal_survival.max()}))
        return pd.DataFrame(result)
    output_dir.mkdir(parents=True,exist_ok=False)
    retained.to_csv(output_dir/'original_witness_retention.csv',index=False)
    cells(retained).to_csv(output_dir/'original_witness_cells.csv',index=False)
    cells(all_profiles).to_csv(output_dir/'all_fixed_source_cells.csv',index=False)
    all_profiles.to_csv(output_dir/'all_fixed_source_profiles.csv',index=False)
    # Row totals describe multiplicity in the fixed grid, never model probabilities.
    summary=dict(status='complete',fixed_sources=517,original_witness_profiles=1527,
        retained_witness_profiles=int(retained.new_compatible.sum()),
        no_longer_qualified_witness_profiles=int((~retained.new_compatible).sum()),
        original_witness_new_status_counts=status_counts,
        original_witness_sources_retaining_at_least_one_profile=int(retained.loc[retained.new_compatible,'source_id'].nunique()),
        viability_failed_sources=int((~sources.viable).sum()),
        original_witness_undefined_paired_profiles=int((~retained.status.eq('defined')).sum()),
        all_fixed_source_primary_compatible_profiles=int((all_profiles.new_compatible&~all_profiles.observation_model.eq('independent_quality')).sum()),
        interpretation='Fixed-source/profile sensitivity counts only; no probabilities, mechanism ranking, q comparison or global exclusion. Includes approved initialization change.')
    (output_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    outputs={p.name:file_hash(p) for p in sorted(output_dir.iterdir())}
    (output_dir/'summary_receipt.json').write_text(json.dumps(dict(status='complete',script=file_hash(Path(__file__)),analysis_receipt=file_hash(receipt_path),freeze_manifest=file_hash(freeze_dir/'freeze_manifest.json'),run_manifest=file_hash(run_dir/'run_manifest.json'),outputs=outputs),indent=2)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('freeze-dir','run-dir','analysis-dir','output-dir'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();print(json.dumps(summarize(a.freeze_dir,a.run_dir,a.analysis_dir,a.output_dir),indent=2))
