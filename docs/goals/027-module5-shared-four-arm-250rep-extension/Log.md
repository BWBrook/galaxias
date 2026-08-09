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

- Frozen implementation commit:
  `4e2e786381595a4dcb9ca11f04b40df1d5606f2a`.
- Pushed to `origin/main`; local and remote counts were `0 0` before remote
  execution.
- Local Git bundle:
  `/tmp/galaxias-4e2e786381595a4dcb9ca11f04b40df1d5606f2a-20260809T053041Z.bundle`.
- Bundle SHA-256:
  `653d6ace2a48f5b9aceaca692bcbfe8384caf25d8c8f48b73c7e44c9248850b1`.
- Remote detached checkout:
  `/data/codex/repos/galaxias-goal027-20260809T053041Z-goal027-m5-shared-smoke`.
- Remote checkout HEAD and bundle verification matched the frozen SHA; status
  was clean detached `HEAD`.

## Remote Smoke

- Alias: `deep-server-ts`; fallback not used.
- Run ID: `20260809T053041Z-goal027-m5-shared-smoke`.
- Session: `galaxias-m5-shared-smoke-20260809T053041Z`.
- Scratch:
  `/data/codex/scratch/galaxias/module5_factorial_extension_20260809T053041Z-goal027-m5-shared-smoke`.
- Artifact:
  `/data/codex/artifacts/galaxias/module5_factorial_extension_20260809T053041Z-goal027-m5-shared-smoke`.
- All 15 parameter artifacts verified before execution.
- Start/end: `2026-08-09T05:31:42Z` to `2026-08-09T05:32:00Z`;
  duration 18 seconds; 32 workers; both execution exit files were zero.
- Output: 7,725 rows from 2,575 source-replicate blocks and 10,300
  simulations.
- Raw smoke size: 12,563,707 bytes; SHA-256:
  `028376a853c0eab1bbe2a383a179eddd5b85499283e0b51f5bc918cd5b9282cc`.
- All 21 QC checks passed, including exact source counts and axes, one seed per
  block, baseline reuse, zero collisions, source identity, schema, provenance,
  and finite endpoints.
- Smoke artifact checksum verification passed. No smoke raw output was pulled
  back.

## Remote 250-Replicate Extension

- Run ID: `20260809T053300Z-goal027-m5-shared-250rep`.
- Execution session: `galaxias-m5-shared-250-20260809T053300Z`.
- Audit session: `galaxias-m5-shared-audit-20260809T053300Z`.
- Scratch:
  `/data/codex/scratch/galaxias/module5_factorial_extension_20260809T053300Z-goal027-m5-shared-250rep`.
- Artifact:
  `/data/codex/artifacts/galaxias/module5_factorial_extension_20260809T053300Z-goal027-m5-shared-250rep`.
- Start/end: `2026-08-09T05:33:31Z` to `2026-08-09T05:41:18Z`;
  duration 467 seconds; 32 workers; execution and tmux exit files were zero.
- Output: 386,250 stored contrasts from 128,750 source-replicate blocks and
  515,000 actual arm simulations.
- Seed audit: 128,750 distinct seeds, zero collisions.
- Raw size: 631,217,121 bytes; SHA-256:
  `3ea4ad0a05ad928628fc3cd780cb94a3f4517d07a1827b16a527ea9000ce20c5`.
- Full compact audit completed in 54 seconds with exit zero. All 21 QC checks
  passed.
- Remote artifact size: 604 MB. A fresh checksum verification passed all 23
  manifest entries.
- Compact output rows: QC 21; source effects 1,545; context effects 90;
  prefix/batch summaries 384; decisions 6; Goal 026 continuity checks 24.
- Only the seven compact audit files, totalling about 1.1 MB, were pulled back
  to `data/module5_factorial_250rep_extension/`.

## Scientific Decision

- All six family-endpoint combinations pass the family-level 250-replicate
  stability gate. Context-equal and source-equal practical classifications
  agree throughout.
- Both families retain less-than-additive persistence interaction,
  more-than-additive minimum-abundance interaction, and near-additive or
  unresolved lake/refuge interaction.
- Five combinations also pass source-class-proportion stability.
- Transient-perfect-storm lake/refuge interaction is the sole source-
  distribution exception: class proportions move 0.064 from 175 to 250, while
  the family estimate remains near additive and stable.
- That residual is threshold-sensitive: 83 of 250 source means lie within
  0.005 of the +/-0.01 class boundary. Do not make a stable categorical
  source-prevalence claim for this surface.
- Goal 027's 100-prefix estimates triggered zero Goal 026 continuity flags.
  Common seeding reduced 100-replicate interaction Monte Carlo half-widths by
  roughly 9% to 38% without changing a family-level conclusion.
- Decision: 250 replicates are sufficient for current family-level synthesis.
  Stop; do not run 500 or 1,000 replicates.

## Completion Validation

- Every pulled compact file matched the corresponding remote SHA-256.
- Structured compact-record validation passed: metadata, raw-output boundary,
  row counts, QC flags, decision counts, stop level, continuity flags, and the
  one source-distribution exception matched the recorded claims.
- All seven compact files are below 20 MB; no `matched_outcomes.csv` exists in
  the compact local directory.
- `git diff --check` and the final trailing-whitespace scan passed.
- Language-marker hits were explicit boundaries, stop rules, or internal
  scientific cautions rather than stronger claims.
- `make fast-check` was not rerun after remote completion because the only
  post-freeze local changes are the compact data, this log, and the review
  memo. The frozen executable source already passed `105 passed, 5
  deselected` before execution.

## Boundary Status

- No simulation, remote access, raw-output pull-back, intervention-contract
  edit, manuscript wording, or causal conclusion occurred during local
  implementation.
- Remote writes were confined to new run-specific source, scratch, and
  artifact paths. Prior artifacts were not mutated.
- No raw Goal 027 matched output exists locally or in Git.
- No manuscript prose, polished display artefact, final causal claim,
  posterior update, pressure-semantic change, 500/1,000-replicate escalation,
  force-push, amend, rebase, reset, or destructive cleanup occurred.
