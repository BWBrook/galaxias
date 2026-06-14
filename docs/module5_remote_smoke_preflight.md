# Module 5 Remote Smoke Preflight

## Current State And Non-Claims

Goal 010 ran a bounded Module 5 remote smoke on `deep-server`. The smoke used
the accepted dirty local action-repo surface from Goals 005-010, mirrored to a
disposable remote source directory. It was a preflight and remote execution
proof only.

This report does not authorise the 25-replicate rehearsal, the 279,500-row
production execution, production attribution claims, manuscript claims,
publication, staging, commit, push, or a PR. Raw matched outcomes were not
copied back into the local repo.

## Local Starting State

- Local repo: `/Users/bwbrook/papers/galaxias`
- Branch: `main`
- HEAD: `7f77fc4b43e6`
- Starting dirty state: matched the expected accepted Goal 005/006/007/008/009
  surface plus the Goal 010 packet.
- Local source policy: mirror the accepted dirty local source surface rather
  than cloning stale `origin/main`.

## Remote Target And Environment

- Remote alias used: `deep-server-ts`
- Fallback alias: not used
- Remote host: `deep-server`
- Remote user: `bwbrook`
- Kernel: `Linux deep-server 6.8.0-124-generic`
- `/data` capacity at probe: 13T total, 8.1T used, 4.5T available, 65% used
- `uv`: `/home/bwbrook/.local/bin/uv`, version `0.11.14`
- System `python3`: `3.12.3`
- Smoke environment: `uv` downloaded and used CPython `3.14.5`
- `tmux`: `3.4`

## Run Identifiers And Remote Paths

- Run stamp: `20260613T095744Z`
- Run ID: `20260613T095744Z-goal010-m5-remote-smoke`
- `tmux` session: `galaxias-m5-smoke-20260613T095744Z`
- Remote source mirror:
  `/data/codex/repos/galaxias-goal010-remote-smoke-20260613T095744Z-goal010-m5-remote-smoke`
- Remote scratch:
  `/data/codex/scratch/galaxias/module5_remote_smoke_20260613T095744Z-goal010-m5-remote-smoke`
- Remote artifact:
  `/data/codex/artifacts/galaxias/module5_remote_smoke_20260613T095744Z-goal010-m5-remote-smoke`
- Smoke output directory:
  `/data/codex/scratch/galaxias/module5_remote_smoke_20260613T095744Z-goal010-m5-remote-smoke/outputs/module5_remote_smoke_goal010`
- Artifact copy of smoke output:
  `/data/codex/artifacts/galaxias/module5_remote_smoke_20260613T095744Z-goal010-m5-remote-smoke/outputs/module5_remote_smoke_goal010`

## Source Mirror Evidence

The source mirror was created with `rsync`, including `.git`, excluding
`.venv/`, `.pytest_cache/`, `__pycache__/`, and `outputs/`. The one required
ignored smoke artifact was copied separately into its expected repo-relative
path.

Remote source state:

- Remote HEAD: `7f77fc4b43e6071d492d51ed40a425cd395bb22a`
- Remote status: matched the accepted dirty Goal 005/006/007/008/009 surface
  plus the Goal 010 packet.
- Remote source footprint after `uv` environment creation: `332M`

## Smoke Input Artifact

Required artifact:

```text
outputs/remote/module4_observation_sensitivity_20260522T101942Z/baseline_current_seed20260410/parameter_values.csv.gz
```

Evidence:

- Local size from `ls -lh`: `3.7M`
- Manifest byte count: `3862605`
- Local SHA-256:
  `49e080a23dcaca2f29874c0e3825bd806406f494b2db046307a84a74e8673c4c`
- Remote SHA-256:
  `49e080a23dcaca2f29874c0e3825bd806406f494b2db046307a84a74e8673c4c`
- Selected proposal parameter coverage: 200 rows, 40 rows for each of the
  five Goal 006 proposal IDs.

## Smoke Shape

- Proposal source: five `baseline_current` / `20260410` `family_winners`
  proposal rows from Goal 006
- Intervention matrix: all 13 current Module 5 intervention rows
- Replicates: 5 per intervention row
- Expected matched-outcome rows: 65
- Production attribution flag expected: `false`

Selected proposal IDs:

- `persistent_joint_cause:p00162`
- `climbing_only:p00216`
- `transient_perfect_storm:p00144`
- `habitat_only_null:p00761`
- `trout_only:p00814`

## Commands And Session Evidence

Remote script:

```text
/data/codex/artifacts/galaxias/module5_remote_smoke_20260613T095744Z-goal010-m5-remote-smoke/run_module5_remote_smoke.sh
```

The script ran inside `tmux` session
`galaxias-m5-smoke-20260613T095744Z` and wrote:

- `smoke.exit`: `0`
- `tmux_command.exit`: `0`
- log:
  `/data/codex/artifacts/galaxias/module5_remote_smoke_20260613T095744Z-goal010-m5-remote-smoke/logs/smoke.log`

Runner command shape:

```bash
uv run python scripts/run_module5_real_proposal_dry_run.py \
  --output-dir "$REMOTE_SCRATCH/outputs/module5_remote_smoke_goal010" \
  --replicates 5
```

Inspector command shape:

```bash
uv run python scripts/inspect_module5_real_proposal_dry_run.py \
  --dry-run-dir "$REMOTE_SCRATCH/outputs/module5_remote_smoke_goal010" \
  --inspection-dir "$REMOTE_SCRATCH/outputs/module5_remote_smoke_goal010/inspection" \
  --expected-replicates 5
```

## Smoke And Inspection Outcomes

The remote smoke passed.

| fact | value |
| --- | ---: |
| matched-outcome rows | 65 |
| columns | 50 |
| proposal count | 5 |
| intervention count | 13 |
| expected replicates | 5 |
| matched-pair count | 65 |
| seed mismatches | 0 |
| bad replicate sets | 0 |
| inspection `all_checks_passed` | true |
| inspection `replicate_coverage` | true |
| provenance `production_attribution` | false |

Every intervention row had exactly 5 rows. The replicate ID set for every
intervention was exactly `0..4`. The disk inspector passed all checks:
schema columns, row count, proposal IDs, intervention IDs, replicate coverage,
matched-pair IDs, common-random-seed pairing, provenance labels, and dry-run
boundary language.

## Remote Artifact Inventory

Key remote files:

- `logs/smoke.log`
- `run_module5_remote_smoke.sh`
- `smoke.exit`
- `tmux_command.exit`
- `smoke_summary.json`
- `run_timing.json`
- `storage_footprint.txt`
- `checksums.sha256`
- `outputs/module5_remote_smoke_goal010/matched_outcomes.csv`
- `outputs/module5_remote_smoke_goal010/provenance.json`
- `outputs/module5_remote_smoke_goal010/inspection/inspection_summary.json`
- `outputs/module5_remote_smoke_goal010/inspection/inspection_checks.csv`
- `outputs/module5_remote_smoke_goal010/inspection/inspection_report.md`

Important checksums:

| artifact | SHA-256 |
| --- | --- |
| `matched_outcomes.csv` | `f8e230d0fc7ecc598fb14f77ba7bb822ca94da286c55d69ae2e8c5088f8b1127` |
| `provenance.json` | `c90ef769ccb1b955efbd303e2e7f9d58cb1d353aa5566a172898e39ad209d67a` |
| `inspection_summary.json` | `708ac8790bedb611d6888dc5c754347afe03fb0c5e208f9d527743a61f1805bc` |
| `inspection_checks.csv` | `0d897c1becdef59208e2e88ffee00c514b93b9d8460ca098caee84a4d3bb5c7b` |
| `smoke_summary.json` | `1d9ff3e24df2c5f5522558275dc75ca2d55b72c77df7f8d8e6533252e3db39ee` |

The full checksum manifest remains on `deep-server` at:

```text
/data/codex/artifacts/galaxias/module5_remote_smoke_20260613T095744Z-goal010-m5-remote-smoke/checksums.sha256
```

## Timing And Storage

- Smoke script start: `2026-06-13T10:00:49Z`
- Smoke script end: `2026-06-13T10:01:01Z`
- Script duration: 12 seconds
- Remote source mirror footprint after environment creation: `332M`
- Remote artifact footprint: `140K`
- Remote scratch footprint: `92K`

The log records that `uv` downloaded CPython `3.14.5` and created the remote
`.venv`, then installed 36 packages. `uv` warned that hardlinking was not
available and fell back to full copy; this is a performance warning only for
this smoke.

## Deviations Or Warnings

- The first local remote-probe attempt failed before SSH execution because of
  local shell quoting. It was corrected with a here-doc; the actual
  `deep-server-ts` probe succeeded. No fallback alias was used.
- The remote runner provenance still labels the status
  `real_proposal_local_dry_run`, because that is the existing runner label.
  The remote paths, host, report, and Goal 010 log distinguish this as a
  remote smoke/preflight. No code was changed to relabel it.
- The remote `tmux` session remains available for audit after successful
  completion.

## Recommendation

Goal 010 satisfies the remote-smoke gate for the current 13-row Module 5
matrix and the five Goal 006 real-proposal smoke rows. The next goal can be a
production-execution authorization packet if Galaxias and Barry accept the
remaining production decisions from Goal 009:

- 100 replicates versus a 25-replicate rehearsal;
- whether diagnostics run in the same session as headline partitions;
- exact production run ID and partition layout;
- final pull-back policy for compact summaries;
- implementation work needed to use proposal-row source identity for the
  750-row accepted-frontier production source.

The important implementation risk remains the Goal 009 identity issue:
production must not key seeds or matched-pair IDs by bare `proposal_id`, since
the accepted-frontier table repeats proposal IDs across variant/seed source
rows. Production code should use a source-context proposal-row key before the
279,500-row run is authorized.
