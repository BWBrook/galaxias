# Review Pipeline Disposition Audit

## Decision

The current product promise of the review layer is to protect consequential
model and calibration transitions with explicit gates, not to regenerate every
historical report indefinitely.

`src/galaxias_model/review.py` is large for two different reasons. Its first
half retains superseded Module 1.5, 2, and 2.5 report pipelines whose scientific
checks now live in focused tests and lower-level model code. Its second half
contains Module 3 calibration-readiness and Module 3.5 target-sensitivity
checks that remain scientifically distinct. A mechanical file split would
preserve both kinds of complexity and is therefore the wrong next move.

## Active Flow

The current simulation and inference path does not import the review layer:

```text
canonical data -> simulation/scoring -> calibration -> Module 4/4.5
               -> Module 5 counterfactual execution and inspection
```

`review.py` is reached only through five dedicated review scripts and a small
number of tests. Among those five `review.py` wrappers, only Module 3.5 has a
Make target; the separate Module 3.75 wrapper also has one but is implemented
outside this module. The tracked CSV and Markdown bundles are historical
decision receipts, not inputs to Module 4.5 or Module 5. Two early CSV bundles
are still used as regression fixtures by tests.

## Dispositions

### Module 1.5: delete review machinery; retain regression fixtures

The subsystem runs deterministic defaults for five families and 20 stochastic
transient-perfect-storm seeds, then renders and writes two CSVs and a review
document. Its chronology, boom, persistence, and reproducibility conditions
are already exercised directly in `tests/test_latent_kernel.py`.

No current command or test calls the Module 1.5 writer. The two tracked CSVs
remain useful regression fixtures in `tests/test_module2_5_scenario_bundle.py`,
but that does not justify retaining a second report-generation path.

Disposition: delete the runner, renderer, writer, CLI wrapper, and stale review
document. Retain the two CSV checkpoints as canonical regression fixtures and
describe them that way.

### Module 2: delete review machinery; retain scoring tests and fixtures

The subsystem reruns all five deterministic families, 20 stochastic replicates,
synthetic monotonicity probes for CT006-CT010, and a same-seed check before
writing two CSVs and a review document. The same consequential scoring behavior
is covered more directly in `tests/test_observation_scoring.py`, including all
target types, monotonicity, observation-bridge variants, reproducibility, and
finite aggregation.

The only current caller is the thin CLI, and the only direct writer test checks
that files and document markers exist. The two CSVs remain regression inputs
for Module 2.5 tests.

Disposition: delete the review runner, renderer, writer, CLI wrapper, and stale
review document. Remove the redundant writer/Markdown existence test. Retain
the CSV checkpoints and the direct scoring tests.

### Module 2.5: delete review machinery; retain scenario tests and fixtures

The subsystem combines historical, Lake Oberon, and Strathgordon scenarios,
checks 20 stochastic bundles, compares against Module 2 checkpoints, and
writes two CSVs and a review document. The underlying scenario definitions,
bundle aggregation, regression checkpoints, and readiness flags are already
tested directly in `tests/test_module2_5_scenario_bundle.py`.

Its optional stochastic baseline smoke is recorded as a metric but is not a
readiness gate. The direct writer test again proves file existence and document
markers rather than a distinct scientific failure.

Disposition: delete the review runner, renderer, writer, CLI wrapper, and stale
review document. Remove the redundant writer test. Retain the two CSV
checkpoints and the direct scenario/scoring tests.

### Module 3: retain, then simplify separately

The readiness subsystem performs a primary calibration plus repeat, worker,
and resume comparisons. Its gates cover sampler validity, Stage A
discrimination, finite stochastic confirmation, deterministic/stochastic rank
consistency, complete accepted-target scoring, and reproducibility.

These are scientifically consequential calibration-harness checks. They are
also expensive and partly duplicate the dedicated serial/parallel and
resume/clean integration tests. The wrapper has no Make target, and its tracked
outputs are historical readiness receipts.

Disposition: retain for now. A later calibration-focused tranche should decide
whether the six-run orchestrator can be reduced to one primary run plus the
two existing integration tests. Do not mix that decision with early-module
deletion.

### Module 3.5: retain

This subsystem produces sampler diagnostics, Stage B frontier and family-best
tables, target leverage, accepted/best-proposal penalties, and target-omission
sensitivity. The tracked result contains three target-omission ranking flips.
That is a material warning against treating the current family ranking as
target-independent.

The subsystem has a live `make module3-5` entrypoint and a slow integration
test. Its scientific role has not been superseded by the Module 5 execution.

Disposition: retain. Revisit its execution and rendering only when Module 6
robustness work is designed.

### Shared helpers

Retain `_format_value` and `_markdown_table` because the Module 3 and 3.5
renderers use them. Delete `_regression_frames_match` with Module 2.5 if it has
no remaining caller. Clean imports after the early subsystems are removed; do
not add a generic report framework.

## Recommended Action Tranche

The next implementation goal should retire the Module 1.5, 2, and 2.5 review
generation surface only:

- remove their functions from `review.py`;
- delete their three CLI wrappers and three stale Markdown review documents;
- remove only the two writer-existence tests;
- keep all six CSV checkpoints used by regression tests;
- update current data documentation to call those CSVs canonical regression
  fixtures rather than generated products;
- preserve all direct latent-kernel, scoring, scenario, and checkpoint tests;
- leave Module 3 and 3.5 code, scripts, outputs, and scientific semantics
  untouched.

This should remove roughly the first half of `review.py` plus three thin
wrappers without weakening a current scientific decision boundary.

## Proportional Gate

Run the direct early-module test files, the Module 3 calibration test file to
catch retained-import damage, and one full fast gate. Run the slow Module 3
integration slice once only if imports or shared helpers change. No review
bundle regeneration is needed.

## Stop And Residual Risk

Stop after the early review surface is removed and the retained tests pass.
Do not reorganize Module 3/3.5 merely because the remaining file is still
large.

The main residual risk is that the retained CSV fixtures become stale without
an active generator. That is acceptable if they are treated explicitly as
versioned regression checkpoints: intentional scientific changes should update
them through a reviewed change, while Git preserves their history. The later
Module 3 disposition remains a separate decision because its reproducibility
gates are materially consequential and computationally heavier.
