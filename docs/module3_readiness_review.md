# Module 3 Readiness Review

## Summary

Module 3 adds the first full two-stage ABC/history-matching calibration harness on top of the validated latent kernel and the Module 2.5 bundle scorer.
Stage A screens equal proposal budgets across all five hypothesis families using deterministic scenario bundles, while Stage B confirms retained proposals against stochastic historical replicates with deterministic baselines.

## Acceptance Gates

| gate | status |
| --- | --- |
| sampler_valid_rate_pass | FAIL |
| screen_discrimination_pass | PASS |
| stochastic_confirmation_finite_pass | PASS |
| rank_consistency_pass | PASS |
| accepted_set_nonempty_pass | PASS |
| reproducibility_pass | PASS |
| full_ready_for_module4 | FAIL |
| needs_module_3_5 | PASS |

## Family Summary

| family_id | stage_a_valid_rate | stage_a_retained | stage_b_valid | final_accepted | final_acceptance_rate |
| --- | --- | --- | --- | --- | --- |
| climbing_only | 0.500 | 20 | 20 | 10 | 0.040 |
| habitat_only_null | 0.688 | 20 | 20 | 0 | 0.000 |
| persistent_joint_cause | 0.424 | 20 | 20 | 0 | 0.000 |
| transient_perfect_storm | 0.416 | 20 | 20 | 0 | 0.000 |
| trout_only | 0.604 | 20 | 20 | 0 | 0.000 |

## Screen Discrimination

| family_id | retained_median | rejected_median | pass |
| --- | --- | --- | --- |
| habitat_only_null | 609.623 | 1765.390 | PASS |
| trout_only | 564.336 | 1374.558 | PASS |
| climbing_only | 301.005 | 1008.239 | PASS |
| persistent_joint_cause | 350.588 | 1075.909 | PASS |
| transient_perfect_storm | 371.156 | 1125.896 | PASS |

## Rank Consistency

| family_id | spearman_rank_correlation | pass |
| --- | --- | --- |
| habitat_only_null | 0.980 | PASS |
| trout_only | 0.869 | PASS |
| climbing_only | 0.916 | PASS |
| persistent_joint_cause | 0.576 | PASS |
| transient_perfect_storm | 0.233 | FAIL |

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
| climbing_only:p00128 | climbing_only | 2655917679 | 194.449 | 188.970 | 5.479 | 22.916 |
| climbing_only:p00149 | climbing_only | 250829610 | 243.567 | 238.613 | 4.954 | 10.748 |
| climbing_only:p00143 | climbing_only | 4005831409 | 254.213 | 250.002 | 4.211 | 11.544 |
| climbing_only:p00160 | climbing_only | 2672422109 | 257.025 | 252.926 | 4.100 | 6.020 |
| climbing_only:p00204 | climbing_only | 3768857523 | 263.721 | 259.555 | 4.166 | 76.090 |
| climbing_only:p00129 | climbing_only | 1314256164 | 269.144 | 265.344 | 3.800 | 30.227 |
| climbing_only:p00009 | climbing_only | 3399848197 | 272.273 | 265.775 | 6.498 | 12.194 |
| climbing_only:p00011 | climbing_only | 716525167 | 272.772 | 268.721 | 4.051 | 33.809 |
| climbing_only:p00139 | climbing_only | 782542887 | 289.170 | 284.353 | 4.818 | 52.738 |
| climbing_only:p00206 | climbing_only | 1085534493 | 291.047 | 286.921 | 4.126 | 18.826 |

## Interpretation

Module 4 should not start yet.
The correct next step is Module 3.5 because at least one calibration-harness readiness gate failed.

## Module 3.5 Trigger

- Trigger a sampler/constraint realignment pass if valid-rate failures or pre-simulation proposal failures dominate.
- Trigger a Stage A to Stage B handoff refinement pass if rank consistency is weak or stochastic confirmation is numerically unstable.
- Trigger a reproducibility repair pass if accepted proposal ids differ under the same seed or across worker counts.

## Artifacts

- `data/module3_readiness_family_summary.csv`
- `data/module3_readiness_accepted_summary.csv`
- `docs/module3_readiness_review.md`
