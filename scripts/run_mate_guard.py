#!/usr/bin/env python3
"""Finite, fixed-witness singleton-guard experiment; never searches or resumes."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
import multiprocessing
from pathlib import Path
import platform
import shutil
import sys
import time
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_common_model_comparison import (IDENTITY, _resolved, _flatten_history,
    file_hash, history_seed, require, require_runtime_match, summarize_source, verify_archive)
from galaxias_model.mate_guard import intrinsic_viability, run_common_history

SCOPE = 'common_model_mate_guard'
FREEZE = ROOT / 'data/common_model/mate_guard_20260920'
PROTOCOL = ROOT / 'docs/common_model_mate_guard_protocol.md'
SEEDS = ['replicate_index', 'simulation_seed', 'environment_seed']
SOURCE_KEYS = [*IDENTITY, 'source_id']
ANNUAL = ['year', 'J_L', 'A_L', 'J_R', 'A_R', 'N_L', 'N_R', 'N_total',
          'pre_breeding_A_L', 'pre_breeding_A_R', 'pre_breeding_A_total',
          'recruitment_mean_total', 'realised_recruits_L', 'realised_recruits_R', 'mate_guard_active']


def dump(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
    temporary.replace(path)


def read(path):
    return pd.read_csv(path, float_precision='round_trip')


def csv(frame, path):
    # Deterministic gzip headers make byte-level serial/parallel checks useful.
    if str(path).endswith('.gz'):
        with Path(path).open('wb') as raw, gzip.GzipFile(filename='', fileobj=raw, mode='wb', mtime=0) as out:
            out.write(frame.to_csv(index=False).encode())
    else:
        frame.to_csv(path, index=False)


def runtime():
    return dict(python=sys.version, numpy=np.__version__, pandas=pd.__version__, platform=platform.platform())


def bindings():
    paths = sorted((ROOT / 'src').rglob('*.py'))
    paths += [ROOT / 'scripts' / name for name in ('run_common_model_comparison.py', 'run_mate_guard.py', 'analyze_mate_guard.py', 'qualify_mate_guard_replay.py', 'execute_mate_guard_pipeline.py')]
    paths += [ROOT / 'pyproject.toml', ROOT / 'uv.lock', PROTOCOL]
    paths += sorted(p for p in (ROOT / 'data/raw').rglob('*') if p.is_file())
    # Include the actual model-input directory independently of layout above.
    paths += sorted(p for p in (ROOT / 'data').iterdir() if p.is_file() and p.suffix in ('.csv', '.json'))
    return {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(set(paths))}


def freeze(baseline, output):
    require(not output.exists(), f'freeze exists: {output}')
    validation = baseline / 'validate'
    verify_archive(validation, phase='validate')
    profile_path = baseline / 'analysis/validated_source_profiles.csv'
    receipt_path = baseline / 'analysis/analysis_receipt.json'
    receipt = json.loads(receipt_path.read_text())
    verification_path = ROOT / 'data/common_model/production_verification.json'
    verification = json.loads(verification_path.read_text())
    require(verification['status']=='verified' and verification['analysis_receipt']==file_hash(receipt_path), 'original verification/analysis ancestry')
    require(verification['phase_manifests']['validate']==file_hash(validation/'run_manifest.json'), 'verified validation ancestry')
    expected = receipt['outputs']['validated_source_profiles.csv']
    require(file_hash(profile_path) == expected, 'original profile hash mismatch')
    profiles = read(profile_path)
    chosen = profiles.loc[profiles.primary_profile & profiles.joint_mc_qualified &
        profiles.early_pattern_lower95.ge(.5) & profiles.joint_lower95.ge(1e-6)].copy()
    ids = sorted(chosen.source_id.unique())
    require(len(ids) == 517 and len(chosen) == 1527, 'fixed witness set count changed')
    sources = read(validation / 'sources.csv').set_index('source_id').loc[ids].reset_index()
    require(sources.viable.all(), 'original witness not viable')
    sources.insert(0, 'source_ordinal', range(len(sources)))
    sources['original_viable'] = sources.viable
    params = read(validation / 'parameter_values.csv.gz')
    params = params.loc[params.source_id.isin(ids)].copy()
    require(params.groupby('source_id').size().eq(40).all() and len(params) == 517*40, 'parameter count')
    seed_parts = []
    for chunk in pd.read_csv(validation / 'raw_histories.csv.gz', usecols=['source_id', *SEEDS],
                             dtype={'simulation_seed':'uint64', 'environment_seed':'uint64'}, chunksize=100000):
        seed_parts.append(chunk.loc[chunk.source_id.isin(ids)])
    seeds = pd.concat(seed_parts).sort_values(['source_id', 'replicate_index']).reset_index(drop=True)
    require(len(seeds) == 529408 and not seeds.duplicated(['source_id','replicate_index']).any(), 'seed count/identity')
    for sid, rows in seeds.groupby('source_id'):
        require(rows.replicate_index.tolist() == list(range(1,1025)), 'replicate sequence')
        for row in rows.itertuples(index=False):
            require(int(row.simulation_seed) == history_seed(sid, 'validate', int(row.replicate_index), 'demographic'), 'demographic seed mismatch')
            require(int(row.environment_seed) == history_seed(sid, 'validate', int(row.replicate_index), 'environment'), 'environment seed mismatch')
    output.mkdir(parents=True)
    for name, frame in [('sources.csv',sources), ('parameter_values.csv.gz',params),
                        ('history_seeds.csv.gz',seeds), ('selected_profiles.csv',chosen)]:
        csv(frame, output/name)
    original_files = {str(p.relative_to(baseline)):file_hash(p) for p in
        [profile_path, receipt_path, validation/'run_manifest.json', validation/'sources.csv',
         validation/'parameter_values.csv.gz',validation/'raw_histories.csv.gz']}
    dump(output/'freeze_manifest.json', dict(scope=SCOPE, status='frozen', source_count=517,
        history_count=529408, original_files=original_files, original_verification=file_hash(verification_path), protocol=file_hash(PROTOCOL),
        outputs={p.name:file_hash(p) for p in sorted(output.iterdir())}))
    print(json.dumps({'frozen_sources':517,'history_count':529408,'directory':str(output)}),flush=True)


def load_freeze(directory):
    manifest = json.loads((directory/'freeze_manifest.json').read_text())
    require(manifest['status']=='frozen' and manifest['protocol']==file_hash(PROTOCOL),'freeze protocol/status drift')
    for name, expected in manifest['outputs'].items():
        require(file_hash(directory/name)==expected, f'freeze drift: {name}')
    sources = read(directory/'sources.csv')
    params = read(directory/'parameter_values.csv.gz')
    seeds = pd.read_csv(directory/'history_seeds.csv.gz',dtype={'simulation_seed':'uint64','environment_seed':'uint64'})
    require(manifest['source_count']==517 and manifest['history_count']==529408, 'frozen planned counts')
    require(len(sources)==517 and sources.source_id.is_unique and sources.source_ordinal.tolist()==list(range(517)), 'fixed source identities/count')
    require(len(params)==20680 and params.groupby('source_id').size().eq(40).all(), 'fixed parameter counts')
    require(not params.duplicated(['source_id','parameter_id']).any(), 'duplicate parameter')
    require(len(seeds)==529408 and seeds.groupby('source_id').size().eq(1024).all(), 'fixed history counts')
    require(not seeds.duplicated(['source_id','replicate_index']).any(), 'duplicate frozen history')
    require(set(seeds.source_id)==set(sources.source_id)==set(params.source_id), 'frozen membership mismatch')
    require(seeds.replicate_index.between(1,1024).all(), 'frozen replicate range')
    require(manifest['original_verification']==file_hash(ROOT/'data/common_model/production_verification.json'), 'original verification drift')
    return manifest,sources,params,seeds


def source_task(task):
    started = time.monotonic()
    source = task['source']
    params = _resolved(task['parameters'], task['data_dir'])
    viability = intrinsic_viability(params)
    updated = {k:v for k,v in source.items() if not k.startswith('viability_') and k!='viable'}
    for key,value in viability.items():
        name = 'viable' if key=='viable' else 'viability_'+key
        if isinstance(value,dict):
            updated[name+'_json']=json.dumps(value,sort_keys=True,separators=(',',':'))
        else:
            updated[name]=value
    ordinal = int(source['source_ordinal'])
    root = Path(task['output'])
    rows=[]
    annual_path=root/'annual'/f'{ordinal:04d}.csv.gz'
    with annual_path.open('wb') as rawout, gzip.GzipFile(filename='',fileobj=rawout,mode='wb',mtime=0) as out:
        for index, seed in enumerate(task['seeds']):
            result = run_common_history(params,source['restriction'],source['configuration'],
                                        int(seed['simulation_seed']),int(seed['environment_seed']))
            row={key:source[key] for key in SOURCE_KEYS}
            row.update(phase='mate_guard',**seed)
            row.update(_flatten_history(result))
            trajectory=result.trajectory_table
            for year in (1980,1983):
                state=trajectory.loc[trajectory.year.eq(year)].iloc[0]
                row[f'ct005_N_L_{year}']=float(state.N_L)
                row[f'ct005_C_L_{year}']=float(state.C_L)
            row['ct005_cross_product_change']=row['ct005_C_L_1983']*row['ct005_N_L_1980']-row['ct005_C_L_1980']*row['ct005_N_L_1983']
            row.update({f'annual_N_R_{int(y)}':float(n) for y,n in trajectory[['year','N_R']].itertuples(index=False,name=None)})
            rows.append(row)
            annual=trajectory[ANNUAL].copy()
            annual.insert(0,'replicate_index',seed['replicate_index'])
            # Source identity and exact seeds are losslessly joined via ordinal and replicate index.
            out.write(annual.to_csv(index=False,header=index==0).encode())
    raw=pd.DataFrame(rows)
    csv(raw,root/'raw'/f'{ordinal:04d}.csv.gz')
    summary=summarize_source(raw,bool(viability['viable']))
    csv(summary,root/'summaries'/f'{ordinal:04d}.csv')
    return dict(source=updated,ordinal=ordinal,histories=len(rows),seconds=time.monotonic()-started)


def run(args):
    freeze_manifest,sources,parameters,seeds=load_freeze(args.freeze_dir)
    baseline_manifest=json.loads((args.baseline_dir/'run_manifest.json').read_text())
    require(file_hash(args.baseline_dir/'run_manifest.json')==freeze_manifest['original_files']['validate/run_manifest.json'],'baseline ancestry')
    require_runtime_match(baseline_manifest)
    # All original archive and source bindings are checked before simulation.
    verify_archive(args.baseline_dir,phase='validate')
    if args.mode=='production':
        require(args.source_limit is None and args.replicates is None,'production cannot be resized')
        require(args.workers==8, 'production must use the qualified eight workers')
        require(args.gate is not None, 'production needs qualification receipt')
        gate=json.loads(args.gate.read_text())
        require(gate.get('status')=='qualified' and gate.get('source_bindings')==bindings(),'qualification gate/source drift')
        require(gate.get('freeze_manifest')==file_hash(args.freeze_dir/'freeze_manifest.json'),'gate freeze drift')
        require(gate.get('runtime')==runtime(),'qualification runtime drift')
        require(gate.get('approved_production_histories')==529408,'gate budget mismatch')
        require(gate.get('approved_auxiliary_ceiling')==15000, 'auxiliary ceiling mismatch')
        for name in ('independent_preflight','serial_parallel','analysis_smoke','baseline_replay','execution_budget'):
            evidence=gate.get(name,{})
            require(evidence.get('status') in ('passed','qualified','reserved'), f'missing or failed gate evidence: {name}')
            require(file_hash(Path(evidence['path']))==evidence['file_hash'], f'gate evidence drift: {name}')
    else:
        require(args.source_limit is not None and args.replicates is not None,'qualification needs explicit counts')
        require(1<=args.source_limit<=32 and 1<=args.replicates<=8,'qualification bound')
        # Deterministic spread over configuration/restriction, then ordinal.
        priority=sources.groupby(['configuration','restriction'],sort=True).head(1)
        sources=pd.concat([priority,sources]).drop_duplicates('source_id').head(args.source_limit).sort_values('source_ordinal')
        seeds=seeds.loc[seeds.replicate_index.le(args.replicates)&seeds.source_id.isin(sources.source_id)]
    require(1<=args.workers<=8,'worker bound')
    require(not args.output_dir.exists(), f'output already exists; no resume: {args.output_dir}')
    args.output_dir.mkdir(parents=True)
    for name in ('raw','annual','summaries'):
        (args.output_dir/name).mkdir()
    params=parameters.loc[parameters.source_id.isin(sources.source_id)]
    csv(params,args.output_dir/'parameter_values.csv.gz')
    csv(seeds,args.output_dir/'history_seeds.csv.gz')
    initial=dict(scope=SCOPE,mode=args.mode,status='running',source_count=len(sources),history_count=len(seeds),
        runtime=runtime(),workers=args.workers,source_bindings=bindings(),
        freeze_manifest=file_hash(args.freeze_dir/'freeze_manifest.json'),
        baseline_manifest=file_hash(args.baseline_dir/'run_manifest.json'),
        reserved_historical_executions=len(seeds),reserved_auxiliary_executions=3*len(sources),
        qualification_gate=file_hash(args.gate) if args.gate else None)
    dump(args.output_dir/'run_manifest.json',initial)
    tasks=[]
    for source in sources.to_dict('records'):
        sid=source['source_id']
        tasks.append(dict(source=source,parameters=params.loc[params.source_id.eq(sid)].to_dict('records'),
            seeds=seeds.loc[seeds.source_id.eq(sid),SEEDS].to_dict('records'),
            data_dir=str(ROOT/'data'),output=str(args.output_dir)))
    finished=[]
    start=time.monotonic()
    try:
        def collect(results):
            for result in results:
                finished.append(result)
                receipt=dict(status='running',completed_sources=len(finished),planned_sources=len(sources),
                    completed_histories=sum(r['histories'] for r in finished),planned_histories=len(seeds),
                    elapsed_seconds=time.monotonic()-start,last_source=result['source']['source_id'])
                dump(args.output_dir/'execution_receipt.json',receipt)
                print(json.dumps(receipt),flush=True)
        if args.workers==1:
            collect(map(source_task,tasks))
        else:
            with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
                collect(pool.map(source_task,tasks,buffersize=2*args.workers))
        csv(pd.DataFrame([r['source'] for r in finished]).sort_values('source_ordinal'),args.output_dir/'sources.csv')
        summary=pd.concat([read(args.output_dir/'summaries'/f'{int(r["ordinal"]):04d}.csv') for r in finished],ignore_index=True)
        csv(summary,args.output_dir/'source_summary.csv')
        require(sum(r['histories'] for r in finished)==len(seeds),'incomplete history total')
        require(bindings()==initial['source_bindings'],'source changed during run')
        initial.update(status='complete',elapsed_seconds=time.monotonic()-start,
            completed_histories=len(seeds),completed_sources=len(finished),
            outputs={str(p.relative_to(args.output_dir)):file_hash(p) for p in sorted(args.output_dir.rglob('*'))
                     if p.is_file() and p.name not in ('run_manifest.json','execution_receipt.json')})
        dump(args.output_dir/'run_manifest.json',initial)
        dump(args.output_dir/'execution_receipt.json',dict(status='complete',completed_sources=len(finished),
            completed_histories=len(seeds),elapsed_seconds=time.monotonic()-start,
            run_manifest=file_hash(args.output_dir/'run_manifest.json')))
    except BaseException as error:
        initial.update(status='failed',error=repr(error),completed_sources=len(finished),elapsed_seconds=time.monotonic()-start)
        dump(args.output_dir/'run_manifest.json',initial)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    freeze_parser=commands.add_parser('freeze')
    freeze_parser.add_argument('--baseline-dir',type=Path,required=True)
    freeze_parser.add_argument('--output-dir',type=Path,default=FREEZE)
    runner=commands.add_parser('run')
    runner.add_argument('--freeze-dir',type=Path,default=FREEZE)
    runner.add_argument('--baseline-dir',type=Path,required=True)
    runner.add_argument('--output-dir',type=Path,required=True)
    runner.add_argument('--mode',choices=['qualification','production'],required=True)
    runner.add_argument('--workers',type=int,default=8)
    runner.add_argument('--source-limit',type=int)
    runner.add_argument('--replicates',type=int)
    runner.add_argument('--gate',type=Path)
    args=parser.parse_args()
    if args.command=='freeze':
        freeze(args.baseline_dir,args.output_dir)
    else:
        run(args)

if __name__=='__main__':
    main()
