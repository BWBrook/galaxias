# Runbook

## Read First

- `AGENTS.md`
- `README.md`
- `docs/module5_counterfactual_attribution_plan.md`
- `docs/goals/001-module5-counterfactual-design-and-smoke/`
- `docs/goals/002-module5-runner-prototype/`
- `docs/goals/003-module5-smoke-inspection/`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`

## Operating Mode

Docs-only production-readiness gate design. Do not run production Module 5,
remote compute, broad simulations, or tests unless a future implementation goal
explicitly authorises them.

## Readiness Decision Sequence

1. Confirm baseline contract state.
   - Review `data/module5_counterfactual_interventions.csv`.
   - Review `data/module5_counterfactual_outcome_schema.csv`.
   - Confirm Goal 002 and Goal 003 validation evidence remains accepted.
   - Stop if the contract or schema changed since the smoke inspection.

2. Confirm family and intervention scope.
   - Primary family remains `persistent_joint_cause`.
   - Sensitivity families remain `climbing_only` and
     `transient_perfect_storm`.
   - Negative references remain `habitat_only_null` and `trout_only`.
   - Intervention axes remain `status_quo`, `no_trout_pressure`,
     `no_climbing_pressure`, and `no_trout_or_climbing_pressure`.
   - SRF-A/Barry must approve any change before execution.

3. Decide production sample size.
   - Specify proposal source table or artifact.
   - Specify proposals per family.
   - Specify stochastic replicates per proposal/intervention.
   - Specify whether family weighting is equal, accepted-frontier weighted, or
     sensitivity-only.
   - Stop for SRF-A/Barry approval before implementation.

4. Decide stochastic seed policy.
   - Preserve common-random-number pairing.
   - Define seed derivation from proposal, intervention, and replicate IDs.
   - Define restart/resume behaviour.
   - Stop if pairing cannot be inspected from disk.

5. Decide output and provenance handling.
   - Raw production outputs stay ignored under local `outputs/` or remote
     artifact/scratch paths.
   - Compact summaries are reviewed before tracking.
   - Provenance must capture git SHA, command line, runner path, contract path,
     Module 4/4.5 manifest paths, compute host, environment summary, and
     checksums for promoted artefacts.

6. Decide compute target.
   - Mac mini remains appropriate for smoke and explicitly approved small
     local dry-runs.
   - Any production-sized run requires deliberate planning through
     `/Users/bwbrook/work/nectar`.
   - The default production-sized CPU/RAM candidate should be selected from
     current Nectar control-plane guidance, usually `deep-server` first unless
     the control-plane docs say otherwise.
   - Stop before remote probes or remote execution.

7. Define validation ladder.
   - Contract validator.
   - Focused runner tests.
   - Focused inspection tests.
   - `make fast-check`.
   - `make module5-smoke`.
   - `make module5-inspect`.
   - Future approved local dry-run validation.
   - Future approved remote smoke validation before production run.

8. Define rollback and cleanup.
   - Preserve source branch and exact git SHA.
   - Keep generated outputs in ignored or remote artifact locations.
   - Record cleanup commands before deleting large outputs.
   - Do not remove raw artifacts until SRF-A/Barry approve retention policy.

9. Define claim-language guardrail.
   - Before production results are reviewed, say only that the project is
     ready or not ready for production Module 5.
   - After production results are reviewed, any claim must remain
     Module 4.5-conditioned matched attribution under sparse evidence.
   - Do not use final-causal-proof or manuscript-ready causal language at this
     gate.

## Proposed Next-Run Ladder

1. Completed:
   - Goal 002 tiny local smoke runner.
   - Goal 003 disk-first smoke inspection.

2. Optional next implementation gate:
   - an explicitly approved small local dry-run that exercises production-like
     proposal selection and output partitioning at minimal scale.

3. Production-sized planning gate:
   - use `/Users/bwbrook/work/nectar` to choose compute target, paths, resource
     budget, remote smoke, and artifact-retention rules.

4. Production execution gate:
   - run only after SRF-A/Barry approve the production spec, compute target,
     validation ladder, and claim-language guardrail.

## Validation For This Goal

Docs-only validation:

```bash
git status --short --branch
git diff --check
```

Marker scan:

```bash
{ git diff --name-only --diff-filter=ACM; git ls-files --others --exclude-standard; } | sort
```

Use those paths for a narrow scan of production-claim, remote-run, and
manuscript-claim language before reporting.

## Boundaries

Pause before:

- production Module 5 attribution;
- broad simulation batches;
- remote compute or remote probes;
- calibration reruns;
- code, test, scientific-default, prior, target-weight, family-definition,
  observation-bridge, or Module 4.5 output changes;
- manuscript-level causal claims;
- commit, push, or staging.
