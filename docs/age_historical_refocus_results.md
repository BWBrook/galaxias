# Lake-history-conditioned recovery test

2 October 2026. **STOP_BEFORE_HISTORICAL_COMPARISON.** The bounded repair is
implemented and its prospective run is complete. Early-Lake conditioning changes
the weighted histories, but the fresh sample still cannot support terminal
recovery assessment. No historical comparison or rescue-effect calculation was
launched. Generation, analysis and mirrored-output receipts have been verified.

## Prospective recovery result

The run generated 30,720 joint attempts, charged as 92,160 nominal site-history
attempts: 9,740 completed, 3,544 failed algebraic feasibility and 17,436 failed
process/intervention feasibility. Its 15,360 source-bank rows are paired
cell/source combinations. They represent **3,072 independent nuisance IDs**:
2,048 truth and 1,024 inference IDs. Each has its planned two process replicates
within each applicable cell, with no replacement.

All 4,320 base-panel primary rows are unassessed for both truth and inference
support. This includes 2,880 Poisson/gamma rows eligible to qualify and 1,440
fixed-total controls. There are zero qualifying passes. The limitation already
exists before observation coherence or weighting:

| Loss-class support within a cell/index stratum | Truth | Inference bank |
|---|---:|---:|
| Raw independent sources, range across 40 strata | 0–14 | 0–7 |
| Required independent sources | 16 | 8 |
| Maximum available under base observation coherence | 12 | 7 |
| Maximum base loss-class source ESS | 3.72 | 2.45 |
| Required source ESS | 16 | 4 |

The 540-profile, three-generator, four-endpoint analysis retains 259,200 rows.
All are unassessed: 258,984 lack both truth and bank support; 216 lack truth
support alone. Breeding-pair, same-compartment-pair and age-1+10 endpoints
therefore do not provide an assessed alternative. No balanced-accuracy or
survey-versus-full-model improvement has been estimated from this run.

This is a representation failure of the bounded proposal, not a measured failure
to discriminate adequately represented terminal classes. Weighting cannot
create the missing independent loss histories. The frozen thresholds and run
size were retained.

## Effect of the Lake evidence

Compare the early-Lake target with the process-feasible original engineering
distribution using the same fresh histories and proposal-density correction.
The following counts keep truth and inference draws separate; they are counts
of model/index strata, not model-averaged probabilities.

| Primary-conditioning diagnostic, out of 40 strata | Truth | Inference bank |
|---|---:|---:|
| Weighted mean Lake abundance in 2002 decreases | 39 | 33 |
| Weighted loss share increases | 14 | 9 |
| Weighted loss share decreases | 17 | 14 |
| Weighted loss share is unchanged | 9 | 17 |
| Weighted loss share exceeds one half | 0 | 1 |
| Conditional median persisting abundance is at most four fish | 0 | 0 |

Thus the directional expectation of lower Lake abundance is usually reproduced.
The stronger prediction of majority loss with only a handful of persisting fish
is not reproduced by the primary diagnostic. Representation remains too sparse
to estimate a precise terminal frequency: total source ESS ranges from 2.87 to
39.30 in truth strata and 1.03 to 16.85 in inference strata. The sole
majority-loss inference stratum has total ESS 1.03 and loss-class ESS 1.01.
The loss-class support table above is more relevant to recovery than the total
ESS. These diagnostics do not establish historical persistence.

The absolute-absence sensitivities demonstrably change the weights, but usually
concentrate them further. For a compact view, the table below uses both campaign
nondetections, equal declared q values for the two different methods, and the
midpoint electrofishing time proxy. The full unequal-q grid, separate-campaign
cases and start/end time brackets remain in the archived tables.

| Campaign law and assumed q for each method | Majority-loss truth strata | Majority-loss inference strata | Inference total source ESS, range |
|---|---:|---:|---:|
| Poisson, 0.01 | 11/40 | 7/40 | 1.00–3.71 |
| Poisson, 0.1 | 13/40 | 10/40 | 1.00–1.05 |
| Poisson, 1 | 13/40 | 10/40 | 1.00–1.0001 |
| Gamma quality, 0.01 | 8/40 | 5/40 | 1.00–5.68 |
| Gamma quality, 0.1 | 11/40 | 5/40 | 1.00–4.92 |
| Gamma quality, 1 | 10/40 | 5/40 | 1.00–4.84 |

The q values are assumptions, not detection estimates. The apparent terminal
fractions often depend on roughly one effective source and disagree between
truth and inference samples. They cannot establish historical fate or rescue a
failed primary gate. Under extreme Poisson weighting, blank conditional
persistence quantiles can reflect numerical underflow of the globally normalized
persistence weight; they do not demonstrate that no persistent history exists.

## What the repair addresses

The first gate sampled intervention-feasible worlds and generated new
observations from them. Its coherence event did not condition those worlds on
the actual early Lake trajectory. It could therefore retain large lake
populations without demonstrating a missing or numerically broken Lake score.
The repaired question conditions on that trajectory before testing whether
fresh observations discriminate loss from persistence.

The fixed design is in `age_historical_refocus_protocol.md`. A proposal trained
on the first archive generates fresh, independent truth and inference sources.
The target retains the original engineering distribution, corrected for the
proposal density and weighted by the early-history score exactly once. The
proposal does not use terminal outcomes. There is no replacement of failed
attempts or adaptation to this test's results.

The eight retained Lake visits replace the earlier two-bin allocation score.
The 1988–89 electrofishing and 1990–91 larval nondetections enter named
sensitivity targets, with explicit assumed detection strengths and campaign
quality. Their uncalibrated effort cannot identify absolute abundance or
justify a hard empty-lake constraint through 2002. No primary later lake-specific
effort series was recovered in the local corpus audited here.

The primary endpoint remains any natural-range fish at end-2002. Separate
endpoints describe a realized male/female breeding pair in the 2002 prespawning
pool, a pair in the same modeled compartment, and at least ten age-1+ fish at
end-2002. They do not form a guaranteed viability ordering. Compartment breeder
counts omitted from the old summary are recovered from retained states and
the original keyed draws; their pooled totals must match the stored diagnostics.

The full intervention chronology remains a process condition, including later
insurance transfers. The target is therefore not conditioned on an exclusively
pre-1996 information set. No new abundance score is added for the rescue fish.

## What the original archive establishes

The source diagnostic confirms 2,005 of 2,016 persisting histories had fish in
the Lake in 2002. Across the persisting histories, median Lake abundance was
21,182.5 and its 95th percentile was 1,026,811.5. These are unweighted simulated
histories, not estimates of historical abundance.

| Empty-Lake terminal class | Histories | Independent nuisance source IDs | Cell/source combinations |
|---|---:|---:|---:|
| Natural-range loss | 39 | 23 | 32 |
| Creek persistence | 11 | 10 | 11 |

The eleven persisting histories had one to four refuge fish. Selection on the
2002 Lake state is an exploratory diagnostic; it is not used to train the new
proposal or define historical compatibility. Pairing across restrictions and
removal accounts does not create independent sources. The count of 28 distinct
parameter sets quoted in the review is therefore not used as the independent
sample size.

Wild-capture availability failures occurred in 1,404 histories in 1990, 2,557
in 1991, and 22 in 1996. Actual collections constrain the eligible sex/age pool
immediately before each event. Summing captures over 1990–91 does not establish
that all those fish were alive simultaneously, because survival and recruitment
occur between events.
Bounds involving inferred extractions also inherit the declared removal-account
assumptions; reconstructed captures are not additional recovered field counts.

Before the fresh run, the protocol recorded a directional expectation of less
Lake-supported persistence after early-history conditioning. Fable's stronger
prediction—majority loss, with only a handful of fish in persisting worlds—was
recorded as a hypothesis, not as an acceptance criterion or a historical
probability.

## Verification and provenance

The local `make fast-check` passed 326 tests, with five existing slow tests
excluded; portability and compilation checks also passed. The accounting
summarizer reproduced its smoke CSVs exactly and rejected deliberately missing
bindings and inconsistent counts.

The Linux qualification passed 26 focused tests. Its 80 joint attempts produced
34 complete histories, 16 algebraic failures and 30 process failures; one- and
16-worker executions matched exactly for raw and compact history content.
The local and Linux compact features also matched byte-for-byte. Raw local/Linux
outputs differed only in small floating-point forcing and diagnostic values
within a declared relative/absolute tolerance; they are not claimed to be
byte-identical across platforms.

All 661 files in the source snapshot were verified before remote dispatch.
The 9,216 unique parameter/process seeds for the full run have no overlap with
the training archive or qualification namespace. Weighted-score controls pass.
The archived breeder reconstruction agrees with an independent replay for all
2,055 completed original histories.

The fixed allocation is 20 cells × (512 truth + 256 inference sources) × two
process replicates × three sites = 92,160 nominal site-history attempts. This
is reassigned from the original initial-search allocation, leaving 399,360
there. The planned programme allocation remains 1,035,520 within the 1.1-million
ceiling. The conservative qualification charge is 2,263 of its 8,000 reserve,
including 240 local and 480 Linux attempts for this repair.

An independent methods check before prospective results clarified that the
synthetic experiment provides fresh replicate observations conditional on the
early-history target. A pass is necessary but not sufficient to validate the
historical comparison using the remaining evidence: the actual Lake record
has already been consumed in the target weights. It cannot be scored again as
if it were the synthetic replicate. Any continuation must use the remaining
evidence once, or return to the original engineering distribution and evaluate
the full joint score once. The frozen test is retained with that interpretation.
The analysis receipt's assessed base-primary count includes fixed-total controls;
its qualifying pass count excludes those controls.

Compact artifacts and source records are in `data/age_lake_repair_20261002/`.
The unchanged first gate remains in `data/age_linked_recovery_20261001/` and
`outputs/remote/age_linked_recovery_20261001/`. The new remote source and outputs
are under `/data/codex/repos/galaxias-age-refocus-20261002` and
`/data/codex/scratch/galaxias/age_lake_refocus_20261002` on `utas-ubuntu`.

The generated archive and full analysis are mirrored in
`outputs/remote/age_lake_refocus_20261002/`. Generation took 2,003 seconds and
observation analysis 411 seconds. The remote driver exited zero and reverified
all 661 snapshot files. `gate_summary/audit.json` binds the compact tables to
the verified generation and analysis outputs; `report_summary.json` records the
descriptive comparisons above.

## Scientific stopping point

This tranche repairs the conditioning contract, adds the missing evidence
sensitivities and functional endpoints, and measures the remaining support
problem. It does not supply a qualified collection of history-compatible loss
and persistence worlds. Another unmodified large draw is not established as a
solution. A further proposal would need an explicit way to represent the narrow
joint region satisfying the early decline and later collections, checked against
the uncertain Lake observation process. No such additional adaptive proposal or
biological change was made here. The original and repaired STOP results, source
snapshots, raw histories and qualification evidence are preserved.
