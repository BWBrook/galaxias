# Goal: Module 5 25-Replicate Production Rehearsal

## Objective

Implement, validate, and execute a source-key-aware 25-replicate Module 5
production rehearsal on `deep-server`.

This goal should exercise the full accepted-frontier production selection,
diagnostic sidecars, source-artifact resolution, partition accounting,
restart/inspection identity checks, and remote artifact layout at one quarter
of the currently recommended production replicate count.

The goal stops before the 100-replicate production run, production attribution
interpretation, manuscript claims, staging, commit, push, PR, or publication.

## Why This Matters

Goals 009-011 left the project in a good pre-production posture:

- Goal 009 specified the recommended production design and row counts.
- Goal 010 proved that a tiny Module 5 remote smoke can run on `deep-server`
  through a durable `tmux` session.
- Goal 011 fixed the key identity hazard by making proposal source context
  explicit in seeds, matched-pair IDs, run IDs, outcome rows, provenance, and
  inspection.

The next progressive step is not yet the 279,500-row 100-replicate execution.
It is a 69,875-row rehearsal that uses the same source rows and intervention
layout while proving the production runner can resolve all required Module 4
parameter artifacts and preserve source identity across the whole run shape.

## Authorized Run Shape

Use 25 stochastic replicates per proposal-row/intervention-row unit.

Source tables:

- accepted-frontier source rows:
  `data/module4_5_proposal_set_membership.csv` where `in_accepted == true`
  for `persistent_joint_cause`, `climbing_only`, and
  `transient_perfect_storm`;
- negative-reference diagnostic rows:
  `data/module4_5_proposal_set_membership.csv` where
  `in_family_winners == true` for `habitat_only_null` and `trout_only`;
- Module 4 parameter artifacts resolved through
  `data/module4_raw_artifact_manifest.csv`.

Expected selection facts from Galaxias preflight:

| selection | source rows | intervention rows | replicate count | expected rows |
| --- | ---: | ---: | ---: | ---: |
| `persistent_joint_cause` headline | 265 | 4 | 25 | 26,500 |
| `climbing_only` headline | 235 | 2 | 25 | 11,750 |
| `transient_perfect_storm` headline | 250 | 4 | 25 | 25,000 |
| `climbing_only` diagnostic sidecar | 235 | 1 | 25 | 5,875 |
| `habitat_only_null` negative reference | 15 | 1 | 25 | 375 |
| `trout_only` negative reference | 15 | 1 | 25 | 375 |
| total rehearsal | 780 distinct source rows, with 235 reused for the sidecar | mixed | 25 | 69,875 |

The source rows span 15 Module 4 source contexts:

- five variants:
  `baseline_current`, `ct007_occupancy_primary`,
  `ct009_terminal_window_gap3`, `ct010_detection_half`, and
  `late_bridge_soft`;
- three seeds: `20260410`, `20260411`, and `20260412`;
- 15 required `parameter_values` manifest rows and no missing source contexts
  in `data/module4_raw_artifact_manifest.csv`.

If live repo counts differ, stop and wake Galaxias before implementing or
running the rehearsal.

## Partition Contract

Produce explicit partition labels in provenance, summaries, and inspection.

Required partitions:

- `headline/persistent_joint_cause`
  - source: 265 accepted `persistent_joint_cause` rows
  - interventions:
    - `m5_persistent_joint_cause_status_quo`
    - `m5_persistent_joint_cause_no_trout_pressure`
    - `m5_persistent_joint_cause_no_climbing_pressure`
    - `m5_persistent_joint_cause_no_trout_or_climbing_pressure`
- `headline/climbing_only`
  - source: 235 accepted `climbing_only` rows
  - interventions:
    - `m5_climbing_only_status_quo`
    - `m5_climbing_only_no_climbing_pressure`
- `headline/transient_perfect_storm`
  - source: 250 accepted `transient_perfect_storm` rows
  - interventions:
    - `m5_transient_perfect_storm_status_quo`
    - `m5_transient_perfect_storm_no_trout_pressure`
    - `m5_transient_perfect_storm_no_climbing_pressure`
    - `m5_transient_perfect_storm_no_trout_or_climbing_pressure`
- `diagnostic_sidecar/climbing_only_no_trout_pressure`
  - source: same 235 accepted `climbing_only` rows
  - intervention:
    - `m5_climbing_only_no_trout_pressure`
- `negative_reference/habitat_only_null`
  - source: 15 `habitat_only_null` `family_winners` rows
  - intervention:
    - `m5_habitat_only_null_negative_reference`
- `negative_reference/trout_only`
  - source: 15 `trout_only` `family_winners` rows
  - intervention:
    - `m5_trout_only_negative_reference`

Do not blend family summaries into a single cross-family causal estimate.
Family-level and partition-level summaries are allowed as rehearsal diagnostics
only.

## Source Identity Contract

Use the Goal 011 source identity contract throughout:

```text
proposal_source_key = module4_run_id|variant_id|seed|run_dir_name|family_id|proposal_id
```

Seeds must derive from:

```text
base_label|proposal_source_key|intervention_id|stochastic_replicate_id
```

Matched-pair IDs must use:

```text
<proposal_source_key>|<intervention_id>|r<stochastic_replicate_id>
```

Every rehearsal output row must keep the source identity fields required by
`data/module5_counterfactual_outcome_schema.csv`. Do not use bare
`proposal_id`, DataFrame index, CSV row number, or sort order as the production
unit.

## Remote Execution Contract

Default remote target:

- first: `deep-server-ts`;
- fallback only if needed: `utas-ubuntu`.

Use a durable `tmux` session. Recommended names:

- run ID: `YYYYMMDDTHHMMSSZ-goal012-m5-25rep-rehearsal`;
- tmux session: `galaxias-m5-25rep-YYYYMMDDTHHMMSSZ`;
- source mirror:
  `/data/codex/repos/galaxias-goal012-m5-25rep-rehearsal-<RUN_ID>`;
- scratch:
  `/data/codex/scratch/galaxias/module5_25rep_rehearsal_<RUN_ID>`;
- artifacts:
  `/data/codex/artifacts/galaxias/module5_25rep_rehearsal_<RUN_ID>`.

Because the local action repo has an accepted uncommitted Goal 005-011 surface,
do not rely on a fresh GitHub clone alone. Build the remote source mirror from
the local checkout state with `rsync` or an equivalent file transport,
excluding only bulky/cache paths that are not needed for execution
(`.venv`, caches, previous outputs, and similar).

Required Module 4 parameter artifacts may be made available on the remote
mirror by either:

- verifying existing `remote_artifact_path` files from
  `data/module4_raw_artifact_manifest.csv` on `deep-server` and using them
  directly or through stable links; or
- transferring the required local `local_path` artifacts if a verified remote
  copy is absent.

In either case, verify size and SHA-256 against the manifest before execution.
Stop if any required artifact is missing or hash-mismatched.

## Scope

In scope:

- Add production/rehearsal source-selection, artifact-resolution, runner,
  inspection, and reporting code as needed.
- Add a local tiny validation mode or fixture mode if it helps prove the
  machinery before the remote 25-replicate rehearsal.
- Add focused tests for selection arithmetic, source-context artifact
  resolution, source-key uniqueness, seed/matched-pair uniqueness, partition
  counts, restart/inspection checks, and malformed-output failure modes.
- Update existing Module 5 proposal/counterfactual/inspection code only where
  needed to support the rehearsal cleanly.
- Update `Makefile` or README only if needed for a reproducible rehearsal
  command or operator-facing entry point.
- Create a tracked compact report, recommended path:
  `docs/module5_25rep_rehearsal_report.md`.
- Update this goal `Log.md`.
- Leave raw matched outcomes and other large rehearsal artifacts on the remote
  artifact path unless a compact summary is needed for the tracked report.

Allowed tracked files:

- `Makefile`
- `README.md`
- `scripts/validate_module5_counterfactual_contract.py` only if schema or
  validation wiring requires it
- `scripts/run_module5_real_proposal_dry_run.py` only if shared runner
  extraction or help text requires it
- `scripts/inspect_module5_real_proposal_dry_run.py` only if shared inspector
  extraction or help text requires it
- new `scripts/` files for production rehearsal running, preflight, remote
  command generation, artifact checks, or inspection
- `src/galaxias_model/module5_proposals.py`
- `src/galaxias_model/module5_counterfactual.py`
- `src/galaxias_model/module5_dry_run_inspect.py`
- new `src/galaxias_model/` files for rehearsal selection, artifact
  resolution, partitioning, execution, or inspection
- existing focused Module 5 tests affected by the new runner surface
- new focused tests under `tests/`
- `docs/module5_production_run_spec.md`
- `docs/module5_remote_smoke_preflight.md` only if a factual cross-reference
  is needed
- `docs/module5_source_identity_contract.md` only if a factual cross-reference
  is needed
- `docs/module5_25rep_rehearsal_report.md`
- `docs/goals/012-module5-25rep-production-rehearsal/Log.md`

Out of scope:

- No 100-replicate production run.
- No production attribution interpretation or final causal effect estimate.
- No manuscript, abstract, figure, supplement, or publication claim language.
- No changes to `data/module5_counterfactual_interventions.csv`.
- No changes to pressure-removal semantics or new scenario hooks.
- No changes to proposal sampling, family weighting, diagnostic ordering, or
  replicate count beyond this 25-replicate rehearsal.
- No raw matched-outcome promotion into tracked files.
- No deletion of remote artifacts unless cleaning a failed disposable attempt
  before a successful rerun in the same goal.
- No staging, commit, push, PR, or publication.
- Do not read `/Users/bwbrook/chief_of_staff` or
  `/Users/bwbrook/work/goal_composer`.

## Required Evidence

Record in `Log.md`:

- starting branch, HEAD, and status;
- any pre-work deviations from the expected accepted dirty surface;
- source-selection counts and row arithmetic;
- 15 required parameter artifact contexts and hash-verification evidence;
- remote target, run ID, tmux session, source mirror, scratch path, and
  artifact path;
- RED-first or fail-first test evidence for new rehearsal checks where
  practical;
- local validation commands and outcomes;
- remote preflight environment facts: host, user, `/data` space, `uv`,
  Python, and `tmux`;
- remote command line, start/end timestamps, duration, and exit codes;
- exact rehearsal row counts by partition and total;
- output column count and schema conformance;
- distinct `proposal_source_key` count;
- distinct proposal/intervention unit count;
- replicate coverage for every unit: exactly 25 rows and replicate IDs
  `0..24`;
- seed mismatch count;
- source-identity, matched-pair, and run-ID inspection outcomes;
- artifact inventory, sizes, and checksums;
- compact tracked-report path;
- generated ignored local output paths, if any;
- final status and changed files;
- deviations, risks, and recommended next-goal shape.

## Completion Condition

Goal 012 is complete when:

- the source-key-aware 25-replicate rehearsal has run successfully on
  `deep-server` or the approved fallback;
- inspection proves the 69,875-row run has exact partition counts, source
  identity, seed pairing, and replicate coverage;
- a compact tracked report and `Log.md` capture the evidence;
- raw remote artifacts are inventoried and checksummed but not promoted into
  tracked files;
- no production attribution, manuscript claims, staging, commit, push, or PR
  occurred;
- `pedder` sends a short wake-up to Galaxias on completion or blockage and
  then waits.
