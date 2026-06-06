# Goal: Module 5 Production Readiness Gate

## Objective

Create a decision-ready production-readiness gate for the next Module 5 phase.
This goal defines the evidence, compute-routing, validation, output-handling,
and approval conditions required before any production attribution run can be
authorised.

This is a docs-only gate design. It does not authorise production Module 5,
remote compute, broad simulations, or manuscript-level interpretation.

## Why This Matters

Goals 001-003 established the Module 5 contract, tiny local runner prototype,
and disk-first smoke inspection. The project now needs a formal pause point
between smoke-scale mechanics and production-scale matched attribution.

The readiness gate makes that pause explicit. It records what SRF-A and Barry
must approve before production compute begins, what validation must pass, where
outputs may live, and what claim language remains off limits until production
results are reviewed.

## Scope

In scope:

- Create `docs/goals/004-module5-production-readiness/`.
- Define approval gates for:
  - retained family set;
  - intervention axes;
  - sample size and replicate count;
  - stochastic seed policy;
  - output schema and provenance capture;
  - ignored versus tracked output handling;
  - compute target and resource budget;
  - validation commands;
  - rollback and cleanup;
  - claim language.
- Define a proposed next-run ladder:
  - tiny local smoke already completed;
  - optional small local dry-run only if explicitly approved;
  - deliberate remote-compute plan via `/Users/bwbrook/work/nectar` for any
    production-sized job.
- Update discoverability or stale next-step wording in existing docs only if
  needed.

Out of scope:

- No production Module 5 attribution.
- No broad simulation batches.
- No remote compute or remote probes.
- No calibration reruns.
- No code, test, scientific-default, prior, target-weight, family-definition,
  observation-bridge, or Module 4.5 output changes.
- No manuscript-level causal claims.
- No commit or push.
- Generated outputs under `outputs/` must remain ignored and unstaged.

## Required Deliverables

1. Formal goal packet:
   - `Goal.md`
   - `Plan.md`
   - `Runbook.md`
   - `Log.md`

2. Readiness checklist:
   - exact approval gates;
   - explicit stop points;
   - validation ladder;
   - compute-routing decision points.

3. Narrow discoverability updates:
   - `docs/module5_counterfactual_attribution_plan.md`;
   - `README.md` or `data/README.md` only where needed.

## Approval Gates

Production Module 5 may not begin until SRF-A and Barry explicitly approve all
of the following:

- Family set:
  - primary: `persistent_joint_cause`;
  - sensitivity: `climbing_only`, `transient_perfect_storm`;
  - negative references: `habitat_only_null`, `trout_only`;
  - any deviation must be documented before execution.
- Intervention axes:
  - `status_quo`;
  - `no_trout_pressure`;
  - `no_climbing_pressure`;
  - `no_trout_or_climbing_pressure`;
  - any additional axis requires a new contract row and review.
- Sample size and replicate count:
  - proposal sampling source;
  - number of proposals per family;
  - stochastic replicates per proposal/intervention;
  - acceptance of any family weighting or stratification.
- Stochastic seed policy:
  - common-random-number pairing;
  - stable seed derivation;
  - reproducibility across restart/resume.
- Output schema:
  - all production rows conform to
    `data/module5_counterfactual_outcome_schema.csv`;
  - schema changes require review before compute.
- Provenance capture:
  - git SHA;
  - command line;
  - runner script path;
  - intervention contract path;
  - Module 4/4.5 source manifest paths;
  - compute host and environment summary;
  - output checksums for promoted artefacts.
- Output handling:
  - raw production outputs remain outside git under ignored `outputs/` locally
    or remote artifact/scratch paths;
  - only compact reviewed summaries may be considered for tracking;
  - no generated output is staged without explicit approval.
- Compute target and budget:
  - Mac mini only for smoke and small dry-run work;
  - use `/Users/bwbrook/work/nectar` to choose `deep-server`, Nectar, or other
    resources for production-sized work;
  - record expected wall time, storage, CPU/RAM needs, and stop rules.
- Validation:
  - contract validator;
  - focused runner/inspection tests;
  - `make fast-check`;
  - tiny smoke and disk-first inspection;
  - production dry-run or remote smoke if separately approved.
- Rollback and cleanup:
  - preserve source state;
  - keep generated outputs in ignored or remote artifact locations;
  - document cleanup commands before deleting any large outputs.
- Claim language:
  - production outputs may support only Module 4.5-conditioned matched
    attribution statements after review;
  - no final causal proof language;
  - no manuscript-level interpretation until a later gate.

## Stop Points

Stop for SRF-A/Barry approval before:

- changing the family set or intervention axes;
- choosing production proposal/replicate counts;
- launching any production-sized local or remote run;
- touching `/Users/bwbrook/work/nectar` for remote execution planning;
- moving generated output into tracked files;
- interpreting production results as causal evidence;
- drafting manuscript claims.

## Validation Gates

Docs-only validation for this goal:

- `git status --short --branch`
- `git diff --check`
- marker scan over changed/new tracked text

No tests are required while this goal remains docs-only. If code or tests
change, stop and report before validating.

## Done When

- The readiness gate packet exists and is self-contained.
- Existing docs point to the readiness gate where useful.
- The branch has only docs changes.
- Whitespace and marker scans pass.
- Final report confirms no production attribution, compute, code, tests,
  commit, or push occurred.
