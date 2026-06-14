# Log

## 2026-06-13 - Packet Created By Galaxias

Barry approved proceeding with a careful progressive Goal 012 after accepting
Goal 011 source-context identity.

Galaxias preflight facts from the local action repo:

- repo: `/Users/bwbrook/papers/galaxias`
- branch: `main`
- HEAD: `7f77fc4b43e6071d492d51ed40a425cd395bb22a`
- status: accepted uncommitted Goal 005/006/007/008/009/010/011 surface on
  `main...origin/main`
- accepted-frontier rows:
  - `persistent_joint_cause`: 265
  - `climbing_only`: 235
  - `transient_perfect_storm`: 250
  - total: 750
- `family_winners` rows:
  - 15 rows per family across all five families
  - Goal 012 uses only `habitat_only_null` and `trout_only` winners for
    negative-reference diagnostics
- accepted/winner source contexts: 15
- required `parameter_values` manifest rows: 15
- missing parameter contexts from manifest: 0
- 25-replicate rehearsal expected total: 69,875 matched-outcome rows
- 100-replicate production expected total remains 279,500 rows and is not
  authorized by this goal

Delegation boundary:

- `pedder` may implement and run the 25-replicate rehearsal under this packet.
- Raw rehearsal artifacts should remain remote under the Goal 012 artifact
  path unless compact summaries are needed for the tracked report.
- No production attribution, manuscript claims, staging, commit, push, PR, or
  publication are authorized.

Awaiting action-agent execution.

## 2026-06-13 - Action-Agent Execution

### Starting Guard

Recorded starting state before edits or remote commands:

- `pwd`: `/Users/bwbrook/papers/galaxias`
- branch: `main`
- HEAD: `7f77fc4b43e6`
- status: matched the expected accepted Goal 005/006/007/008/009/010/011
  dirty surface plus this Goal 012 packet; no unrelated dirty state was found.

Read-first surface was completed from repo-local files only, including
`AGENTS.md`, Goal 012 `Goal.md`/`Plan.md`/`Runbook.md`/`Log.md`, Module 5
production/source-identity docs, the Module 4 membership/manifest CSVs, Module
5 intervention/schema CSVs, existing Module 5 code, scripts, and tests. Chief
of Staff, Goal Composer, and Nectar files were not read.

### Source-Selection And Artifact Guard

Structured local count check matched the packet invariants:

- accepted rows: 750
- accepted by family:
  - `persistent_joint_cause`: 265
  - `climbing_only`: 235
  - `transient_perfect_storm`: 250
- family winners: 15 rows per family across all five families
- Goal 012 negative-reference winners used:
  - `habitat_only_null`: 15
  - `trout_only`: 15
- source contexts: 15
- missing parameter contexts from manifest: 0
- 25-replicate expected rehearsal rows: 69,875

The local plan-only preflight wrote ignored files under
`outputs/module5_25rep_rehearsal_goal012_local_preflight/` and verified all 15
required local `parameter_values.csv.gz` artifacts.

### RED-First And Implementation

RED-first command:

```bash
uv run pytest tests/test_module5_production_rehearsal.py -q
```

Initial result: failed as expected with
`ModuleNotFoundError: No module named 'galaxias_model.module5_rehearsal'`.

Implemented a narrow Goal 012 surface:

- `src/galaxias_model/module5_rehearsal.py`
  - rehearsal partition/source selection;
  - artifact resolution and size/SHA-256 verification;
  - source-key-aware execution;
  - optional worker parallelism;
  - disk-first inspection.
- `scripts/run_module5_25rep_rehearsal.py`
  - plan-only and full rehearsal runner.
- `scripts/inspect_module5_25rep_rehearsal.py`
  - disk inspector runner.
- `tests/test_module5_production_rehearsal.py`
  - selection arithmetic, collision resistance, artifact verification, and
    malformed-output checks.
- `src/galaxias_model/module5_counterfactual.py`
  - uncertainty summaries now group by `proposal_source_key` plus
    `intervention_id` when source keys are present, preserving the existing
    smoke/dry-run path while keeping rehearsal summaries source-local.

No tracked intervention-matrix rows, pressure-removal semantics, proposal
sampling, family weighting, diagnostic ordering, or scenario hooks were
changed by this goal.

### Local Validation

Final local validation commands and outcomes:

```bash
uv run pytest tests/test_module5_production_rehearsal.py -q
```

Result: 5 passed.

```bash
uv run pytest tests/test_module5_source_identity.py tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q
```

Result: 17 passed.

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
```

Result: `Module 5 counterfactual contract validation passed.`

```bash
make module5-dry-run
```

Result: passed; regenerated ignored
`outputs/module5_dry_run_baseline_current_20260410/`.

```bash
make module5-dry-run-inspect
```

Result: passed; Module 5 real-proposal dry-run inspection passed.

```bash
make fast-check
```

Result: passed; portability checked 232 git-managed files, compileall passed,
and pytest reported 88 passed, 5 deselected.

```bash
git diff --check
```

Result: passed.

```bash
rg -n "[ \t]+$" docs/goals/012-module5-25rep-production-rehearsal docs/module5_25rep_rehearsal_report.md src/galaxias_model/module5_rehearsal.py src/galaxias_model/module5_counterfactual.py scripts/run_module5_25rep_rehearsal.py scripts/inspect_module5_25rep_rehearsal.py tests/test_module5_production_rehearsal.py
```

Result: no matches.

Marker scan over the Goal 012 packet, the new report, and accepted Module 5
production/source-identity docs returned only expected boundary, remote-path,
`tmux`, ignored-output, and stop-point language.

### Remote Preflight

Remote alias used: `deep-server-ts`; `utas-ubuntu` fallback was not needed.

Remote facts:

- host: `deep-server`
- user: `bwbrook`
- `/data`: 13T total, 4.5T available at preflight
- `uv`: `/home/bwbrook/.local/bin/uv 0.11.14`
- system Python: 3.12.3
- `uv` rehearsal environment: CPython 3.14.5
- `tmux`: 3.4

The first non-login probe did not find `uv` on PATH. The run script exported
`$HOME/.local/bin` before using `uv`, and preflight then passed.

Successful run paths:

- run ID: `20260613T115519Z-goal012-m5-25rep-rehearsal`
- tmux session: `galaxias-m5-25rep-20260613T115519Z`
- source mirror:
  `/data/codex/repos/galaxias-goal012-m5-25rep-rehearsal-20260613T115519Z-goal012-m5-25rep-rehearsal`
- scratch:
  `/data/codex/scratch/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal`
- artifact:
  `/data/codex/artifacts/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal`

Remote artifact verification:

- required `parameter_values` rows: 15
- source: existing `remote_artifact_path`
- total verified bytes: 57,941,680
- size checks: all passed
- SHA-256 checks: all passed

### Remote Execution And Inspection

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

Execution facts:

- start UTC: 2026-06-13T11:56:42Z
- end UTC: 2026-06-13T12:00:21Z
- duration: 219 seconds
- rehearsal exit: 0
- tmux command exit: 0
- workers: 32
- remote artifact footprint: 104M
- source mirror footprint: 329M
- scratch footprint: 104M

Inspection facts:

- all checks passed: true
- matched rows: 69,875
- columns: 53
- expected replicates: 25
- replicate IDs: `0..24`
- source/intervention units: 2,795
- distinct `proposal_source_key` values: 780
- partition row counts:
  - `headline/persistent_joint_cause`: 26,500
  - `headline/climbing_only`: 11,750
  - `headline/transient_perfect_storm`: 25,000
  - `diagnostic_sidecar/climbing_only_no_trout_pressure`: 5,875
  - `negative_reference/habitat_only_null`: 375
  - `negative_reference/trout_only`: 375
- source identity: true
- replicate coverage: true
- matched-pair IDs: true
- schema columns: true
- seed mismatches: 0
- status: `module5_25rep_rehearsal`
- `production_attribution`: false

Remote raw matched outcomes:

- path:
  `/data/codex/artifacts/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal/outputs/module5_25rep_rehearsal/matched_outcomes.csv`
- size: 108,604,509 bytes
- SHA-256:
  `d6f0e74e73cced8047776b2d40e494482b2b10c1349e5620c54ea872aaf614b0`
- not copied into the local repo

Compact remote summaries and checksums remain under the successful artifact
path. Local tracked report:
`docs/module5_25rep_rehearsal_report.md`.

### Deviation

An initial serial tmux attempt,
`20260613T113751Z-goal012-m5-25rep-rehearsal`, completed neither rehearsal nor
inspection within a reasonable smoke window and was stopped before producing
`matched_outcomes.csv`. Its artifact path is preserved for audit:

`/data/codex/artifacts/galaxias/module5_25rep_rehearsal_20260613T113751Z-goal012-m5-25rep-rehearsal`

That path contains only the run script, log, and `tmux_command.exit=143`; it
has no `rehearsal.exit` and no raw matched outcomes.

### Final Files And Status

Goal 012 local changed files:

- `docs/goals/012-module5-25rep-production-rehearsal/Log.md`
- `docs/module5_25rep_rehearsal_report.md`
- `scripts/run_module5_25rep_rehearsal.py`
- `scripts/inspect_module5_25rep_rehearsal.py`
- `src/galaxias_model/module5_rehearsal.py`
- `src/galaxias_model/module5_counterfactual.py`
- `tests/test_module5_production_rehearsal.py`

Ignored local outputs:

- `outputs/module5_25rep_rehearsal_goal012_local_preflight/`
- `outputs/module5_dry_run_baseline_current_20260410/`

Final branch/status after validation:

- branch: `main`
- HEAD: `7f77fc4b43e6`
- `git status --short --branch`: accepted pre-existing Goal 005-011 dirty
  surface plus Goal 012 packet/report/implementation files; no staging,
  commit, push, or PR was performed.

### Risks, Questions, And Next Goal Shape

Residual risks:

- The 25-replicate rehearsal passed execution and inspection, but it is still
  a rehearsal and should not be interpreted as production attribution.
- The successful run used a 32-worker implementation change introduced after
  the serial attempt proved too slow. The local tests and remote inspection
  passed with that surface.
- Raw matched outcomes remain only on `deep-server` under the successful
  artifact path.

Recommended next-goal shape:

- authorize a final pre-production review of the Goal 012 implementation and
  report;
- if accepted, authorize the 100-replicate Module 5 execution as a separate
  goal with explicit run ID, worker count, restart/resume policy, artifact
  retention policy, inspection gate, and post-run interpretation boundary.

Wake-up to Galaxias orchestrator thread
`019eaac3-85f6-7853-bc28-a4d905dadfc3` sent after final status capture.
