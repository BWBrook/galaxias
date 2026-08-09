# Module 5 Factorial Interaction And Monte Carlo Stability Audit

## Boundary

This internal audit estimates expectation-scale additive interactions within
the retained Module 5 model families and asks whether the existing 100
stochastic replicates are adequate. It does not update historical
plausibility, estimate posterior model probabilities or real-world
attributable fractions, or establish ecological synergy outside the simulated
intervention semantics.

No new simulation was run. The checksummed Goal 014 matched outcomes remained
on `deep-server`; only compact audit outputs were copied into the repository.

## Design

The analysis uses the three accepted endpoint-bundle contrasts:

- persistence at 2002;
- minimum abundance over 1992-2002;
- lake/refuge share at 2002.

For each proposal source, endpoint, and replicate prefix, the interaction is:

```text
joint-removal effect - trout-removal effect - climbing-removal effect
```

Positive values denote a more-than-additive benefit of joint pressure removal
on that endpoint scale; negative values denote a less-than-additive or
overlapping benefit. Values within the endpoint-specific tolerance are treated
as near-additive or unresolved.

The baseline and counterfactual are seed-matched within each intervention.
Different interventions use different stochastic seed streams, so the audit
combines source-level intervention means rather than constructing invalid
replicate-wise four-arm contrasts.

Primary family estimates give equal weight to each of the 15 observation-
variant by Module 4 calibration-seed contexts. Equal proposal-source weighting
is retained as a sensitivity check. The two weighting schemes did not differ
enough to alter any endpoint-scale classification.

## Provenance And QC

- Source execution SHA:
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`.
- Goal 014 record SHA:
  `a96cfed24800823b77cbafeed5e9603e9dd6d33c`.
- Source matched-outcome SHA-256:
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`.
- Final audit run:
  `20260809T045756Z-goal026-m5-interaction-stability`.
- Remote compact artifact:
  `/data/codex/artifacts/galaxias/module5_interaction_stability_20260809T045756Z-goal026-m5-interaction-stability`.
- Audit duration: 15 seconds.
- Raw rows checked: 279,500.
- Factorial source rows: 265 persistent-joint-cause and 250
  transient-perfect-storm sources, each complete for all three removal axes
  and replicate IDs `0..99`.
- Required endpoints were finite; all within-pair seeds matched; all QC checks
  passed.
- Compact artifact checksums passed.
- Raw matched outcomes were not copied locally.

## Factorial Results

The table reports context-equal estimates at 100 replicates. Monte Carlo
half-width is the conditional 95% half-width for the family estimate.

| Family | Endpoint | Trout removed | Climbing removed | Both removed | Interaction | MC half-width | Classification |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| persistent joint cause | persistence 2002 | 0.0241 | 0.0332 | 0.0328 | -0.0245 | 0.0033 | less than additive |
| persistent joint cause | minimum abundance | 19.1 | 106.6 | 180.6 | 54.9 | 1.31 | more than additive |
| persistent joint cause | lake/refuge share | 0.0826 | 0.1195 | 0.2011 | -0.0010 | 0.0028 | near additive or unresolved |
| transient perfect storm | persistence 2002 | 0.0168 | 0.0311 | 0.0320 | -0.0158 | 0.0031 | less than additive |
| transient perfect storm | minimum abundance | 22.7 | 124.4 | 200.5 | 53.4 | 1.51 | more than additive |
| transient perfect storm | lake/refuge share | 0.0672 | 0.1295 | 0.1999 | 0.0032 | 0.0026 | near additive or unresolved |

The interaction is therefore strongly endpoint-scale dependent:

- All individual and joint removal effects are positive at the family level.
- Persistence benefits are less than additive. Joint removal improves
  persistence, but it does not add the two single-removal probability changes;
  overlap and the bounded binary endpoint are plausible contributors.
- Minimum-abundance benefits are more than additive in both families. This is
  the clearest current evidence of a reinforcing joint effect within the
  simulated histories.
- Lake/refuge-share effects are approximately additive at the chosen
  tolerance.

These patterns are conditional on the retained proposal ensemble and the
implemented zero-pressure interventions. They should not yet be translated
into an unqualified ecological-synergy claim.

## Monte Carlo Adequacy

The family-level evidence is stable at 100 replicates:

- interaction classifications are unchanged at prefixes 50, 75, and 100;
- estimates and conditional Monte Carlo bounds change by less than the
  prespecified endpoint tolerances from 75 to 100;
- all 100-replicate conditional Monte Carlo half-widths are below their
  endpoint tolerances;
- the four disjoint 25-replicate batches preserve the abundance-interaction
  classification in both families and the persistent-family persistence
  classification. The final transient persistence batch falls inside the
  near-additive band, but the nested 50/75/100 estimates remain less than
  additive.

The strict source-distribution criterion does not fully pass. Between 75 and
100 replicates, near-zero versus signed source proportions move by:

- 7.9 percentage points for persistent-family persistence interaction;
- 7.6 percentage points for transient-family persistence interaction;
- 6.8 percentage points for persistent-family lake/refuge-share interaction.

The instability is concentrated in proposal sources close to the practical
zero threshold. It does not alter the family-level effect direction,
interaction classification, or Monte Carlo interval.

## Seed Audit

Across all 279,500 source/intervention/replicate keys, the current 32-bit seed
contract produced 279,489 distinct seeds and 11 collision groups. No collision
reused a seed across different intervention arms for the same proposal source.
The observed collision rate is negligible for the current family summaries,
but a future production design should use a wider seed space.

## Replication Decision

The audit does not support an automatic 1,000-replicate rerun.

- For family-level endpoint and interaction conclusions, 100 replicates are
  adequate under every prespecified estimate, bound, classification, and
  Monte Carlo half-width criterion.
- For publication-facing statements about proportions of proposal sources
  showing positive, near-zero, or negative effects, the strict convergence
  criterion is not yet met.
- The evidence-driven next level is 250 replicates, not 1,000, and only if
  those source-distribution statements are required.

Any new run should use a true four-arm source-replicate seed block across
status quo, trout removed, climbing removed, and both removed. It should start
at 250 replicates and be assessed against the same frozen criteria before any
extension to 500 or 1,000.

## Compact Outputs

- `data/module5_interaction_stability/audit_metadata.json`
- `data/module5_interaction_stability/qc_summary.csv`
- `data/module5_interaction_stability/source_effect_summary.csv`
- `data/module5_interaction_stability/context_effect_summary.csv`
- `data/module5_interaction_stability/prefix_stability_summary.csv`
- `data/module5_interaction_stability/replication_decision.csv`
