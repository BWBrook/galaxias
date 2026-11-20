# Lake-history conditioning: prospective repair after the first recovery gate

2 October 2026. Barry relayed Fable's message 816 and asked Astra to advance the
repair. This amendment addresses the sampling target exposed by the completed
1 October gate. It preserves that gate, its STOP disposition and all its raw
outputs. The amendment is prospective for the new sources and simulations;
the earlier bank has already been inspected and is proposal-training data.

## Diagnosis and question

The earlier synthetic coherence event A required simulated observations to
support the documented rescue collections. It did not condition simulated
worlds on the real early Lake record. Its generated late Lake counts were
allowed to be positive. Large lake populations among coherent worlds therefore
expose a mismatch between the tested world distribution and the historical
question, not a demonstrated omission or numerical failure in the Lake scorer.

The repaired question is whether natural-range terminal occupancy can be
discriminated among intervention-feasible worlds weighted by the documented
early Lake trajectory. The process kernel, forcing, parameter bounds, removal
accounts, site links and union calendar remain as qualified. The age/nursery/
restriction cells and refuge-index strata retain their separate meanings.

The analysis may refocus on pre-1996 evidence before the gate. It may not infer
the real terminal fate or dispatch the full historical comparison unless the
repaired gate qualifies. No terminal state, class, functional endpoint or
preferred result enters proposal fitting, source replacement or budget changes.

## Evidence used once

The primary historical conditioning block is Lake's eight retained December
visits: 1976–80 and 1983/86/89. The five positive digitised means and three zeros
form one conditional allocation score. This replaces the previous two-bin
early/late Lake score; it does not add a second score for the same fish.

For accessible abundance x at each trip, multiply the last three exposures by
the declared late/early accessibility ratio rho. Let c be twelve times each
digitised mean, C their sum, and p_i=x_i/sum(x). Use the saturated-relative score

    S_E = tau sum_{c_i>0} c_i log[p_i/(c_i/C)].

The maximum is zero; positive recorded catch with zero modeled exposure gives
minus infinity. This remains a tempered compatibility score for derived capture
equivalents, not a likelihood for recovered integer catches. The data-only
saturated constant does not affect normalized weights. Using eight categories
now makes the observed boom shape part of conditioning. The change from a
shape diagnostic is explicit and follows the requested early-history repair.

The base is tau=1/12, rho=1, age-0 accessibility, and central readings. Retain
one-factor cases tau=1/4 and 1; rho=0.25 and 4; age-0-plus-age-1 accessibility;
and positive means shifted by -0.08 or +0.08. Verified zeros stay zero.
No profile is chosen because it produces loss or passes recovery. Absolute
Lake abundance is not identified by a conditional allocation score.

The 1988–89 lake electrofishing and Hamr's 1990–91 lake-edge larval searches
are separate source evidence, but their effort and accessibility are not
quantified sufficiently to calibrate absolute detection. They are sensitivity
blocks, not additional primary pass/fail conditions. Represent each as one
campaign-level nondetection, not as invented independent visits. Use effective
q values 0.01, 0.1 and 1 with both a Poisson zero model and a shared-quality
gamma(shape=rate=1) campaign model. These q values are assumptions, not estimates.
For joint campaign sensitivities, cross both q grids; campaign quality is
shared within a campaign and independent between the two different methods.
The electrofishing proxy brackets Lake age-1+ abundance at the start versus end
of 1988 and 1989; the campaign exposure is their two-year average. The larval
proxy is mean post-newborn-survival Lake age-0 abundance in 1990 and 1991.
Annual states cannot reproduce each November–January search date; report that
limitation. Evaluate campaigns singly and jointly to expose their contribution.
Their weight is applied once in each named sensitivity target. They do not
alter primary proposal training or authorize a primary GO.

Lake's gear was four three-minute pond-net sweeps at each of twelve sites;
the 1988–89 electrofishing is a separate method. Hamr reports intensive
spawning-season searches in November 1990–January 1991 and November 1991 with
no larvae in creeks or nearby lake edges. The local corpus has no later primary
lake-specific effort series. Later annual-survey summaries do not establish
latent lake absence in every year through 2002. Nondetection must not be
replaced by a hard N_lake=0 constraint or by selecting on the 2002 lake state.

The exact capture, holding, release and donor-transfer chronology remains a
process-feasibility condition A_proc. It includes documented insurance
transfers after 1996, as in the original linked design. Thus the conditioning
is on early Lake evidence plus the complete intervention schedule, not on an
entirely pre-1996 information set. No additional abundance likelihood is added
for those same rescue fish. Cumulative 1990–91 captures are not a lower bound
on abundance at a single date: survival and recruitment occur between events.
Each capture provides an event-time eligible sex/age-pool lower bound.

## Target, proposal and independent sources

Within each cell and refuge-index stratum the target is proportional to

    g(theta) p(history | theta) I(A_proc) exp(S_E(history)),

where g is the original engineering distribution, not an empirical prior.
Use the original frozen bank only to learn a proposal. An exploratory archive
diagnostic remains explicitly separate from the prospective test.

Fit within each of four maximum-age/nursery source groups and two refuge-index
strata. A nuisance source's utility is the arithmetic mean of exp(S_E) across
its predeclared cells and process replicates, with infeasible attempts assigned
zero. Compute this with log-mean-exp, not by exponentiating a mean log score.
Pairing across restrictions/removal accounts does not create independent sources.

Use independent unit-interval coordinates for s0, s1, adult survival, age-2
breeding probability, nursery allocation p, conditional log R0, log refuge
fraction, recruitment sigma, four log abundance scales, log Strathgordon
pre-2007 spawning multiplier, and PR027/28/33. Preserve g's conditional p/R0
bounds within each refuge stratum. Other parameters retain their original
distributions. For each coordinate fit four equal-width bin probabilities,
shrunk 20% toward uniform. With no training weight, use the uniform distribution.

Draw the complete vector from a 50:50 mixture of uniform g coordinates and the
product of the fitted histogram marginals. If h_j are their normalized densities,

    q(theta)/g(theta) = 0.5 + 0.5 product_j h_j(u_j).

This is a whole-vector mixture, not separate coordinate-wise mixture choices.
Record the exact mixture density; g/q is at most two. Recompute derived
demography and feasibility after transformation. Retain every invalid or failed
source without replacement. The proposal retains support but may be inefficient
if compatibility depends on parameter interactions; that risk is measured by
fresh source weights and cannot be solved by outcome-driven resampling.

Freeze the proposal before generating independent truth and bank namespaces.
Keep discrete refuge strata, ledger timing and March retention balanced by
source index. Preserve cross-restriction and removal-account pairing. Each
history's final weight is W=(g/q) exp(S_E), exactly once. Training on old S_E
does not substitute for this weight and does not justify weighting by g/q alone.
Other sensitivity targets use their own S_E and campaign score with the same
proposal-density correction.

## Prospective endpoints and predictions

Keep Y0, any natural-range fish at end-2002, as the primary endpoint. Add:

- Ypair: at least one realized female breeder and one realized male breeder
  in the model's 2002 prespawning pool. Also report a pair within the same
  modeled compartment, since the kernel pools sexes across compartments.
- Y10: end-2002 natural-range age-1+ abundance at least ten.

These endpoints are not a nested ordering: Ypair uses an earlier within-year
time, and ten fish need not contain both sexes. A pair is a breeding opportunity
under the model, not a guarantee of long-term viability. A pass for a secondary
endpoint cannot rescue an unqualified primary endpoint.

The frozen runner's annual summary retains pooled sexes but omits compartment
counts. Recover the compartment counts from the retained Pedder checkpoint at
the 2002 spawning time (the no-op `transfer_2002_late` calendar entry), using
the original source demography, process seed and keyed breeding draws. Require
the reconstructed sex totals to match the saved pooled counts exactly. This
recovers omitted metadata without advancing the history or changing the kernel.

Before new simulations, record the directional expectation that early-history
conditioning reduces lake-supported persistence and increases loss and small
persisting populations relative to the original complete-history distribution.
Record Fable's stronger prediction, majority loss with only a handful of
survivors in persisting worlds, as a hypothesis under the declared conditional
engineering distribution. Neither prediction is an acceptance criterion.
Refutation, weak shifts or sensitivity to detection assumptions must be retained.
An engineering-distribution frequency is not the probability of historical loss.

## Recovery assessment and decision

Generate new synthetic observations under the three original generators and
retain their intervention-coherence flags without replacement. They represent
independent replicate observations conditional on the early-history target;
they are not the original Lake data observed a second time. The historical
score map marks the early Lake block as already consumed. Any later historical
comparison must use remaining evidence once, or return to the original g and
evaluate the full joint score once.

Use final W in class-normalized bank evidence and truth sensitivities. Average
over the fixed number of planned process replicates per source, including
zero weights for failed or incoherent attempts as appropriate. Keep equal
terminal-class reference weights for discrimination. Do not infer endpoint
prevalence from that artificial class balance. Report unstratified weighted
composition separately, including the failed-attempt accounting.

Retain minimum support of sixteen distinct coherent truth sources and eight
bank sources per terminal class, within every cell/refuge-index stratum/profile.
Add truth source-weight ESS at least sixteen per class, so many negligible
weights cannot masquerade as adequate support. Require bank source-weight ESS
at least four before classification and after multiplication by each dataset's
likelihood. Bootstrap nuisance-source IDs, carrying paired ablations and all
their process replicates together, for 1,000 bootstrap draws.

The primary accuracy criteria remain balanced accuracy at least 0.75, both
sensitivities at least 0.70 and lower 95% source-bootstrap bound above 0.5.
Abstentions count as errors. Compare Creek-only, Creek-plus-Lake and full scores
on identical observations and bank histories; report paired improvements.
The complete original 540-profile panel remains the declared observation panel.
At each profile use its declared Lake power/accessibility/reading settings in
historical weights as well as synthetic observation scoring. Assess secondary
endpoints separately where source support permits.

Support is checked before expensive classification. Insufficient support is
unassessed; concentrated bank weights are a representation failure; poor
classification with adequate support is a discrimination failure. No new draw,
class balancing, change in q or softened constraint fills a failed cell. If no
primary stratum qualifies, retain STOP before the historical comparison.
Only a passing base-panel Poisson or gamma-quality Y0 column can qualify;
fixed-total controls, non-base profiles and secondary endpoints cannot by
themselves authorize a historical comparison.

## Budget and execution freeze

Use 20 cells x (512 truth + 256 bank sources) x 2 joint process replicates x
3 sites = 92,160 nominal site-history attempts. This is a fixed repair tranche
reassigned from the original 491,520 initial historical-search allocation,
leaving 399,360 there. The overall planned allocation remains 1,035,520 within
the 1.1-million ceiling. It is a recorded route amendment, not reuse of an
unspent allowance to extend the failed first gate. No outcome triggers more
draws. Qualification uses at most 1,000 additional attempts within the existing
8,000 reserve; its earlier conservative charge was 1,543.

Run meaningful simulation on utas-ubuntu with at most sixteen worker processes
and one numerical-library thread each. Bind the protocol, proposal, source,
parameter, lockfile and calendar provenance before dispatch. Verify a small
local smoke, exact Linux serial/parallel replay, source/seed separation,
importance-density checks and mechanical scoring controls. Preserve both raw
histories and compact features. Record all attempts, early failures, runtime,
hashes, and source counts; retain existing receipts byte-for-byte.

The stopping point is a verified repair with a prospective gate disposition,
including STOP if support or discrimination fails. There is no authorization
here for publication, commits/pushes, biological changes, post hoc thresholds
or another adaptive proposal.
