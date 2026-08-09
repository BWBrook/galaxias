# Goal 027: Shared Four-Arm Module 5 Extension

## Objective

Replace the intervention-specific random streams used for the Goal 014
interaction audit with a four-arm common-seed block, then use a
bounded 250-replicate extension to decide whether the source-level interaction
classifications that were still moving at 100 replicates have stabilised.

This goal is a conditional simulation and Monte Carlo stability analysis. It
does not update historical plausibility, assign posterior probabilities,
estimate real-world attributable fractions, or authorize manuscript-facing
causal claims.

## Scientific Design

Run all accepted proposal-source rows from the two complete-factorial families:

- `persistent_joint_cause`: 265 proposal sources, primary family;
- `transient_perfect_storm`: 250 proposal sources, sensitivity family.

For every proposal source and stochastic replicate, run exactly four arms from
one shared stochastic seed:

1. status quo;
2. no trout pressure;
3. no climbing pressure;
4. neither trout nor climbing pressure.

The status-quo simulation is run once and reused when constructing the three
stored removal contrasts. With 515 sources and 250 replicates, the execution
therefore comprises 515,000 simulations and 386,250 stored contrast rows.
Do not include `climbing_only`, diagnostic-sidecar, or negative-reference
families in this extension.

## Seed And Identity Contract

For proposal-source key `s` and replicate `r`, derive one deterministic
non-negative 63-bit seed from:

```text
int.from_bytes(sha256(base_label|s|r)[:8]) & ((1 << 63) - 1)
```

The intervention identifier must not enter the seed. Use that same integer for
all four arms in the source-replicate block. The signed-64-bit-compatible range
keeps CSV and pandas handling portable while providing a vastly larger space
than the Goal 014 32-bit seeds; require zero observed collisions.

Equal starting seeds provide a reproducible common-seed coupling. Because
state-dependent random draws can consume a pseudorandom stream differently
after trajectories diverge, do not describe the arms as receiving identical
event-level ecological shocks.

Preserve the existing proposal-source identity and matched-pair identifiers in
the stored contrast rows. Verify:

- all three stored intervention rows in a source-replicate block carry the
  same baseline and intervention seed;
- baseline endpoint values are identical across those three rows because they
  came from the same simulated status-quo object;
- every source-replicate seed is unique across the run;
- the output covers every expected source, intervention, and replicate once.

## Interaction And Aggregation

For endpoint `Y` and a source-replicate block, let the three stored contrasts
be `D_trout`, `D_climbing`, and `D_both`. Define:

```text
I = D_both - D_trout - D_climbing
```

Compute `I` at replicate level before taking source means. Estimate the Monte
Carlo variance of each source mean from its replicate-level values, retaining
the observed covariance across the common-seed arms. Do not add independent
intervention variances as in Goal 026.

Keep families separate. Use the accepted endpoint bundle:

- `persistence_2002_contrast`: lead endpoint;
- `min_abundance_1992_2002_contrast`: supporting magnitude endpoint;
- `lake_refuge_share_2002_contrast`: supporting spatial endpoint.

Primary summaries weight the 15 `variant_id` by Module 4 calibration-seed
contexts equally after averaging proposal sources within context. Equal
proposal-source weighting is a sensitivity analysis. Treat the proposal-source
ensemble as fixed, not as an iid posterior sample.

## Prespecified 250-Replicate Gate

Apply the Goal 026 practical tolerances:

- persistence probability: `0.01`;
- lake/refuge share: `0.01`;
- minimum abundance: the larger of `10` units and `2%` of the family-specific
  status-quo median minimum abundance.

Summarise nested prefixes at 100, 175, and 250 replicates, plus five disjoint
50-replicate batches. For every family-endpoint combination, assess all three
removal effects and the interaction. Declare the 250-replicate result stable
only when:

1. context-equal estimates and conditional Monte Carlo bounds change by no
   more than the endpoint tolerance from 175 to 250;
2. interaction classification is unchanged at 100, 175, and 250;
3. the 250-replicate conditional Monte Carlo 95% half-width is no larger than
   the endpoint tolerance; and
4. source-level negative/near-zero/positive proportions change by less than
   `0.05` from 175 to 250.

Classify interaction as `more_than_additive`,
`near_additive_or_unresolved`, or `less_than_additive` using the endpoint
tolerance. This is an endpoint-scale conditional interaction, not proof of
ecological synergy.

The final decision vocabulary is:

- `stable_at_250`;
- `family_level_stable_source_distribution_unstable`;
- `unstable_at_250`;
- `heterogeneity_not_monte_carlo_limited`.

As a non-gating implementation diagnostic, compare the Goal 027 100-prefix
family estimates with Goal 026. Flag differences larger than the greater of
the endpoint tolerance and three times the combined conditional Monte Carlo
standard error. A flag triggers review; it does not alter the prespecified
250-replicate stability decision.

Stop at 250 under every outcome. Do not launch 500 or 1,000 replicates in this
goal.

## Execution Ladder

1. Implement and validate locally without running the full simulation.
2. Commit and push the exact execution source, then transport that frozen SHA
   to `deep-server-ts` by a checksummed Git bundle.
3. Run an all-515-source, five-replicate smoke in a unique `tmux` session.
4. Inspect schema, artifact hashes, source coverage, shared seeds, baseline
   reuse, and finite endpoints.
5. Only if the smoke passes, run the 250-replicate extension under a new run ID
   with 32 workers in `tmux`.
6. Audit the remote raw output and pull back compact summaries only.

Runs are all-or-nothing. On execution failure, preserve the run-specific
evidence and restart under a new run ID rather than adding checkpoint/resume
machinery.

## Required Tracked Surface

```text
docs/goals/027-module5-shared-four-arm-250rep-extension/
docs/module5_shared_four_arm_250rep_extension.md
data/module5_factorial_250rep_extension/
src/galaxias_model/module5_factorial_extension.py
src/galaxias_model/module5_factorial_extension_audit.py
scripts/run_module5_factorial_extension.py
scripts/audit_module5_factorial_extension.py
tests/test_module5_factorial_extension.py
```

A small performance-preserving change to the shared Module 5 output builder is
allowed if it avoids repeated Git subprocess calls while leaving existing
output semantics unchanged.

## Validation

- Synthetic tests must prove deterministic 63-bit seed derivation, one seed
  across four arms, one status-quo simulation per source-replicate block,
  exact plan counts, replicate-level interaction calculation with covariance,
  context/source weighting, and 250-replicate decision classification.
- Run the focused Goal 027 tests and the relevant existing Module 5 tests.
- Run the CLI help gates, contract validator, and `make fast-check` once before
  the execution-source commit.
- Verify both remote runs from disk, generate checksum manifests, and verify
  them.
- After compact pull-back, run the focused structured-output check,
  `git diff --check`, and one scientific review. Rerun `make fast-check` only if
  the completion-record edits touch executable code.

## Publication Boundary

Barry has authorized commits and pushes for the frozen execution source and
the final compact Goal 027 record after their respective gates pass. Stage
exact paths. Never commit or pull back raw matched outcomes, remote virtual
environments, logs containing bulky payloads, or generated local `outputs/`.

## Boundaries

- No pressure-semantic or intervention-contract changes.
- No rerun of unrelated Module 5 partitions.
- No automatic 500- or 1,000-replicate escalation.
- No polished figure, manuscript prose, final attribution conclusion, or
  publication-ready causal wording.
- No force-push, amend, rebase, reset, destructive cleanup, or mutation of
  prior remote artifacts.
- Perform one focused review and at most one material repair pass.

## Completion Condition

Goal 027 is complete when the frozen shared-four-arm implementation passes its
smoke, the 250-replicate extension and compact audit have either completed or
reported a precise blocker, and the stability decision is explicit without
stronger ecological or manuscript claims.
