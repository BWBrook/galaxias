# Approved singleton breeding guard: fixed-witness sensitivity

20 September 2026. Barry approved the proposal, required compute and modified
demographic kernel in Codex: “Thanks for the clarification. Yes, looks good for
the next bounded test: approved, including required compute and modified
demographic kernel.” This freezes the scientific scope below. The original
proposal, signed candidate-2 protocol, kernel and archives remain unchanged.

## Scientific decision

Test how much the existing compatible witness set depends on allowing one
adult to generate recruits. This is a narrow robustness question, not a new
search or a definitive test of whether cryptic persistence is possible under
all biologically defensible models.

Approved comparison: retain the original recruitment equation when
the pre-breeding adult total A = A_L + A_R is at least two; set recruitment to
zero when A < 2. Juvenile/adult survival, maturation, density dependence, movement,
forcing, removals and observation laws stay unchanged. PR004 is not retuned.
The guard also applies during demographic initialization and insurance-scenario
evaluation; recalculate those states and viability diagnostics instead of
reusing caches made by a different kernel. For deterministic noninteger adult
states use the same explicit A < 2 rule, recognising this as a coarse closure
for a necessary breeder-count condition, not an exact expectation over sexes.

This removes reproduction by one modeled adult. It does not ensure opposite
sexes, co-location or mate encounter when A >= 2, and it retains the pooled
breeding/settlement abstraction. It is therefore a structural sensitivity to a
necessary condition for reproduction, not a complete demographic repair.

Fable's proposed expected factor A(1-2^(1-A)) is not E[2 min(F,M)] for a 1:1
binomial sex assignment. At A=3 the two expressions are 2.25 and 1.5. The
factor instead equals E[2F 1(M>=1)]: female reproduction with male presence,
scaled to preserve adult-based fecundity and permitting one male to fertilise
multiple females. These different biological assumptions require an explicit
choice; neither is needed to test the narrower singleton defect first. An
expected recruitment factor would also not reproduce the stochastic variation
or persistent sex composition of an explicit two-sex population.

## Fixed inputs and finite execution

- Freeze the 517 distinct source IDs witnessing the original permissive primary
  slice (early lower95 >= .50, joint lower95 >= 1e-6 and original joint-weight
  qualification), their parameters, configurations and archived validation
  seeds. They were selected under the original kernel; that selection limits
  inference. No refocusing, replacement sources, parameter refitting or new q.
- Execute 1,024 amended histories per source: **529,408 stochastic historical
  trajectories**. Use the original histories as the paired baseline and retain
  event-keyed seed streams. This is a kernel-sensitivity comparison, not fresh
  independent validation of newly selected parameter points.
- Re-evaluate early targets, dated-removal validity and the insurance viability
  screen under the amended demographic equation. Keep failures and all source
  identities; zero-weight sources do not get replacements.
- Store annual J_L, A_L, J_R, A_R, pre-breeding adult total, recruitment mean,
  realised recruits before density dependence, and guard activation in compact
  archives. This resolves the missing stage and compartment information without
  asserting that it measures actual breeding locations. Include the existing
  observation-state fields and all original target/weight diagnostics.
- Reserve at most 15,000 additional qualification/initialization/insurance
  executions conservatively in the receipt. Added ceiling: 544,408; programme
  ceiling after this amendment: **5,320,368**, within the original 7.1 million.
  No further runs follow automatically if the comparison is inconclusive.
  Choose and check remote resources before dispatch; no production simulation
  on the Mac mini. This document is not an execution-budget receipt.

## Estimands and interpretation

Primary survival remains N_L + N_R > 0. Report refuge presence, lake-only
persistence, compartment counts, stage structure and low-adult transitions as
secondary diagnostics. Do not recode lake-only survivors as extinct.

Report two explicitly separate comparisons:

1. Paired process contrasts under the original factual history weights, to
   describe changes along matched parameter/seed histories. Any amended
   invalid-removal history with positive original support makes that paired
   contrast undefined; do not discard or renormalise its original weight.
2. Rescored source compatibility and survival using the amended histories'
   own early-pattern, viability and observation terms, with the same factual
   records and q scenarios. All 1,024 histories remain in each source's joint
   mean; invalid histories contribute zero. Preserve the existing ESS/RSE/
   maximum-weight criteria and report survivor-tail precision separately.

The direction of reweighted survival is an outcome to estimate. Lower
recruitment can change density feedback, stage structure and observation
weights; the old flagged fractions are not predicted survival losses. Report
effect sizes and Monte Carlo errors, not just changed witness counts. New
precision problems remain unresolved, without an automatic replication top-up.

Persistence under the guard would establish examples robust to this specific
necessary-condition amendment within the fixed set. Loss of support would
establish sensitivity of those witnesses, not global exclusion of persistence
or identification of climbing effects. No new cutoff distinguishes two causal
branches, and no <=5-to->20 transition rule is introduced as a rejection test.

## Gates and closeout

Barry has approved the precise amendment and ceiling. Before scientific dispatch:
freeze the new implementation and source/seed manifest; test A=0/1 zero
recruitment and A>=2 unchanged recruitment, deterministic closure, source
initialization, observation timing, failure retention and serial/parallel
identity on the target. Verify the original baseline/archive bindings without
overwriting them. A consequential departure from this proposal returns for a
scientific decision.

After completion: verify identities and output hashes, independently check the
central paired/rescored conclusions, write one conditional synthesis and hand
the findings to Fable. No additional search, combined structural change,
commit, push or publication is included.

## Execution specification

Use eight spawned workers on deep-server-ts, with numerical library threads set
to one. The new source snapshot is /data/codex/repos/galaxias-mate-guard-20260920;
run artifacts are /data/codex/scratch/galaxias/mate_guard_20260920. Use the exact
original production Python/NumPy/pandas/Linux runtime. Do not overwrite or
resume an existing run directory. Failures retain their directory and reservation.

A hashed freeze records all 517 source identities, 20,680 parameter rows,
529,408 pairs of archived demographic/environment seeds, and the 1,527 original
qualifying source/profile rows. Production must use exactly this membership and
1,024 replicates per source; reduced runs are explicitly labelled qualification.
Separate per-source raw and annual archives join losslessly by source ordinal
and replicate index. The raw rows carry both complete seeds and source identity.

The execution receipt reserves 529,408 production historical calls plus an
auxiliary allowance of 15,000 executions. Count deterministic initialization
and each insurance scenario conservatively as one execution, even though their
cost differs from a stochastic history. Reserve all attempted source tasks;
failed attempts do not restore budget. Qualification, smoke and baseline replay
calls are charged to the auxiliary allowance. Record any cache-related upper
bounds explicitly. No adaptive top-up is authorised.

A target qualification gate binds the complete implementation, model inputs,
this protocol, fixed-source manifest, exact runtime and independent preflight.
It includes byte-identical serial/parallel archive comparisons and an end-to-end
analysis smoke. Production refuses mismatched bindings. Verify the original
baseline's source and output hashes and require exact original runtime before
execution. Kernel tests and selective original-kernel replay supplement the
already completed 712,000-history legacy replay; the original archive is not
rerun in full.
