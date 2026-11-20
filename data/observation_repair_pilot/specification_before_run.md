# Observation repair: specification and bounded pilot

Date: 2026-09-08. Status: specification fixed before pilot results.

Barry authorized this tranche after the
[historical-fit audit](historical_fit_observation_audit.md): settle the
evidence-to-score mapping, implement the smallest repair and evaluate a bounded
calibration pilot. This is an experimental comparison. Production observation
variants, priors, latent equations and historical ensembles remain unchanged.
No endpoint replay, manuscript preparation or production calibration is included.

## Scientific question

Can a source-level observation score respect known presence and imperfect
nondetection without the unsupported count/occupancy mapping or fitted score
inflation, and does it produce useful historical ensembles under contrasting
fixed detection assumptions?

Success means a correct, reproducible mapping and an informative independent
evaluation. A different family winner is not a success criterion. Neither a
particular family nor a particular detection scenario is preferred in advance.

## Evidence update and mapping

The source follow-up did not recover the original Hamr survey tables or IFS
visit-level logs. Forty-three visits are not 43 measured equal exposures;
their totals cannot standardise catches across the different survey windows.
The fewer-than-50 estimate remains a retrospective, uncertain-scope statement.
Hamr's contemporary 1995 account instead describes apparently fewer than 100
fish, also without a quantitative estimation method. Both remain contextual.

The [1997 recovery plan, §§1.1.2 and 1.1.6](https://www.dcceew.gov.au/environment/biodiversity/threatened/recovery-plans/pedder-swan-clarence-swamp-saddled-galaxias)
adds relevant detail: three streams were detected in the later 1990–1991 survey;
20 wild Bonnet Bay fish and 11 captive juveniles founded Oberon during 1991–1992;
four wild fish were removed in January 1996, with three survivors transferred
to Oberon in May 1997. The transfer year is not their removal year. Hamr records
an 18-fish November 1991 release after holding and a February 1992 capture and
removal, but the complete natural-range removal schedule remains unresolved.
The pilot does not amend the demographic forcing to invent that schedule.

| Evidence | Experimental use |
| --- | --- |
| Refuge captures in 1988, 1989, 1990, 1991, 1992 and 1996 | Necessary presence conditions, represented jointly on each history. Positive records within the same domain/year enter once. |
| Lake nondetection in the 1988–1989 surveys | Two annual lake-domain nondetection episodes under fixed sensitivity assumptions. Survey intensity and independence are assumptions, not recovered field facts. |
| Five cumulative positive streams / 117 survey locations | Descriptive distribution evidence; no numerical site prediction from the two-compartment model. |
| Eleven, 68 and ten collection totals; 43 visits | Descriptive, with dates and footprint preserved. No fitted count index or inferred abundance ratios. |
| Rough circa-1995 abundance estimate | Descriptive until date, derivation and natural-only scope are established. |
| Last known record, 6 March 1996 | Requires presence compatible with the record; later survival is permitted. |
| Nondetection during 1998–2002 | Five annual natural-domain nondetection episodes. This conservative documented block does not imply no survey in 1997. |

The complete earlier source trace remains in
[evidence_trace.csv](../data/historical_fit_observation_audit/evidence_trace.csv).
Additional local passages are in [Hamr 1992](../literature/pedder/hamr_1992_pedderensis_report.md)
(methods, population results and late update) and
[Hamr 1995](../literature/pedder/hamr_1995_envirbiolfishes_pedderensis.md)
(Remarks). Repeated source accounts of the same events are not extra observations.

## Annual census convention

The simulator advances each year's population before recording it. For this
pilot all annual observations use the **early-year proxy**, the previous year's
recorded state. Thus the March 1996 presence condition uses the 1995 recorded
state; it does not require survival through the entire 1996 transition. The
January 1996 refuge collection supports a refuge-domain condition in that same
annual bin. Positives use refuge states recorded in 1987, 1988, 1989, 1990, 1991
and 1995. Lake nondetections use lake states in 1987 and 1988; natural-domain
nondetections use total states in 1997–2001.

This is a declared coarse timing approximation. Some survey dates are not known,
and the model cannot resolve January–March mortality or within-year refuge
movements. It does not reproduce the exact collection dates. End-1996 and
end-2002 abundance are separate physical diagnostics.

## Fixed observation scenarios and source score

| Profile | Fixed detection probability per occupied-domain annual episode |
| --- | --- |
| `baseline_current` | Original scoring, used only as a paired control |
| `repair_presence_only` | Nondetection omitted (`p = 0` in the compatibility calculation); positives still constrain histories |
| `repair_detection_060` | 0.60 |
| `repair_detection_098` | 0.98 |

The two nonzero values are the bounds already used for PR035, now treated as
explicit hypothetical scenarios rather than fitted quantities or measured
catchability. They have the same values across sources, families, compartments
and years. Conditional independence across the seven nondetection episodes and
equal occupied-domain detection are simplifying sensitivity assumptions.

For replicate `r`, let `I_r` indicate compatibility with all positive records,
and `K_r` count the occupied domains among the two lake and five natural-range
nondetection episodes. Then

```text
L_r = I_r * (1 - p)^K_r
D_late = -log(mean_r L_r)
D_total = median_r(sum of weighted CT001–CT005 and CT011–CT012 penalties)
          + 5 * D_late
```

An empty domain has nondetection compatibility one; an occupied domain can still
be missed. The score factors into `-log(positive-compatible fraction)` plus
`-log(mean nondetection compatibility conditional on positive compatibility)`.
It averages all replicates before taking the logarithm. A median of binary
positive-record penalties would conceal incompatible histories and is not used.

The block weight of five retains the existing individual late-anchor priority
as one declared block weight, without counting duplicated CT006–CT010 summaries
as independent targets. This remains a composite pattern-scoring experiment,
not a full likelihood or posterior. Positive events supply necessary occupancy
conditions; for the nonzero detection scenarios, detection factors constant
across compatible histories are omitted. The presence-only profile omits the
nondetection data; it is not a generative claim that positive surveys had zero
chance of detecting fish.
Scores from different profiles are not directly comparable as absolute fit.

A source with no positive-compatible histories in the sampled replicates is
ineligible at that Monte Carlo budget. No finite penalty floor invents support;
zero sampled support is not proof of zero underlying model probability.
PR035–PR037 have no influence on repaired scores. Their original sampled values
are retained to preserve the paired parameter draws and original control.
PR038 and all CT001–CT005/CT011–CT012 definitions are unchanged and remain outside
this late-observation repair.

Binary detection conditional on an occupied domain cannot distinguish one fish
from many. Consequently this pilot cannot calibrate absolute abundance from
nondetection. It tests a modest interpretation of the available information.

## Pilot envelope fixed before execution

- Five original mechanism families; two new search seeds, 20260908 and 20260909.
- 100 prior proposals per family and seed, shared across all four profiles.
- Deterministic Stage A: retain the best 20 per family and profile. Simulate the
  union of retained sources in Stage B; each profile may select only from its
  own Stage A set.
- Stage B: 20 stochastic historical replicates per source; deterministic
  intrinsic-baseline scores cached from Stage A. Shared source/replicate seeds
  across profiles provide matched process histories, not independent experiments.
- Retain the best 10% of finite eligible Stage B sources per profile/seed,
  capped at 50; at full coverage this is ten sources per context.
- Independently evaluate the union of selected sources using 100 new historical
  replicates per source in a separate seed namespace. Preserve original
  selection; do not select or tune using validation outcomes.
- Use the original overall/historical/intrinsic/historical-IQR/proposal-ID
  tie-break order; the repaired late block is constant at source level.
- Upper bound: 1,000 prior sources, 800 Stage B sources and 80 validation sources;
  at most 27,000 scenario simulations including deterministic baselines.

Deterministic histories may retain positive but very small populations. If all
their binary occupied-domain states match, the repaired detection scenarios
have identical Stage A rankings; stochastic late compatibility then enters only
in Stage B. This is a limitation of the screening design, to report rather than
silently fix by changing the search after seeing outcomes.

Tiny local tests establish semantics and control parity. The bounded pilot runs
on `deep-server-ts` using at most 16 worker processes, one shared source snapshot
and locked Python 3.14 dependencies. The host was lightly loaded at preflight
with 64 logical CPUs and over 110 GiB available RAM. Existing remote clones are
preserved; use a new run-specific snapshot under `/data/codex/repos` and payloads
under `/data/codex/scratch`.

## Evaluation fixed before results

1. Confirm dated-presence semantics, positive incompatibility, occupied-domain
   nondetection, unique episode counting, source-level averaging and absence of
   PR035–PR037 influence using constructed histories and analytic checks.
2. Reproduce a tiny original calibration control using identical proposals and
   seeds. Check profile pairing, source identity, score decompositions, selection
   membership, and disjoint validation seeds. Preserve source/config/input and
   output hashes without modifying historical raw artifacts.
3. Report each profile and seed separately: family composition, early/intrinsic
   scores, positive-compatible fraction, conditional nondetection compatibility,
   abundance and compartment presence, and end-2002 persistence. Summaries weight
   sources equally within context; seed summaries remain within a profile.
4. Compare search and independent validation estimates for the frozen selected
   sources. Report the effective number of compatibility-weight contributions
   `ESS = (sum L)^2 / sum L^2`, largest contribution, and Monte Carlo relative
   standard error. Flag validation ESS below ten or a single contribution above
   20% as a precision warning, not a biological rejection rule.
5. Distinguish a semantic repair from historically adequate calibration. Strong
   sensitivity to assumed detection or rare compatible histories is an informative
   pilot result. Do not choose a detection scenario, enlarge the run or promote a
   family because it produces a preferred ecological story.

The closing decision will state whether the repair is working, what independent
evaluation supports, and which scientific choice or next analysis is needed.
Neither fixed detection value becomes the main scientific formulation through
this pilot alone.

## Execution and results

Pending the frozen-specification pilot. No pilot result informed the choices
above; add execution receipts, validation and scientific findings here.
