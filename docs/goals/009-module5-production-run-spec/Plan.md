# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`. Treat repo-local
instructions and this packet as the source of truth. Do not read
`/Users/bwbrook/chief_of_staff`, `/Users/bwbrook/work/goal_composer`, or
`/Users/bwbrook/work/nectar` in this goal.

This is a docs/specification goal. Do not edit code, tests, CSV contracts,
Makefile targets, generated outputs, or remote state.

## Starting State Guard

1. Record:
   - `pwd`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse --short=12 HEAD`
   - `git status --short --branch`

2. Expected pre-work dirty state is limited to accepted Goal 005/006/007/008
   material plus this Goal 009 packet:
   - `M Makefile`
   - `M README.md`
   - `M data/module5_counterfactual_interventions.csv`
   - `M src/galaxias_model/module5_counterfactual.py`
   - `M tests/test_module5_counterfactual_contract.py`
   - `?? docs/goals/005-module5-dry-run-production-spec/`
   - `?? docs/goals/006-module5-real-proposal-dry-run/`
   - `?? docs/goals/007-module5-intervention-matrix-review/`
   - `?? docs/goals/008-module5-production-matrix-contract-revision/`
   - `?? docs/goals/009-module5-production-run-spec/`
   - `?? docs/module5_dry_run_production_spec.md`
   - `?? docs/module5_intervention_matrix_review.md`
   - `?? docs/module5_production_matrix_contract.md`
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
- `docs/module5_intervention_matrix_review.md`
- `docs/module5_production_matrix_contract.md`
- `docs/module5_counterfactual_attribution_plan.md`
- `docs/goals/005-module5-dry-run-production-spec/Log.md`
- `docs/goals/006-module5-real-proposal-dry-run/Log.md`
- `docs/goals/007-module5-intervention-matrix-review/Log.md`
- `docs/goals/008-module5-production-matrix-contract-revision/Log.md`
- `data/module4_5_family_decision_table.csv`
- `data/module4_5_proposal_set_membership.csv`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`

You may inspect source files and scripts in read-only mode only if needed to
understand currently available entrypoints and provenance fields. Do not edit
them.

## Tasks

### Task 1: Log Starting State

- Confirm working directory, branch, HEAD, and dirty state.
- Confirm the dirty state matches the expected accepted Goal 005/006/007/008
  surface plus this Goal 009 packet.
- Update `Log.md` with starting state and boundary confirmation.

### Task 2: Summarize Production Inputs

Using tracked CSVs and accepted docs, summarize:

- accepted proposal counts by family;
- available proposal sets (`accepted`, `family_winners`, `global_winners`,
  `near_frontier_absolute`, `near_frontier_relative`);
- the Goal 008 13-row intervention matrix;
- outcome-schema/provenance fields that matter for production review.

Use read-only Python/pandas summaries if helpful. Do not write output files.

### Task 3: Recommend Proposal And Family Treatment

Make a clear recommendation for:

- production proposal source and whether to use all accepted proposals or a
  stratified sample;
- primary versus sensitivity family reporting;
- family weighting or a decision to avoid a single blended estimate;
- diagnostic treatment of `m5_climbing_only_no_trout_pressure`;
- negative-reference treatment.

If recommending a staged path, name the stages explicitly and state which one
the next execution goal should implement.

### Task 4: Recommend Replicate And Seed Policy

Recommend:

- stochastic replicate count;
- deterministic base label;
- per-pair seed derivation rule;
- restart rules;
- provenance fields needed to prove common-random-number pairing and
  reproducibility.

Calculate expected output rows for the recommended design and at least one
smaller fallback if relevant.

### Task 5: Specify Remote Execution Model

Write the provisional `deep-server` execution plan without running it.

Include:

- SSH alias preference: `deep-server-ts` or `utas-ubuntu`;
- `tmux` session naming convention;
- remote repo path under `/data/codex/repos`;
- run-specific scratch path under `/data/codex/scratch`;
- durable artifact path under `/data/codex/artifacts`;
- log/provenance paths;
- tiny remote-smoke gate;
- production-execution gate;
- cleanup and pull-back policy.

Do not run SSH, `tmux`, `rsync`, `scp`, or any remote command.

### Task 6: Draft The Spec

Create `docs/module5_production_run_spec.md` with the structure required in
`Goal.md`.

The spec should be decisive. It may include alternatives, but it must identify
the recommended next execution shape and where Galaxias/Barry approval is
still required.

### Task 7: Validate Docs-Only Work

Run:

```bash
git status --short --branch
git diff --check
```

Run trailing-whitespace and marker scans as specified in `Runbook.md`.

Review marker hits manually. They should be recommendation, boundary,
non-claim, stop-point, or future-gate language.

### Task 8: Final Log And Wake-Up

Update `Log.md` with:

- files changed;
- recommendation summary;
- expected row count(s);
- validation commands and outcomes;
- final status;
- risks/questions.

Send a short wake-up to Galaxias thread
`019eaac3-85f6-7853-bc28-a4d905dadfc3` on completion or blockage.
