# Goal 024 Runbook

## Baseline

Stop unless the repository is clean `main` at
`f1fb7f72c33ef609ff239128ae8d6e33c236ee16` plus this untracked packet.

## Evidence Surface

Read only:

- `src/galaxias_model/review.py`
- its direct imports and callers under `scripts/`, `tests/`, and `src/`
- relevant Makefile targets, README references, and tracked review documents
- Git history only where current intent cannot be established from the tree

Do not run review entrypoints or simulations. Static call mapping and existing
tests/docs are sufficient for this disposition decision.

## Allowed Writes

- `docs/review_pipeline_disposition_audit.md`
- `docs/goals/024-review-pipeline-disposition-audit/Log.md`

## Required Memo Shape

- one-sentence current product promise;
- concise active-flow map;
- per-subsystem caller/output/test/scientific-value evidence;
- retain/simplify/delete/defer decisions;
- shared-helper and duplicate-coverage findings;
- smallest recommended action tranche;
- protected invariants, proportional gate, stopping point, and residual risk.

## Validation

```bash
git diff --check
rg -n "[ \t]+$" \
  docs/goals/024-review-pipeline-disposition-audit \
  docs/review_pipeline_disposition_audit.md
```

Review every concrete caller claim against repository search evidence.

## Stop Conditions

Stop rather than editing code, generating review bundles, preserving obsolete
APIs, designing a replacement framework, broadening into Module 4.5/5 science,
or staging/committing/pushing. One integration review is enough.
