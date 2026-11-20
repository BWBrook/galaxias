# Conditional stochastic calibration

Date: 2026-09-12. State: protocol frozen before fresh calibration histories.
Execution and results will be recorded separately so this specification remains
bound to the run archives.

Barry approved a larger autonomous programme following the terminal-history
screen. The endpoint is a fresh, independently evaluated comparison across all
five mechanism families, with unresolved observation assumptions represented
explicitly. Existing pilot and screen archives remain unchanged. This is a
conditional calibration experiment, not a production ensemble or intervention
analysis, and it does not authorize publication.

## Scientific contract

Use the existing prior pack, simulator, five early historical targets CT001–005,
and intrinsic targets CT011–012. Do not apply deterministic historical screening.
Detection is not estimable from the available evidence; compare these five
scenarios on identical histories:

| Profile | Occupied-domain detection | Dependence |
|---|---:|---|
| `repair_presence_only` | 0 | Presence compatibility only |
| `repair_detection_060` | 0.60 | Independent annual episodes |
| `repair_detection_098` | 0.98 | Independent annual episodes |
| `repair_shared_window_060` | 0.60 | Shared within each survey window |
| `repair_shared_window_098` | 0.98 | Shared within each survey window |

For independent episodes, use the previous bridge unchanged:
`L = I(positive records compatible) * (1-p)^(K_lake + K_natural)`.
For shared detection, use
`L = I(positive records compatible) * (1-p)^(I(K_lake>0)+I(K_natural>0))`.
This corresponds to a common detection uniform within each window, with
independent uniforms between the 1988–1989 lake window and the 1998–2002
natural-range window. Perfect positive dependence is a sensitivity scenario,
not an empirical estimate or a universal bound on all possible dependence.
The presence-only profile is a compatibility bracket rather than a generative
likelihood for all field observations.

Retain the existing annual census proxy and positive-record years. Conservation
collections are not demographic forcing. In particular, do not subtract the
four fish collected in January 1996: the latent count multiplier PR039 is not an
absolute census calibration, life-stage allocation is unknown, January removal
and March detection need a within-year ordering, and earlier collections remain
incompletely dated. Mechanism parameters may absorb omitted extraction effects.
See [the evidence follow-up](terminal_history_evidence_followup.md).

The primary search score remains
`median(early + intrinsic penalties) + 5 * [-log(mean(L))]`.
Every simulated history enters the denominator. Zero sampled compatibility is
infinite discrepancy at this budget; do not introduce a numerical floor.
Retain a separate family diagnostic cohort using multiplier one in place of
five, because that weight is a search preference and may drive scalar rankings.

## Fixed programme and stop condition

1. Sample 500 parameter sources per family for each of three fresh search seeds
   20260912, 20260913 and 20260914: 7,500 sources total. Cache the two deterministic
   intrinsic simulations per source. Preserve exact sampled values and composite
   `(search_seed, family_id, proposal_id)` identities.
2. Screen every source with 100 stochastic historical replicates. Within each
   seed/profile, retain the best 100 finite sources by the primary score and
   best five per family. Also retain five per family by score weight one.
   Use existing historical/intrinsic/IQR/proposal-ID tie-breaking.
3. Freeze the union and simulate 500 fresh refinement histories per source.
   Within each profile's admitted candidates, select the primary global top 50,
   primary family top three, and weight-one family top three. The diagnostic
   cohorts are distinct memberships; duplicate physical sources run once.
4. Freeze that union and simulate 2,000 fresh validation histories per source.
   Never select or replace sources using validation. These histories are
   independent process realizations at selected parameter points, not unseen
   field observations or independent parameter draws.
5. Verify raw-to-summary calculations, summarize search-versus-validation
   changes, family representation, score components, prior-search progression,
   observation/dependence sensitivity, and source-level terminal events and
   Monte Carlo precision. Independently review central claims and produce a
   compact scientific synthesis and handoff.

There are at most 2,250 distinct refinement sources and 1,200 validation
sources, giving a hard envelope of 4,275,000 new stochastic histories plus
15,000 deterministic intrinsic runs; overlap should reduce this considerably.
Use at most 32 workers on the idle 64-thread deep-server, with native numerical
threads fixed to one. Source lives in an isolated remote run checkout, generated
payloads under `/data/codex` according to the Nectar control-plane conventions.
Small local tests and a target-host smoke precede the run. Check actual planned
random-seed domains for collisions before simulation; phase labels alone do not
guarantee distinct random streams. Record the realized counts and runtime.

The closing criterion is a verified conditional comparison with disclosed
precision and search limits. No particular winning family, lower survival,
improved biological fit, or posterior claim is required. This tranche ends
after the fixed validation and one focused scientific review; do not expand
draws or pursue rare-event precision indefinitely. If discovery curves remain
open, report that the searched prior is unresolved. Any new substantive model
formulation, removal forcing, or privileged empirical detection assumption
requires a separate scientific decision.

## Interpretation and numerical qualification

Keep global selection and family diagnostic cohorts separate. Summarize each
search seed and profile, with equal weight per source. Report unconditional
simulated survival and within-source compatibility-weighted survival separately.
Neither source selection frequencies nor family representation are posterior
probabilities or causal attribution. Families have different parameter counts
and prior geometry; minimum scores mix flexibility, search resolution and
biological fit. A zero event count is budget-limited absence of evidence, not
impossibility within a family.

Use ESS >=100, relative Monte Carlo standard error <=0.10 and largest history
weight <=0.05 jointly as a descriptive numerical qualification flag for a
source/profile's mean compatibility estimate. These thresholds concern simulation precision, not historical
adequacy; report all metrics continuously and do not discard unqualified
validation sources. Unobserved rare high-weight histories can still undermine
an apparently reassuring ESS. Weighted survival and abundance also receive
delta-method ratio-estimator Monte Carlo standard errors, computed from
`w*(endpoint-weighted_mean)` over all histories; the weight-precision flag alone
does not qualify an endpoint ratio. These estimates cannot reveal unseen rare
events or resolve structural uncertainty. Preserve zero-event one-sided 95% bounds
`1 - 0.05^(1/n)`. Keep the 1995 survey proxy, end-1996 abundance, and censored
first-zero and last-presence summaries distinct.

No universal historical-adequacy threshold has been established. Report score
components, terminal support and sensitivity without relabelling finite scores
as an adequate historical reconstruction. Observational assumptions, early
targets, extraction omission and the weight-five preference remain explicit
limits even if process Monte Carlo validation is stable.
