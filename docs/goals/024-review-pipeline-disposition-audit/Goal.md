# Goal 024: Review Pipeline Disposition Audit

## Objective

Decide which parts of the 2,023-line `src/galaxias_model/review.py` still earn
their maintenance cost before any refactor or deletion is attempted.

## Product Promise

The repository should retain review machinery only when it supports a current
workflow, produces evidence still used for scientific decisions, or detects a
distinct consequential failure. File size alone is not a reason to preserve,
split, or delete code.

## Required Outcomes

1. Trace the direct callers, tests, outputs, and current documentation role for
   the Module 1.5, 2, 2.5, 3, and 3.5 review subsystems.
2. Identify the scientific or reproducibility decision each subsystem protects
   today, if any.
3. Classify each subsystem and shared helper as `retain`, `simplify`, `delete`,
   or `defer`, with evidence.
4. Distinguish valuable computational checks from obsolete report rendering,
   bundle writing, historical entrypoints, and duplicated test coverage.
5. Recommend one bounded implementation tranche with an exact proposed scope,
   protected invariants, and proportional validation.
6. Produce one concise decision memo at
   `docs/review_pipeline_disposition_audit.md`.

## Non-Goals

- No production-code, script, test, data, or generated-output changes.
- No automatic split of `review.py` into modules.
- No compatibility wrappers, public API preservation work, generic review
  framework, or speculative replacement design.
- No simulations, review-bundle generation, remote access, staging, commit, or
  push.
- No audit of Module 4.5 or Module 5 interpretation code outside direct
  comparison needed to establish current ownership.

## Completion Standard

The memo provides a mechanically grounded call map and assertive disposition
for all five subsystems, identifies the smallest high-value next deletion or
simplification tranche, and states material uncertainty. Stop after one
integration review; do not polish prose or enumerate hypothetical futures.
