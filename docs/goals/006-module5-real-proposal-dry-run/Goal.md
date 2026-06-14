# Goal: Module 5 Real-Proposal Local Dry Run

## Objective

Implement and validate a small local Module 5 dry run that consumes real
Module 4.5 proposal rows, exercises the current Module 5 intervention matrix,
and writes inspectable ignored outputs.

This goal is an execution-contract and plumbing check. It is not production
counterfactual attribution, remote compute, or manuscript evidence.

## Approved Dry-Run Shape

Use the Goal 005 recommendation unchanged:

| family_id | module5_role | proposal_id | source |
| --- | --- | --- | --- |
| `persistent_joint_cause` | primary | `persistent_joint_cause:p00162` | `family_winners`, `baseline_current`, seed `20260410` |
| `climbing_only` | sensitivity | `climbing_only:p00216` | `family_winners`, `baseline_current`, seed `20260410` |
| `transient_perfect_storm` | sensitivity | `transient_perfect_storm:p00144` | `family_winners`, `baseline_current`, seed `20260410` |
| `habitat_only_null` | negative_reference | `habitat_only_null:p00761` | `family_winners`, `baseline_current`, seed `20260410` |
| `trout_only` | negative_reference | `trout_only:p00814` | `family_winners`, `baseline_current`, seed `20260410` |

Run all current rows in `data/module5_counterfactual_interventions.csv`:

- 10 intervention rows total.
- 10 proposal/intervention combinations, because each intervention row applies
  to one selected family.
- 5 matched stochastic replicates per proposal/intervention combination.
- Expected `matched_outcomes.csv` rows: 50.
- Output directory:
  `outputs/module5_dry_run_baseline_current_20260410/`.

## Required Inputs

Tracked source tables:

- `data/module4_5_proposal_set_membership.csv`
- `data/module4_raw_artifact_manifest.csv`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`
- `data/module4_5_family_decision_table.csv`

Ignored local raw Module 4 artifact mirror:

- `outputs/remote/module4_observation_sensitivity_20260522T101942Z/baseline_current_seed20260410/parameter_values.csv.gz`

The `parameter_values.csv.gz` file is listed in
`data/module4_raw_artifact_manifest.csv` with local SHA-256
`49e080a23dcaca2f29874c0e3825bd806406f494b2db046307a84a74e8673c4c`.

If the raw parameter-values artifact is missing, has a manifest/hash mismatch,
or does not contain all 5 selected proposals with 40 parameters each, stop and
report to Galaxias. Do not fetch remote artifacts during this goal.

## Scope

In scope:

- Add tests for real-proposal selection, proposal-parameter resolution,
  matched common-random-number pairing, schema-conforming output, and disk-first
  dry-run inspection.
- Implement a focused real-proposal resolver that converts selected rows from
  `parameter_values.csv.gz` into simulator-ready `ResolvedParameters`.
- Add a real-proposal dry-run runner while preserving the existing smoke runner
  and smoke-only labels.
- Add a dry-run inspector that proves row counts, schema order, selected
  proposal IDs, matched pair IDs, common random seeds, provenance labels, and
  non-production boundary language from disk.
- Add narrow CLI scripts and Makefile targets for the dry run and inspection.
- Update `docs/goals/006-module5-real-proposal-dry-run/Log.md` as work
  proceeds.
- Make only narrow README or `data/README.md` discoverability updates if the
  new commands would otherwise be hard to find.

Out of scope:

- No production Module 5 attribution.
- No production-sized simulation batches.
- No remote compute, remote probes, remote fetches, or Nectar planning.
- No changes to model families, priors, targets, observation bridges, Module
  4.5 summary tables, intervention rows, or outcome-schema rows.
- No manuscript claims or causal proof language.
- No staging, commit, push, PR, or publication step.
- Do not normalize historical `SRF-A` wording unless a future docs goal
  explicitly authorizes it.

## Allowed Source Changes

Expected source-change surface:

- `docs/goals/006-module5-real-proposal-dry-run/Log.md`
- `src/galaxias_model/module5_counterfactual.py`
- optional focused helper modules such as
  `src/galaxias_model/module5_proposals.py` or
  `src/galaxias_model/module5_dry_run_inspect.py`
- `scripts/run_module5_real_proposal_dry_run.py`
- `scripts/inspect_module5_real_proposal_dry_run.py`
- focused tests under `tests/`
- `Makefile`
- optional narrow discoverability edits to `README.md` or `data/README.md`

Do not edit the tracked CSV contracts unless you stop first and ask Galaxias.

## Output Policy

Generated dry-run outputs are allowed only under:

- `outputs/module5_dry_run_baseline_current_20260410/`

That directory must remain ignored and unstaged. At minimum, it should contain:

- `matched_outcomes.csv`
- `provenance.json`
- inspection outputs under an `inspection/` subdirectory

Raw matched outcomes remain generated artifacts, not tracked evidence. Compact
summaries may be proposed for tracking only in a later review/publish goal.

## Done When

- The dry-run code resolves the five approved real proposal rows from local raw
  Module 4 artifacts.
- The dry run writes exactly 50 schema-conforming rows from 10 intervention
  rows x 5 stochastic replicates.
- Existing smoke behavior and smoke-only boundary tests still pass.
- Disk-first dry-run inspection passes and writes an ignored inspection bundle.
- Validation commands in `Runbook.md` pass or any failure is logged with exact
  command output and diagnosis.
- `Log.md` records starting state, files changed, commands run, generated
  output paths, validation evidence, and remaining risks.
- Final status is left uncommitted and unstaged for Galaxias review.
- `pedder` sends a short wake-up to the Galaxias orchestrator thread on
  completion or blockage.
