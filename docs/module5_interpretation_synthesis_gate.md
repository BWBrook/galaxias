# Module 5 Interpretation-Synthesis Gate

## Boundary

This memo is an internal interpretation-synthesis decision record. It
synthesizes the committed Goal 015 compact summaries, Goal 016
interpretation-gate review, and Goal 017 targeted source/intervention audit.

It does not create public-facing wording, paper-facing prose, display
artefacts, or a final conclusion. No remote audit or raw matched-outcome read
was performed for Goal 018.

## Evidence Stack

The synthesis uses these committed inputs:

- `docs/module5_production_summary_review.md`
- `docs/module5_interpretation_gate_review.md`
- `docs/module5_targeted_source_intervention_audit.md`
- `data/module5_production_summaries/`
- `data/module5_interpretation_audits/`
- `data/module5_source_intervention_audits/`

Structured evidence verification passed:

- Goal 015 compact summary QC passed.
- Goal 015 row count is 279,500.
- Goal 015 source/intervention units are 2,795.
- Goal 015 distinct source keys are 780.
- Goal 015 reports no local raw matched-output copy.
- Goal 016 endpoint-priority table has 6 rows.
- Goal 016 audit-target table has 14 rows.
- Goal 017 selected IDs are `A01`, `A02`, `A03`, `A04`, `A05`, and `A10`.
- Goal 017 reports that the endpoint bundle survived targeted raw-row audit.
- Goal 017 reports no local raw matched-output copy and no broad raw extract.

No committed evidence contradicts the Galaxias starting decisions for this
goal.

## Accepted Synthesis Decisions

The synthesis decision matrix is recorded in
`data/module5_interpretation_synthesis/synthesis_decision_matrix.csv`.

Accepted decisions:

- The three-endpoint bundle is accepted for internal synthesis.
- Source-level audit is sufficient for this synthesis gate.
- Persistent-joint-cause remains the primary internal review basis.
- Sensitivity partitions remain robustness and contrast-shape checks.
- `A03` is carried as a caution on primary no-trout single-pressure
  decomposition.
- `A10` is carried as a transient-perfect-storm no-trout sensitivity caution.
- `extirpation_year_contrast` remains secondary and audit-selector only.
- Diagnostic sidecar and negative-reference rows remain QC/context material.
- No public or paper-facing wording is authorized by this gate.

## Endpoint Bundle Decision

The accepted endpoint bundle is:

1. `persistence_2002_contrast` as the lead endpoint.
2. `min_abundance_1992_2002_contrast` as primary magnitude support.
3. `lake_refuge_share_2002_contrast` as primary spatial-refuge support.

This bundle is accepted because Goal 016 recommended it and Goal 017 audited
the selected source/intervention targets without finding a contradiction.

Key Goal 017 audit support:

- `A01`: 100 rows; 0 negative, 19 zero, and 81 positive
  `persistence_2002_contrast` values.
- `A02`: 100 rows; 1 negative, 16 zero, and 83 positive
  `persistence_2002_contrast` values.
- `A03`: 4,000 rows across 40 primary no-trout negative-subset units; 147
  negative, 3,263 zero, and 590 positive `persistence_2002_contrast` values.
- `A04`: 100 positive `min_abundance_1992_2002_contrast` values, with median
  856.5.
- `A05`: 100 positive `lake_refuge_share_2002_contrast` values, with median
  0.7520.

The endpoint evidence table is recorded in
`data/module5_interpretation_synthesis/endpoint_bundle_evidence.csv`.

## Primary Partition Treatment

Persistent-joint-cause should be treated as the primary internal review
partition. It remains the accepted Module 4.5 primary ensemble and now has
source-audited support for the accepted endpoint bundle.

Within that primary partition:

- combined pressure removal should be the main comparator;
- no-climbing and no-trout rows should be treated as decompositions;
- the no-trout decomposition should carry the `A03` caution.

`A03` does not block the endpoint bundle. It does prevent clean,
over-simplified no-trout decomposition wording in this synthesis.

## Sensitivity Treatment

Climbing-only remains a sensitivity and contrast-shape check. It should not be
given equal headline status without a later Galaxias/Barry decision.

Transient-perfect-storm remains a sensitivity and contrast-shape check with an
explicit `A10` caution. Goal 017 confirmed that the no-trout sensitivity row
has a real negative persistence subset:

- 23 source/intervention units;
- 2,300 replicate rows;
- 150 negative, 1,724 zero, and 426 positive persistence values.

The sensitivity treatment matrix is recorded in
`data/module5_interpretation_synthesis/sensitivity_treatment_matrix.csv`.

## Diagnostic And Negative-Reference Treatment

Diagnostic sidecar and negative-reference rows should be retained as QC/context
material only. Goal 015 showed zero contrasts across the summarized diagnostic
sidecar and negative-reference endpoints, and Goals 016-017 did not create a
reason to change that treatment.

These rows should help frame confidence in matching, controls, and context.
They should not be used as headline evidence.

## Source-Audit Sufficiency

Source-level audit is sufficient for this synthesis gate.

Reasoning:

- Goal 017 audited the selected primary source-specific targets.
- Goal 017 audited the primary no-trout negative subset.
- Goal 017 audited the transient-perfect-storm no-trout sensitivity caution.
- All selected targets were consistent with Goal 016 compact-summary
  descriptions.
- The endpoint bundle survived targeted raw-row audit.

No further raw audit is required before internal synthesis. A later goal may
still choose to audit extirpation timing if that endpoint becomes more central.

## Extirpation Timing Decision

`extirpation_year_contrast` remains secondary and audit-selector only.

Rationale:

- Goal 016 identified median-zero timing with positive upper tails.
- Goal 017 did not audit timing because Galaxias selected persistence,
  abundance, lake-refuge, and negative persistence subset targets.
- Goal 018 explicitly does not authorize an extirpation-timing audit.

Do not promote timing above the accepted endpoint bundle without a separate
audit goal.

## Future Artefact Recommendations

Future artefact recommendations are design notes only. Goal 018 does not
create those artefacts.

Recommended future artefact concepts:

- `endpoint_bundle_summary_grid`: summarize lead persistence with abundance and
  lake-refuge support.
- `pressure_removal_contrast_visual_concept`: compare primary pressure-removal
  rows across the accepted endpoint bundle.
- `source_audit_appendix_grid`: summarize A01-A05 and A10 audit findings.
- `sensitivity_diagnostic_context_grid`: keep sensitivity, diagnostic, and
  negative-reference context visible without headline weighting.

These recommendations are recorded in
`data/module5_interpretation_synthesis/future_artifact_recommendations.csv`.

## Wording Boundaries

Allowed internal wording:

- Goal 015-017 compact evidence is verified and suitable for internal
  synthesis.
- The endpoint bundle is accepted for internal synthesis.
- Persistent-joint-cause is the primary review basis.
- `A03` and `A10` are caution flags for their respective single-pressure rows.
- Extirpation timing remains secondary and audit-selector only.
- Diagnostic sidecar and negative-reference rows are QC/context checks.
- Future artefacts are design recommendations only.

Not authorized in Goal 018:

- public certainty statements;
- one-endpoint certainty;
- unqualified public mechanism statements;
- clean single-pressure decomposition wording;
- headline sensitivity claims;
- timing-led interpretation;
- paper-facing artefacts or public wording.

The wording boundary decisions are recorded in
`data/module5_interpretation_synthesis/wording_boundary_decisions.csv`.

## Unresolved Decisions

For Galaxias/Barry:

1. Decide whether the accepted endpoint bundle is now ready for a human-facing
   internal review packet.
2. Decide whether to run a narrow extirpation-timing audit before artefact
   design, or keep timing secondary for now.
3. Decide how much sensitivity detail should appear in the next review packet.
4. Decide whether `A03` and `A10` should be visible in the main internal review
   memo or held in an audit appendix.
5. Decide which future artefact concepts should be authorized next.

## Recommended Goal 019

Recommended Goal 019 shape: an internal results-review packet design goal.
It should use the Goal 018 decisions to design, but not overstate, the next
review artefacts:

- endpoint-bundle summary grid;
- pressure-removal contrast visual concept;
- source-audit appendix grid;
- sensitivity and diagnostic context grid;
- wording boundary checklist for Barry/Galaxias review.

Goal 019 should remain internal unless Galaxias explicitly widens the boundary
to public or paper-facing drafting in a later packet.
