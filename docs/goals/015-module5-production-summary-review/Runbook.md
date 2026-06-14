# Runbook

## Constants

Goal 014 artifact:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production
```

Raw matched outcomes:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/matched_outcomes.csv
```

Raw matched SHA-256:

```text
ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727
```

Expected QC:

```text
row_count=279500
column_count=53
expected_replicates=100
source_intervention_units=2795
distinct_proposal_source_keys=780
seed_mismatches=0
```

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short --branch
git rev-list --left-right --count HEAD...origin/main
```

Expected:

```text
main
a96cfed24800823b77cbafeed5e9603e9dd6d33c
## main...origin/main
0 0
```

Only this Goal 015 packet should be uncommitted at start.

## Remote Artifact Verification

Run read-only:

```bash
ssh deep-server-ts 'bash -lc '"'"'
set -euo pipefail
ART=/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production
cd "$ART"
sha256sum -c checksums.sha256
python3 - << "PY"
import json
from pathlib import Path

root = Path(".")
summary = json.loads((root / "outputs/module5_100rep_production/inspection/inspection_summary.json").read_text())
for key in [
    "all_checks_passed",
    "row_count",
    "column_count",
    "expected_replicates",
    "source_intervention_units",
    "distinct_proposal_source_keys",
    "seed_mismatches",
    "source_identity",
    "replicate_coverage",
    "matched_pair_ids",
    "schema_columns",
    "production_attribution",
]:
    print(f"{key}={summary.get(key)}")
PY
'"'"''
```

## Local Tests

```bash
uv run pytest tests/test_module5_production_summary.py -q
uv run python scripts/summarize_module5_production.py --help
git diff --check
```

## Remote Summary Command

The exact command depends on the implemented CLI. It should be equivalent to:

```bash
uv run python scripts/summarize_module5_production.py \
  --matched-outcomes /data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/matched_outcomes.csv \
  --output-dir /data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/compact_summaries_goal015 \
  --expected-sha256 ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727 \
  --source-artifact /data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production \
  --source-execution-sha ddb8a6de583e85f170f46c9dec9b1246baa6dccc \
  --goal014-record-sha a96cfed24800823b77cbafeed5e9603e9dd6d33c \
  --run-id 20260614T031501Z-goal014-m5-100rep-production
```

Do not copy the raw matched outcomes locally.

## Pull-Back

Create local directory:

```bash
mkdir -p data/module5_production_summaries
```

Copy only:

```text
summary_metadata.json
qc_summary.csv
partition_endpoint_summary.csv
source_intervention_endpoint_summary.csv
direction_summary.csv
```

Verify file sizes:

```bash
du -h data/module5_production_summaries/*
```

Stop if any compact summary file exceeds 20 MB.

## Final Validation

```bash
uv run pytest tests/test_module5_production_summary.py -q
uv run python scripts/summarize_module5_production.py --help
git diff --check
```

Trailing whitespace:

```bash
rg -n "[ \t]+$" \
  docs/goals/015-module5-production-summary-review \
  docs/module5_production_summary_review.md \
  data/module5_production_summaries \
  src/galaxias_model/module5_production_summary.py \
  scripts/summarize_module5_production.py \
  tests/test_module5_production_summary.py
```

No matches expected. `rg` exit 1 with no matches is pass after confirming no
output.

Marker scan:

```bash
rg -n "production attribution|production-ready|manuscript|causal|claim|caused|demonstrates|proves|outputs/|matched_outcomes.csv" \
  docs/goals/015-module5-production-summary-review \
  docs/module5_production_summary_review.md \
  data/module5_production_summaries
```

Review hits manually. They should be source-path, boundary, stop-point, or
non-claim language only.

## Stage And Publish

Stage exact allowed files:

```bash
git add \
  docs/goals/015-module5-production-summary-review \
  docs/module5_production_summary_review.md \
  data/module5_production_summaries \
  src/galaxias_model/module5_production_summary.py \
  scripts/summarize_module5_production.py \
  tests/test_module5_production_summary.py
```

Verify:

```bash
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
```

Commit and push:

```bash
git commit -m "Summarize Module 5 production execution"
git push origin main
```

Do not stage raw outputs, remote artifacts, caches, or unrelated files.

## Wake-Up Content

Report:

- final branch, HEAD, status, and pushed commit SHA;
- remote artifact and checksum verification;
- compact summary command;
- compact summary file list and sizes;
- QC facts;
- descriptive patterns and interpretation questions;
- confirmation that no raw output was copied and no final claim was made;
- recommended Goal 016 shape.
