# Conditional calibration: results and interpretation

2026-09-12. Fixed programme complete; independent scientific review recorded below.

The larger stochastic experiment is complete, but it does **not** establish a
causal ranking of the five mechanism families. The most consequential finding
is that the family definitions and historical targets partly prescribe that
ranking: removing an invasive species from a family also removes the state or
forcing needed to satisfy observed species-presence and timing targets.
Detection assumptions and parameter selection separately change conditional
terminal survival. These results support a redesign of the causal comparison,
not promotion of a winning family or an empirical extinction probability.

The [frozen protocol](conditional_calibration.md) remains unchanged. The
[figure](../data/conditional_calibration/conditional_calibration.pdf) and
[compact evidence](../data/conditional_calibration/) accompany this report.

## Completed experiment

Three fresh search seeds each supplied 500 parameter draws per family:
7,500 sources across all five families. Every source received stochastic
historical screening; no deterministic historical gate was applied.

| Phase | Distinct sources | Histories per source | Historical simulations |
|---|---:|---:|---:|
| Screen | 7,500 | 100 | 750,000 |
| Refinement | 636 | 500 | 318,000 |
| Independent validation | 356 | 2,000 | 712,000 |
| Total | — | — | 1,780,000 |

A further 15,000 deterministic intrinsic simulations were cached before
screening. Final memberships contain 1,200 slots: 750 global, 225 family, and
225 weight-one family diagnostic slots. Their union contains 356 physical
parameter sources; duplicate memberships reuse the same histories. Validation
used fresh process seeds and did not select or replace any source. It is
independent simulation validation at selected parameter points, not held-out
field evidence or independent parameter sampling.

The deep-server programme ran with 32 workers from 03:52:15 to 04:53:13 UTC
(60 minutes 58 seconds), including all phase analyses and summary generation.
The realized simulation budget was below the frozen 4.275-million-history
ceiling. No further search expansion was undertaken.

## Why family ranks cannot identify causes

CT005 scores climbing-galaxias dominance. In `trout_only` and
`habitat_only_null`, climbing-galaxias abundance is identically zero. The ratio
floor of 1e-9 and maximum PR038 of 0.8 impose a minimum weighted CT005 penalty
of `0.5 * 5 * log(1e9) / 0.8 = 64.7602`. This persists however well the focal
species history otherwise fits. CT004 requires trout-related features including
a later piscivory increase; absent trout fails all three checks, while the
persistent-joint formulation fails the increase check by construction.

| Family | Minimum CT004 penalty | Minimum CT005 penalty | Combined floor |
|---|---:|---:|---:|
| Habitat only | 5.000 | 64.760 | 69.760 |
| Trout only | 0 | 64.760 | 64.760 |
| Climbing only | 5.000 | 0 | 5.000 |
| Persistent joint | 1.667 | 0 | 1.667 |
| Transient joint | 0 | 0 | 0 |

At the nine frozen presence-only family representatives per family, CT005
accounts for approximately 92.3% of habitat-only and 94.9% of trout-only mean
early-target penalty (averaging the three seed-level shares). Their PR038
seed-level median values are 0.713–0.793 and 0.699–0.766 respectively, consistent
with the score rewarding a larger discrepancy scale when the taxon is absent.
The floor therefore depends on the chosen PR038 upper bound; this nuisance-parameter tradeoff is not independent evidence of observation variability.

The validated mean primary scores in that cohort are 79.13 (habitat only),
78.35 (trout only), 6.96 (climbing only), 3.82 (persistent joint), and 2.56
(transient joint). Much of this separation is already present in the floors.
The weight-one family cohort preserves the same broad ordering: changing the
late-compatibility multiplier does not remove structural early-target penalties.
Decomposing CT004/005 is a diagnostic on frozen sources; we did not remove
those targets, rescore a new calibration, or reselect sources after validation.

Global selections contain no habitat-only or trout-only sources. Across the
three seeds, the climbing/persistent/transient counts are respectively
0/83/67 for presence only, 27/58/65 for independent 0.60, 45/53/52 for
independent 0.98, 0/83/67 for shared 0.60, and 6/81/63 for shared 0.98.
These are counts selected by this search rule, not posterior family weights.
Different prior geometry and parameter counts add further comparison limits.

## Detection, dependence and source selection

Detection remains unidentified from the available field evidence. Each history
was evaluated under presence compatibility only, independent annual detection
at 0.60 and 0.98, and detection perfectly shared within each of the two survey
windows at those same levels. The two windows remain independent. Shared
within-window detection is a sensitivity scenario, not a universal dependence
bound. The annual census proxy and unmodelled conservation collections remain
as specified in the protocol.

The following ranges are across the three search seeds, using each profile's
own frozen global cohort of 50 sources per seed. Each source receives equal
weight in the reported mean. Survival is simulated presence at end-2002.

| Profile | Unconditional survival | Compatibility-weighted survival | Weight-precision qualified / 150 |
|---|---:|---:|---:|
| Presence only | 0.994–0.998 | 0.996–0.999 | 150 |
| Independent 0.60 | 0.605–0.734 | 0.327–0.428 | 136 |
| Independent 0.98 | 0.371–0.462 | 3.76e-8–6.16e-8 | 0 |
| Shared 0.60 | 0.994–0.998 | 0.995–0.998 | 150 |
| Shared 0.98 | 0.888–0.910 | 0.777–0.847 | 146 |

That comparison combines a change in selected parameters with a change in
history weighting. Holding parameters fixed separates them. In the union of
all global cohorts (107, 106 and 110 distinct sources by seed), unconditional
survival is 0.682–0.724. Under independent 0.98 detection, weighted survival is
0.400–0.425; under shared 0.98 it is 0.544–0.548. Within the presence-only
reference cohorts alone, those ranges are 0.880–0.900 and 0.970–0.987. The
near-zero figure therefore depends strongly on selecting parameters with the
independent-0.98 score as well as applying its observation weights. It is not a
general consequence of applying that profile to any fitted parameter set.

The figure uses the fixed global union for this comparison. Its approximate
Monte Carlo error bars describe simulated uncertainty conditional on those
sources and weights; they omit parameter-search uncertainty, uncertainty about
observation assumptions, and unseen rare histories. None of these conditional
survival summaries is an estimated real-world extinction probability.

## Numerical precision, support and search limits

For the independent-0.98 global cohort, median weight ESS is 18.30 from 2,000
histories and median relative Monte Carlo error is 0.233; none passes the
planned joint weight-precision flag. Its validation-minus-refinement score has
median +0.476 and 10th–90th percentiles −3.94 to +6.86. This remains a material
simulation-precision limitation after independent validation. The flag concerns
mean compatibility, not automatic rejection of every endpoint ratio; separate
ratio-estimator errors are retained. A small estimated ratio error cannot
resolve structural assumptions or detect an unobserved rare high-weight event.

Independent 0.60 has median ESS 169.35 and 136/150 qualified sources. Presence
only and shared 0.60 qualify all sources; shared 0.98 qualifies 146/150.
Validation-minus-refinement score medians are zero for these four cohorts;
their 10th–90th ranges are approximately −0.016–0.029, −1.23–1.12,
−0.017–0.031 and −0.239–0.474 respectively (presence, independent 0.60,
shared 0.60, shared 0.98). Stable simulation scores are not historical adequacy.

Every family produced some positive-record-compatible terminal-loss histories
in the full screen. Validation at the frozen sources yielded:

| Family | Validated sources | Histories compatible with positives and extinct by end-2002 | Histories also empty at all seven nondetection proxies |
|---|---:|---:|---:|
| Habitat only | 9 | 0 | 0 |
| Trout only | 15 | 182 | 0 |
| Climbing only | 59 | 13,966 | 11 |
| Persistent joint | 148 | 17,525 | 11 |
| Transient joint | 125 | 16,930 | 14 |

These counts use unequal selected source sets and are not comparative family
rates. The 36 all-empty histories occur at 22 sources. Zero events in 2,000
histories give a pointwise one-sided 95% upper bound of 0.00150 for that event
at that source; zero does not prove a family cannot produce it. First-zero,
last-presence and abundance summaries retain their annual census and censoring
conventions in the verified source archives.

Search remains finite. From 250 to 500 proposals per family and seed, 35 of 75
seed/profile/family discovery curves improved their best screening score by
more than 0.1. The checkpoints are 50, 100, 250 and 500; they provide no basis
for a later-block plateau or convergence claim. Finite first-stage admissions
also limit what refinement can recover. Neither more histories at these fixed
sources nor the weight-one diagnostic cohort explores omitted parameter regions.

## Decision and next scientific step

This tranche meets its fixed computational and diagnostic endpoint. It does
not meet a criterion for historical adequacy, causal attribution, or production
ensemble promotion; no historical-adequacy threshold was defined.

The next useful design is a nested mechanism comparison that retains known
invasive species and their historical forcing in every model, while switching
off specified demographic effects on Pedder galaxias. The definition of those
effects, nuisance parameters and shared historical targets needs an explicit
scientific decision before new calibration. Conservation removal timing, life
stages and the latent-to-census scale also remain unresolved; four collected
fish cannot simply be subtracted from latent abundance. Existing conditional
intervention results are not automatically invalidated by this family-ranking
issue, but this experiment supplies no new causal endorsement of them.

## Reproducibility and verification

The isolated run used repository base `81e37202f6322e37ac7f1b0070402b76b7967a82`
plus the recorded source snapshot. Source, input, protocol and phase manifests
bind the exact files used; this is not a clean-commit-only reproducibility claim.
Local raw mirror: `outputs/remote/conditional_calibration_20260912T034910Z/`.
Remote archive: `/data/codex/scratch/galaxias/conditional_calibration_20260912T034910Z/`.
Raw histories remain outside Git. The compact evidence directory includes the
cross-phase summary receipt, frozen memberships, source comparisons, discovery
curves, parameter diagnostics, target decomposition, paired observation
sensitivity and figure. `completion_receipt.json` binds delivery artifacts and
copied run/analysis manifests.

The conservative 19.5-million planned process-seed domain was checked for
internal and cross-phase collisions and against 175,980 prior process and
parameter-draw seeds. All 7,500 parameter proposal seeds were unique. Local
`make check` passed 137 tests; targeted remote tests and the target-host smoke
passed. Serial and two-worker tiny runs gave identical raw histories and
summaries. Every main phase completed, raw archives were verified against
manifests, all source/profile summaries were independently recomputed, and
final membership ancestry and cross-phase output bindings passed. The final
figure was visually inspected. Independent scientific review checked the
structural score floors, paired-source sensitivity and central interpretation.
