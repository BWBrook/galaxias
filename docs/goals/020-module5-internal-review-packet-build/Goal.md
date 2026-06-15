# Goal: Module 5 Internal Review Packet Build

## Objective

Build the internal, non-display Module 5 results-review packet specified by
Goal 019.

This goal should assemble review-ready internal tables and a concise review
packet memo for Barry and Galaxias. The packet should make the accepted
endpoint bundle, audit cautions, sensitivity context, and wording guardrails
easy to inspect together before any stronger interpretation or manuscript work
is considered.

This goal must not create polished figures, manuscript-ready display tables,
captions, public-facing prose, or final attribution claims.

## Source Inputs

Use these committed inputs:

```text
docs/module5_results_review_artifact_design.md
data/module5_results_review_design/
docs/module5_interpretation_synthesis_gate.md
data/module5_interpretation_synthesis/
docs/module5_targeted_source_intervention_audit.md
data/module5_source_intervention_audits/
docs/module5_production_summary_review.md
data/module5_production_summaries/
```

Do not read raw matched outcomes, run remote commands, or modify prior summary,
audit, synthesis, or design outputs.

## Scope

In scope:

- Verify the Goal 019 design outputs and upstream compact evidence.
- Build internal non-display review tables:
  - wording boundary checklist;
  - endpoint-bundle summary grid;
  - source-audit appendix grid;
  - pressure-removal contrast matrix;
  - sensitivity and diagnostic context grid.
- Write an internal review packet memo that explains how Barry and Galaxias
  should inspect the tables.
- Label all outputs as internal review material.
- Preserve explicit stop points before public or paper-facing wording.
- Commit and push the Goal 020 packet, internal review tables, and memo if all
  checks pass.

Out of scope:

- No new simulation, production rerun, counterfactual execution, remote audit,
  or raw matched-output read.
- No local copy of `matched_outcomes.csv`.
- No changes to production code, contracts, interventions, pressure semantics,
  proposal selection, family weighting, diagnostic ordering, summaries, or
  prior audit/synthesis/design outputs.
- No polished figures, final display tables, rendered plots, captions,
  abstract, supplement, manuscript prose, public-facing wording, final
  attribution language, or final causal claims.
- No PR creation.
- No force-push, amend, rebase, reset, or destructive cleanup.
- Do not read `/Users/bwbrook/chief_of_staff` or
  `/Users/bwbrook/work/goal_composer`.

## Required Outputs

Create:

```text
docs/module5_internal_results_review_packet.md
```

Create compact internal review tables under:

```text
data/module5_internal_review_packet/
```

Required files:

- `wording_boundary_checklist.csv`
- `endpoint_bundle_summary_grid.csv`
- `source_audit_appendix_grid.csv`
- `pressure_removal_contrast_matrix.csv`
- `sensitivity_diagnostic_context_grid.csv`
- `review_packet_manifest.json`

Every CSV must include a first column named `packet_status`, and every row in
that column must be `internal_non_display`.

## Table Requirements

### Wording Boundary Checklist

Purpose: give Barry and Galaxias a first-stop checklist before reading any
other table.

Required row count: at least 8 rows.

Required content:

- allowed internal wording pattern;
- blocked stronger wording pattern;
- reason;
- reviewer check;
- release condition.

### Endpoint-Bundle Summary Grid

Purpose: place `persistence_2002_contrast`,
`min_abundance_1992_2002_contrast`, and
`lake_refuge_share_2002_contrast` beside each other for the primary
persistent-joint-cause pressure-removal rows.

Required content:

- primary partition rows first;
- endpoint role;
- median or direction evidence;
- audited source support;
- A03 caution on the no-trout single-pressure row;
- review-decision placeholder.

Stop if the table lets `persistence_2002_contrast` stand alone without
abundance and lake-refuge support.

### Source-Audit Appendix Grid

Purpose: summarize A01-A05 and A10 compact audit findings as audit context.

Required row count: 6 rows.

Required content:

- audit ID;
- endpoint;
- source/intervention unit count;
- replicate rows;
- negative/zero/positive counts;
- review use;
- caution text.

### Pressure-Removal Contrast Matrix

Purpose: organize pressure-removal contrasts across the accepted endpoint
bundle for internal review.

Required content:

- primary persistent-joint-cause rows before sensitivity rows;
- explicit A03 and A10 caution tags;
- no polished visual styling or figure rendering;
- diagnostic and negative-reference context kept outside headline rows.

### Sensitivity And Diagnostic Context Grid

Purpose: keep sensitivity, diagnostic sidecar, and negative-reference context
visible without headline weighting.

Required content:

- climbing-only sensitivity context;
- transient-perfect-storm sensitivity context with A10 caution;
- diagnostic sidecar as QC/context;
- negative references as QC/context;
- reviewer question asking whether context changes the next internal review.

## Memo Requirements

The review packet memo should include:

- boundary statement;
- evidence basis;
- packet manifest summary;
- recommended reading order;
- how to inspect each table;
- explicit places where Barry/Galaxias should apply skeptical review;
- stop conditions before stronger wording;
- recommended next step after Galaxias review.

Use internal review language only. Do not write manuscript-style results prose.

## Validation

Run and log:

- starting repo state guard;
- structured parse checks for Goal 019 design outputs;
- structured parse checks for all Goal 020 packet tables;
- manifest consistency check;
- `git diff --check`;
- trailing-whitespace scan over Goal 020 files;
- marker scan for final-claim, manuscript, caption, and public-facing
  language;
- staged path list and staged diff check;
- commit and push if all gates pass.

## Stop Points

Stop and wake Galaxias before:

- reading remote raw data or running remote commands;
- creating polished figures, rendered plots, final display tables, captions,
  manuscript prose, public-facing wording, or final attribution claims;
- changing earlier summary, audit, synthesis, design, code, or contract files;
- staging files outside the allowed Goal 020 packet surface;
- proceeding if the internal packet requires a scientific decision not already
  authorized by Goal 018/019.

## Completion Condition

Goal 020 is complete when:

- the internal review packet is assembled from compact committed evidence;
- all tables are labelled `internal_non_display`;
- no polished artefacts, manuscript prose, or final claims are created;
- allowed Goal 020 files are committed and pushed;
- `pedder` wakes Galaxias and waits.
