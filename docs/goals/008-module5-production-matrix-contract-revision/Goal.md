# Goal: Module 5 Production Matrix Contract Revision

## Objective

Revise the tracked Module 5 intervention contract so the next production
attribution planning step starts from a coherent 13-row matrix rather than the
asymmetric 10-row dry-run matrix.

This is a docs-and-contract goal. It authorizes a narrow tracked CSV revision,
focused contract checks, and a short post-approval contract note. It does not
authorize production attribution, simulation execution, generated-output
promotion, remote compute, manuscript claims, staging, commit, or push.

## Why This Matters

Goal 006 proved that the current 10-row matrix can be consumed by the local
real-proposal dry-run path. Goal 007 then concluded that this is adequate as a
dry-run/diagnostic matrix but should not be silently promoted unchanged to a
production attribution matrix.

Barry has approved proceeding with the Goal 007 recommendation. The next
useful step is to make the tracked intervention contract explicit:

- retain the complete `persistent_joint_cause` pressure-removal block;
- give `climbing_only` its direct active-mechanism removal row;
- give `transient_perfect_storm` the trout and joint-removal companion rows it
  needs for a balanced sensitivity-family interpretation;
- retain the existing `climbing_only` / `no_trout_pressure` row as a diagnostic
  sidecar rather than the headline climbing-only contrast;
- keep negative-reference families as status-quo diagnostics only.

The result should be a clear contract for the next planning decision, not a
production run.

## Scope

In scope:

- Edit `data/module5_counterfactual_interventions.csv`.
- Create `docs/module5_production_matrix_contract.md`.
- Update this goal `Log.md`.
- Add or update focused contract tests if needed to lock the revised matrix
  shape.
- Remove stale wording in the intervention contract that implies local
  pressure-removal hooks are absent.
- Validate the revised contract with narrow contract/docs checks.

Out of scope:

- No edits to `data/module5_counterfactual_outcome_schema.csv` unless the
  existing contract validator unexpectedly requires a narrow explanatory fix.
- No runner, simulation, inspector, model, proposal-selection, Makefile, or
  generated-output changes.
- No Module 5 dry-run reruns.
- No production-sized attribution, production proposal sampling, family
  weighting, replicate-count choice, compute target, or artifact-retention
  decision.
- No pressure-removal semantic changes and no new scenario hooks.
- No remote compute, remote probes, remote fetches, or Nectar planning.
- No manuscript claims, final causal interpretation, or publication language.
- No staging, commit, push, PR, or publication.

## Required Contract Changes

The revised `data/module5_counterfactual_interventions.csv` must preserve all
current rows and add exactly these new intervention IDs:

- `m5_climbing_only_no_climbing_pressure`
- `m5_transient_perfect_storm_no_trout_pressure`
- `m5_transient_perfect_storm_no_trout_or_climbing_pressure`

After revision, the tracked matrix should have 13 intervention rows with this
family-axis shape:

| family_id | module5_role | required axes |
| --- | --- | --- |
| `persistent_joint_cause` | `primary` | `status_quo`, `no_trout_pressure`, `no_climbing_pressure`, `no_trout_or_climbing_pressure` |
| `climbing_only` | `sensitivity` | `status_quo`, `no_climbing_pressure`, `no_trout_pressure` |
| `transient_perfect_storm` | `sensitivity` | `status_quo`, `no_climbing_pressure`, `no_trout_pressure`, `no_trout_or_climbing_pressure` |
| `habitat_only_null` | `negative_reference` | `status_quo` |
| `trout_only` | `negative_reference` | `status_quo` |

Keep `production_status` as an implementation/execution status field unless
you stop and ask Galaxias first. The default expectation is:

- current `implemented` status-quo rows remain `implemented`;
- pressure-removal rows remain `design_only` until production use is approved;
- diagnostic-sidecar meaning is expressed in `intervention_label`,
  `expected_counterfactual_question`, `notes`, and the new contract note, not
  by adding a new `production_status` enum.

Required wording fixes:

- Existing pressure-removal rows must not say or imply that local intervention
  override hooks are missing.
- Notes may say that local hooks exist and were exercised by Goal 006, while
  production use remains pending contract approval, proportionate validation,
  and later production planning.
- `m5_climbing_only_no_trout_pressure` must be clearly described as a
  diagnostic sidecar/control contrast, not the primary climbing-only production
  contrast.
- Negative-reference rows must remain status-quo diagnostics and must not be
  represented as production attribution ensemble members.

## Required Documentation

Create `docs/module5_production_matrix_contract.md` with:

- current state and non-claims;
- link back to the Goal 007 review recommendation;
- final 13-row matrix summary;
- diagnostic-sidecar treatment;
- negative-reference treatment;
- what remains undecided before production planning;
- validation evidence and stop points.

This note should be concise and operational. It should make the next planning
decision easier without turning into manuscript interpretation.

## Required Validation

Run and log:

- `uv run python scripts/validate_module5_counterfactual_contract.py`
- `uv run pytest tests/test_module5_counterfactual_contract.py -q`
- a focused row-shape check proving:
  - 13 intervention rows;
  - no duplicate `intervention_id`;
  - all three new intervention IDs are present;
  - the family-axis shape matches this goal;
  - negative-reference families have only `status_quo` rows.
- `git diff --check`
- a direct trailing-whitespace scan over the Goal 008 packet, changed docs, and
  changed CSV/test files.
- `git status --short --branch`

Do not run `make module5-dry-run`, `make module5-dry-run-inspect`, production
attribution, remote probes, or generated-output commands for this goal.

If you change validator logic or more than one focused contract test file, run
the narrowest additional tests needed to justify that change and record why.

## Required Deliverables

1. Goal packet:
   - `Goal.md`
   - `Plan.md`
   - `Runbook.md`
   - `Log.md`

2. Revised intervention contract:
   - `data/module5_counterfactual_interventions.csv`

3. Contract note:
   - `docs/module5_production_matrix_contract.md`

4. Focused validation evidence in `Log.md`.

## Done When

- The intervention contract contains the required 13-row matrix and no
  unexpected row deletions, ID renames, or negative-reference intervention
  expansions.
- Stale hook-absence wording is removed from pressure-removal rows.
- Diagnostic-sidecar and negative-reference treatment are explicit.
- The contract note is decision-ready for Galaxias review.
- Required validation commands pass, or any failure is logged with exact
  command output and diagnosis.
- The action repo remains uncommitted and unstaged.
- No generated outputs, simulations, dry runs, remote compute, manuscript
  claims, staging, commit, push, PR, or publication occur.
- `pedder` sends a short wake-up to the Galaxias orchestrator thread on
  completion or blockage.
