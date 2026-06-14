# Runbook

## Constants

Frozen source SHA:

```text
ddb8a6de583e85f170f46c9dec9b1246baa6dccc
```

Expected production facts:

```text
expected_row_count=279500
source_intervention_unit_count=2795
distinct_proposal_source_key_count=780
source_context_count=15
expected_replicates=100
artifact_verification_rows=15
workers=32
```

## Local Starting Commands

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
ddb8a6de583e85f170f46c9dec9b1246baa6dccc
## main...origin/main
0 0
```

Only this Goal 014 packet should be uncommitted.

## Local 100-Replicate Plan-Only Check

```bash
TMPDIR_GOAL014="$(mktemp -d /tmp/galaxias-goal014-plan.XXXXXX)"
uv run python scripts/run_module5_25rep_rehearsal.py \
  --plan-only \
  --output-dir "$TMPDIR_GOAL014" \
  --run-id goal014-local-plan-only \
  --replicates 100
python3 - <<'PY' "$TMPDIR_GOAL014"
import csv
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
plan = json.loads((root / "rehearsal_plan.json").read_text(encoding="utf-8"))
artifacts = list(csv.DictReader((root / "artifact_verification.csv").open(newline="", encoding="utf-8")))
print(f"expected_row_count={plan['expected_row_count']}")
print(f"source_intervention_unit_count={plan['source_intervention_unit_count']}")
print(f"distinct_proposal_source_key_count={plan['distinct_proposal_source_key_count']}")
print(f"source_context_count={plan['source_context_count']}")
print(f"artifact_verification_rows={len(artifacts)}")
print(f"all_artifacts_verified={all(row['verified'].lower() == 'true' for row in artifacts)}")
PY
```

Required:

```text
expected_row_count=279500
source_intervention_unit_count=2795
distinct_proposal_source_key_count=780
source_context_count=15
artifact_verification_rows=15
all_artifacts_verified=True
```

## Remote Preflight

Use `deep-server-ts`.

Recommended variable setup:

```bash
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${RUN_STAMP}-goal014-m5-100rep-production"
SESSION="galaxias-m5-prod-${RUN_STAMP}"
REMOTE_REPO="/data/codex/repos/galaxias-goal014-m5-100rep-production-${RUN_ID}"
REMOTE_SCRATCH="/data/codex/scratch/galaxias/module5_100rep_production_${RUN_ID}"
REMOTE_ARTIFACT="/data/codex/artifacts/galaxias/module5_100rep_production_${RUN_ID}"
SOURCE_SHA="ddb8a6de583e85f170f46c9dec9b1246baa6dccc"
```

Preflight probe:

```bash
ssh deep-server-ts 'bash -lc '"'"'
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
hostname
whoami
df -h /data
git --version
uv --version
python3 --version
tmux -V
'"'"''
```

Fresh checkout pattern:

```bash
ssh deep-server-ts 'bash -lc '"'"'
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
SOURCE_SHA="ddb8a6de583e85f170f46c9dec9b1246baa6dccc"
REMOTE_REPO="REPLACE_WITH_REMOTE_REPO"
if [ -e "$REMOTE_REPO" ]; then
  echo "remote repo path already exists: $REMOTE_REPO" >&2
  exit 2
fi
git clone git@github.com:BWBrook/galaxias.git "$REMOTE_REPO"
cd "$REMOTE_REPO"
git checkout --detach "$SOURCE_SHA"
git rev-parse HEAD
git status --short --branch
uv run python scripts/run_module5_25rep_rehearsal.py \
  --plan-only \
  --output-dir /tmp/galaxias-goal014-remote-plan \
  --run-id goal014-remote-plan-only \
  --replicates 100 \
  --artifact-path-preference remote
'"'"''
```

If GitHub remote URL differs, use the repo's configured `origin` from the
local action repo. Stop if clone or checkout fails.

## Production Execution Command

The exact remote script should create the source, scratch, and artifact paths,
run inside `tmux`, and write timing/exit files.

The core execution command inside the remote checkout is:

```bash
uv run python scripts/run_module5_25rep_rehearsal.py \
  --output-dir "$REMOTE_SCRATCH/outputs/module5_100rep_production" \
  --run-id "$RUN_ID" \
  --replicates 100 \
  --workers 32 \
  --artifact-path-preference remote
```

Then inspect:

```bash
uv run python scripts/inspect_module5_25rep_rehearsal.py \
  --rehearsal-dir "$REMOTE_SCRATCH/outputs/module5_100rep_production" \
  --inspection-dir "$REMOTE_SCRATCH/outputs/module5_100rep_production/inspection"
```

Copy or sync the durable outputs into:

```text
$REMOTE_ARTIFACT
```

Generate:

```bash
find "$REMOTE_ARTIFACT" -type f -printf "%p %s\n" | sort > "$REMOTE_ARTIFACT/artifact_inventory.txt"
(cd "$REMOTE_ARTIFACT" && find . -type f ! -name checksums.sha256 -print0 | sort -z | xargs -0 sha256sum > checksums.sha256)
(cd "$REMOTE_ARTIFACT" && sha256sum -c checksums.sha256)
```

## Required Inspection Facts

Inspection summary must report:

```text
all_checks_passed=True
row_count=279500
column_count=53
expected_replicates=100
source_intervention_units=2795
distinct_proposal_source_keys=780
seed_mismatches=0
source_identity=True
replicate_coverage=True
matched_pair_ids=True
schema_columns=True
production_attribution=False
```

Expected partition counts:

```text
headline/persistent_joint_cause=106000
headline/climbing_only=47000
headline/transient_perfect_storm=100000
diagnostic_sidecar/climbing_only_no_trout_pressure=23500
negative_reference/habitat_only_null=1500
negative_reference/trout_only=1500
```

## Local Report Publication

Create:

```text
docs/module5_100rep_production_execution_report.md
```

Update:

```text
docs/goals/014-module5-100rep-production-execution/Log.md
```

Run:

```bash
git diff --check
rg -n "[ \t]+$" docs/goals/014-module5-100rep-production-execution docs/module5_100rep_production_execution_report.md
rg -n "production attribution|production-ready|manuscript|causal|claim|outputs/|commit|push|tmux|deep-server" docs/goals/014-module5-100rep-production-execution docs/module5_100rep_production_execution_report.md
```

Stage only:

```bash
git add \
  docs/goals/014-module5-100rep-production-execution \
  docs/module5_100rep_production_execution_report.md
```

Verify staged files:

```bash
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
```

Expected staged files:

```text
docs/goals/014-module5-100rep-production-execution/Goal.md
docs/goals/014-module5-100rep-production-execution/Log.md
docs/goals/014-module5-100rep-production-execution/Plan.md
docs/goals/014-module5-100rep-production-execution/Runbook.md
docs/module5_100rep_production_execution_report.md
```

Commit and push:

```bash
git commit -m "Record Module 5 production execution"
git push origin main
```

Do not stage generated outputs.

## Commands Not Authorized

Do not run:

```bash
git push --force
git commit --amend
git reset
git rebase
```

Do not run interpretation notebooks, manuscript commands, figure export, PR
creation, or any command that changes source code or scientific contracts.

## Wake-Up Content

Report:

- final branch, HEAD, status, and pushed commit SHA;
- source SHA used for remote execution;
- remote alias, run ID, tmux session, source/scratch/artifact paths;
- local and remote plan-only facts;
- artifact verification summary;
- execution duration and worker count;
- inspection facts;
- raw matched-output path, size, and SHA-256;
- checksum verification result;
- local committed path list;
- deviations and risks;
- recommended Goal 015 shape.
