#!/usr/bin/env bash
set -euo pipefail
base=/data/codex/scratch/galaxias/age_linked_recovery_20261001
cd /data/codex/repos/galaxias-age-linked-20261001
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_CACHE_DIR=/data/codex/tmp/uv-cache
uv=/home/bwbrook/.local/bin/uv
finish() {
    code=$?
    printf '%s\n' "$code" > "$base/gate_exit_code.txt"
    date -u +%FT%TZ > "$base/gate_finished_utc.txt"
}
trap finish EXIT
date -u +%FT%TZ > "$base/gate_started_utc.txt"
"$uv" run --locked python - <<'PY'
from pathlib import Path
import json,hashlib
base=Path('/data/codex/scratch/galaxias/age_linked_recovery_20261001')
qualification=json.loads((base/'qualification/receipt.json').read_text())
replay=json.loads((base/'qualification_replay.json').read_text())
smoke=json.loads((base/'smoke_analysis/summary.json').read_text())
assert qualification['status']=='complete' and qualification['serial_parallel_exact']
assert replay['status']=='complete' and replay['serial_parallel_exact']
assert smoke['status']=='QUALIFICATION_SMOKE_ONLY' and smoke['score_controls_passed']
for rel,expected in qualification['source_bindings'].items():
    assert hashlib.sha256(Path(rel).read_bytes()).hexdigest()==expected['sha256'],rel
PY
printf 'generation\n' > "$base/gate_current_step.txt"
"$uv" run --locked python scripts/run_age_recovery.py --output-dir "$base/gate" --workers 16 > "$base/gate_generation.log" 2>&1
printf 'analysis\n' > "$base/gate_current_step.txt"
"$uv" run --locked python scripts/analyze_age_recovery.py --input-dir "$base/gate" --output-dir "$base/analysis" --workers 16 --bootstrap-replicates 1000 > "$base/gate_analysis.log" 2>&1
printf 'complete\n' > "$base/gate_current_step.txt"
