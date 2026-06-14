# Log

## Current Status

Goal 011 execution by `pedder` is complete. Module 5 now carries
source-context proposal identity through local dry-run seed derivation,
matched-pair IDs, run IDs, output schema, provenance, and disk inspection.
The local validation gate passed, and the wake-up is pending.

## Starting State

- Goal path: `docs/goals/011-module5-source-context-identity/`
- Action repo: `/Users/bwbrook/papers/galaxias`
- Branch at start: `main`
- HEAD at start: `7f77fc4b43e6`
- Confirmed working directory: `/Users/bwbrook/papers/galaxias`
- Initial status:
  - `## main...origin/main`
  - ` M Makefile`
  - ` M README.md`
  - ` M data/module5_counterfactual_interventions.csv`
  - ` M src/galaxias_model/module5_counterfactual.py`
  - ` M tests/test_module5_counterfactual_contract.py`
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
- Pre-work dirty state matched the expected accepted Goal 005/006/007/008/009/010
  surface plus this Goal 011 packet. No unexpected dirty files were observed
  before edits.
- Reconfirmed boundaries:
  no `/Users/bwbrook/chief_of_staff`, `/Users/bwbrook/work/goal_composer`, or
  `/Users/bwbrook/work/nectar`; no remote SSH, `deep-server`, `utas-ubuntu`,
  `tmux`, remote mirrors, production run, 25-replicate rehearsal, tracked
  intervention-matrix changes, staging, commit, push, PR, publication,
  production-attribution claims, manuscript claims, or contact with Barry or
  Chief.

## Milestone Notes

### 2026-06-13 | Read-first guard

- Read the Goal 011 packet first: `Goal.md`, `Plan.md`, `Runbook.md`, and
  this `Log.md`.
- Read repo-local instructions and accepted context:
  `AGENTS.md`, `README.md`, `docs/module5_production_run_spec.md`,
  `docs/module5_remote_smoke_preflight.md`,
  `docs/module5_production_matrix_contract.md`, Goal 009 `Log.md`, and
  Goal 010 `Log.md`.
- Read the required local source/test/contract surfaces:
  `data/module4_5_proposal_set_membership.csv`,
  `data/module4_raw_artifact_manifest.csv`,
  `data/module5_counterfactual_outcome_schema.csv`,
  `src/galaxias_model/module5_proposals.py`,
  `src/galaxias_model/module5_counterfactual.py`,
  `src/galaxias_model/module5_dry_run_inspect.py`,
  `scripts/validate_module5_counterfactual_contract.py`,
  `tests/test_module5_real_proposal_dry_run.py`,
  `tests/test_module5_dry_run_inspection.py`, and
  `tests/test_module5_counterfactual_contract.py`.

### 2026-06-13 | Identity risk confirmed

- Structured accepted-frontier source check:
  - accepted rows: `750`
  - unique bare `proposal_id` values: `246`
  - repeated bare `proposal_id` values: `158`
  - maximum bare-ID reuse: `7`
  - unique candidate source-context tuples: `750`
  - duplicate source-context tuples: `0`
- Duplicate bare-ID examples:
  `climbing_only:p00005:2`, `climbing_only:p00013:4`,
  `climbing_only:p00015:4`, `climbing_only:p00036:5`,
  `climbing_only:p00088:5`.
- Example repeated bare ID:
  `climbing_only:p00005` appears as:
  - `module4_observation_sensitivity_20260522T101942Z|ct007_occupancy_primary|20260410|ct007_occupancy_primary_seed20260410|climbing_only|climbing_only:p00005`
  - `module4_observation_sensitivity_20260522T101942Z|late_bridge_soft|20260410|late_bridge_soft_seed20260410|climbing_only|climbing_only:p00005`

### 2026-06-13 | RED-first source-identity tests

- Added focused source-identity assertions before implementation.
- RED command:
  `uv run pytest tests/test_module5_source_identity.py tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q`
- RED result: failed as expected with `9 failed, 8 passed`.
- Expected RED failures included:
  - missing `build_proposal_source_key`;
  - missing `SelectedProposal.proposal_source_key`;
  - missing `proposal_source_key`, `module4_run_id`, and `run_dir_name` output
    schema/rows;
  - missing inspection summary field `proposal_source_key_count`;
  - missing source-identity columns for malformed-output tests;
  - missing required source-identity schema rows.
- These failures matched the Goal 011 source-identity gap rather than an
  unrelated validation failure.

### 2026-06-13 | Implementation

- Chosen source-identity contract:
  `proposal_source_key = module4_run_id|variant_id|seed|run_dir_name|family_id|proposal_id`.
- Added `PROPOSAL_SOURCE_KEY_FIELDS` and `build_proposal_source_key`.
- Extended `SelectedProposal` with `module4_run_id` and
  `proposal_source_key`.
- Updated Module 5 seed derivation to use
  `base_label|proposal_source_key|intervention_id|stochastic_replicate_id`.
- Updated `matched_pair_id` to
  `<proposal_source_key>|<intervention_id>|r<stochastic_replicate_id>`.
- Updated run IDs to `<matched_pair_id>|baseline` and
  `<matched_pair_id>|counterfactual`.
- Added `proposal_source_key`, `module4_run_id`, and `run_dir_name` to the
  matched-outcome schema. The schema now has `53` rows.
- Updated the `proposal_id` schema description so it is source-context scoped,
  not globally unique.
- Updated real-proposal dry-run provenance with source identity fields,
  source-key strategy, selected source keys, selected source rows, and the new
  seed-derivation rule.
- Updated disk inspection with a `source_identity` check:
  required columns, no blank source keys, key consistency with visible source
  fields, no duplicate `(proposal_source_key, intervention_id,
  stochastic_replicate_id)` grains, and provenance/source-field agreement.
- Updated matched-pair inspection to verify exact source-key-based
  `matched_pair_id`, `run_id_baseline`, and `run_id_counterfactual` shapes.
- Created `docs/module5_source_identity_contract.md`.
- Updated `docs/module5_production_run_spec.md` to point at the implemented
  source identity contract and the 53-column schema.

## Validation Evidence

- GREEN focused source-identity command:
  `uv run pytest tests/test_module5_source_identity.py tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q`
  - Result: `17 passed`.
- Required pytest command:
  `uv run pytest tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q`
  - Result: `15 passed`.
- New focused test file:
  `uv run pytest tests/test_module5_source_identity.py -q`
  - Result: `2 passed`.
- Contract validation:
  `uv run python scripts/validate_module5_counterfactual_contract.py`
  - Result: `Module 5 counterfactual contract validation passed.`
- Local dry run:
  `make module5-dry-run`
  - Result: passed; wrote ignored dry-run matched outcomes and provenance under
    `outputs/module5_dry_run_baseline_current_20260410/`.
- Local dry-run inspection:
  `make module5-dry-run-inspect`
  - Result: passed.
  - Summary facts:
    - `all_checks_passed=True`
    - `row_count=65`
    - `column_count=53`
    - `proposal_count=5`
    - `proposal_source_key_count=5`
    - `intervention_count=13`
    - `expected_replicates=5`
    - `source_identity=True`
    - `replicate_coverage=True`
    - `matched_pair_count=65`
  - Inspection checks passed:
    schema columns, row count, proposal IDs, intervention IDs,
    replicate coverage, source identity, matched-pair IDs,
    common-random-seed pairing, provenance labels, and dry-run boundary.
  - Seed mismatches: `0`.
  - Provenance `production_attribution=False`.
  - Matched outcomes SHA-256:
    `2746a642a9b68a80c6ac6b5b723c60d637e5b54d7a941e4b5cb95b012af41aba`.
- Full local gate:
  `make fast-check`
  - Result: portability passed, compileall passed, pytest reported
    `83 passed, 5 deselected`.
- `git diff --check`
  - Result: passed with no output.
- Direct trailing-whitespace scan:
  `rg -n "[ \t]+$" docs/goals/011-module5-source-context-identity docs/module5_source_identity_contract.md docs/module5_production_run_spec.md data/module5_counterfactual_outcome_schema.csv scripts/validate_module5_counterfactual_contract.py src/galaxias_model/module5_proposals.py src/galaxias_model/module5_counterfactual.py src/galaxias_model/module5_dry_run_inspect.py tests/test_module5_counterfactual_contract.py tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_source_identity.py`
  - Result: no matches.
- Marker scan:
  `rg -n "production attribution|production-ready|deep-server|tmux|outputs/|manuscript|commit|push" docs/goals/011-module5-source-context-identity docs/module5_source_identity_contract.md docs/module5_production_run_spec.md`
  - Result: hits reviewed as expected boundary, non-claim, local-validation,
    artifact-path, stop-point, risk, or future-gate language.

## Generated Outputs

Authorized ignored local validation outputs were regenerated under:

- `outputs/module5_dry_run_baseline_current_20260410/matched_outcomes.csv`
- `outputs/module5_dry_run_baseline_current_20260410/provenance.json`
- `outputs/module5_dry_run_baseline_current_20260410/inspection/inspection_summary.json`
- `outputs/module5_dry_run_baseline_current_20260410/inspection/inspection_checks.csv`
- `outputs/module5_dry_run_baseline_current_20260410/inspection/inspection_report.md`

No generated outputs were promoted into tracked files.

## Changed Files

Goal 011 changed or added:

- `data/module5_counterfactual_outcome_schema.csv`
- `scripts/validate_module5_counterfactual_contract.py`
- `src/galaxias_model/module5_proposals.py`
- `src/galaxias_model/module5_counterfactual.py`
- `src/galaxias_model/module5_dry_run_inspect.py`
- `tests/test_module5_source_identity.py`
- `tests/test_module5_real_proposal_dry_run.py`
- `tests/test_module5_dry_run_inspection.py`
- `tests/test_module5_counterfactual_contract.py`
- `docs/module5_source_identity_contract.md`
- `docs/module5_production_run_spec.md`
- `docs/goals/011-module5-source-context-identity/Log.md`

Existing accepted Goal 005/006/007/008/009/010 dirty surfaces remain
uncommitted and unstaged.

## Blockers

None.

## Final Status

- Branch: `main`
- HEAD: `7f77fc4b43e6`
- Final status remains uncommitted and unstaged, with the accepted Goal
  005/006/007/008/009/010 surface plus Goal 011 changes.
- Source-identity collision risk is removed for the current local dry-run
  implementation surface: source rows with repeated bare `proposal_id` values
  have distinct source keys and seeds.
- Remaining risks/questions:
  - this goal did not implement the full 750-row production proposal source
    selection or remote artifact-resolution ladder;
  - production or rehearsal execution still needs a separate packet that
    explicitly authorises replicate count, target, partition layout, restart
    policy, artifact retention, and compact pull-back policy;
  - production attribution and manuscript language remain out of scope.
- Recommended next-goal shape:
  a bounded source-key-aware production rehearsal or production execution
  packet. The packet should choose 25-replicate rehearsal versus
  100-replicate production, freeze run ID and partition layout, verify all
  required parameter artifacts, use the Goal 011 `proposal_source_key`
  contract for restart/seed/inspection checks, and stop before production
  attribution or manuscript claims.
- Wake-up to Galaxias orchestrator thread
  `019eaac3-85f6-7853-bc28-a4d905dadfc3`: sent successfully.
