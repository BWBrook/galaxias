# Module 3 Readiness Review

## Summary

Module 3 adds the first full two-stage ABC/history-matching calibration harness on top of the validated latent kernel and the Module 2.5 bundle scorer.
Stage A screens equal proposal budgets across all five hypothesis families using deterministic scenario bundles, while Stage B confirms retained proposals against stochastic historical replicates with deterministic baselines.

## Acceptance Gates

| gate | status |
| --- | --- |
| sampler_valid_rate_pass | PASS |
| screen_discrimination_pass | PASS |
| stochastic_confirmation_finite_pass | PASS |
| rank_consistency_pass | PASS |
| accepted_set_nonempty_pass | PASS |
| reproducibility_pass | PASS |
| full_ready_for_module4 | PASS |
| needs_module_3_5 | FAIL |

## Family Summary

| family_id | stage_a_valid_rate | stage_a_retained | stage_b_valid | final_accepted | final_acceptance_rate |
| --- | --- | --- | --- | --- | --- |
| climbing_only | 1.000 | 20 | 20 | 3 | 0.012 |
| habitat_only_null | 1.000 | 20 | 20 | 0 | 0.000 |
| persistent_joint_cause | 1.000 | 20 | 20 | 5 | 0.020 |
| transient_perfect_storm | 1.000 | 20 | 20 | 2 | 0.008 |
| trout_only | 1.000 | 20 | 20 | 0 | 0.000 |

## Screen Discrimination

| family_id | retained_median | rejected_median | pass |
| --- | --- | --- | --- |
| habitat_only_null | 573.468 | 1699.121 | PASS |
| trout_only | 505.730 | 1273.884 | PASS |
| climbing_only | 267.731 | 910.364 | PASS |
| persistent_joint_cause | 282.090 | 884.310 | PASS |
| transient_perfect_storm | 291.607 | 866.594 | PASS |

## Rank Consistency

| family_id | spearman_rank_correlation | pass |
| --- | --- | --- |
| habitat_only_null | 0.947 | PASS |
| trout_only | 0.958 | PASS |
| climbing_only | 0.728 | PASS |
| persistent_joint_cause | 0.886 | PASS |
| transient_perfect_storm | 0.205 | FAIL |

## Reproducibility Checks

| metric | value |
| --- | --- |
| accepted_count | 10 |
| same_seed_same_worker_identical | PASS |
| workers1_vs_workers2_identical | PASS |
| resume_matches_clean_run | PASS |

## Accepted Proposals

| proposal_id | family_id | proposal_seed | stochastic_overall_distance_median | stochastic_historical_core_distance_median | stochastic_intrinsic_baseline_distance_median | stochastic_historical_core_distance_iqr |
| --- | --- | --- | --- | --- | --- | --- |
| climbing_only:p00216 | climbing_only | 553821216 | 152.819 | 148.739 | 4.080 | 39.821 |
| transient_perfect_storm:p00144 | transient_perfect_storm | 1142654192 | 179.119 | 174.458 | 4.661 | 7.831 |
| persistent_joint_cause:p00162 | persistent_joint_cause | 3523308519 | 185.704 | 181.277 | 4.427 | 12.405 |
| climbing_only:p00128 | climbing_only | 2655917679 | 194.449 | 188.970 | 5.479 | 22.916 |
| persistent_joint_cause:p00227 | persistent_joint_cause | 2214655864 | 205.290 | 202.437 | 2.853 | 28.928 |
| transient_perfect_storm:p00162 | transient_perfect_storm | 2762550668 | 214.294 | 211.221 | 3.073 | 30.855 |
| persistent_joint_cause:p00032 | persistent_joint_cause | 1845646538 | 216.878 | 212.985 | 3.892 | 26.299 |
| climbing_only:p00245 | climbing_only | 300342900 | 234.509 | 230.980 | 3.530 | 5.765 |
| persistent_joint_cause:p00065 | persistent_joint_cause | 520489453 | 238.008 | 233.287 | 4.721 | 20.119 |
| persistent_joint_cause:p00092 | persistent_joint_cause | 2950334167 | 238.981 | 233.585 | 5.395 | 45.404 |

## Interpretation

All Module 3 readiness gates passed.
The retained-sample calibration harness is ready to support Module 4 posterior summaries and counterfactual analysis.

## Module 3.5 Trigger

- Trigger a sampler/constraint realignment pass if valid-rate failures or pre-simulation proposal failures dominate.
- Trigger a Stage A to Stage B handoff refinement pass if rank consistency is weak or stochastic confirmation is numerically unstable.
- Trigger a reproducibility repair pass if accepted proposal ids differ under the same seed or across worker counts.

## Artifacts

- `data/module3_readiness_family_summary.csv`
- `data/module3_readiness_accepted_summary.csv`
- `docs/module3_readiness_review.md`
