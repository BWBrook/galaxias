# Module 5 25-Replicate Rehearsal Report

## Objective And Boundary

Goal 012 implemented, validated, and executed a source-key-aware 25-replicate
Module 5 rehearsal on `deep-server`. The run used the accepted-frontier source
rows, diagnostic sidecar, negative-reference rows, Goal 011
`proposal_source_key` identity contract, and verified Module 4 parameter
artifacts.

This report is a compact execution and inspection record only. It is not a
100-replicate production run, not production attribution, not a final causal
effect estimate, and not manuscript evidence.

## Local Implementation

Goal 012 added a focused rehearsal surface:

- `src/galaxias_model/module5_rehearsal.py`
  - source selection and partition planning;
  - required `parameter_values` artifact resolution and size/SHA-256
    verification;
  - source-key-aware execution with optional worker parallelism;
  - disk-first rehearsal inspection.
- `scripts/run_module5_25rep_rehearsal.py`
  - plan-only preflight and full rehearsal CLI.
- `scripts/inspect_module5_25rep_rehearsal.py`
  - disk inspection CLI for rehearsal outputs.
- `tests/test_module5_production_rehearsal.py`
  - focused tests for selection arithmetic, source-key collision resistance,
    artifact verification, and malformed replicate/identity inspection
    failures.

The shared Module 5 matched-output helper now attaches uncertainty summaries by
`proposal_source_key` and `intervention_id` when source keys are present. This
keeps rehearsal summaries source-local while preserving the existing smoke and
dry-run paths.

## Source And Partition Shape

The local count guard matched the packet invariants.

| selection | source rows | intervention rows | replicates | rows |
| --- | ---: | ---: | ---: | ---: |
| `headline/persistent_joint_cause` | 265 | 4 | 25 | 26,500 |
| `headline/climbing_only` | 235 | 2 | 25 | 11,750 |
| `headline/transient_perfect_storm` | 250 | 4 | 25 | 25,000 |
| `diagnostic_sidecar/climbing_only_no_trout_pressure` | 235 | 1 | 25 | 5,875 |
| `negative_reference/habitat_only_null` | 15 | 1 | 25 | 375 |
| `negative_reference/trout_only` | 15 | 1 | 25 | 375 |
| total | 780 distinct source keys | 2,795 source/intervention units | 25 | 69,875 |

Additional guard facts:

- accepted-frontier rows: 750 total;
- accepted families: 265 `persistent_joint_cause`, 235 `climbing_only`,
  250 `transient_perfect_storm`;
- negative-reference rows: 15 `habitat_only_null` family winners and
  15 `trout_only` family winners;
- source contexts: 15;
- required `parameter_values` manifest rows: 15;
- missing parameter contexts: 0.

## Local Validation

Pre-remote validation evidence:

- `uv run pytest tests/test_module5_production_rehearsal.py -q`
  - 5 passed after RED-first failure on the missing rehearsal module.
- `uv run pytest tests/test_module5_source_identity.py tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q`
  - 17 passed.
- `uv run python scripts/run_module5_25rep_rehearsal.py --plan-only --output-dir outputs/module5_25rep_rehearsal_goal012_local_preflight --run-id local-goal012-preflight`
  - wrote ignored local plan and artifact verification;
  - expected rows: 69,875;
  - source/intervention units: 2,795;
  - distinct `proposal_source_key` values: 780;
  - artifact count: 15;
  - local artifact verification: all passed.
- `uv run python scripts/validate_module5_counterfactual_contract.py`
  - passed.
- `make module5-dry-run`
  - passed, leaving ignored dry-run outputs under
    `outputs/module5_dry_run_baseline_current_20260410/`.
- `make module5-dry-run-inspect`
  - passed.
- `make fast-check`
  - passed: portability, compile, and tests; pytest reported 88 passed and
    5 deselected.
- `git diff --check`
  - passed.

## Remote Run

Remote target:

- alias: `deep-server-ts`;
- host: `deep-server`;
- user: `bwbrook`;
- `/data`: 13T total, 4.5T available at preflight;
- `uv`: `/home/bwbrook/.local/bin/uv 0.11.14`;
- system Python: 3.12.3;
- `uv` rehearsal environment: CPython 3.14.5;
- `tmux`: 3.4.

Successful run identity:

- run ID: `20260613T115519Z-goal012-m5-25rep-rehearsal`;
- tmux session: `galaxias-m5-25rep-20260613T115519Z`;
- source mirror:
  `/data/codex/repos/galaxias-goal012-m5-25rep-rehearsal-20260613T115519Z-goal012-m5-25rep-rehearsal`;
- scratch:
  `/data/codex/scratch/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal`;
- artifact:
  `/data/codex/artifacts/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal`.

Primary remote command:

```bash
uv run python scripts/run_module5_25rep_rehearsal.py \
  --output-dir /data/codex/scratch/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal/outputs/module5_25rep_rehearsal \
  --run-id 20260613T115519Z-goal012-m5-25rep-rehearsal \
  --replicates 25 \
  --workers 32
```

Inspection command:

```bash
uv run python scripts/inspect_module5_25rep_rehearsal.py \
  --rehearsal-dir /data/codex/scratch/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal/outputs/module5_25rep_rehearsal \
  --inspection-dir /data/codex/scratch/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal/outputs/module5_25rep_rehearsal/inspection
```

Execution outcome:

- start UTC: 2026-06-13T11:56:42Z;
- end UTC: 2026-06-13T12:00:21Z;
- duration: 219 seconds;
- rehearsal exit: 0;
- tmux command exit: 0;
- workers: 32;
- remote artifact footprint: 104M;
- source mirror footprint: 329M;
- scratch footprint after run: 104M.

## Artifact Verification

The successful rehearsal verified all 15 required Module 4
`parameter_values.csv.gz` artifacts from existing `remote_artifact_path`
locations before execution.

- verification rows: 15;
- verification source: `remote_artifact_path`;
- total verified bytes: 57,941,680;
- size checks: all passed;
- SHA-256 checks: all passed.

## Remote Inspection

The disk inspection passed.

| check | result |
| --- | --- |
| all checks passed | true |
| matched rows | 69,875 |
| columns | 53 |
| expected replicates | 25 |
| replicate IDs | `0..24` |
| source/intervention units | 2,795 |
| distinct `proposal_source_key` values | 780 |
| partition counts | matched expected counts |
| source identity | true |
| replicate coverage | true |
| matched-pair IDs | true |
| common-random seed mismatches | 0 |
| schema columns | true |
| status | `module5_25rep_rehearsal` |
| `production_attribution` | false |

Remote raw matched outcomes:

- path:
  `/data/codex/artifacts/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal/outputs/module5_25rep_rehearsal/matched_outcomes.csv`;
- size: 108,604,509 bytes;
- SHA-256:
  `d6f0e74e73cced8047776b2d40e494482b2b10c1349e5620c54ea872aaf614b0`;
- not copied into the local repo.

Compact remote artifacts:

- `rehearsal_summary.json`: 918 bytes;
- `inspection/inspection_summary.json`: 1,594 bytes;
- `inspection/inspection_checks.csv`: 1,418 bytes;
- `inspection/inspection_report.md`: 1,992 bytes;
- `artifact_verification.csv`: 6,445 bytes;
- `provenance.json`: 147,087 bytes;
- `rehearsal_plan.json`: 12,297 bytes;
- `checksums.sha256`: 1,251 bytes.

## Deviations And Risks

Observed deviations:

- The first remote probe found `uv` absent from the non-login PATH. The run
  script used `/home/bwbrook/.local/bin` explicitly, and preflight then
  confirmed `uv 0.11.14`.
- An initial serial tmux attempt,
  `20260613T113751Z-goal012-m5-25rep-rehearsal`, was stopped after proving too
  slow for the rehearsal scale. It produced only a script, log, and
  `tmux_command.exit=143`; it did not produce `matched_outcomes.csv` or an
  inspection artifact. The preserved path is
  `/data/codex/artifacts/galaxias/module5_25rep_rehearsal_20260613T113751Z-goal012-m5-25rep-rehearsal`.
- The successful run used the same contract with 32 workers and completed in
  219 seconds.

Residual risks and stop points:

- This rehearsal proves the 25-replicate execution/inspection shape; it does
  not authorize or replace the 100-replicate execution gate.
- Raw matched outcomes remain remote and ignored from local tracked files.
- No production attribution interpretation should be made from this rehearsal.
- The next goal should explicitly authorize any 100-replicate execution,
  final artifact policy, restart behavior, and post-run interpretation gates.
