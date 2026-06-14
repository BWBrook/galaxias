# Goal: Module 5 Targeted Source/Intervention Audit

## Objective

Perform a targeted, read-only audit of selected Module 5 production
source/intervention units from the Goal 016 audit-target list.

This goal should pressure-test the endpoint bundle recommended by Goal 016
against raw replicate distributions while keeping the full matched outcomes
remote-only. It should decide whether the compact-summary interpretation gate
is source-level audit ready, not draft manuscript prose or final attribution
claims.

## Source Inputs

Use the committed Goal 016 audit targets:

```text
data/module5_interpretation_audits/source_intervention_audit_targets.csv
data/module5_interpretation_audits/endpoint_priority_matrix.csv
data/module5_interpretation_audits/wording_boundary_matrix.csv
docs/module5_interpretation_gate_review.md
```

Use the committed compact summaries for context:

```text
data/module5_production_summaries/
docs/module5_production_summary_review.md
```

Use the Goal 014 production artifact as the raw-row source, read-only:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production
```

Expected raw matched-output facts:

- file:
  `/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/matched_outcomes.csv`
- SHA-256:
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`
- size: `435867556` bytes
- row count: `279500`
- source/intervention units: `2795`
- expected replicates: `100`

## Audit Target Set

Audit these Goal 016 target IDs:

- `A01`
- `A02`
- `A03`
- `A04`
- `A05`
- `A10`

Rationale:

- `A01` to `A05` cover the primary persistent-joint-cause endpoint bundle:
  target-year persistence, abundance magnitude, lake-refuge support, and the
  primary no-trout negative subset.
- `A10` resolves the transient-perfect-storm no-trout negative persistence
  subset before sensitivity language hardens.

Do not audit `A06` to `A09` unless the selected targets reveal a problem that
requires sensitivity comparator expansion. Do not audit `A11` to `A14` unless
Galaxias authorizes an iteration.

## Scope

In scope:

- Verify the pushed Goal 016 audit-target files.
- Verify the Goal 014 remote artifact checksum manifest before reading raw
  rows.
- Read the raw matched outcomes on `deep-server-ts` only.
- Extract compact replicate-distribution summaries for selected audit targets.
- For source-specific targets, audit the exact `proposal_source_key`,
  `intervention_id`, and endpoint.
- For aggregate negative-subset targets (`A03`, `A10`), identify compact
  source-level rows with negative persistence minima, then summarize only the
  selected source/intervention units needed to characterize that subset.
- Pull back only compact audit CSV/JSON/Markdown files.
- Produce a memo that says whether the Goal 016 endpoint bundle and audit
  boundaries survive this targeted raw-row check.
- Commit and push the Goal 017 packet, compact audit outputs, and memo if all
  checks pass.

Out of scope:

- No production rerun, new simulation, or new counterfactual execution.
- No local copy of `matched_outcomes.csv`.
- No broad scan beyond the selected target set except as needed to select the
  negative-subset source rows for `A03` and `A10`.
- No changes to production code, contracts, interventions, pressure semantics,
  proposal selection, family weighting, diagnostic ordering, or Goal 015/016
  summaries.
- No manuscript prose, figures, display tables, captions, abstract,
  supplement, public-facing wording, or final causal claims.
- No PR creation.
- No force-push, amend, rebase, reset, or destructive cleanup.
- Do not read `/Users/bwbrook/chief_of_staff` or
  `/Users/bwbrook/work/goal_composer`.

## Required Outputs

Create:

```text
docs/module5_targeted_source_intervention_audit.md
```

Create compact audit outputs under:

```text
data/module5_source_intervention_audits/
```

Required files:

- `audit_metadata.json`
- `selected_audit_targets.csv`
- `replicate_distribution_summary.csv`
- `negative_subset_sources.csv`

No output file should contain all raw matched rows, all production rows, or
unbounded replicate-level production extracts. Keep compact outputs below
20 MB each.

## Audit Requirements

For each selected target, report:

- `audit_id`;
- partition;
- family;
- intervention ID;
- endpoint;
- proposal source key or aggregate target flag;
- number of source/intervention units audited;
- number of replicate rows summarized;
- replicate ID coverage;
- endpoint minimum, median, mean, maximum, and selected quantiles;
- count and proportion of negative, zero, and positive endpoint values;
- whether the raw-row replicate distribution is consistent with the Goal 016
  compact-summary description;
- whether this target should be carried into the next interpretation review.

For `A03` and `A10`, include a compact source list for the negative persistence
subset. Limit the source list to the most informative rows, ordered by
negative count and then by endpoint minimum. Record how many negative-subset
sources exist in total.

## Memo Requirements

The memo should include:

- boundary statement;
- remote artifact and checksum verification;
- selected target list and rationale;
- source-specific audit findings for `A01`, `A02`, `A04`, and `A05`;
- negative-subset audit findings for `A03` and `A10`;
- whether the Goal 016 endpoint bundle remains the right next review burden;
- whether `extirpation_year_contrast` should remain audit-only or become a
  secondary review endpoint;
- whether any target changes the sensitivity/diagnostic treatment recommended
  by Goal 016;
- remaining questions for Galaxias/Barry;
- recommended Goal 018 shape.

Use provisional language. Do not write results-section prose.

Allowed language:

- "replicate-distribution audit"
- "source-level check"
- "consistent with compact summary"
- "audit supports carrying this endpoint into review"
- "requires further review"
- "not yet manuscript-ready"

Avoid final-claim language:

- "caused"
- "demonstrates"
- "proves"
- "the effect is"
- "the result shows"
- "manuscript result"
- "publication-ready"
- "final attribution"

## Validation

Run and log:

- starting repo state guard;
- Goal 016 audit-target parse check;
- remote checksum verification on `deep-server-ts`;
- remote compact audit command and exit status;
- local parse checks for all Goal 017 audit outputs;
- file-size check confirming compact outputs are each below 20 MB;
- `git diff --check`;
- trailing-whitespace scan over Goal 017 files;
- marker scan for final-claim language;
- staged path list and staged diff check;
- commit and push if all gates pass.

## Stop Points

Stop and wake Galaxias before:

- pulling `matched_outcomes.csv` or broad raw production extracts into the
  local repo;
- auditing beyond `A01` to `A05` and `A10`;
- creating figures, display tables, captions, manuscript prose, public-facing
  wording, or final attribution claims;
- changing production code, contracts, summaries, interventions, or pressure
  semantics;
- staging files outside the allowed Goal 017 docs/audit surface;
- proceeding if remote checksum verification fails;
- proceeding if selected raw-row audit facts contradict Goal 016 compact
  summaries in a material way.

## Completion Condition

Goal 017 is complete when:

- selected raw-row replicate distributions have been audited remotely;
- only compact audit outputs are pulled back;
- the audit memo states whether Goal 016 endpoint priorities survive the
  targeted source/intervention check;
- no manuscript or final-claim artefacts are created;
- allowed Goal 017 files are committed and pushed;
- `pedder` wakes Galaxias and waits.
