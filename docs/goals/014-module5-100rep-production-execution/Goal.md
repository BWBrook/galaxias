# Goal: Module 5 100-Replicate Production Execution

## Objective

Execute and inspect the full 100-replicate Module 5 production run on
`deep-server` from the frozen preproduction baseline commit:

```text
ddb8a6de583e85f170f46c9dec9b1246baa6dccc
```

This goal is execution and inspection only. It should produce a durable remote
artifact set, checksum manifest, disk inspection record, compact local report,
and Goal 014 log evidence.

This goal does not authorize production attribution interpretation, final
causal effect claims, manuscript language, figure/table preparation, PR
creation, or generated-output promotion into Git.

## Why This Matters

Goal 012 proved the source-key-aware runner and inspector on the exact
production source shape at 25 replicates. Goal 013 froze that accepted surface
into a clean pushed commit. The project can now run the full 100-replicate
execution from a stable Git SHA rather than from an uncommitted dirty tree.

The 100-replicate run is the production execution artifact, but it is not by
itself the interpretation step. Interpretation should wait for a separate
Goal 015 after Galaxias reviews the production inspection evidence.

## Authorized Run Shape

Run from Git commit:

```text
ddb8a6de583e85f170f46c9dec9b1246baa6dccc
```

Use the Goal 012 partition contract with 100 replicates:

| selection | source rows | intervention rows | replicate count | expected rows |
| --- | ---: | ---: | ---: | ---: |
| `headline/persistent_joint_cause` | 265 | 4 | 100 | 106,000 |
| `headline/climbing_only` | 235 | 2 | 100 | 47,000 |
| `headline/transient_perfect_storm` | 250 | 4 | 100 | 100,000 |
| `diagnostic_sidecar/climbing_only_no_trout_pressure` | 235 | 1 | 100 | 23,500 |
| `negative_reference/habitat_only_null` | 15 | 1 | 100 | 1,500 |
| `negative_reference/trout_only` | 15 | 1 | 100 | 1,500 |
| total production execution | 780 distinct source rows, with 235 reused for the sidecar | mixed | 100 | 279,500 |

Required source and identity invariants:

- 15 source contexts;
- 15 verified `parameter_values.csv.gz` artifacts;
- 2,795 source/intervention units;
- 780 distinct `proposal_source_key` values;
- replicate IDs exactly `0..99` for every unit;
- zero baseline/counterfactual seed mismatches;
- matched-pair IDs and run IDs must use the Goal 011 source identity contract;
- output schema must conform to
  `data/module5_counterfactual_outcome_schema.csv`.

## Remote Execution Contract

Default remote target:

- first and expected target: `deep-server-ts`;
- no fallback unless Galaxias explicitly authorizes it after a blocker.

Recommended run identity:

- run ID: `YYYYMMDDTHHMMSSZ-goal014-m5-100rep-production`;
- tmux session: `galaxias-m5-prod-YYYYMMDDTHHMMSSZ`;
- source checkout:
  `/data/codex/repos/galaxias-goal014-m5-100rep-production-<RUN_ID>`;
- scratch:
  `/data/codex/scratch/galaxias/module5_100rep_production_<RUN_ID>`;
- artifacts:
  `/data/codex/artifacts/galaxias/module5_100rep_production_<RUN_ID>`.

Use a fresh remote Git checkout or clone pinned to
`ddb8a6de583e85f170f46c9dec9b1246baa6dccc`. Do not use a dirty rsync mirror
for this goal.

Use 32 workers by default, matching the successful Goal 012 rehearsal. If
preflight suggests a different worker count is safer, stop and wake Galaxias
before changing it.

## Restart And Resume Policy

This run should be restartable by run directory, not by mutating raw output.

Before launching, record whether the target artifact and scratch directories
already exist:

- if neither exists, proceed;
- if a failed disposable attempt exists for the same run ID before any
  `matched_outcomes.csv` is produced, preserve it with a suffix such as
  `.failed-<timestamp>` and start a new run ID;
- if any `matched_outcomes.csv`, provenance, inspection output, checksum
  manifest, or non-empty artifact tree exists for the intended run ID, stop
  and wake Galaxias.

Do not append to an existing production `matched_outcomes.csv`. Do not delete
or overwrite prior production artifacts.

## Artifact Policy

Raw production matched outcomes remain remote only.

Remote artifact directory must include, at minimum:

- run script;
- stdout/stderr log;
- run timing;
- storage footprint;
- artifact inventory;
- `checksums.sha256`;
- `outputs/module5_25rep_rehearsal/` or equivalent production output
  directory if the current script name remains reused;
- `matched_outcomes.csv`;
- `provenance.json`;
- `rehearsal_plan.json` or production plan equivalent;
- `artifact_verification.csv`;
- `inspection/inspection_summary.json`;
- `inspection/inspection_checks.csv`;
- `inspection/inspection_report.md`.

The script and report names may continue to use the existing rehearsal runner
if the CLI supports `--replicates 100`. In all reporting language, call this
Goal 014 run a 100-replicate production execution, not a causal interpretation.

Local tracked output should be compact:

- create `docs/module5_100rep_production_execution_report.md`;
- update this goal `Log.md`;
- do not copy raw `matched_outcomes.csv` into the local repo;
- do not stage ignored generated outputs.

## Scope

In scope:

- Remote preflight.
- Fresh pinned source checkout on `deep-server`.
- Verifying the checkout commit.
- Verifying all 15 required Module 4 parameter artifacts by size and SHA-256.
- Running the 100-replicate execution in durable `tmux`.
- Running disk inspection.
- Creating a compact local execution report.
- Updating this Goal 014 `Log.md`.
- Committing and pushing the compact Goal 014 report/log if and only if all
  checks pass and the staged set is exactly the Goal 014 tracked docs.

Allowed local tracked edits:

- `docs/goals/014-module5-100rep-production-execution/Log.md`
- `docs/module5_100rep_production_execution_report.md`

Allowed local Git actions:

- commit and push exactly the Goal 014 packet plus compact report/log after
  successful execution and inspection.

Out of scope:

- No code changes unless the production run cannot be launched from the frozen
  SHA. If code change appears necessary, stop and wake Galaxias.
- No changes to scientific contracts, intervention rows, pressure-removal
  semantics, proposal selection, family weighting, diagnostic ordering, or
  replicate count.
- No production attribution interpretation or final causal effect estimate.
- No manuscript, abstract, figure, supplement, or publication claim language.
- No raw matched-outcome promotion into tracked files.
- No PR creation.
- No force-push, amend, rebase, reset, or destructive cleanup.
- Do not read `/Users/bwbrook/chief_of_staff` or
  `/Users/bwbrook/work/goal_composer`.

## Required Validation And Evidence

Before remote launch:

- `git status --short --branch` locally;
- `git rev-parse HEAD` locally;
- `git rev-list --left-right --count HEAD...origin/main` locally;
- remote host/user/`/data` free space;
- remote `git`, `uv`, `python3`, and `tmux` versions;
- remote checkout commit exactly
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`;
- remote plan-only check with `--replicates 100` confirming 279,500 expected
  rows, 2,795 units, 780 source keys, 15 contexts, and 15 verified artifacts.

During execution:

- exact tmux session name;
- exact command;
- start/end UTC timestamps;
- exit codes;
- duration;
- worker count;
- log path.

Inspection must prove:

- all checks passed;
- row count: 279,500;
- column count: 53 unless the schema changed in a separately authorized
  pre-run goal;
- expected replicates: 100;
- source/intervention units: 2,795;
- distinct `proposal_source_key` values: 780;
- partition row counts match the table above;
- source identity true;
- replicate coverage true;
- matched-pair IDs true;
- schema columns true;
- seed mismatches: 0;
- status is either `module5_25rep_rehearsal` from the existing runner or a
  production-execution status if already supported by the frozen code;
- `production_attribution=false`.

After inspection:

- create checksum manifest and verify it;
- record raw `matched_outcomes.csv` size and SHA-256;
- create compact local report;
- run `git diff --check`;
- run trailing-whitespace scan over the Goal 014 packet/report;
- run marker scan over Goal 014 docs;
- stage exact Goal 014 docs only;
- commit and push the compact execution record only if all gates pass.

## Stop Points

Stop and wake Galaxias before:

- changing code;
- using any commit other than
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`;
- changing worker count from 32;
- changing replicate count from 100;
- using fallback remote target;
- overwriting or deleting existing production artifacts;
- proceeding after any preflight, execution, checksum, or inspection failure;
- making production attribution interpretation or causal/manuscript claims;
- staging anything beyond Goal 014 docs/report/log.

## Completion Condition

Goal 014 is complete when:

- the full 100-replicate production execution has run on `deep-server`;
- disk inspection passes all required checks;
- remote artifacts are inventoried and checksummed;
- compact local Goal 014 report/log are committed and pushed;
- raw production outputs remain remote-only;
- no interpretation or manuscript claim is made;
- `pedder` sends a wake-up to Galaxias and waits.
