# Log

## Current Status

Running and completed by action agent. Goal packet created by supervisor on
2026-06-03.

## Starting State

- branch/remote: `main...origin/main`
- dirty state at supervisor publication: clean
- goal publication path:
  `docs/goals/001-module5-counterfactual-design-and-smoke/`
- commit/push policy: action agent may commit and push exact-path changes after
  validation passes

## Milestone Notes

### 2026-06-03T00:00:00Z | Milestone 1

- Working directory confirmed as `/Users/bwbrook/papers/galaxias`.
- Recorded start-up state: `git status --short --branch` = `## main...origin/main`.
- Read mandatory preface documents from `Goal.md`, `Plan.md`, `Runbook.md`, and required
  data/docs sources.
- Confirmed required boundary rules for this goal:
  - read-only orientation on existing contract files first,
  - no Module 5 production runs,
  - no Module 4 reruns,
  - no changes to scientific defaults or family definitions.

### 2026-06-03T04:50:09Z | Milestone 2

- `docs/module5_counterfactual_attribution_plan.md` added and reviewed against
  `Goal.md`.
- The design document states:
  - Module 5 purpose and explicit non-purpose (no production attribution yet),
  - family-role mapping carried from Module 4.5,
  - sensitivity and negative-reference contrasts,
  - intervention axes and held-constant framing,
  - matched paired stochastic contrast logic,
  - deterministic caveat carry-forward and production-readiness gate.
- No production or manuscript-interpretation claims were added; wording stays at
  contract/specification level.

### 2026-06-03T04:50:09Z | Milestone 3

- Added `data/module5_counterfactual_interventions.csv` with 10 rows, 15 columns.
- Added `data/module5_counterfactual_outcome_schema.csv` with 50 rows, 6 columns.
- Intervention rows cover all required families/roles from
  `data/module4_5_family_decision_table.csv`:
  `persistent_joint_cause` (`primary`), `climbing_only` (`sensitivity`),
  `transient_perfect_storm` (`sensitivity`),
  `habitat_only_null` (`negative_reference`), `trout_only`
  (`negative_reference`).
- Included production status distinctions (`implemented` vs `design_only`) to
  mark non-executable axes explicitly.
- Updated `data/README.md` with discoverability notes for the two new contract
  files and the validator.

### 2026-06-03T04:50:09Z | Milestone 4

- Added `scripts/validate_module5_counterfactual_contract.py` to validate:
  - required columns in interventions/schema,
  - unique `intervention_id`,
  - role compatibility against `data/module4_5_family_decision_table.csv`,
  - required intervention-axis coverage,
  - required output schema field names.
- Added `tests/test_module5_counterfactual_contract.py` with:
  - happy-path validation,
  - duplicate-id failure,
  - missing-axis failure regression.
- Fixed test fixture loading to avoid brittle global-path assumptions in a
  non-packaged `scripts/` directory.

### 2026-06-03T04:50:09Z | Milestone 5

- Executed all required repository gates:
  - `uv run python scripts/validate_module5_counterfactual_contract.py` (pass),
  - `uv run pytest tests/test_module5_counterfactual_contract.py -q` (pass),
  - `make fast-check` (pass),
  - `git diff --check` (pass, no whitespace errors).
- No further repo-wide blockers discovered during execution.
- Goal committed and pushed to `origin main`.
- Final status recorded after push: `## main...origin/main` (clean worktree).

## Decisions

- This is a Module 5 design and smoke/scaffold prelude, not a production
  counterfactual run.
- The Module 4.5 decision table is treated as the ensemble contract:
  `persistent_joint_cause` primary, `climbing_only` and
  `transient_perfect_storm` sensitivity, `habitat_only_null` and `trout_only`
  negative references.
- Deterministic landmark trajectories should not be converted into extinction
  claims. Future Module 5 work must emphasize matched stochastic
  counterfactual outcomes and detection-linked endpoints.

## Blockers

None known at publication.

## Artefacts

Expected:

- `docs/module5_counterfactual_attribution_plan.md`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`
- `scripts/validate_module5_counterfactual_contract.py`
- `tests/test_module5_counterfactual_contract.py`
- `data/README.md` updates
- optional narrow Makefile validation target

## Review Notes

Supervisor should review the design document, CSV contract rows, validator
failure modes, validation output, and scope discipline before authorising any
Module 5 production or prototype run.

## Final Status

- validation: passed
- tracked changes: all expected new files and tracked updates are scoped to this
  goal.
- worktree: clean after commit and push.
- next recommendation: `Goal 002` should define and prototype the
  Module 5 runner that operationalises these intervention rows into paired runs.

### Validation evidence

- `uv run python scripts/validate_module5_counterfactual_contract.py`
- `uv run pytest tests/test_module5_counterfactual_contract.py -q`
- `make fast-check`
- `git diff --check`
- `git status --short --branch`

### Outstanding risks

- Intervention axes `no_trout_pressure`, `no_climbing_pressure`,
  `no_trout_or_climbing_pressure` are design-only until intervention override
  hooks are added to the runner.
