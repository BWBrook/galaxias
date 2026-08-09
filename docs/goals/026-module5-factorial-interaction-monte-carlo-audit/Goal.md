# Goal 026: Module 5 Factorial Interaction And Monte Carlo Audit

## Objective

Use the existing checksummed Goal 014 production output to answer two linked
questions before any additional simulation is authorized:

1. What departures from additive trout-removal and climbing-removal effects
   are supported within the retained Module 5 families?
2. Are 100 stochastic replicates adequate for the publication-relevant
   family-level conclusions, or would additional replication materially
   improve their stability?

This is a conditional simulation audit. It must not update historical
plausibility, assign posterior probabilities, estimate real-world attributable
fractions, or make manuscript-facing causal claims.

## Scientific Contract

For endpoint `Y`, source row `s`, and replicate prefix `n`, define the three
matched baseline-counterfactual effects:

```text
D_trout(s,n) = mean contrast when trout pressure is removed
D_climbing(s,n) = mean contrast when climbing pressure is removed
D_both(s,n) = mean contrast when both pressures are removed
```

The expectation-scale additive interaction is:

```text
I(s,n) = D_both(s,n) - D_trout(s,n) - D_climbing(s,n)
```

For the three selected endpoints, higher values are favourable. Positive `I`
therefore denotes a more-than-additive benefit of joint pressure removal on
that endpoint scale; negative `I` denotes a less-than-additive or redundant
benefit. This classification is endpoint-specific and is not, by itself,
proof of ecological synergy.

The existing seed contract pairs baseline and counterfactual runs within each
intervention. Because `intervention_id` is part of the seed derivation, equal
replicate IDs across different interventions are not one shared stochastic
four-arm block. Calculate source-level intervention means before calculating
`I`; do not present replicate-wise four-arm contrasts.

## Families And Endpoints

Audit separately:

- `persistent_joint_cause`: primary family;
- `transient_perfect_storm`: sensitivity family.

Do not pool families. The climbing-only family lacks the complete factorial
intervention set and remains outside the interaction analysis.

Use the accepted internal endpoint bundle:

- `persistence_2002_contrast`: lead probability-scale endpoint;
- `min_abundance_1992_2002_contrast`: supporting magnitude endpoint;
- `lake_refuge_share_2002_contrast`: supporting spatial endpoint.

Keep extirpation timing and all semantically excluded detection-summary fields
outside this goal.

## Aggregation And Uncertainty

- Treat the retained proposal-source ensemble as fixed, not as an iid sample
  from a posterior distribution.
- Primary family summaries must weight the 15 Module 4 observation-variant by
  calibration-seed contexts equally, after averaging proposal sources within
  context.
- Also report equal-proposal-source weighting as a sensitivity analysis.
- Quantify Monte Carlo error conditional on the fixed ensemble from
  within-source replicate variation. Intervention streams are independent
  across intervention IDs, so interaction variances add.
- Report context and source heterogeneity descriptively. Do not combine them
  with Monte Carlo error into a confidence or credible interval implying
  population sampling.
- Audit reuse of current 32-bit stochastic seeds across distinct
  source/intervention/replicate keys and record whether any collisions affect
  the same source across intervention arms.

## Replicate-Adequacy Gate

Recompute effects at nested prefixes `25`, `50`, `75`, and `100` and inspect
four disjoint 25-replicate batches.

Use these practical stability tolerances:

- persistence probability: `0.01`;
- lake/refuge share: `0.01`;
- minimum-abundance index: the larger of `10` units and `2%` of the
  family-specific status-quo median minimum abundance.

For every family-endpoint combination, assess all three removal effects and
the interaction. Declare 100 replicates adequate only when:

1. the context-equal estimate and its conditional Monte Carlo bounds change
   by no more than the endpoint tolerance from 75 to 100 replicates;
2. the practical interaction classification is unchanged at 50, 75, and 100;
3. the 100-replicate conditional Monte Carlo 95% half-width is no larger than
   the endpoint tolerance; and
4. the source-level negative/near-zero/positive proportions change by less
   than `0.05` from 75 to 100.

Classify interaction estimates as `more_than_additive` above the positive
tolerance, `less_than_additive` below the negative tolerance, and
`near_additive_or_unresolved` within the tolerance band.

The final decision must distinguish:

- `no_rerun`: all publication-relevant Monte Carlo criteria pass;
- `targeted_extension`: instability is confined to non-headline source tails
  or a limited sensitivity surface;
- `full_factorial_rerun`: a lead or supporting interpretation fails because
  of Monte Carlo error;
- `more_replicates_will_not_help`: instability is driven mainly by context,
  parameterisation, weighting, or model-family heterogeneity.

If more replication is recommended, estimate the smallest useful next level
and choose sequentially among `250`, `500`, and `1000`; do not default to
`1000`.

## Required Outputs

Add a focused analysis module, CLI, and synthetic tests:

```text
src/galaxias_model/module5_interaction_stability.py
scripts/audit_module5_interaction_stability.py
tests/test_module5_interaction_stability.py
```

Create compact tracked audit outputs:

```text
data/module5_interaction_stability/audit_metadata.json
data/module5_interaction_stability/qc_summary.csv
data/module5_interaction_stability/source_effect_summary.csv
data/module5_interaction_stability/context_effect_summary.csv
data/module5_interaction_stability/prefix_stability_summary.csv
data/module5_interaction_stability/replication_decision.csv
docs/module5_interaction_stability_audit.md
```

Keep the 435 MB raw matched-outcome file remote. Pull back only the compact
outputs above.

## Validation

- Synthetic tests must verify the interaction sign and magnitude, independent
  intervention-stream variance calculation, context-equal versus source-equal
  weighting, prefix handling, tolerances, and run/no-run classification.
- Verify the Goal 014 checksum before reading the remote raw output.
- Verify exact source/intervention/replicate coverage for the two factorial
  families.
- Run the focused test, the relevant Module 5 summary/check slice, and
  `make fast-check` once.
- Run `git diff --check` and one focused scientific review.

## Boundaries

- No new simulation, production rerun, pressure-semantic change, intervention
  contract change, or raw-output pull-back.
- No polished figure, manuscript prose, final attribution claim, or
  publication-ready wording.
- No staging, commit, push, PR, rebase, amend, reset, destructive cleanup, or
  remote artifact mutation.
- Remote writes are limited to a new run-specific scratch workspace and a new
  compact Goal 026 artifact directory. Do not alter Goal 014 artifacts.
- Perform one focused review and at most one material repair pass, then stop.

## Completion Condition

Goal 026 is complete when the existing production output yields a checksummed,
compact interaction and convergence audit, the evidence-driven replication
decision is explicit, and no additional simulation or stronger causal wording
has occurred.
