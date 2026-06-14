# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`.

Treat repo-local instructions and this Goal 013 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, sibling projects, or archive material.

This is a publication/reproducibility goal only. Do not implement new science
or run Module 5 production.

## Starting State Guard

1. Record:
   - `pwd`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse --short=12 HEAD`
   - `git status --short --branch`

2. Run:

   ```bash
   git fetch --prune origin
   git rev-list --left-right --count HEAD...origin/main
   ```

   Expected before committing: `0 0`.

3. Confirm the dirty surface is the accepted Goal 005-012 surface plus this
   Goal 013 packet. If anything else appears, stop and wake Galaxias.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- Goal 005-013 `Goal.md`, `Plan.md`, `Runbook.md`, and `Log.md`
- `docs/module5_dry_run_production_spec.md`
- `docs/module5_intervention_matrix_review.md`
- `docs/module5_production_matrix_contract.md`
- `docs/module5_production_run_spec.md`
- `docs/module5_remote_smoke_preflight.md`
- `docs/module5_source_identity_contract.md`
- `docs/module5_25rep_rehearsal_report.md`
- the changed Module 5 code, scripts, tests, and CSV contracts listed in
  `Runbook.md`

## Task 1: Validate Before Staging

Run the full validation ladder in `Runbook.md`.

Use a temporary directory outside the repo for the plan-only Goal 012 rehearsal
preflight, for example:

```bash
TMPDIR_GOAL013="$(mktemp -d /tmp/galaxias-goal013-plan.XXXXXX)"
uv run python scripts/run_module5_25rep_rehearsal.py \
  --plan-only \
  --output-dir "$TMPDIR_GOAL013" \
  --run-id goal013-plan-only
```

Parse the generated `rehearsal_plan.json` and `artifact_verification.csv` to
confirm the required counts.

If local validation changes ignored outputs, leave them ignored and record the
paths.

## Task 2: Read-Only Remote Evidence Check

If `deep-server-ts` is reachable, verify the successful Goal 012 artifact
directory without modifying it:

```text
/data/codex/artifacts/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal
```

Required read-only checks:

- `sha256sum -c checksums.sha256`
- parse `outputs/module5_25rep_rehearsal/inspection/inspection_summary.json`
- parse `outputs/module5_25rep_rehearsal/provenance.json`

Record the exact facts in `Log.md`.

If `deep-server-ts` is not reachable, record the exact error. Do not create a
new remote session and do not fall back to `utas-ubuntu` for this publication
goal.

## Task 3: Confirm Exact Publication Surface

Compare `git status --short --branch` to the expected accepted surface.

Confirm no ignored generated outputs are candidates for staging:

```bash
git status --ignored --short outputs .pytest_cache .venv
```

Do not stage anything until validation and this check have passed.

## Task 4: Stage Exact Paths Only

Use exact path staging from `Runbook.md`. Do not use `git add .`.

After staging, run:

```bash
git diff --cached --name-only
git diff --cached --stat
git status --short --branch
```

The staged file list must exactly match the expected list in `Runbook.md`.
If it differs, unstage only the incorrect paths if that can be done
non-destructively with `git restore --staged <path>`, record the issue, and
stop before commit unless the list is made exact. Do not modify file contents
to force the staged set.

## Task 5: Commit And Push

Commit exactly once:

```bash
git commit -m "Prepare Module 5 production baseline"
```

Then record:

```bash
git rev-parse HEAD
git status --short --branch
```

Push:

```bash
git push origin main
```

Then record:

```bash
git status --short --branch
git rev-parse HEAD
```

If commit or push fails, stop and wake Galaxias with exact output. Do not
force-push, reset, rebase, amend, or create a PR.

## Task 6: Final Log And Wake-Up

Update `Log.md` before committing with:

- starting state;
- validation evidence;
- remote read-only evidence or exact remote-unavailable error;
- staged path list and staged stat;
- ignored-output status;
- commit/push commands planned.

After commit/push, send the wake-up with:

- final branch, HEAD, and status;
- pushed commit SHA;
- exact staged/committed file list;
- validation outcomes;
- remote evidence check outcome;
- ignored generated-output paths left local only;
- confirmation that no production run, interpretation, PR, or generated-output
  promotion occurred;
- recommended Goal 014 shape.

Wait after waking Galaxias.
