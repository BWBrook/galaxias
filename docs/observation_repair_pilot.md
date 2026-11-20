# Observation repair: specification and bounded pilot

Date: 2026-09-08. Status: bounded pilot complete; semantic repair passes,
historical ensembles remain qualified.

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

**Decision: retain the experimental repair; do not promote these pilot ensembles
to the main historical analysis or endpoint work.** The code respects the
declared observation semantics, but detection assumptions, limited search and
concentrated Monte Carlo weights materially affect the retained histories.
Neither historical adequacy nor a preferred mechanism family is established.

The exact [specification before execution](../data/observation_repair_pilot/specification_before_run.md)
is preserved with SHA-256
`0389e2f015ab16b0a3a1e7b0312b1b374016ae01e22c1db08d9067630c4fb1a2`.
Its contents match the specification bound into the remote run manifest.
The sections above record that design; this closing section was added after
execution and independent validation.

### Execution and verification

Run `observation_repair_pilot_20260908T004649Z` completed on `deep-server-ts`
with exit code zero in 89.455 seconds using 16 workers, Python 3.14.5,
NumPy 2.4.6 and pandas 2.3.3. Its source snapshot comprises commit
`81e37202f6322e37ac7f1b0070402b76b7967a82` plus the hashed experimental overlay.
The 15,480 scenario simulations comprised 1,000 deterministic histories,
2,000 intrinsic baselines, 6,980 Stage B histories (349 distinct sources),
and 5,500 independent validation histories (55 distinct selected sources).
There are 80 selected source/profile records: ten in each of eight contexts.

All seven raw data-file size/hash bindings and 33 source/input bindings were
verified. The archive summariser independently reconstructed Stage A and final
selection, checked source and replicate coverage and disjoint random-seed
namespaces, and recomputed compatibility scores and weight diagnostics.
The full project check passed 121 tests before execution; the subsequent
summary regression test also passed. The remote smoke and 13 focused repair
and runner tests passed. Independent methodological review reproduced four
source-level calculations from raw histories and found no implementation defect.

The [receipt](../data/observation_repair_pilot/receipt.json) binds the raw files,
analysis helper and three compact outputs:

- [source_validation.csv](../data/observation_repair_pilot/source_validation.csv):
  all selected sources, search versus validation scores, physical diagnostics
  and precision warnings;
- [context_summary.csv](../data/observation_repair_pilot/context_summary.csv):
  separate profile, seed, family and phase summaries, including early/intrinsic
  scores and abundances;
- [selection_overlap.csv](../data/observation_repair_pilot/selection_overlap.csv):
  paired selection overlap within each search seed.

The local ignored archive is
`outputs/remote/observation_repair_pilot_20260908T004649Z/`.
Remote raw data and launch receipts remain under
`/data/codex/scratch/galaxias/observation_repair_pilot_20260908T004649Z/`;
the isolated execution source remains under
`/data/codex/repos/galaxias-observation-repair-20260908T004649Z/`.
Reproduce the compact analysis without running simulations:

```sh
uv run --locked python scripts/summarize_observation_repair_pilot.py \
  --input-dir outputs/remote/observation_repair_pilot_20260908T004649Z/pilot
```

### Selection and independent histories

All three repaired profiles selected **zero of the ten original-control
sources in both seeds**. This is evidence of a consequential combined repair;
the experiment does not attribute that change to a single removed component.
The 0.60 and 0.98 profiles overlapped by five and six sources respectively.
The three repaired Stage A sets were identical within each seed, as anticipated
from their deterministic binary occupancy states. Stochastic compatibility
therefore could not rescue proposals discarded at that screen.

Every selected source had some positive-compatible independent history. This
does not imply strong support: the least-supported selected source had only
three such histories among 100. One unselected Stage B source in the second
seed had no sampled positive-compatible history and was ineligible for repair.

The following are validation summaries. Each context weights its ten selected
parameter sources equally. "Conditional survival" first weights the 100
histories within each source by `L_r`, then averages those source expectations.
It is conditional on the experimental observation assumptions, not a posterior
probability of a model or an empirical extinction estimate. The control has no
corresponding observation likelihood, so its conditional value is omitted here.

| Search seed | Profile | Positive-compatible histories | Unconditional survival to end-2002 | Conditional survival to end-2002 | Sources with ESS <10 |
| --- | --- | ---: | ---: | ---: | ---: |
| 20260908 | Original control | 99.8% | 98.7% | — | — |
| 20260908 | Presence only | 100.0% | 100.0% | 100.0% | 0/10 |
| 20260908 | Detection 0.60 | 98.8% | 98.2% | 92.5% | 1/10 |
| 20260908 | Detection 0.98 | 97.1% | 96.6% | 70.2% | 3/10 |
| 20260909 | Original control | 97.8% | 97.8% | — | — |
| 20260909 | Presence only | 98.2% | 98.9% | 99.3% | 0/10 |
| 20260909 | Detection 0.60 | 88.3% | 83.7% | 60.5% | 4/10 |
| 20260909 | Detection 0.98 | 74.8% | 69.7% | 39.3% | 7/10 |

The repaired ensembles still often persist through 2002. Their model-internal
mean end-2002 abundances were 234.5 and 188.5 for presence only, 203.0 and 93.3
for detection 0.60, and 127.3 and 28.8 for detection 0.98, in seed order.
These are simulated abundance units, not fish-count estimates inferred from
surveys. The binary detection formulation cannot identify absolute abundance.
Mean early-target discrepancies among repaired contexts ranged from 1.43 to
4.95, and intrinsic discrepancies from 2.88 to 4.57. Their exact context values
are retained alongside the late scores; aggregate scores across different
profiles are not an absolute goodness-of-fit comparison.

Family composition also varied. In climbing / persistent-joint / transient
order, the ten-source counts were 3/2/5 and 3/3/4 for the control; 0/6/4 and
0/4/6 for presence only; 0/7/3 and 1/4/5 for detection 0.60; and 3/4/3 and
1/4/5 for detection 0.98. Habitat-only and trout-only were not selected.
These small, screened-pool counts do not estimate model probabilities or settle
the production family hierarchy.

### Nondetection compatibility and precision

Let `Q` be the mean nondetection compatibility conditional on all positive
records for one source. The table reports the median and range across ten
sources, avoiding a mean that can be dominated by a few compatible histories.
`Q` is not a p-value or a calibrated historical-adequacy threshold.

| Search seed | Detection | Median validation Q | Source range | Sources with a single history >20% of weight |
| --- | ---: | ---: | ---: | ---: |
| 20260908 | 0.60 | 0.0016384 | 0.0016384–0.0078662 | 1/10 |
| 20260909 | 0.60 | 0.0025506 | 0.0016384–0.0729670 | 3/10 |
| 20260908 | 0.98 | 7.87 × 10⁻¹² | 1.28 × 10⁻¹²–1.89 × 10⁻⁵ | 3/10 |
| 20260909 | 0.98 | 8.31 × 10⁻⁶ | 1.28 × 10⁻¹²–0.0016786 | 5/10 |

High detection makes a history occupied throughout all seven nondetection
episodes extremely weakly compatible: `0.02^7 = 1.28 × 10⁻¹²`. This is a direct
consequence of the declared detection and independence assumptions. The weaker
scenario is also not uniformly precise; four selected sources in its second
seed have validation ESS below ten.

Two raw-history checks illustrate the high-detection limitation:

- Seed 20260908, `transient_perfect_storm:p00072`: 99/100 histories met the
  positive conditions, but one history with four occupied nondetection episodes
  supplied 98.34% of compatibility weight. ESS was 1.034. Its 1.66% conditional
  end-2002 survival is too concentrated to interpret as a stable extinction result.
- Seed 20260909, `persistent_joint_cause:p00084`: only 3/100 histories met the
  positive conditions; their occupied-episode counts were 6, 7 and 7. ESS was
  1.081 and the largest weight 96.15%. Mean joint compatibility changed from
  `4.0 × 10⁻⁷` in search to `6.656 × 10⁻¹³` in validation.

For the high-detection sources, individual changes in `D_late` from search to
validation ranged from −7.61 to +0.35 in the first seed and −10.83 to +13.31 in
the second. Validation does not uniformly worsen the selected scores, but it
exposes substantial source-level variability. One hundred fresh replicates
provide an independent diagnosis, not a general precision guarantee.

### Scientific disposition and next useful tranche

The semantic repair is usable for further controlled work. Positive records now
constrain compatible histories without imposing extinction at the last record;
nondetection can coexist with continued presence; and unsupported count/site
conversions and proposal-specific score inflation are absent from repaired
scores. Production variants and previous Module 4/5 results retain their
original definitions and provenance.

The ensembles remain **qualified**. The pilot sampled only 100 prior proposals
per family and screened them deterministically before stochastic evaluation.
It cannot show that the wider prior or model lacks histories compatible with
presence into 1996 followed by nondetection. Nor do the fixed detection bounds
identify actual survey detection, independence or exposure. Concentrated weights
make some conditional physical estimates unstable even within the selected pool.

The recommended next tranche is a **terminal-history feasibility and observation
evidence assessment**: use a small stochastic screen of the same prior pool to
test what the deterministic screen missed; preserve both detection scenarios;
and examine whether presence followed by late loss has usable support across
families. Seek visit-level effort and the natural-range removal chronology in
parallel where accessible. Increase replication only for sources whose rare
histories could change that feasibility decision. Do not choose a preferred
detection value, widen the priors, alter removal forcing or launch production
calibration on the strength of this pilot alone.
