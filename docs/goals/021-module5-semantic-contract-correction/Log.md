# Goal 021 Log

## Delegation State

- Baseline branch: `main`
- Baseline SHA: `8838db8ef8aca7ad2374cb9c726e6f2966fbd8a2`
- Baseline status: clean and synchronized with `origin/main`
- Publish boundary: no staging, commit, or push
- Remote boundary: no remote access or production rerun

## Progress

Goal 021 implementation is complete and remains unstaged and uncommitted for
Galaxias review.

## Baseline Confirmation

- Working directory: `/Users/bwbrook/papers/galaxias`
- Branch: `main`
- HEAD: `8838db8ef8aca7ad2374cb9c726e6f2966fbd8a2`
- Initial status: synchronized `main...origin/main` plus the untracked Goal 021
  packet only.
- No remote access or production execution occurred.

## RED-First Evidence

The initial focused contract slice failed in exactly the three new semantic
assertions:

```text
3 failed, 8 passed
```

- active schema had 53 rather than 50 rows;
- execution status was `module5_25rep_rehearsal`;
- default compact summaries still included `detection_summary_contrast`.

## Semantic Decisions

- Deleted `detection_summary_baseline`,
  `detection_summary_counterfactual`, and `detection_summary_contrast` from the
  active output builder, schema, validator, summary defaults, and focused test
  fixtures.
- Deleted the now-unused `_detection_proxy` helper rather than retaining a
  compatibility path.
- Filtered only `detection_summary_contrast` rows from the three committed
  compact summary tables.
- Recorded in summary metadata and current review memos that the immutable
  Goal 014 raw fields are a fixed `N_total(2002) * 0.01` abundance proxy, not
  an observation-model projection, and are excluded from scientific review.
- Changed execution status to
  `module5_matched_counterfactual_execution`; module and boundary prose are
  replicate-neutral while `production_attribution=false` remains enforced.
- Preserved `REHEARSAL_SEED_BASE_LABEL` exactly. A proposed neutral seed-label
  change was rejected during the focused self-review because it would alter
  the stochastic stream rather than merely correct provenance.
- Kept historical rehearsal filenames and APIs unchanged, as required.

## Compact Summary Facts

- active schema rows: 50;
- contrast endpoints: 5;
- `partition_endpoint_summary.csv`: 65 rows;
- `source_intervention_endpoint_summary.csv`: 13,975 rows;
- `direction_summary.csv`: 65 rows;
- metadata row counts match the CSVs;
- all three compact tables contain the same five endpoint values and no
  `detection_summary_contrast` rows.

## Protected Evidence

- Frozen Goal 014 raw outputs, checksums, and execution report were not read or
  changed.
- Accepted Goal 018 synthesis evidence tables, Goal 019 scientific design
  tables other than the explicitly allowed dependency row-count reference,
  and all Goal 020 packet tables are byte-for-byte unchanged from the delegated
  baseline.
- The accepted three-endpoint bundle remains
  `persistence_2002_contrast`, `min_abundance_1992_2002_contrast`, and
  `lake_refuge_share_2002_contrast`.
- Source identity, matched-pair identity, common-random-number seed pairing,
  replicate coverage, partition definitions, and schema ordering remain
  enforced.

## Validation

- RED-first focused slice: `3 failed, 8 passed` for the intended semantic
  assertions.
- Final required focused slice: `18 passed`.
- `uv run python scripts/validate_module5_counterfactual_contract.py`: passed.
- `make fast-check`: portability passed for 305 git-managed files, compileall
  passed, and pytest reported `90 passed, 5 deselected`.
- Structured compact-summary parse: schema 50 rows; summary counts
  65 / 13,975 / 65; five endpoints; metadata counts matched.
- Protected-table hash comparison: no changes outside the explicitly allowed
  Goal 019 dependency row-count reference.
- `git diff --check`: passed before final logging and will be repeated in the
  final diff gate.

## Deviations And Residual Risk

- No deviations from the remote, execution, publication, or historical-record
  boundaries.
- The committed compact summaries remain derived from the immutable 53-column
  Goal 014 raw artifact; metadata now distinguishes that historical raw width
  from the 50-column active schema and explicitly excludes the three proxy
  fields.
- Historical Goal 001-020 packets and frozen execution reports still contain
  their original labels and field descriptions by design. Current active and
  interpretive surfaces are corrected.
