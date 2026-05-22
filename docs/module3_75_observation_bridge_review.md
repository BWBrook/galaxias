# Module 3.75 Observation-Bridge Review

## Summary

Module 3.75 reuses the three remote Module 3.5 sensitivity sweeps and asks whether the late-history targets are carrying biological signal or observation-bridge artefacts.
The pass decomposes `CT007`, softens the exact-year treatment in `CT009`, and rescales `CT010` expected detections without rerunning the simulator.

## Inputs

| seed | run_label | stage_a_draws_per_family | stage_a_keep_per_family | stage_b_replicates |
| --- | --- | --- | --- | --- |
| 20260410 | module3_5_sensitivity_20260518T104633Z | 1000 | 100 | 20 |
| 20260411 | module3_5_sensitivity_seed20260411_20260518T105533Z | 1000 | 100 | 20 |
| 20260412 | module3_5_sensitivity_seed20260412_20260518T105533Z | 1000 | 100 | 20 |

## CT007 Occupancy And Count Split

| family_id | expected_sites | expected_capture | occupancy_raw | count_raw | count_share | current_weighted |
| --- | --- | --- | --- | --- | --- | --- |
| climbing_only | 1.220 | 16.322 | 0.445 | 33.264 | 0.986 | 84.327 |
| persistent_joint_cause | 1.090 | 14.570 | 0.478 | 35.622 | 0.987 | 90.432 |
| transient_perfect_storm | 1.068 | 14.284 | 0.483 | 35.002 | 0.986 | 88.682 |

## Accepted Late-Target Summary

| family_id | accepted_proposals | ct007_current | ct007_count_share | ct009_current | ct009_soft_gap3 | ct010_current | ct010_half |
| --- | --- | --- | --- | --- | --- | --- | --- |
| climbing_only | 47 | 71.125 | 0.986 | 30.000 | 10.000 | 84.050 | 42.025 |
| persistent_joint_cause | 52 | 90.205 | 0.988 | 30.000 | 10.000 | 65.885 | 32.943 |
| transient_perfect_storm | 51 | 89.560 | 0.986 | 30.000 | 10.000 | 61.072 | 30.536 |

## Scenario Winners

| seed | scenario_id | family_id | proposal_id | adjusted_target_sum |
| --- | --- | --- | --- | --- |
| 20260410 | baseline_current | persistent_joint_cause | persistent_joint_cause:p00162 | 156.367 |
| 20260411 | baseline_current | persistent_joint_cause | persistent_joint_cause:p00884 | 173.595 |
| 20260412 | baseline_current | persistent_joint_cause | persistent_joint_cause:p00078 | 165.054 |
| 20260410 | ct007_count_primary | climbing_only | climbing_only:p00216 | 184.931 |
| 20260411 | ct007_count_primary | persistent_joint_cause | persistent_joint_cause:p00884 | 195.684 |
| 20260412 | ct007_count_primary | climbing_only | climbing_only:p00367 | 193.417 |
| 20260410 | ct007_occupancy_primary | persistent_joint_cause | persistent_joint_cause:p00162 | 123.630 |
| 20260411 | ct007_occupancy_primary | climbing_only | climbing_only:p00106 | 138.230 |
| 20260412 | ct007_occupancy_primary | persistent_joint_cause | persistent_joint_cause:p00078 | 132.149 |
| 20260410 | ct009_terminal_window_gap3 | persistent_joint_cause | persistent_joint_cause:p00162 | 136.367 |
| 20260411 | ct009_terminal_window_gap3 | persistent_joint_cause | persistent_joint_cause:p00884 | 153.595 |
| 20260412 | ct009_terminal_window_gap3 | persistent_joint_cause | persistent_joint_cause:p00078 | 145.054 |
| 20260410 | ct010_detection_half | climbing_only | climbing_only:p00818 | 124.172 |
| 20260411 | ct010_detection_half | persistent_joint_cause | persistent_joint_cause:p00884 | 131.005 |
| 20260412 | ct010_detection_half | climbing_only | climbing_only:p00367 | 129.332 |
| 20260410 | late_bridge_soft | persistent_joint_cause | persistent_joint_cause:p00162 | 84.646 |
| 20260411 | late_bridge_soft | persistent_joint_cause | persistent_joint_cause:p00884 | 88.916 |
| 20260412 | late_bridge_soft | persistent_joint_cause | persistent_joint_cause:p00078 | 85.488 |

## Interpretation

Under the current target-sum scoring, the baseline winners across seeds are {'persistent_joint_cause': 3}.
Under the deliberately softer late observation bridge, the winners are {'persistent_joint_cause': 3}.
`CT007` is not a pure occupancy target in practice: the Bonnet Bay capture anchor often contributes most of its raw penalty, so changing that split is a scientific choice rather than a cosmetic scoring tweak.
`CT009` is structurally harsh because any proposal retaining natural-range presence to 2002 receives a fixed 30 weighted-penalty hit. A terminal-window version reduces that hit to about 10 for 2002 persistence, which is enough to check robustness but not enough to make the endpoint irrelevant.
`CT010` behaves exactly like an observation-effort scale for zero detections: halving the expected detection bridge halves the weighted penalty. This is useful for sensitivity analysis, but it should be justified from survey/capture effort rather than tuned to favor a family.

## Recommended Next Step

Keep the current biological family set, but promote the late observation bridge to an explicit Module 4 sensitivity axis: baseline, occupancy-primary `CT007`, soft `CT009`, and low-detection `CT010`. The key research question is no longer whether transient, persistent, and climbing-only mechanisms can all enter the frontier; they can. It is which conclusion survives transparent observation-model assumptions.

## Artifacts

- `data/module3_75_ct007_decomposition.csv`
- `data/module3_75_ct009_soft_window.csv`
- `data/module3_75_ct010_detection_sensitivity.csv`
- `data/module3_75_family_bridge_summary.csv`
- `data/module3_75_ranking_scenarios.csv`
- `docs/module3_75_observation_bridge_review.md`
