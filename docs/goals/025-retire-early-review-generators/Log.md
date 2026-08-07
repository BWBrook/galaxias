# Goal 025 Log

## Baseline And Boundary

- Baseline: clean `main` at
  `69976e2dce3317d047b0272b7f892da614606d09` plus this packet.
- Publish boundary: none; leave Goal 025 unstaged and uncommitted.
- Root owns orchestration and acceptance. A native implementation sub-agent
  owns the authorized code/document deletion; a fresh native reviewer will
  inspect the resulting diff.

## Execution Evidence

- Removed the Module 1.5, 2, and 2.5 runners, renderers, writers, and their
  caller-free helpers from `src/galaxias_model/review.py`; retained
  `_format_value`, `_markdown_table`, and the complete Module 3/3.5 tail.
- Deleted the three named CLI wrappers and three stale generated review
  documents.
- Preserved the active `score_historical_run.py` CLI test while removing its
  deleted Module 2 review-writer assertions; removed the Module 2.5
  writer-only test.
- Updated `data/README.md` to identify the four consumed early CSVs as canonical
  regression checkpoints rather than generated review products.
- The Module 3/3.5 tail beginning at `MODULE3_REVIEW_TARGET_IDS` matched the
  baseline byte hash before and after the edit:
  `6d362a7f3c4bc7930b1faf9b27ba90d273a5011e5110ca4b6ac6471d7df4891b`.

## Protected Checkpoint Hashes

Baseline and final SHA-256 values matched:

```text
daccdc0641edcee4c9bd08e5688894d2a64c2f41b74bb8a3ef6e9ab263e89357  data/module1_5_example_summary.csv
66ad01da8a9e0653d25a47e33b2cd08f09691083f5e88dec1b4142bc3dc86311  data/module1_5_stochastic_summary.csv
c191a2bd531e3a7c32a569a44d5b828e65fca9f80d44ae8c2c7a6fbff0da1157  data/module2_default_target_scores.csv
8d55744d39076049822716c9ecbf37b68eb54b9d7039efb113f4a993dbe50ad1  data/module2_transient_replicate_scores.csv
```

## Validation

- Direct early-science suite: `49 passed`.
- Module 3 non-slow suite: `7 passed, 5 deselected`.
- Retained Module 3 and 3.5 review entrypoint tests: `2 passed`.
- Deleted-surface reference scan: no current source, test, script, Make target,
  project configuration, or current data documentation references remain.
- `make fast-check`: blocked in its first `portability` step. The checker
  enumerates paths from the unchanged Git index and then attempts to read the
  six intentionally deleted working-tree files, raising `FileNotFoundError`
  for `docs/module1_5_review.md` first. The no-staging boundary prevents
  reconciling the index for this gate; it was not rerun.
- `git diff --check`: passed.

## Review

- One focused review found and removed only the two imports made unused by the
  deleted Module 2.5 writer test.
- No scientific semantics, protected checkpoints, Module 3/3.5 code, remote
  state, index state, or repository history were changed.

## Authorized Material Repair

- Fresh review proved `data/module2_5_default_bundle_scores.csv` and
  `data/module2_5_transient_bundle_scores.csv` had no live code or test
  consumer. They were orphan writer outputs, not regression checkpoints, so
  both files were deleted rather than preserved without scientific coverage.
- Goal, plan, runbook, log, and current data documentation now protect only the
  four checkpoints consumed by direct Module 1.5 and Module 2 regression tests.
- Direct Module 2.5 scenario tests and all scientific behavior remain intact.
- Repair validation: `tests/test_module2_5_scenario_bundle.py` passed all 13
  tests; `git diff --check` passed.

## Orchestrator Acceptance

- The first native implementer produced no worktree change within the bounded
  interval and did not answer a status nudge, so it was stopped under the
  global delivery policy. A fresh native implementer completed the task.
- Independent review found the two orphan Module 2.5 CSVs above; one material
  repair removed them. Scoped re-review returned `CLEAN`.
- Root reproduced the final-tree release gate with a temporary external Git
  index because the real-index no-staging boundary still lists deleted paths:
  portability passed for 317 files, compilation passed, and pytest reported
  `94 passed, 5 deselected`.
- Root confirmed all four retained checkpoint files are byte-for-byte
  unchanged and found no active reference to the deleted wrappers, writers, or
  orphan Module 2.5 CSVs.
- Final `git diff --check` passed. No further repair or polish pass is needed.
