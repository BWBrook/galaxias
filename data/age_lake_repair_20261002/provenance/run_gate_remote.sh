#!/usr/bin/env bash
set -euo pipefail
base=/data/codex/scratch/galaxias/age_lake_refocus_20261002
clone=/data/codex/repos/galaxias-age-refocus-20261002
uv=/home/bwbrook/.local/bin/uv
finish() {
    code=$?
    printf '%s\n' "$code" > "$base/gate_exit_code.txt"
    date -u +%FT%TZ > "$base/gate_finished_utc.txt"
}
trap finish EXIT
date -u +%FT%TZ > "$base/gate_started_utc.txt"
cd "$clone"
python3 - <<'PY'
from pathlib import Path
import hashlib,json
base=Path('/data/codex/scratch/galaxias/age_lake_refocus_20261002')
assert (base/'qualification_exit_code.txt').read_text().strip()=='0'
qualification=json.loads((base/'qualification_receipt.json').read_text())
assert qualification['status']=='complete' and qualification['serial_parallel_exact'] and qualification['weighted_score_controls_passed']
seeds=json.loads((base/'seed_separation_preflight.json').read_text())
assert seeds['status']=='passed' and seeds['qualification_seed_overlap']==seeds['training_seed_overlap']==0
assert seeds['run_namespace']=='age-lake-refocus-20261002-gate'
assert seeds['proposal_sha256']==hashlib.sha256(Path('data/age_lake_repair_20261002/proposal.json').read_bytes()).hexdigest()
record=json.loads((base/'source_snapshot.json').read_text())
for name,expected in record['files'].items():
    data=Path(name).read_bytes()
    assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],name
print('qualified source snapshot and seed separation verified',flush=True)
PY
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_CACHE_DIR=/data/codex/tmp/uv-cache
"$uv" run --locked python scripts/run_age_historical_refocus.py run --proposal data/age_lake_repair_20261002/proposal.json --mode gate --truth-sources 512 --bank-sources 256 --replicates 2 --run-namespace age-lake-refocus-20261002-gate --output-dir "$base/gate" --workers 16 > "$base/gate_generation.log" 2>&1
"$uv" run --locked python scripts/analyze_age_historical_refocus.py --input-dir "$base/gate" --output-dir "$base/analysis" --workers 16 --bootstrap-replicates 1000 > "$base/gate_analysis.log" 2>&1
"$uv" run --locked python - <<'PY'
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
base=Path('/data/codex/scratch/galaxias/age_lake_refocus_20261002')
record=json.loads((base/'source_snapshot.json').read_text())
for name,expected in record['files'].items():
    data=Path(name).read_bytes()
    assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],name
generation=json.loads((base/'gate/run_manifest.json').read_text())
assert generation['status']=='complete' and generation['nominal_site_histories']==92160
analysis=json.loads((base/'analysis/analysis_receipt.json').read_text())
assert analysis['status'] in ('STOP_BEFORE_HISTORICAL_COMPARISON','CONDITIONAL_GO_REQUIRES_QUALIFIED_COLUMNS')
assert analysis['profiles']==540 and analysis['strata']==40 and analysis['metric_rows']==259200 and analysis['score_controls_passed']
def binding(p):
    return dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
for directory,receipt in (('gate',generation),('analysis',analysis)):
    for name,expected in receipt['outputs'].items():
        assert binding(base/directory/name)==expected,name
receipt=dict(status='complete',completed_utc=datetime.now(timezone.utc).isoformat(),source_files_verified=len(record['files']),generation_manifest=binding(base/'gate/run_manifest.json'),analysis_receipt=binding(base/'analysis/analysis_receipt.json'),gate_disposition=analysis['status'],primary_base_passes=analysis['primary_base_passes'],nominal_site_histories=92160)
(base/'execution_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt),flush=True)
PY
