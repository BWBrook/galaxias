# Goal: Module 5 Interpretation-Synthesis Gate

## Objective

Synthesize the Goal 015 compact summaries, Goal 016 interpretation-gate review,
and Goal 017 targeted source/intervention audit into a constrained internal
interpretation decision record.

This goal should decide what is ready for later Galaxias/Barry discussion,
what remains provisional, and what artefacts should be considered in a future
results-review goal. It must not draft manuscript prose, create display
figures, or make final attribution claims.

## Source Inputs

Use these committed inputs:

```text
docs/module5_production_summary_review.md
docs/module5_interpretation_gate_review.md
docs/module5_targeted_source_intervention_audit.md
data/module5_production_summaries/
data/module5_interpretation_audits/
data/module5_source_intervention_audits/
```

Use Goal 014/015/016/017 logs only for provenance and validation context:

```text
docs/goals/014-module5-100rep-production-execution/Log.md
docs/goals/015-module5-production-summary-review/Log.md
docs/goals/016-module5-interpretation-gate-review/Log.md
docs/goals/017-module5-targeted-source-intervention-audit/Log.md
```

Do not read raw remote matched outcomes unless Galaxias authorizes a later
goal. Goal 018 should work from committed compact summaries and audit outputs.

## Galaxias Decisions For This Goal

Treat these as the starting decisions for the synthesis:

- Accept the endpoint bundle for synthesis:
  `persistence_2002_contrast`, `min_abundance_1992_2002_contrast`, and
  `lake_refuge_share_2002_contrast`.
- Treat `persistence_2002_contrast` as the lead endpoint.
- Treat `min_abundance_1992_2002_contrast` and
  `lake_refuge_share_2002_contrast` as primary support endpoints.
- Keep `extirpation_year_contrast` secondary and audit-selector only; do not
  run an extirpation-timing audit in this goal.
- Treat `A03` as a caution on the primary no-trout single-pressure
  decomposition, not as a blocker to the endpoint bundle.
- Treat `A10` as a sensitivity caution for transient-perfect-storm no-trout
  wording, not as headline material.

If the committed evidence contradicts any of these decisions, stop and wake
Galaxias instead of forcing the synthesis.

## Scope

In scope:

- Verify the Goal 015, 016, and 017 compact inputs.
- Produce a synthesis memo that records accepted endpoint priorities,
  source-audit sufficiency, sensitivity treatment, diagnostic treatment,
  unresolved scientific decisions, and future artefact needs.
- Create compact decision tables supporting the memo.
- Identify candidate future artefacts in design-note form only.
- Define exact wording boundaries for any later internal results memo.
- Commit and push the Goal 018 packet, synthesis memo, and compact decision
  tables if all checks pass.

Out of scope:

- No new simulation, production rerun, counterfactual execution, or remote raw
  audit.
- No raw matched-output pull-back.
- No changes to production code, contracts, interventions, pressure semantics,
  proposal selection, family weighting, diagnostic ordering, summaries, or
  audit CSVs from prior goals.
- No manuscript prose, final results prose, figures, display tables, captions,
  abstract, supplement, public-facing wording, or final attribution claims.
- No PR creation.
- No force-push, amend, rebase, reset, or destructive cleanup.
- Do not read `/Users/bwbrook/chief_of_staff` or
  `/Users/bwbrook/work/goal_composer`.

## Required Outputs

Create:

```text
docs/module5_interpretation_synthesis_gate.md
```

Create compact decision outputs under:

```text
data/module5_interpretation_synthesis/
```

Required files:

- `synthesis_decision_matrix.csv`
- `endpoint_bundle_evidence.csv`
- `sensitivity_treatment_matrix.csv`
- `future_artifact_recommendations.csv`
- `wording_boundary_decisions.csv`

These are internal decision tables, not display tables for a manuscript.

## Synthesis Requirements

The synthesis memo should answer:

1. Is the three-endpoint bundle accepted for the next internal interpretation
   review?
2. Is source-level audit sufficient for the current synthesis gate?
3. How should the primary persistent-joint-cause partition be treated relative
   to sensitivity partitions?
4. How should `A03` and `A10` affect later wording?
5. Should `extirpation_year_contrast` remain secondary/audit-selector only?
6. What diagnostic and negative-reference evidence should be retained as QC
   context?
7. What future artefacts would be useful for a later Barry/Galaxias review,
   without creating them now?
8. What language remains prohibited until a later human-reviewed results or
   manuscript goal?

## Required Stance

The synthesis should be decisive but provisional:

- Accept the endpoint bundle if the evidence remains consistent.
- Do not over-weight single source-specific examples.
- Keep negative single-pressure subsets visible as cautions.
- Keep sensitivity partitions as contrast-shape and robustness checks, not
  equal headline bases.
- Preserve the distinction between internal readiness and manuscript readiness.

## Allowed Language

Allowed:

- "accepted for internal synthesis"
- "source-audited support"
- "sensitivity caution"
- "diagnostic context"
- "not yet manuscript-ready"
- "candidate future artefact"
- "requires Barry/Galaxias review before public wording"

Avoid:

- "caused"
- "demonstrates"
- "proves"
- "the effect is"
- "the result shows"
- "manuscript result"
- "publication-ready"
- "final attribution"
- "final causal claim"

## Validation

Run and log:

- starting repo state guard;
- structured parse checks for the Goal 015, 016, and 017 compact inputs;
- CSV parse checks for all Goal 018 decision outputs;
- `git diff --check`;
- trailing-whitespace scan over Goal 018 files;
- marker scan for final-claim or manuscript language;
- staged path list and staged diff check;
- commit and push if all gates pass.

## Stop Points

Stop and wake Galaxias before:

- running any remote audit or reading raw matched outcomes;
- creating figures, display tables, captions, manuscript prose, public-facing
  wording, or final attribution claims;
- changing prior summary or audit outputs;
- changing production code or contracts;
- staging files outside the allowed Goal 018 docs/decision-table surface;
- proceeding if the compact evidence contradicts the starting Galaxias
  synthesis decisions.

## Completion Condition

Goal 018 is complete when:

- the compact evidence stack has been synthesized into a clear internal
  decision record;
- future artefact needs are listed only as design recommendations;
- no manuscript or final-claim artefacts are created;
- allowed Goal 018 files are committed and pushed;
- `pedder` wakes Galaxias and waits.
