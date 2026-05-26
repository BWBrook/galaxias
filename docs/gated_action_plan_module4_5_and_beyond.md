# Gated Action Plan From Module 4.5 Audit

Last updated: 2026-05-23

Source feedback:
`docs/galaxias_repo_audit_module45_feedback.md`

## Purpose

This document turns the Module 4.5 audit into a modular action plan with
explicit pass gates. The aim is to keep progress disciplined: each module must
leave behind clear artefacts, validation evidence, and a written decision about
whether the project is ready to proceed.

The immediate risk identified by the audit is that Module 4 produced a strong
calibration pattern, but Module 5 counterfactual attribution would be premature
unless Module 4.5 shows that the surviving families are biologically coherent
and not mostly carried by late-observation nuisance terms.

## Operating Rule From Here

At the end of every module or gated submodule, the report-back should include:

1. what changed or was produced;
2. where the tracked outputs are;
3. what validation passed;
4. what scientific interpretation is now licensed;
5. what uncertainty or caveat remains;
6. the recommended next task for Barry's go-ahead or modification.

## Status Legend

- `pending`: not started.
- `active`: current work item.
- `blocked`: cannot proceed without a missing artefact, decision, or access.
- `passed`: gate has been satisfied and recorded.
- `conditional`: only needed if an earlier gate triggers it.

## Current Baseline

Completed baseline:

- Modules 1 through 4 are documented and reproducible from tracked summaries.
- Module 4 has a committed mechanism-sensitivity result:
  `persistent_joint_cause` won 12 of 15 variant/seed runs, including all
  baseline and combined soft late-observation runs.
- `habitat_only_null` and `trout_only` had zero accepted proposals across the
  Module 4 grid.
- The Module 4 raw artefact exists locally under ignored `outputs/remote/` and
  remotely on `deep-server`.

Current planning state:

- Module 4.5 should remain a mechanism audit, not a posterior-summary gloss.
- Module 5 should not start until the Module 4.5 diagnostic gates have passed.
- `deep-server` remains the first serious compute target.
- `kunanyi` remains reserved for large PBS-scale sweeps, not ordinary
  Module 4.5 summarisation.

## Gate 0: Feedback Intake And Plan Freeze

Status: `passed`

Goal:

Convert the audit into an agreed project roadmap before implementing Module
4.5.

Required actions:

- Read and retain the audit feedback as the planning basis.
- Create this gated action plan.
- Cross-reference this plan from the existing Module 4.5 plan.
- Review whether the audit file itself should be tracked in git or kept as
  local review input.

Pass gate:

- Barry confirms or modifies the gated plan.
- The plan identifies every must-pass gate before Module 5.
- The repo has a clean checkpoint once Barry approves the plan.

This gate is now satisfied.

## Gate 1: Reproducibility And Repo-Health Foundation

Status: `passed`

Purpose:

Make sure Module 4.5 is not built on hidden remote state, slow or fragile test
behaviour, or missing onboarding documentation.

### Gate 1A: Raw Module 4 Artefact Provenance

Status: `passed`

Required actions:

- Create a compact Module 4 raw publish manifest.
- Include every variant/seed run directory used by Module 4.5.
- Record paths, file sizes, hashes, source command, run date, commit, Python
  version, seed, variant, and remote/local location.
- Ensure each run has:
  - `proposal_summary.csv.gz`;
  - `parameter_values.csv.gz`;
  - `target_scores.csv.gz`;
  - `accepted_proposals.csv`;
  - `family_summary.csv`;
  - `run_manifest.json`.
- Decide whether compact raw artefacts are tracked, mirrored under ignored
  `outputs/`, or kept externally with a tracked manifest.

Suggested tracked output:

- `data/module4_raw_artifact_manifest.csv`

Pass gate:

- A fresh checkout can identify exactly which raw files Module 4.5 needs.
- The Module 4.5 command can run from an explicit `--module4-root` or manifest,
  without relying on a remembered `deep-server` path.
- Hashes and run manifests match the Module 4 summary tables already tracked.

### Gate 1B: Predictable Test Tiers

Status: `passed`

Required actions:

- Add pytest markers for slow/integration tests.
- Mark the parallel worker reproducibility test and larger calibration
  exercises as slow if they are not fast enough for routine local checks.
- Add Make targets such as:
  - `make fast-check`;
  - `make check`;
  - `make integration-check`;
  - `make module4-smoke`;
  - `make module4-5-smoke`.
- Decide whether `make check` should remain full-suite or become a fast
  developer gate plus explicit integration gate.

Pass gate:

- The fast gate finishes reliably on the MacBook.
- The full or integration gate is still available and documented.
- Parallel-vs-serial reproducibility remains tested somewhere deliberate.

### Gate 1C: Onboarding And Offline Reproducibility

Status: `passed`

Required actions:

- Add a root `README.md` with:
  - biological question;
  - current status;
  - module map;
  - quick start;
  - source versus generated files;
  - current headline result and non-claims;
  - raw artefact locations;
  - compute-resource policy.
- Add offline/cluster-safe `uv` notes, including use of a pre-installed Python
  and `UV_PYTHON_DOWNLOADS=never` when downloads are undesirable.
- Improve `scripts/check_portability.py` by either:
  - clearly requiring a Git checkout; or
  - falling back to a tree walk for zip/export audits.
- Extend `.gitignore` for routine transient files:
  `.mypy_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `*.log`, and
  `.ipynb_checkpoints/`.

Pass gate:

- A new collaborator can orient from `README.md` without reading every module
  document.
- The portability check fails clearly outside Git or works outside Git.
- Offline or cluster Python setup expectations are explicit.

## Gate 2: Module 4.5 Design Lock

Status: `passed`

Purpose:

Pre-register the diagnostic definitions before generating Module 4.5 results.

Required actions:

- Revise `docs/module4_5_mechanism_interpretation_plan.md` to incorporate the
  audit sharpenings.
- Define proposal sets operationally:
  - `accepted`: `accepted_final = True`;
  - `near_frontier_absolute`: valid Stage B proposals with
    `target_sum <= best_target_sum + 10` within each variant/seed;
  - `near_frontier_relative`: valid Stage B proposals with
    `target_sum <= 1.05 * best_target_sum` within each variant/seed;
  - `family_winners`: best proposal per family/variant/seed;
  - `global_winners`: best proposal per variant/seed.
- Define target-sum distance explicitly from replicate-median weighted target
  penalties.
- Define how target-sum ranking will be compared with
  `stochastic_overall_distance_median`.
- Write minimum biological requirements for each surviving family before
  interpreting output.
- Define derived pressure metrics and time windows.
- Define Module 5 ensemble decision rules.

Minimum biological requirements:

- `climbing_only` must show early enough climbing activation and pressure to
  explain the 1980-1983 shift, without relying on nuisance extremes.
- `persistent_joint_cause` must show non-negligible trout pressure beyond the
  early trophy-trout phase plus sustained climbing pressure.
- `transient_perfect_storm` must show a materially elevated early trout
  overshoot, later decay, and later climbing/refuge pressure.

Derived pressure windows:

- 1972-1977: post-flood boom and trout upsurge.
- 1978-1983: community shift toward climbing galaxias.
- 1984-1991: refuge contraction.
- 1992-1996: terminal natural-range record.
- 1998-2002: non-detection endpoint.

Pass gate:

- The Module 4.5 plan contains fixed definitions for proposal sets, target
  distance, derived pressure metrics, nuisance diagnostics, biological minimum
  requirements, and Module 5 decision rules.
- The plan says which outputs are mandatory.
- The gate is reviewed before running full Module 4.5 interpretation.

## Gate 3: Module 4.5 Implementation

Status: `passed`

Purpose:

Build Module 4.5 as a separate, auditable analysis layer.

Required actions:

- Create a dedicated implementation module rather than adding to
  `src/galaxias_model/review.py`, for example:
  - `src/galaxias_model/mechanism_interpretation.py`; or
  - `src/galaxias_model/review/module4_5.py`.
- Create:
  - `scripts/run_module4_5_mechanism_interpretation.py`;
  - tests for proposal-set assignment, target-sum calculation, nuisance
    scaling, and derived pressure calculations.
- The script should accept explicit paths and parameters:

```bash
uv run python scripts/run_module4_5_mechanism_interpretation.py \
  --module4-root outputs/remote/module4_observation_sensitivity_20260522T101942Z \
  --manifest data/module4_raw_artifact_manifest.csv \
  --publish-root . \
  --near-frontier-delta 10 \
  --near-frontier-relative 1.05 \
  --trajectory-sample 100 \
  --seed 20260523
```

- Add a smoke target:
  - `make module4-5-smoke`

Mandatory outputs:

- `data/module4_5_proposal_set_membership.csv`
- `data/module4_5_distance_audit.csv`
- `data/module4_5_parameter_summary.csv`
- `data/module4_5_parameter_contrasts.csv`
- `data/module4_5_nuisance_audit.csv`
- `data/module4_5_target_family_summary.csv`
- `data/module4_5_pressure_landmarks.csv`
- `data/module4_5_trajectory_landmarks.csv`
- `data/module4_5_family_decision_table.csv`
- `docs/module4_5_mechanism_interpretation_review.md`

Current implementation:

- Module 4.5 code has a dedicated home in
  `src/galaxias_model/mechanism_interpretation.py`.
- The smoke CLI is `scripts/run_module4_5_mechanism_interpretation.py`.
- `make module4-5-smoke` validates explicit raw-artifact inputs and the
  mandatory output contract.
- The full CLI generates all mandatory Module 4.5 tables and the Markdown
  interpretation review from the raw Module 4 artifact manifest.

Pass gate:

- Local one-variant/one-seed smoke passes.
- Tests for the new analysis layer pass.
- `make fast-check` or `make check` passes as defined by Gate 1.
- The full script can re-render outputs from existing raw Module 4 artefacts.

## Gate 4: Module 4.5 Diagnostic Execution

Status: `passed`

Purpose:

Run the full Module 4.5 diagnostic and decide whether the project is ready for
counterfactual attribution.

Compute plan:

- Develop and smoke locally on the MacBook.
- Use `deep-server` if full raw-artifact joins or trajectory regeneration are
  slow locally.
- Use `tmux` on `deep-server` for any run that may outlive the interactive
  session.
- Do not use `kunanyi` unless this unexpectedly becomes a large resimulation
  exercise.

Required analyses:

- Proposal-set membership audit.
- Distance audit comparing target-sum ranking with Stage B distance columns.
- Parameter summaries and family contrasts.
- Nuisance boundary and rank-correlation audit for `PR035`-`PR039`.
- Target-block posterior-predictive style summaries, including pass fractions.
- Derived pressure summaries for trout, climbing, lake, and refuge windows.
- Landmark trajectory summaries for 1972, 1977, 1980, 1983, 1988-1991, 1996,
  and 2002.
- Persistent-versus-transient degeneracy check in trajectory or pressure space.
- Family decision table against the pre-written biological requirements.

Pass gate:

- `docs/module4_5_mechanism_interpretation_review.md` states:
  - whether `persistent_joint_cause` is mechanistically coherent;
  - whether `climbing_only` is a serious alternative or mainly an
    observation-model artefact;
  - whether `transient_perfect_storm` is biologically distinct or should be
    folded into a broader joint-cause ensemble;
  - whether nuisance terms are acceptable or need refinement;
  - which ensemble is carried into Module 5.
- `docs/notes_for_chris.md` is updated in plain language.
- Validation passes locally and, if run remotely, on `deep-server`.

Current result:

- `persistent_joint_cause` is carried into Module 5 as the primary ensemble.
- `climbing_only` remains a sensitivity case because it is accepted and
  locally competitive under single-axis late-observation variants, but it does
  not win the baseline or combined soft late-observation variants.
- `transient_perfect_storm` remains a joint-cause sensitivity case because it
  is accepted and has a transient overshoot signature, but it did not win the
  Module 4 target-sum grid.
- `habitat_only_null` and `trout_only` remain negative references.
- Current nuisance-bound diagnostics are low risk for the accepted
  mechanism-rich families, so Gate 4.75 is not triggered by the present audit.

Module 5 is unblocked.

## Gate 4.75: Conditional Refinement Before Counterfactuals

Status: `conditional`

Trigger this gate if Module 4.5 shows that interpretation is still unstable.

Triggers:

- Accepted fits depend on boundary-hugging nuisance terms.
- `climbing_only` is competitive only under one late-observation assumption.
- Persistent and transient joint-cause are not distinguishable, but the plan
  still wants to treat them separately.
- CT009 or CT010 needs a structural observation-model revision.
- A small number of prior bounds or target definitions clearly need adjustment.

Possible actions:

- Recast CT009 as a last-detection event rather than a hard latent-presence
  endpoint.
- Add or approximate year-specific effort in CT010.
- Tighten or re-express nuisance priors if they are acting as escape valves.
- Run a targeted Module 4 sensitivity update on `deep-server`.

Pass gate:

- The refinement is documented as Module 4.75.
- Any changed target/prior/scoring decision has a written rationale.
- Module 4.5 outputs are regenerated if the input interpretation changes.
- The Module 5 ensemble decision is no longer ambiguous.

## Gate 5: Matched Counterfactual Attribution

Status: `pending`

Purpose:

Estimate historical causal contrasts using the Module 4.5-approved ensemble.

Required design actions:

- Predefine the retained proposal ensemble.
- Predefine common-random-number replication.
- Separate state removal from effect removal.
- Define outcomes:
  - persistence past 2002;
  - expected extirpation year;
  - persistence past 1996;
  - minimum abundance over 1992-2002;
  - lake versus refuge persistence;
  - expected detections under the observation bridge.

Candidate interventions:

- historical baseline;
- no trout stocking;
- trout effects removed;
- no climbing-galaxias effect;
- no trout or climbing effects;
- no transient trout overshoot;
- no habitat-transition penalty;
- strong refuge buffering within plausible limits.

Pass gate:

- Counterfactual scenarios are coded and smoke-tested.
- Baseline historical reruns reproduce the Module 4.5-approved ensemble
  behaviour.
- Common-random-number contrasts are implemented.
- Outputs separate family-specific results from overall ensemble summaries.
- The report states the attribution conclusion and what it does not prove.

## Gate 5.5: Present-Day Coexistence Envelope

Status: `pending`

Purpose:

Convert the retrospective model into a management-relevant envelope: under
what standardised trout, climbing, and refuge conditions could Pedder galaxias
persist now?

Required design actions:

- Turn off transient post-flood upsurge terms.
- Define pressure axes in standardised units.
- Define 25-year and/or 50-year persistence outcomes.
- Explore refuge buffering and habitat-quality assumptions.

Pass gate:

- Coexistence surfaces are produced with uncertainty bands or sensitivity
  bands.
- Outputs are framed in standardised pressure or CPUE-equivalent terms, not
  overconfident literal fish-per-hectare thresholds.
- Conservation interpretation is clearly separated from historical
  attribution.

## Gate 6: Robustness And Prior/Target Sensitivity

Status: `pending`

Purpose:

Test whether the headline causal conclusion survives reasonable alternatives.

Required actions:

- Perturb weak interaction priors.
- Jitter or block-omit target weights.
- Revisit CT007, CT009, and CT010 observation bridge alternatives.
- Test proposal-set definitions.
- Expand the calibration grid only if Module 4.5/5 ambiguity is sample-size
  driven.
- Consider SMC-ABC or history-matching refinement only if the simpler grid is
  clearly insufficient.

Compute plan:

- Use `deep-server` for moderate additional grids.
- Escalate to `kunanyi` only for many independent calibration jobs or large
  embarrassingly parallel sweeps.

Pass gate:

- The robustness report states which conclusions are stable, which are
  sensitive, and which should be worded cautiously.
- Any larger compute result has a manifest, hashes, and raw artefact location.

## Gate 7: Manuscript And Communication Package

Status: `pending`

Purpose:

Turn the modelling workflow into a collaborator- and manuscript-ready package.

Required outputs:

- Historical timeline figure.
- Model schematic.
- Calibration-family ranking figure across Modules 3.5, 3.75, and 4.
- Module 4.5 mechanism figure showing derived pressure trajectories.
- Module 5 counterfactual attribution figure.
- Optional present-day coexistence-envelope figure.
- Plain-language Chris summary.
- Manuscript outline or draft sections.

Pass gate:

- The manuscript language matches the evidentiary strength.
- The strongest claim remains model-family causal attribution under sparse
  evidence, not proof of a single true cause.
- Chris has a concise review package that separates results, assumptions,
  uncertainties, and questions.

## Gate 8: Genetics And Identity Sidecar

Status: `pending`

Purpose:

Keep genetics, introgression, insurance-population history, and taxonomic
interpretation visible without forcing them into the Tier 1 demographic
mechanism.

Required actions:

- Summarise the recent genetics evidence.
- Identify which points affect conservation implications rather than
  historical demographic causation.
- Decide whether this belongs in the manuscript body, supplement, or a
  separate companion note.

Pass gate:

- Genetics is integrated as interpretation and management context.
- It does not distort the 1972-2002 demographic mechanism unless new evidence
  justifies coupling it directly.

## Parking Lot: Companion Clarence Lagoon Work

Status: `pending`

Clarence Lagoon is a plausible companion project, but it should not be folded
into the Pedder module sequence until the historical Pedder causal-attribution
story is stable. It is likely a separate forward-management optimisation
problem using some shared modelling ideas.

## Immediate Recommended Sequence

1. Start Module 5 matched counterfactual attribution using
   `persistent_joint_cause` as the primary ensemble.
2. Carry `climbing_only` and `transient_perfect_storm` as sensitivity
   ensembles rather than collapsing them away.
3. Keep `habitat_only_null` and `trout_only` as negative references.
4. Revisit Gate 4.75 only if counterfactual setup or Chris review exposes a
   nuisance-bound or late-observation dependence not visible in Module 4.5.
