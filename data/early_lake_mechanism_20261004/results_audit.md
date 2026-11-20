# Independent final audit: early-Lake production gate

**PASS — Stop without historical scoring under the frozen procedure.**

The audit read only the frozen synthetic production archives and analysis outputs. It did not run demographic histories or load the historical Lake observations.

## Evidence

- 6,144 source rows and 49,152 ordered feature/history rows were complete and hash-bound.
- Status counts: `{'valid': 37992, 'algebraically_infeasible': 11160}`; all valid histories had 25 annual advances and all retained algebraic failures had zero.
- All 32 prescribed analysis groups and 16 primary age-six groups were independently reconstructed.
- R `qbeta` independently reproduced 1536 exact Clopper–Pearson intervals.
- The scalar Lake score replayed 32 deterministic query vectors across 96 bank variants; maximum absolute score difference was 5.51e-14.
- Reconstructed decision: `STOP_EARLY_RECOVERY_UNASSESSED`; the raw, non-qualifying directed-pair intersection was `['R_J->R_H', 'R_T->R_H']`.
- Primary failure counts: `{'bank_half_instability': 16, 'coverage_precision_unassessed': 13}`; age-eight sensitivity failure counts: `{'bank_half_instability': 16, 'coverage_precision_unassessed': 13}`.

## Interpretation

The synthetic result is unassessed because prespecified stability or coverage checks failed. The raw directed-pair intersection cannot qualify a contrast. This does not establish intrinsic non-identifiability, equifinality, or any historical mechanism probability.

## Residual risk

The test population remains the declared conditional engineering distribution. Under this STOP there is no permitted historical comparison, and the raw pair intersection must not be reused as evidence. A different historical analysis would require a separately approved design.
