# Plan

## Milestones

## Milestone 1: Orient And Freeze The Starting State

Acceptance criteria:

- Working directory is `/Users/bwbrook/papers/galaxias`.
- `git status --short --branch` has been recorded in `Log.md`.
- Read-first files have been inspected:
  - `AGENTS.md`
  - `README.md`
  - `docs/gated_action_plan_module4_5_and_beyond.md`
  - `docs/module4_5_mechanism_interpretation_plan.md`
  - `docs/module4_5_mechanism_interpretation_review.md`
  - `data/module4_5_family_decision_table.csv`
  - `data/README.md`
  - `Makefile`

Validation:

- No validation command is required beyond recording the starting git state.
- If the worktree is not clean at the start, preserve existing changes and
  record them before editing.

## Milestone 2: Draft The Module 5 Design Document

Acceptance criteria:

- `docs/module5_counterfactual_attribution_plan.md` exists.
- The document states:
  - Module 5 purpose and non-purpose
  - Module 4.5 ensemble roles
  - primary and sensitivity comparisons
  - intervention axes and what each axis holds constant
  - endpoint families and matched-comparison logic
  - stochastic/detection-linked emphasis
  - production-readiness gate for the next goal
  - residual scientific caveats
- The document does not claim that counterfactual results have been run.

Validation:

- Re-read the document against `Goal.md` and record any intentional deviations
  in `Log.md`.

## Milestone 3: Add Structured Contract Tables

Acceptance criteria:

- `data/module5_counterfactual_interventions.csv` exists with the required
  columns from `Goal.md`.
- `data/module5_counterfactual_outcome_schema.csv` exists with the required
  schema columns from `Goal.md`.
- Intervention rows cover:
  - `persistent_joint_cause` as `primary`
  - `climbing_only` as `sensitivity`
  - `transient_perfect_storm` as `sensitivity`
  - `habitat_only_null` as `negative_reference`
  - `trout_only` as `negative_reference`
- The intervention contract distinguishes runnable/currently expressible rows
  from `design_only` rows.
- `data/README.md` describes both new data files.

Validation:

- Inspect the CSV headers and row counts with a lightweight Python or shell
  check.
- Record the row counts in `Log.md`.

## Milestone 4: Add Contract Validator And Focused Test

Acceptance criteria:

- `scripts/validate_module5_counterfactual_contract.py` validates the two new
  CSV contracts against Module 4.5 family decisions.
- `tests/test_module5_counterfactual_contract.py` exercises the validator
  against the tracked contract and at least one failing temporary contract.
- If a Makefile target is added, it runs only the contract validator and stays
  cheap.

Validation:

- `uv run python scripts/validate_module5_counterfactual_contract.py`
- `uv run pytest tests/test_module5_counterfactual_contract.py -q`

## Milestone 5: Run The Repo Gate And Publish If Clean

Acceptance criteria:

- `make fast-check` passes, or any failure is clearly unrelated and documented
  with evidence. Do not publish if this goal's own changes fail validation.
- `git diff --check` passes.
- `Log.md` has final validation evidence, artefact paths, caveats, and next
  recommendation.
- If validation passes, commit and push exact paths for this goal.

Validation:

- `make fast-check`
- `git diff --check`
- `git status --short --branch`
- After committing, `git status --short --branch`
- After pushing, record the pushed branch and commit hash in `Log.md`.

## Stop-And-Fix Rule

If validation fails, repair or narrow the failure before moving to the next
milestone. Do not accumulate known-broken work. If fixing a failure would
require production simulations, remote compute, new scientific assumptions, or
broad refactoring, stop and report the blocker instead of expanding scope.
