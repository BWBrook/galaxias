# Module 1.5 Review

## Summary

Module 1.5 reran the latent kernel after adding count-scale Pedder capacities (`PR039`) and a delayed inundation habitat-transition forcing (`PR040`).
This pass also keeps the post-flood boom interpretable by letting the upsurge temporarily relax lake density pressure and by applying explicit trout/climbing states as lagged annual pressures rather than as an instantaneous 1972 collapse.
The purpose of this bundle is to decide whether the default kernel behavior is stable and qualitatively aligned with the Pedder chronology before Module 2.

## Acceptance Gates

| gate | status |
| --- | --- |
| deterministic_habitat_peak_1975_1978 | PASS |
| deterministic_transient_peak_1975_1978 | PASS |
| deterministic_habitat_boom_ratio_gt_1 | PASS |
| deterministic_transient_boom_ratio_gt_1 | PASS |
| deterministic_transient_final_below_habitat | PASS |
| deterministic_transient_climbing_switch_1980_1984 | PASS |
| stochastic_zero_pre1972_extinctions | PASS |
| stochastic_at_least_18_present_in_1980 | PASS |
| stochastic_median_peak_1975_1978 | PASS |
| overall_ready_for_module2 | PASS |

## Deterministic Default Runs

| family_id | peak_year_pedder_lake_index | boom_ratio_1977_vs_1965 | first_year_climbing_ratio_gt_one | N_total_2002 | final_to_peak_ratio |
| --- | --- | --- | --- | --- | --- |
| climbing_only | 1977 | 1.376 | 1984.000 | 91.178 | 0.174 |
| habitat_only_null | 1977 | 1.383 | NA | 185.390 | 0.346 |
| persistent_joint_cause | 1975 | 1.233 | 1984.000 | 73.405 | 0.200 |
| transient_perfect_storm | 1975 | 1.199 | 1984.000 | 73.515 | 0.215 |
| trout_only | 1975 | 1.205 | NA | 149.822 | 0.432 |

## Stochastic Transient Perfect-Storm Review

| metric | value |
| --- | --- |
| stochastic_runs | 20 |
| pre1972_extinctions | 0 |
| present_in_1980 | 20 |
| median_peak_year | 1975.000 |

## Interpretation

All Module 1.5 acceptance gates passed.
The default latent kernel is now stable enough and ecologically plausible enough to support Module 2 observation scoring without the scorer being dominated by initialization artefacts.

## Artifacts

- `data/module1_5_example_summary.csv`
- `data/module1_5_stochastic_summary.csv`
- `docs/module1_5_review.md`
