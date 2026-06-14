# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`. Treat repo-local
instructions and this packet as the source of truth. Do not read
`/Users/bwbrook/chief_of_staff` or `/Users/bwbrook/work/goal_composer`.

This goal is docs/spec/decision-only. Do not edit code, tests, tracked CSV
contracts, generated outputs, or runner/inspection commands.

## Starting State Guard

1. Record:
   - `pwd`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse --short=12 HEAD`
   - `git status --short --branch`

2. Expected pre-work dirty state is limited to the accepted Goal 005/006
   context plus this Goal 007 packet:
   - `M Makefile`
   - `M README.md`
   - `M src/galaxias_model/module5_counterfactual.py`
   - `?? docs/goals/005-module5-dry-run-production-spec/`
   - `?? docs/goals/006-module5-real-proposal-dry-run/`
   - `?? docs/goals/007-module5-intervention-matrix-review/`
   - `?? docs/module5_dry_run_production_spec.md`
   - `?? scripts/inspect_module5_real_proposal_dry_run.py`
   - `?? scripts/run_module5_real_proposal_dry_run.py`
   - `?? src/galaxias_model/module5_dry_run_inspect.py`
   - `?? src/galaxias_model/module5_proposals.py`
   - `?? tests/test_module5_dry_run_inspection.py`
   - `?? tests/test_module5_real_proposal_dry_run.py`

3. If any other pre-work dirty state exists, stop and report it to Galaxias
   before editing.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- `docs/module5_dry_run_production_spec.md`
- `docs/module5_counterfactual_attribution_plan.md`
- `docs/goals/004-module5-production-readiness/Goal.md`
- `docs/goals/004-module5-production-readiness/Runbook.md`
- `docs/goals/005-module5-dry-run-production-spec/Log.md`
- `docs/goals/006-module5-real-proposal-dry-run/Log.md`
- `data/module5_counterfactual_interventions.csv`
- `data/module4_5_family_decision_table.csv`
- `data/module4_5_proposal_set_membership.csv`

You may inspect the existing ignored Goal 006 dry-run inspection summary if it
is already present, but do not regenerate outputs.

## Tasks

### Task 1: Log Starting State

- Confirm the working directory, branch, HEAD, and dirty state.
- Confirm the dirty state matches the expected Goal 005/006/007 surface.
- Update `Log.md` with the starting state and boundary confirmation.

### Task 2: Build The Current Matrix Summary

- Summarize the current 10-row intervention table by family, role,
  intervention axis, production status, and negative-reference flag.
- Keep the summary descriptive. Do not change the CSV.

### Task 3: Audit Rows Against Mechanism Roles

For each current row, classify:

- production-ready candidate;
- sensitivity-only candidate;
- diagnostic-only candidate;
- dry-run-only row;
- not recommended without revision.

For each classification, give a short reason grounded in:

- the family role from `data/module4_5_family_decision_table.csv`;
- the mechanism question in
  `data/module5_counterfactual_interventions.csv`;
- Goal 005 and Goal 006 non-claim boundaries.

### Task 4: Identify Candidate Changes

Evaluate at least these candidate changes:

- add `climbing_only` / `no_climbing_pressure`;
- keep or demote `climbing_only` / `no_trout_pressure`;
- add `transient_perfect_storm` / `no_trout_pressure`;
- add `transient_perfect_storm` / `no_trout_or_climbing_pressure`;
- keep negative references as status-quo diagnostics only;
- exclude negative references from production;
- add diagnostic interventions for negative references;
- defer pressure-removal versus no-invasion/no-stocking state scenarios to a
  later model-design goal.

### Task 5: Make A Recommendation

Pick a clear recommendation. Do not leave it as an undecided list.

Recommended default, unless the evidence points elsewhere:

- keep the current matrix as the dry-run/diagnostic matrix;
- revise the production attribution matrix before production;
- use a future implementation goal to edit the intervention CSV only after
  Galaxias/Barry approve the revised matrix.

### Task 6: Draft The Memo

Create `docs/module5_intervention_matrix_review.md` with the structure in
`Goal.md`.

Be concise but explicit. Barry should be able to approve, reject, or modify
the next step without rereading all prior goal logs.

### Task 7: Validate Docs-Only Work

Run:

```bash
git status --short --branch
git diff --check
```

Run a direct trailing-whitespace scan over:

- `docs/goals/007-module5-intervention-matrix-review/`
- `docs/module5_intervention_matrix_review.md`

Run a narrow marker scan over changed/new text for language around:

- production attribution;
- production-ready;
- remote compute;
- outputs;
- manuscript;
- commit;
- push.

Marker hits are allowed only when they are boundary, non-claim, or stop-point
language.

### Task 8: Final Log And Wake-Up

Update `Log.md` with:

- files changed;
- validation commands and outcomes;
- final status;
- recommendation;
- blockers or questions.

Send a short wake-up to Galaxias thread
`019eaac3-85f6-7853-bc28-a4d905dadfc3` on completion or blockage.
