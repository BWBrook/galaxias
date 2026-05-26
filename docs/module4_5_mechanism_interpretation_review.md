# Module 4.5 Mechanism Interpretation Review

## Provenance And Run Contract

Validated `90` raw Module 4 artifact records across `15` variant/seed runs before interpretation.

- Raw manifest: `data/module4_raw_artifact_manifest.csv`
- Module 4 root: `outputs/remote/module4_observation_sensitivity_20260522T101942Z`
- Near-frontier absolute margin: `10` target-sum units
- Near-frontier relative margin: `1.05` times the best target sum
- Accepted trajectory sample cap per variant/seed: `100`
- Deterministic landmark regeneration seed: `20260523`

## Proposal Sets

Target-sum distance is reconstructed as the sum across targets of Stage B replicate-median weighted penalties. The accepted set remains the main biological ensemble; near-frontier and winner sets are diagnostics.

| proposal_set | family_id | proposal_count |
| --- | --- | --- |
| accepted | climbing_only | 235 |
| accepted | persistent_joint_cause | 265 |
| accepted | transient_perfect_storm | 250 |
| family_winners | climbing_only | 15 |
| family_winners | habitat_only_null | 15 |
| family_winners | persistent_joint_cause | 15 |
| family_winners | transient_perfect_storm | 15 |
| family_winners | trout_only | 15 |
| global_winners | climbing_only | 3 |
| global_winners | persistent_joint_cause | 12 |
| near_frontier_absolute | climbing_only | 14 |
| near_frontier_absolute | persistent_joint_cause | 18 |
| near_frontier_absolute | transient_perfect_storm | 3 |
| near_frontier_relative | climbing_only | 9 |
| near_frontier_relative | persistent_joint_cause | 13 |
| near_frontier_relative | transient_perfect_storm | 2 |

## Distance Audit

`best_target_sum` and `best_stochastic_distance` are deliberately reported side by side because Module 4 family ranking used target-sum reconstruction.

| variant_id | seed | family_id | best_target_sum_proposal_id | best_target_sum | best_stochastic_distance_proposal_id | best_stochastic_distance | same_best_proposal_under_both_distances |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_current | 20260410 | persistent_joint_cause | persistent_joint_cause:p00162 | 156.367 | persistent_joint_cause:p00162 | 167.924 | yes |
| baseline_current | 20260411 | persistent_joint_cause | persistent_joint_cause:p00884 | 173.595 | persistent_joint_cause:p00884 | 171.810 | yes |
| baseline_current | 20260412 | persistent_joint_cause | persistent_joint_cause:p00078 | 165.054 | persistent_joint_cause:p00078 | 168.924 | yes |
| ct007_occupancy_primary | 20260410 | persistent_joint_cause | persistent_joint_cause:p00162 | 123.630 | persistent_joint_cause:p00162 | 128.282 | yes |
| ct007_occupancy_primary | 20260411 | climbing_only | climbing_only:p00106 | 138.230 | climbing_only:p00106 | 138.355 | yes |
| ct007_occupancy_primary | 20260412 | persistent_joint_cause | persistent_joint_cause:p00078 | 132.149 | persistent_joint_cause:p00078 | 136.728 | yes |
| ct009_terminal_window_gap3 | 20260410 | persistent_joint_cause | persistent_joint_cause:p00162 | 136.367 | persistent_joint_cause:p00162 | 147.924 | yes |
| ct009_terminal_window_gap3 | 20260411 | persistent_joint_cause | persistent_joint_cause:p00884 | 153.595 | persistent_joint_cause:p00884 | 151.810 | yes |
| ct009_terminal_window_gap3 | 20260412 | persistent_joint_cause | persistent_joint_cause:p00078 | 145.054 | persistent_joint_cause:p00078 | 148.924 | yes |
| ct010_detection_half | 20260410 | climbing_only | climbing_only:p00818 | 124.172 | climbing_only:p00818 | 123.443 | yes |
| ct010_detection_half | 20260411 | persistent_joint_cause | persistent_joint_cause:p00884 | 131.005 | persistent_joint_cause:p00884 | 129.960 | yes |
| ct010_detection_half | 20260412 | climbing_only | climbing_only:p00367 | 129.332 | climbing_only:p00367 | 131.888 | yes |
| late_bridge_soft | 20260410 | persistent_joint_cause | persistent_joint_cause:p00162 | 84.646 | persistent_joint_cause:p00162 | 90.919 | yes |
| late_bridge_soft | 20260411 | persistent_joint_cause | persistent_joint_cause:p00884 | 88.916 | persistent_joint_cause:p00884 | 89.823 | yes |
| late_bridge_soft | 20260412 | persistent_joint_cause | persistent_joint_cause:p00078 | 85.488 | persistent_joint_cause:p00078 | 86.948 | yes |

## Late-Target Summary

| variant_id | seed | family_id | proposal_set | target_id | n_proposals | median_weighted_penalty | pass_fraction_zero_weighted_penalty |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_current | 20260410 | climbing_only | accepted | CT007 | 15 | 62.024 | 0.000 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | CT007 | 16 | 90.205 | 0.000 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | CT007 | 19 | 93.529 | 0.000 |
| baseline_current | 20260410 | climbing_only | accepted | CT009 | 15 | 30.000 | 0.000 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | CT009 | 16 | 30.000 | 0.000 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | CT009 | 19 | 30.000 | 0.000 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | CT010 | 19 | 61.072 | 0.000 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | CT010 | 16 | 65.885 | 0.000 |
| baseline_current | 20260410 | climbing_only | accepted | CT010 | 15 | 91.144 | 0.000 |
| baseline_current | 20260410 | climbing_only | near_frontier_absolute | CT007 | 1 | 41.824 | 0.000 |
| baseline_current | 20260410 | persistent_joint_cause | near_frontier_absolute | CT007 | 1 | 67.886 | 0.000 |
| baseline_current | 20260410 | climbing_only | near_frontier_absolute | CT009 | 1 | 30.000 | 0.000 |
| baseline_current | 20260410 | persistent_joint_cause | near_frontier_absolute | CT009 | 1 | 30.000 | 0.000 |
| baseline_current | 20260410 | persistent_joint_cause | near_frontier_absolute | CT010 | 1 | 37.967 | 0.000 |
| baseline_current | 20260410 | climbing_only | near_frontier_absolute | CT010 | 1 | 76.443 | 0.000 |
| baseline_current | 20260411 | transient_perfect_storm | accepted | CT007 | 14 | 61.672 | 0.000 |
| baseline_current | 20260411 | climbing_only | accepted | CT007 | 19 | 71.125 | 0.000 |
| baseline_current | 20260411 | persistent_joint_cause | accepted | CT007 | 17 | 83.668 | 0.000 |
| baseline_current | 20260411 | climbing_only | accepted | CT009 | 19 | 30.000 | 0.000 |
| baseline_current | 20260411 | persistent_joint_cause | accepted | CT009 | 17 | 30.000 | 0.000 |
| baseline_current | 20260411 | transient_perfect_storm | accepted | CT009 | 14 | 30.000 | 0.000 |
| baseline_current | 20260411 | persistent_joint_cause | accepted | CT010 | 17 | 78.747 | 0.000 |
| baseline_current | 20260411 | climbing_only | accepted | CT010 | 19 | 84.050 | 0.000 |
| baseline_current | 20260411 | transient_perfect_storm | accepted | CT010 | 14 | 92.519 | 0.000 |
| baseline_current | 20260411 | climbing_only | near_frontier_absolute | CT007 | 1 | 41.715 | 0.000 |
| baseline_current | 20260411 | persistent_joint_cause | near_frontier_absolute | CT007 | 1 | 45.838 | 0.000 |
| baseline_current | 20260411 | climbing_only | near_frontier_absolute | CT009 | 1 | 30.000 | 0.000 |
| baseline_current | 20260411 | persistent_joint_cause | near_frontier_absolute | CT009 | 1 | 30.000 | 0.000 |
| baseline_current | 20260411 | climbing_only | near_frontier_absolute | CT010 | 1 | 84.050 | 0.000 |
| baseline_current | 20260411 | persistent_joint_cause | near_frontier_absolute | CT010 | 1 | 85.180 | 0.000 |

## Nuisance Diagnostic

| variant_id | family_id | parameter_id | n_proposals | median_value | near_either_bound_fraction | boundary_status | spearman_value_vs_target_sum |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ct007_occupancy_primary | transient_perfect_storm | PR039 | 44 | 93.374 | 0.159 | low_boundary_dependence | -0.101 |
| baseline_current | persistent_joint_cause | PR038 | 52 | 0.251 | 0.154 | low_boundary_dependence | -0.104 |
| ct009_terminal_window_gap3 | persistent_joint_cause | PR038 | 52 | 0.251 | 0.154 | low_boundary_dependence | -0.104 |
| ct007_occupancy_primary | persistent_joint_cause | PR039 | 59 | 82.372 | 0.136 | low_boundary_dependence | 0.241 |
| late_bridge_soft | persistent_joint_cause | PR038 | 53 | 0.269 | 0.130 | low_boundary_dependence | -0.001 |
| ct007_occupancy_primary | climbing_only | PR039 | 46 | 93.358 | 0.128 | low_boundary_dependence | 0.335 |
| ct010_detection_half | persistent_joint_cause | PR038 | 47 | 0.249 | 0.125 | low_boundary_dependence | -0.059 |
| ct007_occupancy_primary | persistent_joint_cause | PR038 | 59 | 0.260 | 0.119 | low_boundary_dependence | 0.204 |
| ct007_occupancy_primary | transient_perfect_storm | PR038 | 44 | 0.230 | 0.114 | low_boundary_dependence | -0.145 |
| ct010_detection_half | persistent_joint_cause | PR039 | 47 | 111.583 | 0.104 | low_boundary_dependence | -0.089 |
| baseline_current | transient_perfect_storm | PR038 | 50 | 0.266 | 0.098 | low_boundary_dependence | -0.044 |
| baseline_current | transient_perfect_storm | PR039 | 50 | 96.319 | 0.098 | low_boundary_dependence | 0.069 |
| ct009_terminal_window_gap3 | transient_perfect_storm | PR038 | 50 | 0.266 | 0.098 | low_boundary_dependence | -0.044 |
| ct009_terminal_window_gap3 | transient_perfect_storm | PR039 | 50 | 96.319 | 0.098 | low_boundary_dependence | 0.069 |
| late_bridge_soft | persistent_joint_cause | PR039 | 53 | 108.623 | 0.093 | low_boundary_dependence | -0.001 |
| ct007_occupancy_primary | transient_perfect_storm | PR037 | 44 | 3.242 | 0.091 | low_boundary_dependence | -0.466 |
| late_bridge_soft | transient_perfect_storm | PR038 | 46 | 0.242 | 0.087 | low_boundary_dependence | 0.060 |
| late_bridge_soft | transient_perfect_storm | PR039 | 46 | 103.024 | 0.087 | low_boundary_dependence | 0.153 |
| ct010_detection_half | transient_perfect_storm | PR038 | 58 | 0.263 | 0.086 | low_boundary_dependence | -0.170 |
| ct010_detection_half | transient_perfect_storm | PR039 | 58 | 113.724 | 0.086 | low_boundary_dependence | 0.308 |
| ct007_occupancy_primary | persistent_joint_cause | PR037 | 59 | 3.117 | 0.085 | low_boundary_dependence | -0.585 |
| ct010_detection_half | persistent_joint_cause | PR037 | 47 | 2.992 | 0.083 | low_boundary_dependence | -0.241 |
| baseline_current | persistent_joint_cause | PR037 | 52 | 3.166 | 0.077 | low_boundary_dependence | -0.463 |
| baseline_current | persistent_joint_cause | PR039 | 52 | 108.863 | 0.077 | low_boundary_dependence | 0.038 |
| ct009_terminal_window_gap3 | persistent_joint_cause | PR037 | 52 | 3.166 | 0.077 | low_boundary_dependence | -0.463 |
| ct009_terminal_window_gap3 | persistent_joint_cause | PR039 | 52 | 108.863 | 0.077 | low_boundary_dependence | 0.038 |
| late_bridge_soft | persistent_joint_cause | PR037 | 53 | 3.082 | 0.074 | low_boundary_dependence | -0.383 |
| ct010_detection_half | climbing_only | PR038 | 43 | 0.217 | 0.068 | low_boundary_dependence | -0.093 |
| late_bridge_soft | transient_perfect_storm | PR037 | 46 | 3.242 | 0.065 | low_boundary_dependence | -0.209 |
| baseline_current | climbing_only | PR037 | 47 | 3.236 | 0.064 | low_boundary_dependence | -0.342 |

## Derived Pressure Landmarks

| variant_id | seed | family_id | proposal_set | window_label | n_proposals | median_cumulative_lake_trout_pressure | median_cumulative_lake_climbing_pressure | median_cumulative_refuge_climbing_pressure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_current | 20260410 | climbing_only | accepted | climbing_transition_1978_1983 | 15 | 0.000 | 0.804 | 0.772 |
| baseline_current | 20260410 | climbing_only | family_winners | climbing_transition_1978_1983 | 1 | 0.000 | 0.804 | 0.388 |
| baseline_current | 20260410 | climbing_only | accepted | final_record_window_1992_1996 | 15 | 0.000 | 3.500 | 2.934 |
| baseline_current | 20260410 | climbing_only | family_winners | final_record_window_1992_1996 | 1 | 0.000 | 4.345 | 2.545 |
| baseline_current | 20260410 | climbing_only | accepted | non_detection_endpoint_1998_2002 | 15 | 0.000 | 3.941 | 2.934 |
| baseline_current | 20260410 | climbing_only | family_winners | non_detection_endpoint_1998_2002 | 1 | 0.000 | 4.353 | 2.545 |
| baseline_current | 20260410 | climbing_only | accepted | post_flood_boom_1972_1977 | 15 | 0.000 | 0.100 | 0.073 |
| baseline_current | 20260410 | climbing_only | family_winners | post_flood_boom_1972_1977 | 1 | 0.000 | 0.202 | 0.078 |
| baseline_current | 20260410 | climbing_only | accepted | refuge_contraction_1984_1991 | 15 | 0.000 | 4.486 | 4.194 |
| baseline_current | 20260410 | climbing_only | family_winners | refuge_contraction_1984_1991 | 1 | 0.000 | 5.450 | 3.477 |
| baseline_current | 20260410 | habitat_only_null | family_winners | climbing_transition_1978_1983 | 1 | 0.000 | 0.000 | 0.000 |
| baseline_current | 20260410 | habitat_only_null | family_winners | final_record_window_1992_1996 | 1 | 0.000 | 0.000 | 0.000 |
| baseline_current | 20260410 | habitat_only_null | family_winners | non_detection_endpoint_1998_2002 | 1 | 0.000 | 0.000 | 0.000 |
| baseline_current | 20260410 | habitat_only_null | family_winners | post_flood_boom_1972_1977 | 1 | 0.000 | 0.000 | 0.000 |
| baseline_current | 20260410 | habitat_only_null | family_winners | refuge_contraction_1984_1991 | 1 | 0.000 | 0.000 | 0.000 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | climbing_transition_1978_1983 | 16 | 3.729 | 0.952 | 1.496 |
| baseline_current | 20260410 | persistent_joint_cause | family_winners | climbing_transition_1978_1983 | 1 | 3.908 | 1.446 | 0.788 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | final_record_window_1992_1996 | 16 | 1.583 | 5.031 | 2.456 |
| baseline_current | 20260410 | persistent_joint_cause | family_winners | final_record_window_1992_1996 | 1 | 1.583 | 9.213 | 2.633 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | non_detection_endpoint_1998_2002 | 16 | 1.583 | 5.089 | 2.458 |
| baseline_current | 20260410 | persistent_joint_cause | family_winners | non_detection_endpoint_1998_2002 | 1 | 1.582 | 9.240 | 2.633 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | post_flood_boom_1972_1977 | 16 | 1.143 | 0.110 | 0.112 |
| baseline_current | 20260410 | persistent_joint_cause | family_winners | post_flood_boom_1972_1977 | 1 | 1.675 | 0.225 | 0.099 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | refuge_contraction_1984_1991 | 16 | 2.579 | 6.021 | 3.626 |
| baseline_current | 20260410 | persistent_joint_cause | family_winners | refuge_contraction_1984_1991 | 1 | 2.600 | 11.160 | 3.997 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | climbing_transition_1978_1983 | 19 | 3.636 | 0.823 | 1.157 |
| baseline_current | 20260410 | transient_perfect_storm | family_winners | climbing_transition_1978_1983 | 1 | 3.636 | 1.859 | 1.736 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | final_record_window_1992_1996 | 19 | 1.206 | 5.595 | 2.358 |
| baseline_current | 20260410 | transient_perfect_storm | family_winners | final_record_window_1992_1996 | 1 | 1.118 | 6.378 | 2.139 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | non_detection_endpoint_1998_2002 | 19 | 1.153 | 5.777 | 2.358 |

## Trajectory Landmarks

| variant_id | seed | family_id | proposal_set | year | n_proposals | median_N_total | median_N_L | median_N_R | total_present_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_current | 20260410 | climbing_only | accepted | 1977 | 15 | 823.348 | 583.599 | 179.664 | 1.000 |
| baseline_current | 20260410 | climbing_only | family_winners | 1977 | 1 | 447.709 | 276.153 | 171.556 | 1.000 |
| baseline_current | 20260410 | climbing_only | accepted | 1991 | 15 | 133.258 | 57.641 | 80.919 | 1.000 |
| baseline_current | 20260410 | climbing_only | family_winners | 1991 | 1 | 117.044 | 33.472 | 83.572 | 1.000 |
| baseline_current | 20260410 | climbing_only | accepted | 1996 | 15 | 127.520 | 46.105 | 76.637 | 1.000 |
| baseline_current | 20260410 | climbing_only | family_winners | 1996 | 1 | 114.301 | 32.362 | 81.939 | 1.000 |
| baseline_current | 20260410 | climbing_only | accepted | 2002 | 15 | 127.829 | 45.211 | 76.898 | 1.000 |
| baseline_current | 20260410 | climbing_only | family_winners | 2002 | 1 | 114.526 | 32.367 | 82.159 | 1.000 |
| baseline_current | 20260410 | habitat_only_null | family_winners | 1977 | 1 | 534.768 | 429.707 | 105.061 | 1.000 |
| baseline_current | 20260410 | habitat_only_null | family_winners | 1991 | 1 | 193.291 | 102.680 | 90.611 | 1.000 |
| baseline_current | 20260410 | habitat_only_null | family_winners | 1996 | 1 | 186.157 | 97.150 | 89.007 | 1.000 |
| baseline_current | 20260410 | habitat_only_null | family_winners | 2002 | 1 | 185.461 | 96.397 | 89.065 | 1.000 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | 1977 | 16 | 509.190 | 346.981 | 110.837 | 1.000 |
| baseline_current | 20260410 | persistent_joint_cause | family_winners | 1977 | 1 | 233.761 | 172.576 | 61.185 | 1.000 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | 1991 | 16 | 89.947 | 32.024 | 57.776 | 1.000 |
| baseline_current | 20260410 | persistent_joint_cause | family_winners | 1991 | 1 | 32.247 | 8.274 | 23.973 | 1.000 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | 1996 | 16 | 85.569 | 23.534 | 55.953 | 1.000 |
| baseline_current | 20260410 | persistent_joint_cause | family_winners | 1996 | 1 | 30.678 | 7.485 | 23.192 | 1.000 |
| baseline_current | 20260410 | persistent_joint_cause | accepted | 2002 | 16 | 85.812 | 22.993 | 56.022 | 1.000 |
| baseline_current | 20260410 | persistent_joint_cause | family_winners | 2002 | 1 | 30.785 | 7.507 | 23.278 | 1.000 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | 1977 | 19 | 368.110 | 234.932 | 127.298 | 1.000 |
| baseline_current | 20260410 | transient_perfect_storm | family_winners | 1977 | 1 | 271.606 | 144.308 | 127.298 | 1.000 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | 1991 | 19 | 94.930 | 29.673 | 61.289 | 1.000 |
| baseline_current | 20260410 | transient_perfect_storm | family_winners | 1991 | 1 | 72.821 | 11.532 | 61.289 | 1.000 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | 1996 | 19 | 89.239 | 24.707 | 60.289 | 1.000 |
| baseline_current | 20260410 | transient_perfect_storm | family_winners | 1996 | 1 | 70.787 | 10.498 | 60.289 | 1.000 |
| baseline_current | 20260410 | transient_perfect_storm | accepted | 2002 | 19 | 89.687 | 25.211 | 60.345 | 1.000 |
| baseline_current | 20260410 | transient_perfect_storm | family_winners | 2002 | 1 | 70.746 | 10.401 | 60.345 | 1.000 |
| baseline_current | 20260410 | trout_only | family_winners | 1977 | 1 | 116.028 | 38.162 | 77.865 | 1.000 |
| baseline_current | 20260410 | trout_only | family_winners | 1991 | 1 | 91.723 | 17.447 | 74.277 | 1.000 |

## Module 5 Decision Table

| family_id | accepted_proposal_count | global_winner_count | stable_rank | nuisance_boundary_status | coherent_pressure_history | module5_role |
| --- | --- | --- | --- | --- | --- | --- |
| habitat_only_null | 0 | 0 | no | uncertain_no_accepted_set | not_applicable_negative_reference | negative_reference |
| trout_only | 0 | 0 | no | uncertain_no_accepted_set | not_applicable_negative_reference | negative_reference |
| persistent_joint_cause | 265 | 12 | yes | low_boundary_risk | yes | primary |
| climbing_only | 235 | 3 | partial | low_boundary_risk | yes | sensitivity |
| transient_perfect_storm | 250 | 0 | no | low_boundary_risk | yes | sensitivity |

## Interpretation

Primary Module 5 ensemble under this diagnostic rule: `['persistent_joint_cause']`. Families retained as sensitivity cases: `['climbing_only', 'transient_perfect_storm']`.
This is still a mechanism audit, not a posterior claim. The strongest current claim is whether a family survives target-sum, nuisance, and derived-pressure checks well enough to seed counterfactual analysis.
`habitat_only_null` and `trout_only` remain useful negative references when their accepted-frontier support is absent under the current target/prior framework.

## Generated Artifacts

- `data/module4_5_proposal_set_membership.csv`
- `data/module4_5_distance_audit.csv`
- `data/module4_5_parameter_summary.csv`
- `data/module4_5_parameter_contrasts.csv`
- `data/module4_5_nuisance_audit.csv`
- `data/module4_5_target_family_summary.csv`
- `data/module4_5_pressure_landmarks.csv`
- `data/module4_5_trajectory_landmarks.csv`
- `data/module4_5_family_decision_table.csv`
- `docs/module4_5_mechanism_interpretation_review.md`
