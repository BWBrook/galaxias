#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_CACHE_DIR=/data/codex/tmp/uv-cache
export UV_LINK_MODE=copy
early_checkout=/data/codex/repos/galaxias-age-early-lake-20261004
early_output=/data/codex/scratch/galaxias/age_early_lake_20261004
early_uv=/home/bwbrook/.local/bin/uv
cd "$early_checkout"
trap 'early_exit=$?; printf "%s\n" "$early_exit" > "$early_output/gate_exit_code.txt"; date -u +%Y-%m-%dT%H:%M:%SZ > "$early_output/finished_utc.txt"' EXIT
date -u +%Y-%m-%dT%H:%M:%SZ > "$early_output/started_utc.txt"
"$early_uv" run --locked python - <<'PY'
from pathlib import Path
import hashlib,json
m=json.loads(Path('data/early_lake_mechanism_20261004/frozen_source_manifest.json').read_text())
for p,h in m['files'].items():
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h, p
q=json.loads(Path('/data/codex/scratch/galaxias/age_early_lake_20261004/qualification/qualification_receipt.json').read_text())
assert q['status']=='PASS'
print('Source snapshot and qualification receipt verified before production.',flush=True)
PY
"$early_uv" run --locked python scripts/run_age_early_lake.py --mode gate --output "$early_output/gate" --workers 16
"$early_uv" run --locked python scripts/analyze_age_early_lake.py --run "$early_output/gate" --output "$early_output/analysis" --workers 8
"$early_uv" run --locked python - <<'PY'
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
root=Path.cwd()
out=Path('/data/codex/scratch/galaxias/age_early_lake_20261004')
m=json.loads((root/'data/early_lake_mechanism_20261004/frozen_source_manifest.json').read_text())
for p,h in m['files'].items():
    assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h, p
g=json.loads((out/'gate/manifest.json').read_text())
a=json.loads((out/'analysis/recovery_gate.json').read_text())
assert g['status']=='complete' and g['accounting']['history_rows']==49152
assert not a['historical_observations_read']
r={'status':'COMPLETE','verified_utc':datetime.now(timezone.utc).isoformat(),'source_files_reverified':len(m['files']),
   'generation_status':g['status'],'analysis_decision':a['decision'],'historical_observations_read':False,
   'manifest_sha256':hashlib.sha256((out/'gate/manifest.json').read_bytes()).hexdigest(),
   'analysis_sha256':hashlib.sha256((out/'analysis/recovery_gate.json').read_bytes()).hexdigest()}
(out/'execution_receipt.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps(r,sort_keys=True),flush=True)
PY
