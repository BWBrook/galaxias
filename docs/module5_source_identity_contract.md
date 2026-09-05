# Module 5 Source-Context Identity Contract

## Current State And Non-Claims

This contract applies to Module 5 seeds,
matched-pair IDs, run IDs, matched-outcome rows, provenance, and disk
inspection.

The fixed Goal 006 dry-run implementation has been retired. The general
matched-pair and shared four-arm runners use this identity contract and the
common checks in `src/galaxias_model/module5_output_checks.py`.

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

Current runner provenance records:

- `source_identity_fields`
- `source_identity_strategy`
- `selected_proposal_source_keys`
- seed derivation over `proposal_source_key`

## Seed And Pair Identity Rule

The general matched-pair runner derives stochastic seeds from:

```text
base_label|proposal_source_key|intervention_id|stochastic_replicate_id
```

The baseline and intervention arms keep common-random-number pairing by using
the same stochastic seed inside each matched pair.

The shared four-arm runner instead derives one seed per source-replicate block:

```text
base_label|proposal_source_key|stochastic_replicate_id
```

It runs status quo once and starts all three removal arms from that seed.
Each runner supplies its own frozen seed label. Equal starting seeds do not
guarantee identical event-level random shocks after trajectories diverge.

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

The common `source_identity` check fails if:

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

Uncertainty summaries also require `proposal_source_key`; they never fall back
to pooling all proposals under the same intervention ID.

## Local Verification

The current real-source test exercises sampled parameter loading, matched-pair
execution, provenance and disk inspection with one source and two replicates.
The ordinary Module 5 smoke command uses default parameters. Both are plumbing
checks; scientific interpretation rests on the recorded production evidence.
