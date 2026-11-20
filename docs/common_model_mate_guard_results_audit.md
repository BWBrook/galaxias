# Independent audit of singleton-guard central results

20 September 2026  
Production archive: `outputs/remote/mate_guard_20260920/production`  
Analysis archive: `outputs/remote/mate_guard_20260920/analysis`

## Verdict

**Supported with material interpretive qualifications.** The approved singleton
guard substantially reduces the frozen witness set: of 1,527 originally
qualified primary profiles, 600 remain qualified, 193 become unresolved and 734
become not-found. The retained profiles represent 226 of the 517 selected
sources. Across every primary q/law profile at those fixed sources, 609 profiles
are qualified after the amendment, comprising 600 retained profiles and nine
q/law profiles that newly qualify.

This establishes strong sensitivity to the singleton-reproduction assumption,
but it does not resolve the original equifinality. Compatible fixed-source
examples remain under all four restrictions. The counts are not posterior
probabilities, mechanism votes or estimates of general prevalence because all
517 sources were selected under the original kernel.

I independently rebuilt the central joins, permissive-profile classifications,
homogeneous q = 0.005 weights, paired survival contrasts, own-weight survival,
Monte Carlo diagnostics and survivor-tail diagnostics. I did not call the
project analysis functions or run simulations. Calculations used round-trip CSV
parsing under the exact production runtime: Python 3.14.5, NumPy 2.4.6 and
pandas 2.3.3 on Linux.

## Archive, identity and arithmetic checks

- The completed manifest contains 517 sources and 529,408 histories. The
  independent seed join found exactly 529,408 distinct source/replicate keys in
  each of the frozen seed table, amended raw files and selected original raw
  histories, with zero seed or key mismatches.
- The closeout verified 1,555 output hashes, 85 source/input files and
  20,117,504 annual rows. There are zero positive recruitment records while the
  guard is active and zero zero/singleton-total rebounds.
- The original kernel remains bound at SHA256
  `2031373352dbdb55b30db571dc7b861e67f804fc0b5709ef99233f73e8e463c4`;
  the amended kernel is bound at
  `7da473275457d9970c7b6a748e4ac92043c96ccdd14266142fb6e02827bdb332`.
  Current local copies match the production manifest. The runner, analysis and
  protocol bindings also match.
- All independently reconstructed headline counts match the compact readout.
  Four targeted raw-history recomputations match the analysis to a maximum
  absolute numerical discrepancy of `1.14e-13`.

The machine-readable evidence and input bindings are recorded in
`data/common_model/mate_guard_20260920/results_audit.json`.

## Compatibility and viability

The original profiles transition as follows:

| New status | Profiles | Fraction of original 1,527 |
|---|---:|---:|
| Qualified-compatible | 600 | 39.3% |
| Unresolved | 193 | 12.6% |
| Not-found | 734 | 48.1% |

The nine gains among all fixed-source primary profiles arise because the amended
trajectories change early-pattern frequencies, observation likelihoods and
weight concentration. They are not evidence that the guard improves biological
performance, and they do not constitute a new search.

The amended deterministic insurance screen rejects 108 sources and retains 409.
All 108 failures are confined to one component: Oberon abundance in 2012 does
not exceed the 34 founders. Their 2012 totals range from 8.35 to 33.91, while
annual persistence, juveniles by 1997 and all three Strathgordon components pass.
Thus the failure is specific to the prescribed net-growth phase. It does not
mean the founders died, that stochastic historical persistence is absent, or
that the parameter point is biologically non-viable under every criterion. The
analysis correctly retains all histories but assigns zero amended own weight to
these sources.

Sensitivity is associated with the established refuge-capacity stratum:

| Stratum | Original profiles retained | Sources passing amended screen | Sources retaining a profile |
|---|---:|---:|---:|
| `K_R < 20` | 23 / 199 | 13 / 58 | 6 / 58 |
| `K_R >= 20` | 577 / 1,328 | 396 / 459 | 220 / 459 |

The lower-capacity stratum is therefore more fragile in this selected set. The
threshold is a diagnostic boundary rather than a calibrated field capacity;
capacity, restriction, configuration and other parameters are confounded by the
original selection, so this association is not a causal capacity effect.

## Paired process changes

Paired contrasts use original factual weights. Among the original 1,527
profiles, 1,073 contrasts are defined and 454 are undefined because an amended
invalid-removal history has positive original support. The undefined histories
are retained and the remaining weights are not renormalised. Across all 6,204
source/q/law profiles, 4,368 are defined and 1,836 are undefined for this reason.

Of the 1,073 defined original-profile contrasts, 451 are negative, 617 are
exactly zero and five are positive. Differences range from -0.605880 to
+0.037202, with median zero. These are descriptive paired estimates, not
significance results. The 454 undefined profiles and fixed-source selection
prevent a population-average directional claim.

The two prespecified base sources both originally qualify at q = 0.02 under the
shared-quality law. Independent raw-history reconstruction gives:

| Original witness profile | Original weighted survival | Guarded survival under original weights | Paired difference (MC SE) | Guarded own-weight survival (MC SE) | New status |
|---|---:|---:|---:|---:|---|
| Base `R_C`, 20260918 w1 s0011 | 0.511121 | 0.219912 | -0.291209 (0.035338) | 0.203124 (0.048122) | Not-found |
| Base `R_J`, 20260919 w3 s0082 | 0.528087 | 0.204452 | -0.323635 (0.038686) | 0.094609 (0.029364) | Unresolved |

The amended `R_C` profile fails the early-pattern threshold and has own-weight
ESS 32.72. The `R_J` profile exceeds the early and joint thresholds but has
own-weight ESS 25.07, so its upper bounds overlap the cutoffs while its weight
concentration prevents qualification. These statuses and all displayed values
match the production analysis exactly.

Four homogeneous q = 0.005 cases were rebuilt directly from raw histories:

| Case | Original weighted survival | Guarded survival under original weights | Paired difference (MC SE) | Guarded own-weight survival | Own ESS / survivor ESS | Own status |
|---|---:|---:|---:|---:|---:|---|
| Base `R_C`, 20260918 w1 s0011 | 0.707963 | 0.343026 | -0.364937 (0.040327) | 0.357426 | 14.19 / 8.33 | Not-found |
| Base `R_J`, 20260919 w3 s0082 | 0.812946 | 0.417719 | -0.395227 (0.051026) | 0.349932 | 19.56 / 6.87 | Not-found |
| Largest defined q=.005 homogeneous change: `env_rho_002 R_C`, 20260918 w3 s0156 | 0.889732 | 0.244923 | -0.644808 (0.042913) | 0.579941 | 99.06 / 53.92 | Not-found |
| Invalid-removal example: minimum-dated-juvenile-first `R_H`, 20260918 w3 s0153 | 1.000000 | Undefined | Undefined | Undefined | 0 / 0 | Not-found; screen failed |

The two named base sources were previously selected through shared-quality
profiles; their q = 0.005 homogeneous rows are a uniform diagnostic comparison,
not their original qualifying profiles. Their guarded own-weight survival near
0.35 is highly concentrated and cannot be presented as retained-witness
survival. The largest defined paired decrease likewise has a very different
own-weight estimate and fails qualification, demonstrating why the two
estimands must remain separate.

For the invalid-removal example, 335 original positive-support histories become
removal-invalid and carry 0.72152 of the original weight. Its paired result is
therefore undefined exactly as specified; dropping those histories would answer
a different, selected counterfactual question.

## Survival precision and surviving examples

The amended base, q = 0.005 homogeneous slice contains 17 qualified `R_C`, six
`R_H`, six `R_J` and one `R_T` profiles. Their own-weight terminal-survival
ranges are 0.703–1.000 for `R_C` and effectively 1.000 for the other three
restrictions. All 30 pass the survivor-tail ESS, relative-error and largest-share
checks. These are fixed-source examples and do not rank restrictions.

Survivor-tail precision is weaker across the complete primary set. Only 568 of
the 600 retained original profiles, and 574 of all 609 amended compatible
profiles, pass the tail checks. The worst retained survivor ESS is 1.65 despite
the profile meeting overall joint-weight qualification; the sole q = 0.2
compatible primary profile is this case. Low or near-zero weighted survival from
the remaining 35 profiles must therefore carry an explicit precision warning.

The archive also contains 159 unweighted terminal lake-only histories. They are
correctly retained as survivors under the prespecified total-population endpoint
and should not be recoded as extinct.

## Interpretation and recommendation

The amendment includes deterministic initialization. In the bounded 24-source
qualification, 22 sources entered a genuine alternating burn-in cycle and two
retained exact initial-state parity. This diagnostic is not a claim about the
frequency of initialization changes among all 517 sources. It does establish
that downstream differences cannot all be attributed to late singleton
histories, and the current experiment does not factorially separate
initialization, insurance-screen and historical-transition effects.

The remaining compatible examples establish robustness only to this coarse
necessary breeder-count guard. Sparse binary observations, scenario q values,
the unknown mapping from model counts to surveyed fish, fixed parameter points,
pooled breeding and settlement, and the absence of sex, co-location and mate
encounter remain. Not-found profiles do not exclude unsampled parameter regions,
and retained profiles do not validate the historical mechanism.

Recommendation: report substantial structural sensitivity together with the
surviving fixed-source examples. Preserve the paired-versus-rescored distinction,
undefined-removal rule, phase-specific viability interpretation, survivor-tail
warnings, initialization scope and global-nonexclusion boundary. Independent
scientific review materially increases confidence in the interpretation, though
the central arithmetic and provenance checks are complete and require no rerun.
