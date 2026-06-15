# Goal: Module 5 Results-Review Artefact Design

## Objective

Design the internal results-review artefacts that Barry and Galaxias should use
to interrogate the Module 5 interpretation stack.

This goal should convert the Goal 018 synthesis decisions into a constrained
review packet outline and artefact specifications. It may create compact
internal scaffold tables to clarify design requirements, but it must not create
manuscript-ready figures, display tables, captions, final prose, public-facing
wording, or final attribution claims.

## Source Inputs

Use these committed inputs:

```text
docs/module5_interpretation_synthesis_gate.md
data/module5_interpretation_synthesis/
docs/module5_targeted_source_intervention_audit.md
data/module5_source_intervention_audits/
docs/module5_interpretation_gate_review.md
data/module5_interpretation_audits/
docs/module5_production_summary_review.md
data/module5_production_summaries/
```

Use Goal 018 recommendations as the design basis:

- endpoint-bundle summary grid;
- pressure-removal contrast visual concept;
- source-audit appendix grid;
- sensitivity and diagnostic context grid;
- wording boundary checklist.

Do not read raw matched outcomes, run remote commands, or create final
publication artefacts.

## Scope

In scope:

- Verify the Goal 018 synthesis decision outputs.
- Create a concise internal review packet design memo.
- Create artefact specification CSVs for the recommended review artefacts.
- Create optional compact scaffold CSVs only if needed to make the designs
  reviewable; every scaffold must be labelled internal and non-display.
- Define review questions Barry and Galaxias should answer when they later
  inspect the artefacts.
- Define data dependencies, construction rules, and wording constraints for
  each future artefact.
- Commit and push the Goal 019 packet, design memo, and compact specification
  files if all checks pass.

Out of scope:

- No new simulation, production rerun, counterfactual execution, remote audit,
  or raw matched-output read.
- No local copy of `matched_outcomes.csv`.
- No changes to production code, contracts, interventions, pressure semantics,
  proposal selection, family weighting, diagnostic ordering, summaries, or
  previous audit/synthesis outputs.
- No polished figures, final display tables, captions, abstract, supplement,
  manuscript prose, public-facing wording, final attribution language, or final
  causal claims.
- No PR creation.
- No force-push, amend, rebase, reset, or destructive cleanup.
- Do not read `/Users/bwbrook/chief_of_staff` or
  `/Users/bwbrook/work/goal_composer`.

## Required Outputs

Create:

```text
docs/module5_results_review_artifact_design.md
```

Create compact design outputs under:

```text
data/module5_results_review_design/
```

Required files:

- `artifact_specifications.csv`
- `review_question_checklist.csv`
- `data_dependency_matrix.csv`
- `wording_guardrails.csv`

Optional internal scaffold files may be created under the same directory only
if they are needed to clarify an artefact design. If created, their filenames
must begin with `internal_scaffold_`, and their first column must be
`scaffold_status` with value `internal_non_display`.

## Artefact Design Requirements

Design these review artefacts:

1. `endpoint_bundle_summary_grid`
   - Purpose: show lead persistence evidence beside abundance and lake-refuge
     support.
   - Inputs: Goal 015 compact summaries, Goal 017 audit summary, Goal 018
     endpoint evidence.
   - Must include: primary partition emphasis, source-audit flags, and A03
     caution.
2. `pressure_removal_contrast_visual_concept`
   - Purpose: specify a future visual that compares pressure-removal rows
     across the accepted endpoint bundle.
   - Inputs: `partition_endpoint_summary.csv`,
     `replicate_distribution_summary.csv`, and Goal 018 decision tables.
   - Must remain a concept/specification, not an actual figure.
3. `source_audit_appendix_grid`
   - Purpose: specify an appendix-style internal review table for A01-A05 and
     A10 audit evidence.
   - Inputs: Goal 017 replicate distribution and negative-subset files.
   - Must keep source-level material as audit context, not narrative proof.
4. `sensitivity_diagnostic_context_grid`
   - Purpose: specify how sensitivity partitions, diagnostic sidecar, and
     negative-reference rows should be kept visible without headline weighting.
   - Inputs: Goal 015 summaries, Goal 016 sensitivity treatment, Goal 018
     sensitivity decisions.
   - Must carry A10 as caution, not headline material.
5. `wording_boundary_checklist`
   - Purpose: give Barry/Galaxias a checklist for later review.
   - Inputs: Goal 018 wording boundaries.
   - Must distinguish internal review wording from public/paper-facing wording.

## Design Memo Requirements

The memo should include:

- boundary statement;
- evidence basis;
- accepted Goal 018 decisions being carried forward;
- one section per artefact design;
- review questions for Barry/Galaxias;
- recommended construction order;
- validation and provenance expectations for a future artefact-building goal;
- wording guardrails;
- recommended Goal 020 shape.

Use concise specification language. Do not write results-section prose.

## Validation

Run and log:

- starting repo state guard;
- structured parse checks for the Goal 018 decision outputs;
- CSV parse checks for all Goal 019 design outputs;
- optional scaffold checks if scaffolds are created;
- `git diff --check`;
- trailing-whitespace scan over Goal 019 files;
- marker scan for final-claim, manuscript, caption, and public-facing language;
- staged path list and staged diff check;
- commit and push if all gates pass.

## Stop Points

Stop and wake Galaxias before:

- reading remote raw data or running remote commands;
- creating actual figures, final display tables, captions, manuscript prose,
  public-facing wording, or final attribution claims;
- changing earlier summary, audit, synthesis, code, or contract files;
- staging files outside the allowed Goal 019 docs/design surface;
- proceeding if design work requires scientific choices not already authorized
  by Goal 018.

## Completion Condition

Goal 019 is complete when:

- the future internal review artefacts are specified clearly enough for a later
  artefact-building goal;
- review questions and wording guardrails are explicit;
- no final artefacts, manuscript prose, or final claims are created;
- allowed Goal 019 files are committed and pushed;
- `pedder` wakes Galaxias and waits.
