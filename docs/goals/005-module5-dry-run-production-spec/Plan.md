# Plan

## Milestone 1: Confirm State And Boundaries

Acceptance criteria:

- `pwd`, branch, HEAD, and `git status --short --branch` are recorded in
  `Log.md`.
- The action repo is confirmed as the only working scope.
- `pedder` confirms it will not read Chief of Staff or Goal Composer.
- Any dirty state outside this Goal 005 packet is treated as a blocker unless
  Galaxias explicitly authorises continuing.

Validation:

- `git status --short --branch`

## Milestone 2: Refresh The Module 5 Decision Surface

Acceptance criteria:

- Required repo-local docs, prior goal logs, Module 4.5 tables, Module 5
  contracts, runner, inspector, scripts, and tests are read.
- The refresh distinguishes current facts from historical/superseded wording
  such as `SRF-A`.
- `Log.md` lists the main surfaces inspected.

Validation:

- Manual cross-check against the `Read First` list in `Goal.md`.

## Milestone 3: Draft The Specification

Acceptance criteria:

- `docs/module5_dry_run_production_spec.md` is created.
- It compares accepted, family-winner, global-winner, near-frontier-absolute,
  and near-frontier-relative proposal sources.
- It recommends one dry-run subset and one later production proposal source.
- It audits the current intervention matrix and says whether it is adequate
  for the next implementation goal.
- It specifies seed, restart/resume, output, provenance, validation, approval,
  and stop-point policies.
- It proposes the next goal after this one without authorising it.

Validation:

- Re-read the draft against Goal 004 readiness gates and this Goal 005
  objective.

## Milestone 4: Validate Docs-Only Scope

Acceptance criteria:

- `git diff --check` passes.
- Trailing-whitespace scan over changed and untracked goal/spec text finds no
  matches.
- Marker scan over changed and untracked goal/spec text is reviewed for
  accidental production execution, remote execution, generated-output, or
  manuscript-claim language.
- Any hits are either boundary/non-claim language or are corrected before
  reporting.
- No code, test, data contract, generated output, commit, push, or staging
  occurred.

Validation:

- `git status --short --branch`
- `git diff --check`
- trailing-whitespace scan over changed and untracked goal/spec text
- narrow marker scan over changed and untracked goal/spec text

## Milestone 5: Report And Wake Galaxias

Acceptance criteria:

- `Log.md` records final status, validation evidence, outputs, blockers, and
  recommendations.
- Final response summarises the specification and decisions needed.
- A short wake-up is sent to the Galaxias orchestrator thread if thread tools
  are available.
- If thread tools are unavailable, the final response reports that explicitly.

Validation:

- Read back the final `Log.md` update before reporting.

## Stop-And-Fix Rule

If this work starts requiring implementation, schema changes, simulation
execution, remote compute, or scientific claim upgrades, stop and report the
scope break rather than stretching the goal.
