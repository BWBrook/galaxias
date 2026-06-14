# Goal: Module 5 Production Summary Review

## Objective

Create reproducible compact summaries and a review memo from the Goal 014
100-replicate Module 5 production execution, while keeping raw matched
outcomes remote-only and stopping before final interpretation or manuscript
claims.

This goal should answer: "What compact evidence do we now have, what quality
checks support it, and what interpretation questions should Galaxias and Barry
decide next?"

It should not answer: "What is the final causal conclusion?"

## Source Artifact

Use the accepted Goal 014 production artifact:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production
```

Raw matched outcomes:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/matched_outcomes.csv
```

Expected raw matched SHA-256:

```text
ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727
```

Source execution commit:

```text
ddb8a6de583e85f170f46c9dec9b1246baa6dccc
```

Goal 014 record commit:

```text
a96cfed24800823b77cbafeed5e9603e9dd6d33c
```

## Scope

In scope:

- Verify the Goal 014 local record and remote artifact/checksum state.
- Add a small reproducible production-summary implementation.
- Add focused tests using synthetic compact data.
- Run the summarizer on `deep-server-ts` against the remote raw matched
  outcomes.
- Pull back only compact summary artifacts.
- Create a review memo with descriptive summaries, QC findings, and
  interpretation-planning questions.
- Commit and push the Goal 015 packet, summarizer, tests, compact summaries,
  and review memo if all checks pass.

Out of scope:

- No new simulations or reruns.
- No changes to Module 5 execution code, intervention contracts, pressure
  semantics, proposal selection, family weighting, diagnostic ordering, or
  production artifacts.
- No raw matched-outcome pull-back into the local repo.
- No production attribution interpretation as a final conclusion.
- No final causal claim language.
- No manuscript, abstract, figure, supplement, or publication text.
- No PR creation.
- No force-push, amend, rebase, reset, or destructive cleanup.
- Do not read `/Users/bwbrook/chief_of_staff` or
  `/Users/bwbrook/work/goal_composer`.

## Required Summary Outputs

Create compact tracked outputs under:

```text
data/module5_production_summaries/
```

Required files:

- `summary_metadata.json`
  - source artifact path;
  - source execution SHA;
  - raw matched-output SHA and size;
  - summarizer command and timestamp;
  - row count, column count, replicate count, source-key count, unit count;
  - explicit non-interpretation boundary.
- `qc_summary.csv`
  - check name, observed value, expected value, pass/fail, details.
- `partition_endpoint_summary.csv`
  - partition, family, intervention, endpoint, row count, source count, unit
    count, mean, median, q025, q25, q75, q975, min, max.
- `source_intervention_endpoint_summary.csv`
  - one row per source/intervention/endpoint with source identity, partition,
    family, intervention, n replicates, mean, median, q025, q975, min, max.
- `direction_summary.csv`
  - partition, family, intervention, endpoint, negative/zero/positive counts
    and proportions using the endpoint contrast values.

Create tracked review memo:

```text
docs/module5_production_summary_review.md
```

The memo should:

- state the boundary clearly;
- summarize QC status;
- describe the compact summary outputs;
- identify descriptive patterns and possible interpretation questions;
- separate primary, sensitivity, diagnostic sidecar, and negative-reference
  material;
- explicitly stop before final causal claims, figures/tables, or manuscript
  language.

## Required Endpoints

Summarize contrast endpoints only:

- `extirpation_year_contrast`
- `persistence_2002_contrast`
- `persistence_1996_contrast`
- `min_abundance_1992_2002_contrast`
- `lake_refuge_share_2002_contrast`
- `detection_summary_contrast`

Do not summarize raw baseline/counterfactual abundance trajectories as if they
were final effects.

## Required QC Checks

The summarizer must verify and record:

- raw matched-output file exists only on the remote artifact path;
- raw matched-output SHA matches
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`;
- row count: 279,500;
- column count: 53;
- replicate IDs exactly `0..99`;
- source/intervention units: 2,795;
- distinct `proposal_source_key` values: 780;
- seed mismatches: 0;
- expected partition counts:
  - `headline/persistent_joint_cause`: 106,000
  - `headline/climbing_only`: 47,000
  - `headline/transient_perfect_storm`: 100,000
  - `diagnostic_sidecar/climbing_only_no_trout_pressure`: 23,500
  - `negative_reference/habitat_only_null`: 1,500
  - `negative_reference/trout_only`: 1,500
- every source/intervention unit has exactly 100 rows;
- summary outputs contain no raw matched-outcome rows.

## Allowed Files

Allowed local tracked edits/additions:

- `docs/goals/015-module5-production-summary-review/Goal.md`
- `docs/goals/015-module5-production-summary-review/Plan.md`
- `docs/goals/015-module5-production-summary-review/Runbook.md`
- `docs/goals/015-module5-production-summary-review/Log.md`
- `docs/module5_production_summary_review.md`
- `data/module5_production_summaries/summary_metadata.json`
- `data/module5_production_summaries/qc_summary.csv`
- `data/module5_production_summaries/partition_endpoint_summary.csv`
- `data/module5_production_summaries/source_intervention_endpoint_summary.csv`
- `data/module5_production_summaries/direction_summary.csv`
- `src/galaxias_model/module5_production_summary.py`
- `scripts/summarize_module5_production.py`
- `tests/test_module5_production_summary.py`

Do not edit production runner code unless you stop and ask first.

## Validation

Run and log:

- focused tests for the production summary module;
- `uv run python scripts/summarize_module5_production.py --help`;
- remote summary command against the Goal 014 artifact;
- local verification of pulled-back compact summary files;
- `git diff --check`;
- trailing-whitespace scan over changed files;
- marker scan over Goal 015 docs for boundary language;
- staged path list and staged diff check;
- commit and push if all gates pass.

## Stop Points

Stop and wake Galaxias before:

- copying raw `matched_outcomes.csv` into the local repo;
- changing source/execution code;
- changing or rerunning production execution;
- altering raw remote artifacts;
- making final causal/manuscript claims;
- staging files outside the allowed list;
- committing if any QC check fails.

## Completion Condition

Goal 015 is complete when:

- compact summaries are generated reproducibly from the remote production
  artifact;
- QC passes;
- a review memo frames descriptive patterns and interpretation questions
  without final claims;
- allowed local files are committed and pushed;
- raw matched outcomes remain remote-only;
- `pedder` wakes Galaxias and waits.
