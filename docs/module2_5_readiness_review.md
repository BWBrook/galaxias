# Module 2.5 Readiness Review

## Summary

Module 2.5 adds explicit `lake_oberon` and `strathgordon` scenarios, then scores all twelve calibration targets through a scenario bundle rather than a single historical run.
The historical path is checked against the tracked Module 2 outputs, while the new baseline scenarios activate `CT011` and `CT012` without introducing new free parameters.

## Acceptance Gates

| gate | status |
| --- | --- |
| historical_default_regression_pass | PASS |
| historical_transient_regression_pass | PASS |
| bundle_all_targets_scored | PASS |
| bundle_no_missing_scenarios | PASS |
| default_bundles_full_ready_for_module3 | PASS |
| transient_bundle_full_ready_for_module3 | PASS |
| aggregate_history_median_and_iqr_finite | True |
| historical_core_ready | PASS |
| full_ready_for_module3 | PASS |
| needs_module_2_75 | FAIL |

## Baseline Target Highlights

| family_id | target_id | scenario_id | evaluation_status | raw_penalty |
| --- | --- | --- | --- | --- |
| climbing_only | CT011 | lake_oberon | scored | 1.397 |
| habitat_only_null | CT011 | lake_oberon | scored | 1.397 |
| persistent_joint_cause | CT011 | lake_oberon | scored | 1.397 |
| transient_perfect_storm | CT011 | lake_oberon | scored | 1.397 |
| trout_only | CT011 | lake_oberon | scored | 1.397 |
| climbing_only | CT012 | strathgordon | scored | 0.022 |
| habitat_only_null | CT012 | strathgordon | scored | 0.022 |
| persistent_joint_cause | CT012 | strathgordon | scored | 0.022 |
| transient_perfect_storm | CT012 | strathgordon | scored | 0.022 |
| trout_only | CT012 | strathgordon | scored | 0.022 |

## Transient Bundle Summary

| metric | value |
| --- | --- |
| historical_core_distance_median | 525.449 |
| historical_core_distance_iqr | 61.584 |
| intrinsic_baseline_distance_median | 4.256 |
| optional_stochastic_baseline_smoke_finite | PASS |

## Interpretation

All bundle targets now score successfully, with no missing scenarios and no deferred targets.
Module 3 can proceed on top of the Module 2.5 bundle-scoring interface.

## Module 2.75 Trigger

- Trigger if `historical_core_ready=False` after scenario enablement, which means the shared kernel/scoring contract regressed.
- Trigger if `historical_core_ready=True` but `full_ready_for_module3=False`, which means the baseline scenarios or their target formulas still need refinement.

## Artifacts

- `data/module2_5_default_bundle_scores.csv`
- `data/module2_5_transient_bundle_scores.csv`
- `docs/module2_5_readiness_review.md`
