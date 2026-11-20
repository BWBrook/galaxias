# Common-model comparison and abundance-dependent detection

Date: 2026-09-18. Version: review candidate 2. Scientific execution has not begun.

Barry authorised autonomous progress on the direction discussed in Correspondence
thread 31, including Fable's proposal #166 and review #243. This document makes the choices
concrete for Fable's pre-run review. That review precedes scientific replay or
new-model simulation; implementation and synthetic unit tests may proceed.
After review, freeze the accepted text and implementation hashes before dispatch.
Changes before dispatch are prospective amendments, not changes to old results.

## Question, deliverable and stopping rule

Can a common simulator reproduce the stated historical patterns without direct
trout effects, without direct climbing-galaxias effects, or without either, and
how does the answer depend on observation and process assumptions?

Deliver a verified frozen-history detection replay, a comparison of explicit
restrictions under four classes of structure, and conditional overshoot-removal
contrasts. The extraction class is explicitly **minimum dated removals** and
does not test the broader conservation-removal hypothesis. Report compatible examples, unresolved cases, and cases where none
was found at the declared search resolution. A failed finite search does not
prove a mechanism necessary. No posterior family weights, empirical extinction
probability, universal historical-adequacy threshold or publication decision
is implied. The programme ends at its stated budget and scientific synthesis;
there is no automatic escalation to more search or combined structural arms.

The September 12 histories and reports remain immutable. The common-model
implementation will be separate from the frozen legacy simulator, so exact
replay does not depend on a compatibility mode inside a changed kernel.

## 1. Replay before redesign calibration

Replay all 712,000 validation histories at the 356 frozen sources in
`outputs/remote/conditional_calibration_20260912T034910Z/`. Use archived sampled
values, source identities and simulation seeds, not new random streams or new
parameter selection. Use the original Linux runtime: Python 3.14.5, NumPy 2.4.6,
pandas 2.3.3. Verify original source, input, archive and membership hashes.

Before new observation scoring, require agreement with every archived physical,
terminal-event and historical target diagnostic; intrinsic target fields must
agree with their original cached values. Counts, flags and seeds match exactly;
floating diagnostics may differ only within relative/absolute tolerance 1e-12.
Any mismatch stops the replay. Do not regenerate a new baseline to conceal it.
This reproduces old process realisations and supplies missing annual abundance
fields; it is not additional independent process evidence.

Use the same 13 annual domain records as the repaired bridge:

| Outcome | Domain abundance | Record years |
|---|---|---|
| Detection | refuge N_R | 1988, 1989, 1990, 1991, 1992, 1996 |
| Nondetection | lake N_L | 1988, 1989 |
| Nondetection | natural-range N_L + N_R | 1998–2002 |

A record in year y uses the state recorded at y−1. Retain this annual proxy in
replay; section 4 specifies the event-ordering exceptions in the new removal
configuration. Do not claim within-year survey reconstruction. Original positive and
negative records in the same domain/year appear once.

For both outcomes use `p(detect | N,q) = 1 − (1−q)^N`, with fixed
`q = {0.005, 0.02, 0.05, 0.20}`. q is per **model count unit** per annual domain
programme. Calling it measured per-fish catchability would require an empirical
mapping from model counts to surveyed fish that this project does not possess.
Use log probabilities: a=N*log1p(−q), log miss=a, log detection=log(−expm1(a)).
Zero abundance gives zero detection probability exactly; no epsilon floor.

Evaluate three observation representations on the same histories:

1. **Homogeneous:** fixed q, conditionally independent episode outcomes.
2. **Shared quality:** one M in {0.5,1.5}, equally likely, per block; use Mq
   jointly for every record in that block and integrate M after multiplying
   their probabilities. Blocks are early 1988–1992 (five refuge detections and
   both lake misses), the singleton 1996 detection, and late 1998–2002 misses.
   Blocks are independent. Early positive and negative records share M.
3. **Independent quality:** the same two-point mixture integrated separately
   for each episode. This is a diagnostic with identical marginal heterogeneity
   to representation 2; their contrast isolates block dependence. Comparing
   representation 1 with 2 changes both heterogeneity and dependence.

These are observation-quality scenarios, not recovered effort histories.
`E(Mq)=q` preserves marginal detection for one model count unit, not p(N) for
larger N. Integrate quality analytically; do not add observation random draws.
Aggregate each history's joint probability over **all** process histories in
log space. Report log mean probability, ESS, relative MC error, largest weight,
unconditional and weighted endpoints, and ratio-estimator MC errors. Underflow
of the displayed ordinary probability must not become zero statistical support.

Primary comparisons retain the same source sets: all 356 sources, the union of
all old global cohorts, and the old presence-only global cohort. Preserve search
seed and legacy family identity as labels. Do not reselect under q or claim that
this old selected pool tests compatibility of a newly calibrated common model.
Compare the old occupancy profiles on these same sets. No q is selected because
it produces preferred survival or a larger likelihood.

## 2. Common forcing and explicit restrictions

Use the existing transient-model forcing parameterisation as the common
historical forcing, with trout, piscivory, climbing and upsurge present in all
restrictions. Replace the legacy family activation map for new-model runs.

| Restriction | Coefficients fixed to zero | Meaning |
|---|---|---|
| R_H | PR020, PR021, PR027, PR028 | No direct biotic effects on Pedder |
| R_T | PR027, PR028 | Trout effects, no climbing effects |
| R_C | PR020, PR021 | Climbing effects, no trout effects |
| R_J | none of those four | Both biotic pathways available |

PR033 remains free in every restriction. R_H is not a no-environment-change
model: inundation, recruitment/capacity upsurge and habitat effects remain.
These four restrictions do not establish necessity of habitat effects.

Remove H only from the two biotic exposure sums. Keep the existing one-year lag
for T, P and C. Connectivity is the historical post-inundation indicator, not a
new estimated ramp; pre-inundation forcing is zero and the first post-stocking
Pedder exposure uses the following annual transition. Keep current-year H in
habitat mortality and spawn quality. Keep U in recruitment and lake capacity.
Preserve the existing exposure-driven movement path: zeroing a biotic coefficient
removes both its mortality contribution and its contribution to redistribution.

All restrictions share the same non-effect parameter distributions, bounds,
constraints and forcing targets. First-wave nuisance draws are paired across
restrictions and structural configurations. Subsequent refocusing is separate
per restriction; a null may refit nuisance parameters rather than inheriting a
poor fit from R_J. New free effect coefficients PR020/21/27/28/33 use uniform
sampling on zero to their existing upper bounds, with PR020 >= PR021. This is
a declared search distribution permitting weak effects, not an inferred prior.
These zero-inclusive coefficients use the identity transform for refocusing;
do not apply a log transform at a zero bound.
Other active parameters retain the current bounded distributions. PR035–038
are unused in the new observation/target formulation and fixed for storage.

Report derived annual exposures, not separately identified coefficients.
PR034 and refuge vulnerabilities enter as products; forcing amplitude and
vulnerability also trade off. A pathway is descriptively “below 5% peak annual
mortality” only if its isolated `1−exp(−hazard)` is below .05 for every relevant
stage/compartment/year during 1972–2002. This is not a declaration of ecological
irrelevance: recruitment and movement can amplify small hazards over time.

## 3. Evidence targets and count scale

CT004 is a common forcing check (stocking, trout increase, piscivory increase),
not evidence that the trout effect on Pedder is required. It is evaluated once
for a shared forcing draw. Keep overshoot parameters PR018/19 free in every
historical restriction; remove overshoot only in the later counterfactual.

Replace CT005's two level penalties with one directional museum contrast:
`N_L,1980 > 0`, `C_L,1983 > 0`, and
`C_L,1983 * N_L,1980 > C_L,1980 * N_L,1983`.
The threshold is zero change: the source supplies no defensible magnitude.
Use raw latent Pedder counts, not N/(N+K). The cross-product inequality avoids
pseudocounts, handles valid one-sided zeros and is invariant to constant
multiplicative species scales. It assumes unchanged relative catchability and
that the climbing index is proportional to comparable abundance over the two
years; neither assumption is verified by the few museum lots. This contrast
remains a demographic pattern because N changes across restrictions. It is
**not** a forcing-only QC check. Report original dominance levels descriptively
and CT005 pass fractions separately by restriction and configuration.

A history's early-pattern indicator requires: presence in both compartments in
all pre-flood years 1965–1971; a lake boom peak in 1975–1980 above both pre-flood
1965–1971 and late 1988–1991 means; peak year within 1976–1978 (the existing
one-year tolerance around 1977); and the CT005 contrast. CT004 must pass for
the source. Record each component separately. Evaluate these patterns and the
binary observation likelihood on the **same history**, rather than combining
an early median from one subset with late support from another.

Founder counts do not identify PR039. The code uses products PR008*PR039 and
PR009*PR039, and transports the same capacities into Oberon, Strathgordon and
Pedder without area scaling. Known founders and CT011 constrain those assumed
products; they do not independently estimate historical Pedder capacity.
Therefore new primary historical selection excludes CT011/12 count penalties,
but restores a binary intrinsic-viability requirement V from the two existing
deterministic insurance scenarios. For each new source require:

- Oberon N_total > 0 at every annual state from its first founder addition
  through 2012, N_total(2012) greater than the total founders added (34 in the
  current scenario), and first juvenile year no later than 1997.
- Strathgordon no juveniles in 2001–2007, juveniles present in 2008, and positive
  total population in 2012. The pre-2008 condition is imposed by the spawn
  schedule and is a consistency check, not independent evidence of fit.

Cache these diagnostics once per exact nuisance/scenario source, including all
annual states needed for the checks. The old cached endpoint projections alone
cannot certify continuous persistence; do not infer missing diagnostics from
them or modify the archived cache. These deterministic checks use the same
baseline scenarios across restrictions and configurations; environmental noise
and historical removals are not added to insurance scenarios. Define
I_early = V * I_historical_patterns, with CT004 also required at source level.
Keep V and each historical component separately visible. V-failing proposals
retain their identities and failure diagnostics, receive W=0 and cannot be
parents or retained candidates. Do not replace them with extra proposals; a
wave with no viable local parents uses its allocated local slots as global draws.
There is no deterministic historical-trajectory gate.

This is a growth/persistence screen without fitted count penalties, not literally
scale-free: founder counts and transported capacities still enter. It filters
intrinsically poor establishment scenarios but does not guarantee a viable or
large historical refuge. Founders enter the insurance lake; growth there can
coexist with very small K_R. Retain the current capacity-product distribution;
no invented area multiplier or hard lower refuge-capacity cutoff is introduced.
Site-specific capacity modelling is outside this tranche.

For all proposals and validated witnesses report K_L, K_R, PR011, K_R/PR011,
PR033 and realised annual N_R by restriction, configuration, search seed and q
profile. Flag K_R<20 as a declared diagnostic, not empirical inadequacy. For each
compatibility cell report witnesses with K_R<20 and K_R>=20 separately; label
support found only below 20 as **low-refuge-capacity-dependent support**. Also
show retained PR033 distributions so upsurge-only or weak-habitat witnesses are
visible. Capacity and PR033 are not separately identified biological estimates.

### Prospective habitat-only observation reference

R_H has zero direct refuge exposure, but its abundance is not determined by
K_R alone. In the deterministic annual map the resident refuge total is
X_R/(1 + PR011*X_R/K_R), followed by lake immigrants. X_R includes survivor
terms and recruitment from both compartments, whose spawn quality depends on
habitat. Habitat-driven lake-to-refuge movement also remains. Thus K_R is a
density-dependence scale, not an equilibrium count; the resident term saturates
at K_R/PR011, and immigration can add to it. Demographic stochasticity and
nonlinear density dependence further preclude an exact R_H prediction from
(K_R,q) alone (`src/galaxias_model/simulation.py`, `_advance_pedder_state`).

Before simulation record the analytic **constant-refuge observation reference**:
N_R=n at every observation, N_L=0, no removals, and early/viability indicators
set to one solely for this calculation. With seven positives in the common
model (section 4), L_ref(n,q)=[1-(1-q)^n]^7*(1-q)^(5*n).
This reference intentionally omits the historical boom and other dynamics; it
is not itself a compatible R_H trajectory. Its homogeneous maximum is at
n*=log(5/12)/log(1-q). The late-miss factor alone is (1-q)^(5*n), not the full
likelihood. The thirteen-record replay reference instead has exponent 6 for
positives and optimum log(5/11)/log(1-q).

Tabulate the reference over n={1,3.75,10,20,50,70,100,200} and all four q values,
including the prescribed shared-quality mixture. It can be plotted against a
capacity axis only under the explicit simplifying assumption n=K_R. Compare
new R_H trajectories with these count/detection predictions after the run;
agreement would expose observation/scale sensitivity, not prove habitat caused
or could not cause extinction. Neither this reference nor V closes the remaining
small-refuge loophole; capacity-stratified reporting makes it visible.

The pre-run table is `data/common_model/constant_refuge_observation_reference.csv`,
reproducible with `uv run python scripts/tabulate_detection_reference.py --output
data/common_model/constant_refuge_observation_reference.csv`. This is analytic
evaluation only; no ecological trajectory has been simulated for it.

| q | Homogeneous optimum constant refuge n (14-record reference) |
|---|---:|
| .005 | 174.656 |
| .02 | 43.334 |
| .05 | 17.068 |
| .20 | 3.923 |

## 4. One-at-a-time structural comparisons

Four classes require six numerical configurations; they are not combined.

| Class | Configuration |
|---|---|
| Base | common forcing/gating, demographic noise, stage-neutral biotic mortality, no explicit removals |
| Environmental survival | base plus annual shared juvenile survival Beta(mu*kappa,(1−mu)*kappa), mu=PR001; rho=1/(kappa+1) is .02 or .10 |
| Juvenile climbing | base with juvenile climbing mortality hazard doubled; adult climbing hazard and movement retain the base coefficients |
| Minimum dated removals | base with the two confirmed-date extraction events below; 1996 allocation adult-first or juvenile-first; does not test the broader removal hypothesis |

The environmental distribution preserves mean juvenile survival, not expected
population size. Annual draws are independent through time and shared across
lake/refuge compartments. Adult survival is unchanged. Use a separate
environmental stream so adding the deviate does not shift demographic draws.
Retain the same deterministic burn-in in all configurations; stochastic dynamics
start in 1965. Do not promise increased extinction or improved observation ESS.

The juvenile climbing multiplier is fixed at two as a structural sensitivity;
no second unsupported coefficient is fitted. It multiplies PR027/28, so R_H and
R_T remain pure zero-climbing restrictions. It affects mortality only and does
not silently double movement response. It is not an egg-predation model.

Use the strict confirmed-date subset: one **adult** removed from Bonnet Bay
Creek 1 on 4 February 1992, and four stage-unknown wild fish removed in January
1996. In 1992 observe the early-year state, remove one adult, then transition.
In 1996 evaluate a January positive on the pre-removal early-year state, remove
four, evaluate the March positive on the post-removal state, then transition.
The March probability is not evaluated on the unmodified N_R(1995). This annual
approximation has no intervening January–March demographic transition.
Counts insufficient for documented extraction make the history incompatible;
never silently reduce the observed removal or create fish. For 1996 compare
adult-first versus juvenile-first, spilling to the other stage only when
required. These allocations are not guaranteed bounds on long-term effect.
Remove from the refuge compartment in both cases.

Use both January and March 1996 positive records in **all new-model
configurations**, including no-removal configurations, so comparisons share the
same evidence. They have the same state when no extraction is imposed. The
common model therefore has 14 records: seven positives and seven negatives;
the January and March positives share one 1996 quality block. Conditional on
state and quality, event outcomes are independent, a declared observation
assumption. q is now per model count unit per specified record, with equal q for
the two 1996 events despite unknown effort. This does not establish measured
per-fish detection. The archived replay retains its original 13-record bridge
and may not be ranked against the new 14-record likelihood as a model contest.

Every table, plot legend and results section must call this arm **minimum dated
removals** and state that it **does not test the broader removal hypothesis**.
It omits the substantial 1990–1991 Bonnet Bay collections highlighted in Fable's
review (20 wild founders in the proposed window reconstruction), captive losses,
and other incompletely dated extractions. A null contrast cannot support
“removals did not matter”. This accepts Fable's explicit narrow-scope alternative
to adding the bounded-window arm, preserving the six-configuration budget.
Hamr's 1991 release group includes an immature fish; an all-adult window
allocation would itself require qualification. Captive-born juveniles are not
additional wild removals. May 1997 is a release date for three survivors, not an
extraction date. A broader window-removal comparison remains outside this
tranche. Evidence: `literature/pedder/hamr_1992_pedderensis_report.md`,
`docs/terminal_history_evidence_followup.md`, and Correspondence #243.

## 5. Search, validation and interpretation

For each of six configurations and four restrictions use two fresh search
seeds, 20260918 and 20260919. Three fixed waves each evaluate 200 sources with
64 stochastic histories: 28,800 sources and 1,843,200 screening histories.
Wave 1 samples the full bounded distribution. Waves 2/3 each use 80 fresh global
draws and 120 local perturbations, preserving a global exploration component.
Local parents are sampled uniformly from the union of the previous wave's best
20 sources per primary observation profile. Perturb free continuous parameters
in their declared transformed space with standard deviations .20 and .10 of
the full transformed bound width in waves 2 and 3; round discrete parameters,
reject violations and remain inside original bounds. No Gaussian approximation
to a posterior is claimed. Preserve the best sources across all completed waves.

Eight primary profiles are the four q values crossed with homogeneous and
shared quality. Independent-quality mixtures are scored as diagnostics at all
sources but do not create another search. Rank by mean joint weight
`W = V * I(historical early patterns) * L(binary records | history,q)`; no weight-five score or
nuisance variance can deflate it. Among V-passing sources with sampled W zero, refocusing tie-breaks use
early-pattern pass fraction, then binary-record likelihood, then source ID.
All histories enter denominators for viable sources; a source failing V has
W=0 by definition and does not consume stochastic histories. Saved runs are
not reassigned to extra search. No deterministic historical gate is used.

Per configuration/restriction/seed retain 20 sources per primary profile for
256 fresh refinement histories; after refinement freeze five per profile for
1,024 fresh validation histories. No validation reselection. Union duplicates
run once. At most 7,680 refinement and 1,920 validation sources imply 1,966,080
histories in each phase. Keep all candidates and component summaries, including
unsupported and imprecise cases.

The readout is a **conditional compatibility map**, not a causal exclusion set.
Evaluate the declared sensitivity grid of early-pattern probabilities
P(I_early=1) in {.50,.80,.95} and mean same-history joint weights
E[W]=E[I_early * L_binary] in {1e-6,1e-4,1e-2}.
These are transparent numerical criteria, not empirical adequacy standards.
Read the grid only within a fixed q, observation representation and
configuration; absolute joint-weight cutoffs are not comparable across q.
Report continuous values as well as the grid. For every validated source also
report delta_log_W = log(E[W_source]) minus the largest validated log(E[W])
across restrictions and search seeds at the **same q, observation representation
and configuration**. This descriptive reference does not reselect sources,
change witness criteria, estimate model probabilities or support cross-q model
ranking. An unsupported source has delta=-inf if the reference is finite; if
all sources have no observed support the reference is undefined. Report the
reference source identity and MC precision; the observed maximum is noisy and
its normalisation does not remove selection uncertainty. A compatible witness requires an
independently validated source above both cutoffs at that same source with its approximate lower
95% MC bounds above them and the joint-weight precision criteria below. A grid
cell without a witness is “not found at cap”; if candidate intervals straddle
cutoffs or precision fails, label it unresolved. Neither label excludes an
unsampled region or proves causation. Do not use top-K membership as adequacy.

For probability indicators report binomial uncertainty; for continuous joint
weights report mean, empirical MC error and ESS. The joint-weight flag requires
ESS>=100, relative MC error<=.10 and largest weight<=.05. Approximate intervals
and flags cannot reveal unseen rare events. Zero observed support retains the
pointwise one-sided bound 1−.05^(1/n); it is not a family-wide bound. Publish no
causal necessity claim from this finite comparison. Report prior/refocused
search curves, improvement by wave, and the independent global-draw component.

Within each configuration, compare independently refitted restrictions and,
separately, paired toggles at frozen R_J sources. The latter share parameters;
they do not establish whether a restriction could fit after refitting.

## 6. Overshoot counterfactual and budget

At all final R_J sources, replay the historical baseline and remove only the
upsurge-linked component of P (PR018=1), retaining T, U, habitat and climbing
forcing. Use paired demographic/environmental streams. Reuse the factual
observation weights for conditional endpoint contrasts; do not weight the
counterfactual by whether it reproduces the actual observations. CT004's
piscivory-rise check is inapplicable to that counterfactual. Report survival,
minimum abundance relative to pre-flood reference, and censored extinction time.
This removes the piscivory overshoot only, not all transient inundation effects.

Worst-case historical budget: 712,000 old-history replays; 1,843,200 new screening;
1,966,080 refinement; 1,966,080 validation; and up to 491,520 R_J counterfactuals:
**6,978,880 histories**. An overall ceiling of 7.1 million allows small prescribed
smokes, not additional search waves. At most 57,600 deterministic insurance
checks (two per fresh source) are separate and supply the binary viability
screen; they carry no scored count penalty. End early on a source
identity, reproduction, physical-validity or implementation-contract failure.

Run on deep-server after live capacity checks, initially eight workers with
native numerical threads one. On 18 September the original runtime was present,
load was about 24 and available memory about 81 GiB; an ongoing 24-worker dSDM
allocation is not to be interrupted. Use an isolated new source snapshot and
`/data/codex/scratch/galaxias/` output directory. Replay uses the old snapshot;
new-model work uses its separately frozen source. Other compute routing remains
available under the existing authorised resource policy.

## Review and acceptance

Before dispatch, Fable is asked to review five consequential choices: the null
restrictions/gating; CT005's raw-count directional contrast; treatment of
transported insurance capacities and the viability screen; minimum dated
removals and equal 1996 evidence across configurations; the qualified analytical
reference and capacity diagnostics; and q-specific normalised reporting. The
search and 7.1-million compute envelope remain unchanged. Their
review is advisory scientific scrutiny, not independent empirical validation.
Astra resolves routine implementation issues and reports any material departure
from the authorised scientific scope to Barry.

Acceptance requires: exact frozen-history reproduction; identical forcing across
restrictions for matched parameter draws; exact null-effect identities; no H
multiplication of biotic exposure; mean-preserving environmental law; pure
juvenile-only contrast; valid removal accounting; stable full binary likelihood;
serial/parallel agreement; verified selection ancestry and fresh validation;
and one focused independent check of central results. No preferred effect sign,
winning restriction or low survival is required. Code and raw evidence remain
available even if the scientific result is that the planned comparison cannot
support attribution at this resolution.
