#!/usr/bin/env bash
set -euo pipefail
base=/data/codex/scratch/galaxias/age_lake_refocus_20261002
clone=/data/codex/repos/galaxias-age-refocus-20261002
uv=/home/bwbrook/.local/bin/uv
finish() {
    code=$?
    printf '%s\n' "$code" > "$base/qualification_exit_code.txt"
    date -u +%FT%TZ > "$base/qualification_finished_utc.txt"
}
trap finish EXIT
date -u +%FT%TZ > "$base/qualification_started_utc.txt"
test "$(sha256sum "$base/source_snapshot.tar.gz" | cut -d' ' -f1)" = 5488493b1a426a363c6f3ae8cff112cd05b44bac9a95238aac0365ed496da26a
tar -xzf "$base/source_snapshot.tar.gz" -C "$clone"
cd "$clone"
python3 - <<'PY'
from pathlib import Path
import hashlib,json
record=json.loads(Path('/data/codex/scratch/galaxias/age_lake_refocus_20261002/source_snapshot.json').read_text())
for name,expected in record['files'].items():
    data=Path(name).read_bytes()
    assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],name
print('all source snapshot files verified:',len(record['files']))
PY
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export UV_CACHE_DIR=/data/codex/tmp/uv-cache
"$uv" sync --locked --python 3.14 > "$base/setup.log" 2>&1
"$uv" run --locked pytest -q tests/test_age_historical_refocus.py tests/test_age_historical_refocus_runner.py tests/test_age_historical_refocus_analysis.py tests/test_age_refocus_scores.py > "$base/qualification_tests.log" 2>&1
for mode in serial parallel; do
    workers=1
    if [ "$mode" = parallel ]; then workers=16; fi
    "$uv" run --locked python scripts/run_age_historical_refocus.py run --proposal data/age_lake_repair_20261002/proposal.json --mode smoke --truth-sources 2 --bank-sources 2 --replicates 1 --run-namespace age-lake-refocus-20261002-qualification --output-dir "$base/smoke_$mode" --workers "$workers" > "$base/smoke_$mode.log" 2>&1
done
"$uv" run --locked python scripts/analyze_age_historical_refocus.py --input-dir "$base/smoke_parallel" --output-dir "$base/smoke_analysis" --profiles K5_rho1_q0.1_base,K20_rho4_q1_high_information_corner --workers 16 > "$base/smoke_analysis.log" 2>&1
"$uv" run --locked python - <<'PY'
from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
base=Path('/data/codex/scratch/galaxias/age_lake_refocus_20261002')
manifests=[json.loads((base/f'smoke_{mode}/run_manifest.json').read_text()) for mode in ('serial','parallel')]
assert all(m['status']=='complete' and m['nominal_site_histories']==240 for m in manifests)
assert manifests[0]['content_sha256']==manifests[1]['content_sha256']
assert manifests[0]['outputs']['source_banks.jsonl']==manifests[1]['outputs']['source_banks.jsonl']
analysis=json.loads((base/'smoke_analysis/analysis_receipt.json').read_text())
assert analysis['status']=='QUALIFICATION_SMOKE_ONLY' and analysis['score_controls_passed'] and analysis['metric_rows']==960
record=json.loads((base/'source_snapshot.json').read_text())
for name,expected in record['files'].items():
    data=Path(name).read_bytes()
    assert len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],name
receipt={'status':'complete','completed_utc':datetime.now(timezone.utc).isoformat(),'serial_parallel_exact':True,'nominal_site_histories':480,'source_files_verified':len(record['files']),'content_sha256':manifests[0]['content_sha256'],'history_status_counts':manifests[0]['history_status_counts'],'tests':'26 focused tests','weighted_score_controls_passed':True,'analysis_metric_rows':960}
(base/'qualification_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps(receipt))
PY
