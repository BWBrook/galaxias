# Log

## Current Status

Not started by action agent. Goal packet created by supervisor on 2026-06-03.

## Starting State

- branch/remote: `main...origin/main`
- dirty state at supervisor publication: clean
- goal publication path:
  `docs/goals/001-module5-counterfactual-design-and-smoke/`
- commit/push policy: action agent may commit and push exact-path changes after
  validation passes

## Milestone Notes

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

- validation: pending
- tracked changes: pending
- untracked changes: pending
- recommended next step: pending action-agent execution
