# Plan

## Milestones

## Milestone 1: Orient And Branch

Acceptance criteria:

- Initial pwd, git toplevel, git dirs, branch, HEAD, and status are reported.
- `git fetch --prune origin` has run.
- `origin/main` is confirmed at `4d161f4` or newer.
- Branch is
  `codex/galaxias-goal003-module5-smoke-inspection`, created from
  `origin/main`.
- Required Goal 001, Goal 002, contract, runner, and test files are refreshed.

Validation:

- `git status --short --branch`
- `git rev-parse --short origin/main`
- `git rev-parse --short HEAD`

## Milestone 2: Write Focused Inspection Tests

Acceptance criteria:

- Tests describe inspection of emitted smoke files from disk.
- Happy-path test checks:
  - schema-conforming output;
  - matched pair identifiers;
  - paired stochastic seeds;
  - provenance labels;
  - smoke-only boundary language.
- Failure-path test tampers with emitted seeds and expects the inspection to
  fail the common-random-number check.
- Tests fail before the inspector exists.

Validation:

- `uv run pytest tests/test_module5_smoke_inspection.py -q`

## Milestone 3: Implement Disk-First Inspector

Acceptance criteria:

- Inspector reads:
  - `matched_outcomes.csv`;
  - `provenance.json`;
  - `data/module5_counterfactual_outcome_schema.csv`.
- Inspector writes:
  - `inspection_summary.json`;
  - `inspection_checks.csv`;
  - `inspection_report.md`.
- Inspector reports pass/fail status without running simulations.
- CLI defaults to `outputs/module5_runner_smoke/` and writes under
  `outputs/module5_runner_smoke/inspection/`.

Validation:

- `uv run pytest tests/test_module5_smoke_inspection.py -q`

## Milestone 4: Add Goal Packet And Command Surface

Acceptance criteria:

- `docs/goals/003-module5-smoke-inspection/` contains
  `Goal.md`, `Plan.md`, `Runbook.md`, and `Log.md`.
- `make module5-inspect` runs the disk-first inspection only.
- Discoverability docs mention the inspector without implying production
  attribution.

Validation:

- Re-read changed docs for boundary language.

## Milestone 5: Run Validation And Stop

Acceptance criteria:

- Contract validator passes.
- Focused inspection tests pass.
- `make fast-check` passes.
- `make module5-smoke` regenerates tiny ignored smoke files.
- Inspection CLI or `make module5-inspect` passes.
- `git diff --check` passes.
- Marker scan over changed/new tracked text finds no production-claim drift.
- Final git status is reported.
- No commit or push is created.

Validation:

- `uv run python scripts/validate_module5_counterfactual_contract.py`
- `uv run pytest tests/test_module5_smoke_inspection.py -q`
- `make fast-check`
- `make module5-smoke`
- `make module5-inspect`
- `git diff --check`
- marker scan command recorded in `Log.md`
- `git status --short --branch`

## Stop-And-Fix Rule

If validation fails, repair the inspection layer while staying within the
disk-first smoke-output review boundary. Stop and report if a fix would require
production simulations, remote compute, new scientific assumptions, or broad
refactoring.
