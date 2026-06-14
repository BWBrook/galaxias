# Module 5 Production Run Specification

## Current State And Non-Claims

Goals 005-011 moved Module 5 from a readiness gate to a real-proposal local
dry run and then to an approved 13-row production-planning intervention
matrix. Goal 006 showed that local pressure-removal hooks exist for
`no_trout_pressure`, `no_climbing_pressure`, and
`no_trout_or_climbing_pressure`, and that a small real-proposal dry run can be
written and inspected from disk. Goal 008 revised the tracked intervention
contract to the 13-row matrix needed for production planning. Goal 011
implemented the source-context proposal identity contract now recorded in
`docs/module5_source_identity_contract.md`.

This specification recommends the next production-run shape. It does not
authorise production execution, remote probes, remote setup, `tmux` session
creation, generated-output changes, production attribution claims, manuscript
claims, staging, commit, push, or publication.

The current scientific claim boundary remains the Module 4.5 boundary:
`persistent_joint_cause` is the primary Module 5 family, `climbing_only` and
`transient_perfect_storm` are sensitivity families, and
`habitat_only_null` plus `trout_only` are negative references. Module 5
production output, after review, can support matched counterfactual summaries
conditioned on that framework. It cannot by itself be treated as final causal
proof or manuscript-ready attribution language.

## Production Input Contracts Reviewed

The production source table is
`data/module4_5_proposal_set_membership.csv`. It contains 750 accepted
proposal rows for the accepted-frontier families:

| family_id | module5_role | accepted proposal rows |
| --- | --- | ---: |
| `persistent_joint_cause` | primary | 265 |
| `climbing_only` | sensitivity | 235 |
| `transient_perfect_storm` | sensitivity | 250 |

The accepted rows span five observation-bridge variants and three seeds:
`baseline_current`, `ct007_occupancy_primary`,
`ct009_terminal_window_gap3`, `ct010_detection_half`, and
`late_bridge_soft` crossed with seeds `20260410`, `20260411`, and
`20260412`. Every accepted proposal row reports `min_replicate_count = 20`.

The production unit should be a proposal membership row, not a bare
`proposal_id`. In the tracked membership table, the 750 accepted rows contain
246 unique `proposal_id` strings. Module 5 now uses the source-context
`proposal_source_key` shape
`module4_run_id|variant_id|seed|run_dir_name|family_id|proposal_id` for seed
derivation, matched-pair IDs, run IDs, provenance, and disk inspection.

Available proposal sets are:

| proposal set | rows by family | recommended use |
| --- | --- | --- |
| `accepted` | 265 `persistent_joint_cause`, 235 `climbing_only`, 250 `transient_perfect_storm` | Recommended production source for the accepted-frontier families. |
| `family_winners` | 15 rows per family across all five families | Recommended only for negative-reference diagnostics and tiny smoke gates. |
| `global_winners` | 12 `persistent_joint_cause`, 3 `climbing_only` | Too narrow for production; omit as a production source. |
| `near_frontier_absolute` | 18 `persistent_joint_cause`, 14 `climbing_only`, 3 `transient_perfect_storm` | Optional later robustness sidecar after the accepted-frontier run is reviewed. |
| `near_frontier_relative` | 13 `persistent_joint_cause`, 9 `climbing_only`, 2 `transient_perfect_storm` | Optional later robustness sidecar, not the first production source. |

The current intervention matrix is
`data/module5_counterfactual_interventions.csv`. It has 13 rows:

| family_id | intervention axes | row count |
| --- | --- | ---: |
| `persistent_joint_cause` | `status_quo`, `no_trout_pressure`, `no_climbing_pressure`, `no_trout_or_climbing_pressure` | 4 |
| `climbing_only` | `status_quo`, `no_climbing_pressure`, `no_trout_pressure` | 3 |
| `transient_perfect_storm` | `status_quo`, `no_trout_pressure`, `no_climbing_pressure`, `no_trout_or_climbing_pressure` | 4 |
| `habitat_only_null` | `status_quo` | 1 |
| `trout_only` | `status_quo` | 1 |

The outcome schema is `data/module5_counterfactual_outcome_schema.csv` and
currently defines 53 required columns. Production review depends especially on
the proposal lineage fields (`family_id`, `family_role`, `proposal_id`,
`proposal_source_key`, `module4_run_id`, `variant_id`, `seed`,
`run_dir_name`, `proposal_seed`), matching fields
(`stochastic_replicate_id`, `intervention_id`, `intervention_axis`,
`matched_pair_id`, `run_id_baseline`, `run_id_counterfactual`,
`baseline_stochastic_seed`, `intervention_stochastic_seed`), endpoint fields,
uncertainty-summary fields, and provenance fields.

## Recommended Production Run Shape

Recommended next production execution, after approval:

- Use all 750 `accepted` proposal rows for `persistent_joint_cause`,
  `climbing_only`, and `transient_perfect_storm`.
- Do not downsample the accepted frontier for the first production run. The
  recommended row count is modest for the proposed remote target, and using
  all accepted rows avoids adding an avoidable sampling decision.
- Run the 10 headline accepted-frontier rows:
  four `persistent_joint_cause` rows, two headline `climbing_only` rows, and
  four `transient_perfect_storm` rows.
- Run `m5_climbing_only_no_trout_pressure` as a diagnostic sidecar, not as the
  headline climbing-only contrast.
- Run negative-reference status-quo diagnostics from `family_winners`, with
  15 `habitat_only_null` rows and 15 `trout_only` rows.
- Use 100 stochastic replicates per proposal-row/intervention-row unit.
- Report family-specific summaries. Do not compute a single blended
  cross-family attribution estimate unless a later approval gate defines a
  defensible weighting model.

The recommended execution can be one supervised remote session with separate
partitions for headline, accepted-family diagnostic sidecar, and
negative-reference diagnostics. Partition labels should be explicit in output
paths, provenance, and inspection summaries.

## Proposal Source And Sampling Rule

Use the `accepted` proposal set for the accepted-frontier families. The filter
is:

- `in_accepted == true`;
- `family_id` in `persistent_joint_cause`, `climbing_only`,
  `transient_perfect_storm`.

Each selected unit is the full source row from
`data/module4_5_proposal_set_membership.csv`. The production launcher must
retain `module4_run_id`, `variant_id`, `seed`, `proposal_seed`,
`run_dir_name`, `family_id`, `proposal_id`, and the derived
`proposal_source_key`, and must resolve the corresponding Module 4
parameter-values artifact through `data/module4_raw_artifact_manifest.csv` or
an approved equivalent manifest. A future execution gate should prove that all
required parameter-values files exist on the remote host before production
execution.

Do not use `global_winners` as the production source because it omits the
transient sensitivity family. Do not use `near_frontier_absolute` or
`near_frontier_relative` for the first production run; they are better kept as
later robustness sidecars if reviewed production summaries indicate that the
extra contrast is useful.

## Family Treatment And Weighting

The primary report should be family-specific:

- `persistent_joint_cause`: primary headline family.
- `climbing_only`: sensitivity family, reported separately.
- `transient_perfect_storm`: sensitivity family, reported separately.
- `habitat_only_null` and `trout_only`: negative-reference diagnostics only.

Do not blend the three accepted-frontier families into a single estimate in
the first production report. Equal family weighting would imply a family-level
mixture model that has not been approved. Accepted-row weighting would
confound family support with proposal-set size and variant/seed structure.
Primary-plus-sensitivity reporting is the cleanest match to the Module 4.5
decision table.

Within each accepted-frontier family, summaries should preserve the nested
structure: matched replicates within proposal rows, proposal rows within
variant/seed source contexts, and family-specific intervals across the
accepted frontier.

## Diagnostic Sidecar

Run `m5_climbing_only_no_trout_pressure` as an accepted-family diagnostic
sidecar using the same 235 accepted `climbing_only` proposal rows and the same
100 replicate policy. This row tests removal of trout pressure in a
climbing-only family context, but it does not remove the active
climbing-galaxias pressure. It should therefore be labelled
`diagnostic_sidecar` or equivalent in production summaries and excluded from
headline climbing-only attribution weighting.

The headline `climbing_only` contrast is `m5_climbing_only_status_quo` versus
`m5_climbing_only_no_climbing_pressure`.

## Negative-Reference Treatment

Run the two negative-reference status-quo rows as diagnostics only:

- `m5_habitat_only_null_negative_reference`;
- `m5_trout_only_negative_reference`.

Use the 15 `family_winners` rows for each negative-reference family rather
than the `accepted` set, because those families have no accepted-frontier
support. These rows should check that the production pipeline can carry
non-competitive family contexts without converting them into attribution
claims.

Negative references should be excluded from production attribution summaries,
family weighting, and manuscript-level interpretation. No pressure-removal
rows should be added for negative references in the next production execution
goal.

## Replicate And Seed Policy

Recommended production replicate count: 100 stochastic replicates per
proposal-row/intervention-row unit.

Rationale:

- Module 4.5 accepted proposal rows each report `min_replicate_count = 20`;
  100 replicates gives a fivefold increase for matched counterfactual
  contrasts without creating a large artifact burden for `deep-server`.
- Goal 006 used 5 replicates to prove local plumbing and disk inspection. That
  is sufficient for a dry run but not for production uncertainty summaries.
- The recommended full run is 279,500 matched outcome rows including
  diagnostics, which is small enough for a single-host remote run but large
  enough to make replicate-level inspection meaningful.

Use deterministic common-random-number pairing. Recommended production seed
base label:

```text
galaxias-module5-production-v1
```

For each proposal-row/intervention-row/replicate unit, derive a stable
unsigned 32-bit integer seed from a SHA-256 digest over:

```text
base_label|proposal_source_key|intervention_id|stochastic_replicate_id
```

The baseline arm and intervention arm must use the same stochastic seed.
Different replicate IDs must use different seeds. The `proposal_source_key`
is:

```text
module4_run_id|variant_id|seed|run_dir_name|family_id|proposal_id
```

Matched-pair IDs and run IDs should likewise include the proposal source
context. The implemented shape is:

```text
<proposal_source_key>|<intervention_id>|r<stochastic_replicate_id>
<matched_pair_id>|baseline
<matched_pair_id>|counterfactual
```

Restart rules:

- write each partition to a temporary path and promote atomically only after
  schema, row-count, seed-pairing, and checksum checks pass;
- skip an existing partition only if its provenance, input hashes, expected
  row count, replicate coverage, and output checksum match the current run
  manifest;
- invalidate partial outputs if the intervention matrix, proposal membership
  table, raw parameter artifact manifest, seed base label, code revision, or
  environment changes.

## Expected Row Counts

Recommended production counts use 100 replicates.

| block | proposal rows | intervention rows per proposal row | proposal/intervention units | output rows |
| --- | ---: | ---: | ---: | ---: |
| `persistent_joint_cause` headline | 265 | 4 | 1,060 | 106,000 |
| `climbing_only` headline | 235 | 2 | 470 | 47,000 |
| `transient_perfect_storm` headline | 250 | 4 | 1,000 | 100,000 |
| Headline accepted-frontier total | 750 | mixed | 2,530 | 253,000 |
| `climbing_only` diagnostic sidecar | 235 | 1 | 235 | 23,500 |
| Negative-reference diagnostics | 30 | 1 | 30 | 3,000 |
| Total recommended execution | 780 distinct source rows, with 235 reused for the sidecar | mixed | 2,795 | 279,500 |

Smaller fallback if Galaxias wants a staged production rehearsal after the
remote smoke: the same design with 25 replicates would emit 69,875 rows
including diagnostics. That fallback should be treated as a rehearsal or
resource check, not as the recommended final production run.

Artifact-size expectation: plan for matched-outcome CSVs in the tens to low
hundreds of megabytes, plus provenance, logs, checksums, and inspection files.
Reserve several gigabytes of remote scratch so reruns, temporary files, and
compressed copies do not compete with the final artifact.

## Provisional `deep-server` And `tmux` Execution Model

Target: `deep-server`, using `deep-server-ts` as the preferred alias and
`utas-ubuntu` as the fallback alias if the next execution packet authorises a
live check. This Goal 009 did not run SSH, remote probes, or `tmux`.

Session model:

- one durable session named with the goal and date, for example
  `galaxias-m5-prod-YYYYMMDD`;
- source clone under `/data/codex/repos/galaxias`;
- run-specific scratch under
  `/data/codex/scratch/galaxias/module5_production_YYYYMMDD`;
- durable artifacts under
  `/data/codex/artifacts/galaxias/module5_production_YYYYMMDD`;
- logs under the run artifact directory, with separate stdout/stderr capture
  for preflight, smoke, headline execution, diagnostic sidecar, inspection,
  checksum generation, and pull-back summary creation.

Source state should be frozen before execution:

- Git branch and full SHA recorded;
- dirty state recorded and justified or rejected;
- `uv` environment created from the tracked lockfile;
- Python version and platform recorded;
- input table hashes recorded before execution;
- output and artifact directories created empty or archived before reuse.

The production run should be partitioned by family and block so that failures
can be restarted without touching valid partitions. Suggested partitions:

- `headline/persistent_joint_cause`;
- `headline/climbing_only`;
- `headline/transient_perfect_storm`;
- `diagnostic_sidecar/climbing_only_no_trout_pressure`;
- `negative_reference/habitat_only_null`;
- `negative_reference/trout_only`.

## Remote Smoke Gate

Before production execution, run a tiny remote smoke in a future authorised
goal. Recommended smoke shape:

- source: the five `baseline_current` / `20260410` `family_winners` proposal
  rows used by Goal 006;
- intervention rows: all 13 current matrix rows;
- replicates: 5 per intervention row;
- expected rows: 65;
- output: remote scratch/artifact only, not tracked and not promoted.

The remote smoke must prove:

- access to `deep-server` through an approved alias;
- repo checkout and exact source SHA;
- `uv` environment creation without unplanned dependency drift;
- availability and hashes of required local/remote Module 4 parameter-value
  artifacts for the smoke rows;
- output path creation under `/data/codex/scratch` and
  `/data/codex/artifacts`;
- schema-conforming matched outcomes;
- every intervention row has exactly 5 replicates and replicate IDs `0..4`;
- baseline and intervention stochastic seeds are paired;
- provenance labels clearly state smoke or rehearsal status, not production
  attribution;
- cleanup and artifact retention are recorded.

Production should not start if the remote smoke fails any disk-first
inspection check.

## Production Execution Gate

Production execution should require a separate Goal 010-style packet after
Galaxias and Barry approve this specification. That packet should authorise,
in writing:

- use of the 13-row matrix exactly as tracked or any approved revision;
- execution of pressure-removal rows whose current `production_status` is
  `design_only`;
- all 750 accepted proposal rows as the production source;
- the 100-replicate policy;
- the seed base label and source-context seed tuple;
- negative-reference diagnostics from `family_winners`;
- the `deep-server` target, alias, session name, remote paths, and output
  retention policy;
- the exact validation ladder and stop conditions.

Execution should stop before production if any of these conditions fail:

- input hashes or row counts differ from this specification without approval;
- raw parameter artifacts are missing for any selected proposal row;
- matched-pair IDs collide after adding source context;
- common-random-number pairing cannot be inspected from disk;
- a design-only pressure-removal row requires semantic changes rather than the
  existing hook behavior;
- remote storage, memory, or wall-time expectations are materially worse than
  expected.

## Validation And Inspection Ladder

Pre-execution local checks for a future execution goal:

- `git status --short --branch`;
- `git diff --check`;
- Module 5 contract validator;
- focused tests for proposal resolution, intervention override behavior,
  matched seed derivation, output schema, and disk-first inspection;
- a row-count preflight over proposal membership and intervention matrix;
- input-hash preflight for proposal membership, family decision table,
  intervention matrix, outcome schema, raw artifact manifest, and required
  parameter-value artifacts.

Remote preflight:

- verify host, working directory, branch, SHA, and dirty state;
- verify `uv` environment and Python version;
- verify source, scratch, artifact, and log paths;
- verify required input artifacts and available disk;
- run the tiny remote smoke and inspect from disk.

Production completion inspection:

- exact row counts for each partition and total;
- schema columns and order match `data/module5_counterfactual_outcome_schema.csv`;
- every expected proposal-row/intervention-row unit has exactly 100
  replicates;
- each replicate ID set is exactly `0..99`;
- no unexpected proposal rows, intervention IDs, or family/proposal pairings;
- matched-pair IDs are unique and include source context;
- baseline and intervention stochastic seeds match within every pair;
- uncertainty summary fields are consistent with 100 replicates;
- provenance records source SHA, dirty state, commands, input hashes, seed
  policy, remote host, output paths, partition checksums, and boundary labels;
- output checksums are written for CSV, JSON, Markdown, and compressed
  artifacts.

Pull-back criteria:

- pull back compact logs, provenance summaries, checksums, row-count reports,
  and inspection reports only after they pass review;
- leave raw matched outcomes under remote artifacts unless a later goal
  explicitly approves a local ignored mirror or a compact tracked summary.

## Output Retention And Pull-Back Policy

Raw production outputs must remain outside git. The default durable location
is `/data/codex/artifacts/galaxias/module5_production_YYYYMMDD` on
`deep-server`. Temporary work should stay under `/data/codex/scratch` and be
cleaned or archived after checksum verification.

Local pull-back, if authorised later, should use ignored `outputs/` paths and
should be limited to compact review artifacts unless Barry/Galaxias request a
raw-output mirror. Tracked files may be created only by a later review goal
and should be compact summaries, not raw matched outcomes.

Recommended artifact contents:

- `matched_outcomes.csv` or partitioned matched outcome CSVs;
- compressed copies of raw CSV partitions;
- run manifest JSON;
- provenance JSON per partition and top-level merged provenance;
- input-hash manifest;
- inspection summary JSON;
- inspection checks CSV;
- inspection report Markdown;
- checksum manifest;
- execution logs.

## Claim-Language Boundary

Reviewed production outputs may support statements of this form:

- "Within the current Module 4.5 accepted-frontier and Module 5 matched
  counterfactual design, the `persistent_joint_cause` family shows [reviewed
  matched contrast] under [named intervention]."
- "Sensitivity-family summaries for `climbing_only` and
  `transient_perfect_storm` are reported separately and do not define a
  blended family-weighted attribution estimate."
- "Negative-reference outputs are diagnostics for non-competitive families,
  not attribution evidence."

Do not use production outputs, without later review and explicit approval, to
claim final causation, manuscript-level proof, production-ready causal
language, extinction certainty, or a cross-family weighted estimate.

## Open Decisions For Galaxias And Barry

This specification makes a recommendation, but the next execution packet still
needs explicit approval for:

- full 100-replicate production execution versus a 25-replicate rehearsal;
- whether to run diagnostics in the same remote session or after headline
  partitions pass;
- exact date-stamped run name and artifact directory;
- whether the future production implementation should write one combined CSV
  or partitioned CSVs plus a merged manifest;
- whether compact production summaries should be pulled back immediately after
  inspection or only after Galaxias reviews remote artifacts.

## Proposed Next Goal

Recommended next goal after Goal 010 remote smoke and Goal 011 source identity:
a bounded source-key-aware production rehearsal or production-execution packet,
not immediate production attribution.

Suggested scope for that next goal:

- choose 25-replicate rehearsal versus 100-replicate production execution;
- freeze the source SHA, dirty-state policy, run ID, partition layout, and
  artifact locations;
- verify all required parameter-values artifacts for the selected proposal
  rows;
- run source-key-aware row-count, seed, matched-pair, provenance, restart, and
  inspection preflights;
- execute only the explicitly authorised rehearsal or production shape;
- pull back compact summaries only under the later packet's artifact policy;
- stop before any production attribution or manuscript claim language.

## Stop Points

Stop before:

- changing code, tests, Makefile, or tracked CSV contracts;
- changing pressure-removal semantics or adding new scenario hooks;
- running local or remote simulations without a future goal packet;
- probing SSH, creating `tmux` sessions, running `rsync` or `scp`, or setting
  up remote state without authorisation;
- staging, committing, pushing, publishing, or opening a PR;
- promoting raw outputs into tracked files;
- making final causal, production attribution, or manuscript-level claims.
