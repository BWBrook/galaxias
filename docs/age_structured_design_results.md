# Age-structured design and qualification, 27 September 2026

The age/sex candidate and review protocol are complete for the current reporting
horizon. Read `docs/age_structured_protocol.md` for the scientific specification
and remaining pre-dispatch work. No renewed calibration or historical comparison
has run. The 32-cell, 1,597,248-site-history programme is a proposal for review,
not an execution receipt or permission to restart production.

## What is implemented

- December cohort states with six/eight-year truncation scenarios, sex-specific
  demographic stochasticity and actual male/female breeding participation.
- Beverton–Holt recruitment regulation, analytic neutral abundance-to-limit
  mapping, mean-one recruitment variability and dated extraction/addition events.
- Birth-year and following-year nursery exposure; a juvenile climbing pathway;
  habitat-dependent refuge recruitment; common restriction/forcing translation.
- A common-calendar materializer and observation primitives for accessible
  abundance, positive records and a conditional early/late capture contrast.
- Evidence registers that distinguish direct records, conflicting totals and
  declared reconstructions. Oberon offspring are not counted as wild removals;
  the four January 1996 fish and three May 1997 survivors remain linked.

These components do not yet constitute the full coupled historical/insurance
runner or observation scorer. They must not be passed to an old search driver
that assumes independent sites, adult-only founder additions or old hard filters.

## Verification and execution accounting

The final focused suite passed **26 tests**. `make fast-check` passed portability,
compile and **267 tests**, with five slow integration tests deselected; this was
before the final diagnostics-only renaming. All 26 affected tests passed again
after the rename. The five unrelated slow tests were not run. New file text and
compilation were also checked explicitly because the repository portability
script only inventories Git-managed files.

`scripts/qualify_age_demography.py` ran two preserved synthetic qualifications:

| Check | Each attempt | Result |
|---|---:|---|
| Neutral fixed-point map | 2 lifespans × 3 scales | Maximum absolute discrepancy 9.095e-13 |
| Stochastic histories | 24 distinct paths, 20 updates each | Nonnegative integer states |
| Replay | Same 24 paths serial and with two workers | Exact states and recorded diagnostics |
| Frozen calendar | Three shared no-op observation checkpoints | Same hashed calendar in both executions |

Each attempt used 48 stochastic path executions plus six deterministic map
executions. Attempt 2 followed the diagnostic field rename; its stored histories
are bit-for-bit identical to attempt 1. Combined local qualification is **108
path/map executions**, plus **three single-update audit probes**, within the
declared 128-execution allowance. Unit-test fixtures are recorded separately
from these path counts; no tests are called scientific comparison histories.
No heavy compute or remote job was launched.

The source snapshots, raw receipts and serial/parallel traces remain under
`outputs/age_structured_design_20260927/attempt_1/` and `attempt_2/`.
Compact receipts and source/output hashes are in
`data/age_structured_design_20260927/`. The original common model, mate guard,
two-stage recruitment core and its scenario adapter retain their starting SHA256
values. The current working tree and old archives remain uncommitted and intact.

One independent methods audit found and resolved the Q-placement defect and
mixed-event provenance issue before acceptance. Its checkpoint sensitivity
finding is handled by an explicit calendar contract, not dismissed as harmless.
See `docs/age_structured_design_audit.md` for the diagnostic evidence and limits.

## Scientific interpretation and review handoff

This package establishes a mechanically coherent candidate. It does not yet
show which mechanism best explains Pedder's history or whether anything persisted
after 1996. The finite-lifespan implication is conditional: under the specified
six-year cohort calendar, survival during 2002 requires a 1996-or-later birth;
the eight-year scenario can differ. The reported maximum age alone does not
make either calendar empirically correct.

The proposed conditional capture contrast removes a common catchability factor
and abundance scale, but retains assumptions about effort, accessible ages,
relative catchability and capture independence. Insurance positives and linked
transfers constrain establishment without the earlier double-used viability
screen. Coarsening the reported catches leaves substantial information unused;
Fable is asked to critique that choice before the observation implementation.

Fable's next response should address the scientific contract as a package,
particularly the removal reconstruction, shared-demography/site-scale supports
and observation coarsening. After that review, the remaining concrete work is
the linked runner, finalized source-to-score map, Lake figure digitisation,
synthetic observation/recovery controls and executable freeze. No new Barry
decision is required for this review handoff.
