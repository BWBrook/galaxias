# Goal: Module 5 Smoke Inspection

## Objective

Create a disk-first inspection layer for the tiny Module 5 smoke runner output.
The inspection layer reads emitted `matched_outcomes.csv` and `provenance.json`
files from disk and writes a review bundle under ignored `outputs/`.

This is a runner-output review and contract layer. It is not production Module
5 attribution and does not support manuscript-level causal claims.

## Why This Matters

Goal 002 made the Module 5 smoke runner executable. Goal 003 makes its emitted
files easier for SRF-A and Barry to review without rerunning broad simulations
or treating smoke rows as scientific results.

The inspector should answer simple contract questions:

- Do the output columns match the declared outcome schema?
- Are matched pair identifiers stable and unique?
- Are baseline and intervention stochastic seeds paired?
- Does provenance label the output as tiny local smoke only?
- Does the emitted review bundle preserve the boundary that these files are
  not production attribution or manuscript evidence?

## Scope

In scope:

- Create `docs/goals/003-module5-smoke-inspection/`.
- Add a small source module that consumes the Goal 002 smoke output from disk.
- Add a CLI script defaulting to `outputs/module5_runner_smoke/`.
- Write an inspection bundle under
  `outputs/module5_runner_smoke/inspection/`.
- Add focused tests for schema, pairing, provenance, and smoke-only boundary
  checks.
- Add a narrow Makefile target if it fits the existing command style.
- Update discoverability docs only where useful.

Out of scope:

- No production Module 5 attribution.
- No broad simulation batches.
- No remote compute.
- No calibration reruns.
- No changes to scientific defaults, priors, target weights, family
  definitions, observation-bridge assumptions, or Module 4.5 outputs.
- No manuscript-level causal claims.
- No commit or push.
- Generated outputs under `outputs/` must remain ignored and unstaged.

## Required Deliverables

1. Formal goal packet:
   - `Goal.md`
   - `Plan.md`
   - `Runbook.md`
   - `Log.md`

2. Inspection implementation:
   - `src/galaxias_model/module5_smoke_inspect.py`
   - `scripts/inspect_module5_counterfactual_smoke.py`

3. Focused tests:
   - passing inspection on valid smoke output;
   - failing inspection on broken seed pairing.

4. Optional command surface:
   - `make module5-inspect`, if added.

## Validation Gates

- `uv run python scripts/validate_module5_counterfactual_contract.py`
- focused pytest for new/changed tests
- `make fast-check`
- `make module5-smoke`
- new inspection CLI or Makefile target
- `git diff --check`
- marker scan over changed/new tracked text
- `git status --short --branch`

## Decision Authority

Executor may define the exact inspection summary/report format while preserving
the disk-first, smoke-only, no-claims boundary.

Executor must pause before production attribution, broad simulations, remote
work, scientific-default changes, manuscript claims, commits, or pushes.

## Done When

- The inspection layer can read disk outputs and write an inspection bundle.
- The focused tests pass.
- The inspection bundle remains under ignored `outputs/`.
- Validation evidence is recorded in `Log.md`.
- The final report confirms no production attribution, commit, push, or remote
  compute occurred.
