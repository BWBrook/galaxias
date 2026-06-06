# Plan

## Milestones

## Milestone 1: Orient And Branch

Acceptance criteria:

- Initial pwd, git toplevel, git dirs, branch, HEAD, and status are reported.
- `git fetch --prune origin` has run.
- `origin/main` is confirmed at `ddbbe4c` or newer.
- Branch is
  `codex/galaxias-goal004-module5-production-readiness`, created from
  `origin/main`.
- Required Goal 001, Goal 002, Goal 003, contract, runner, inspector, and test
  files are refreshed.

Validation:

- `git status --short --branch`
- `git rev-parse --short origin/main`
- `git rev-parse --short HEAD`

## Milestone 2: Draft The Readiness Gate

Acceptance criteria:

- `docs/goals/004-module5-production-readiness/Goal.md` states this is
  docs-only and does not authorise production compute.
- The goal defines approval gates for:
  - family set;
  - intervention axes;
  - sample size and replicate count;
  - stochastic seed policy;
  - output schema;
  - provenance capture;
  - ignored versus tracked output handling;
  - compute target and resource budget;
  - validation commands;
  - rollback and cleanup;
  - claim language.
- The goal includes explicit stop points for SRF-A/Barry approval.

Validation:

- Re-read `Goal.md` against the delegation boundary.

## Milestone 3: Add Operational Plan And Runbook

Acceptance criteria:

- `Plan.md` describes the docs-only milestones and validation surface.
- `Runbook.md` gives a decision sequence for a future production-readiness
  review without launching compute.
- `Runbook.md` includes the proposed next-run ladder:
  - completed tiny local smoke;
  - optional approved small local dry-run;
  - deliberate remote-compute plan via `/Users/bwbrook/work/nectar` for any
    production-sized job.
- `Runbook.md` names the approvals required before each escalation.

Validation:

- Re-read for stop-point clarity and absence of execution instructions that
  would launch production work.

## Milestone 4: Add Log And Discoverability Updates

Acceptance criteria:

- `Log.md` records start state, branch creation, read-first refresh, docs-only
  boundary, and validation evidence.
- `docs/module5_counterfactual_attribution_plan.md` no longer points the next
  work at already-completed Goal 002.
- `README.md` and `data/README.md` are updated only if needed for current
  next-step discoverability.

Validation:

- `git diff --name-only` shows docs-only changes.

## Milestone 5: Validate And Stop

Acceptance criteria:

- `git status --short --branch` is reported.
- `git diff --check` passes.
- Marker scan over changed/new tracked text finds only boundary/non-claim or
  expected readiness-gate language.
- No tests are run because no code or test files changed.
- No commit or push is created.

Validation:

- `git status --short --branch`
- `git diff --check`
- marker scan over changed/new tracked text

## Stop-And-Fix Rule

If validation finds code/test changes, production-run instructions, remote
probe instructions, or manuscript-level causal claims, stop and correct the
docs before reporting. If correction would require a non-doc change, stop and
report the blocker.
