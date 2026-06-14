# Goal: Module 5 Source-Context Proposal Identity

## Objective

Remove the remaining proposal-identity collision risk before any Module 5
production run.

Goal 011 should make Module 5 seed derivation, matched-pair IDs, run IDs,
outcome rows, provenance, and disk inspection use explicit source-context
proposal-row identity rather than bare `proposal_id`.

This goal authorizes a careful local implementation and validation step only.
It does not authorize the 25-replicate rehearsal, the 279,500-row production
run, remote execution, staging, commit, push, PR, publication, production
attribution claims, or manuscript claims.

## Why This Matters

Goal 009 specified that the production unit is a full proposal membership row,
not a bare proposal ID. The accepted-frontier source has:

- 750 accepted proposal rows for the accepted-frontier families;
- only 246 unique bare `proposal_id` strings;
- 158 repeated bare `proposal_id` values;
- a maximum observed bare-ID reuse of 7 rows;
- 750 unique candidate source-context keys if using
  `module4_run_id`, `variant_id`, `seed`, `run_dir_name`, `family_id`, and
  `proposal_id`.

Goal 010 proved that remote execution works on `deep-server`, but it did not
fix this production identity risk. A production run must not collapse seeds,
matched-pair IDs, run IDs, provenance, restart checks, or summaries across
distinct accepted source rows that happen to share `proposal_id`.

## Required Identity Contract

Define a canonical Module 5 proposal source identity for any row from
`data/module4_5_proposal_set_membership.csv`.

The identity must include, at minimum:

- `module4_run_id`;
- `variant_id`;
- `seed`;
- `run_dir_name`;
- `family_id`;
- `proposal_id`.

The implementation should expose a deterministic string key, recommended name
`proposal_source_key`, that is stable across machines and independent of CSV
row order. A safe shape is:

```text
module4_run_id|variant_id|seed|run_dir_name|family_id|proposal_id
```

If `pedder` finds a better repo-local naming pattern, use that pattern only if
the same fields are retained and the output/provenance contract remains
explicit. Do not rely on row number, DataFrame index, sort order, or bare
`proposal_id`.

## Required Output Contract

The Module 5 matched-outcome schema should carry source identity explicitly.

Add or update required outcome columns so each output row records:

- `proposal_source_key`;
- `module4_run_id`;
- `run_dir_name`;
- the existing `variant_id`, `seed`, `family_id`, and `proposal_id`.

The existing `proposal_id` schema description must no longer claim global
uniqueness. It should state that `proposal_id` is unique only within its
source context.

Matched-pair and run IDs must include `proposal_source_key` or an equivalent
source-context tuple, for example:

```text
<proposal_source_key>|<intervention_id>|r<stochastic_replicate_id>
```

Seed derivation must include the source-context proposal identity:

```text
base_label|proposal_source_key|intervention_id|stochastic_replicate_id
```

The baseline and intervention arms must still share the same stochastic seed
inside each matched pair. Distinct source rows with the same bare
`proposal_id` must produce distinct seeds and distinct matched-pair IDs for
the same intervention and replicate.

## Scope

In scope:

- Update `SelectedProposal` or an equivalent local structure to retain the
  source-context fields needed for production identity.
- Add a canonical proposal source-key helper.
- Update Module 5 seed derivation to use source-context identity.
- Update matched-pair IDs, `run_id_baseline`, and `run_id_counterfactual` to
  include source-context identity.
- Update matched-outcome schema and output rows with explicit source identity.
- Update real-proposal dry-run provenance so it records source identity,
  source-key strategy, and the changed seed derivation.
- Update disk inspection to verify source-identity presence and uniqueness at
  the row grain needed by the current dry run.
- Update stale Goal 006-era tests that still expect the old 10-intervention /
  50-row dry-run shape. The accepted Goal 008 matrix has 13 rows, so a
  5-replicate all-intervention dry run emits 65 rows.
- Add focused RED-first tests proving duplicate bare `proposal_id` values do
  not collide when source context differs.
- Create `docs/module5_source_identity_contract.md`.
- Update `docs/module5_production_run_spec.md` if needed to point to the
  implemented identity contract.
- Update this goal `Log.md`.
- Regenerate only ignored local dry-run outputs under the existing Module 5
  dry-run output path if needed for validation.

Allowed tracked files:

- `data/module5_counterfactual_outcome_schema.csv`
- `scripts/validate_module5_counterfactual_contract.py`
- `src/galaxias_model/module5_proposals.py`
- `src/galaxias_model/module5_counterfactual.py`
- `src/galaxias_model/module5_dry_run_inspect.py`
- `src/galaxias_model/module5_smoke_inspect.py` only if needed because the
  schema changes affect the default smoke inspector.
- `scripts/run_module5_real_proposal_dry_run.py` only if CLI help or argument
  wiring needs to expose the identity change.
- `tests/test_module5_counterfactual_contract.py`
- `tests/test_module5_real_proposal_dry_run.py`
- `tests/test_module5_dry_run_inspection.py`
- `tests/test_module5_runner_prototype.py` only if the output-schema change
  requires updating default-smoke expectations.
- `tests/test_module5_smoke_inspection.py` only if the output-schema change
  requires updating default-smoke expectations.
- a new focused test file under `tests/` if cleaner than expanding an existing
  file.
- `docs/module5_source_identity_contract.md`
- `docs/module5_production_run_spec.md`
- `docs/goals/011-module5-source-context-identity/Log.md`

Out of scope:

- No production-sized execution.
- No 25-replicate rehearsal.
- No remote SSH, `deep-server`, `tmux`, remote source mirrors, or remote
  artifact changes.
- No changes to `data/module5_counterfactual_interventions.csv`.
- No changes to pressure-removal semantics or new scenario hooks.
- No proposal sampling, family weighting, production partitioning, or
  diagnostic-ordering decisions.
- No raw-output promotion into tracked docs.
- No staging, commit, push, PR, publication, or manuscript commands.
- No final causal, production-attribution, production-ready, or manuscript
  claim language.

## Required Tests And Evidence

Use RED-first where possible. At minimum, add tests that prove:

- the accepted-frontier membership rows contain repeated bare `proposal_id`
  values but unique source-context keys;
- two synthetic or real source rows with the same bare `proposal_id` but
  different source context produce different Module 5 stochastic seeds for
  the same intervention and replicate;
- two such source rows produce different `matched_pair_id`,
  `run_id_baseline`, and `run_id_counterfactual` values;
- real-proposal dry-run outputs include `proposal_source_key`,
  `module4_run_id`, and `run_dir_name`;
- current real-proposal dry-run outputs still have zero seed mismatches;
- disk inspection fails when source identity is missing, blank, duplicated at
  the proposal/intervention/replicate grain, or inconsistent with visible
  source-context fields;
- the dry-run inspector expects the current 13-row intervention matrix and
  65 rows for 5 replicates.

## Required Validation

Run and log:

- focused RED-first failure evidence for the new source-identity tests before
  implementation;
- `uv run pytest tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q`;
- any additional focused test file created for source identity;
- `uv run python scripts/validate_module5_counterfactual_contract.py`;
- `make module5-dry-run`;
- `make module5-dry-run-inspect`;
- `make fast-check`;
- `git diff --check`;
- a direct trailing-whitespace scan over changed Goal 011/docs/code/test
  files;
- a marker scan over changed Goal 011/docs files for:
  - `production attribution`
  - `production-ready`
  - `deep-server`
  - `tmux`
  - `outputs/`
  - `manuscript`
  - `commit`
  - `push`

Review marker hits manually. They should be boundary, non-claim,
local-validation, artifact-path, stop-point, risk, or future-gate language.

If `make fast-check` reveals pre-existing failures outside the Goal 011 scope,
stop and wake Galaxias with exact evidence rather than broadening.

## Stop Points

Stop and wake Galaxias before:

- changing proposal source selection, family weighting, production replicate
  count, or production partitioning;
- using a source identity that omits any of `module4_run_id`, `variant_id`,
  `seed`, `run_dir_name`, `family_id`, or `proposal_id`;
- relying on bare `proposal_id`, CSV row number, DataFrame index, or sort
  order as production identity;
- running remote commands, `tmux`, a 25-replicate rehearsal, or the
  279,500-row production execution;
- changing pressure-removal semantics, scenario hooks, or the intervention
  matrix;
- staging, committing, pushing, publishing, or opening a PR;
- making final causal, production-attribution, production-ready, or
  manuscript-level claims.

## Done When

- Source-context proposal identity is explicit in code, outcome schema,
  output rows, provenance, and inspection.
- Focused tests prove duplicate bare proposal IDs do not collide when source
  context differs.
- The current real-proposal dry run still passes with the 13-row intervention
  matrix and 5 replicates, emitting 65 rows.
- The dry-run inspector passes on valid output and fails on malformed
  source-identity cases.
- `docs/module5_source_identity_contract.md` records the accepted identity
  contract and remaining boundary.
- Validation evidence is recorded in `Log.md`.
- The action repo remains uncommitted and unstaged.
- No remote execution, production run, staging, commit, push, publication, or
  manuscript/production-attribution claim occurs.
- `pedder` sends a short wake-up to the Galaxias orchestrator thread on
  completion or blockage.
