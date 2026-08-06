# Goal 022 Runbook

## Baseline

```bash
pwd
git branch --show-current
git rev-parse HEAD
git status --short --branch
```

Stop if the baseline is not clean `main` at
`3963315b8b3f82eee42aace00de78a99ab37d0a1` plus this untracked packet.

## Focused Validation

```bash
uv run pytest \
  tests/test_module5_output_checks.py \
  tests/test_module5_smoke_inspection.py \
  tests/test_module5_dry_run_inspection.py \
  tests/test_module5_production_rehearsal.py \
  tests/test_module5_production_summary.py -q
make fast-check
git diff --check
```

Use structural searches to confirm:

- partition definitions and mapping exist in one production module;
- common ordered-schema, source-identity, matched-pair-ID, and seed-pairing
  logic each have one production implementation;
- `module5_rehearsal.py` no longer owns disk inspection/report generation;
- the four named dead/redundant residues are absent;
- run-specific inspectors retain their unique boundary checks.

Do not run production, remote commands, or broad output regeneration.

## Stop Conditions

Stop and report rather than:

- designing a configurable validation framework;
- changing check semantics merely to make extraction easier;
- adding compatibility wrappers for moved internal code;
- renaming CLIs or output artefacts;
- extending cleanup into unrelated modules;
- staging, committing, or pushing.

After one focused review, make at most one material repair pass. Do not polish
module boundaries or names beyond what the required outcomes need.

## Report

Report final branch, HEAD, status, exact changed paths, before/after ownership
of checks, removed residue, focused and full validation, deviations, and
residual risks. Send a wake-up on completion or blockage.
