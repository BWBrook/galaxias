# Final bounded terminal-probability gate

3 October 2026. **STOP_FINAL_BOUNDED_ATTEMPT.** No primary procedure qualified
after the third bounded attempt. The terminal loss probability remains
unassessed under the prescribed procedure. Actual remaining records were not
consumed, no historical loss probability was calculated, and no further
proposal was started. The frozen design is in
`docs/age_probability_gate_protocol.md`.

## Result and interpretation

The complete analysis contains 1,152 assessment rows: eight process cells,
two refuge-index strata, 36 observation profiles and two matched observation
laws. No row qualified, including the maximum-age-eight sensitivity.

| Maximum age | Computationally unassessable | Computational checks pass, calibration too uncertain | Qualified |
|---|---:|---:|---:|
| Six, primary | 564 | 12 | 0 |
| Eight, sensitivity | 469 | 107 | 0 |

This is an uncertainty-limited result. Calibration was neither established
nor decisively rejected under the frozen rule: no row received
`CALIBRATION_FAILED`, and none met the required calibration equivalence bounds.
The result does not determine whether the wild population was lost or persisted,
or establish that historical fate is unidentifiable in principle.

Record-directed sampling still left the conditional weights concentrated in
few independent sources. Each age/index/role group contains 256 planned
sources, but primary source ESS is only 2.06–19.91 for synthetic truths and
2.95–12.87 for inference. The largest source contributes 13.2–65.2% of truth
weight and 16.6–43.7% of inference weight. ESS is a diagnostic here, not a
reintroduced minimum number of sources per terminal class.

| Primary restriction | Refuge index | Truth source ESS | Inference source ESS | Best precision-covered truth weight | Computational passes / 72 |
|---|---|---:|---:|---:|---:|
| R_H | Below one | 14.64 | 5.10 | 0.0% | 0 |
| R_H | Above one | 19.91 | 12.87 | 0.0% | 0 |
| R_T | Below one | 5.10 | 4.47 | 99.9% | 12 |
| R_T | Above one | 11.49 | 8.39 | 0.0% | 0 |
| R_C | Below one | 8.94 | 5.57 | 58.0% | 0 |
| R_C | Above one | 18.33 | 12.41 | 93.2% | 0 |
| R_J | Below one | 2.06 | 2.95 | 29.9% | 0 |
| R_J | Above one | 6.84 | 5.23 | 61.0% | 0 |

Precision coverage combines finite bootstrap support, forecast-interval width
at most 0.20 and half-bank disagreement at most 0.05; at least 95% of target
truth weight was required. The table shows the best coverage across all 72
prespecified profile/law combinations in each group, without selecting one
for subsequent inference. The twelve computational passes all occur in
R_T below one. Their marginal calibration residual intervals contain zero,
but their upper limits range from 0.682 to 0.723, far beyond the required
0.05. They therefore cannot establish calibration within the declared tolerance.

All primary synthetic records have finite supported forecasts within numerical
roundoff. Seventy-seven primary rows contain explicit zero/one-probability
contradictions for positive-weight truth outcomes; none of these flags arises
solely from an undefined forecast. Boundary safeguards prevent rare or absent
events from acquiring a spuriously certain bootstrap estimate. No probability
was clipped to make a contradiction disappear. The source-weighted breeding-pair,
same-compartment-pair and age-1+10 diagnostics remain archived separately and do
not qualify the unassessed primary endpoint.

The target includes feasibility of known interventions after 2002. Among
histories valid through 2002, those later constraints exclude 5.3–45.2% of
early-evidence weight in the primary truth groups and 5.2–39.4% in the inference
groups. This material selection is recorded in
`data/age_probability_gate_20261003/future_feasibility_selection.csv`.
Any conditional probability from this design would include that retrospective
information. The E-only probabilities and functional-endpoint compositions
are simulation diagnostics, without historical qualification.

## Scope

Barry accepted option A in the relayed Fable message 841: one further bounded
attempt using broader nursery allocation, record-directed sampling and a
probability-calibration criterion. This follows two preserved STOP results.
The earlier gates assessed terminal-class discrimination; this gate instead
asks whether a conditional loss probability is precise and calibrated, and
whether remaining observations improve it over the early-evidence comparator.

The run uses the existing broad nursery range, with 35–90% of recruits
allocated to the lake. Maximum age six is primary; eight is a sensitivity.
All four restrictions, both refuge-replacement-index strata and the primary
removal account remain separate. The biological kernel, intervention calendar
and parameter support otherwise retain their previous definitions.

The conditioning block contains the eight observed Lake visits, the early
creek allocation of 68 and one fish, March 1996 presence, and feasibility of
the complete intervention chronology through 2012. Remaining observations
are the late creek count and nine insurance-population binary records.
Synthetic remaining records are generated under two matched observation laws
and all 36 prespecified base profiles. Actual remaining records are withheld
unless a primary procedure qualifies, and would then be used only once.

Continued creek records are consistent with recruitment after the lake decline.
The retained primary sources do not establish continuous lake-nursery absence
from 1983, two identified generations of creek-born fish, or a wild mating-pair
observation in 1991. Hamr describes breeding-condition adults and successful
artificial fertilisation. The recovery plan supports a six-year lifespan.
These qualifications are preserved in the protocol; nondetections are not
converted to a hard empty-lake condition.

## Execution and qualification

The allocation is 147,456 nominal site-history attempts: 49,152 linked
three-site attempts, in eight cells with 512 truth and 512 inference sources
and six process replicates per source. The 8,192 cell/source rows contain
2,048 independent nuisance identities, paired across restrictions.

The joint proposal uses both earlier archives and only the conditioning block,
with the earlier proposal correction applied once. It retains a 50% uniform
component and two joint beta-kernel components. Failed planned attempts remain
in the source universe with zero contribution. Terminal labels and remaining
observations do not enter proposal fitting. The natural-prevalence forecast
does not balance terminal classes or assign them equal prior probability.

The local fast check passed 368 tests; five existing slow integration tests
were excluded. All 42 targeted tests also passed on Linux. Local and Linux
qualification each used the same fixed 32 joint attempts. Linux serial and
16-worker replay matched exactly. Mac/Linux sources and complete history
records agreed within absolute tolerance 1e-10 and relative tolerance 1e-12
across 416,160 numerical comparisons; the largest absolute difference was
2.91e-11. They were not byte-identical across platforms.

An independent methods review found no blocker to qualification. Corrections
before biological qualification included pooled independent-source boundary
bounds, propagation of zero-probability comparator contradictions, and complete
analysis dependency bindings. The final proposal geometry was unchanged by
the last metadata-binding correction. A 32-bit seed collision was detected
before production simulation; the replacement namespace passed the full
cross-archive and qualification-seed check with zero overlap.

Production completed on `utas-ubuntu` with 16 workers and one numerical-library
thread each. All 49,152 planned joint attempts are accounted for: 15,384 complete
histories, 5,568 algebraic exclusions and 28,200 process failures. Generation
took 3,244.4 seconds (54.1 minutes), and analysis took 117.4 seconds. The wrapper
exited zero at 08:27 UTC, reverified its 720-file source snapshot, and ended its
processes. Its proposal and protocol remain frozen.
The remote parent directory is
`/data/codex/scratch/galaxias/age_probability_gate_20261003`; its local mirror is
`outputs/remote/age_probability_gate_20261003`. Compact receipts and result
tables are under `data/age_probability_gate_20261003/`.

The independent result audit passed 52/52 checks. It verified physical and
decompressed hashes, complete source/history coverage, the earlier receipts,
all 1,152 decision rows and all 576 primary rows. It independently reconstructed
all 16 E-only probabilities and 32 deterministically sampled synthetic forecasts
using fresh negative-binomial and Poisson/shared-Gamma binary formulas. Maximum
absolute disagreement was 3.11e-15. The audit verifies the frozen remote
rehash receipt rather than equating the subsequent local reporting worktree
with the original snapshot. No OS-level file-access trace was recorded; the
no-actual-R conclusion follows from the bound source, execution path and
receipts. See `provenance/independent_result_audit.json` in the compact bundle.

The tranche reallocates 147,456 attempts from the remaining original search,
leaving 251,904 and retaining the programme plan of 1,035,520 below its
1.1-million ceiling. The explicit new platform smokes used 288 site attempts;
the full additional allowance of 1,000 is conservatively charged, including
tests, bringing qualification accounting to 3,263 of the existing 8,000
reserve. All earlier result receipts and the previous handoff are
preserved. No additional draw or relaxed criterion is authorized if this
attempt remains unassessable. The agreed stopping condition has now been met.
