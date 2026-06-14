# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`.

Treat repo-local instructions and this Goal 011 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, or `/Users/bwbrook/work/nectar`.

This goal is local implementation and validation only. Do not use remote
compute and do not run production or rehearsal ensembles.

## Starting State Guard

1. Record:
   - `pwd`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse --short=12 HEAD`
   - `git status --short --branch`

2. Expected pre-work dirty state is the accepted Goal 005/006/007/008/009/010
   surface plus this Goal 011 packet:
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
   - `?? docs/goals/010-module5-deep-server-remote-smoke-preflight/`
   - `?? docs/goals/011-module5-source-context-identity/`
   - `?? docs/module5_dry_run_production_spec.md`
   - `?? docs/module5_intervention_matrix_review.md`
   - `?? docs/module5_production_matrix_contract.md`
   - `?? docs/module5_production_run_spec.md`
   - `?? docs/module5_remote_smoke_preflight.md`
   - `?? scripts/inspect_module5_real_proposal_dry_run.py`
   - `?? scripts/run_module5_real_proposal_dry_run.py`
   - `?? src/galaxias_model/module5_dry_run_inspect.py`
   - `?? src/galaxias_model/module5_proposals.py`
   - `?? tests/test_module5_dry_run_inspection.py`
   - `?? tests/test_module5_real_proposal_dry_run.py`

3. If any other pre-work dirty state exists, stop and report it to Galaxias
   before editing or running validation.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- `docs/module5_production_run_spec.md`
- `docs/module5_remote_smoke_preflight.md`
- `docs/module5_production_matrix_contract.md`
- `docs/goals/009-module5-production-run-spec/Log.md`
- `docs/goals/010-module5-deep-server-remote-smoke-preflight/Log.md`
- `data/module4_5_proposal_set_membership.csv`
- `data/module4_raw_artifact_manifest.csv`
- `data/module5_counterfactual_outcome_schema.csv`
- `src/galaxias_model/module5_proposals.py`
- `src/galaxias_model/module5_counterfactual.py`
- `src/galaxias_model/module5_dry_run_inspect.py`
- `scripts/validate_module5_counterfactual_contract.py`
- `tests/test_module5_real_proposal_dry_run.py`
- `tests/test_module5_dry_run_inspection.py`
- `tests/test_module5_counterfactual_contract.py`

## Task 1: Confirm The Identity Risk

- Count accepted-frontier rows and repeated bare `proposal_id` values from
  `data/module4_5_proposal_set_membership.csv`.
- Confirm that the candidate source-context tuple
  `(module4_run_id, variant_id, seed, run_dir_name, family_id, proposal_id)`
  is unique for the 750 accepted-frontier rows.
- Record the counts and at least one repeated bare-ID example in `Log.md`.

Expected reference facts from Galaxias preflight:

- accepted-frontier rows: 750;
- unique bare `proposal_id`: 246;
- repeated bare `proposal_id` values: 158;
- maximum bare-ID reuse: 7;
- unique source-context tuples using the required fields: 750.

## Task 2: Write RED Source-Identity Tests

Add or update focused tests before implementation.

Tests should fail against the current Goal 010 code because the current seed
and matched-pair identity use bare `proposal_id`.

Required failure targets:

- accepted-frontier source key uniqueness while bare IDs repeat;
- same bare `proposal_id`, different source context, same intervention, same
  replicate yields different seeds;
- same bare `proposal_id`, different source context yields different
  `matched_pair_id`, `run_id_baseline`, and `run_id_counterfactual`;
- real dry-run output contains source-identity columns;
- dry-run inspector detects source-identity corruption.

Run the focused tests and record the RED failures in `Log.md`.

## Task 3: Implement Source Identity

Implement the smallest coherent source-identity surface.

Expected behavior:

- `SelectedProposal` or an equivalent type retains `module4_run_id`,
  `run_dir_name`, and a canonical source key in addition to existing
  `variant_id`, `seed`, `family_id`, and `proposal_id`.
- A helper builds the source key from the required fields.
- Seed derivation uses `base_label|proposal_source_key|intervention_id|replicate`.
- Matched-pair IDs and run IDs use the source key.
- Default smoke rows still emit schema-conforming placeholder source identity
  rather than blank values.
- Real-proposal dry-run provenance records source-key strategy and selected
  source keys.

Prefer one clear helper over repeated string formatting.

## Task 4: Update Schema And Contract Validation

- Add required outcome-schema rows for `proposal_source_key`,
  `module4_run_id`, and `run_dir_name`.
- Update the `proposal_id` description so it no longer claims global
  uniqueness.
- Update the contract validator and contract tests if needed so the new fields
  are required.
- Preserve existing required fields and schema ordering expectations.

Do not change `data/module5_counterfactual_interventions.csv`.

## Task 5: Update Disk Inspection

Update the real-proposal dry-run inspector so it checks source identity from
disk.

Minimum checks:

- required source-identity columns exist;
- no blank source keys;
- source keys are consistent with visible source-context fields;
- no duplicate
  `(proposal_source_key, intervention_id, stochastic_replicate_id)` rows;
- matched-pair IDs and run IDs are unique and source-context based;
- the 13-row intervention matrix with 5 replicates expects 65 rows.

Add malformed-output tests for at least missing/blank source key and duplicate
source-key/intervention/replicate collision.

## Task 6: Update Documentation

Create `docs/module5_source_identity_contract.md` with:

- current non-claim boundary;
- why bare `proposal_id` is unsafe for production;
- the accepted canonical source identity fields;
- the emitted output/provenance fields;
- the seed and matched-pair identity rule;
- what the goal validates;
- what remains for later production execution.

Update `docs/module5_production_run_spec.md` if needed so it points to the new
contract rather than leaving the identity work as only a warning.

## Task 7: Validate

Run:

```bash
uv run pytest tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q
```

Run any new focused test file you created.

Run:

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
make module5-dry-run
make module5-dry-run-inspect
make fast-check
git diff --check
```

Run a trailing-whitespace scan over changed Goal 011/docs/code/test files.

Run the marker scan from `Runbook.md` and review hits manually.

If validation creates ignored outputs, leave them ignored and report their
paths. Do not stage or promote generated outputs.

## Task 8: Final Log And Wake-Up

Update `Log.md` with:

- starting state;
- source-identity counts;
- RED-first failures;
- changed files;
- generated ignored outputs, if any;
- validation commands and outcomes;
- final status;
- remaining risks/questions;
- recommended next-goal shape.

Send a short wake-up to Galaxias thread
`019eaac3-85f6-7853-bc28-a4d905dadfc3` on completion or blockage, then wait.
