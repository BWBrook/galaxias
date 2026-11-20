# Age-structured renewal: candidate 1 for review

27 September 2026. Status: **candidate, not frozen for scientific dispatch**.
Barry approved the next substantive repair/design action. This package implements
and qualifies the demographic primitives and proposes a finite comparison for
Fable's review. It does not run a historical comparison or reinstate the earlier
equifinality, ranking or management conclusions. The archived common model,
mate-guard experiment and two-stage recruitment repair remain unchanged.

## Question and boundary

Can a shared demographic model, with distinct site scales and explicit ages,
sexes, nursery exposure and removals, reproduce the recorded sequence under
habitat-only, trout-only, climbing-only and joint effect restrictions? Which
conditional conclusions about persistence through 2002 change with lifespan,
nursery dependence, removals and the late observation process?

Invader forcing remains present in every restriction. R_H sets all four Pedder
biotic-effect coefficients to zero; R_T sets climbing effects to zero; R_C sets
trout effects to zero; R_J retains both. The trout overshoot remains factual in
every fit. Removing it is a later counterfactual scored with factual weights.
These restrictions concern Pedder effects, not whether the invaders existed.

The reporting horizon for this tranche is a tested demographic candidate,
traceable evidence accounts, a bounded protocol and independent methodological
check, followed by Fable's substantive review. The full linked-site runner,
observation scorer and search driver follow review; they are not implemented or
qualified by this package. No remote job, production restart, extra structural
arm, commit, push or publication is authorized by this document.

## Annual demographic contract

`age_demography.py` stores December counts by lake/refuge, female/male and cohort
age 0 through A. A is six in the base and eight in the sensitivity. These are
truncation scenarios, not estimates of a biological maximum. No plus group is
allowed. Old class A leaves at the following January boundary; a fish born in
year t can breed first at the spawning season of t+2, last at t+A, and is absent
from t+A+1. With this convention, a fish alive during 2002 under A=6 must have
been born in 1996 or later. The implication depends on this explicitly imposed
lifespan; it is not a new field observation.

Survival of an existing cohort over a fractional year d is
`s[a]^d exp(-h[a] d)`. Breeding occurs at fraction 0.75 (early October).
Participation probabilities apply to attained cohort age a+1: zero at ages 0–1,
estimated within declared bounds at age 2, and one at age 3+. These are annual
breeding participation probabilities, not a separately persistent maturity
state. The predicted proportion of breeders aged 3–4 is a diagnostic, not a
target to which parameters will be tuned.

At spawning, actual participating females and males are drawn by binomial
sampling. Females are pooled across the two compartments, with reproduction
requiring at least one participating male. Pooled mating assumes reproductive
connectivity; it does not demonstrate encounter success in scattered creeks.
The deterministic skeleton uses fractional females and a positive male pool;
it is not the expectation of low-abundance stochastic trajectories.

For nursery i, with allocation w_i, effective recruits per female b, spawning
quality Q and recruitment limit C_i:

    x_i = b F w_i Q
    mean_i = [x_i / (1 + x_i / C_i)] Z
    Z = exp(sigma_R z - sigma_R^2 / 2), z ~ Normal(0,1)

Zero C means zero recruitment. Density dependence regulates **incoming recruits
only**. A shared site-year Z acts after Beverton–Holt, so its mean is one and it
does not change the meaning of the conditional mean limit C. The shock is shared
between the site's nurseries; sites have distinct streams. This is a recruitment
residual, not environmental noise inside the stock–recruit function. C is a
mean-recruitment scale, not a ceiling on realized counts. Draw Poisson recruits,
then split sexes 1:1. The deterministic skeleton uses Z=1.
Diagnostics distinguish the mean marginal over Z, the mean conditional on the
realized Z, the Poisson draw before newborn hazards, and surviving newborns;
all mean calculations condition on the current realized breeder pool.

Neutral egg-to-December survival is already contained in b. Newborns incur only
the additional post-hatch threat for 1/12 year. The following year's start-age-0
cohort incurs nursery/climbing hazard for 11/12 year, then leaves that hazard.
Thus nursery exposure totals one year across the boundary, rather than 13/12.
Habitat/trout hazards continue through that final month; their birth-plus-next-
year exposure totals 13/12, as intended. Baseline survival follows the start-age
class throughout the interval, a declared cohort approximation. December age-1+
lake survivors can move to refuge; newborns remain in their assigned nursery.

Historical forcing preserves the common model's one-year invader lag and
connectivity gate. Climbing effects act only on the nursery cohort. Habitat
and trout affect older fish as specified in `age_scenarios.py`. Movement is
driven by habitat plus trout exposure, not an invented adult climbing hazard.
The habitat spawning-quality term is divided by its neutral value. Upsurge
multiplies both potential supply and the lake recruitment limit, preserving
`BH(M*x,M*C)=M*BH(x,C)`. Refuge recruitment limit becomes
`C_R(t)=C_R(0)[1-(1-eta_R)H(t)]` in **all** restrictions, including R_H. This gives
habitat a refuge recruitment pathway absent from the previous common model;
old restriction results therefore cannot be carried over as evidence.

## Neutral initialization and parameter support

Let `l[0]=1`, `l[j]=product(s[0:j])`,
`E=sum(l[1:A+1])`, and
`B=sum(l[j-1] s[j-1]^0.75 m[j], j=2..A)`.
For independently specified neutral age-1+ compartment abundances N_i+:

    R_i = N_i+ / E
    F* = B (R_L + R_R) / 2
    x_i* = b F* w_i
    C_i = R_i x_i* / (x_i* - R_i)

Reject positive allocations with `x_i* <= R_i`; never clamp them into viability.
The returned state has each sex equal to `R_i l[a]/2`. This mapping assumes
shared neutral survival and zero neutral movement. It also reports the expected
male pool and whether it exceeds one. Stochastic runs use integer states and
the actual male guard, never the fractional equilibrium guard.

Site scales are separate: historical lake and refuge each have a neutral
abundance, and Oberon and Strathgordon each have their own total. No single
capacity is transported from a 16-ha lake to the impoundment. For the insurance
sites, the abstract nursery/refuge allocation divides the declared total in
proportion to w; it does not assert mapped stream areas. Their initial state is
zero before founders; neutral abundance only parameterizes recruitment limits.
Historical initialization uses the analytic distribution with each cell rounded
to the nearest integer; the rounding difference is retained in the manifest.
There is no calibrated burn-in or hidden establishment screen.

`data/age_structured_design_20260927/scenarios.json` specifies proposed search
bounds. They are exploration distributions, **not measured or posterior priors**.
The old insurance-informed survival priors are not reused. Survival has separate
s0, s1 and shared s2+ quantities; b is derived from sampled `R0=b B/2`, with a
declared upper mean bound of 1,200 informed only by the reported upper fecundity.
That report is not a measured recruitment rate or a hard cap on a Poisson draw.
No numerical FishLife species prediction has been retrieved or silently assumed.
Published insurance outcomes will enter once as observations, not also as priors
and CT011/CT012-style viability filters. Boundary dependence must be reported;
the proposed ranges need review before being frozen.

Near-obligate lake nursery allocation is uniform on [0.90,0.99]; the separate
sensitivity uses the old PR006 support [0.35,0.90], not its fitted density.
Exactly one is excluded because positive neutral refuge recruitment without
neutral movement would otherwise be algebraically impossible. Common forcing
parameters retain the common protocol's declared supports; superseded Pedder
survival, maturation, fecundity and capacity conversions are not used. Hash the
explicit retained parameter table at dispatch rather than importing changing
defaults. Reject algebraically invalid source draws without replacement and
report their fraction by process cell.

## Founders, removals and dates

The evidence ledger preserves conflicting accounts as accounts. It is not yet
an executable list of unambiguous removals. Hamr directly records 18 releases on
1 November 1991 (9 mature males, 8 mature females, 1 unsexed immature), then 11
hatchery juveniles plus one wild adult on 5 February 1992. The wild adult was
collected on 4 February. The [1997 recovery plan, revised 1999](https://www.dcceew.gov.au/environment/biodiversity/threatened/recovery-plans/pedder-swan-clarence-swamp-saddled-galaxias)
reports 31 early releases: 20 wild and 11 captive-bred. Sanger instead reports
42 releases between November 1991 and November 1992. Later total-founder
summaries do not reconcile these dates and identities.

Propose two explicit **reconstruction assumptions**, subject to review:

1. Primary-plan account: 20 wild founders plus 11 offspring in 1991–92, followed
   by three survivors in May 1997. If the five captive deaths reported by
   Chilcott are additional to released founders, early wild extractions total
   25. Treat the reported 12 captives as seven of the released founders plus
   those five deaths, not an additional 12 removals.
2. Sanger account: 42 early releases, provisionally decomposed as 31 wild plus
   the documented 11 offspring; with the same nonoverlapping five deaths,
   early wild extractions total 36. The split is an explicit assumption, not
   Sanger's stated composition. Neither source account is assigned a probability.

Do not add the six stripped breeding fish as six more removals without identity
evidence. The known 18+1 wild releases leave one additional wild founder in the
primary account, or twelve in the alternative, with unresolved release dates.
This arithmetic locates the missing records; it does not recover them.

Four fish left Bonnet Bay in January 1996; three survived captivity and were
released at Oberon in May 1997. There is no additional 1997 wild removal.
The 6 March 1996 record is a positive observation; permanent extraction is not
established by the accessible wording. Carry March retention 0 versus 1 as a
paired ledger sensitivity inside each account. January's pre-removal detection
and March's detection enter **every** restriction on identical evidence.

Before dispatch, materialize early/late endpoint calendars within each published
date window; known dates stay exact. Capture must precede its linked release,
and holding mortality is assigned only among held fish. Unmeasured capture ages
are drawn from eligible source cohorts; reported release sexes constrain that
allocation. Do not create founders independently of the removals that supplied
them. Holding survival of the known released subset is conditioned on the
release record, not scored again as establishment evidence. The 11 artificial
offspring are new fish, explicitly linked to captive breeding, not extracted
from the wild. The November 1991 release occurs after the main October spawn;
the base allows no 1991 Oberon spawning. Hamr's possible late spawning is a
documented residual uncertainty, not a silently added event.

The 52/22/117/53/109 Oberon-to-Strathgordon transfers in 2001/02/05/06/07 sum to
353. Subtract each actual sex/age vector from the donor and add the identical
vector to the recipient. If a scheduled removal is impossible, give the
replicate zero weight and retain the reason; never cap it or draw replacement
fish. These transfers themselves constrain Oberon production without a second
founder-persistence/growth filter.

`CountEvent` is a primitive for dated pre-spawn and post-spawn events, including
pre-event observation checkpoints. Additions are **start-year cohort ages**;
current-year births enter in December. The future linked-site driver must
coordinate transfers and captivity and audit conservation. That driver and the
source-consistent sex/age conditioning remain mandatory pre-dispatch work.
Strathgordon's early-2007 littoral modification affects the 2007 spawning event;
April 2008 juveniles are observations after that event. Before 2007, a small
spawning multiplier is explored rather than equating nondetection with no births.

## Observation contract and information used once

The observation register distinguishes measured counts, positives, proposed
proxies and personal communications. Chris's answers, relayed by Fable, motivate
scenario choices; they are not unpublished quantitative data recovered from IFS.
No agency reply is required to proceed. Late effort is K={2.5,5,10,20}
coverage-equivalent creek trips over 1998–2002. The recovery plan's proposed six
trips a year is not an observed survey log.

For the early programme, X_E is 43 times mean accessible refuge abundance over
February 1990–September 1991. For the late programme, X_L is K times mean
accessible refuge abundance over 1998–2002, multiplied by a declared relative
catchability rho={0.25,1,4}. Initially allocate effort uniformly within each
window; this is a declared scenario because visit dates are missing. Age-0
accessibility is {0,0.25,1}; age-1+ accessibility is one. Calendar checkpoints
must represent the same within-year convention in both periods.

Under independent Poisson capture counts sharing one multiplicative
catchability, condition on the total 68 captures across the early and late
blocks. Observing all 68 early gives

    log P(Y_late=0 | Y_early+Y_late=68) = -68 log(1 + X_L/X_E).

This removes a common catchability and common abundance scale. It does not
remove different gear, season, creek selection, recapture dependence or
coverage; rho and accessibility are therefore explicit sensitivities. The 68
captures need not be 68 unique fish. The conditional model omits information
about absolute abundance and is not the plug-in approximation
`exp[-(68/43) K N_late/N_early]`. With no late exposure it contributes one;
zero early exposure cannot explain positive captures. Do not also score CT007,
another early positive from that programme, or five separate late annual zeros.

Other positive records use `1-exp(-q X)` with explicit record/gear catchability
scenarios; presence is not deterministic occupancy. Candidate q grid is
{0.01,0.1,1} capture intensity per accessible fish per normalized visit, shared
within a gear/site group, with equal grid weighting only for an explicitly
declared mixture. Report each q profile before any mixture. Do not compare raw
weights between q values. These are scenario rates, not estimates calibrated
by 68/43. January's count also imposes physical feasibility of removing four.

For this first comparison, propose coarsening insurance survey outcomes to
dated adult and juvenile detection/nondetection records, with a declared
juvenile proxy comprising age 0–1 and an age-0-only sensitivity. The 1997 Oberon
postlarval record precedes the May release and directly tests local recruitment.
The net catches and length categories in 2012 remain quantitative diagnostics;
they do not become population censuses. This intentionally uses less information
than a gear-specific count/length model, and needs Fable's review. Never claim
the resulting site scales have been empirically identified. Sparse early
Strathgordon juvenile nondetections get the same detection formulation, not a
hard no-recruitment rule. Published climbing detections in Strathgordon in
2010–11 make a wholly predator-free interpretation of its 2012 outcome
questionable: keep that endpoint diagnostic in the primary comparison and
report its coarsened score separately, without inventing an incursion hazard.

Lake (2001) Figure 6 is now available, but its S.E./SD conflict and half-year
label prevent treating it as raw annual Poisson counts. Before a scientific
freeze, digitize the mean/error-bar coordinates with uncertainty and retain the
image, calibration and source hash. Candidate primary use is a relative shape
diagnostic; no invented sampling-error likelihood. The existing lake chronology
targets may be retained only where they do not duplicate the same underlying
record, with an explicit source-to-score map. CT005, if retained, is a ratio of
the 1983 species ratio to its 1980 value, so a time-constant relative museum
catchability cancels. The present package does not assert this data/score
compilation has been completed.

## Proposed finite comparison and reporting

Two lifespans × two nursery supports × two removal accounts × four restrictions
give 32 process cells. March-retention and feasible early/late removal dates are
balanced source strata within each cell, not an open-ended search arm. All
observation profiles replay the same frozen latent histories. Environmental
variation, nursery climbing, refuge recruitment loss and the reconciled
removals are common base structure. There are no combined exploratory arms.

Proposed ceiling: **1.6 million new site-histories**, not yet dispatched:

| Stage | Allocation | Site-histories |
|---|---|---:|
| Initial finite search | 32 × 512 sources × 16 joint replicates × 3 sites | 786,432 |
| One bounded refocus | 32 × 512 sources × 8 joint replicates × 3 sites | 393,216 |
| Fresh validation | at most 8 sources/cell × 512 replicates × 32 × 3 sites | 393,216 |
| Overshoot counterfactual | at most 2 sources/cell × 256 historical paths × 32 | 16,384 |
| Qualification reserve | checks, target smoke and dispatch reconciliation | 8,000 |
| Total allocation | unused paths are not replacement authority | 1,597,248 |

The 1.6-million allocation plus 5,320,368 previously charged histories and
preserved repair qualification stays below the standing 7.1-million ceiling.
The exact cumulative receipt must be reconciled before dispatch. Unknown
holding-period annual updates also count toward compute planning even though
they are not extra independent wild-site histories. Runtime benchmarking and
finite worker/wall-time limits must accompany the final receipt. Large runs go
to the appropriate remote host, not the Mac mini.

Before freezing search, specify the single refocus kernel and source-selection
rule, seed namespaces, score map and per-cell normalizer from the complete
observation implementation. No data-dependent extra refocus is allowed. Search
weights describe compatibility within these declared scenarios, not probabilities
that a restriction is true. Use one reference shared across the four restrictions
at the same lifespan, nursery, removal account and observation profile, rather
than giving each restriction its own best-fit value of one. Do not carry that
reference across q values or other scenario assumptions.

Fresh validation seeds are disjoint from both search waves. Report effective
sample size and MC standard error for every weighted terminal quantity. A
candidate reporting threshold is ESS≥64 and relative MC error≤0.25 for nonzero
terminal estimates; zeros receive binomial/weighted-tail qualification, not a
zero-error claim. Unresolved precision stays unresolved and triggers no
replacement runs. Failure to find a witness in a finite search is **not** an
exclusion certificate for the whole biological hypothesis.

Report, for each restriction/scenario, feasibility failure reasons, normalized
compatibility, neutral N+ and C scales, historical and post-inundation refuge
counts, the proportion relying on refuge age-1+ abundance below 20, breeder-age
composition, terminal occupancy and evidence leverage. Site scale, catchability,
lifespan and nursery assumptions must accompany every ecological statement.
Counterfactuals keep factual source/replicate weights fixed and do not refit.

## Qualification, review and freeze conditions

This tranche allows at most 128 synthetic site-path executions in addition to
unit tests. No historical data select parameters. Qualification covers analytic
fixed points, census timing, actual sex guards, cohort retention independent of
b/C, post-BH mean-one noise, nursery exposure, dated event accounting, observation
identities and exact serial/two-worker replay on a frozen synthetic calendar.
This is implementation evidence, not demographic adequacy or history recovery.

RNG is keyed by seed, site, year and event/cell. Survival depends on event
breakpoints. Every paired arm/profile must materialize the same union calendar,
including zero-effect placeholders; `complete_event_calendar` checks their IDs,
times and compartments. Arbitrary insertion of an observation checkpoint changes
stochastic histories. The calendar is a hashed input, and changing it invalidates
replay qualification. No bitwise legacy-model parity is claimed.

Fable should review three connected decisions: the cohort/timing and noise
contract; the explicit removal-account assumptions and linked-site conservation;
and the conditional observation bridge plus deliberate insurance-count
coarsening. Prior bounds and retained target definitions remain reviewable.
Then complete the dated runner, source-to-score map, Lake digitisation and
bounded synthetic observation/recovery controls before freezing executable
configuration, source/input/output hashes, search protocol and execution receipt.
Review agreement is not independent empirical validation. A material change to
the scientific question or resource ceiling comes to Barry; routine implementation
inside the agreed design does not require another series of permissions.
