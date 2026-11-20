# Independent demographic-repair audit

23 September 2026. One bounded, read-only methods audit was performed by the
`density_regulation_audit` scientific specialist after implementation and
qualification. This record summarizes its returned findings; the auditor did
not edit files or run a new simulation programme. This is independent code and
mathematical scrutiny, not independent empirical validation.

**Verdict:** proceed to Fable's substantive review after binding the closure
receipt. No further kernel correction was identified in the amended candidate.

## Checks and findings

- Recruitment-only Beverton–Holt regulation and the declared annual stage
  timing match the protocol. New recruits enter J after old-J maturation and
  cannot reproduce before update t+2.
- Existing-adult expected retention equals .65 times pre-breeding adults in
  all 2,304 stochastic rows. Recruitment limits bound the asymptotic Poisson
  mean, not realized recruitment; exceeding that mean is legitimate.
- Scenarios require explicit limits. The retired fecundity and capacity
  parameters do not enter the repaired adapter. Event streams use positions
  0–7 and 12–17, leaving the old density-thinning positions 8–11 unused.
- Source and output hashes verify for the amended qualification. Founder,
  neutral-reference and stochastic artifacts are byte-identical across the
  two attempts. Differences concern the numerical boundary correction and
  associated neutral-grid outputs/receipts.
- Factoring b outside the weight sum correctly classifies all 81 exact
  replacement-boundary cells as zero analytic equilibria. The retained
  99–101-step error is 1.854e-7; the 126–128-step error is 3.796e-10.
  No period-two candidate occurs in the prescribed grid.
- All 47 unresolved paths are exact-boundary cases. Eleven positive
  unguarded equilibria have A<2 and all their guarded paths approach zero.
  Other supercritical near-zero outcomes are guard-dependent establishment
  failures rather than algebra failures.

## Issues resolved before handoff

The audit requested inclusion of the 423 standalone one-step checks in each
attempt's execution accounting, and hashes/commands for the tests. The final
protocol and completion receipt distinguish 2,588 iterated paths from 846
one-step checks, for 3,434 deterministic executions under the corrected 3,600
deterministic-execution envelope. There were separately 384 stochastic
executions. The correction does not authorize additional runs. Focused tests
are reported separately; 27 demographic tests and the final 81-test combined
regression suite passed.

## Scientific qualifications retained

b=4 and the historical/insurance recruitment limits are diagnostic fixtures.
The reported stage fraction concerns next-season eligibility, not measured
gonadal maturity. Pooled breeding across compartments, the hard two-adult
threshold, site scales, normalized spawn quality, dual upsurge placement,
annual founder timing and the observation bridge still require biological
review. No search, history fit, restored equifinality or conservation claim
follows from these mechanical results.
