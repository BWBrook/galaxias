# Module 5 Interpretation-Gate Review

## Boundary

This is an interpretation-gate review of the committed Goal 015 compact
summaries. It recommends endpoint priorities, audit targets, sensitivity
treatment, diagnostic use, and wording boundaries for the next review step.

It does not draft final results prose, display items, paper-facing artifacts,
or a final attribution conclusion. Raw matched outcomes remain remote-only.

## Evidence Basis

Inputs:

- Goal 014 production execution record:
  `docs/module5_100rep_production_execution_report.md`
- Goal 015 compact-summary review:
  `docs/module5_production_summary_review.md`
- Goal 015 compact summaries:
  `data/module5_production_summaries/`
- Goal 016 compact audit CSVs:
  `data/module5_interpretation_audits/`

The compact summaries report:

- row count: 279,500
- column count: 53
- replicate IDs: 0 to 99
- source/intervention units: 2,795
- distinct `proposal_source_key` values: 780
- seed mismatches: 0
- raw matched-output SHA:
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`
- `raw_matched_outcomes_copied_locally`: false

All Goal 015 compact-summary QC checks passed.

## Endpoint Priority

Primary recommendation: carry the next review with a three-endpoint bundle:

1. `persistence_2002_contrast` as the lead target-year endpoint.
2. `min_abundance_1992_2002_contrast` as the primary magnitude support.
3. `lake_refuge_share_2002_contrast` as the spatial-refuge support.

This bundle is stronger than any single endpoint. The 2002 persistence endpoint
is directly aligned with the target-year question, but aggregate medians are
often zero and source-level heterogeneity matters. The abundance and
lake-refuge endpoints provide continuous support for magnitude and spatial
structure.

Use `extirpation_year_contrast` as a secondary heterogeneity and audit-selector
endpoint. Its aggregate medians are zero in the pressure-removal rows, but
positive upper tails identify sources worth review. It should not carry the
next review alone.

Use `persistence_1996_contrast` as an early-window consistency check. Use
`detection_summary_contrast` as a diagnostic/context endpoint, especially for
source selection, rather than as the lead interpretation endpoint.

The endpoint-priority details are recorded in
`data/module5_interpretation_audits/endpoint_priority_matrix.csv`.

## Primary Partition Readiness

The persistent-joint-cause partition should remain the primary review basis
because it is the accepted Module 4.5 primary ensemble.

Recommended treatment:

- Treat `no_trout_or_climbing_pressure` as the main combined-pressure removal
  comparator within the primary partition.
- Treat `no_climbing_pressure` and `no_trout_pressure` as single-pressure
  decompositions, not as replacements for the combined-pressure row.
- Audit source/intervention units before later wording if the review leans on
  high-persistence sources, high-abundance sources, or negative single-pressure
  values.

Key compact evidence:

- Primary combined-pressure removal has the largest median primary abundance
  and lake-refuge contrasts among the primary pressure-removal rows.
- Primary `no_climbing_pressure` and `no_trout_or_climbing_pressure` have
  similar positive `persistence_2002_contrast` proportions in aggregate.
- Primary `no_trout_pressure` has lower positive persistence proportion and a
  larger negative-value subset than the other two primary pressure-removal rows.
- `extirpation_year_contrast` medians are zero across primary pressure-removal
  rows, while upper-tail values are positive.

## Sensitivity Partition Treatment

Climbing-only sensitivity should be used as a robustness and contrast-shape
comparison, not as an equal headline basis. Its `no_climbing_pressure` row has
positive median abundance, lake-refuge, and detection-summary contrasts, and a
small positive persistence subset without negative persistence values.

Transient-perfect-storm sensitivity should also be used as a comparison
partition. The combined-pressure row has larger median abundance and
lake-refuge contrasts than the single-pressure rows, while the no-trout
single-pressure row has a negative persistence subset that deserves review if
single-pressure contrasts become central.

Recommended treatment:

- Use sensitivity partitions to check whether the endpoint bundle behaves
  coherently across accepted non-primary families.
- Do not let sensitivity partitions override the primary partition without a
  separate Galaxias/Barry decision.
- Audit selected high-magnitude sensitivity sources if later wording compares
  sensitivity magnitude against the primary partition.

## Diagnostic And Negative-Reference Treatment

The diagnostic sidecar
`diagnostic_sidecar/climbing_only_no_trout_pressure` is zero across all
summarized contrast endpoints. Use it as a diagnostic check beside the
climbing-only sensitivity partition, not as an independent headline result.

Both negative-reference partitions are zero across summarized contrast
endpoints. Use them as QC/context checks after interpretation review decides
how much space they deserve in later communication.

No remote raw-row audit is recommended now for the diagnostic sidecar,
negative references, or status-quo rows.

## Source/Intervention Audit Targets

The compact source/intervention summaries are sufficient to identify audit
targets for the next step. A remote raw-row audit is not needed in Goal 016.

Highest-priority source/intervention audit targets:

- `A01`: primary combined-pressure persistence source
  `persistent_joint_cause:p00297` under `ct007_occupancy_primary` seed
  20260411; compact persistence mean 0.81 and median 1.
- `A02`: primary no-climbing persistence source using the same source key;
  compact persistence mean 0.82 and median 1, with a negative minimum value.
- `A03`: primary no-trout persistence aggregate; 40 source/intervention units
  have negative persistence minima.
- `A04`: primary combined-pressure abundance source
  `persistent_joint_cause:p00819` under `ct010_detection_half` seed 20260411;
  compact abundance median 856.5.
- `A05`: primary combined-pressure lake-refuge source
  `persistent_joint_cause:p00695` under `ct007_occupancy_primary` seed
  20260412; compact lake-refuge median 0.752.

Sensitivity audit targets:

- climbing-only `no_climbing_pressure` high-persistence and high-abundance
  sources (`A06`, `A07`);
- transient-perfect-storm high-persistence and high-abundance sources
  (`A08`, `A09`);
- transient-perfect-storm no-trout negative persistence subset (`A10`).

The full audit-target list is recorded in
`data/module5_interpretation_audits/source_intervention_audit_targets.csv`.
All rows currently have `remote_raw_needed_now=false`; the recommended next
goal should decide which targets need read-only remote replicate inspection.

## Wording Boundaries

Allowed next-stage wording can say:

- the production execution and compact-summary QC passed;
- the interpretation gate recommends a lead endpoint bundle;
- persistent-joint-cause remains the primary partition for review;
- sensitivity partitions provide robustness and contrast-shape checks;
- diagnostic sidecar and negative-reference rows support QC/context review;
- selected source/intervention units require audit before stronger wording.

Not-yet wording includes:

- final attribution conclusions;
- one-endpoint certainty;
- equal headline weight for sensitivity partitions without an explicit
  decision;
- source-level prose without source audit;
- public-facing certainty language.

The wording matrix is recorded in
`data/module5_interpretation_audits/wording_boundary_matrix.csv`.

## Decisions For Galaxias And Barry

1. Confirm that the next review should use
   `persistence_2002_contrast`, `min_abundance_1992_2002_contrast`, and
   `lake_refuge_share_2002_contrast` as the primary endpoint bundle.
2. Decide whether `extirpation_year_contrast` should be described only as a
   heterogeneity/audit endpoint or also as a secondary timing endpoint.
3. Decide how much sensitivity-partition contrast is needed before later
   wording: primary-only, primary plus short sensitivity check, or primary plus
   detailed sensitivity comparison.
4. Decide whether the small negative subsets in single-pressure rows require
   remote replicate inspection before later wording.
5. Select the first remote audit target set from `A01` to `A10`, if raw-row
   inspection is authorized in the next goal.

## Recommended Goal 017

Goal 017 should be a targeted, read-only remote source/intervention audit. It
should inspect only selected source/intervention units from
`source_intervention_audit_targets.csv`, keep raw matched outcomes remote-only,
and pull back only compact replicate-distribution audit rows if needed.

Recommended first target set:

- `A01` to `A05` for the primary partition;
- `A10` if Galaxias wants to resolve the negative single-pressure sensitivity
  subset before wording;
- diagnostic/negative-reference rows only if a reviewer asks for control
  confirmation beyond the compact summaries.

Goal 017 should end with an audit-readiness decision and still stop before
paper-facing prose or final attribution language.
