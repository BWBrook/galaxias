# Goal 025: Retire Early Review Generators

## Objective

Remove the superseded Module 1.5, 2, and 2.5 review-generation machinery while
preserving their canonical numerical regression checkpoints and all direct
scientific tests.

## Product Promise

Early model behavior should be protected by direct latent-kernel, scoring,
scenario, and checkpoint tests, not by three parallel report pipelines whose
only remaining job is to recreate historical CSV and Markdown bundles.

## Required Outcomes

1. Remove the Module 1.5, 2, and 2.5 runners, renderers, writers, and helpers
   used only by those subsystems from `src/galaxias_model/review.py`.
2. Delete their three CLI wrappers:
   - `scripts/review_module1_5_examples.py`;
   - `scripts/review_module2_readiness.py`;
   - `scripts/review_module2_5_readiness.py`.
3. Delete their three stale generated review documents:
   - `docs/module1_5_review.md`;
   - `docs/module2_readiness_review.md`;
   - `docs/module2_5_readiness_review.md`.
4. Remove only the tests that invoke the deleted writer CLIs and assert file or
   Markdown-marker existence.
5. Retain and do not modify the four tracked numerical checkpoint CSVs used by
   current regression tests.
6. Update `data/README.md` to describe those CSVs as canonical regression
   checkpoints rather than generated review products.
7. Remove imports and private helpers made caller-free by this deletion.
8. Preserve Module 3 and 3.5 code, scripts, outputs, tests, gates, and semantics.

## Protected Scientific Invariants

- Direct deterministic and stochastic latent-kernel behavior.
- Historical target projection, scoring monotonicity, observation variants,
  reproducibility, and finite aggregation.
- Lake Pedder, Lake Oberon, and Strathgordon scenario scoring.
- All four numerical regression checkpoint comparisons.
- Module 3 sampler, discrimination, rank, accepted-target, worker, resume, and
  repeat reproducibility gates.
- Module 3.5 target-leverage and omission-sensitivity diagnostics.

## Non-Goals

- No change to simulation, scoring, calibration, scenarios, parameters, the
  four retained checkpoint CSVs, Module 3/3.5 semantics, or later modules.
- No compatibility re-exports, replacement report generator, generic renderer,
  module split, archive, migration, or new provenance layer.
- No regeneration of deleted reports or checkpoint CSVs.
- No remote work, staging, commit, or push.

## Completion Standard

The early review-generation surface, its two orphan Module 2.5 CSV outputs,
and current references are absent; all four consumed checkpoint files are
byte-for-byte unchanged; direct early scientific tests and retained Module
3/3.5 review entrypoints pass. Perform one self-review and at most one material
repair pass.
