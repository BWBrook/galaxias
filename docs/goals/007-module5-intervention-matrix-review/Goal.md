# Goal: Module 5 Intervention Matrix Review

## Objective

Create a decision-ready review of the current Module 5 intervention matrix
before any production-sized attribution planning begins.

This is a spec/decision goal. It does not authorize data-contract edits,
production attribution, new simulations, remote compute, tracked generated
outputs, or manuscript-level interpretation.

## Why This Matters

Goal 006 proved the current 10-row matrix is runnable with real Module 4.5
proposal rows. That is a plumbing result, not a scientific approval of the
matrix for production attribution.

The current matrix is asymmetric:

- `persistent_joint_cause`: `status_quo`, `no_trout_pressure`,
  `no_climbing_pressure`, `no_trout_or_climbing_pressure`;
- `climbing_only`: `status_quo`, `no_trout_pressure`;
- `transient_perfect_storm`: `status_quo`, `no_climbing_pressure`;
- `habitat_only_null`: `status_quo` negative reference;
- `trout_only`: `status_quo` negative reference.

Before production, Galaxias and Barry need a defensible decision about whether
that asymmetry is intentional, should be revised, or should be confined to
dry-run diagnostics.

## Scope

In scope:

- Create `docs/module5_intervention_matrix_review.md`.
- Update this goal `Log.md`.
- Review the current matrix row by row.
- Compare each row against the current Module 5 family roles and mechanism
  interpretation.
- Identify candidate missing, redundant, or diagnostic-only rows.
- Recommend one of:
  - keep the current matrix for production;
  - revise the matrix before production;
  - split the current dry-run/diagnostic matrix from a future production
    attribution matrix.
- Define the next implementation goal if a matrix revision is recommended.

Out of scope:

- No edits to `data/module5_counterfactual_interventions.csv`.
- No edits to `data/module5_counterfactual_outcome_schema.csv`.
- No code, test, Makefile, runner, or inspector changes.
- No generated-output creation, regeneration, promotion, or deletion.
- No simulations, dry-run reruns, validation suites, remote compute, or remote
  probes.
- No production proposal sampling, family weighting, replicate-count, compute
  target, or artifact-retention decision beyond what is needed to frame matrix
  choices.
- No manuscript claims, causal proof language, or production attribution
  interpretation.
- No staging, commit, push, PR, or publication.

## Required Deliverables

1. Goal packet:
   - `Goal.md`
   - `Plan.md`
   - `Runbook.md`
   - `Log.md`

2. Matrix review memo:
   - `docs/module5_intervention_matrix_review.md`

3. Clear recommendation:
   - preferred matrix path;
   - rationale;
   - explicit non-claims;
   - stop points and next-goal shape.

## Review Questions

Answer these directly in the memo:

1. Is the current `persistent_joint_cause` four-row block production-ready?
2. Should `climbing_only` include `no_climbing_pressure`, given that climbing
   is its active mechanism and the current row instead removes trout pressure?
3. Should `climbing_only` retain `no_trout_pressure` as a negative/control
   contrast, or should that row be diagnostic-only?
4. Should `transient_perfect_storm` include `no_trout_pressure` and/or
   `no_trout_or_climbing_pressure` to separate early trout overshoot from later
   climbing pressure?
5. Should negative references remain status-quo diagnostics only, be excluded
   from production, or receive explicit diagnostic interventions?
6. Should production distinguish pressure removal from state/removal scenarios
   such as no stocking, no invasion, no transient overshoot, or habitat-buffer
   interventions?
7. Which rows should be labelled production-ready, sensitivity-only,
   diagnostic-only, or not recommended?

## Expected Memo Structure

`docs/module5_intervention_matrix_review.md` should include:

- current state and non-claims;
- evidence inputs reviewed;
- current matrix summary;
- row-by-row audit table;
- candidate row changes table;
- negative-reference treatment;
- dry-run versus production matrix distinction;
- recommendation;
- proposed next goal;
- approval gates and stop points.

## Done When

- The memo is decision-ready for Galaxias/Barry review.
- The goal log records starting state, files read, files changed, validation
  checks, and final status.
- The action repo has only the expected Goal 005/006 dirty surface plus the
  Goal 007 packet/memo.
- Docs-only validation passes:
  - `git status --short --branch`;
  - `git diff --check`;
  - narrow trailing-whitespace scan over Goal 007 and the memo;
  - marker scan confirming production/remote/manuscript language is boundary
    or non-claim language.
- `pedder` sends a short wake-up to the Galaxias orchestrator thread on
  completion or blockage.
