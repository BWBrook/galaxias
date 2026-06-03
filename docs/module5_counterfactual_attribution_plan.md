# Module 5 Counterfactual Attribution Plan (Design Contract)

## Purpose and Boundaries

Module 5 is a **matched counterfactual attribution design** built on the
completed Module 4.5 mechanism interpretation. Its purpose is to define
what to contrast, at what granularity, and with what uncertainty treatment
before any production-level Module 5 simulations are run.

It is **not** a production attribution run. No new calibrations, simulations,
or remote/HPC jobs are launched in this step.

## Module 5 Ensemble Role (from Module 4.5)

Module 4.5 selected the following family roles for attribution design:

- Primary: `persistent_joint_cause`
- Sensitivity: `climbing_only`, `transient_perfect_storm`
- Negative references: `habitat_only_null`, `trout_only`

The decision table used is `data/module4_5_family_decision_table.csv` and is
treated as the **contractual family inventory** for this scaffold.

## Counterfactual Question

For each retained family proposal in the Module 4.5-approved family roles,
the counterfactual question is:

> What is the paired change in extinction and persistence outcomes when a
> specific threat axis is removed while holding all other proposal-level values
> and stochastic seed structure fixed?

The emphasis is on **matched stochastic contrasts**, not one-off deterministic
runs. Module 5 will later compare paired outcomes within family/proposal pairs
to reduce Monte Carlo noise.

## Deterministic Landmark Caveat (carried forward)

Module 4.5 deterministic landmark summaries retained a positive latent
abundance through 2002 while still supporting a joint-cause mechanism narrative.
Attribution from this phase therefore uses only **stochastic matched
counterfactual outcomes and detection-linked endpoints**. No deterministic
landmark trajectory should be interpreted as direct extinction-proof statements.

## Intervention Design

All interventions are anchored to `historical_lake` and the Module 4.5 family
inventory.

### Scenario Class

- `historical_match` — one contract class for all intervention/scenario rows in
  this initial scaffold.

### Intervention Axes

- `status_quo`
  - Baseline condition for the family in its accepted/sensitivity family context.
  - Holds all family proposal and intervention defaults unchanged.
- `no_trout_pressure`
  - Counterfactual that suppresses trout-mediated pressure.
  - Currently **design-only** until a Module 5 runner-level intervention hook
    is added for parameter forcing/override.
- `no_climbing_pressure`
  - Counterfactual that suppresses climbing-galaxias pressure.
  - Currently **design-only** for the same reason above.
- `no_trout_or_climbing_pressure`
  - Counterfactual that suppresses both trout and climbing pressure.
  - Requires a dual suppression hook; therefore currently **design-only**.

`baseline_source` for each row should resolve to
`data/module4_5_family_decision_table.csv` and the selected family proposal
set in implementation.

## Endpoints and Matched Contrast Logic

Primary endpoint:

- Probability of persistence past 2002 and matched expected extirpation-year
  contrast.

Secondary endpoints:

- Persistence past 1996, as a stochastic prevalence endpoint.
- Minimum total abundance across 1992-2002.
- Lake versus refuge persistence split in the terminal period.
- Expected detection-linked summaries (rather than latent-only summaries alone).
- Intervention–baseline contrasts by family/proposal pair using matched seed
  pairing (paired replicate indices).

Matched contrast fields are computed as `counterfactual - baseline` per
proposal/seed/replicate pairing and then summarised across replicates with
uncertainty summaries (median and interval bounds).

## Production Status and Scope

In this scaffold:

- `status_quo` rows are directly executable in principle under existing family-
  proposal machinery.
- Other axes are design-only placeholders for the next scaffold stage and are
  explicitly marked as requiring a module-level intervention implementation.

## Production-Readiness Gate for the Next Goal

Before moving to Module 5 production/prototype:

1. The counterfactual intervention contract and outcome schema in this goal are
   finalised and immutable.
2. A lightweight validator and focused test demonstrate:
   - required column coverage,
   - family-role reference integrity,
   - unique intervention IDs,
   - required axis presence,
   - contract schema completeness.
3. The `data/README.md` documents these artefacts and where generated outputs
   will be written.
4. Negative references remain negative references until matched stochastic
   outcomes show otherwise.

## Residual Work for Goal 002 (next)

- Implement the execution runner that maps rows in
  `data/module5_counterfactual_interventions.csv` into proposal-level matched
  simulation pairs.
- Generate and store contract-conforming outputs and provenance files.
- Add a short interpretation gate note that keeps causal language scoped to
  Module 4.5-conditioned attribution, not certainty claims.
