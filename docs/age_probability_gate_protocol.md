# Third and final bounded terminal-probability gate

3 October 2026. Barry accepted option A in Fable's message 841: one further
bounded attempt using broader nursery allocation, histories directed at the
record, and probability calibration. If the endpoint remains unassessable,
stop. This is a prospective amendment after two preserved STOP results, not a
continuation of either draw. No publication or rescue-effect calculation is
authorized by this amendment.

## Biological scope and evidence

Promote the existing `legacy_range_sensitivity` nursery allocation,
`p ~ Uniform(0.35,0.90)`, where p is the fraction of recruits allocated to the
lake. This is an engineering distribution, not a measured recruitment fraction.
Use all four restrictions with the primary recovery-plan removal account:
maximum age six is primary and eight is a sensitivity, giving eight cells.
Retain the two refuge-replacement-index strata separately. All other support,
forcing, process equations, sex/age accounting and the union calendar remain
unchanged. This does not introduce a new creek-breeding mechanism: the broader
range already existed in the second gate.

The recovery plan reports maturity at about two years, usual breeding at three
to four, and a lifespan up to six years (`literature/pedder/
tasmanian_galaxiidae_recovery_plan_2006_2010.md`, section 1.1.4). Continued creek
records are consistent with recruitment after the lake decline. They do not
establish continuous absence of lake recruitment or identify two generations
of creek-born fish. Hamr reports breeding-condition adults collected in October
1991 and successful artificial fertilisation. No wild mating-pair observation
was located in the retained primary corpus; his explicit pairing discussion
concerns captive fish and says pairing was not known (`literature/pedder/
hamr_1992_pedderensis_report.md`, captive breeding section).

Lake nondetections remain observations at sampled occasions. Do not require an
empty lake in 2002 or use a terminal outcome to construct the proposal. Retain
the earlier absolute-detection sensitivities as qualifications of the evidence;
their unestimated detection rates do not become hard biological constraints.

## Evidence partition and target

Let F be feasibility of the complete documented intervention chronology through
2012, including the actual dated capture, holding, release and donor-transfer
constraints. The target in each cell/index stratum is

    pi_E(theta,H) proportional to g(theta) p(H|theta) I(F) exp(S_E(H)).

The engineering distribution g is the existing broad-nursery distribution.
S_E contains the previously specified eight-visit Lake score at its base
settings, plus the early creek allocation of counts (68,1), conditional on
their total 69. For X_E = 43 times mean accessible early creek abundance and
X_F = 2 times accessible abundance immediately before the February 1992 catch,
use the saturated-relative score

    S_C = 68 log[(X_E/(X_E+X_F))/(68/69)]
          + log[(X_F/(X_E+X_F))/(1/69)].

Both saturated-relative scores have maximum zero. Lake accessibility is age 0;
creek accessibility is age 1+. January's four captured fish enter through
the existing removal ledger. Every history must also contain at least one fish
in the March 1996 pre-event refuge pool, whether or not that fish was retained.
The retained-fish ledger already enforces this, while the non-retained branch
requires the explicit presence check. This is a logical support indicator,
without another detection-rate likelihood. Conditioning on the complete F is not a wholly pre-1996 information
set. Record the exclusion fraction after end-2002 among histories with a valid
2002 state and compare their E-weighted endpoint with the full-F target. This
is a selection diagnostic, not an alternative qualifying target.

Remaining evidence R consists of the 1998–2002 creek count and the nine
insurance-population binary records (indices 2–10 of `BINARY_RECORDS`). Generate
only R in the prospective test: do not regenerate or score the real Lake or
early creek block a second time. The post-1996 creek count is withheld from
proposal construction and conditional weights.

For the late creek window X_L = K rho times accessible mean abundance, use
the conditional predictive negative binomial

    N_L | E,H ~ NB(size=69, probability=(X_E+X_F)/(X_E+X_F+X_L)).

This follows from a common Poisson capture rate with the reference measure
p(lambda) proportional to 1/lambda, giving lambda|E,H ~ Gamma(69,X_E+X_F).
It is a declared observation assumption, not an estimate of field catchability.
At N_L=0, the product of early allocation and this predictive mass reproduces
the earlier (68,1,0) conditional allocation score up to a data-only constant.
Verify that identity mechanically.

Keep the 36 original base K × rho × q profiles. For insurance records use two
matched probability laws: `poisson`, and `gamma_binary_quality` with independent
Gamma(1,1) quality between visits and shared quality within each adult/juvenile
visit. Integrate shared quality exactly for the paired binary outcomes. The
creek predictive law is the same in both cases. This second law is not the
earlier generator with gamma quality in creek counts. No profile is selected
for a favourable terminal result.

## Joint proposal and fresh draw

Train on the two completed archives only. Restrict training to the broad
nursery cells. Collapse paired restrictions and process replicates within each
nuisance-source identity using the arithmetic mean of exp(S_E); failures
contribute zero. Include the archive-specific g/q correction for the second
archive. Neither terminal states nor R enter training. Fit separately within
maximum-age/index-stratum groups.

Use all positive-weight source centres in the existing 16 unit coordinates.
For centre c, a beta kernel has independent coordinates conditional on that
common centre: alpha_j=1+kappa*c_j and beta_j=1+kappa*(1-c_j). The full joint
proposal is

    q/g = 0.5 + 0.25 KDE_kappa=8 + 0.25 KDE_kappa=32.

This mixture retains source-level parameter interactions; it is not a product
of separately fitted marginals. Bandwidths and mixture weights are fixed before
the fresh draw. Record the exact joint density and use w_E=exp(S_E)/(q/g), so
0 <= w_E <= 2. No training history is a fresh test history. Failure, very small
weights or absent outcomes never trigger replacement or an additional draw.

Generate eight cells × (512 truth + 512 bank sources) × six process replicates
× three sites = **147,456 nominal site-history attempts**. Pair nuisance sources
across the four restrictions, with separate truth/bank namespaces. Keep source
indices balanced over replacement-index, ledger timing and March retention.
The fresh independent unit is the nuisance source, not a process replicate or
paired cell. Verify all parameter/process namespaces against both old archives
and qualification draws before production.

## Probability forecast and calibration

Primary Y is loss of every natural-range fish at end-2002. Preserve the
breeding-pair, same-compartment-pair and age-1+10 diagnostics separately; they
cannot qualify an unassessed primary endpoint. For each synthetic r predict

    p(r) = sum[w_E L_R(r|H) Y] / sum[w_E L_R(r|H)].

The E-only comparator p0 uses the same bank with L_R=1. Use natural prevalence:
never normalize loss and persistence separately or assign equal class priors.
Average the six planned process replicates within each source; all failed
sources remain in the sampling universe with zero contribution.

Use 2,000 deterministic source-cluster bootstrap draws of both truth and bank,
stratified by the declared ledger-timing/March-retention design. Resample whole
source IDs with their process replicates. Reuse the resampling indices for
paired restrictions and observation-profile comparisons. Record source ESS and
largest source shares, without a minimum number of sources in each terminal
class. A zero-width bootstrap at a boundary is not evidence for probability
zero or one: supplement boundary intervals with bounded-weight
empirical-Bernstein numerator/denominator ratio bounds using w_E L_R <= 2.
Do not use a Kish-ESS Wilson interval as a qualifying confidence bound.

The bootstrap namespace is `probability-bootstrap-20261003`, keyed by maximum
age, index stratum and role; the half-bank namespace is
`probability-halves-20261003`, keyed by maximum age and index stratum. Blocks
are the fixed `ledger_timing:march_retention` combinations. The observation
namespace is `age-probability-observations-20261003`, keyed by source, process
replicate, K, rho, q and observation law. These keys pair the observation
namespaces across restrictions while separating truth from inference. They
do not promise exact common random numbers for every insurance draw: the
negative-binomial sampler can consume different numbers of variates when
exposures differ. Bootstrap source indices remain exactly paired.

Require at least 95% of target truth weight to have finite supported forecasts,
at least 95% finite bootstrap draws, a 95% forecast interval of total width at
most 0.20, and an absolute difference at most 0.05 between prespecified bank
halves. These forecast-precision checks apply to synthetic R first. Marginal
calibration is the target-weighted mean Y-p: its conservative 95% interval must
lie wholly within [-0.05,0.05]. Use the four fixed forecast groups [0,.25),
[.25,.5), [.5,.75), [.75,1]. Group membership uses the point forecast and stays
fixed during bootstrap; truth outcomes never choose cutpoints. Every occupied
group in a resolved multi-group forecast must have its residual interval
wholly within [-0.10,0.10]. A single forecast group permits only a
marginal-calibration statement. Unsupported predictions contribute their full
possible residual range rather than disappearing from the assessed target.

The boundary concentration bound pools the independent source-cluster means
within an age/index stratum. Theorem 11 of
[Maurer and Pontil (2009)](https://www.cs.mcgill.ca/~colt2009/papers/012.pdf)
allows independent, non-identically distributed variables, so the fixed
ledger/March blocks do not require separate bounds. For each source mean in
[0,b], with b=2, use radius
sqrt(2 sample_variance log(8/alpha)/n) + 7 b log(8/alpha)/(3(n-1)); the four
one-sided numerator/denominator events share alpha equally. Divide the
resulting numerator and denominator bounds, truncating only the confidence
set to [0,1]; a denominator interval reaching zero gives upper limit one.
All 256 planned sources, including zero-contribution failures, enter this
bound. A zero-numerator, unit-denominator fixture gives an upper limit about
0.102 at alpha=.05, but low absolute E support makes the bound much wider.
For boundary calibration residuals, also bound the truth event and forecast
means with a three-way alpha split and take the hull with the two-stage
bootstrap interval. Do not substitute a narrow bootstrap-only interval.

Compare log-score and Brier-score improvements over p0 on identical truth
cases. Do not clip probabilities to avoid contradictions. A positive-weight
outcome assigned probability zero is a support failure. If computational and
calibration checks pass, distinguish `CALIBRATED_AND_INFORMATIVE` (both paired
gain intervals have positive lower limits) from
`CALIBRATED_BUT_NO_INCREMENTAL_INFORMATION`. The latter may be a faithful
probability forecast for a stochastic process; it does not identify terminal
fate. Neither calibration nor a conditional engineering probability establishes
the biological model's empirical adequacy.

The probability tolerances are prospective working criteria. They are not
literature-derived biological constants. Proper-score rationale follows
[Gneiting and Raftery (2007)](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf);
the need to distinguish computational calibration from using data effectively
is also discussed by [Modrak et al.](https://arxiv.org/abs/2211.02383).

## Decision, budget and stopping point

Report every cell/index/profile/law result. An age-eight sensitivity cannot
alone authorize the historical comparison. Only a qualified primary procedure
may next consume R_actual, once, with the same precision and split-bank checks
at that particular dataset. Restriction/index mixtures have no empirical prior
weights; report qualified columns separately. A calibrated but uninformative
column supports a conditional simulation probability with uncertainty and no
claim of fate discrimination. Unassessable or miscalibrated columns retain
STOP. If none qualify, this is the final bounded attempt: do not start another
proposal, soften the tolerances or add process replicates.

Reallocate 147,456 from the remaining 399,360 initial-search attempts, leaving
251,904; the programme's planned 1,035,520 remains below 1.1 million. Use at
most 1,000 additional qualification attempts within the existing 8,000 reserve
(2,263 conservatively charged beforehand). Run meaningful compute on
utas-ubuntu with at most 16 workers and one numerical-library thread each.
Preserve prior protocols, receipts and raw outputs. Verify local tests, Linux
serial/parallel replay, transfer hashes, frozen source bindings and independent
method/result audit. The final deliverable is the verified gate disposition
and, only where qualified, a clearly conditional remaining-evidence result.
