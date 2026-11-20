# Early-lake overshoot readout

This note describes paired frozen validation/counterfactual histories. It does not add histories, replay annual trajectories, or treat source extrema as model rankings.

The archive contains 254 R_J sources and 1024 paired streams per source. The permissive factual-compatible slice contains 274 source/profile rows; 1065 of its five-endpoint rows are defined and 1065 meet the factual ESS/RSE/largest-weight criteria.

Counterfactual weights are the fixed factual 14-record joint weights, multiplied by the factual early-pattern and removal eligibility flags. No counterfactual likelihood or source reselection is used. An altered invalid-removal history with positive factual support leaves the contrast undefined without renormalisation, including when its total weight is numerically tiny.

The 1988/1989 negative lake fields are labelled actual state years 1987/1988 because they are observation proxies for the preceding state. The whole-period minimum endpoint cannot locate an early effect, and the archive does not supply a complete annual lake trajectory.

Across profile rows, confidence intervals and paired Monte Carlo errors are descriptive. A small or sign-uncertain effect is insufficient to infer a direction; these summaries do not average across parameter sources as a population estimand.

Checks: paired_formula=passed, invalidity=passed, zero_effect=passed.

Defined compatible estimate ranges by endpoint:
- lake_N_L_1980: -1.13142 to 134.784; CI above zero 204, below zero 0, zero 0.
- lake_N_L_1983: -0.826888 to 44.5138; CI above zero 127, below zero 0, zero 0.
- lake_N_L_1987: -0.634953 to 6.34757; CI above zero 60, below zero 5, zero 0.
- lake_N_L_1988: -1.48211 to 3.60805; CI above zero 44, below zero 15, zero 0.
- minimum_N_total_1972_2002: -0.999415 to 3.82547; CI above zero 26, below zero 3, zero 0.
