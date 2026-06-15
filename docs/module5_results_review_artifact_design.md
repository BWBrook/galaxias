# Module 5 Results-Review Artefact Design

## Boundary

This memo specifies internal results-review artefacts for Barry and Galaxias.
It converts the Goal 018 synthesis decisions into construction requirements,
review questions, data dependencies, and wording guardrails.

It does not create polished visuals, final display tables, paper-facing prose,
public wording, or end-state causal language. No remote command, remote audit,
raw matched-output read, simulation, or counterfactual execution was performed
for Goal 019.

No optional internal scaffold CSVs were created. The four CSV outputs are
design specifications only.

## Evidence Basis

The design uses committed compact inputs only:

- `docs/module5_interpretation_synthesis_gate.md`
- `data/module5_interpretation_synthesis/`
- `docs/module5_targeted_source_intervention_audit.md`
- `data/module5_source_intervention_audits/`
- `docs/module5_interpretation_gate_review.md`
- `data/module5_interpretation_audits/`
- `docs/module5_production_summary_review.md`
- `data/module5_production_summaries/`

Input verification confirmed:

- Goal 018 synthesis decision matrix: 9 rows.
- Goal 018 endpoint-bundle evidence: 3 rows.
- Goal 018 sensitivity treatment matrix: 4 rows.
- Goal 018 future artefact recommendations: 4 rows.
- Goal 018 wording boundary decisions: 8 rows.
- Goal 017 replicate distribution summary: 6 rows.
- Goal 017 negative-subset source list: 40 rows.
- Goal 015 summary metadata reports that raw matched outcomes were not copied
  locally.

## Goal 018 Decisions Carried Forward

The accepted endpoint bundle is carried forward unchanged:

1. `persistence_2002_contrast` is the lead endpoint.
2. `min_abundance_1992_2002_contrast` is primary magnitude support.
3. `lake_refuge_share_2002_contrast` is primary spatial-refuge support.

Persistent-joint-cause remains the primary internal review partition.
Climbing-only and transient-perfect-storm remain sensitivity and
contrast-shape checks. Diagnostic sidecar and negative-reference rows remain
QC/context material only.

`A03` is a caution on the primary no-trout single-pressure decomposition. `A10`
is a sensitivity caution for transient-perfect-storm no-trout wording.
`extirpation_year_contrast` remains secondary and audit-selector only.

## Artefact Design Summary

The required design tables are:

- `data/module5_results_review_design/artifact_specifications.csv`
- `data/module5_results_review_design/review_question_checklist.csv`
- `data/module5_results_review_design/data_dependency_matrix.csv`
- `data/module5_results_review_design/wording_guardrails.csv`

Recommended construction sequence:

1. Build the wording boundary checklist first so the later artefact builder has
   a live stop-condition sheet.
2. Build the endpoint-bundle summary grid second, because it carries the main
   review burden.
3. Build the source-audit appendix grid third, so A01-A05 and A10 can be
   checked beside the endpoint bundle before any stronger wording is drafted.
4. Build the pressure-removal contrast visual concept fourth, still as an
   internal review visual until Barry/Galaxias approve a display goal.
5. Build the sensitivity and diagnostic context grid last, after the primary
   bundle and audit cautions are visible.

## Endpoint-Bundle Summary Grid Specification

Purpose: place the lead persistence endpoint beside abundance and lake-refuge
support for the primary pressure-removal rows.

Inputs:

- `data/module5_production_summaries/partition_endpoint_summary.csv`
- `data/module5_production_summaries/direction_summary.csv`
- `data/module5_interpretation_synthesis/endpoint_bundle_evidence.csv`
- `data/module5_source_intervention_audits/replicate_distribution_summary.csv`

Required structure:

- one section for `headline/persistent_joint_cause`;
- rows for the relevant pressure-removal interventions;
- columns for endpoint-bundle role, median or direction context, audited source
  flags, A03 caution, and review-decision placeholder.

Guardrail: the grid must not let persistence alone carry the review. Abundance
and lake-refuge support should appear adjacent to the lead endpoint.

Stop condition: stop if the primary no-trout row is shown without the A03
caution.

## Pressure-Removal Contrast Visual Concept Specification

Purpose: specify a future internal visual concept comparing pressure-removal
rows across the accepted endpoint bundle.

Inputs:

- `data/module5_production_summaries/partition_endpoint_summary.csv`
- `data/module5_production_summaries/direction_summary.csv`
- `data/module5_source_intervention_audits/replicate_distribution_summary.csv`
- `data/module5_interpretation_synthesis/sensitivity_treatment_matrix.csv`

Required structure:

- primary partition first;
- sensitivity partitions after the primary partition;
- endpoint-bundle measures grouped consistently across pressure-removal rows;
- explicit A03 and A10 caution tags;
- diagnostic and negative-reference context outside the headline comparison.

Guardrail: this Goal 019 output is only a design for a later visual. It should
not render a plot or select visual styling.

Stop condition: stop if the concept gives sensitivity partitions equal lead
status without a new Galaxias/Barry decision.

## Source-Audit Appendix Grid Specification

Purpose: specify an internal appendix-style grid for the selected
source/intervention audit evidence.

Inputs:

- `data/module5_source_intervention_audits/replicate_distribution_summary.csv`
- `data/module5_source_intervention_audits/negative_subset_sources.csv`
- `docs/module5_targeted_source_intervention_audit.md`

Required structure:

- rows for `A01`, `A02`, `A03`, `A04`, `A05`, and `A10`;
- columns for endpoint, unit count, replicate coverage, negative/zero/positive
  counts, review use, and caution text;
- a separate compact note for the highest-ranked A03 and A10 negative-subset
  sources if the reviewer asks for source-level detail.

Guardrail: source rows are audit context. They should not be converted into a
broad mechanism statement.

Stop condition: stop if a reviewer requests raw row inspection; that requires a
separate authorized audit goal.

## Sensitivity And Diagnostic Context Grid Specification

Purpose: keep sensitivity partitions, diagnostic sidecar, and
negative-reference rows visible without headline weighting.

Inputs:

- `data/module5_production_summaries/partition_endpoint_summary.csv`
- `data/module5_production_summaries/direction_summary.csv`
- `data/module5_interpretation_synthesis/sensitivity_treatment_matrix.csv`
- `data/module5_interpretation_synthesis/synthesis_decision_matrix.csv`

Required structure:

- climbing-only sensitivity section;
- transient-perfect-storm sensitivity section with A10 caution;
- diagnostic sidecar section labelled QC/context;
- negative-reference section labelled QC/context;
- final column asking whether the context changes the next internal review
  question.

Guardrail: diagnostic and negative-reference rows must remain context checks.

Stop condition: stop if context rows are used as headline evidence.

## Wording Boundary Checklist Specification

Purpose: give Barry and Galaxias a checklist before later internal review text
or artefact construction.

Inputs:

- `data/module5_interpretation_synthesis/wording_boundary_decisions.csv`
- `docs/module5_interpretation_synthesis_gate.md`

Required structure:

- allowed internal wording pattern;
- blocked stronger wording pattern;
- reason;
- reviewer check;
- release condition for any later stronger language.

Guardrail: the checklist should constrain later work; it should not itself
become paper-facing phrasing.

Stop condition: stop if a checklist item reads like a result statement rather
than a review rule.

## Review Questions For Barry And Galaxias

Highest-priority questions:

1. Is the three-endpoint bundle sufficient for the next internal review, or
   should any endpoint be demoted before artefact construction?
2. Should A03 appear in the main endpoint grid or in the source-audit appendix
   only?
3. Should A10 appear in the sensitivity context grid only, or also in a short
   cross-reference from the pressure-removal concept?
4. Is extirpation timing still secondary, or should a separate timing audit be
   authorized before any paper-facing work?
5. How much diagnostic and negative-reference context should the next packet
   include: minimal QC row, short context grid, or fuller internal appendix?
6. Which reviewer decision should stop the next goal before any stronger
   wording is drafted?

The complete question list is in
`data/module5_results_review_design/review_question_checklist.csv`.

## Validation Expectations For A Future Artefact-Building Goal

A future artefact-building goal should:

- re-verify the Goal 015 compact summary metadata and no-local-raw flag;
- re-verify Goal 018 decision-table row counts;
- parse every Goal 019 design table;
- prove any constructed artefact is internal and non-display unless a later
  packet explicitly widens the boundary;
- keep raw matched outcomes remote-only unless a separate remote audit goal is
  authorized;
- include marker scans for stronger causal, paper-facing, and public wording;
- stage only the authorized artefact-building files.

## Wording Guardrails

The strongest safe internal formulation is:

- the endpoint bundle is accepted for internal review;
- `persistence_2002_contrast` is the lead endpoint;
- `min_abundance_1992_2002_contrast` and
  `lake_refuge_share_2002_contrast` are primary support endpoints;
- persistent-joint-cause is the primary review partition;
- A03 and A10 are caution flags for specified single-pressure rows;
- diagnostic and negative-reference rows are QC/context checks.

Do not use this design goal to draft stronger public, paper-facing, or
end-state causal language.

The detailed guardrails are in
`data/module5_results_review_design/wording_guardrails.csv`.

## Recommended Goal 020

Recommended Goal 020 shape: an internal artefact-building specification or
construction goal that builds the non-display review packet from these designs.
It should start with the wording checklist, then construct the endpoint-bundle
grid, source-audit appendix grid, pressure-removal visual concept, and
sensitivity/diagnostic context grid in that order.

Goal 020 should still stop before public wording or end-state causal language
unless Galaxias explicitly authorizes a wider communication step.
