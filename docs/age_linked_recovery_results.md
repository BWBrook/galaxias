# Linked age model and synthetic endpoint recovery

2 October 2026, Australia/Hobart. Candidate 2 and the
[executable protocol](age_linked_recovery_protocol.md) govern this tranche.

## Decision

**STOP before historical comparison: endpoint discrimination is unassessed.**
The linked runner passes its engineering qualification, but the frozen
synthetic design does not provide enough independent extinction sources to
assess its recovery criterion. This is a source-support and inference-bank
representation failure. It is not a demonstrated discrimination failure, and
the high frequency of persistence among completed simulations is not an
estimate of the historical population's fate.

Every one of the 40 cell × refuge-index strata has at most two distinct
completed extinction sources in either role. The protocol requires at least
16 coherent truth sources and eight inference-bank sources **in each terminal
class**. Observation conditioning can remove sources, but cannot repair this
pre-observation deficit. Fable's question—whether the linked population model
adds useful discrimination beyond the survey record—therefore remains open.

No historical calibration or causal counterfactual comparison was dispatched.
Both real-world terminal fate and the net effect of the rescue removals remain
unestimated.

## Fixed run and accounting

The run used all 20 candidate-2 cells, with 64 truth and 32 bank sources per
cell, four process replicates per source, and three linked sites per replicate.
The 1,920 source–cell rows represent 384 distinct nuisance sources; draws are
deliberately paired across restrictions and removal accounts. They must not be
treated as 1,920 independent biological parameter draws.

All **7,680 joint proposals / 23,040 nominal site-history attempts** were
accounted for without replacement. Generation took 472.55 seconds on
`utas-ubuntu`, using 16 workers and one native numerical thread per worker.

| Outcome or first failing constraint | Joint proposals |
|---|---:|
| Complete linked histories, 1965–2012 | 2,055 |
| Algebraic feasibility | 848 |
| Availability for natural-range captures/removals | 3,983 |
| Availability for Oberon-to-Strathgordon transfers | 735 |
| Captive age/sex availability at a known release | 59 |
| **Total** | **7,680** |

The last three rows sum to 4,777 process failures. These are first-failure
counts, not independent causes or the number of constraints a history would
eventually violate. There were 697,624 executed site-year advances. Failed and
partial histories, source identities, ledgers, and their reasons remain in the
raw archive; no failed source or process draw was replaced.

The largest individual failure groups were the early 12-fish captive-group
collection (1,385 histories) and the late 1991 ten-adult collection (1,218).
The imposed intervention history excludes many worlds with too few fish before
terminal classification. Donor requirements impose a further abundance filter
on the insurance population. This helps explain the composition of the retained
bank; it does not calibrate the source distribution to the real population.

## Terminal-class support

The completed truth histories comprise 1,355 persistence and 27 loss outcomes;
the completed inference bank comprises 661 persistence and 12 loss outcomes.
These are execution counts across paired cells, not independent evidence for
an endpoint probability.

| Distinct completed extinction sources within a cell × index stratum | Truth strata | Bank strata |
|---|---:|---:|
| 0 | 21 | 34 |
| 1 | 14 | 4 |
| 2 | 5 | 2 |
| 3 or more | 0 | 0 |
| Required minimum per terminal class | 16 | 8 |

There are 40 strata in each role. The below-one, age-eight, legacy-nursery,
joint-restriction primary stratum has no completed histories in either role.
It remains explicitly unassessed. The other 39 strata also fail both class
support requirements before applying observation coherence.

Actual linked loss histories exist, so the model does not structurally prohibit
the loss endpoint. Fourteen source–cell–role groups produce both terminal
outcomes among their process replicates. This does not establish matched
observational exposures or individual-history identifiability.

### Observation panel

The frozen analysis completed all 540 profiles and the Poisson, gamma-quality,
and fixed-total generators. It records 63,180 cell/stratum/profile/generator
rows for the 39 strata with completed histories. All 4,212 base-panel rows are
classified as insufficient truth **and** bank source coverage. The fortieth
stratum remains explicitly represented in the compact source-coverage table,
with zero completed histories. There are no qualifying columns.

The classifier abstains on every dataset because the extinction bank fails
its eight-source minimum. Accordingly, zero or undefined recovery metrics in
the raw tables are consequences of mandatory abstention, not estimates of a
well-supported classifier's accuracy. No valid full-minus-survey improvement
claim follows from this run. Both mechanical score controls pass: informative
high/zero exposures separate, and identical exposures with opposite terminal
labels remain tied.

Observation coherence further restricts the completed truth set. Across the
36 base profiles, the overall coherent fraction of the 1,382 completed truth
histories ranges as follows:

| Observation generator | Coherent fraction, minimum–maximum across base profiles |
|---|---:|
| Poisson | 20.4–93.5% |
| Shared visit-quality stress | 12.2–79.9% |
| Fixed Creek total, control only | 18.5–94.1% |

These are unweighted engineering-world diagnostics across paired cells, not
historical probabilities. Some generated loss datasets are coherent, but no
profile increases their maximum distinct-source support beyond two.
[`coherence_base.csv`](../data/age_linked_recovery_20261001/coherence_base.csv)
retains the source counts and changes in mean refuge index, refuge abundance,
and Lake abundance after conditioning, separately by cell, index stratum,
terminal class, profile, and generator. The full sensitivity tables and
generated observations remain in the analysis archive.

Analysis took 533.99 seconds. The finite generation-plus-analysis driver
completed in 16 minutes 54 seconds, with exit status zero; completion receipts
and all output hashes were verified after copying the archive locally.

## Refuge index and small breeding pools

Exactly half of the proposed sources in every cell and role lie above
`R0(1-p)=1` by design. After algebraic feasibility, the above-one share ranges
from 50.8–64.0% across truth cells and 51.6–71.4% across bank cells. Among
sources with at least one complete process history, it ranges from 53.1–100%
and 52.2–100%, respectively. These are per-cell ranges under the declared
engineering distribution; they are not prior or posterior probabilities of
viability. The index was not used as a viability exclusion rule.

Unweighted Pedder breeding diagnostics are retained for every completed
history. A small pool means at most two prespawning females or at most two
prespawning males; an attempted breeding event requires both sexes, and a
successful event requires at least one surviving newborn.

| Period | Breeding attempts | Attempts with a small pool | Successful recruitment events | Successful events with a small pool |
|---|---:|---:|---:|---:|
| 1997–2002 | 12,066 | 240 | 12,064 | 238 |
| 1997–2012 | 31,329 | 717 | 31,326 | 714 |

These are descriptive event totals across the 2,055 completed histories,
including deliberately paired cells. Cell/role/index tables preserve the
heterogeneity: the small-pool share of successful events ranges from 0–38.5%
over 1997–2002 and 0–50% over 1997–2012. The longer wild trajectory is a
conditional model projection. No factual weighting or empirical small-pool
viability claim is available from this recovery exercise.

## Runner qualification and source correction

Local and Linux qualification each used 21 joint engineering histories.
All four deterministic ledger cases completed; seven of eight stochastic cases
completed, with the remaining captive-release shortfall preserved. Repeating
the eight stochastic cases in parallel produced exactly the same decoded raw
histories. The finite source-bank smoke likewise reproduced serial and parallel
compact and full raw content exactly.

The independent audit checked the raw vectors and verified:

- The initial captive group is 5 female and 7 male; its released survivors are
  3 female and 4 male. The exact complementary capture cohorts account for the
  five captive deaths.
- Founder additions total 34 under the primary account and 45 under Sanger's
  sensitivity, including the later three-fish release.
- All five transfers total 353 fish. Their donor compartment/sex/age tensors
  conserve the recipient sex/age vectors, including sampling from both donor
  compartments and younger ages.
- Captures precede releases, held fish retain cohort identity and chronological
  age, and release vectors contain no terminal-age fish.
- The no-wild-removals engineering counterfactual suppresses every dependent
  rescue addition and transfer. Oberon and Strathgordon remain empty, and the
  paired Pedder history is identical through 1989.
- Extended forcing agrees exactly with 2,052 common-model scalar values through
  2002, and all arms retain one hashed union calendar.

`make fast-check` passed 300 tests, with five existing slow tests deselected.
Those slow tests were not rerun. Qualification and source-bank replay are
separate engineering checks, not additional independent recovery observations.
The bounded implementation/target work remains within the 8,000-site-history
reserve: remote qualification and the two replay smokes charge 543 nominal
site histories, with a conservative 1,000-history local-development charge
(including at least 435 recorded linked-history executions). This 1,543 charge
is budget accounting, not a claim of 1,543 independent simulations. The
960-history recovery-control reserve was unused because the score controls
require no demographic calls.

The source query is resolved. The May-1997 IFC newsletter, p.3, reports the
50–200 estimate and 18 + 13 early Oberon releases. The project had already
located it on 8 September. The 31 releases corroborate the primary account;
the estimate's population coverage remains undefined and it cannot supply a
pre-removal denominator. Its retrieval correction adds no new population
constraint. See the [source correction](age_linked_recovery_protocol.md#source-correction)
and the [original newsletter](https://www.ifs.tas.gov.au/media/publications/IFS_Newsletter_VOL26-_NO1-_MAY1997.pdf#page=3).

## Next scientific decision

Repair the recovery sampling design before historical search. A useful design
must obtain enough independent, intervention-consistent worlds in both
terminal classes while making its proposal distribution, any importance
weights, and validation separation explicit. Sampling more copies of the
current surviving sources cannot supply the missing source diversity.

Such a repair must not silently soften the documented captures/transfers,
change biological assumptions to manufacture losses, lower the agreed
qualification thresholds, or reinterpret the surviving bank as historical
evidence. The present frozen run should remain the record of what the accepted
engineering design could and could not assess.

## Artifacts and reproducibility

Compact deliverables are in
[`data/age_linked_recovery_20261001/`](../data/age_linked_recovery_20261001/).
The source-bank and raw-history archive is mirrored locally at
`outputs/remote/age_linked_recovery_20261001/` and retained remotely at
`/data/codex/scratch/galaxias/age_linked_recovery_20261001/`.
The immutable dispatch snapshot records 610 staged files and Git ancestry
`81e37202f6322e37ac7f1b0070402b76b7967a82`; generation and analysis receipts
separately bind the actual implementation, inputs, and outputs.

The run scripts and qualification receipts are copied into `provenance/`.
The dispatch snapshot's 610 files were verified again on the server after
completion, and all 42 generation-source bindings and 10 analysis-source
bindings still match the local implementation. Compact CSV copies use LF-only
serialization; original raw tables retain their original hashes in the archive.
A separate read-only methods agent independently reproduced the support and
coherence results, re-aggregated the small-pool diagnostics from full histories,
and verified all 47 analysis-output hashes. It found no material repair needed.
This review supports the stated qualification limits, not empirical validation
of the historical endpoint.

The key review artifacts are the
[gate decision](../data/age_linked_recovery_20261001/gate_decision.json),
[40-stratum coverage table](../data/age_linked_recovery_20261001/stratum_coverage.csv),
[failure accounting](../data/age_linked_recovery_20261001/process_summary.csv),
[source-support table](../data/age_linked_recovery_20261001/source_support.csv), and
[small-pool diagnostics](../data/age_linked_recovery_20261001/small_sex_pool_summary.csv).

Reproduce the compact summaries from the completed, hash-bound archives with:

```sh
uv run --locked python scripts/summarize_age_linked_recovery.py \
  --input-dir outputs/remote/age_linked_recovery_20261001/gate \
  --analysis-dir outputs/remote/age_linked_recovery_20261001/analysis \
  --output-dir outputs/age_linked_summary_new
```

The output directory must be new. No commit, push, or publication accompanied
this tranche.
