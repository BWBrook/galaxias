#!/usr/bin/env python3
"""Read-only identity, guard and analysis reconciliation after the finite run."""
import argparse,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_mate_guard import load_freeze,bindings,read,file_hash,dump

def verify(freeze_dir,run_dir,analysis_dir,output):
    assert not output.exists()
    freeze,sources,parameters,seeds=load_freeze(freeze_dir)
    manifest=json.loads((run_dir/'run_manifest.json').read_text())
    assert manifest['status']=='complete' and manifest['mode']=='production'
    assert manifest['source_count']==517 and manifest['history_count']==529408
    assert manifest['source_bindings']==bindings()
    assert manifest['freeze_manifest']==file_hash(freeze_dir/'freeze_manifest.json')
    for name,h in manifest['outputs'].items():assert file_hash(run_dir/name)==h,name
    amended=read(run_dir/'sources.csv').sort_values('source_ordinal')
    assert amended.source_id.tolist()==sources.source_id.tolist()
    for key in ('source_ordinal','configuration','restriction','K_L','K_R','PR011','PR033'):
        assert amended[key].equals(sources[key]),key
    newparams=read(run_dir/'parameter_values.csv.gz')
    pd.testing.assert_frame_equal(parameters,newparams,check_exact=True)
    raw_seeds=[];annual_rows=guard_rows=guard_violations=0
    for source in amended.to_dict('records'):
        ordinal=int(source['source_ordinal']);sid=source['source_id']
        raw=read(run_dir/'raw'/f'{ordinal:04d}.csv.gz')
        assert len(raw)==1024 and raw.source_id.eq(sid).all()
        raw_seeds.append(raw[['source_id','replicate_index','simulation_seed','environment_seed']])
        annual=read(run_dir/'annual'/f'{ordinal:04d}.csv.gz')
        assert len(annual)==1024*38
        assert not annual.duplicated(['replicate_index','year']).any()
        assert annual.year.between(1965,2002).all() and annual.replicate_index.between(1,1024).all()
        assert annual.groupby('replicate_index').size().eq(38).all()
        assert np.array_equal(annual.pre_breeding_A_total,annual.pre_breeding_A_L+annual.pre_breeding_A_R)
        assert np.array_equal(annual.mate_guard_active,annual.pre_breeding_A_total.lt(2))
        guard=annual.mate_guard_active
        violations=(annual.loc[guard,['recruitment_mean_total','realised_recruits_L','realised_recruits_R']].to_numpy()!=0).any(axis=1)
        guard_violations+=int(violations.sum());guard_rows+=int(guard.sum());annual_rows+=len(annual)
        assert np.array_equal(annual.N_L,annual.J_L+annual.A_L)
        assert np.array_equal(annual.N_R,annual.J_R+annual.A_R)
        assert np.array_equal(annual.N_total,annual.N_L+annual.N_R)
        ordered=annual.sort_values(['replicate_index','year'])
        previous=ordered.groupby('replicate_index').N_total.shift(1)
        assert not ((previous<=1)&(ordered.N_total>previous)).any(), 'zero/singleton total population grew'
        terminal=annual.loc[annual.year.eq(2002)].sort_values('replicate_index')
        raw=raw.sort_values('replicate_index')
        assert np.array_equal(terminal.N_total.to_numpy(),raw.endpoint_N_total_2002.to_numpy())
        assert np.array_equal(terminal.N_total.gt(0).to_numpy(),raw.endpoint_terminal_survival.to_numpy())
        assert np.array_equal(terminal.N_R.to_numpy(),raw.annual_N_R_2002.to_numpy())
    assert guard_violations==0
    actual=pd.concat(raw_seeds,ignore_index=True).sort_values(['source_id','replicate_index']).reset_index(drop=True)
    expected=seeds.sort_values(['source_id','replicate_index']).reset_index(drop=True)
    pd.testing.assert_frame_equal(actual,expected,check_exact=True)
    receipt=json.loads((analysis_dir/'mate_guard_analysis_receipt.json').read_text())
    assert receipt['status']=='complete' and receipt['mode']=='production'
    assert receipt['input_hashes']['amended_manifest']==file_hash(run_dir/'run_manifest.json')
    for name,h in receipt['outputs'].items():assert file_hash(analysis_dir/name)==h
    profile=read(analysis_dir/'rescored_profiles.csv')
    summary=read(run_dir/'source_summary.csv')
    keys=['source_id','q','observation_model'];paired=profile.merge(summary,on=keys,validate='one_to_one')
    assert len(paired)==6204
    for new,old in [('new_joint_lower95','joint_lower95'),('new_early_pattern_lower95','early_pattern_lower95'),
                    ('new_log_joint_mean','log_joint_mean'),('new_weighted_terminal_survival','weighted_terminal_survival')]:
        assert np.allclose(paired[new],paired[old],rtol=1e-12,atol=1e-14,equal_nan=True),(new,old)
    assert np.array_equal(paired.new_weight_qualified,paired.joint_mc_qualified)
    assert profile.loc[~profile.viable,'new_joint_mean'].eq(0).all()
    result=dict(status='verified',source_count=517,paired_histories=529408,annual_rows=annual_rows,
        guard_active_rows=guard_rows,nonzero_recruitment_when_guard_active=guard_violations,
        zero_or_singleton_total_population_rebounds=0,
        output_files_verified=len(manifest['outputs']),viability_failed_sources=int((~amended.viable).sum()),
        seed_design='Exact archived validation seed pairs reused; no fresh independent validation claim',
        run_manifest=file_hash(run_dir/'run_manifest.json'),analysis_receipt=file_hash(analysis_dir/'mate_guard_analysis_receipt.json'),
        source_files_verified=len(manifest['source_bindings']),script=file_hash(Path(__file__)))
    dump(output,result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('freeze-dir','run-dir','analysis-dir','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();print(json.dumps(verify(a.freeze_dir,a.run_dir,a.analysis_dir,a.output),indent=2))
