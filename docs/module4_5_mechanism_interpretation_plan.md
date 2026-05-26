# Module 4.5 Mechanism Interpretation Plan

Last updated: 2026-05-23

Companion gate plan:
`docs/gated_action_plan_module4_5_and_beyond.md`

## Purpose

Module 4.5 is the interpretive bridge between calibration sensitivity and
counterfactual analysis. Modules 3.75 and 4 have already shown that the
accepted frontier is not a habitat-only or trout-only story. They also showed
that `persistent_joint_cause` is the most stable target-sum winner when late
observation assumptions are made explicit.

The next question is not simply "which family won?" It is:

> What biological mechanism, parameter pattern, and historical trajectory make
> the accepted families work?

This module should explain the accepted frontier in terms a trained biologist
can interrogate: trout pressure, climbing-galaxias pressure, trophic upsurge,
refuge buffering, habitat transition, and observation uncertainty.

## Revised Context From Modules 3.75 And 4

The Module 4.5 plan should start from these results:

- `persistent_joint_cause` won 12 of 15 Module 4 variant/seed runs.
- `persistent_joint_cause` won all baseline runs and all combined soft
  late-observation runs.
- `climbing_only` won 3 of 15 runs, only under single-axis late-observation
  relaxations.
- `transient_perfect_storm` remained strongly represented in accepted proposal
  mixes, but did not win target-sum ranking in the Module 4 grid.
- `habitat_only_null` and `trout_only` had zero accepted proposals across the
  Module 4 sensitivity grid.
- `CT007`, `CT009`, and `CT010` remain the late-history targets that most
  control local rank order.

This means Module 4.5 should focus on the three mechanism-rich families:

- `climbing_only`
- `persistent_joint_cause`
- `transient_perfect_storm`

The two excluded families should be kept as negative references only where
useful.

## Scientific Questions

### 1. What makes `persistent_joint_cause` win?

Check whether persistent joint-cause proposals have a coherent biological
signature:

- sustained trout impact after the early trophy-trout phase;
- sustained climbing-galaxias pressure in lake and refuge habitats;
- plausible Pedder refuge buffering and lake habitat decline;
- no obvious dependence on extreme observation nuisance parameters.

### 2. Why does `climbing_only` sometimes win?

The `climbing_only` wins are informative because they identify the scoring
conditions under which trout is no longer required. Module 4.5 should test
whether those proposals:

- require earlier or stronger climbing-galaxias expansion than the priors
  suggest;
- lean heavily on low detection or high overdispersion;
- still reproduce the early trout/trophic-upsurge chronology targets only
  because those targets are indirect mechanism checks rather than active trout
  effects.

### 3. Is `transient_perfect_storm` biologically distinct?

The transient family should not be discarded merely because it was not the
winner. Module 4.5 should test whether accepted transient proposals have a
clear signature:

- stronger `PR018` upsurge-linked trout piscivory;
- rapid decay of that early trout effect through `PR019`;
- later climbing-galaxias pressure carrying the terminal decline;
- historical trajectories that differ meaningfully from persistent joint-cause
  rather than just fitting the same path through extra flexibility.

### 4. Are nuisance terms carrying too much of the fit?

Audit the observation and scale terms:

- `PR035` occupancy detection probability;
- `PR036` survey count scaling;
- `PR037` count overdispersion;
- `PR038` museum composition noise;
- `PR039` latent count scale.

If accepted proposals cluster near bounds, or if family ranking is strongly
associated with nuisance terms, the next step should be targeted prior or
observation-model refinement before counterfactual production runs.

### 5. Which uncertainty should be carried into Module 5?

Module 4.5 should end with a decision about the ensemble to use for
counterfactual analysis:

- persistent joint-cause only;
- all three mechanism-rich accepted families;
- persistent plus transient joint-cause families;
- or a weighted/sensitivity ensemble that preserves family uncertainty.

## Inputs

Primary inputs:

- `data/module4_raw_artifact_manifest.csv`
- `outputs/remote/module4_observation_sensitivity_20260522T101942Z/*`
- `data/module4_family_summary.csv`
- `data/module4_accepted_mix.csv`
- `data/module4_family_winners.csv`
- `data/module4_target_leverage.csv`
- `data/parameter_priors.csv`
- `data/model_family_parameter_map.csv`
- `data/calibration_targets.csv`
- `data/calibration_target_details.json`

Secondary context:

- `docs/module3_75_observation_bridge_review.md`
- `docs/module4_observation_sensitivity_review.md`
- `docs/model_spec_tier1.md`
- `docs/notes_for_chris.md`

## Proposal Sets To Compare

Use five pre-defined proposal sets:

1. `accepted`: proposals with `accepted_final = True`.
2. `near_frontier_absolute`: valid Stage B proposals with
   `target_sum <= best_target_sum + 10` within each variant/seed.
3. `near_frontier_relative`: valid Stage B proposals with
   `target_sum <= 1.05 * best_target_sum` within each variant/seed.
4. `family_winners`: the best proposal per family, variant, and seed.
5. `global_winners`: the winning proposal for each variant/seed.

The accepted set is the main biological ensemble. The near-frontier and
winner-only sets are diagnostic: they help distinguish robust patterns from
rank-order noise.

Target-sum distance is defined as the sum, across targets, of replicate-median
weighted target penalties for valid Stage B proposals. Module 4.5 must report
where target-sum rank agrees or disagrees with
`stochastic_overall_distance_median`, because Module 4 family winners were
chosen by target-sum rank rather than the aggregate stochastic distance alone.

## Analyses

### A. Parameter Posterior-Like Summaries

For each family and observation-bridge variant, summarize accepted and
near-frontier parameter distributions:

- median, interquartile range, and 5th-95th percentile;
- distance from prior median or default where useful;
- proportion near lower or upper prior bounds;
- rank correlations with target-sum and stochastic distance.

Priority parameters:

- trout abundance and piscivory: `PR012`-`PR021`;
- climbing expansion and impact: `PR022`-`PR028`;
- trophic upsurge: `PR029`-`PR031`;
- habitat and refuge modifiers: `PR032`-`PR034`, `PR040`;
- observation and scale terms: `PR035`-`PR039`;
- Pedder demography and capacity checks: `PR001`-`PR011`.

### B. Family Contrast Tables

Build compact contrast tables that answer:

- which parameters separate persistent from transient joint-cause?
- which parameters separate climbing-only from joint-cause?
- which parameters separate accepted proposals from Stage B rejected proposals?
- which contrasts are stable under `baseline_current` and `late_bridge_soft`?

Use effect sizes and rank summaries rather than relying only on raw medians.

### C. Late-Target And Nuisance Audit

For `CT007`, `CT009`, and `CT010`, summarize target penalties by family,
variant, and proposal set. Link these penalties to `PR035`-`PR039`.

Specific checks:

- Does low `PR036` or high `PR037` explain good late-count scores?
- Does `PR035` affect the apparent plausibility of post-1996 persistence?
- Does `PR039` differ by family enough to change biological interpretation?
- Are `climbing_only` wins mainly observation-model wins?

### D. Historical Trajectory Reconstruction

Regenerate deterministic historical trajectories for selected proposal sets:

- all `global_winners`;
- all `family_winners`;
- accepted proposals if runtime is trivial, otherwise a stratified sample per
  family and variant.

Summarize landmark years rather than creating an unreadable wall of paths:

- 1972 system connection and trout stocking;
- 1977 trophic-upsurge and trout peak;
- early-to-mid 1980s transition;
- 1990-1991 severe contraction;
- 1996 final natural-range record;
- 2002 no-detection endpoint.

Trajectory summaries should include:

- Pedder total, lake, and refuge latent abundance;
- trout abundance and piscivory pressure;
- climbing lake and refuge pressure;
- trophic upsurge state;
- combined threat pressure if the simulator exposes or can derive it.

### E. Mechanism Narrative Synthesis

Translate the quantitative contrasts into plain-language mechanism statements:

- what must be true for a persistent joint-cause explanation to work;
- what must be true for a climbing-only explanation to work;
- what must be true for a transient perfect-storm explanation to work;
- which assumptions are well-supported by evidence and which are placeholders.

This synthesis should explicitly separate:

- biological process uncertainty;
- observation and detection uncertainty;
- calibration/sample-size uncertainty;
- future counterfactual uncertainty.

## Expected Outputs

Tracked summary artifacts:

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

Optional artifacts if useful:

- compact figures under `outputs/module4_5/figures/`;
- a small selected-proposal table for Module 5 counterfactual inputs.

The raw regenerated trajectories should stay under ignored `outputs/` unless a
small landmark table is needed for reproducibility.

## Compute Plan

### MacBook

Use the MacBook for:

- reading and editing the plan;
- developing the summarizer on one variant/seed;
- running `make check`;
- inspecting small CSV outputs.

Avoid loading all raw remote artifacts repeatedly on the MacBook if memory use
is clumsy.

### Mac Mini

Use the Mac Mini if the work is mostly pandas/report generation and the
MacBook feels memory-bound. This is a good fallback for medium local analysis,
but it is not necessary if `deep-server` is more convenient.

### Deep-server

Use `deep-server` for the full Module 4.5 extraction if trajectory
regeneration or all-artifact pandas joins become slow locally. The Module 4 raw
artifact already exists there:

`/data/codex/artifacts/galaxias/module4_observation_sensitivity_20260522T101942Z`

Expected run style:

- mirror latest repo to `/data/codex/repos/galaxias`;
- verify `uv sync --locked` and `make check`;
- run the full Module 4.5 summarizer against the existing artifact using an
  explicit `--module4-root` and `--manifest`;
- copy compact `data/` and `docs/` products back to the MacBook.

Use `tmux` if trajectory regeneration is run across hundreds of proposals, or
if the job may outlive the interactive Codex session.

### Kunanyi

Do not use `kunanyi` for Module 4.5 unless this unexpectedly turns into a very
large resimulation exercise. This module is analysis and summarization, not a
multi-node production grid.

## Success Criteria

Module 4.5 is successful if it can answer:

- whether the `persistent_joint_cause` signal is mechanistically coherent;
- whether `climbing_only` wins are biologically plausible alternatives or
  mainly late-observation artefacts;
- whether `transient_perfect_storm` deserves to remain in the Module 5
  counterfactual ensemble;
- which nuisance terms are safe enough to carry forward;
- which family or families should seed counterfactual coexistence analysis.

## Decision Rules After Module 4.5

Proceed to Module 5 counterfactual analysis if:

- accepted mechanism-rich families have interpretable, non-pathological
  parameter profiles;
- nuisance terms are not the main explanation for family ranking;
- the persistent-vs-transient distinction remains biologically meaningful.

Run a targeted Module 4.75 refinement if:

- accepted fits depend on extreme nuisance values;
- `climbing_only` looks competitive only because of one late-observation
  assumption;
- persistent and transient joint-cause are indistinguishable under current
  summaries;
- a small number of prior bounds or target definitions need revision before
  counterfactuals.

Escalate to a larger calibration grid only if:

- Module 4.5 shows that sample size, not biology or scoring, is the main source
  of ambiguity;
- the required grid is large enough to justify more `deep-server` runs or,
  eventually, a PBS sweep on `kunanyi`.
