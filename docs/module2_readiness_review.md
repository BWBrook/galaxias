# Module 2 Readiness Review

## Summary

Module 2 adds the observation bridge and deterministic target scoring layer for CT001-CT012 without changing the validated latent kernel.
Historical-core targets are now projectable and scoreable from the current `historical_lake` scenario, while the intrinsic-baseline targets remain blocked until Lake Oberon and Strathgordon scenarios are implemented in Module 2.5.

## Acceptance Gates

| gate | status |
| --- | --- |
| deterministic_core_targets_scored | PASS |
| deterministic_core_penalties_finite | PASS |
| ct004_discriminates_trout_active_vs_inactive | PASS |
| ct005_discriminates_climbing_active_vs_inactive | PASS |
| ct006_monotonicity | PASS |
| ct007_monotonicity | PASS |
| ct008_monotonicity | PASS |
| ct009_monotonicity | PASS |
| ct010_monotonicity | PASS |
| replicate_same_seed_stable | PASS |
| transient_replicate_penalties_finite | PASS |
| aggregate_history_median_and_iqr_finite | PASS |
| historical_core_ready | PASS |
| full_ready_for_module3 | FAIL |
| needs_module_2_5 | PASS |

## Target Highlights

| family_id | target_id | evaluation_status | raw_penalty |
| --- | --- | --- | --- |
| climbing_only | CT004 | scored | 1.000 |
| habitat_only_null | CT004 | scored | 1.000 |
| persistent_joint_cause | CT004 | scored | 0.333 |
| transient_perfect_storm | CT004 | scored | 0.000 |
| trout_only | CT004 | scored | 0.000 |
| climbing_only | CT005 | scored | 0.615 |
| habitat_only_null | CT005 | scored | 34.539 |
| persistent_joint_cause | CT005 | scored | 0.110 |
| transient_perfect_storm | CT005 | scored | 0.064 |
| trout_only | CT005 | scored | 34.539 |
| climbing_only | CT011 | deferred_requires_scenario | NA |
| habitat_only_null | CT011 | deferred_requires_scenario | NA |
| persistent_joint_cause | CT011 | deferred_requires_scenario | NA |
| transient_perfect_storm | CT011 | deferred_requires_scenario | NA |
| trout_only | CT011 | deferred_requires_scenario | NA |
| climbing_only | CT012 | deferred_requires_scenario | NA |
| habitat_only_null | CT012 | deferred_requires_scenario | NA |
| persistent_joint_cause | CT012 | deferred_requires_scenario | NA |
| transient_perfect_storm | CT012 | deferred_requires_scenario | NA |
| trout_only | CT012 | deferred_requires_scenario | NA |

## Transient Replicate Summary

| metric | value |
| --- | --- |
| historical_core_distance_median | 525.449 |
| historical_core_distance_iqr | 61.584 |
| deferred_target_ids | CT011;CT012 |
| stochastic_replicate_rows | 240 |

## Interpretation

The historical-core scoring layer passed its readiness gate.
Module 3 should not start yet.
Because `CT011` and `CT012` are still `deferred_requires_scenario` under the current `historical_lake` kernel, the correct next step is Module 2.5.
This is a baseline-scenario enablement problem, not a failure of the historical-core observation bridge.

## Module 2.5 Trigger

- Trigger if `historical_core_ready=False` because the scorer is unstable, non-monotonic, or poorly discriminative.
- Trigger if `historical_core_ready=True` but `full_ready_for_module3=False` because `CT011` and `CT012` remain deferred.
- In the current state, the second trigger applies.

## Artifacts

- `data/module2_default_target_scores.csv`
- `data/module2_transient_replicate_scores.csv`
- `docs/module2_readiness_review.md`
