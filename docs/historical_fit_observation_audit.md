# Historical-fit and observation-model audit

Date: 2026-09-08. Internal scientific assessment of the existing Module 4
ensemble; model, targets and calibration outputs remain unchanged.

## Decision

**REPAIR the observation bridge before advancing historical-adequacy claims or
using the retained family hierarchy to motivate new ecological endpoint work.**
Preserve the existing ensembles and Module 5 experiments as conditional scenario
results with their original provenance. This audit does not establish a new
family ranking or invalidate the numerical counterfactual calculations.

The problem extends beyond target weights. The bridge compares collection totals
from different survey programmes using one exposure-free abundance multiplier,
constructs spatial occupancy from those same counts, and scores a known last
capture as the last year of latent presence. Baseline and combined-soft formulations
share these assumptions. Agreement between them cannot validate those assumptions.

## Scope and reproducibility

The audit traces CT006–CT010 to the available source passages, examines archived
Stage B target projections in interpretable units, and rescales existing scores
algebraically to assess leverage. It uses five formulations separately and three
search seeds within each. Baseline and combined-soft are reference bookends;
the single-axis variants diagnose particular scoring changes.

The archive contains 15 contexts, each with 5,000 Stage A proposals, 500 Stage B
sources (100 per family), 20 stochastic historical replicates per source and 12
targets. Fifty sources per context were retained. Context is part of source
identity: repeated proposal IDs in different contexts must not be pooled as one
source or treated as independent new parameter draws.

The [audit script](../scripts/audit_historical_fit_observation.py) verified byte
sizes and SHA256 hashes for all 60 raw files it consumed (116,594,114 bytes),
checked source/replicate/target grain, and processed 1.8 million Stage B target
rows. It reproduced all 15 accepted sets and the published family score minima.
CT007–CT010 penalties were independently reconstructed from stored projections
and parameters. CT006 lake presence was **inferred** from its archived penalty,
capture index and refuge presence; its range was checked, but it is not an
independent trajectory validation.

Reproduce from the existing local archive:

```sh
uv run --locked python scripts/audit_historical_fit_observation.py
UV_LOCKED=1 make check
```

Input bindings and aggregation definitions are recorded in
[audit_metadata.json](../data/historical_fit_observation_audit/audit_metadata.json).
No new historical ensemble runs, recalibrations, counterfactual replays or
dependencies were needed. The complete project checks passed: portability,
compilation and 108 tests, including eight focused audit checks.

## What the retained histories reproduce

Numerical projections below use the median across each source's 20 replicates,
then the median across sources within a context. The displayed value is the
equal-weight mean of those three seed-context medians; brackets show their
minimum–maximum, **not** a confidence interval. Criterion and survival percentages
instead average replicate indicators within each source, sources within context,
then the three contexts. All retained sources have equal weight; their family
mix can differ by context. No statistic averages the five observation formulations.

The reported capture quantities are **capture-equivalent indices**, not
effort-standardised predictions of field counts. The existing bridge cannot
supply the latter.

| Retained-source metric | Baseline | Combined soft | Existing nominal criterion / evidence |
| --- | --- | --- | --- |
| CT006, 1988–1989 capture index | 14.67 [12.92–16.24] | 14.34 [13.22–16.07] | Index 5–20; 11 reported captures |
| CT006, inferred lake-presence fraction | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | Zero in score; lake nondetection in sources |
| CT006, refuge-presence fraction | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | Presence supported |
| CT007, projected occupied sites | 1.04 [0.86–1.22] | 1.03 [0.86–1.21] | Nominal 3–7; cumulative five-site evidence |
| CT007, 1990–1991 capture index | 13.95 [11.45–16.38] | 13.78 [11.45–16.25] | 68 reported repeated-visit captures |
| CT008, 1992–1996 capture index | 22.29 [18.24–26.77] | 21.96 [18.24–26.15] | Nominal upper bound 10 |
| CT008, mean latent abundance during 1992–1996 | 86.10 [79.70–92.70] | 81.90 [76.70–89.30] | Nominal upper bound 50; source/date/scope qualification below |
| CT009, fraction surviving through 2002 | 98.90% [98.20–99.60] | 98.33% [97.60–99.20] | Last recorded capture in 1996; subsequent nondetection |
| CT010, mean 1998–2002 capture index | 22.29 [18.12–27.12] | 22.10 [18.48–26.39] | Zero observed detections |

Refuge persistence and the earlier low capture-index range are comparatively
well represented: 65.83% of baseline and 67.00% of combined-soft replicates meet
CT006's 5–20 index range. The typical retained history still has lake fish in
1988–1989, misses the nominal CT007 site/count anchors, and exceeds both CT008
nominal bounds. These are discrepancies in the current scoring system, not
validated biological rejection thresholds.

Selection is a compromise among scores rather than uniform improvement on each
historical pattern. The following percentages compare all 500 eligible Stage B
sources per context with its 50 retained sources. This comparison includes the
changed family mix. The eligible pool has already passed Stage A screening;
it is not the full prior search.

| Replicate property | Baseline eligible | Baseline retained | Soft eligible | Soft retained |
| --- | --- | --- | --- | --- |
| CT007 sites in nominal 3–7 range | 4.40% | 2.27% | 4.18% | 1.80% |
| CT008 capture index ≤10 | 17.42% | 7.77% | 18.06% | 9.77% |
| CT008 mean abundance ≤50 | 27.32% | 19.97% | 27.61% | 22.87% |
| Latent persistence through 2002 | 93.49% | 98.90% | 93.52% | 98.33% |

The three accepted families show the same broad problem. For
`persistent_joint_cause`, `transient_perfect_storm`, and `climbing_only`,
respectively, baseline projected-site summaries are 1.05, 1.13 and 1.18, and
persistence through 2002 is 98.31%, 99.27% and 99.19%. Combined-soft equivalents
are 1.04, 1.07 and 1.03 sites, and 98.08%, 98.00% and 99.17% persistence.
Full family-specific source quantiles and seed variation are in the
[context summaries](../data/historical_fit_observation_audit/context_fit_summary.csv)
and [variant summaries](../data/historical_fit_observation_audit/variant_fit_summary.csv).

### Single-axis diagnostics

All rows use the aggregation definitions above and the retained sources.
Count-share and late-score-share percentages are means of within-replicate
contributions, averaged equally by source and seed. “Sites” is the context-median
summary, while “in range” is a replicate fraction.

| Formulation | CT007 sites | CT007 in range | CT007 count share | Surviving 2002 | CT006–CT010 share of all 12 target scores |
| --- | --- | --- | --- | --- | --- |
| `baseline_current` | 1.04 | 2.27% | 98.66% | 98.90% | 91.26% |
| `ct007_occupancy_primary` | 0.70 | 0.03% | 96.56% | 91.67% | 88.62% |
| `ct009_terminal_window_gap3` | 1.04 | 2.27% | 98.66% | 98.90% | 90.43% |
| `ct010_detection_half` | 1.75 | 10.20% | 98.70% | 99.63% | 89.65% |
| `late_bridge_soft` | 1.03 | 1.80% | 96.14% | 98.33% | 85.55% |

Calling the CT007 variant “occupancy-primary” does not establish that occupancy
drives its score: counts still contribute 96.56%, and nominal occupancy fit is
worse than baseline. Halving the CT010 multiplier permits higher capture indices
and increases CT007 range coverage, while almost all histories still persist.
The terminal-window change reproduces baseline native summaries; lower scores
alone are not evidence of improved historical representation.

## Relative acceptance and ranking leverage

Actual acceptance takes the best 10% of eligible Stage B sources, capped at 50,
using the **median of replicate total penalties**, followed by the existing
historical/intrinsic/IQR/ID tie-breakers. It has no absolute-fit condition.
Published family winners instead minimise the **sum of target-wise median
penalties**. These functionals need not identify the same source or family;
marginal target medians need not describe one jointly fitting trajectory.

The existing published tally of 12 joint-family and three climbing-only wins is
reproduced. Under the actual acceptance distance, the corresponding best-source
families are eight joint, six climbing-only and one transient. These are search
outcomes, not family probabilities.

| Formulation, three seeds each | Published target-median-sum winners | Median replicate-total winners |
| --- | --- | --- |
| Baseline | Joint 3 | Joint 2; climbing 1 |
| Occupancy-primary | Joint 2; climbing 1 | Joint 1; climbing 1; transient 1 |
| Terminal window | Joint 3 | Joint 2; climbing 1 |
| Detection half | Joint 1; climbing 2 | Joint 1; climbing 2 |
| Combined soft | Joint 3 | Joint 2; climbing 1 |

Six algebraic probes preserve each context's existing 500-source pool and
replicate scores. They recompute the original acceptance order and separately
report target-median-sum winners. CT007 count omission retains the original
occupancy coefficient. Fixed PR037 rescales only CT007's count component and
CT010 to the maintained default of 1.2, holding ecology fixed; it is a leverage
test, not a proposed numerical replacement.

| Probe | Baseline retained overlap /50, seed order 10/11/12 | Soft retained overlap /50, same order | Interpretation |
| --- | --- | --- | --- |
| As scored | 50 / 50 / 50 | 50 / 50 / 50 | Exact archive reconciliation |
| Omit CT009 | 50 / 50 / 50 | 50 / 50 / 50 | Large timing penalties have little current selection leverage |
| Omit CT007 count component | 10 / 3 / 13 | 10 / 5 / 14 | Most retained sources depend on this component |
| Omit CT009 and CT007 count | 10 / 3 / 13 | 10 / 5 / 15 | Count component dominates these two changes |
| Omit CT006–CT010 | 16 / 11 / 17 | 17 / 9 / 15 | Late evidence strongly shapes the frontier |
| Fix PR037 at 1.2 | 21 / 18 / 16 | 20 / 16 / 16 | Proposal-specific score scaling has material leverage |

Across the individual contexts, CT009 omission preserves all best-source family
winners and retains 48–50 of 50 sources. Its semantic defect remains, but it is
not the main driver of current ranking. CT007 count omission retains only 3–14
sources, and fixed PR037 retains 14–23. Under fixed PR037, target-median-sum
winners become joint 1/transient 2 in baseline and one each of joint, transient
and climbing in combined-soft. This exposes sensitivity; it does not establish
those alternative winners as better supported ecologically.

Retained median PR037 is 3.18 in baseline and 3.16 in combined-soft, compared
with 2.37 and 2.31 in their respective eligible pools (same source-median/seed
aggregation). This empirical shift accompanies the division-only score leverage
demonstrated below. Full probe results, including all families and single-axis
contexts, are in [rank_leverage.csv](../data/historical_fit_observation_audit/rank_leverage.csv);
the original selections are in
[context_selection_summary.csv](../data/historical_fit_observation_audit/context_selection_summary.csv).

## What the observations support

The [evidence trace](../data/historical_fit_observation_audit/evidence_trace.csv)
records dates, geographic scope, effort, unsupported inferences and unresolved
information separately. Its eight rows retain overlapping source descriptions
without counting repeated accounts of the same surveys as independent evidence.

| Target | Source-supported observation | Mismatch in the current bridge |
| --- | --- | --- |
| CT006 | Eleven reported captures across 1988–1989 and four historically detected streams; no lake records. | A two-year total is compared with a multiplier of mean refuge abundance. No lake records become a requirement for literal zero lake fish. |
| CT007, distribution | Five positive streams are a cumulative 1988–1991 description. Hamr dates the 117-location distribution survey to February 1990–May 1991. | Five of 117 is treated as a simultaneous 1990–1991 occupancy anchor. Spatial occupancy is derived entirely from the capture projection. |
| CT007, captures | Sixty-eight reported captures over 43 visits to two Bonnet Bay creeks, February 1990–September 1991. Fish were normally returned, except broodstock retention. | Captures are not established as distinct fish; visits differ from the 117-site survey footprint. Repeat visits, effort and possible recaptures are absent from the projection. |
| CT008 | Ten collected fish during 1992–1996; a separate retrospective estimate of fewer than 50 fish around initial 1995 listing. | Multi-year collections are compared with a mean abundance index; the rough listing estimate is applied to mean natural abundance throughout 1992–1996. Its derivation and natural-only scope are unverified. |
| CT009 | The last known collection was 6 March 1996. | Exact mode asks for last latent presence in 1996. Soft mode permits last presence in 1992–1996 without penalty, including extinction before the known collection. |
| CT010 | Subsequent nondetection despite intensive annual low-flow electrofishing through 2002; the 2005 assessment specifically describes 1998–2002 surveys. | A mean scaled abundance penalty is used without survey-specific detection or an interpretable probability of the observed nondetections. |

The decisive primary-source details are in
[Hamr 1992](../literature/pedder/hamr_1992_pedderensis_report.md)
(opening history; methods; distribution and population results),
[Sanger 2001](../literature/pedder/Sanger_2001_CES_UTAS.md), and
[Chilcott et al. 2013](../literature/pedder/chilcott_2013_lessons_learned_pedderensis.md).
The final dated record and annual search description are in the
[recovery plan, printed p. 10](https://www.dcceew.gov.au/sites/default/files/documents/tasmanian-galaxiidae.pdf#page=11).
The [2005 assessment](https://www.dcceew.gov.au/environment/biodiversity/threatened/assessments/galaxias-pedderensis-2005)
identifies unpublished IFS field logbooks. The fewer-than-50 statement occurs in
the [2023 listing statement, p. 4](https://nre.tas.gov.au/Documents/Galaxias%20pedderensis_LS_APPROVED%20BY%20GM_15062023.pdf#page=4)
and does not provide the estimate's method or explicitly restrict it to natural
populations. E037's description as a “lower-bound” anchor is also inconsistent
with “fewer than 50”.

Hamr's narrative suggests three detected streams during the later distribution
survey, including one Stillwater fish followed by five unsuccessful revisits.
This is a reason to recover the original site table, **not** to silently replace
five with three: local transcription has degraded numerical table cells. The
five specimens reported for 1994–1997 in the 2005 assessment can coexist with ten
for 1992–1996; the differing windows do not establish a contradiction.

## Why weight changes are insufficient

In [observation.py](../src/galaxias_model/observation.py), the capture-equivalent
index is `C = q * mean(N)`, where `q = PR035 * PR036`. These two parameters enter
this bridge only through their product. Survey duration, visits, geographic
coverage and catch-return history do not enter. The same expression therefore
imposes abundance ratios when comparing heterogeneous collection totals.

CT007 predicts `sites = 117 * (1 - exp(-alpha * C))`, with
`alpha = -log(1 - 5/117) / 68`. Thus 68 captures maps to five sites by construction.
The nominal 3–7 site interval is equivalent to `C = 40.443–96.054`. CT006's upper
capture index of 20 maps to only 1.493 sites. Under shared `q`, reaching even the
lower CT007 occupancy bound from the CT006 upper bound requires more than a
twofold rise in mean refuge abundance; matching the 11 and 68 anchors requires
6.18-fold growth. This demonstrates imposed rebound pressure, not biological
proof that a rebound could not occur.

In [scoring.py](../src/galaxias_model/scoring.py), the count discrepancy is much
larger than the occupancy discrepancy. Even at `C = 20` and the maximum PR037 of
4, counts contribute 93.97% of the “occupancy-primary” CT007 score (97.91% in the
baseline). Merely changing the coefficients from 0.5/0.5 to 0.75/0.25 leaves a
predominantly count-driven constraint on a quantity that is already count-derived.

For CT010 the raw discrepancy simplifies to `2 * m * q * mean(N) / phi`, with
variant detection multiplier `m` and `phi = PR037`. It is not a calibrated
probability of missing survivors. Positive expected captures allow realised zero
captures; zero discrepancy is therefore a mathematical score property, not a
necessary condition for scientific adequacy. Averaging annual discrepancies also
does not accumulate the evidence from repeated searches.

The numerical identities and scale examples are exported in
[bridge_algebra_probes.csv](../data/historical_fit_observation_audit/bridge_algebra_probes.csv).

Increasing PR037 mechanically reduces CT007's count component and CT010 at fixed
ecology, with no compensating term. It functions as proposal-specific score
downweighting. A lack of values crowded at the prior boundary cannot demonstrate
that this mechanism is harmless or that dispersion has been estimated.

## Smallest defensible correction design

This is a recommended specification for the next tranche, **not an implemented
or approved recalibration design**. Resolve the evidence-to-score mapping before
examining revised family winners.

1. **Respect the positive 1996 record.** Define presence on 6 March relative to
   the simulator's annual census and within-year events. An extinct-before-record
   history cannot receive perfect fit; survival after the record is assessed
   through subsequent nondetection, without an exact-1996 extinction target.
2. **Separate distribution evidence from repeated creek captures.** Preserve the
   cumulative footprint and contraction evidence. Retire the count-anchored
   occupancy curve as a numerical spatial prediction. A replacement numerical
   constraint needs a justified site domain and survey timing; the two-compartment
   model does not itself resolve 117 sites.
3. **Reconcile observation exposure.** Seek the original Hamr survey tables and
   IFS visit records, including dates, reaches, effort, catches, releases and
   removals. Where quantitative exposure remains unavailable, retain counts as
   descriptive evidence or use a small, explicit set of fixed sensitivity
   assumptions. Do not introduce freely fitted window multipliers simply to
   absorb the mismatch.
4. **Align the abundance estimate and lake evidence.** Verify the fewer-than-50
   estimate's population scope and date before treating it as a numerical natural
   population constraint. Carry its uncertainty. Distinguish lake nondetection
   from latent lake extirpation.
5. **Use declared, common discrepancy scales.** Remove the mechanical reward for
   proposal-specific scale inflation. A statistically specified observation model
   is an option if the data support one; constructing a full likelihood is not
   required for honest pattern-oriented filtering.

Evaluation criteria should be fixed before a bounded recalibration pilot:
correct temporal/spatial units; positive records respected; nondetection distinct
from extinction; no automatic score improvement from nuisance-scale inflation;
physical-unit fit distributions shown separately from relative acceptance; and
family sensitivity compared across declared observation assumptions and seeds.
Passing these checks can justify a larger run. Adding replicates to the current
bridge cannot correct its semantics.

## Limits and disposition of earlier results

The archive stores target projections and penalties, not complete stochastic
trajectories or visit-level detection histories. This audit can expose target
misfit and scoring leverage, but cannot reconstruct annual spatial occupancy,
recapture histories or a probability of nondetection. Algebraic reranking uses
only the existing Stage A-screened Stage B pool; it cannot recover sources already
discarded or stand in for recalibration.

The current family hierarchy is a result under the original scoring assumptions.
Retain it as provenance and as a conditional scenario comparison. Existing
Module 5 contrasts still describe what happens to those selected model histories
when pressures are removed. Their precision does not establish historical
adequacy or real-world causal attribution. Defer censored extinction-time and
quasi-extinction extensions until the observation repair is evaluated.
