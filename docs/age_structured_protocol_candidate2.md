# Age-structured renewal: candidate 2 after Fable's review

29 September 2026. This amendment implements Astra's assessment of Correspondence
thread 31 message 650. It supersedes the affected portions of
`age_structured_protocol.md` (candidate 1); that original remains unchanged.
The age/sex kernel, six/eight-year scenarios, census convention, nursery timing,
neutral mapping, post-BH environmental residual and one-year forcing lag stand.
Candidate 2 is the implementation specification. It is not an executable freeze
or a claim that the linked runner and synthetic recovery gate have passed.

## Primary and secondary removal accounts

Use the recovery-plan account for the full 16-cell primary comparison: two
lifespans × two nursery supports × four restrictions. Retain Sanger's account
only at A=6, near-obligate nursery, across four restrictions, giving **20 cells**.
This sensitivity assumes the eleven additional wild fish, relative to the
primary account, were captured in 1990–91 and held until release in 1992.
Holding is an explicit reconstruction; no source has documented these eleven
individuals or their captivity. Do not call Sanger's total disproven.

Hamr reports 18 releases on 1 November 1991 and twelve on 5 February 1992,
eleven of the latter being hatchery offspring. The recovery plan's 31 early
releases require one additional fish beyond those dated releases. Sanger's 42
require twelve. Chilcott's ten reported captures over 1992–96, combined with
the February 1992 adult, four January 1996 fish and March 1996 record, leave at
most four other capture records under an explicit common-coverage assumption.
Thus twelve additional *new* wild captures after February 1992 conflict with
that complete-record interpretation. Previously held fish, offspring or
inconsistent retrospective totals remain possible explanations.

Enforce at most ten reconstructed natural-range removals dated 1992–96, while
retaining the record's distinction between captures and permanent extractions.
Do not add an aggregate ten-count likelihood on top of its dated components.
The five captive deaths are additional to released founders only under the
candidate's non-overlap assumption; 25 versus 36 early removals remain scenario
totals, not recovered field ledgers. The immature fish in Hamr's first release
also means they must not all be described as adults.

Horner et al. (2026) reports approximately 45 founders, including seven captive
offspring. The total is numerically consistent with 42 plus the three May 1997
survivors, but seven offspring conflicts with Hamr's contemporary eleven.
Whether seven was confused with captive adult survivors is unknown. Preserve
this source conflict without adding another model cell.

The possible 1991 allocation of seven captive survivors (4 male, 3 female),
ten newly collected adults (5 male, 5 female), and one immature fish reproduces
Hamr's release sexes. It is one feasible allocation, not an identity match.
It depends on those groups being disjoint; preserve that assumption in the
linked runner. March 1996 retention remains 0/1, January 1996 and May 1997
remain linked, and all 353 Oberon-to-Strathgordon transfers conserve sex/age.

The statement that rescue removed a known fraction of a 50–200 population is
not adopted. The accessible original Lake chapter gives a belief of no more
than 200, attributed to Hamr; a lower bound of 50 has not been located. Hamr's
target of at least 50 fish in Oberon is a management target. Even a recovered
1992 abundance estimate would not be an interchangeable pre-removal denominator
for cumulative captures in 1990–92. Report model-based pre-event removal
fractions by date and sex, with their assumptions, rather than that quotient.

## Creek observation block: 68, 1, 0

Hamr explicitly reports intensive electrofishing of both creeks by two teams
on 4 February 1992, with one adult caught and subsequently released in Oberon.
Include this record before its removal transition. Define:

    X_E = 43 × effort-weighted accessible abundance, February 1990–September 1991
    X_F = e_F × accessible abundance immediately before the 4 February 1992 capture
    X_L = K × rho × effort-weighted accessible abundance, 1998–2002

Use e_F=2 or 4 creek-trip equivalents as separate profiles. Two teams do not
establish a measured doubling of effort: both values are declared scenarios.
Under independent Poisson counts with shared multiplicative catchability,
conditioning on the total 69 gives a multinomial with counts (68,1,0):

    log L = log(69) + 68 log[X_E/(X_E+X_F+X_L)]
                         + log[X_F/(X_E+X_F+X_L)].

`conditional_capture_log_probability` implements the general identity. Do not
also score a February positive, CT007 or separate annual late zeros. A known
capture can enter its observation factor and the consequent removal transition
without being counted as two independent observations. Keep all dated positive
and removal records in every restriction.

Independent captures, common catchability after adjustments, visit allocation
and the possibility of recaptures remain assumptions. Retain the existing K,
rho and age-accessibility profiles. Report an additional quarter-power creek
score beside the untempered score as robustness to excessive concentration.
This is a generalized compatibility score, not a fitted overdispersion model.

## Lake sweep observations and digitisation

The original chapter describes twelve sites, four three-minute sweeps per site,
and ten December visits. Figure 6 has zero catches at plotted times 8,11,14,
mapped to **1983, 1986 and 1989**, using the stated 1977 peak at time 2. These
are three sampled occasions, not annual zeros for every year from 1981 onward.
They show failure to catch fish in the sampled habitat; nursery extinction is
a model-dependent interpretation.

`lake_figure6_digitised.csv` retains source-pixel coordinates, all seven positive
means, unclassified error-bar heights and the three verified zeros. The axis
says SE and caption says SD; neither label is silently selected. The original
PDF and extracted stencil hashes, coordinate calibration and reading band are
in `observation_checks.json`. The halfwidth of 0.08 fish/site/trip is a declared
digitisation band, not a confidence interval or sampling-error estimate.

For primary use, omit time 0 and 0.5 because their relation to the three-site
November 1975 pilot is unresolved. Use the five unambiguous 1976–80 mean indices
and the three zero visits. Under the twelve-sites-per-visit interpretation,
the positive mean sum corresponds to approximately **173 capture equivalents**,
with a conservative reading envelope about **168–178**. These are derived
summary values, not recovered integer catches; do not round them and then
claim an exact Poisson likelihood.

Let X_E and X_L sum equal-effort accessible December lake abundance over these
five and three dates, respectively. Primary accessibility is age 0, with
age-0-plus-age-1 as an observation sensitivity. Use lake relative catchability
rho_L={0.25,1,4} even though nominal effort is constant: changing shoreline
habitat may change accessibility. Score

    S_lake = -tau C_eq log(1 + rho_L X_L/X_E),

with tau={1/12,1/4,1} and C_eq at the centre and endpoints of the digitisation
envelope. Call it a **tempered conditional compatibility score**. Deflation is
not a claim that the uncertain error bars identify dispersion. Keep the
positive mean trajectory as a shape diagnostic, not an additional independent
score derived from the same fish. Remove any existing target that would double
use the Lake record. The source-to-score map must implement that exclusion.

## Reporting and shared-demography assumptions

For every source and every factual/counterfactual endpoint, report

    R_refuge,0 = R0 (1-p).

The fractions above one are 7.628% under the near-obligate proposal support and
67.721% under the legacy support, **before** neutral-allocation rejection.
Report fractions among proposed, algebraically feasible and supported sources
separately. This is a neutral, isolated, low-density replacement index. Do not
use it as a viability filter or infer that every finite persistence history
with it below one is impossible. Existing cohorts, stochastic good years,
movement and reproduction subsidized by lake breeders can sustain finite
occupancy. Above one likewise does not protect against mate limitation or threats.

For post-1996 successful recruitment events, report the factual-weighted share
where participating females≤2 or participating males≤2; define the denominator
as events with at least one surviving newborn. Also report the analogous share
among breeding attempts with both sexes present. These diagnose the consequence
of pooling the two creeks, without claiming all small-pool matings fail.

Keep the 2012 juvenile shares (48/158 Oberon; 27/265 Strathgordon) as diagnostics
for this first comparison, profiled by juvenile selectivity and age/length
mapping. No share score is added on top of a juvenile-positive score. The primary
coarsening decision is deliberate; these diagnostic data cannot then be called
independent validation. Strathgordon 2012 remains outside the primary selection
because of the recorded 2010–11 climbing incursion. Sharing demographic parameters
between the lowland Pedder system and high-elevation Oberon is an explicit
transportability assumption. Independent annual recruitment residuals omit
serially correlated recruitment failures; add neither an arm nor a claim that
this uncertainty has been resolved.

## No-wild-removals counterfactual

At the validated factual sources, use fixed factual weights, identical union
calendars and matched exogenous random streams. Suppress natural-range removals
at their reconstructed dates, leaving fish in their modeled source cohorts.
Also suppress all causally dependent insurance releases and captive offspring,
and their downstream Oberon-to-Strathgordon transfers. No counterfactual rescue
population may be founded with fish never removed from the natural population.
The calendar retains no-op placeholders. State-dependent demographic draws can
diverge after intervention; pairing does not make individual random deaths
identical across different population sizes.

Report paired natural-range occupancy in 2002, loss-time differences censored
at the simulation horizon, and any-site persistence in 2012. The latter prevents
describing possible longer wild persistence while ignoring the insurance
populations. Simulate all sites through 2012 for this endpoint; extend the same
common forcing equations beyond the earlier historical horizon with no added
forcing events. Mark those wild-site years as a conditional projection, not new
observational evidence, and separate the observed-window 2002 contrast.
With no externally supplied founders and zero insurance initial
states, insurance states stay zero in the no-removals counterfactual; this can
be verified as a conservation invariant without separately simulating empty
sites. Retain joint outcome categories and pre-event removal fractions. Do not
score counterfactual histories against factual insurance observations or refit
their parameters. This is a conditional mechanistic counterfactual, not an
identified causal effect or a retrospective verdict on the rescue decision.

## Synthetic discrimination is a gate on claims

Before real-data search, execute a prospectively frozen, bounded recovery test
through the **full linked runner and complete observation profiles**, including
the new creek/Lake blocks. Truth is natural-range occupancy at the stated 2002
checkpoint. Observation counts must be newly simulated, not fixed to the real
(68,1,0) vector. Keep truth-generation, inference-bank and observation seeds
separate from each other and from later search/validation seeds.
Use proper observation generators: Poisson captures as the baseline, and an
independent visit-quality gamma multiplier (shape=rate=1) as a declared
overdispersion stress test on the same latent histories. The powered scores are
analysis rules, not probability distributions from which to simulate. Preserve
all observation-generator settings and results, including failed controls.
For Lake, simulate raw counts at each of twelve sites on each retained trip
with mean `q N_accessible/12` per site, multiplying by the declared site-trip
quality deviate in the clustered case. Collapse counts to per-site trip means;
leave exact zeros as zeros and add a Uniform(-0.08,0.08) digitisation perturbation
to each nonzero mean, floored at zero. Reconstruct early and late catch
equivalents and apply each power profile. Synthetic late catches are allowed to
be positive: use the generalized two-block allocation score, not a hardcoded
historical zero. Site homogeneity and the perturbation distribution are declared
test assumptions, not recovered characteristics of Lake's sampling process.

Proposed allocation within the 24,000-site-history reserve:

- 20 cells × 64 truth sources × 4 joint replicates × 3 sites = 15,360.
- 20 cells × 32 independent inference-bank sources × 4 joint replicates ×
  3 sites = 7,680.
- Up to 960 site histories for fixed positive/leakage controls; no replacement
  draws to force a desired terminal outcome.

Stratify source generation across the refuge-index boundary where reachable;
retain all actual outcomes and infeasibility reasons. This diagnostic design is
not a prior sample. Require both terminal classes and at least sixteen distinct
truth sources contributing to each before declaring a scenario stratum assessed;
otherwise label insufficient support. Average compatibility within balanced
loss/persistence banks before forming the class log ratio. Fix the decision
threshold at zero, not after inspecting results. Report both class sensitivities,
balanced accuracy, confusion matrices, abstention/score margins and source-level
cluster-bootstrap uncertainty. Replicates of one source are not independent
parameter worlds.

An informative stratum passes potential discrimination if balanced accuracy≥0.75,
both sensitivities≥0.70 and the lower 95% source-bootstrap interval exceeds 0.5.
Use informative positive controls and leakage controls with no available
class information. With both controls passing, failure in realistic worlds
prohibits a categorical loss-versus-persistence claim for that column; it does
not mean the real outcome is already known. With informative-control failures,
repair before production. A sparse finite inference bank can itself fail to
represent truth: distinguish that failure from demonstrated lack of information.
If no realistic stratum qualifies, stop before large historical search and
report the identification limit, rather than enlarging compute automatically.

The current tranche runs **observation-only algebraic controls**, not this gate.
One exact control has late abundances (1,1,1,1,0) versus (0.8,0.8,0.8,0.8,0.8).
They have different terminal occupancy but identical total late exposure, hence
the same entire aggregate conditional capture distribution. It remains to be
tested whether such pairs are feasible under each demographic restriction.
The oracle checks also quantify missed detection for constant positive late
abundance versus loss before all late visits, assuming known parameters.
They are an upper benchmark for this observation block, not recovery rates of
the fitted model and not an upper bound for additional informative data blocks.

## Budget and prospective predictions

The proposal now allocates 491,520 initial-search site histories, 245,760 for
one refocus, 245,760 for fresh validation, 10,240 each for the overshoot and
no-wild-removal counterfactuals, 24,000 for synthetic recovery, and 8,000 for
implementation/target qualification: **1,035,520** total, within a **1.1-million**
ceiling. Unused allowance does not authorize extra search. The major search
stages shrink by 37.5%; extra discrimination controls and the second
counterfactual bring the total reduction versus candidate 1 to about 35%.
The cumulative conservative envelope stays below 7.1 million; remote resource,
runtime and exact execution receipts still precede dispatch.

Record predictions before that dispatch: persistence witnesses may concentrate
where the refuge index exceeds one; high-dependence columns may owe apparent
discrimination to observation assumptions; each restriction that makes the lake
nursery sufficiently hostile may admit loss histories. These are predictions
to test, not acceptance criteria, established necessities or targeted outcomes.

No broad historical run is launched by this amendment. Astra owns implementation
of the linked runner, score map and full synthetic gate under the accepted
scientific direction. Routine implementation does not require another approval
exchange. Material changes to the scientific question or resource ceiling do.
