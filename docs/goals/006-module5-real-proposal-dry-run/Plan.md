# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`. Treat repo-local
instructions and this packet as the source of truth. Do not read
`/Users/bwbrook/chief_of_staff` or `/Users/bwbrook/work/goal_composer`.

Use `uv run python`, not bare `python`. Keep generated outputs under ignored
`outputs/`.

## Starting State Guard

1. Record:
   - `pwd`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse --short=12 HEAD`
   - `git status --short --branch`

2. Expected pre-work dirty state is limited to the accepted Goal 005 context
   and this Goal 006 packet:
   - `docs/goals/005-module5-dry-run-production-spec/`
   - `docs/module5_dry_run_production_spec.md`
   - `docs/goals/006-module5-real-proposal-dry-run/`

3. If any other pre-work dirty state exists, stop and report it to Galaxias
   before editing.

## File Structure

Prefer focused additions over turning the current smoke modules into a single
large mixed-purpose file.

Likely responsibilities:

- `src/galaxias_model/module5_proposals.py`: load/validate proposal
  membership rows and convert `parameter_values.csv.gz` rows into
  `ResolvedParameters`.
- `src/galaxias_model/module5_counterfactual.py`: keep shared matched-pair
  output construction and retain the existing smoke runner.
- `src/galaxias_model/module5_dry_run_inspect.py`: disk-first inspection for
  the real-proposal dry run.
- `scripts/run_module5_real_proposal_dry_run.py`: CLI wrapper for the approved
  local dry run.
- `scripts/inspect_module5_real_proposal_dry_run.py`: CLI wrapper for dry-run
  inspection.
- `tests/test_module5_real_proposal_dry_run.py`: focused resolver and runner
  tests.
- `tests/test_module5_dry_run_inspection.py`: focused inspection tests.
- `Makefile`: add `module5-dry-run` and `module5-dry-run-inspect`.

If a different decomposition is cleaner after reading the local code, use it,
but preserve the same external behavior and test coverage.

## Tasks

### Task 1: Read And Log Context

- Read this full packet.
- Read `AGENTS.md`, `README.md`, `docs/module5_dry_run_production_spec.md`,
  `docs/module5_counterfactual_attribution_plan.md`, and prior Module 5 goal
  logs as needed.
- Inspect the current runner, smoke inspector, scripts, tests, Makefile, and
  relevant data tables.
- Update `Log.md` with the starting state and read-first notes.

### Task 2: Prove The Proposal Inputs

- Add a focused test proving the approved five proposal IDs are present as
  `in_family_winners` rows for `variant_id == "baseline_current"` and
  `seed == 20260410`.
- Add a focused test proving the local parameter-values artifact has exactly
  40 parameter rows for each selected proposal.
- Add a manifest/hash check helper or test. It should compare the local
  `parameter_values.csv.gz` SHA-256 to the manifest row before the real dry
  run proceeds.
- Stop if the local artifact is absent or mismatched.

### Task 3: Resolve Real Proposal Parameters

- Implement a small resolver that accepts:
  - `ModelInputs`;
  - selected proposal metadata;
  - the parameter-values table or path;
  - one `proposal_id`.
- Return `ResolvedParameters` with:
  - `family_id` and `family_label` from the proposal/family metadata;
  - `values` from `value_natural`;
  - `statuses` from `parameter_status`;
  - a manifest that retains parameter ID, status, active flag, effective value,
    sampled flag, and enough prior/family metadata to debug the row.
- Validate:
  - one and only one family for the proposal;
  - exactly 40 unique parameter IDs;
  - no missing or duplicate parameter rows;
  - proposal family matches the selected membership row and intervention
    family;
  - resolved constraints remain valid, or else stop with a precise error.

### Task 4: Add The Real-Proposal Dry-Run Runner

- Add a runner that consumes the approved selected proposals and the current
  intervention table.
- For each selected intervention row:
  - resolve the matching real proposal for that row's family;
  - run baseline and intervention arms with the same stochastic seed;
  - emit the real `proposal_id`, `variant_id`, `seed`, and `proposal_seed`;
  - preserve existing Module 5 outcome schema order.
- Use a stable SHA-256 seed derivation from:
  - base label `galaxias-module5-dry-run-v1`;
  - `proposal_id`;
  - `intervention_id`;
  - `stochastic_replicate_id`.
- Do not use Python's process-randomized `hash()`.
- Keep the existing `run_module5_counterfactual_smoke` path and smoke labels
  working exactly as before.

### Task 5: Add Dry-Run Provenance

Dry-run provenance must record at least:

- status label such as `real_proposal_local_dry_run`;
- `production_attribution: false`;
- output file and output directory;
- command/script path;
- selected proposal IDs and source filter;
- intervention contract path;
- outcome schema path;
- proposal membership table path;
- raw Module 4 manifest path;
- parameter-values artifact path and SHA-256;
- git SHA and dirty-state summary;
- Python version;
- compute host;
- replicate count;
- seed derivation rule and base label;
- boundary note saying the dry run is not production attribution and not
  manuscript evidence.

### Task 6: Add Disk-First Dry-Run Inspection

Add an inspector that reads emitted dry-run files from disk and writes:

- `inspection/inspection_summary.json`
- `inspection/inspection_checks.csv`
- `inspection/inspection_report.md`

Required checks:

- schema columns exactly match `data/module5_counterfactual_outcome_schema.csv`;
- row count is 50 for the approved dry run;
- proposal IDs are exactly the approved five;
- intervention IDs are exactly the current ten intervention rows;
- matched pair IDs are nonblank and unique;
- baseline and intervention stochastic seeds match within each row;
- provenance status is `real_proposal_local_dry_run`;
- `production_attribution` is false;
- boundary note contains clear non-production and non-manuscript language.

### Task 7: Add Commands

Add CLI and Makefile surfaces:

```bash
make module5-dry-run
make module5-dry-run-inspect
```

The dry-run target should write to:

```text
outputs/module5_dry_run_baseline_current_20260410/
```

The inspect target should inspect that directory.

### Task 8: Validate

Run the validation ladder in `Runbook.md`. Record exact commands and outcomes
in `Log.md`.

If a command fails, do not hide it. Diagnose, fix narrowly if within scope, and
rerun the focused check. If the failure suggests a scientific contract change
or broader compute decision, stop and wake Galaxias.

### Task 9: Final Report And Wake-Up

Before waking Galaxias:

- confirm generated outputs are under ignored `outputs/`;
- run `git status --short --branch`;
- update `Log.md` with final status, generated output paths, validation
  evidence, and any risks;
- do not stage, commit, push, or publish.

Send a short wake-up to Galaxias thread
`019eaac3-85f6-7853-bc28-a4d905dadfc3` when complete or blocked.
