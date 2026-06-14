# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`. Treat repo-local
instructions and this packet as the source of truth. Do not read
`/Users/bwbrook/chief_of_staff` or `/Users/bwbrook/work/goal_composer`.

This goal is a narrow docs-and-contract revision. Do not implement project
science, run simulations, regenerate outputs, or broaden into production
planning.

## Starting State Guard

1. Record:
   - `pwd`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse --short=12 HEAD`
   - `git status --short --branch`

2. Expected pre-work dirty state is limited to accepted Goal 005/006/007
   material plus this Goal 008 packet:
   - `M Makefile`
   - `M README.md`
   - `M src/galaxias_model/module5_counterfactual.py`
   - `?? docs/goals/005-module5-dry-run-production-spec/`
   - `?? docs/goals/006-module5-real-proposal-dry-run/`
   - `?? docs/goals/007-module5-intervention-matrix-review/`
   - `?? docs/goals/008-module5-production-matrix-contract-revision/`
   - `?? docs/module5_dry_run_production_spec.md`
   - `?? docs/module5_intervention_matrix_review.md`
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
- `docs/module5_intervention_matrix_review.md`
- `docs/module5_dry_run_production_spec.md`
- `docs/module5_counterfactual_attribution_plan.md`
- `docs/goals/005-module5-dry-run-production-spec/Log.md`
- `docs/goals/006-module5-real-proposal-dry-run/Log.md`
- `docs/goals/007-module5-intervention-matrix-review/Goal.md`
- `docs/goals/007-module5-intervention-matrix-review/Log.md`
- `data/module5_counterfactual_interventions.csv`
- `data/module4_5_family_decision_table.csv`
- `scripts/validate_module5_counterfactual_contract.py`
- `tests/test_module5_counterfactual_contract.py`

Do not inspect ignored generated outputs unless you need to confirm that this
goal is not touching them.

## Tasks

### Task 1: Log Starting State

- Confirm working directory, branch, HEAD, and dirty state.
- Confirm the dirty state matches the expected accepted Goal 005/006/007
  surface plus this Goal 008 packet.
- Update `Log.md` with starting state and boundary confirmation.

### Task 2: Add Focused Contract Safeguard

Add or update a focused contract test if the current test surface does not
already lock the revised matrix shape. The safeguard should check the actual
default intervention contract, not a generated output.

It should cover:

- total row count after revision;
- expected new intervention IDs;
- expected family-axis shape;
- negative-reference families remaining status-quo only;
- unchanged `production_status` vocabulary unless you have stopped and
  received explicit approval to alter it.

Keep the test narrow. Do not add simulation, runner, proposal, or output
inspection tests for this goal.

### Task 3: Revise The Intervention CSV

Edit `data/module5_counterfactual_interventions.csv` to add:

- `m5_climbing_only_no_climbing_pressure`
- `m5_transient_perfect_storm_no_trout_pressure`
- `m5_transient_perfect_storm_no_trout_or_climbing_pressure`

Preserve current row IDs and row intent. Do not delete or rename existing rows.

Recommended treatment:

- keep existing status-quo rows as `implemented`;
- keep pressure-removal rows as `design_only`;
- use clear labels/questions/notes to distinguish production-candidate
  pressure-removal contrasts from diagnostic sidecar rows;
- update stale notes that imply local hooks are missing.

### Task 4: Create The Contract Note

Create `docs/module5_production_matrix_contract.md`.

The note should summarize:

- what was approved from Goal 007;
- the final 13-row family-axis shape;
- why `climbing_only` / `no_trout_pressure` is retained only as a diagnostic
  sidecar/control contrast;
- why negative references remain status-quo diagnostics only;
- what is still undecided before production planning;
- validation evidence;
- stop points.

### Task 5: Validate Contract And Docs

Run the required validation commands from `Runbook.md`.

If a command fails, diagnose narrowly. Do not repair by broad refactor. If the
failure implies the goal packet is under-specified or requires a broader
semantic decision, stop and wake Galaxias.

### Task 6: Final Log And Wake-Up

Update `Log.md` with:

- files changed;
- final matrix row count and family-axis summary;
- validation commands and outcomes;
- any additional tests run and why;
- final status;
- blockers or questions.

Send a short wake-up to Galaxias thread
`019eaac3-85f6-7853-bc28-a4d905dadfc3` on completion or blockage.
