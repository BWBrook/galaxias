#!/usr/bin/env bash
set -euo pipefail
base=/data/codex/scratch/galaxias/age_linked_recovery_20261001
cd /data/codex/repos/galaxias-age-linked-20261001
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_CACHE_DIR=/data/codex/tmp/uv-cache
uv=/home/bwbrook/.local/bin/uv
date -u +%FT%TZ > "$base/qualification_started_utc.txt"
"$uv" run --locked python scripts/qualify_age_linked_runner.py --output-dir "$base/qualification" --workers 2 > "$base/qualification.log" 2>&1
"$uv" run --locked python scripts/run_age_recovery.py --output-dir "$base/smoke_serial" --truth-sources 2 --bank-sources 2 --replicates 1 --run-namespace qualification-20261001 --workers 1 > "$base/smoke_serial.log" 2>&1
"$uv" run --locked python scripts/run_age_recovery.py --output-dir "$base/smoke_parallel" --truth-sources 2 --bank-sources 2 --replicates 1 --run-namespace qualification-20261001 --workers 4 > "$base/smoke_parallel.log" 2>&1
"$uv" run --locked python - <<'PY' > "$base/qualification_replay.json"
from pathlib import Path
import json
base=Path('/data/codex/scratch/galaxias/age_linked_recovery_20261001')
a=json.loads((base/'smoke_serial/run_manifest.json').read_text())
b=json.loads((base/'smoke_parallel/run_manifest.json').read_text())
assert a['status']==b['status']=='complete'
assert a['content_sha256']==b['content_sha256']
assert a['source_bindings']==b['source_bindings']
print(json.dumps({'status':'complete','serial_parallel_exact':True,'content_sha256':a['content_sha256'],'nominal_site_histories':a['nominal_site_histories']+b['nominal_site_histories']},indent=2))
PY
"$uv" run --locked python scripts/analyze_age_recovery.py --input-dir "$base/smoke_parallel" --output-dir "$base/smoke_analysis" --workers 4 --profiles K2.5_rho0.25_q0.01_base,K20_rho4_q1_base --bootstrap-replicates 1000 > "$base/smoke_analysis.log" 2>&1
date -u +%FT%TZ > "$base/qualification_finished_utc.txt"
