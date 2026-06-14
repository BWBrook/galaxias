# Module 5 Production Matrix Contract

## Current State And Non-Claims

Goal 008 revises the tracked Module 5 intervention contract from the
10-row dry-run/diagnostic matrix to the approved 13-row production-planning
matrix. This is a contract revision only.

This note does not authorise production attribution, production proposal
sampling, family weighting, replicate-count choices, simulations, dry-run
reruns, generated-output promotion, remote compute, manuscript claims, commit,
or push.

The local pressure-removal hook exists for the current pressure axes and was
exercised by Goal 006. The remaining distinction is contractual: pressure
removal rows remain `design_only` until production use is approved and
validated through a later planning gate.

## Source Decision

The approved source decision is the Goal 007 recommendation in
`docs/module5_intervention_matrix_review.md`:

- split the current dry-run/diagnostic matrix from the future production
  attribution matrix;
- revise the tracked production-planning matrix before production-sized
  execution;
- keep negative-reference families as status-quo diagnostics only.

## Final 13-Row Matrix

| family_id | module5_role | intervention axes | row count |
| --- | --- | --- | ---: |
| `persistent_joint_cause` | `primary` | `status_quo`, `no_trout_pressure`, `no_climbing_pressure`, `no_trout_or_climbing_pressure` | 4 |
| `climbing_only` | `sensitivity` | `status_quo`, `no_climbing_pressure`, `no_trout_pressure` | 3 |
| `transient_perfect_storm` | `sensitivity` | `status_quo`, `no_trout_pressure`, `no_climbing_pressure`, `no_trout_or_climbing_pressure` | 4 |
| `habitat_only_null` | `negative_reference` | `status_quo` | 1 |
| `trout_only` | `negative_reference` | `status_quo` | 1 |

New intervention IDs added by this contract revision:

- `m5_climbing_only_no_climbing_pressure`
- `m5_transient_perfect_storm_no_trout_pressure`
- `m5_transient_perfect_storm_no_trout_or_climbing_pressure`

Preserved contract choices:

- existing intervention IDs were not deleted or renamed;
- `production_status` remains an implementation/execution status field;
- status-quo rows remain `implemented`;
- pressure-removal rows remain `design_only`;
- negative-reference families receive no pressure-removal rows.

## Diagnostic-Sidecar Treatment

`m5_climbing_only_no_trout_pressure` is retained as a diagnostic sidecar and
control contrast. It is not the headline climbing-only production contrast,
because the active climbing-only mechanism is tested by
`m5_climbing_only_no_climbing_pressure`.

This row may still help reviewers separate a control-style trout-pressure
removal from direct active-mechanism removal, but it should not be weighted as
the primary climbing-only production attribution contrast without a later
approval gate.

## Negative-Reference Treatment

`habitat_only_null` and `trout_only` remain status-quo diagnostics only. They
have no accepted-frontier support in the current Module 4.5 decision table and
should remain outside the production attribution ensemble unless Galaxias and
Barry explicitly approve a later diagnostic expansion.

No negative-reference pressure-removal rows were added.

## Still Undecided Before Production Planning

The following remain out of scope and undecided:

- production proposal source and sampling rule;
- family weighting or sensitivity-appendix treatment;
- stochastic replicate count;
- compute target and storage budget;
- artifact retention and promotion rules;
- remote smoke or production execution plan;
- pressure-removal semantic changes or new scenario hooks;
- claim-language boundary for reviewed production results.

## Validation Evidence

Goal 008 validation evidence is recorded in
`docs/goals/008-module5-production-matrix-contract-revision/Log.md`.

The required contract checks passed:

- `uv run python scripts/validate_module5_counterfactual_contract.py`
  reported `Module 5 counterfactual contract validation passed.`
- `uv run pytest tests/test_module5_counterfactual_contract.py -q` reported
  `4 passed`.
- The direct matrix-shape check reported `matrix shape ok`.

The final docs/git checks passed:

- `git diff --check` passed with no output.
- The trailing-whitespace scan over changed contract, docs, and test files
  returned no matches.
- The marker scan returned expected boundary, hook-status, contract-status,
  diagnostic-sidecar, and stop-point language.
- `git status --short --branch` reported the expected accepted Goal 005/006/007
  surface plus the Goal 008 packet and changed contract/note/test files.

## Stop Points

Stop for explicit approval before:

- changing `production_status` vocabulary or validator enum semantics;
- deleting, renaming, or reinterpreting existing intervention IDs;
- adding pressure-removal rows for negative-reference families;
- changing pressure-removal semantics or adding new scenario hooks;
- editing runner, simulator, proposal, dry-run, Makefile, or generated-output
  code;
- running simulations, dry-run commands, broad validation suites, remote
  probes, or production-sized work;
- staging, committing, pushing, publishing, or opening a PR;
- making final causal, manuscript-level, or production attribution claims.
