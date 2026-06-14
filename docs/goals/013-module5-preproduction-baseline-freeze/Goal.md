# Goal: Module 5 Preproduction Baseline Freeze

## Objective

Freeze the accepted Goal 005-012 Module 5 work into a clean, pushed Git
baseline before any 100-replicate production execution.

This goal is a publication and reproducibility gate. It should validate the
accepted dirty surface, stage only the accepted files, commit them as one
coherent preproduction baseline, push `main`, and report the resulting commit
SHA for use by the next production-execution goal.

This goal does not authorize the 100-replicate production run, new simulations,
new remote `tmux` runs, production attribution interpretation, manuscript
claims, new science decisions, or broad implementation changes.

## Why This Matters

Goals 005-012 brought Module 5 from a spec-only design to a source-key-aware
remote rehearsal that passed inspection. The action repo is still intentionally
dirty and uncommitted. Running the full 100-replicate execution from that
dirty state would make provenance weaker than it needs to be.

Before Goal 014, the project needs a stable Git SHA that captures:

- the dry-run production spec;
- the real-proposal dry-run runner and inspector;
- the 13-row production matrix contract;
- the production run spec;
- the `deep-server` remote smoke evidence;
- the source-context identity implementation;
- the 25-replicate production rehearsal runner, inspector, report, and log.

Goal 013 should make that baseline explicit, clean, and pushed.

## Authorized Outcome

If all checks pass and the staged path set is exact, create and push one commit
on `main`.

Recommended commit subject:

```text
Prepare Module 5 production baseline
```

The final wake-up must report:

- final branch and commit SHA;
- pushed remote status;
- exact staged file list;
- validation commands and outcomes;
- remote rehearsal evidence rechecked read-only, if available;
- any ignored generated-output paths left untracked;
- remaining risks and the recommended Goal 014 shape.

## Scope

In scope:

- Read repo-local instructions and accepted Goal 005-012 docs/logs/reports.
- Confirm the current dirty surface is exactly the accepted Module 5 surface
  plus this Goal 013 packet.
- Run a full local validation gate before staging.
- Run read-only remote checks against the successful Goal 012 rehearsal
  artifact directory if `deep-server-ts` is reachable.
- Update this Goal 013 `Log.md` with validation, staged-set, commit, and push
  evidence.
- Stage exact accepted paths only.
- Commit one coherent preproduction baseline.
- Push `main` to `origin`.

Allowed local edits:

- `docs/goals/013-module5-preproduction-baseline-freeze/Log.md`

Allowed Git actions:

- `git fetch --prune origin`
- exact-path `git add` commands for the accepted file list in `Runbook.md`
- `git diff --cached --name-only`
- `git diff --cached --stat`
- `git commit`
- `git push origin main`

Out of scope:

- No 100-replicate production execution.
- No new Module 5 simulations or rehearsal reruns.
- No remote `tmux` creation or remote source-mirror mutation.
- No production attribution interpretation or final causal effect estimate.
- No manuscript, abstract, figure, supplement, or publication claim language.
- No changes to scientific contracts, intervention rows, pressure-removal
  semantics, proposal selection, family weighting, diagnostic ordering, or
  replicate counts.
- No raw matched-outcome promotion into tracked files.
- No staging of ignored `outputs/`, `.venv`, caches, remote artifacts, or
  generated payloads.
- No PR creation.
- Do not read `/Users/bwbrook/chief_of_staff` or
  `/Users/bwbrook/work/goal_composer`.

## Required Validation

Run and log:

- `git fetch --prune origin`
- `git rev-list --left-right --count HEAD...origin/main`
- `uv run pytest tests/test_module5_production_rehearsal.py tests/test_module5_source_identity.py tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q`
- `uv run python scripts/validate_module5_counterfactual_contract.py`
- `uv run python scripts/run_module5_25rep_rehearsal.py --plan-only --output-dir <tmpdir> --run-id goal013-plan-only`
- `make module5-dry-run`
- `make module5-dry-run-inspect`
- `make fast-check`
- `git diff --check`
- trailing-whitespace scan over changed Goal 005-013 docs/code/test files
- marker scan over changed docs for boundary language
- `git status --short --branch`

For the plan-only rehearsal preflight, verify and log:

- expected rows: 69,875;
- source/intervention units: 2,795;
- distinct `proposal_source_key` values: 780;
- source contexts: 15;
- artifact verification rows: 15;
- all artifacts verified.

If `deep-server-ts` is reachable, run a read-only remote check of the Goal 012
successful artifact directory:

- checksum manifest verifies;
- inspection summary reports 69,875 rows, 53 columns, 25 replicates, 2,795
  source/intervention units, 780 source keys, zero seed mismatches,
  `all_checks_passed=true`, and `production_attribution=false`.

If `deep-server-ts` is unavailable, do not use the fallback for this publication
goal. Record the exact connection failure and continue only if all local
validation and staged-path checks pass.

## Stop Points

Stop and wake Galaxias before staging or committing if:

- `HEAD...origin/main` is not `0 0` before the publication commit;
- dirty state contains unexpected files outside the accepted Goal 005-013
  surface;
- any validation command fails;
- the plan-only rehearsal preflight does not reproduce the expected counts;
- the staged path list differs from the exact accepted path list in
  `Runbook.md`;
- ignored generated outputs appear staged;
- commit or push fails.

Do not repair by changing science code during this goal. If validation fails,
record the exact failure and wake Galaxias.

## Completion Condition

Goal 013 is complete when:

- the accepted Goal 005-013 surface is committed as one coherent baseline;
- the commit is pushed to `origin/main`;
- local status is clean apart from ignored generated outputs;
- no production execution, interpretation, or generated-output promotion
  occurred;
- `pedder` sends a short wake-up to Galaxias and waits.
