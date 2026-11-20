#!/usr/bin/env python3
"""One finite target-only singleton-guard production/analysis pipeline."""
import datetime
import os
from pathlib import Path
import subprocess
import sys
for thread_variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[thread_variable]='1'
from scripts.run_mate_guard import dump, file_hash

ROOT=Path(__file__).resolve().parents[1]
RUN=Path('/data/codex/scratch/galaxias/mate_guard_20260920')
BASELINE=Path('/data/codex/scratch/galaxias/common_model_20260918/production/validate')
GATE=ROOT/'data/common_model/mate_guard_20260920/target_qualification.json'

def main():
    # Qualification artifacts intentionally share this precreated parent.
    RUN.mkdir(parents=True,exist_ok=True)
    receipt=RUN/'pipeline_receipt.json'
    if receipt.exists() or (RUN/'production').exists():
        raise SystemExit('Existing pipeline evidence: refusing duplicate dispatch')
    state=dict(status='running',pid=os.getpid(),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               source=str(ROOT),gate=file_hash(GATE),production_histories=529408)
    steps=[('production',['scripts/run_mate_guard.py','run','--mode','production','--workers','8',
                         '--baseline-dir',str(BASELINE),'--output-dir',str(RUN/'production'),'--gate',str(GATE)]),
           ('analysis',['scripts/analyze_mate_guard.py','--baseline-dir',str(BASELINE),
                        '--run-dir',str(RUN/'production'),'--output-dir',str(RUN/'analysis')])]
    for name,arguments in steps:
        state['step']=name;dump(receipt,state)
        with (RUN/(name+'.log')).open('w') as log:
            result=subprocess.run([sys.executable,*arguments],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            state.update(status='failed',returncode=result.returncode);dump(receipt,state)
            raise SystemExit(result.returncode)
    state.update(status='complete',step='complete',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    dump(receipt,state)

if __name__=='__main__':main()
