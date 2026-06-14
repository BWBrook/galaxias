# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias` and the authorized
`deep-server` remote paths created for this goal.

Treat repo-local instructions and this Goal 012 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff` or
`/Users/bwbrook/work/goal_composer`.

This goal authorizes one 25-replicate rehearsal on `deep-server` after local
implementation, local validation, source-artifact verification, and remote
preflight. It does not authorize the 100-replicate production run or any
science/manuscript interpretation.

## Starting State Guard

1. Record:
   - `pwd`
   - `git rev-parse --abbrev-ref HEAD`
   - `git rev-parse --short=12 HEAD`
   - `git status --short --branch`

2. Expected pre-work dirty state is the accepted Goal 005/006/007/008/009/010
   and Goal 011 surface plus this Goal 012 packet. If the status has unrelated
   changes outside the accepted Module 5 goal surface, stop and report before
   editing or running remote commands.

3. Confirm that `data/module4_5_proposal_set_membership.csv`,
   `data/module4_raw_artifact_manifest.csv`,
   `data/module5_counterfactual_interventions.csv`, and the Goal 011 source
   identity files are present.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- `docs/module5_production_run_spec.md`
- `docs/module5_remote_smoke_preflight.md`
- `docs/module5_source_identity_contract.md`
- `docs/module5_production_matrix_contract.md`
- `docs/goals/009-module5-production-run-spec/Log.md`
- `docs/goals/010-module5-deep-server-remote-smoke-preflight/Log.md`
- `docs/goals/011-module5-source-context-identity/Log.md`
- `data/module4_5_proposal_set_membership.csv`
- `data/module4_raw_artifact_manifest.csv`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`
- `src/galaxias_model/module5_proposals.py`
- `src/galaxias_model/module5_counterfactual.py`
- `src/galaxias_model/module5_dry_run_inspect.py`
- existing Module 5 runner and inspector scripts
- existing focused Module 5 tests

Do not read Chief of Staff, Goal Composer, sibling projects, or archive
material.

## Task 1: Confirm Rehearsal Counts

Run a structured CSV count from the current repo state.

Confirm:

- accepted-frontier rows:
  - 265 `persistent_joint_cause`
  - 235 `climbing_only`
  - 250 `transient_perfect_storm`
- `family_winners` rows:
  - 15 `habitat_only_null`
  - 15 `trout_only`
- 15 accepted/winner source contexts;
- 15 matching `parameter_values` manifest rows;
- no missing source contexts in the manifest;
- 25-replicate rehearsal total: 69,875 rows.

Stop and wake Galaxias if these counts differ.

## Task 2: Design The Smallest Coherent Rehearsal Surface

Prefer a small, testable production-rehearsal module over scattering logic
across CLI scripts.

The implementation should make these concepts explicit:

- source selection;
- partition definition;
- required parameter artifact resolution;
- artifact verification by manifest size and SHA-256;
- source-key-aware loading of proposal parameters from the correct
  `parameter_values.csv.gz` file for each source context;
- matched execution using the Goal 011 source identity contract;
- resumable or at least restart-detectable output layout;
- disk-first inspection with exact partition and replicate coverage checks.

If an existing helper can be reused safely, reuse it. If reuse would make the
runner harder to inspect, add a narrow new helper.

## Task 3: Write Focused Tests

Use fail-first evidence where practical. Add focused tests that prove:

- accepted and diagnostic source selections have the expected counts;
- the 25-replicate rehearsal arithmetic is exactly 69,875 rows;
- the full run has 2,795 source/intervention units;
- distinct source rows remain keyed by `proposal_source_key`;
- bare `proposal_id` collisions do not collide in seed or matched-pair IDs;
- artifact resolution maps each source context to exactly one
  `parameter_values` manifest row;
- missing or hash-mismatched artifacts fail before execution;
- the inspector rejects missing units, wrong partition counts, duplicate
  `(proposal_source_key, intervention_id, stochastic_replicate_id)` grains,
  missing source keys, or incomplete replicate sets.

It is acceptable for the tests to use small fixtures or a tiny execution mode
for speed, as long as the selection arithmetic and artifact-resolution checks
use the real tracked CSV contracts.

## Task 4: Implement Local Rehearsal Preflight And Runner

Implement the local code and CLI surface needed to:

- build the rehearsal manifest;
- print or write the expected partition plan;
- verify required local or remote artifact metadata;
- run a tiny local validation mode if helpful;
- run the remote rehearsal from a checked source mirror;
- inspect the remote rehearsal outputs from disk.

Do not run the 69,875-row rehearsal locally unless you decide it is genuinely
cheap and useful. The authorized full rehearsal target is `deep-server`.

The runner provenance must record:

- `production_attribution: false`;
- a rehearsal status label such as `module5_25rep_rehearsal`;
- run ID and timestamp;
- source identity fields and strategy;
- selected source row counts by family and partition;
- required artifact manifest rows and verification status;
- partition plan and expected row counts;
- replicate count;
- seed derivation rule.

## Task 5: Local Validation Before Remote

Run and record focused validation before using remote compute:

- the new focused rehearsal tests;
- existing source-identity and real-proposal dry-run tests affected by shared
  code;
- `uv run python scripts/validate_module5_counterfactual_contract.py`;
- `make module5-dry-run`;
- `make module5-dry-run-inspect`;
- `make fast-check`;
- `git diff --check`.

If `make fast-check` fails outside Goal 012 scope, stop and wake Galaxias with
the exact failure instead of broadening.

## Task 6: Remote Preflight

Use `deep-server-ts` first. Use `utas-ubuntu` only as fallback and record why.

Before creating the tmux run, record:

- remote host and user;
- `/data` free space;
- `uv --version`;
- `python3 --version`;
- `tmux -V`;
- source mirror path;
- scratch path;
- artifact path.

Create a disposable source mirror under `/data/codex/repos` from the local
accepted dirty state. Exclude only bulky/cache paths not needed for execution.

Verify all 15 required `parameter_values` artifacts by manifest size and
SHA-256. Prefer existing `remote_artifact_path` files if present and correct;
otherwise transfer the required `local_path` files and verify again.

Stop before rehearsal execution if any remote preflight or artifact check
fails.

## Task 7: Remote Rehearsal Execution

Run the 25-replicate rehearsal in a durable `tmux` session.

Capture:

- exact command;
- stdout/stderr log;
- exit code;
- start/end UTC timestamps;
- duration;
- environment facts;
- storage footprint;
- checksum manifest.

Raw matched outcomes and other large artifacts should remain under the remote
artifact path. Do not copy raw matched outcomes into the local repo.

## Task 8: Remote Inspection

Run the disk inspector over the remote rehearsal artifact.

Required pass criteria:

- total matched rows: 69,875;
- partition counts match the table in `Goal.md`;
- source/intervention units: 2,795;
- distinct source rows: 780, with 235 accepted `climbing_only` rows reused for
  the diagnostic sidecar;
- every unit has exactly 25 rows;
- replicate IDs are exactly `0..24` for every unit;
- no seed mismatches;
- source-identity check passes;
- no duplicate matched-pair IDs;
- no duplicate run IDs within each baseline/counterfactual arm;
- provenance has `production_attribution: false`;
- output schema conforms to
  `data/module5_counterfactual_outcome_schema.csv`;
- artifact checksums are recorded.

If any check fails, do not repair by changing scientific semantics. Capture
the evidence, preserve the remote artifacts, and wake Galaxias.

## Task 9: Local Compact Report

Create `docs/module5_25rep_rehearsal_report.md`.

The report should be compact and evidence-oriented:

- objective and boundary;
- run ID, target, tmux session, paths;
- source and partition row counts;
- artifact verification summary;
- local validation summary;
- remote execution summary;
- inspection summary;
- artifact inventory and checksums;
- deviations and residual risks;
- clear stop point before 100-replicate production or interpretation.

Do not paste raw matched-outcome rows into the report.

## Task 10: Final Log And Wake-Up

Update `Log.md` with:

- all evidence required by `Goal.md`;
- final changed files;
- final branch, HEAD, and status;
- local ignored outputs, if any;
- remote artifact paths;
- deviations, risks, and questions;
- recommended next-goal shape.

Send a short wake-up to Galaxias thread
`019eaac3-85f6-7853-bc28-a4d905dadfc3` on completion or blockage, then wait.
