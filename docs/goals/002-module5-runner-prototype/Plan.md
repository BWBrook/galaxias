# Plan

## Milestones

## Milestone 1: Orient And Branch

Acceptance criteria:

- Starting worktree state is reported before edits.
- Branch is
  `codex/galaxias-goal002-module5-runner-prototype`, created from
  `origin/main`.
- Required Goal 001 and Module 5 contract files are reread.

Validation:

- `git status --short --branch`
- `git rev-parse --short HEAD`

## Milestone 2: Write Focused Runner Tests

Acceptance criteria:

- Tests describe the narrow intervention override behaviour.
- Tests describe matched smoke output behaviour:
  - output columns match the declared outcome schema;
  - baseline and intervention stochastic seeds are paired;
  - generated outputs are written to a caller-provided output directory.
- Tests fail before the runner implementation exists.

Validation:

- `uv run pytest tests/test_module5_runner_prototype.py -q`

## Milestone 3: Implement Tiny Runner Prototype

Acceptance criteria:

- Runner consumes `data/module5_counterfactual_interventions.csv`.
- Runner writes `matched_outcomes.csv` and `provenance.json` under ignored
  `outputs/` by default.
- Runner preserves common-random-number pairing by using the same stochastic
  seed for baseline and intervention arms.
- Runner supports only the four contract axes listed in Goal 002.
- Runner uses smoke-default parameters and records that outputs are not
  production attribution evidence.

Validation:

- `uv run pytest tests/test_module5_runner_prototype.py -q`

## Milestone 4: Add Goal Packet And Documentation Update

Acceptance criteria:

- `docs/goals/002-module5-runner-prototype/` contains
  `Goal.md`, `Plan.md`, `Runbook.md`, and `Log.md`.
- `data/README.md` no longer points current immediate next steps back to the
  stale Module 3 readiness gate.
- Optional Makefile target, if added, runs only the tiny local smoke prototype.

Validation:

- Re-read changed docs for scope and claim discipline.

## Milestone 5: Run Validation And Stop

Acceptance criteria:

- Contract validator passes.
- Focused runner tests pass.
- `make fast-check` passes or any failure is recorded with evidence.
- `git diff --check` passes.
- Final `git status --short --branch` is reported.
- No commit or push is created.

Validation:

- `uv run python scripts/validate_module5_counterfactual_contract.py`
- `uv run pytest tests/test_module5_runner_prototype.py -q`
- `make fast-check`
- `git diff --check`
- `git status --short --branch`

## Stop-And-Fix Rule

If validation fails, fix the local runner or tests while staying within the
bounded prototype. Stop and report if a fix would require production
simulation, remote compute, new scientific assumptions, or broad refactoring.
