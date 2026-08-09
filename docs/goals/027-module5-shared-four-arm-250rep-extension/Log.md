# Goal 027 Log

## Baseline And Authorization

- Barry authorized Goal 027 on 2026-08-09 after accepting the Goal 026
  recommendation to test a true shared four-arm block and stop at 250 before
  considering any larger replication level.
- Baseline: clean synchronized `main` at
  `825bdb75cb066d92169724fdbec5efc075e23755`.
- Commits and pushes are authorized for the validated frozen execution source
  and final compact completion record. Raw matched outcomes remain remote.

## Prespecified Decisions

- Families: all 265 accepted `persistent_joint_cause` sources and all 250
  accepted `transient_perfect_storm` sources.
- One non-negative 63-bit SHA-256-derived seed per proposal-source and
  replicate, shared
  across status quo and all three pressure-removal arms.
- One status-quo simulation per source-replicate; three stored contrasts.
- Interaction calculated at replicate level so its Monte Carlo variance
  retains shared-block covariance.
- Primary context-equal weighting and source-equal sensitivity weighting.
- Stability prefixes `100`, `175`, and `250`; disjoint 50-replicate batches;
  Goal 026 endpoint tolerances.
- Run escalation stops at 250 under all results.

## Execution Evidence

- Added a separate shared-four-arm execution module and CLI. The accepted
  source selection resolves 515 sources across 15 contexts and verifies the
  same 15 parameter artifacts used by the accepted Module 5 execution path.
- Added a separate covariance-aware audit module and CLI. It checks exact
  shared-block coverage, seed identity, baseline reuse, source identity,
  schema, matched-pair IDs, provenance, and finite endpoints before any
  stability calculation.
- The full 250-replicate plan reports 128,750 source-replicate blocks, 515,000
  simulations, 386,250 stored contrasts, 198,750 persistent-joint-cause rows,
  and 187,500 transient-perfect-storm rows.
- Synthetic tests prove one status-quo plus three intervention calls with one
  seed, exact pressure overrides, deterministic 63-bit seeds, direct
  replicate-level interaction variance, shared-block QC failures, and the
  250-replicate decision vocabulary.
- Focused Goal 027 test file: `6 passed`.
- Required focused Module 5 slice after review: `22 passed`.
- Module 5 counterfactual contract validator: passed.
- CLI help gates and local 250-replicate plan-only preflight: passed.
- Final pre-freeze `make fast-check`: portability passed for 340 Git-managed
  files, compilation passed, and pytest reported `105 passed, 5 deselected`.
- `git diff --check` and trailing-whitespace checks passed.

## Focused Review And Repair

- Independent methods review confirmed the estimand, context-equal weighting,
  direct covariance-aware interaction variance, `100/175/250` gate, and firm
  stop at 250.
- The review corrected the terminology from exact common random numbers to a
  common starting seed: state-dependent draws may consume the stream
  differently after trajectories diverge.
- The implementation uses a portable non-negative 63-bit seed rather than an
  oversized decimal CSV integer, with zero observed collisions required.
- One material repair pass made provenance use the full Git SHA, required the
  audit to match raw hash, execution SHA, and run ID, and required exactly 24
  rows in the non-gating Goal 026 continuity comparison.
- A requested post-implementation code-only delegate review did not return
  material evidence within bounded waits and was stopped. Root's focused
  review and the complete validation gates found no further material defect.

## Frozen Execution Source

Pending commit and push.

## Boundary Status

- No simulation, remote access, raw-output pull-back, intervention-contract
  edit, manuscript wording, or causal conclusion occurred during local
  implementation.
