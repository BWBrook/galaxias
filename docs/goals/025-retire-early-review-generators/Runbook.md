# Goal 025 Runbook

## Baseline

Stop unless the repository is clean `main` at
`69976e2dce3317d047b0272b7f892da614606d09` plus this untracked packet.

## Allowed Paths

- `src/galaxias_model/review.py`
- `scripts/review_module1_5_examples.py` (delete)
- `scripts/review_module2_readiness.py` (delete)
- `scripts/review_module2_5_readiness.py` (delete)
- `docs/module1_5_review.md` (delete)
- `docs/module2_readiness_review.md` (delete)
- `docs/module2_5_readiness_review.md` (delete)
- `data/module2_5_default_bundle_scores.csv` (delete)
- `data/module2_5_transient_bundle_scores.csv` (delete)
- `tests/test_observation_scoring.py`
- `tests/test_module2_5_scenario_bundle.py`
- `data/README.md`
- `docs/goals/025-retire-early-review-generators/Log.md`

Do not edit Module 3/3.5 scripts, tests, tracked outputs, or the protected CSVs.

## Protected Checkpoints

Record baseline and final SHA-256 values for:

```text
data/module1_5_example_summary.csv
data/module1_5_stochastic_summary.csv
data/module2_default_target_scores.csv
data/module2_transient_replicate_scores.csv
```

## Validation

```bash
uv run pytest \
  tests/test_latent_kernel.py \
  tests/test_observation_scoring.py \
  tests/test_module2_5_scenario_bundle.py -q
uv run pytest tests/test_module3_calibration.py -m "not slow" -q
uv run pytest \
  tests/test_module3_calibration.py::test_module3_readiness_review_runs_with_small_override \
  tests/test_module3_calibration.py::test_module3_5_diagnostic_review_runs_with_small_override -q
make fast-check
git diff --check
```

Run the two slow retained-review tests once. Do not run review-generation
scripts or regenerate tracked artifacts.

Also confirm:

- all four checkpoint hashes match the baseline;
- no current code, test, Make target, or current data documentation references
  a deleted early writer or wrapper;
- Module 3/3.5 functions and wrappers remain callable;
- no compatibility or replacement reporting layer was added.

## Stop Conditions

Stop rather than changing scientific semantics, updating checkpoint values,
editing retained Module 3/3.5 behavior, splitting `review.py`, broadening into
other cleanup, running remote work, or staging/committing/pushing.

After one focused review, make at most one material repair pass.

## Report

Report branch, HEAD, status, exact paths, removed functions and tests, retained
scientific flow, checkpoint hashes, all validation, deviations, and residual
risks. Send a wake-up to the parent on completion or blockage.
