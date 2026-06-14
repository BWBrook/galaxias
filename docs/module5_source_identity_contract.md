# Module 5 Source-Context Identity Contract

## Current State And Non-Claims

Goal 011 implements the local Module 5 source-context identity contract needed
before any production execution packet. This contract applies to seeds,
matched-pair IDs, run IDs, matched-outcome rows, provenance, and disk
inspection.

This note does not authorise a 25-replicate rehearsal, the 279,500-row
production execution, remote commands, production attribution claims,
manuscript claims, publication, staging, commit, push, or a PR.

## Why Bare `proposal_id` Is Unsafe

The accepted-frontier source table is
`data/module4_5_proposal_set_membership.csv`. For the accepted-frontier
families it has:

- 750 accepted source rows;
- 246 unique bare `proposal_id` values;
- 158 repeated bare `proposal_id` values;
- maximum bare-ID reuse of 7 rows;
- 750 unique source-context tuples under the Goal 011 identity fields.

Therefore `proposal_id` is not a production identity by itself. It is unique
only inside a source context.

## Canonical Source Identity

The canonical Module 5 source key is `proposal_source_key`:

```text
module4_run_id|variant_id|seed|run_dir_name|family_id|proposal_id
```

The required fields are:

- `module4_run_id`
- `variant_id`
- `seed`
- `run_dir_name`
- `family_id`
- `proposal_id`

The key is deterministic, row-order independent, and does not rely on CSV row
number, DataFrame index, or sorting.

## Output And Provenance Contract

Matched outcomes now carry these source-identity columns:

- `proposal_source_key`
- `module4_run_id`
- `run_dir_name`
- existing `variant_id`, `seed`, `family_id`, and `proposal_id`

The outcome schema now treats `proposal_id` as source-context scoped rather
than globally unique.

Real-proposal dry-run provenance records:

- `source_identity_fields`
- `source_identity_strategy`
- `selected_proposal_source_keys`
- `selected_proposal_source_rows`
- seed derivation over `proposal_source_key`

## Seed And Pair Identity Rule

Module 5 stochastic seeds are derived from:

```text
base_label|proposal_source_key|intervention_id|stochastic_replicate_id
```

The baseline and intervention arms keep common-random-number pairing by using
the same stochastic seed inside each matched pair.

Matched-pair IDs use:

```text
<proposal_source_key>|<intervention_id>|r<stochastic_replicate_id>
```

Run IDs are:

```text
<matched_pair_id>|baseline
<matched_pair_id>|counterfactual
```

Distinct source rows with the same bare `proposal_id` now produce distinct
source keys, stochastic seeds, matched-pair IDs, and run IDs.

## Disk Inspection Contract

The real-proposal dry-run inspector now includes a `source_identity` check. It
fails if:

- required source-identity columns are missing;
- `proposal_source_key` is blank;
- `proposal_source_key` is inconsistent with visible source-context fields;
- any `(proposal_source_key, intervention_id, stochastic_replicate_id)` grain
  is duplicated;
- provenance source keys or identity fields disagree with the matched-output
  rows.

The matched-pair check also verifies that `matched_pair_id`,
`run_id_baseline`, and `run_id_counterfactual` have the expected
source-context shapes.

## Validated Local Shape

The current local real-proposal dry run remains a plumbing and inspection
check only:

- five approved `family_winners` proposal rows;
- all 13 current intervention rows;
- 5 replicates per intervention row;
- 65 matched-output rows;
- zero seed mismatches expected;
- `production_attribution` remains `false`.

Generated validation outputs remain ignored under:

```text
outputs/module5_dry_run_baseline_current_20260410/
```

## Remaining Boundary

Goal 011 removes the source-identity collision risk for the current local dry
run and the next production implementation surface. It does not start
production attribution, choose a new proposal sample, alter family weighting,
change pressure-removal semantics, or authorise remote execution.

The next production or rehearsal packet should explicitly choose the run
shape, target, partitioning, artifact policy, and source-key-aware restart
rules before any production-sized work begins.
