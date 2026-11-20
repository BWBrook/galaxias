# Independent pre-freeze methods audit: early-Lake restriction recovery

4 October 2026. Read-only scientific review of the frozen-design candidate,
the repaired age/sex kernel adapter, the numerical recovery helpers, focused
tests, and the directly cited conformal-method reference. No simulation archive
or historical mechanism score was inspected or generated in this audit.

## Decision

**CONDITIONAL GO TO IMPLEMENTATION QUALIFICATION; HOLD PRODUCTION.** The bounded
question and the early-positive calibration partition are defensible for a
synthetic restriction-recovery study. The procedure cannot estimate the
probability that trout, climbing galaxias, habitat change, or their combination
caused the historical decline. Its inferential object is the ability of a fixed
set-valued rule to retain and sometimes exclude four restriction labels for new
records from a declared engineering data-generating distribution.

The originally ambiguous power gate must be frozen as follows: one *same
ordered restriction pair* must have a one-sided Clopper--Pearson lower bound
greater than 0.5 in every one of the 16 age-six profile x replacement-index x
PR032 groups and for the full bank and both bank halves. Any historical
comparator-to-excluded pair must belong to this intersection. A pair qualifying
in only one favourable group, or a different pair qualifying in each group,
does not pass.

Production remains conditional on inspection of the completed driver and
analyser, their focused tests, the Pedder-prefix qualification, and a tiny
end-to-end synthetic run. Historical scoring remains prohibited unless the
fully frozen age-six gate passes.

## Scientific target and scope of inference

The response is the eight-visit Lake Pedder composition from December 1976--80,
1983, 1986 and 1989. The candidate labels are nested process restrictions:
R_H has habitat/productivity forcing without trout or climbing effects, R_T
adds trout, R_C adds climbing galaxias, and R_J adds both. R_H is not a
no-change counterfactual, and the four labels do not identify interaction
effects or empirical causal fractions.

The bank functional is

    ell_r(D) = log mean_source mean_process exp(S(D, H_r)).

It averages the tempered saturated-relative composition score under the
declared nuisance-source distribution. It is neither a likelihood integrated
against an empirical prior nor a posterior model probability. The synthetic
prediction target is a set of restrictions for a fresh feasible source and
one observation realization in a prespecified true-restriction, age,
replacement-index, observation-profile and PR032 group. Historical use is an
engineering stress test of this rule outside any claim that the simulation
distribution represents real-world mechanism frequencies.

The 1989 endpoint correctly excludes rescue removals, captive groups,
insurance populations, transfers and all post-1989 outcome constraints. Later
life-history evidence remains embedded in the repaired kernel and parameter
support, so the exercise is prospective only with respect to the synthetic
recovery test, not temporally blind model development.

## Data-generating and observation processes

The source generator uses fresh role-specific namespaces; pairs the same
nuisance source, process stream and PR032 unit across restrictions and the two
quality regimes; balances the two R0(1-p) strata by design; and retains effect
support arbitrarily close to zero. Neutral PR032 is one and the stress regime
is log-uniform on [0.7, 1.8]. Algebraic feasibility is independent of
restriction and PR032. Infeasible identities are retained without redraw.

The Pedder-only runner starts at the rounded neutral December-1964 state,
advances exactly 25 annual transitions through December 1989, uses the existing
one-year invader lag, and inserts no event or survey checkpoint. A focused
fixture reproduced the corresponding Pedder prefix of the linked runner exactly
for all 25 annual states.

For positive accessible exposure, the observation generator normalizes the
eight trips to approximately 173 expected captures, generates 12 site counts
per trip, and applies the declared nonzero-mean digitisation perturbation. The
Gamma--Poisson profile gives each site-trip an independent Gamma(1,1) factor.
All-zero exposure produces an all-zero record. The primary and score-power
profiles must share the exact generated observation; only the scoring power
may differ.

This matched generator deliberately tests recovery of relative temporal shape,
not abundance scale or detection. It can therefore establish computational
discrimination under its own observation law, but not empirical calibration of
the Lake surveys. The Gamma--Poisson profile is a useful heterogeneity stress,
although it does not span unknown temporal dependence, effort error, or
nonstationary catchability.

## Early-positive partition

Defining Z=1 by at least one positive generated mean in the first five trips is
a valid fixed observed-feature partition. Within each true restriction x index
stratum x profile x PR032 group, independent calibration and test sources are
i.i.d. draws from the same feasible engineering distribution conditional on
Z=1. Class-conditional calibration then tests each proposed label with scores
calibrated under that label. Z=0 queries receive the full set and make no
information claim. Consequently, the two component tests at 0.025 each control
false exclusion of the true restriction by a union bound of 0.05 within the
declared group.

This follows the joint application of group-balanced and class-conditional
conformal calibration described by Angelopoulos and Bates, sections 4.1--4.2
(https://arxiv.org/html/2107.07511v6). The theorem requires exchangeability and
provides marginal coverage over calibration and test draws. It does not give
empirical coverage for the historical record, conditional coverage for the
exact five-positive trajectory, or a guarantee conditional on every realised
calibration sample. The independent test set and exact binomial interval
estimate the coverage of the realised calibrated procedure under the same
simulation law.

The partition is preferable to global label recovery here because global power
would be dominated by generated records with no observed early phase, whereas
the actual record has five early positives. It remains broad: one early
positive suffices, so a passing result is not evidence of local recovery around
the observed five-point trajectory.

## Numerical and inferential verification

- The vectorised compatibility score was checked against the pre-existing
  scalar score, including impossible positive observations.
- The bank functional now uses a stable log-mean-exp reduction. Failed slots
  contribute zero, selected half-banks use the selected-source denominator,
  an empty mask returns minus infinity, and finite log support near -10,000 is
  preserved rather than underflowing to apparent non-support.
- Relative and absolute nonconformity retain positive and negative infinities.
  Equal-infinity subtraction is converted to a neutral tie only where the raw
  subtraction is undefined; NaN is rejected. An all-minus-infinity query is
  flagged unsupported and forced to the full four-label set.
- Finite conformal ranks use `(1 + count(calibration >= query))/(n + 1)`, retain
  ties and infinities, and exclude only at p <= 0.025. With 39 calibration
  cases, the smallest attainable p-value is exactly 0.025.
- The exact binomial bounds were independently compared with R `qbeta` for
  alpha values 0.05, 0.0125 and 0.05/12, n from 1 to 512, boundary counts and
  central counts. Maximum absolute discrepancy was 1.22e-15 for lower bounds
  and 1.11e-15 for upper bounds.
- The focused helper and prefix suite passed: `16 passed`.

The one-sided intervals are simultaneous only over the four true-class
coverage quantities or twelve directed pairs *within one stated analysis
group*. Intersecting pass decisions across 16 groups and three banks is a
conservative operational robustness rule; it is not a 95% simultaneous
confidence statement over all 48 tables unless a broader multiplicity
correction is added. No such broader claim should be made.

## Required implementation invariants

1. Split half-banks by a reproducible hash or permutation of whole source IDs
   after selecting an index stratum. Raw source-index parity defines the index
   stratum and cannot be used for the half split.
2. Store neutral and engineering rows under a composite identity containing at
   least `(source_id, quality_regime)`. The source ID is intentionally shared
   across PR032 regimes; keying a map by source ID alone would overwrite one.
3. Reuse the identical primary observation and observation seed for the
   score-power profile. A profile label must not silently alter that draw.
4. Calibrate and test only on feasible, valid Z=1 sources. Retain algebraic
   failures and Z=0 attempts in accounting; Z=0 produces a full set. Any
   unexpected runtime/process failure blocks qualification rather than entering
   the conformal sample or triggering a replacement.
5. Preserve the initial rounded state, all attempted identities, failure
   reasons, source/role/process/observation namespaces and per-restriction
   validity. Pairing and feasibility equality must be asserted across
   restrictions and PR032 regimes.
6. Compute source averages before any summary across paired restrictions.
   Calibration and test contribute one realization per independent nuisance
   source; process replicates and paired restrictions are never binomial trials.
7. Require every true class in every one of the 16 age-six groups to pass the
   calibration-count, full/half finite-support, exact coverage, set-agreement
   and retention-gap gates. Require the same robust directed pair over all 16
   groups and all three banks.
8. Do not load or score the real Lake vector, digitisation envelope or
   leave-1989-out sensitivity until the synthetic gate is frozen and passes.
   Age eight can qualify robustness after an age-six pass but cannot rescue an
   age-six failure.

## Residual risks and recommendation

The central scientific limit is structural: the four restrictions trade off
against broad demographic, settlement, refuge-quality, habitat, invader and
effect-size coordinates, including near-null effects. The fixed total removes
abundance-scale information. The record has only eight annual points, three of
which are nondetections with no independently estimated detection probability.
Accordingly, stable coverage may coexist with large sets and no robust directed
pair. That outcome is a valid low-information STOP, not evidence that the
mechanisms are intrinsically non-identifiable under every defensible model.

Proceed only to the bounded tiny synthetic qualification after the completed
driver and analyser satisfy the invariants above. If that passes, freeze hashes
and receipts before the 49,152-history production run. If any support,
coverage, half-bank or robust-pair condition fails, stop without refill or
historical scoring. A further general scientific reviewer is unlikely to change
the design decision once the implementation audit is complete; an independent
review of the final analyser and gate receipt would materially increase
confidence because a grouping, pairing or multiplicity error there could
directly reverse GO versus STOP.

## Final qualification decision

**GO TO THE FIXED 49,152-HISTORY PRODUCTION RUN.** The bounded qualification
replay passed the implementation, accounting, portability and parallelism gates.
This authorizes production only from the frozen source snapshot and fixed gate
configuration. It does not authorize historical scoring; that remains conditional
on the prespecified synthetic age-six recovery gate.

The Mac serial, Linux serial and Linux four-worker runs each contain all 192
planned history attempts: 144 valid histories, 48 retained algebraic failures
and no runtime/process failures. Every valid feature row records 25 annual
advances and every algebraic failure records zero. The analyzer independently
accepted the complete source allocation, Cartesian history slots, paired seeds,
feasibility/status mapping, bindings and archive hashes for all three runs.

Linux serial and parallel logical and physical archive hashes are identical.
Mac and Linux Lake features and discrete annual states are exactly equal. Across
307,116 numerical comparisons, the largest remaining platform difference was
1.280568540096283e-9, within the frozen relative tolerance 1e-12 and absolute
tolerance 1e-8. Both platforms passed 36 focused tests and compilation checks.
The replay was rerun independently without simulation and returned `PASS`.

The source manifest binds 56 files and the replay binds all three input
manifests. Independent inspection also verified every manifest member inside
`source_snapshot.tar.gz`; its SHA-256 is
`31c5c9121105924e698d4ab3716ff4f82b290e2dbc2863f6c0d6944d66c8b2b3`.
The qualification used 576 actual site-history attempts, conservatively charged
1,000, bringing the qualification-reserve charge to 4,263 of 8,000.

The smoke analyses correctly report `QUALIFICATION_ONLY_NO_HISTORICAL_PERMISSION`.
Their insufficient conditional sample sizes are expected under the tiny smoke
allocation and are not evidence about mechanism recovery. Production must stop
without refill if its support, coverage, stability or same-directed-pair gate
fails. Independent review of the final production analyzer and receipt remains
material; another general design review is unlikely to change the predispatch
decision.
