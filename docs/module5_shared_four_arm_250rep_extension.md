# Module 5 Shared Four-Arm 250-Replicate Extension

## Review Status

This is an internal scientific review record. It reports conditional simulation
effects and Monte Carlo stability for a fixed ensemble of plausible proposal
sources. It is not posterior inference, a real-world attributable fraction,
proof of ecological synergy, or manuscript-ready wording.

## Why This Run Was Needed

Goal 026 found stable family-level interaction estimates at 100 replicates but
some movement in source-level interaction classes. Its underlying Goal 014
execution paired each intervention with its own status-quo run, while using a
different random stream for each intervention. Goal 027 instead ran one
status-quo arm and all three pressure-removal arms from one starting seed for
each proposal-source and replicate block.

Equal starting seeds provide a reproducible common-seed coupling. They do not
guarantee identical event-level random shocks after trajectories diverge,
because state-dependent draws can consume a pseudorandom stream differently.

## Frozen Execution

- Execution source SHA:
  `4e2e786381595a4dcb9ca11f04b40df1d5606f2a`.
- Remote host: `deep-server` via `deep-server-ts`.
- Source set: 265 accepted `persistent_joint_cause` proposal sources and 250
  accepted `transient_perfect_storm` sources across 15 Module 4 contexts.
- Replicates: 250.
- Workers: 32.
- Source-replicate blocks: 128,750.
- Actual arm simulations: 515,000.
- Stored non-status-quo contrasts: 386,250.
- Runtime: 467 seconds.
- Raw matched output: 631,217,121 bytes, retained remotely only.
- Raw SHA-256:
  `3ea4ad0a05ad928628fc3cd780cb94a3f4517d07a1827b16a527ea9000ce20c5`.

The all-source five-replicate smoke ran first. It produced 7,725 contrast rows
in 18 seconds and passed all 21 structural checks before the 250-replicate run
was started.

## Quality Control

The production extension passed all 21 checks:

- exact 386,250-row schema and source/intervention/replicate coverage;
- exact three removal contrasts in every source-replicate block;
- one starting seed across all stored arms in each block;
- identical stored status-quo endpoint values across the three contrasts;
- 128,750 distinct seeds for 128,750 blocks, with zero collisions;
- exact proposal-source identity and matched-pair IDs;
- finite endpoint values and matching run ID, raw hash, and frozen source SHA;
- `production_attribution=false`.

The remote artifact contains 23 checksummed entries and passed a fresh
`sha256sum -c` verification. The compact audit was pulled back; the raw matched
output was not.

## Family-Level Results

Primary estimates weight the 15 Module 4 variant-by-calibration-seed contexts
equally. The equal-proposal-source sensitivity has the same practical
classification for every effect.

| Family | Endpoint | Trout removed | Climbing removed | Both removed | Interaction | Interaction class | Interaction MC 95% half-width |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| Persistent joint cause | Persistence in 2002 | 0.0236 | 0.0324 | 0.0329 | -0.0231 | less than additive | 0.00127 |
| Transient perfect storm | Persistence in 2002 | 0.0171 | 0.0313 | 0.0328 | -0.0155 | less than additive | 0.00133 |
| Persistent joint cause | Minimum abundance, 1992-2002 | 19.4 | 107.0 | 180.1 | 53.7 | more than additive | 0.759 |
| Transient perfect storm | Minimum abundance, 1992-2002 | 22.7 | 124.8 | 201.2 | 53.6 | more than additive | 0.865 |
| Persistent joint cause | Lake/refuge share in 2002 | 0.0804 | 0.1201 | 0.2009 | 0.0004 | near additive or unresolved | 0.00124 |
| Transient perfect storm | Lake/refuge share in 2002 | 0.0653 | 0.1287 | 0.1992 | 0.0052 | near additive or unresolved | 0.00121 |

All three pressure-removal effects are favourable at family level on all three
endpoint scales. The interaction pattern is also consistent between the
primary and sensitivity families:

- persistence probability is less than additive, consistent with overlapping
  effects or saturation on a bounded endpoint rather than evidence of harm;
- minimum abundance is more than additive on the abundance-index scale;
- lake/refuge share is near additive or unresolved within the practical
  tolerance.

These are scale-specific conditional interactions. They do not, alone,
establish mechanistic ecological synergy or antagonism.

## Stability Decision

All six family-endpoint combinations pass the family-level 250-replicate gate:

- estimates and Monte Carlo bounds change less than their practical tolerance
  from 175 to 250 replicates;
- interaction classes agree at 100, 175, and 250;
- 250-replicate Monte Carlo half-widths are below tolerance;
- context-equal and source-equal classifications agree.

Five of six also pass the source-class-proportion gate. The sole exception is
the transient-family lake/refuge interaction:

| Replicates | Negative sources | Near-zero sources | Positive sources | Family interaction estimate |
| ---: | ---: | ---: | ---: | ---: |
| 100 | 0.232 | 0.408 | 0.360 | 0.00577 |
| 175 | 0.196 | 0.476 | 0.328 | 0.00552 |
| 250 | 0.176 | 0.540 | 0.284 | 0.00524 |

The 175-to-250 maximum class-proportion shift is 0.064, just above the
prespecified 0.05 gate. This is best understood as threshold sensitivity, not
family-level Monte Carlo failure: 83 of 250 source means lie within 0.005 of
the practical +/-0.01 class boundary, including 27 within 0.002. The continuous
family estimate, interval, and near-additive classification remain stable.

The Goal 027 100-prefix estimates generated no Goal 026 continuity flags.
Common seeding reduced the interaction Monte Carlo half-width at 100
replicates by about 9% to 38%, depending on family and endpoint, without
changing any family-level conclusion.

## Decision

The 250-replicate extension is sufficient for the current family-level
interaction conclusions. Do not run 500 or 1,000 replicates.

For later internal artefacts and scientific discussion:

- retain the three-endpoint bundle rather than elevating one scale as the sole
  result;
- treat persistent joint cause as primary and transient perfect storm as
  sensitivity evidence;
- describe the transient lake/refuge source distribution continuously if it
  matters, rather than claiming a stable prevalence of negative, near-zero,
  and positive source classes;
- keep the common-seed versus exact common-shock distinction explicit;
- bring these results into the planned skeptical collaborator review before
  any display artefact or manuscript wording is authorized.

No further Module 5 simulation is recommended at this point.
