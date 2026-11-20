# Common-model implementation clarifications

Date: 2026-09-18. The signed candidate-2 protocol remains unchanged at SHA256
`c165e25bfa223cbb79ba00fce75f099c13979746b2d516ae06e93af5243879d8`.
This note resolves an unspecified diagnostic allocation within its existing
scientific question and 7.1-million-history ceiling, before new-model execution.

## Boom metric

Keep the existing `pedder_lake_index = N_L/(N_L+K_L)` for the boom peak, its
comparison with pre-flood/late means, and peak-year timing. Candidate 2 explicitly
changes CT005 to raw N_L but does not replace the existing boom metric. Record
this metric in the run manifest; do not silently substitute a raw-count mean.
The peak-year ordering is unchanged by this monotone transformation at a source,
but comparisons with means can differ, so the choice remains visible.

## Paired switches at joint-model sources

Section 5 requires paired mechanism switches at frozen R_J sources, but section
6 does not count those histories separately or specify their replicate count.
Use validation replicate indices **1–64**, chosen in advance, at every final
R_J source. Evaluate R_H, R_T and R_C using the same source parameters and the
same validation demographic/environmental seeds. Preserve the factual R_J
source identity and record the evaluated restriction separately. Reuse the
factual histories for those same 64 indices; do not simulate a new baseline.

For each q/observation representation compute factual weights on exactly these
64 histories and hold them fixed across switches. Report paired endpoint
contrasts, Monte Carlo errors, weight concentration and unsupported cases. This
is a fixed-parameter sensitivity diagnostic, not a refitted-null result or a
validation result at 1,024-replicate precision. Its ESS cannot exceed 64 and
therefore cannot meet the primary ESS>=100 criterion or supply compatibility
witnesses. Primary compatibility maps remain based on independent restriction
refits and their full validation histories.

For minimum dated removals, a switched history may be unable to supply a
documented extraction. Report the factual-weighted mass with invalid switched
removals and leave its main endpoint contrast undefined if that mass is
positive. Do not fabricate fish, clip removals, or silently renormalise the
remaining histories. Apply this same physical-validity rule to the overshoot
counterfactual. Unsupported factual weights also produce undefined contrasts.

The maximum final R_J union has 6 configurations × 2 search seeds × 40 sources
= 480 sources. Three switches × 64 histories × 480 adds **92,160** histories.
The full prospective maximum becomes **7,071,040**, including the 712,000
archived-history replays; **28,960** remain within the original hard ceiling
for prescribed implementation checks. No additional search wave or source is
created. Deterministic insurance checks remain separately counted as before.
Count actual executed histories, including both sides of serial/parallel tests,
in the execution receipt. Do not consume unused viability-failure allocations
as replacement proposals or new diagnostic work.

The bounded independent methodological audit checked this arithmetic and the
paired estimand before execution. Fable receives this clarification with the
pre-run reconciliation and serial/parallel evidence. It is not new empirical
validation or a change to the signed causal interpretation limits.
