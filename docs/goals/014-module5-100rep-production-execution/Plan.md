# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias` and the authorized Goal 014
remote paths on `deep-server`.

Treat repo-local instructions and this Goal 014 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, sibling projects, or archive material.

This is production execution and inspection only. Do not interpret the result.

## Starting State Guard

1. Record local state:
   - `pwd`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse HEAD`
   - `git status --short --branch`
   - `git rev-list --left-right --count HEAD...origin/main`

2. Expected local state:
   - branch `main`;
   - HEAD `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`;
   - `HEAD...origin/main` count `0 0`;
   - clean status except this uncommitted Goal 014 packet.

3. If local state differs materially, stop and wake Galaxias.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- `docs/module5_production_run_spec.md`
- `docs/module5_25rep_rehearsal_report.md`
- `docs/module5_source_identity_contract.md`
- `docs/goals/012-module5-25rep-production-rehearsal/Log.md`
- `docs/goals/013-module5-preproduction-baseline-freeze/Log.md`
- `docs/goals/014-module5-100rep-production-execution/Goal.md`
- `docs/goals/014-module5-100rep-production-execution/Plan.md`
- `docs/goals/014-module5-100rep-production-execution/Runbook.md`
- `src/galaxias_model/module5_rehearsal.py`
- `scripts/run_module5_25rep_rehearsal.py`
- `scripts/inspect_module5_25rep_rehearsal.py`

## Task 1: Local Preflight

Run a local plan-only check with 100 replicates into `/tmp`.

Confirm:

- expected rows: 279,500;
- source/intervention units: 2,795;
- distinct source keys: 780;
- source contexts: 15;
- artifact verification rows: 15;
- all artifacts verified.

Do not run the 100-replicate execution locally.

## Task 2: Remote Preflight

Use `deep-server-ts` only.

Record:

- host and user;
- `/data` free space;
- `git --version`;
- `uv --version`;
- `python3 --version`;
- `tmux -V`.

Create a fresh source checkout under the Goal 014 source path and pin it to:

```text
ddb8a6de583e85f170f46c9dec9b1246baa6dccc
```

Verify the remote checkout with:

```bash
git rev-parse HEAD
git status --short --branch
```

Run remote plan-only preflight with 100 replicates and verify the same counts
as the local preflight. Verify all 15 required parameter artifacts by manifest
size and SHA-256.

Stop if the checkout commit or any count differs.

## Task 3: Launch The Production Execution

Use a durable `tmux` session:

```text
galaxias-m5-prod-YYYYMMDDTHHMMSSZ
```

Use run ID:

```text
YYYYMMDDTHHMMSSZ-goal014-m5-100rep-production
```

Run the existing frozen runner with:

- `--replicates 100`;
- `--workers 32`;
- scratch output path under the Goal 014 scratch directory;
- run ID as above.

Capture:

- exact command;
- stdout/stderr log;
- `rehearsal.exit` or production-run exit file;
- `tmux_command.exit`;
- run timing;
- storage footprint.

If the tmux command is still running at the end of a reasonable active turn,
leave it running and wake Galaxias with session name, paths, and current log
tail. Do not poll indefinitely.

## Task 4: Inspect And Checksum

After execution exits successfully:

- run the frozen inspector over the output directory;
- copy or move outputs into the artifact directory according to the same
  durable pattern used by Goal 012;
- generate `artifact_inventory.txt`;
- generate `checksums.sha256`;
- verify `sha256sum -c checksums.sha256`;
- record raw matched outcome size and SHA-256.

Inspection must match every invariant in `Goal.md`.

## Task 5: Compact Local Report

Create `docs/module5_100rep_production_execution_report.md`.

Include:

- boundary statement: execution and inspection only, no interpretation;
- source commit SHA;
- run ID, tmux session, paths;
- remote preflight facts;
- plan-only counts;
- execution timing and worker count;
- inspection facts;
- artifact inventory summary and matched-output SHA;
- deviations and residual risks;
- stop point before Goal 015 interpretation.

Do not include raw matched-outcome rows.

## Task 6: Local Publication Of Execution Record

Update Goal 014 `Log.md` with full evidence.

Run:

```bash
git diff --check
rg -n "[ \t]+$" docs/goals/014-module5-100rep-production-execution docs/module5_100rep_production_execution_report.md
rg -n "production attribution|production-ready|manuscript|causal|claim|outputs/|commit|push|tmux|deep-server" docs/goals/014-module5-100rep-production-execution docs/module5_100rep_production_execution_report.md
```

Review marker hits manually as boundary, path, execution, or stop-point
language only.

Stage exact Goal 014 docs only:

```bash
git add \
  docs/goals/014-module5-100rep-production-execution \
  docs/module5_100rep_production_execution_report.md
```

Verify:

```bash
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
```

Commit and push only if the staged set is exactly:

```text
docs/goals/014-module5-100rep-production-execution/Goal.md
docs/goals/014-module5-100rep-production-execution/Log.md
docs/goals/014-module5-100rep-production-execution/Plan.md
docs/goals/014-module5-100rep-production-execution/Runbook.md
docs/module5_100rep_production_execution_report.md
```

Commit subject:

```text
Record Module 5 production execution
```

Push `main`. Do not create a PR.

## Task 7: Wake-Up

Wake Galaxias with:

- final branch, HEAD, status, and pushed commit SHA;
- source baseline SHA used for execution;
- remote alias, run ID, tmux session, source/scratch/artifact paths;
- execution duration and worker count;
- exact inspection facts;
- raw matched-output size and SHA-256;
- checksum verification result;
- staged/committed path list;
- deviations and risks;
- recommended Goal 015 shape.

Then wait.
