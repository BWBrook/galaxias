# Common-model preflight

The signed candidate-2 protocol is frozen at SHA256
`c165e25bfa223cbb79ba00fce75f099c13979746b2d516ae06e93af5243879d8`.
The common-model implementation is separate from the unchanged legacy kernel.
The independent scientific code audit found no remaining implementation blocker.

## Verified implementation evidence

- Local `make check`: 177 standard and five slow tests passed (182 total), with
  compilation and portability checks. The added files also passed direct checks.
- Target runtime: original Linux Python 3.14.5, NumPy 2.4.6 and pandas 2.3.3.
  All 39 focused kernel, runner and detection tests passed.
- Serial versus parallel: all 24 configuration/restriction cells, two histories
  per cell; 48 distinct histories executed twice, with exact row and float
  equality. Demographic and environmental streams are separately bound.
- Complete target smoke: 288 proposed sources, 287 viable; 574 search, 432
  refinement, 344 validation, 84 overshoot-counterfactual and 252 paired-switch
  histories (1,686 total). The viability failure received no stochastic draws.
- Source/output hashes, parent-archive bindings, disjoint search/refinement/
  validation streams and reused paired seeds were independently checked after
  retrieval. The final analysis completed, including the 2,592-cell numerical
  compatibility grid. No smoke source was labelled a qualified witness, as
  required by its deliberately insufficient Monte Carlo sample size.

These checks establish execution and reproducibility, not biological adequacy.
The source bundle and qualification receipts live in `data/common_model/`.
Full smoke artefacts remain outside Git under
`outputs/remote/common_model_20260918/qualification/` and on deep-server at
`/data/codex/scratch/galaxias/common_model_20260918/qualification/`.

## Completed replay gate

All 712,000 legacy histories reconciled exactly across 61 numeric diagnostics;
counts, flags, seeds and identities also matched. The fixed-cohort analysis and
its output hashes were verified at closure. See `docs/detection_replay_results.md`
and `data/common_model/detection_replay_completion.json` for evidence and limits.

The finite production wrapper requires a dispatch receipt binding these completed
checks and the pre-run Correspondence post. It uses eight workers, replacing the
replay allocation. The maximum scientific/replay count is 7,071,040; prescribed
implementation checks remain within the 7.1-million ceiling. Earlier uninstrumented
local unit checks are bounded conservatively in the execution-budget receipt rather
than presented as an exact count. Live production status is recorded in the handoff
and its separate launch/execution receipts.
