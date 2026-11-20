# Independent audit of the common-model interrogation

## Claim audited and verdict

The operational claim is that the frozen production archive supports two
descriptive conclusions without new simulation: compatible sources imply
materially different persistence and compartment-abundance histories, and
removing the trout overshoot raises mean 1980 lake abundance in the 12
compatible base/q=.02/shared-quality R_J profiles, with a much weaker signal by
1987--1988. This requires correct source selection, actual-year mapping, fixed
factual weights, survivor conditioning, invalid-history handling, paired Monte
Carlo errors, and honest separation of numerical precision from ecological and
causal inference.

**Verdict: conditionally supported.** I found no arithmetic, joining, weighting,
year-mapping, or support-selection error in the bounded independent checks. The
reported ecological contrasts follow from the frozen artifacts. They remain
conditional on the searched parameter sources, declared q and observation-law
scenarios, and simulator structure; they are not calibrated historical
abundance estimates, mechanism probabilities, or evidence that trout caused
the historical loss.

## Strongest evidence

- I reconstructed all 18 selection roles (17 distinct profiles) from the
  validated-profile archive, including the 12-decimal survival tie rule. Every
  role/source/profile assignment matched.
- An independent implementation of the 14-record likelihood reproduced all six
  conditional count rows for three deliberately contrasting profiles: a
  regular mixed-outcome source and both q=.20 survivor-tail cases. Means,
  weighted process quantiles, ratio Monte Carlo SEs, concentration diagnostics,
  and the endpoint refuge identity all matched. The 1998--2002 nondetection
  fields were correctly mapped to 1997--2001 states, with the separate 2002
  endpoint used for 2002.
- All 25 illustrative histories had positive factual support, the reported
  outcome, and the maximum factual log weight within that outcome. Their seeds,
  outcome mass, conditional ESS, and within-outcome weight matched the raw
  histories.
- I independently recomputed 20 paired early-lake rows from four stress-case
  profiles: the lowest qualified factual ESS, the largest 1980 contrast, a
  positive-support invalid-removal case, and an unqualified ESS=1 case. All five
  endpoints, fixed-weight contrasts, paired SEs, qualification labels, and
  invalid-support results matched. The invalid case had 25 positive-support
  histories and factual mass 0.03616; all five contrasts correctly remained
  undefined without renormalisation.
- The 738 conditional-envelope rows and 170 early-lake summary rows reproduced
  exactly from their row-level inputs. The headline base R_J result also
  reproduced: all 12 1980 contrasts were positive and 10/12 intervals lay
  wholly above zero; later endpoints had smaller, mixed-sign estimates.

The bounded raw recomputation read 19,456 factual rows from 19 sources and
4,096 paired counterfactual rows from four sources. It generated no histories.

## Strongest threats, ranked by scientific consequence

1. **Observation and population scale remain unidentified.** The count
   distributions are conditional on scenario q, observation law, simulator,
   and the permissive compatible slice. The latent count scale is not calibrated
   to historical abundance, and homogeneous or shared-quality detection does
   not represent every plausible spatial coverage process. A different
   empirically justified observation model could change which ecological
   histories receive support. This is the main limit on historical inference.
2. **Some survivor-conditioned summaries are poorly concentrated.** Of 1,527
   profiles, 42 fail the conditional precision criteria. Unqualified profiles
   determine 96 minima and 18 maxima in the 738-row unfiltered envelope; q=.20
   has no qualified survivor-conditioned profile. The two q=.20 survival point
   estimates are also noisy (MC SE about 5.0e-6 and 7.2e-5). The report now
   states these limits and does not present the extrema as population bounds.
3. **Illustrations are selected possibilities, not typical histories.** Eight
   of 25 outcome-conditioned examples fail the concentration criteria. Several
   minimum/middle/maximum roles are tied at survival one, so their labels do not
   describe a gradient. The revised report discloses both facts and avoids
   mechanism ranking.
4. **Temporal resolution is limited.** Survey proxies provide preceding-year
   states, and the counterfactual archive supplies four lake endpoints plus a
   whole-period minimum rather than an annual early trajectory. The endpoint
   refuge identity is valid only in 2002. The implementation respects these
   boundaries, but stronger timing claims would require additional archived
   states or a separately authorised replay.

No fatal flaw was found. Threats 1 and 2 are major limits on scope and
precision; threats 3 and 4 are material interpretation limits rather than
calculation failures.

## Corrections and remaining requirements

During review, the results draft described the high-q survival estimates as an
"original qualified result." Qualification applies to the joint-weight profile,
not automatically to every endpoint. The text was corrected to report the
survival MC SEs and the substantial relative uncertainty of the second estimate.
The draft also retains the tied-role, unqualified-example, and envelope-extrema
caveats. I found no further correction required for the present descriptive
claims.

Before treating these outputs as historical population bounds or causal
evidence, the study would need empirical constraints on population scale and
survey coverage, a defensible treatment of spatially heterogeneous detection,
and precision-qualified survivor tails for any claimed extreme. Mechanism or
intervention ranking would require a separate decision-focused analysis. The
remaining uncertainty is therefore ecological and inferential rather than a
detected arithmetic defect: the audit verifies what the frozen model archive
says, not that the model's compatible histories occurred in Lake Pedder.
