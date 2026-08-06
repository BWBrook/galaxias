# Goal 021: Module 5 Semantic Contract Correction

## Objective

Make the active Module 5 output and provenance contracts truthful by removing
the unearned `detection_summary_*` endpoint and replacing hard-coded
25-replicate rehearsal provenance with replicate-neutral execution provenance.

## Why This Matters

The current `detection_summary_*` fields are computed as `N_total(2002) * 0.01`
but described as observation-model projections. They therefore duplicate
terminal abundance under a misleading scientific label. The verified
100-replicate execution also carries a `module5_25rep_rehearsal` status even
though the executor accepts arbitrary replicate counts.

Neither defect changes the accepted Module 5 endpoint bundle:

- `persistence_2002_contrast`;
- `min_abundance_1992_2002_contrast`;
- `lake_refuge_share_2002_contrast`.

## Required Outcomes

1. Delete `detection_summary_baseline`, `detection_summary_counterfactual`, and
   `detection_summary_contrast` from the active output builder, schema,
   validator, summary defaults, and focused test fixtures.
2. Remove `detection_summary_contrast` rows from the current committed compact
   production summaries and update their metadata and current review surfaces.
3. Record clearly that the frozen Goal 014 raw fields were a fixed abundance
   proxy and are excluded from scientific review; do not mutate or rerun the
   remote raw artifact.
4. Replace fixed 25-replicate rehearsal provenance labels with one truthful,
   replicate-neutral matched-counterfactual execution identity while retaining
   `production_attribution=false`.
5. Demonstrate that the accepted three-endpoint scientific bundle and Goals
   018-020 review tables are unchanged.

## Protected Invariants

- Frozen Goal 014 remote raw outputs, checksums, and execution record remain
  immutable.
- Source identity, matched-pair identity, common-random-number seeds, replicate
  coverage, partition counts, and schema ordering remain enforced.
- The accepted three-endpoint bundle is unchanged.
- No final attribution or manuscript claim is introduced.

## Non-Goals

- No production rerun or remote access.
- No inspector consolidation or partition-definition extraction.
- No broad rename of rehearsal modules, scripts, classes, or functions.
- No regeneration of Goal 017-020 audit, synthesis, design, or packet tables.
- No compatibility layer for the deleted detection fields or old status.
- No unrelated cleanup, dependency work, staging, commit, or push.

## Completion Standard

The active schema has 50 columns; the compact summary endpoint tables have
65, 13,975, and 65 rows; no current interpretive surface recommends the deleted
endpoint; focused tests, contract validation, `make fast-check`, and diff checks
pass. Stop after one focused repair pass.
