# Goal: Module 5 Interpretation-Gate Review

## Objective

Review the Goal 015 compact production summaries and produce a constrained
interpretation-gate memo that helps Galaxias and Barry decide what is ready,
what needs deeper audit, and what wording boundaries should govern any later
results work.

This goal is not a manuscript-preparation goal. It should not draft final
results prose, figures, tables, captions, abstract text, supplement text, or
publication claims.

## Source Inputs

Use the committed compact summaries:

```text
data/module5_production_summaries/
```

Use the Goal 015 review memo:

```text
docs/module5_production_summary_review.md
```

Use the Goal 014 production execution record only for provenance and QC:

```text
docs/module5_100rep_production_execution_report.md
docs/goals/014-module5-100rep-production-execution/Log.md
```

Raw matched outcomes remain remote-only unless this goal explicitly needs a
narrow remote source/intervention inspection. If such an inspection is needed,
run it on `deep-server-ts`, pull back only compact audit rows, and record why.

## Scope

In scope:

- Verify the compact summary files and metadata.
- Review endpoint behavior across primary, sensitivity, diagnostic sidecar,
  and negative-reference partitions.
- Identify which endpoint or endpoint bundle should carry the next review
  burden.
- Identify source/intervention units that warrant deeper audit before final
  wording.
- Create compact audit tables if needed.
- Produce an interpretation-gate memo with recommendations, caveats,
  unresolved questions, and wording boundaries.
- Commit and push the Goal 016 packet, memo, and compact audit tables if all
  checks pass.

Out of scope:

- No production rerun or new simulation.
- No raw matched-output local pull-back.
- No changes to production code, contracts, interventions, pressure semantics,
  proposal selection, family weighting, diagnostic ordering, or summaries from
  prior goals unless Galaxias authorizes an iteration.
- No manuscript prose, figure/table design, captions, abstract, supplement, or
  publication-ready results wording.
- No final causal claims.
- No PR creation.
- No force-push, amend, rebase, reset, or destructive cleanup.
- Do not read `/Users/bwbrook/chief_of_staff` or
  `/Users/bwbrook/work/goal_composer`.

## Required Review Questions

Answer these as review recommendations, not final claims:

1. Which endpoint or endpoint bundle should carry the primary interpretation
   burden for the next stage?
2. How should median-zero `extirpation_year_contrast` with positive upper tails
   be treated?
3. How should the persistent-joint-cause primary partition be weighted against
   climbing-only and transient-perfect-storm sensitivity partitions?
4. How should the diagnostic sidecar and negative-reference partitions be used
   in interpretation review?
5. What do the small negative proportions in some single-pressure rows mean for
   audit priority?
6. Which source/intervention units should be inspected remotely before any
   later manuscript-facing wording?
7. What wording is permitted in a later results memo, and what wording remains
   premature?

## Required Outputs

Create:

```text
docs/module5_interpretation_gate_review.md
```

If source/intervention audit tables are needed, create compact tracked files
under:

```text
data/module5_interpretation_audits/
```

Recommended audit files:

- `endpoint_priority_matrix.csv`
- `source_intervention_audit_targets.csv`
- `wording_boundary_matrix.csv`

Do not create figures or manuscript-style tables.

## Memo Requirements

The memo should include:

- boundary statement;
- QC recap from Goal 014/015;
- endpoint-priority recommendation;
- partition-by-partition interpretation readiness;
- source/intervention audit recommendations;
- sensitivity and diagnostic treatment;
- wording boundary matrix in prose or CSV-backed form;
- explicit stop before manuscript artefacts;
- recommended next goal shape.

Allowed language:

- "descriptive contrast"
- "candidate pattern"
- "interpretation-ready subject to Barry/Galaxias review"
- "requires audit"
- "not yet ready for manuscript wording"
- "sensitivity partition"
- "diagnostic sidecar"

Avoid final-claim language:

- "caused"
- "demonstrates"
- "proves"
- "the effect is"
- "the result shows"
- "manuscript result"
- "publication-ready"

## Validation

Run and log:

- summary metadata/QC parse check;
- CSV parse checks for Goal 015 compact summaries;
- any audit-table generation command;
- `git diff --check`;
- trailing-whitespace scan over Goal 016 files;
- marker scan for final-claim language;
- staged path list and staged diff check;
- commit and push if all gates pass.

## Stop Points

Stop and wake Galaxias before:

- pulling raw matched outcomes into the local repo;
- creating figures or manuscript-style tables;
- drafting manuscript prose;
- making final causal claims;
- changing production code or contracts;
- staging files outside the allowed Goal 016 docs/audit surface;
- proceeding if summary QC does not match Goal 015.

## Completion Condition

Goal 016 is complete when:

- compact summary evidence has been reviewed;
- interpretation priorities and audit needs are clearly stated;
- no final claims or manuscript artefacts are created;
- allowed Goal 016 files are committed and pushed;
- `pedder` wakes Galaxias and waits.
