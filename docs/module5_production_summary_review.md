# Module 5 Production Summary Review

## Boundary

This memo reviews compact summaries from the accepted Goal 014 100-replicate
Module 5 production execution. It is a QC and interpretation-planning record,
not a final attribution interpretation, manuscript result, figure/table plan,
or publication text.

Raw matched outcomes remain on `deep-server-ts` under the Goal 014 artifact:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production
```

The remote raw matched-output SHA-256 verified for summary extraction was:

```text
ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727
```

The production execution source SHA was
`ddb8a6de583e85f170f46c9dec9b1246baa6dccc`; the local Goal 014 execution
record SHA was `a96cfed24800823b77cbafeed5e9603e9dd6d33c`.

## Compact Summary Outputs

The allowed compact summaries live in `data/module5_production_summaries/`:

- `summary_metadata.json` (2,762 bytes)
- `qc_summary.csv` (2,456 bytes)
- `partition_endpoint_summary.csv` (18,520 bytes)
- `source_intervention_endpoint_summary.csv` (8,734,938 bytes)
- `direction_summary.csv` (16,987 bytes)

These files summarize only contrast endpoints:

- `extirpation_year_contrast`
- `persistence_2002_contrast`
- `persistence_1996_contrast`
- `min_abundance_1992_2002_contrast`
- `lake_refuge_share_2002_contrast`
- `detection_summary_contrast`

The compact files do not include raw matched-pair IDs, raw baseline run IDs, or
a local copy of the raw matched-output table.

## QC Summary

All summary QC checks passed.

- Raw matched-output file existed at the authorized remote artifact path.
- Raw SHA-256 matched the expected Goal 014 digest.
- Row count was 279,500 and column count was 53.
- Replicate IDs were exactly 0 to 99.
- Source/intervention units were 2,795.
- Distinct `proposal_source_key` values were 780.
- Seed mismatches were 0.
- Partition counts matched the Goal 014 production shape:
  - `headline/persistent_joint_cause`: 106,000 rows
  - `headline/climbing_only`: 47,000 rows
  - `headline/transient_perfect_storm`: 100,000 rows
  - `diagnostic_sidecar/climbing_only_no_trout_pressure`: 23,500 rows
  - `negative_reference/habitat_only_null`: 1,500 rows
  - `negative_reference/trout_only`: 1,500 rows
- Every source/intervention unit had exactly 100 rows.

## Descriptive Patterns

Status-quo rows in the three headline partitions had zero contrasts across the
summarized endpoints, as expected for matched baseline comparisons.

Primary partition: `headline/persistent_joint_cause`

- `no_trout_pressure` had a small positive median contrast for
  `min_abundance_1992_2002_contrast` (median 5) and
  `lake_refuge_share_2002_contrast` (median 0.0627), with 837 of 26,500
  `persistence_2002_contrast` values positive and 147 negative.
- `no_climbing_pressure` had a larger median contrast for
  `min_abundance_1992_2002_contrast` (median 85) and
  `lake_refuge_share_2002_contrast` (median 0.0946), with 981 of 26,500
  `persistence_2002_contrast` values positive and 3 negative.
- `no_trout_or_climbing_pressure` had the largest median primary abundance and
  lake-refuge contrasts among the three pressure-removal rows
  (`min_abundance_1992_2002_contrast` median 159;
  `lake_refuge_share_2002_contrast` median 0.1746), with 972 of 26,500
  `persistence_2002_contrast` values positive and none negative.
- `extirpation_year_contrast` medians were 0 for all three pressure-removal
  rows, while upper-tail values were positive.

Sensitivity partition: `headline/climbing_only`

- `no_climbing_pressure` had a median
  `min_abundance_1992_2002_contrast` of 116, median
  `lake_refuge_share_2002_contrast` of 0.0908, and median
  `detection_summary_contrast` of 1.38.
- `persistence_2002_contrast` was positive in 341 of 23,500 values and never
  negative.
- `extirpation_year_contrast` median was 0, with positive upper-tail values.

Sensitivity partition: `headline/transient_perfect_storm`

- `no_trout_pressure` had comparatively small median abundance and
  lake-refuge contrasts (`min_abundance_1992_2002_contrast` median 5;
  `lake_refuge_share_2002_contrast` median 0.0506), with 536 of 25,000
  `persistence_2002_contrast` values positive and 150 negative.
- `no_climbing_pressure` had larger medians (`min_abundance_1992_2002_contrast`
  median 91; `lake_refuge_share_2002_contrast` median 0.0967), with 723 of
  25,000 `persistence_2002_contrast` values positive and 22 negative.
- `no_trout_or_climbing_pressure` had the largest median sensitivity contrasts
  in this partition (`min_abundance_1992_2002_contrast` median 144;
  `lake_refuge_share_2002_contrast` median 0.1625), with 728 of 25,000
  `persistence_2002_contrast` values positive and none negative.

Diagnostic sidecar

- `diagnostic_sidecar/climbing_only_no_trout_pressure` was zero across all
  summarized contrast endpoints. That is consistent with its diagnostic role
  and should be reviewed alongside the climbing-only headline partition rather
  than treated as an independent headline result.

Negative references

- Both negative-reference partitions were zero across all summarized contrast
  endpoints. This supports the compact-summary extraction and matching checks,
  but interpretation review should still decide how prominently to cite these
  rows in any later results narrative.

## Interpretation Questions

1. Which endpoint should carry the primary review burden: 2002 persistence,
   extirpation timing, minimum abundance, lake-refuge share, detection summary,
   or a prespecified bundle?
2. How should the review treat the difference between median-zero extirpation
   timing and positive upper-tail values in headline pressure-removal rows?
3. Should the primary discussion emphasize the persistent-joint-cause partition
   alone, or explicitly compare it with the climbing-only and transient-perfect
   storm sensitivity partitions?
4. How should small negative proportions in some single-pressure-removal rows
   be handled in the next review: diagnostic uncertainty, expected stochastic
   variation, or a prompt for deeper source-level inspection?
5. What threshold should decide whether a source/intervention-level pattern is
   worth deeper review before any manuscript-facing language is drafted?

## Recommended Next Step

Goal 016 should be an interpretation-gate review, not a rerun. It should use
the compact summaries and selected source/intervention rows to decide endpoint
priority, source-level audit depth, and the wording boundaries for any later
results memo. It should keep the raw matched outcomes remote-only unless
Galaxias explicitly authorizes a narrowly scoped remote inspection.
