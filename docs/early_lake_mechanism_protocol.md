# Bounded recovery of early lake restrictions

4 October 2026. Barry accepted option A in Fable's message 874: use the repaired
model to examine the early lake decline, with a synthetic recovery check before
historical comparison. This is a separate question ending in 1989. The three
terminal-fate attempts remain closed. No rescue-effect calculation, fourth
terminal attempt, adaptive refill or publication is authorized here.

## Question and evidence

The estimand is which of the existing process restrictions can be distinguished
by the early nursery record under a declared engineering distribution. It is
not a probability that a particular mechanism caused the historical decline.
R_H retains habitat change and the productivity upsurge; R_T adds trout effects;
R_C adds climbing-galaxias effects; R_J adds both. All retain identical external
invader trajectories and nuisance draws. R_H is not a no-change control and
R_J does not define an interaction effect.

The scored observations are the eight standardized December visits: 1976–80,
1983, 1986 and 1989. Their digitised means come from
`data/age_structured_design_20260929/lake_figure6_digitised.csv`. The nominal
effort is twelve sites with four three-minute sweeps per site. The 1975 pilot
and ambiguous half-year point remain excluded. Derived capture equivalents
around 173 are not recovered integer counts. Zero visits are nondetections,
not a hard assertion that the entire lake was empty.

The qualitative museum contrast already informs the shared climbing-forcing
support. It is not scored again. The retained sources give no annual species
count denominators; vertebral-screening sample sizes do not supply them. The
model's climbing index and Pedder fish counts also lack a calibrated common
scale, so their quotient is not a museum composition prediction.

The additional 1988–89 lake-absence statement has no recovered effort or
detection denominator. It remains contextual evidence, without an independent
zero-catch factor. If the primary gate qualifies, omitting December 1989 is a
declared sensitivity diagnostic, not another route to qualify a failed gate.
The wild mating-pair correction is documented in
`docs/hamr_spawning_erratum_20261004.md`; that 1991 observation is outside this
response window.

## Process and parameter support

Use the unchanged age/sex kernel and threat adapter, with a Pedder-only runner
from December 1964 initialization through December 1989. Current-year habitat
and productivity combine with the existing one-year invader lag. No events
precede 1990 in the original calendar; no survey checkpoint is inserted into
the stochastic transition. Qualify the Pedder prefix against the linked runner
before dispatch. Insurance populations, their equilibrium checks, removals,
captive groups and transfer constraints are absent from the new runner.

Maximum age six is primary and eight is a sensitivity. Use the broad nursery
allocation p in [0.35,0.90] and the existing demographic, initial-abundance,
forcing and effect-size supports. Keep the two R0(1-p) strata separate and
balanced at source generation; neither is an empirical population-frequency
estimate. A common source is paired across restrictions. Active effect sizes
retain support down to zero: weak effects are not removed to make labels easier
to recover. Biological algebraic failures retain their identities and receive
no replacement draw.

PR032 previously used a later insurance-population proxy. Its primary value
here is the neutral value one, with a paired log-uniform [0.7,1.8] engineering
sensitivity. The same underlying uniform deviate is consumed in both regimes,
preserving all other nuisance values. The remainder of the inherited support
is explicitly an engineering specification, not a posterior fitted using the
late record. Later life-history knowledge remains part of the repaired kernel;
the 1989 boundary concerns the response record and intervention constraints.

## Fixed allocation and observations

For each age, draw 512 independent bank sources, 512 calibration sources and
512 test sources. Each bank source has four process replicates; each calibration
and test source has one. Pair each source across four restrictions and two
PR032 regimes. This gives **49,152 Pedder-history attempts**, with 3,072 distinct
nuisance-source identities. Each history executes at most 25 annual transitions.
Direct draws use fresh role-specific namespaces; no prior terminal archive or
fitted proposal supplies the sample.

The allocation uses 49,152 of the remaining 251,904 initial-search attempts,
leaving 202,752; the programme plan remains 1,035,520 below its 1.1-million
ceiling. Up to 1,000 further site histories are charged to the 8,000 qualification
reserve, whose previous conservative charge was 3,263. There is no conditional
extension to obtain more favourable outcomes or fill rare observation groups.

Generate twelve independent site counts at each visit. For positive total
accessible abundance, normalize the eight visit exposures to expected total
173 captures; each site receives one twelfth of its trip's expectation.
For the clustered profile, multiply each site-trip expectation by its own
independent Gamma(1,1) deviate. Aggregate to per-site trip means, retain exact
zeros, and perturb each nonzero mean by Uniform(-0.08,0.08), floored at zero.
All-zero exposure generates an all-zero record. The normalization and
digitisation law are explicit test assumptions.

Use four prespecified profiles, without a search over additional settings:

| Profile | Accessible ages | Score power | Count generator |
|---|---|---|---|
| Primary | Age 0 | 1/12 | Homogeneous Poisson |
| Age accessibility | Ages 0 and 1 | 1/12 | Homogeneous Poisson |
| Score concentration | Age 0 | 1/4 | Same observations as primary |
| Site-trip quality | Age 0 | 1/12 | Independent Gamma-Poisson site-trip quality |

For observation D and history H, use the existing saturated-relative eight-trip
composition score S, with relative catchability fixed at one. The score is a
tempered compatibility rule. It is not labelled an exact likelihood for the
digitised means.

## Recovery sets and their test population

The historical question concerns a record with observed fish before the
decline. Before generating any study histories, define the observable group
Z=1 when at least one of the first five generated trip means is positive.
Calibrate and test within Z=1 separately for every true restriction, age,
replacement-index stratum, profile and PR032 regime. Z=0 records are retained
and counted but return the full four-restriction set without an information
claim. This fixed feature-defined group avoids evaluating the historical
question primarily on surveys with no early observations. It does not select
latent terminal fate or require the observed five-point trajectory. No source
or process attempt is refilled when Z=1 is scarce.

The algebraically feasible source distribution is the declared data-generating
distribution. Feasibility must be identical across paired restrictions and
quality regimes. An unexpected process failure blocks qualification. Z may
differ across restrictions because it is an observed-data group, not an
algebraic filter. Every failed or Z=0 attempt remains in the accounting.

For each candidate restriction r, calculate bank support

    ell_r(D) = log mean_source mean_process exp(S(D,H_r)).

All planned bank-source and replicate slots remain in this average; failures
contribute zero. No terminal-class balancing or fitted importance weight is
used. Define two nonconformity scores:

    a_relative,r = max_{s != r}(ell_s - ell_r)
    a_absolute,r = -ell_r.

For a proposed true restriction, calibrate each score using independent
calibration records generated under that restriction and with Z=1. The finite
rank is p=(1 + number of calibration scores >= query score)/(n+1). Keep ties
and infinite scores; never discard an inconvenient infinite score. Retain r
when both p values exceed 0.025. An all-unsupported query returns all four
restrictions conservatively and also fails the support check.

The two rank tests allocate 0.05 exclusion error by a union bound. Their
coverage claim concerns new draws from this simulation distribution within
the prespecified groups; it is not empirical coverage for the historical case.
The class/group calibration construction follows the principles in
[Angelopoulos and Bates, sections 4.1–4.2](https://arxiv.org/html/2107.07511v6).

## Qualification and stopping rule

Bank halves split whole source identities reproducibly within each stratum.
Each half recomputes its own calibration scores on the same independent
calibration records. The observed record is not used to choose a split,
threshold, nuisance draw or profile.

For each age/index/profile/quality group, require:

1. At least 39 Z=1 calibration cases for every true restriction, permitting
   a rank as small as 0.025, and a nonempty independent Z=1 test sample.
2. At least 95% of each true restriction's test cases have some finite bank
   support in the full bank and both halves. Unsupported cases are retained
   with full sets when counting coverage and power.
3. A one-sided exact lower bound of at least 0.90 for retention of each true
   restriction, using alpha=0.05/4 across the four restrictions.
4. At least 90% identical full/half restriction sets in each true class, for
   all three bank comparisons, and at most 0.05 difference in class retention.

Compute exact binomial bounds by inverting the binomial tails, following
[Clopper and Pearson (1934)](https://doi.org/10.1093/biomet/26.4.404).
Calibration and test each use one realization per independent source; paired
restrictions are not counted as independent replicates. These bounds are
simultaneous within each stated analysis group, not over every reported table.

For all twelve directed pairs (true i, false j), measure the probability of
retaining i while excluding j. A pair is informative only if its one-sided
exact lower bound exceeds 0.5, using alpha=0.05/12 within the group. This tests
useful exclusion rather than forced top-one selection. The primary result must
pass the above checks in every age-six profile, index stratum and PR032 regime,
and retain at least one **same ordered pair** whose lower bound exceeds 0.5
in every one of those sixteen groups and all three bank variants. Take the
intersection of informative-pair sets; a favourable group alone cannot qualify.

Support, numerical or half-bank failure gives an unassessed computational
result. Insufficient coverage precision is distinct from coverage decisively
below tolerance. Stable, adequately covered sets without a robust informative
pair give a low-information result under this procedure. Neither warrants
another draw, a relaxed criterion or a claim of intrinsic non-identifiability.

## Historical step, only after a qualifying synthetic result

Only a qualifying age-six gate permits scoring the actual eight-visit record.
The primary retained set is the union across all profiles, both index strata,
both PR032 regimes and all three banks. A restriction is excluded only when
all these procedures exclude it and a retained comparator has a directed
synthetic exclusion against it in that same robust intersection. This is a conservative enlargement
of the calibrated sets. Empty raw sets are reported as lack of model adequacy,
not as a winning mechanism. Agreement over the lifespan sensitivity is
required for a lifespan-robust claim; age eight cannot rescue an age-six failure.

A positive trout-effect interpretation additionally requires the two
background contrasts R_T versus R_H and R_J versus R_C to qualify; climbing
requires R_C versus R_H and R_J versus R_T. Report partial or unresolved
contrasts explicitly. No normalized support is presented as model probability,
and no effect is an identified empirical causal fraction.

The same fixed procedure may display digitisation-envelope and leave-1989-out
diagnostics after qualification. They cannot reopen a STOP, qualify another
procedure or replace the primary result. Preserve the executed protocol,
complete attempted-source accounting, raw histories and independent checks.
