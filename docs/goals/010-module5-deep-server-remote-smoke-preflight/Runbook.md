# Runbook

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short=12 HEAD
git status --short --branch
```

Stop before editing or remote commands if dirty state differs from the
expected Goal 005/006/007/008/009 surface plus this Goal 010 packet described
in `Plan.md`.

## Local Artifact Check

```bash
SMOKE_PARAMETER_VALUES="outputs/remote/module4_observation_sensitivity_20260522T101942Z/baseline_current_seed20260410/parameter_values.csv.gz"
EXPECTED_SHA="49e080a23dcaca2f29874c0e3825bd806406f494b2db046307a84a74e8673c4c"

ls -lh "$SMOKE_PARAMETER_VALUES"
shasum -a 256 "$SMOKE_PARAMETER_VALUES"
```

Expected SHA-256:

```text
49e080a23dcaca2f29874c0e3825bd806406f494b2db046307a84a74e8673c4c
```

Stop if the file is missing or the hash differs.

## Run Identifiers

Example setup:

```bash
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${RUN_STAMP}-goal010-m5-remote-smoke"
REMOTE_ALIAS="deep-server-ts"
REMOTE_REPO="/data/codex/repos/galaxias-goal010-remote-smoke-${RUN_ID}"
REMOTE_SCRATCH="/data/codex/scratch/galaxias/module5_remote_smoke_${RUN_ID}"
REMOTE_ARTIFACT="/data/codex/artifacts/galaxias/module5_remote_smoke_${RUN_ID}"
SESSION="galaxias-m5-smoke-${RUN_STAMP}"
```

If `deep-server-ts` fails, try `utas-ubuntu` once and record the exact failure.

## Remote Access Probe

```bash
ssh "$REMOTE_ALIAS" 'bash -lc '"'"'
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
echo "host=$(hostname)"
echo "user=$(whoami)"
echo "pwd=$(pwd)"
uname -a
df -h /data
command -v uv
uv --version
python3 --version
tmux -V
'"'"
```

Stop if both authorized aliases fail or if `uv`/`tmux` are unavailable.

## Remote Directory Creation

```bash
ssh "$REMOTE_ALIAS" "bash -lc 'set -euo pipefail; mkdir -p \"$REMOTE_REPO\" \"$REMOTE_SCRATCH\" \"$REMOTE_ARTIFACT/logs\"'"
```

Use only paths under `/data/codex/repos`, `/data/codex/scratch`, and
`/data/codex/artifacts`.

## Source Mirror

Mirror the current local dirty source surface:

```bash
rsync -a --delete \
  --exclude '/.venv/' \
  --exclude '/.pytest_cache/' \
  --exclude '__pycache__/' \
  --exclude '/outputs/' \
  /Users/bwbrook/papers/galaxias/ \
  "$REMOTE_ALIAS:$REMOTE_REPO/"
```

Then copy only the required ignored smoke input artifact:

```bash
ssh "$REMOTE_ALIAS" "bash -lc 'mkdir -p \"$REMOTE_REPO/outputs/remote/module4_observation_sensitivity_20260522T101942Z/baseline_current_seed20260410\"'"

rsync -a "$SMOKE_PARAMETER_VALUES" \
  "$REMOTE_ALIAS:$REMOTE_REPO/outputs/remote/module4_observation_sensitivity_20260522T101942Z/baseline_current_seed20260410/parameter_values.csv.gz"
```

Verify remote source state and artifact hash:

```bash
LOCAL_HEAD="$(git rev-parse HEAD)"
ssh "$REMOTE_ALIAS" "bash -lc 'set -euo pipefail; cd \"$REMOTE_REPO\"; git rev-parse HEAD; git status --short --branch'"
ssh "$REMOTE_ALIAS" "bash -lc 'cd \"$REMOTE_REPO\" && sha256sum \"$SMOKE_PARAMETER_VALUES\"'"
```

Stop if remote HEAD differs from local HEAD, if remote status is not the
accepted dirty surface plus Goal 010, or if the artifact hash differs.

## Remote Smoke Script

Create a script on the remote host under `$REMOTE_ARTIFACT` with this shape.
Adapt only the expanded paths; do not alter repo code.

```bash
ssh "$REMOTE_ALIAS" "cat > '$REMOTE_ARTIFACT/run_module5_remote_smoke.sh' <<'REMOTE_SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

REMOTE_REPO="__REMOTE_REPO__"
REMOTE_SCRATCH="__REMOTE_SCRATCH__"
REMOTE_ARTIFACT="__REMOTE_ARTIFACT__"
SMOKE_DIR="$REMOTE_SCRATCH/outputs/module5_remote_smoke_goal010"
LOG_DIR="$REMOTE_ARTIFACT/logs"
STATUS_FILE="$REMOTE_ARTIFACT/smoke.exit"
SUMMARY_FILE="$REMOTE_ARTIFACT/smoke_summary.json"
CHECKSUM_FILE="$REMOTE_ARTIFACT/checksums.sha256"

mkdir -p "$SMOKE_DIR" "$LOG_DIR" "$REMOTE_ARTIFACT/outputs"
rm -f "$STATUS_FILE"

{
  date -u +%Y-%m-%dT%H:%M:%SZ
  hostname
  uname -a
  cd "$REMOTE_REPO"
  git rev-parse HEAD
  git status --short --branch
  uv --version
  python3 --version
  sha256sum outputs/remote/module4_observation_sensitivity_20260522T101942Z/baseline_current_seed20260410/parameter_values.csv.gz

  uv run python scripts/run_module5_real_proposal_dry_run.py \
    --output-dir "$SMOKE_DIR" \
    --replicates 5

  uv run python scripts/inspect_module5_real_proposal_dry_run.py \
    --dry-run-dir "$SMOKE_DIR" \
    --inspection-dir "$SMOKE_DIR/inspection" \
    --expected-replicates 5

  uv run python - <<'PY'
import json
from pathlib import Path

import pandas as pd

smoke_dir = Path("__REMOTE_SCRATCH__") / "outputs" / "module5_remote_smoke_goal010"
outcomes = pd.read_csv(smoke_dir / "matched_outcomes.csv")
summary = json.loads((smoke_dir / "inspection" / "inspection_summary.json").read_text())
provenance = json.loads((smoke_dir / "provenance.json").read_text())

expected_replicates = 5
replicate_sets = (
    outcomes.groupby("intervention_id")["stochastic_replicate_id"]
    .apply(lambda values: sorted(set(int(value) for value in values)))
    .to_dict()
)
bad_replicates = {
    key: value
    for key, value in replicate_sets.items()
    if value != list(range(expected_replicates))
}
seed_mismatches = int(
    (
        outcomes["baseline_stochastic_seed"].astype(str)
        != outcomes["intervention_stochastic_seed"].astype(str)
    ).sum()
)
result = {
    "row_count": int(len(outcomes)),
    "proposal_count": int(outcomes["proposal_id"].nunique()),
    "intervention_count": int(outcomes["intervention_id"].nunique()),
    "expected_replicates": expected_replicates,
    "bad_replicate_sets": bad_replicates,
    "seed_mismatches": seed_mismatches,
    "inspection_all_checks_passed": bool(summary.get("all_checks_passed")),
    "production_attribution": bool(provenance.get("production_attribution")),
}
if result["row_count"] != 65:
    raise SystemExit(result)
if result["proposal_count"] != 5:
    raise SystemExit(result)
if result["intervention_count"] != 13:
    raise SystemExit(result)
if result["bad_replicate_sets"]:
    raise SystemExit(result)
if result["seed_mismatches"] != 0:
    raise SystemExit(result)
if not result["inspection_all_checks_passed"]:
    raise SystemExit(result)
if result["production_attribution"]:
    raise SystemExit(result)
Path("__REMOTE_ARTIFACT__", "smoke_summary.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
PY

  rsync -a "$SMOKE_DIR/" "$REMOTE_ARTIFACT/outputs/module5_remote_smoke_goal010/"
  find "$REMOTE_ARTIFACT" -type f ! -name "checksums.sha256" -print0 | sort -z | xargs -0 sha256sum > "$CHECKSUM_FILE.tmp"
  mv "$CHECKSUM_FILE.tmp" "$CHECKSUM_FILE"
} > "$LOG_DIR/smoke.log" 2>&1

echo 0 > "$STATUS_FILE"
REMOTE_SCRIPT"
```

After writing the script, replace placeholders:

```bash
ssh "$REMOTE_ALIAS" "python3 - <<'PY'
from pathlib import Path
path = Path('$REMOTE_ARTIFACT/run_module5_remote_smoke.sh')
text = path.read_text()
text = text.replace('__REMOTE_REPO__', '$REMOTE_REPO')
text = text.replace('__REMOTE_SCRATCH__', '$REMOTE_SCRATCH')
text = text.replace('__REMOTE_ARTIFACT__', '$REMOTE_ARTIFACT')
path.write_text(text)
path.chmod(0o755)
PY"
```

If writing the remote script is error-prone, stop and report rather than
editing project source code.

## Tmux Smoke Run

Start the smoke:

```bash
ssh "$REMOTE_ALIAS" "bash -lc 'set -euo pipefail; tmux new-session -d -s \"$SESSION\" \"bash $REMOTE_ARTIFACT/run_module5_remote_smoke.sh; echo \\$? > $REMOTE_ARTIFACT/tmux_command.exit; exec bash\"'"
```

Poll only for bounded smoke completion:

```bash
ssh "$REMOTE_ALIAS" "bash -lc 'for i in {1..120}; do if test -f \"$REMOTE_ARTIFACT/smoke.exit\"; then exit 0; fi; if test -f \"$REMOTE_ARTIFACT/tmux_command.exit\"; then code=\$(cat \"$REMOTE_ARTIFACT/tmux_command.exit\"); exit \"\${code:-1}\"; fi; sleep 5; done; exit 124'"
```

If the poll times out or exits nonzero, capture:

```bash
ssh "$REMOTE_ALIAS" "bash -lc 'tmux capture-pane -pt \"$SESSION\" -S -200 || true; tail -200 \"$REMOTE_ARTIFACT/logs/smoke.log\" || true; ls -R \"$REMOTE_ARTIFACT\" || true'"
```

Then wake Galaxias with the exact failure.

## Remote Evidence Reads

After completion:

```bash
ssh "$REMOTE_ALIAS" "bash -lc 'cat \"$REMOTE_ARTIFACT/smoke.exit\"; cat \"$REMOTE_ARTIFACT/smoke_summary.json\"; tail -80 \"$REMOTE_ARTIFACT/logs/smoke.log\"; find \"$REMOTE_ARTIFACT\" -maxdepth 4 -type f | sort; du -sh \"$REMOTE_ARTIFACT\" \"$REMOTE_SCRATCH\"'"
```

Do not copy `matched_outcomes.csv` into the local repo. It may remain remote
under `$REMOTE_ARTIFACT/outputs/`.

## Local Report And Validation

Create `docs/module5_remote_smoke_preflight.md`, then run:

```bash
git status --short --branch
git diff --check
rg -n "[ \t]+$" docs/goals/010-module5-deep-server-remote-smoke-preflight docs/module5_remote_smoke_preflight.md
rg -n "production attribution|production-ready|deep-server|tmux|outputs/|manuscript|commit|push" docs/goals/010-module5-deep-server-remote-smoke-preflight docs/module5_remote_smoke_preflight.md
```

Review marker hits manually. They should be boundary, non-claim, remote-smoke,
artifact-path, or future-gate language.

## Commands Not Authorized

Do not run:

```bash
make module5-dry-run
make module5-dry-run-inspect
make fast-check
```

Do not run the 25-replicate rehearsal, the 279,500-row production run, broad
test suites, staging, commit, push, PR, or manuscript/publishing commands.

## Wake-Up Content

Report:

- final branch, HEAD, and status;
- changed local files;
- remote alias used;
- run ID, `tmux` session name, remote source/scratch/artifact paths;
- smoke command and inspection outcomes;
- row count, proposal count, intervention count, replicate coverage, and seed
  mismatch facts;
- remote artifact inventory and size;
- local validation outcomes;
- risks/questions and next-goal recommendation.
