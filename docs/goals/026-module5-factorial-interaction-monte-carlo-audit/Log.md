# Goal 026 Log

## Baseline And Authorization

- Barry authorized the factorial-interaction and Monte Carlo adequacy audit on
  2026-08-09.
- Baseline: clean synchronized `main` at
  `3bd828d8ca1c1386c65f37ff985468838880a9ad`.
- Existing raw production output only; no simulation rerun is authorized.
- Publish boundary: none. Leave Goal 026 unstaged and uncommitted.

## Prespecified Scientific Decisions

- Interaction is estimated from intervention-specific source means because
  stochastic seeds are paired only within baseline-counterfactual pairs.
- Primary aggregation weights the 15 observation-variant by calibration-seed
  contexts equally; equal-source weighting is a sensitivity analysis.
- Endpoint tolerances and the `25/50/75/100` prefix gate were frozen in
  `Goal.md` before remote raw-outcome access.
- Families remain separate, and the accepted three-endpoint bundle remains
  unchanged.

## Execution Evidence

- Added the focused analysis module, explicit CLI, and synthetic test file
  named in the Goal 026 contract.
- Synthetic tests cover known interaction values, unequal context/source
  weighting, independent intervention-stream Monte Carlo variance, prefix and
  batch construction, full-rerun classification failure, and targeted-
  extension classification failure.
- Focused tests: `5 passed`.
- Existing Module 5 production-summary/output-check/source-identity slice:
  `8 passed`.
- `deep-server-ts` preflight passed after applying the documented
  `$HOME/.local/bin` PATH correction for non-login SSH.
- Source matched-output size and SHA-256 matched the Goal 014 record before
  analysis.

## Final Remote Audit

- Run ID: `20260809T045756Z-goal026-m5-interaction-stability`.
- Scratch:
  `/data/codex/scratch/galaxias/module5_interaction_stability_20260809T045756Z-goal026-m5-interaction-stability`.
- Compact artifact:
  `/data/codex/artifacts/galaxias/module5_interaction_stability_20260809T045756Z-goal026-m5-interaction-stability`.
- Start/end: `2026-08-09T04:58:17Z` to `2026-08-09T04:58:32Z`.
- Final artifact size: 1.1 MB; scratch size including the isolated environment:
  282 MB.
- Output rows: QC 11; source effects 1,545; context effects 90; prefix/batch
  summaries 384; replication decisions 6.
- All remote compact artifact checksums passed.
- No `tmux` session was needed and no simulation was run.
- No raw matched output was pulled back.

## Scientific Result

- Both families show a less-than-additive persistence-probability interaction,
  a more-than-additive minimum-abundance interaction, and a near-additive or
  unresolved lake/refuge-share interaction.
- All family-level estimates, bounds, and interaction classifications pass the
  100-replicate adequacy criteria.
- Three source-classification surfaces exceed the prespecified 5 percentage-
  point 75-to-100 drift threshold. The final recommendation is therefore a
  targeted 250-replicate extension only if source-distribution statements are
  intended for publication; no evidence supports jumping directly to 1,000.
- Eleven 32-bit seed collisions occurred across 279,500 keys; none reused a
  seed across intervention arms within the same source.

## Material Repair And Deviations

- The first remote development run used an overly coarse decision branch: it
  labelled a source-proportion-only failure as a full rerun while its replicate
  estimate still said 100. The branch was corrected so source-only drift maps
  to `targeted_extension` and an inadequate result recommends at least 250.
- A second development artifact used the stale metadata key
  `factorial_seed_key_count` after collision auditing had been widened to all
  279,500 rows. The final run uses the accurate key `all_seed_key_count`.
- Both earlier run-specific artifacts were left untouched as development
  evidence. The final authoritative run is the one recorded above.
- One checksum check was initially invoked outside the artifact directory and
  therefore could not resolve relative manifest paths. It passed immediately
  when rerun from the recorded artifact directory.

## Boundary Status

- Goal 014 artifacts were not modified.
- No new simulation, manuscript wording, final causal claim, polished figure,
  staging, commit, push, PR, reset, rebase, amend, or destructive cleanup
  occurred.

## Final Validation And Review

- Compact structured-output check passed: metadata, six expected row counts,
  QC flags, source-output boundary, action vocabulary, and 250-replicate
  targeted-extension values all matched the contract.
- `make fast-check` passed: portability inspected 331 Git-managed files,
  compilation passed, and pytest reported `99 passed, 5 deselected`.
- Direct compilation including the new untracked files passed.
- Final trailing-whitespace scan returned no matches.
- Language-marker hits were boundary statements or explicit non-claim text.
- Final remote checksum verification passed from the authoritative artifact
  directory.
- `git diff --check` passed for tracked changes; the new-file whitespace and
  compilation checks covered the intentionally untracked Goal 026 surface.
- Final status is the expected clean synchronized `main` baseline plus only
  the untracked Goal 026 packet, module, CLI, test, report, and compact-output
  directory.
- Two native implementation delegates produced no file change within bounded
  polling intervals and were stopped; root completed the minimal implementation.
  A later material-only independent auditor likewise did not return after a
  nudge and repeated polling and was stopped. Root's focused scientific review
  reconciled the formula, weighting, Monte Carlo variance, row counts, report
  values, and action mapping with no further material defect found.
