# Response to Fable's age-structured review

29 September 2026. Correspondence thread 31, message 650. This records the
completed review-response and observation-check tranche. The full linked runner,
synthetic recovery gate and historical comparison have **not** run.

## Decisions incorporated

Candidate 2 is in `age_structured_protocol_candidate2.md`; the candidate-1
protocol and qualification records remain unchanged. Its five changes are:

1. Use the recovery-plan removal account in all 16 primary cells. Restrict
   Sanger's account to four declared held-fish sensitivities. The resulting
   20-cell proposal contains 1,035,520 future site histories, including a
   24,000-history synthetic recovery reserve and both counterfactuals. This is
   about 35% below candidate 1, within the proposed 1.1-million ceiling.
2. Include Hamr's 4 February 1992 survey in one conditional three-block
   observation term with counts (68,1,0). Profile the unknown relative effort;
   remove any duplicate positive-only contribution from this same capture.
3. Use Lake's three verified zero occasions, 1983, 1986 and 1989. The five
   unambiguous positive visits in 1976–80 provide the reference. Keep the
   unresolved 0/0.5 time labels outside the primary score, and retain the SE/SD
   conflict without using either interpretation to estimate dispersion.
4. Report the neutral isolated-refuge replacement index R0(1-p), its support
   fractions before and after feasibility checks, and the participating sexes
   in post-1996 breeding. The index is a diagnostic, not a viability gate.
5. Require a prospectively specified full synthetic recovery test before large
   historical search. Add the no-wild-removals counterfactual at fixed factual
   weights, preserving the benefit/cost accounting across all three sites.

The age/sex demographic kernel is unchanged. Six/eight-year lifespan scenarios,
corrected nursery timing and post-recruitment environmental variation stand.
The juvenile catch shares remain diagnostics for this comparison. Shared
demography across sites, pooled-creek mating and independent annual recruitment
variation are explicit limitations.

## Evidence qualifications

Hamr's contemporary account gives the February survey, release sexes and eleven
captive offspring. Chilcott's total of ten captures in 1992–96 constrains
reconstruction under a common-coverage assumption; it is not an independently
scored total on top of those captures. Sanger's additional eleven wild founders
relative to the primary account are placed in pre-1992 holding only as a
scenario. Captivity and non-overlap of the reported source groups are not
established identities. Horner et al.'s approximately 45 founders and seven
offspring are retained as conflicting retrospective evidence, without a new
model cell. Registers are in `data/age_structured_design_20260929/`.

The accessible Lake chapter states that no more than 200 fish were believed
to exist, attributing this to Hamr. We have not located the proposed lower
bound of 50. Hamr's separate target of at least 50 founders in Oberon is a
management target. Neither source supports dividing cumulative 1990–92
collections by a contemporaneous 50–200 interval as a measured removal
fraction. Candidate 2 instead reports model-based pre-event fractions. This
qualification does not rule out a substantial effect of removal; it keeps that
effect as a counterfactual question.

The no-wild-removals intervention must also suppress releases, captive offspring
and downstream transfers that depend on those removals. Retaining those fish in
insurance sites would invent conservation benefits. The comparison therefore
reports both natural-range occupancy in 2002 and any-site persistence in 2012.
Wild-site years beyond the historical window are conditional projections. The
counterfactual is mechanistic and conditional on the factual compatible set;
it is not an identified causal estimate or a verdict on the rescue decision.

## Checks completed

Lake Figure 6 was inspected in the original PDF and digitised from its native
image stencil. The five positive means imply about 172.97 capture equivalents
under the twelve-site interpretation; the declared reading band gives
168.17–177.77. These are derived equivalents, not recovered integer counts.
The score is explicitly tempered and profiled over accessibility and relative
catchability. Source hashes, pixel coordinates and unclassified error-bar
heights are retained. Reproduction uses:

```sh
pdfimages -f 8 -l 8 outputs/literature/lake_2001/h-lake-inverts-11_01.pdf outputs/age_structured_design_20260929/lake_figure6
uv run python scripts/prepare_age_review_20260929.py
```

The observation checks make no demographic calls. The proposal-support
fractions with R0(1-p)>1 are 7.628% and 67.721%, before neutral-allocation
rejection. The smaller fraction does **not** mean that all other draws cannot
breed or cannot persist temporarily.

One matched-exposure control has late abundance (1,1,1,1,0), and the other
(0.8,0.8,0.8,0.8,0.8), with identical early and February abundance. Their terminal
occupancy differs, but their aggregate late exposure and entire conditional
capture distribution are identical. Both observed-vector log scores are
-7.087782870601526. Their best balanced classification accuracy from this block
alone is 0.5. These are observation templates, not biologically qualified
histories. The linked demographic runner must establish whether comparable
histories are feasible under its restrictions.

The 120 oracle controls additionally compare constant late persistence against
loss before every late visit, with parameters known. At late/early abundance
0.02, February effort 2 and relative catchability 1, increasing total late
effort from 2.5 to 20 gives balanced accuracy 0.538 to 0.734. Those are
observation-block benchmarks, not fitted recovery rates or limits for the
complete evidence set. A failure of real-world discrimination would leave an
unresolved result; it would not predetermine extinction.

The final focused command passed **30 tests**:

```sh
uv run pytest -q tests/test_age_observation.py tests/test_age_demography.py tests/test_age_scenarios.py
```

The checks cover likelihood normalization, impossible positive counts, scale
cancellation and two-block parity; fractional tempered Lake scores; positive
synthetic Lake catches; and the existing age-kernel/scenario invariants. No
new scientific demographic histories or remote jobs ran. Unit-test fixtures
are reported separately from the execution budget.

A bounded independent methods check found the amended arithmetic and
counterfactual contract consistent. It identified an omitted generative rule
for synthetic Lake observations. Candidate 2 now specifies site/trip Poisson
counts, optional gamma quality variation, coarsening and digitisation error.
Synthetic late catches may be positive; the score supports them. Its two
editorial corrections—modeled source cohorts and separate figure/methods page
numbers—were also applied. Independent review is not empirical validation.

## Next executable tranche

Astra owns the linked-site runner, source-to-score map and full synthetic gate.
There is no further routine approval exchange to wait for. The gate must use
separate truth/inference sources and seeds, proper observation generators,
source-cluster uncertainty and predeclared classification criteria. It must
distinguish inadequate inference-bank coverage from weak observation
information. Historical search follows only for an adequately qualified design,
with a frozen source/configuration manifest and reconciled remote execution
receipt. No new search, demographic recovery run, commit, push or publication
is claimed by this amendment.
