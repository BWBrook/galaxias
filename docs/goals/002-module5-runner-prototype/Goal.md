# Goal: Module 5 Runner Prototype

## Objective

Create a tiny local Module 5 runner prototype that consumes the existing
counterfactual intervention contract and writes contract-conforming matched
baseline/intervention smoke outputs under ignored `outputs/`.

This goal is complete when the repo has a reviewable runner surface, focused
tests, and validation evidence showing that matched proposal/seed/replicate
pairing is preserved for smoke rows.

## Why This Matters

Goal 001 made Module 5 a written and machine-checkable design contract. Goal
002 turns that contract into the smallest executable runner scaffold so later
work can review the mechanics before any production attribution is authorised.

The prototype deliberately uses default-parameter smoke proposals. Its outputs
test wiring, schema shape, common-random-number pairing, and intervention hook
plumbing only. They are not production attribution results.

## Scope

In scope:

- Create `docs/goals/002-module5-runner-prototype/`.
- Add a tiny local runner that reads
  `data/module5_counterfactual_interventions.csv`.
- Produce matched baseline/intervention rows conforming to
  `data/module5_counterfactual_outcome_schema.csv`.
- Write generated smoke outputs only under ignored `outputs/`.
- Add narrow intervention override hooks for:
  - `status_quo`;
  - `no_trout_pressure`;
  - `no_climbing_pressure`;
  - `no_trout_or_climbing_pressure`.
- Preserve matched stochastic seeds between baseline and intervention arms.
- Add focused tests for override and matched-output behaviour.
- Update stale `data/README.md` immediate-next-step wording if present.

Out of scope:

- No production Module 5 analysis.
- No broad simulation batches.
- No remote compute or HPC work.
- No calibration reruns.
- No changes to scientific defaults, priors, target weights, family
  definitions, observation-bridge assumptions, or Module 4.5 outputs.
- No manuscript-level causal claims.
- No commit, push, or staging in this turn.
- Do not stage generated outputs under git.

## Required Deliverables

1. Formal goal packet:
   - `Goal.md`
   - `Plan.md`
   - `Runbook.md`
   - `Log.md`

2. Tiny runner prototype:
   - a narrow module-level runner implementation;
   - a CLI script for local smoke execution;
   - generated CSV/provenance outputs under `outputs/`.

3. Focused tests:
   - intervention override hook behaviour;
   - matched baseline/intervention seed pairing;
   - output columns conforming to the declared schema.

4. Documentation:
   - narrow `data/README.md` update if needed.

## Validation Gates

Run, proportionate to this bounded prototype:

- `uv run python scripts/validate_module5_counterfactual_contract.py`
- focused pytest for the new or changed runner tests
- `make fast-check` if it remains local and bounded
- `git diff --check`
- `git status --short --branch`

## Decision Authority

Executor may make narrow implementation choices needed for smoke-run wiring,
including row identifiers, default smoke seeds, and generated output paths.

Executor must pause before production attribution, remote work, broad simulator
changes, scientific-default changes, manuscript claims, commits, or pushes.

## Done When

- The branch contains a Goal 002 packet and tiny runner prototype.
- Focused tests pass.
- Generated outputs are under ignored `outputs/`.
- Validation evidence is recorded in `Log.md`.
- The final report confirms no production attribution, commit, push, or remote
  compute occurred.
