# Module 3.5 Diagnostic Review

## Summary

Module 3.5 diagnoses why the first ABC/history-matching readiness run is not yet a sound basis for Module 4 posterior summaries.
It reruns the Module 3 readiness-scale calibration once, then inspects sampler failures, retained-proposal target leverage, and target-omission family ranking.

## Run Configuration

| setting | value |
| --- | --- |
| stage_a_draws_per_family | 250 |
| stage_a_keep_per_family | 20 |
| stage_b_historical_replicates | 5 |
| final_acceptance_fraction | 0.100 |
| final_acceptance_cap | 10 |
| master_seed | 20260410 |
| output_dir | /Users/bwbrook/papers/galaxias/outputs/module3_5/diagnostic_primary |

## Key Metrics

| metric | value |
| --- | --- |
| stage_b_valid_proposals | 100 |
| accepted_count | 10 |
| winning_family | climbing_only |
| target_omission_flip_count | 3 |

## Sampler Geometry

No pre-simulation sampler or constraint failures were recorded.

## Family Ranking Frontier

| global_stage_b_rank | proposal_id | family_id | stage_status | stochastic_overall_distance_median | stochastic_historical_core_distance_iqr |
| --- | --- | --- | --- | --- | --- |
| 1 | climbing_only:p00216 | climbing_only | accepted | 152.819 | 39.821 |
| 2 | transient_perfect_storm:p00144 | transient_perfect_storm | accepted | 179.119 | 7.831 |
| 3 | persistent_joint_cause:p00162 | persistent_joint_cause | accepted | 185.704 | 12.405 |
| 40 | trout_only:p00096 | trout_only | stage_b_rejected | 323.373 | 7.961 |
| 57 | habitat_only_null:p00248 | habitat_only_null | stage_b_rejected | 383.699 | 50.222 |

## Accepted Target Leverage

| target_id | target_group | comparison_type | priority_weight | accepted_median_weighted_penalty |
| --- | --- | --- | --- | --- |
| CT010 | historical_core | zero_detection_window | 5 | 74.759 |
| CT007 | historical_core | joint_occupancy_and_count_constraint | 5 | 63.717 |
| CT009 | historical_core | last_occurrence_event | 5 | 30.000 |
| CT011 | intrinsic_baseline | baseline_growth_constraint | 3 | 4.158 |
| CT008 | historical_core | upper_bound_count_constraint | 5 | 3.675 |
| CT003 | historical_core | target_year_match | 4 | 2.000 |
| CT004 | historical_core | event_and_window_presence | 5 | 1.667 |
| CT006 | historical_core | compartment_presence_constraint | 5 | 1.667 |

## Best Proposal Target Penalties

| family_id | proposal_id | target_id | median_weighted_penalty |
| --- | --- | --- | --- |
| climbing_only | climbing_only:p00216 | CT010 | 71.210 |
| climbing_only | climbing_only:p00216 | CT007 | 37.955 |
| climbing_only | climbing_only:p00216 | CT009 | 30.000 |
| climbing_only | climbing_only:p00216 | CT004 | 5.000 |
| climbing_only | climbing_only:p00216 | CT008 | 4.127 |
| climbing_only | climbing_only:p00216 | CT011 | 4.080 |
| climbing_only | climbing_only:p00216 | CT006 | 2.130 |
| climbing_only | climbing_only:p00216 | CT001 | 0.000 |
| climbing_only | climbing_only:p00216 | CT002 | 0.000 |
| climbing_only | climbing_only:p00216 | CT003 | 0.000 |
| climbing_only | climbing_only:p00216 | CT005 | 0.000 |
| climbing_only | climbing_only:p00216 | CT012 | 0.000 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT007 | 105.659 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT010 | 39.460 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT009 | 30.000 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT011 | 4.304 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT003 | 4.000 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT006 | 1.667 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT008 | 1.593 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT012 | 0.358 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT001 | 0.000 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT002 | 0.000 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT004 | 0.000 |
| transient_perfect_storm | transient_perfect_storm:p00144 | CT005 | 0.000 |
| persistent_joint_cause | persistent_joint_cause:p00162 | CT007 | 68.719 |
| persistent_joint_cause | persistent_joint_cause:p00162 | CT010 | 47.810 |
| persistent_joint_cause | persistent_joint_cause:p00162 | CT009 | 30.000 |
| persistent_joint_cause | persistent_joint_cause:p00162 | CT003 | 8.000 |
| persistent_joint_cause | persistent_joint_cause:p00162 | CT005 | 7.313 |
| persistent_joint_cause | persistent_joint_cause:p00162 | CT011 | 4.237 |

## Target Omission Sensitivity

| omission_label | omitted_target_ids | family_id | best_proposal_id | adjusted_median_target_sum |
| --- | --- | --- | --- | --- |
| none | none | climbing_only | climbing_only:p00216 | 154.501 |
| CT001 | CT001 | climbing_only | climbing_only:p00216 | 154.501 |
| CT002 | CT002 | climbing_only | climbing_only:p00216 | 154.501 |
| CT003 | CT003 | climbing_only | climbing_only:p00216 | 154.501 |
| CT004 | CT004 | climbing_only | climbing_only:p00216 | 149.501 |
| CT005 | CT005 | climbing_only | climbing_only:p00216 | 154.501 |
| CT006 | CT006 | climbing_only | climbing_only:p00216 | 152.371 |
| CT007 | CT007 | persistent_joint_cause | persistent_joint_cause:p00016 | 52.002 |
| CT008 | CT008 | climbing_only | climbing_only:p00216 | 150.374 |
| CT009 | CT009 | climbing_only | climbing_only:p00216 | 124.501 |
| CT010 | CT010 | persistent_joint_cause | persistent_joint_cause:p00132 | 68.600 |
| CT011 | CT011 | climbing_only | climbing_only:p00216 | 150.421 |
| CT012 | CT012 | climbing_only | climbing_only:p00216 | 154.501 |
| late_terminal_block | CT007,CT009,CT010 | persistent_joint_cause | persistent_joint_cause:p00092 | 10.395 |
| causal_mechanism_block | CT004,CT005 | climbing_only | climbing_only:p00216 | 149.501 |

## Interpretation

The constraint-aware sampler removed the pre-simulation validity blocker.
At this readiness scale the accepted frontier now includes climbing-only, persistent joint-cause, and transient perfect-storm proposals, so the earlier climbing-only result should not be interpreted as a stable biological conclusion.
Family ranking remains sensitive to the late detection and contraction targets: omitting `CT007`, `CT010`, or the late-terminal block can move the best retained proposal toward the persistent joint-cause family.

## Recommended Next Step

Run a larger remote sensitivity sweep before changing biological target weights.

## Artifacts

- `data/module3_5_family_summary.csv`
- `data/module3_5_sampler_failures.csv`
- `data/module3_5_stage_b_frontier.csv`
- `data/module3_5_family_best_stage_b.csv`
- `data/module3_5_target_leverage.csv`
- `data/module3_5_accepted_target_penalties.csv`
- `data/module3_5_best_proposal_target_penalties.csv`
- `data/module3_5_target_omission_sensitivity.csv`
- `docs/module3_5_diagnostic_review.md`
