# Goal: Module 5 Counterfactual Design And Smoke

## Objective

Create a reviewable Module 5 counterfactual-attribution design contract and a
minimal executable validation scaffold. This goal is complete when the repo can
state, validate, and test the planned Module 5 intervention and outcome schema
without running production counterfactual simulations.

## Why This Matters

Module 4.5 has passed the mechanism-audit gate and selected a conservative
Module 5 ensemble: `persistent_joint_cause` as the primary family,
`climbing_only` and `transient_perfect_storm` as sensitivity families, and
`habitat_only_null` plus `trout_only` as negative references. Before scaling
Module 5, the project needs a written and machine-checkable contract for what
counterfactuals mean, which endpoints will be compared, and what uncertainty
will be carried forward.

This goal deliberately stops before production attribution. It should make the
next production or prototype goal easier to specify and review.

## Operating Mode

Scientific workflow design contract plus tiny local smoke/scaffold.

## Review Surface

The supervisor will review:

- `docs/module5_counterfactual_attribution_plan.md`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`
- any new validator, test, or Makefile target added for the contract
- `data/README.md` updates
- this goal's `Log.md`
- validation command output and final git state

## Scope

In scope:

- Define the Module 5 counterfactual question in plain scientific language.
- Define intervention rows for the primary, sensitivity, and negative-reference
  family roles selected by Module 4.5.
- Define the future Module 5 outcome schema, including endpoints and contrast
  fields, without pretending that production results already exist.
- Add a lightweight validator and focused tests if useful for making the
  contract executable.
- Add or update a small Makefile target only if it makes contract validation
  more reproducible.
- Update `data/README.md` so the new tracked contract files are discoverable.
- Update this goal's `Log.md` as work proceeds.

Out of scope:

- No full Module 5 production runs.
- No remote, HPC, or large parallel jobs.
- No new calibration grids, posterior-like resampling campaigns, or Module 4
  reruns.
- No changes to scientific defaults, priors, target weights, family
  definitions, observation-bridge assumptions, or Module 4.5 outputs.
- No manuscript causal claims beyond saying what this design contract enables.
- No deletion or rewriting of existing Module 1-4.5 artefacts.

## Required Deliverables

1. `docs/module5_counterfactual_attribution_plan.md`
   - Explain the Module 5 purpose, ensemble roles, intervention families,
     endpoints, contrasts, validation ladder, and production-readiness gate.
   - Explicitly carry forward the Module 4.5 caveat that deterministic
     landmark trajectories retained positive latent abundance through 2002.
     Module 5 should therefore focus on matched stochastic counterfactual
     outcomes and detection-linked endpoints, not deterministic extinction
     narratives.
   - State which work remains for the next goal.

2. `data/module5_counterfactual_interventions.csv`
   - Provide a structured intervention contract with at least these columns:
     `intervention_id`, `family_id`, `module5_role`, `scenario_class`,
     `baseline_source`, `intervention_axis`, `intervention_label`,
     `held_constant`, `modified_parameters`,
     `expected_counterfactual_question`, `primary_endpoint`,
     `secondary_endpoints`, `negative_reference_flag`, `production_status`,
     `notes`.
   - Include the Module 4.5 primary family, sensitivity families, and
     negative-reference families.
   - Include at least these intervention axes where they are scientifically
     meaningful and simulator-expressible: `status_quo`, `no_trout_pressure`,
     `no_climbing_pressure`, and `no_trout_or_climbing_pressure`.
   - If an axis is scientifically useful but not yet simulator-expressible,
     record it as `production_status = design_only` and describe the missing
     implementation hook in `notes` rather than inventing unsupported results.

3. `data/module5_counterfactual_outcome_schema.csv`
   - Define the future tracked or generated outcome fields as a schema table,
     not as a fake result table.
   - Include at least: `column_name`, `required`, `dtype`, `unit`,
     `description`, and `source_or_derivation`.
   - Cover family/proposal identifiers, variant/seed identifiers, intervention
     identifiers, stochastic replicate fields, endpoint values, matched
     comparison fields, contrast fields, uncertainty summaries, and provenance.

4. Minimal executable scaffold
   - Add `scripts/validate_module5_counterfactual_contract.py` and a focused
     test such as `tests/test_module5_counterfactual_contract.py`, unless an
     existing validator pattern can be reused more cleanly.
   - The validator should check required columns, uniqueness of
     `intervention_id`, allowed `module5_role` values, required intervention
     axes, required outcome-schema fields, and references to known families in
     `data/module4_5_family_decision_table.csv`.
   - Keep the validator local and cheap. It must not require Module 4 raw
     artefacts or run simulations.

5. Documentation and log updates
   - Update `data/README.md` for the new contract files and validator.
   - Update this goal's `Log.md` after each milestone and at completion.

## Validation Gates

Minimum validation:

- `uv run python scripts/validate_module5_counterfactual_contract.py`
- `uv run pytest tests/test_module5_counterfactual_contract.py -q`
- `make fast-check`
- `git diff --check`
- `git status --short --branch`

If no validator/test is added because an existing validation surface is reused,
record the reason in `Log.md` and run the equivalent command that proves the
contract is checked.

## Decision Authority

Executor may:

- Choose exact row wording, endpoint names, and schema descriptions when they
  preserve the scientific intent above.
- Add a small helper module or Makefile target if it reduces validation
  ambiguity.
- Make narrow fixes discovered by the new focused tests.
- Commit and push the completed goal work to `main` after validation passes,
  using exact staging paths only.

Executor must pause before:

- Starting production Module 5 runs or remote/HPC work.
- Changing simulator semantics, priors, target weights, family definitions, or
  observation-bridge assumptions.
- Adding non-trivial dependencies.
- Making broad refactors outside the Module 5 contract/scaffold surface.
- Making any manuscript-level causal interpretation that goes beyond the
  contract design.

## Done When

- The design document, intervention contract, outcome schema, and minimal
  validation scaffold are present and tracked.
- `data/README.md` and this goal's `Log.md` explain the new artefacts.
- The validation gates above have been run and recorded.
- The final response identifies the commit hash if committed, the push status,
  tracked/untracked git state, residual caveats, and the recommended next goal.
