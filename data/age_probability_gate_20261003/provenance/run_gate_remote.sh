#!/usr/bin/env bash
set -euo pipefail
base=/data/codex/scratch/galaxias/age_probability_gate_20261003
clone=/data/codex/repos/galaxias-age-probability-20261003
uv=/home/bwbrook/.local/bin/uv
finish() {
    code=$?
    printf '%s\n' "$code" > "$base/gate_exit_code.txt"
    date -u +%FT%TZ > "$base/gate_finished_utc.txt"
}
trap finish EXIT
date -u +%FT%TZ > "$base/gate_started_utc.txt"
cd "$clone"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_CACHE_DIR=/data/codex/tmp/uv-cache
"$uv" run --locked python - <<'PY'
from pathlib import Path
import hashlib,json
base=Path('/data/codex/scratch/galaxias/age_probability_gate_20261003')
qual=json.loads((base/'qualification_receipt.json').read_text())
assert qual['status']=='complete' and qual['serial_parallel_exact'] and qual['focused_tests_passed']==42
assert (base/'qualification_exit_code.txt').read_text().strip()=='0'
record=json.loads((base/'source_snapshot.json').read_text())
for name,expected in record['files'].items():
    data=Path(name).read_bytes()
    assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],name
print('frozen source files verified:',len(record['files']))
PY
"$uv" run --locked python scripts/run_age_probability_gate.py run --proposal data/age_probability_gate_20261003/proposal.json --mode gate --truth-sources 512 --bank-sources 512 --replicates 6 --run-namespace age-probability-20261003-gate-v2 --output-dir "$base/gate" --workers 16 --qualification-manifest /data/codex/scratch/galaxias/age_linked_recovery_20261001/smoke_serial/run_manifest.json --qualification-manifest /data/codex/scratch/galaxias/age_lake_refocus_20261002/smoke_serial/run_manifest.json --qualification-manifest "$base/smoke_serial/run_manifest.json" > "$base/gate_generation.log" 2>&1
"$uv" run --locked python scripts/analyze_age_probability_gate.py --input-dir "$base/gate" --output-dir "$base/analysis" --workers 16 > "$base/gate_analysis.log" 2>&1
"$uv" run --locked python - <<'PY'
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
base=Path('/data/codex/scratch/galaxias/age_probability_gate_20261003')
generation=json.loads((base/'gate/run_manifest.json').read_text())
analysis=json.loads((base/'analysis/analysis_receipt.json').read_text())
assert generation['status']=='complete' and generation['nominal_site_histories']==147456
assert analysis['full_design'] and analysis['bootstrap_draws']==2000 and analysis['metric_rows']==1152
assert not analysis['actual_remaining_evidence_read']
record=json.loads((base/'source_snapshot.json').read_text())
for name,expected in record['files'].items():
    data=Path(name).read_bytes()
    assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],name
receipt={'status':'complete','completed_utc':datetime.now(timezone.utc).isoformat(),'source_files_reverified':len(record['files']),'generation_status':generation['status'],'analysis_status':analysis['status'],'nominal_site_histories':147456,'actual_remaining_evidence_read':False}
(base/'execution_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt))
PY
