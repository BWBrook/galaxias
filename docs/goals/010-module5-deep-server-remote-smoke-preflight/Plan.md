# Plan

## Operating Rules

Work from `/Users/bwbrook/papers/galaxias` as the local action repo. Treat
repo-local instructions and this packet as the source of truth.

Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, or `/Users/bwbrook/work/nectar`. Galaxias
has already summarized the relevant `deep-server` and data-placement policy in
`Goal.md`.

This goal authorizes a bounded remote smoke only. Do not broaden into
production execution.

## Starting State Guard

1. Record:
   - `pwd`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse --short=12 HEAD`
   - `git status --short --branch`

2. Expected pre-work dirty state is limited to accepted Goal 005/006/007/008
   /009 material plus this Goal 010 packet:
   - `M Makefile`
   - `M README.md`
   - `M data/module5_counterfactual_interventions.csv`
   - `M src/galaxias_model/module5_counterfactual.py`
   - `M tests/test_module5_counterfactual_contract.py`
   - `?? docs/goals/005-module5-dry-run-production-spec/`
   - `?? docs/goals/006-module5-real-proposal-dry-run/`
   - `?? docs/goals/007-module5-intervention-matrix-review/`
   - `?? docs/goals/008-module5-production-matrix-contract-revision/`
   - `?? docs/goals/009-module5-production-run-spec/`
   - `?? docs/goals/010-module5-deep-server-remote-smoke-preflight/`
   - `?? docs/module5_dry_run_production_spec.md`
   - `?? docs/module5_intervention_matrix_review.md`
   - `?? docs/module5_production_matrix_contract.md`
   - `?? docs/module5_production_run_spec.md`
   - `?? scripts/inspect_module5_real_proposal_dry_run.py`
   - `?? scripts/run_module5_real_proposal_dry_run.py`
   - `?? src/galaxias_model/module5_dry_run_inspect.py`
   - `?? src/galaxias_model/module5_proposals.py`
   - `?? tests/test_module5_dry_run_inspection.py`
   - `?? tests/test_module5_real_proposal_dry_run.py`

3. If any other pre-work dirty state exists, stop and report it to Galaxias
   before editing or running remote commands.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- `docs/module5_production_run_spec.md`
- `docs/module5_production_matrix_contract.md`
- `docs/module5_dry_run_production_spec.md`
- `docs/goals/006-module5-real-proposal-dry-run/Log.md`
- `docs/goals/009-module5-production-run-spec/Log.md`
- `data/module4_raw_artifact_manifest.csv`
- `data/module4_5_proposal_set_membership.csv`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`
- `src/galaxias_model/module5_proposals.py`
- `src/galaxias_model/module5_counterfactual.py`
- `src/galaxias_model/module5_dry_run_inspect.py`
- `scripts/run_module5_real_proposal_dry_run.py`
- `scripts/inspect_module5_real_proposal_dry_run.py`

## Tasks

### Task 1: Log Starting State

- Confirm local working directory, branch, HEAD, and dirty state.
- Confirm dirty state matches the expected accepted surface plus this
  Goal 010 packet.
- Record the local required smoke artifact:
  `outputs/remote/module4_observation_sensitivity_20260522T101942Z/baseline_current_seed20260410/parameter_values.csv.gz`.
- Verify local artifact size and SHA-256.
- Update `Log.md` with starting state and boundary confirmation.

### Task 2: Prepare Run Identifiers

- Create a UTC run stamp and run ID, for example
  `RUN_STAMP=20260613T000000Z` and
  `RUN_ID=20260613T000000Z-goal010-m5-remote-smoke`.
- Set:
  - `REMOTE_ALIAS=deep-server-ts`, with `utas-ubuntu` fallback only if the
    first alias fails;
  - `REMOTE_REPO=/data/codex/repos/galaxias-goal010-remote-smoke-$RUN_ID`;
  - `REMOTE_SCRATCH=/data/codex/scratch/galaxias/module5_remote_smoke_$RUN_ID`;
  - `REMOTE_ARTIFACT=/data/codex/artifacts/galaxias/module5_remote_smoke_$RUN_ID`;
  - `SESSION=galaxias-m5-smoke-$RUN_STAMP`.
- Record these values in `Log.md`.

### Task 3: Probe Deep-Server Access

- Use `ssh deep-server-ts` first.
- If it fails, record the exact failure and try `ssh utas-ubuntu` once.
- If both fail, stop and wake Galaxias.
- Record remote host, user, `pwd`, kernel, `/data` disk space, `python3`,
  and `uv` availability.

Use a login/path-aware command pattern so `/home/bwbrook/.local/bin/uv` can be
found if needed.

### Task 4: Create Remote Directories

- Create the remote repo, scratch, artifact, and logs directories.
- Do not touch unrelated `/data` paths.
- If a target path already exists, stop unless it clearly belongs to this
  exact run ID and is safe to reuse.

### Task 5: Mirror Source And Smoke Artifact

- Use `rsync` to mirror the current local source tree to `REMOTE_REPO`.
- Include `.git`.
- Exclude:
  - `.venv/`
  - `.pytest_cache/`
  - `__pycache__/`
  - `outputs/`
- Separately create the expected remote `outputs/remote/...` directory and
  transfer only the required `parameter_values.csv.gz` artifact.
- Verify remote `git rev-parse HEAD` equals local HEAD.
- Verify remote `git status --short --branch` records the accepted dirty
  surface.
- Verify remote parameter-values SHA-256 equals the expected hash.

### Task 6: Write Remote Smoke Script

Create a remote script under `REMOTE_ARTIFACT`, for example:

```text
$REMOTE_ARTIFACT/run_module5_remote_smoke.sh
```

The script must:

- set `set -euo pipefail`;
- add `$HOME/.local/bin` to `PATH`;
- `cd` to `REMOTE_REPO`;
- record host, date, working directory, git SHA/status, Python, `uv`, and
  input hashes;
- run `scripts/run_module5_real_proposal_dry_run.py` with:
  - `--replicates 5`;
  - `--output-dir "$REMOTE_SCRATCH/outputs/module5_remote_smoke_goal010"`;
- run `scripts/inspect_module5_real_proposal_dry_run.py` with:
  - `--dry-run-dir "$REMOTE_SCRATCH/outputs/module5_remote_smoke_goal010"`;
  - `--inspection-dir "$REMOTE_SCRATCH/outputs/module5_remote_smoke_goal010/inspection"`;
  - `--expected-replicates 5`;
- run a direct disk check for the required 65-row facts;
- write checksums for remote smoke files;
- copy or sync compact passed smoke artifacts from scratch to
  `REMOTE_ARTIFACT/outputs/`;
- write an exit-status file in `REMOTE_ARTIFACT`.

Do not edit repo source files to make the script work. If the existing runner
or inspector cannot support the smoke, stop and wake Galaxias with the exact
failure.

### Task 7: Run Smoke Under Tmux

- Start a detached `tmux` session named by `SESSION`.
- Run the remote smoke script inside that session.
- Capture logs to `REMOTE_ARTIFACT/logs/`.
- Wait only for the bounded smoke completion by checking the remote
  exit-status file or session completion.
- If the session fails or hangs beyond a reasonable smoke window, capture logs
  and wake Galaxias.

### Task 8: Inspect Remote Evidence

Read remote logs, provenance, inspection summary, inspection checks, row-count
summary, and checksum manifest.

Confirm:

- 65 matched-outcome rows;
- 13 intervention IDs;
- 5 proposal IDs;
- 5 replicates per intervention row;
- replicate IDs exactly `0..4`;
- zero baseline/intervention seed mismatches;
- inspection `all_checks_passed` true;
- provenance `production_attribution` false.

Do not copy raw matched outcomes into the local repo.

### Task 9: Write Preflight Report

Create `docs/module5_remote_smoke_preflight.md` with the required structure
from `Goal.md`.

Include exact remote paths and enough evidence for Galaxias to review the
remote smoke without opening raw outputs.

### Task 10: Validate Local Docs

Run:

```bash
git status --short --branch
git diff --check
rg -n "[ \t]+$" docs/goals/010-module5-deep-server-remote-smoke-preflight docs/module5_remote_smoke_preflight.md
rg -n "production attribution|production-ready|deep-server|tmux|outputs/|manuscript|commit|push" docs/goals/010-module5-deep-server-remote-smoke-preflight docs/module5_remote_smoke_preflight.md
```

Review marker hits manually. They should be boundary, non-claim, remote-smoke,
artifact-path, or future-gate language.

### Task 11: Final Log And Wake-Up

Update `Log.md` with:

- changed files;
- remote alias used;
- run ID, session name, remote paths;
- remote command outcomes;
- smoke row facts;
- validation outcomes;
- final status;
- risks/questions;
- recommended next goal.

Send a short wake-up to Galaxias thread
`019eaac3-85f6-7853-bc28-a4d905dadfc3` on completion or blockage.
