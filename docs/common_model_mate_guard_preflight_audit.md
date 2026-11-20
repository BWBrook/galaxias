# Independent preflight audit: singleton breeding guard

20 September 2026

## Verdict

**GO for the approved finite production run.** The final implementation is
faithful to the approved fixed-witness sensitivity and I found no remaining
scientific or analytical code defect that requires redesign. All prespecified
target-runtime evidence has passed on the final bound source bytes:

1. the independent audit in this document;
2. exact serial/parallel identity for a final 24-source by 2-replicate run,
   covering every configuration/restriction cell;
3. an end-to-end analysis smoke using that final qualification archive;
4. exact replay of 48 archived original-kernel histories, with zero forcing or
   archived-field mismatches; and
5. the reserved execution-budget receipt, including every diagnostic and
   failed or superseded execution.

The finalized audit is the last evidence file to be hashed into the production
gate. The runner refuses production without all five evidence files, the exact
frozen runtime, eight workers, the 517-source freeze and the 529,408-history
allowance. Dispatch remains authorised only while every receipt refers to the
final source bytes, has passing status and matches its recorded hash.

## Scientific target and scope of inference

The estimand is a **fixed-source structural sensitivity**: for the 517 sources
selected as witnesses under the original common-model kernel, how do paired
historical outcomes and rescored within-source compatibility change when annual
recruitment is set to zero for pre-breeding `A_L + A_R < 2`? It is not a new
search, parameter refit, posterior comparison, empirical extinction estimate,
or global test of persistence. Source selection used the original model and
therefore conditions every conclusion on having entered the original permissive
primary slice.

The intervention is a necessary breeder-count guard, not a two-sex population
model. It leaves opposite-sex availability, spatial co-location, mate encounter,
sex persistence and the pooled breeding/settlement abstraction unresolved.
Persistence after the guard would establish robustness only to this amendment;
loss of support would establish sensitivity of these selected witnesses, not
global impossibility or causal identification of trout, climbing galaxias or
habitat effects.

## Evidence and model comparisons

- The amended kernel is a versioned copy. The original
  `src/galaxias_model/common_model.py` remains byte-identical to the verified
  production source at SHA256
  `2031373352dbdb55b30db571dc7b861e67f804fc0b5709ef99233f73e8e463c4`.
- The only process change is applied before recruitment: totals below two set
  both recruitment intensities to zero; totals at least two retain the original
  arithmetic and all 18 event-keyed random-stream slots. The two Poisson slots
  are still consumed when their intensities are zero, preserving downstream
  pairing.
- The guard is used by the kernel's own deterministic burn-in and by both
  deterministic insurance scenarios. Source caches are local to the guarded
  module, so original-kernel initial states are not reused. This makes the
  initialization phase part of the sensitivity intervention, rather than a
  neutral prelude to it.
- Dated removals and observation timing are unchanged. Histories in which the
  amended trajectory cannot support a dated removal remain archived. Positive
  original support on any such history makes its paired amended contrast
  undefined; the analysis does not drop the history or renormalise the remaining
  original weight.
- Paired contrasts use observation weights recomputed from the **original**
  histories and original early/removal/viability terms. Rescored profiles use
  the amended histories' own early-pattern, removal-validity, viability and
  observation terms. These are separate outputs. All 1,024 histories remain in
  the amended joint-mean denominator, including zero-weight histories and all
  histories from an amended viability-failing source.
- Rescoring retains the existing ESS at least 100, relative Monte Carlo error
  at most 0.10 and largest-weight share at most 0.05 criteria. It separately
  reports survivor-tail ESS, relative error and largest share. Compatibility
  bounds now reproduce the established source-summary calculation exactly.
- Annual archives retain juvenile and adult counts by compartment,
  pre-breeding adult totals, recruitment means, realised recruits before density
  dependence and guard activation. The analysis reports exact guard-activation
  counts, annual stage means, counts below two adults, counts at one adult,
  refuge presence and terminal lake-only persistence without recoding lake-only
  survivors as extinct.

The data-generating process remains the original annual, stage-structured,
two-compartment stochastic kernel with one-year-lagged threats, fixed forcing,
common parameters and event-keyed demographic/environment streams. The
observation process remains the 14-record abundance-dependent detection model
under the same four `q` scenarios and three observation laws. Annual values
within a history are dependent; Monte Carlo uncertainty is therefore computed
across the 1,024 independent archived seed pairs within each source, not by
treating years as replicates.

## Verification and provenance

The freeze contains exactly 517 source IDs, 20,680 parameter rows, 529,408
archived seed pairs and 1,527 original qualifying source/profile rows. It binds
the verified validation manifest, sources, parameters, raw histories, original
analysis receipt and production-verification record. Every source has exactly
40 parameter rows and 1,024 unique replicate indices; both archived seeds are
checked against the original event-keyed derivation.

The finite budget is correct: 529,408 production histories plus at most 15,000
qualification, initialization and insurance executions gives an added ceiling
of 544,408 and a programme ceiling of 5,320,368, below 7.1 million. The current
receipt allocates 3,347 of the auxiliary ceiling, including a conservative local
test reserve, the initial smoke, final and superseded serial qualifications,
parallel qualification, both original replays, the initialization diagnostic,
and three deterministic auxiliary executions per production source. Failed and
superseded attempts remain charged and no adaptive top-up is authorised.

The inspected local checks report 32 guarded-kernel tests passed and the
analysis tests passed after repairing three consequential issues: the joint
upper confidence bound, incomplete receipt ancestry, and invalid-removal
counterfactual means. The final files compile under the locked local environment.
The final target qualification covers all 24 configuration/restriction cells
with two histories each. Serial and eight-worker parallel executions match over
all 76 output files. The end-to-end analysis consumed all 48 pairs from 24
sources and wrote its five hash-recorded products. Replay of the same 48
original-kernel histories reproduces all 49 archived fields with zero mismatches
and has zero forcing mismatches between original and guarded initialization.
The final production wrapper creates a single non-resumable run, fixes five
numerical-library thread variables to one, runs production before analysis, and
preserves a failed receipt instead of restarting.

The qualification diagnostic also resolves the observed initialization
difference. In 22 of the 24 target sources, the guard first activates at burn-in
step 2 and then activates on 50 of the 100 fixed burn-in steps, producing a real
two-cycle under the coarse deterministic map rather than floating-point drift or
an unintended arithmetic change. The two unaffected sources have exact initial
state parity. Representative terminal burn-in states show that this phase effect
can be large: for base source `RC0011`, guarded versus original adults are
32.2893 versus 4.8959 and juveniles are 10.6556 versus 169.7425; for juvenile
source `RJ0165`, the corresponding values are 311.5939 versus 23.3209 and
120.5866 versus 1077.7923. The forcing is identical, so these differences are
the expected consequence of applying the approved guard during initialization.

## Residual risks and recommendation

The chief residual risks are scientific rather than computational. The 517
sources are selected under the original model; their parameter distribution is
not a prior or posterior population. Sparse binary observations, unknown mapping
between model counts and surveyed fish, high-weight concentration in some
profiles, fixed parameter points, pooled breeding and settlement, and the lack
of sex structure remain. The amendment can interact nonlinearly with density
dependence, stage structure and observation weights, so no direction of effect
is assumed. Its scope includes sensitivity to the 100-step initialization phase:
downstream differences cannot all be attributed to late singleton histories.
The fixed burn-in length and phase are retained exactly as approved; redesigning
burn-in would define a different experiment and is not authorised. Comparisons
across `q` or observation laws remain scenarios, not
likelihood rankings. Multiple compatibility cells and thresholds are descriptive
views of the prespecified grid and must not be converted into discovery counts.

Recommendation: hash this finalized audit into the qualification gate and
dispatch the one finite production run on the approved deep-server snapshot.
After completion, verify every source/seed/output identity
and independently audit the central paired and rescored conclusions before any
synthesis is sent to Fable. That independent scientific review would materially
increase confidence because invalid-removal support, reweighted survival,
survivor-tail precision and witness losses are the decision-relevant results;
it should not expand the model, replace sources, add replicates or reinterpret
this sensitivity as a full demographic repair.
