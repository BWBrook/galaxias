# Goal: Module 5 Dry-Run And Production Specification

## Objective

Produce a decision-ready Module 5 dry-run and production specification that
turns the Goal 004 readiness gate into concrete, reviewable choices for
proposal source, dry-run subset, intervention matrix, seed policy, output
handling, provenance, validation, and approval gates.

This is a spec/decision-only goal. It does not authorise runner
implementation, production attribution, remote compute, generated output
creation, manuscript interpretation, commit, or push.

## Why This Matters

Goals 001-004 established the Module 5 contract, tiny smoke runner,
disk-first smoke inspection, and readiness gate. The next unresolved step is
not to run more simulations. It is to decide what a defensible next dry-run
and later production run would actually mean.

The current runner proves smoke-scale mechanics, but it still uses
`smoke_default:<family>` proposal identifiers rather than a real Module 4.5
proposal source. Before implementation continues, Galaxias needs a crisp
proposal-set and execution specification that Barry can review.

## Operating Mode

Spec/decision-only action-repo goal.

## Review Surface

Galaxias should inspect:

- `docs/module5_dry_run_production_spec.md`
- this goal `Log.md`
- the final changed-file list and status
- any marker-scan notes about boundary language
- `pedder`'s final recommendation and any explicit questions

## Scope

In scope:

- Inspect tracked repo-local Module 4.5 and Module 5 docs, data contracts,
  runner/inspection surfaces, and prior goal logs.
- Create `docs/module5_dry_run_production_spec.md`.
- Recommend a dry-run proposal subset and explain why it is preferable to
  alternatives.
- Recommend how a later production proposal set should be selected.
- Audit whether the existing Module 5 intervention matrix is adequate or
  needs revision before implementation.
- Specify seed, restart/resume, output, provenance, validation, and approval
  policies for the next implementation goal.
- Update this goal `Log.md` as work proceeds.
- Run only narrow read-only status or text/CSV inspection commands needed to
  support the specification.
- Run docs-only validation checks on changed text.
- Send a short wake-up to the Galaxias orchestrator thread when complete or
  blocked.

Out of scope:

- No code, test, Makefile, schema, CSV contract, scientific-default, prior,
  target-weight, family-definition, observation-bridge, or Module 4.5 output
  changes.
- No Module 5 dry-run execution.
- No production attribution.
- No generated outputs under `outputs/`.
- No remote compute, remote probes, or `/Users/bwbrook/work/nectar` execution
  planning beyond citing the existing routing boundary.
- No calibration reruns or broad simulation batches.
- No manuscript-level causal claims.
- No goal-packet rewrites outside this Goal 005 `Log.md`.
- No commit, push, staging, merge, or PR.
- Do not read `/Users/bwbrook/chief_of_staff`.
- Do not read `/Users/bwbrook/work/goal_composer`.

## Read First

- `AGENTS.md` - repo-local operating and compute boundaries.
- `README.md` - current project status, non-claims, and command surface.
- `docs/gated_action_plan_module4_5_and_beyond.md` - module gate sequence and
  Gate 5 requirements.
- `docs/module4_5_mechanism_interpretation_review.md` - accepted proposal
  sets and Module 5 ensemble interpretation.
- `docs/module5_counterfactual_attribution_plan.md` - Module 5 design
  contract and intervention/endpoints logic.
- `docs/goals/001-module5-counterfactual-design-and-smoke/Log.md` - contract
  and validator provenance.
- `docs/goals/002-module5-runner-prototype/Log.md` - smoke runner provenance
  and limitations.
- `docs/goals/003-module5-smoke-inspection/Log.md` - emitted smoke inspection
  provenance and limitations.
- `docs/goals/004-module5-production-readiness/Goal.md`
- `docs/goals/004-module5-production-readiness/Runbook.md`
- `docs/goals/004-module5-production-readiness/Log.md`
- `data/module4_5_family_decision_table.csv` - family roles for Module 5.
- `data/module4_5_proposal_set_membership.csv` - proposal-source candidates.
- `data/module5_counterfactual_interventions.csv` - current intervention
  matrix.
- `data/module5_counterfactual_outcome_schema.csv` - required output fields.
- `src/galaxias_model/module5_counterfactual.py` - current smoke runner
  implementation boundary.
- `src/galaxias_model/module5_smoke_inspect.py` - current inspection boundary.
- `scripts/run_module5_counterfactual_smoke.py` - current CLI boundary.
- `scripts/inspect_module5_counterfactual_smoke.py` - current inspection CLI.
- `tests/test_module5_runner_prototype.py`
- `tests/test_module5_smoke_inspection.py`

## Starting State Checks

- Confirm `pwd`.
- Confirm branch, HEAD, and `git status --short --branch`.
- Confirm this Goal 005 packet is present.
- Treat any pre-existing dirty state outside this new goal packet as project
  state and pause before broadening.

## Git And Publication Policy

- Commit is forbidden for this goal.
- Push is forbidden for this goal.
- Staging is forbidden for this goal.
- Leave the worktree with uncommitted docs-only changes for Galaxias review.
- If unrelated dirty state appears, report it rather than cleaning or
  reverting it.

## Data, Compute, And Staging Policy

- Use only tracked repo-local source documents, code, tests, and CSVs.
- You may run read-only inspection commands over tracked text and CSV files.
- Do not create generated output bundles.
- Do not run `make module5-smoke`, `make module5-inspect`, `make fast-check`,
  integration tests, or any simulation/calibration command for this goal.
- Do not touch remote hosts or `/Users/bwbrook/work/nectar` beyond preserving
  the existing rule that production-sized planning must later use that
  control-plane guidance.

## Required Work

Create `docs/module5_dry_run_production_spec.md` with these sections:

1. Current State And Non-Claims
   - Summarise what Modules 1-4.5 and Goals 001-004 currently license.
   - State clearly that Module 5 attribution has not begun.

2. Proposal-Source Options
   - Compare at least:
     - `accepted`
     - `family_winners`
     - `global_winners`
     - `near_frontier_absolute`
     - `near_frontier_relative`
   - For each, explain scientific meaning, likely scale, strengths, and risks.
   - Recommend one dry-run subset and one later production source.

3. Dry-Run Specification
   - Define candidate families, proposal counts, intervention rows, replicate
     count, seed policy, expected output location, and validation surface.
   - Keep this as a recommendation only; do not run it.

4. Production Specification Sketch
   - Define what must be decided before production-scale execution.
   - Separate dry-run decisions from production decisions.

5. Intervention Matrix Audit
   - Review the current asymmetry in
     `data/module5_counterfactual_interventions.csv`.
   - Recommend whether the matrix is adequate for the next dry-run or should
     be expanded before implementation.

6. Seed And Restart Policy
   - Specify common-random-number pairing.
   - Recommend deterministic seed derivation from proposal/intervention/
     replicate identifiers.
   - State restart/resume expectations.

7. Output And Provenance Policy
   - Specify ignored raw output handling.
   - Specify what compact summaries, if any, might later be tracked.
   - Specify required provenance fields and checksum expectations.

8. Validation Ladder
   - Define validation for a future implementation goal.
   - Separate docs checks, focused tests, smoke output inspection, local dry-run
     checks, remote smoke, and production validation.

9. Approval Gates And Stop Points
   - List what Galaxias may decide.
   - List what Barry must approve.
   - List what would trigger pause before implementation.

10. Recommended Next Goal
   - Propose the next goal after this one, including whether it should be an
     implementation goal, a contract revision goal, or another review gate.

## Validation Gates

This goal is not complete until:

- `git status --short --branch` has been recorded in `Log.md`.
- `git diff --check` passes for tracked modifications.
- A trailing-whitespace scan over changed and untracked goal/spec text finds
  no matches.
- A narrow marker scan over changed tracked text has been reviewed for
  accidental production-run, remote-run, generated-output, or manuscript-claim
  language. Expected boundary and non-claim references are acceptable if
  described in `Log.md`.
- No code, test, data contract, generated output, remote compute, commit, push,
  staging, or manuscript-claim work occurred.

No tests are required for this docs-only goal. If code, tests, data contracts,
or generated outputs would need to change, stop and report the blocker.

## Deliverables

- `docs/module5_dry_run_production_spec.md`
- Updated `docs/goals/005-module5-dry-run-production-spec/Log.md`
- Final response to Galaxias summarising:
  - what was produced
  - recommended dry-run subset
  - recommended later production source
  - intervention-matrix recommendation
  - validation performed
  - final git status
  - questions or approval points for Barry/Galaxias
- Short wake-up message to the Galaxias orchestrator thread on completion or
  blockage.

## Decision Authority

You may decide:

- how to summarise tracked CSVs and docs;
- how to structure the specification document;
- which dry-run and production options to recommend, provided the reasoning is
  explicit;
- whether stale `SRF-A` wording should be treated as historical/superseded in
  the specification.

You must pause before:

- changing any scientific contract, data table, code, tests, or defaults;
- adding or removing intervention rows;
- choosing production sample size as an instruction rather than a
  recommendation;
- running any simulation or validation suite;
- touching remote compute;
- making manuscript-level causal claims;
- committing or pushing.

## Checkpoint Rules

Update `Log.md` after:

- starting-state checks;
- completing the read-first refresh;
- drafting the specification;
- validation;
- sending the wake-up or discovering that thread tools are unavailable.

## Pause Or Escalate

Pause and report if:

- the repo is unexpectedly dirty outside the Goal 005 packet;
- proposal-source tables are missing or inconsistent;
- the intervention matrix appears scientifically inadequate in a way that
  requires immediate contract edits;
- you cannot keep the goal docs-only;
- thread tools are unavailable for the wake-up.

## Stop Conditions

Stop when one of these is true:

- the specification is produced, docs-only validation passes, `Log.md` is
  updated, and the Galaxias wake-up is sent;
- a blocker prevents a defensible spec without crossing the goal boundary.

## Final Response Requirements

Report:

- branch, HEAD, and `git status --short --branch`;
- files created or modified;
- recommended dry-run subset and later production source;
- whether the intervention matrix should be retained or revised before
  implementation;
- validation commands and outcomes;
- whether the Galaxias wake-up was sent;
- any decisions needed from Galaxias or Barry.
