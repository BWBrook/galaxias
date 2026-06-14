# Goal: Module 5 Deep-Server Remote Smoke And Production Preflight

## Objective

Run a bounded 65-row Module 5 remote smoke on `deep-server` and produce a
decision-ready preflight report for the later production execution goal.

This goal authorizes only remote access/setup needed for the smoke, a
disposable remote source mirror, transfer or verification of the one required
ignored raw Module 4 artifact, a durable `tmux`-supervised 65-row smoke, disk
inspection of that smoke, and a compact tracked preflight report.

It does not authorize the 279,500-row production run, production attribution
claims, code/test/CSV contract edits, staging, commit, push, PR, publication,
or manuscript claims.

## Why This Matters

Goal 009 specified the recommended production run shape: all 750 accepted
proposal rows, family-specific summaries, 100 replicates, `deep-server` as the
remote execution target, and a durable `tmux` session. Before authorizing that
production run, we need proof that the current accepted Goal 005-009 source
surface can be mirrored to `deep-server`, that the required raw Module 4 smoke
artifact is available there with the expected hash, and that the current
Module 5 dry-run runner and disk inspector work on the remote host.

The smoke is deliberately small:

- proposal source: the five Goal 006 `baseline_current` / `20260410`
  `family_winners` proposal rows;
- intervention matrix: all 13 current Module 5 intervention rows;
- replicates: 5 per intervention row;
- expected matched-outcome rows: 65.

This is a remote execution proof and preflight, not production attribution.

## Scope

In scope:

- Create `docs/module5_remote_smoke_preflight.md`.
- Update this goal `Log.md`.
- Run local read-only source/artifact checks needed before remote transfer.
- Probe `deep-server` access using `deep-server-ts` first and `utas-ubuntu` as
  a fallback if needed.
- Create a disposable remote source mirror under `/data/codex/repos`.
- Use `rsync` to transfer the current local working-tree state to that remote
  mirror, preserving `.git` so remote provenance can record the base commit
  and dirty state.
- Exclude heavy/generated/cache paths from the source mirror except for the
  one required smoke input artifact.
- Transfer or verify the required ignored raw artifact:
  `outputs/remote/module4_observation_sensitivity_20260522T101942Z/baseline_current_seed20260410/parameter_values.csv.gz`.
- Verify its SHA-256:
  `49e080a23dcaca2f29874c0e3825bd806406f494b2db046307a84a74e8673c4c`.
- Create run-specific remote scratch and artifact directories under
  `/data/codex/scratch/galaxias/` and `/data/codex/artifacts/galaxias/`.
- Create and run a named remote `tmux` session for the 65-row smoke.
- Run the existing smoke runner:
  `scripts/run_module5_real_proposal_dry_run.py` with 5 replicates and an
  explicit remote output directory.
- Run the existing disk inspector:
  `scripts/inspect_module5_real_proposal_dry_run.py` with
  `--expected-replicates 5`.
- Verify remote smoke facts from disk:
  - 65 matched-outcome rows;
  - 13 intervention IDs;
  - 5 proposal IDs;
  - 5 stochastic replicates per intervention row;
  - replicate IDs exactly `0..4`;
  - zero baseline/intervention stochastic seed mismatches;
  - inspection `all_checks_passed` true;
  - provenance `production_attribution` false.
- Record remote host, paths, source state, environment, commands, durations,
  output paths, hashes, row counts, and stop/next recommendations in the
  preflight report and Log.

Out of scope:

- No production-sized run.
- No 25-replicate rehearsal unless a future goal explicitly authorizes it.
- No 279,500-row execution.
- No code, tests, Makefile, runner, inspector, proposal resolver, tracked CSV,
  or data-contract edits.
- No change to pressure-removal semantics or new scenario hooks.
- No local generated-output promotion.
- No raw matched-outcome pull-back into the local repo.
- No tracked generated artifacts other than the compact preflight report and
  goal log.
- No staging, commit, push, PR, or publication.
- No final causal, production attribution, manuscript-level, or
  production-ready claim language.

## Source-State Policy

The local action repo is intentionally dirty and uncommitted because accepted
Goals 005-009 have not been published. Do not use a plain remote GitHub clone
as the smoke source unless it is first proven to contain the accepted
Goal 005-009 surface.

Default source-transfer policy:

- create a disposable remote mirror such as
  `/data/codex/repos/galaxias-goal010-remote-smoke-<UTC_RUN_ID>`;
- `rsync` the local working tree to the remote mirror;
- include `.git` so remote `git rev-parse` and `git status` work;
- exclude `.venv/`, `.pytest_cache/`, `__pycache__/`, and `outputs/`;
- separately copy the one required ignored smoke artifact into its expected
  repo-relative `outputs/remote/.../parameter_values.csv.gz` path;
- record local and remote `git rev-parse HEAD` and
  `git status --short --branch`;
- record that the remote source is a disposable mirror of an accepted dirty
  local action-repo surface, not canonical published history.

If source mirroring fails, stop and wake Galaxias. Do not fall back to
production, stale `origin/main`, or ad hoc source editing on the remote host.

## Required Remote Layout

Use a UTC run ID, for example:

```text
20260613T000000Z-goal010-m5-remote-smoke
```

Recommended paths:

```text
REMOTE_REPO=/data/codex/repos/galaxias-goal010-remote-smoke-<UTC_RUN_ID>
REMOTE_SCRATCH=/data/codex/scratch/galaxias/module5_remote_smoke_<UTC_RUN_ID>
REMOTE_ARTIFACT=/data/codex/artifacts/galaxias/module5_remote_smoke_<UTC_RUN_ID>
SESSION=galaxias-m5-smoke-<UTC_RUN_STAMP>
```

The smoke output should live only on `deep-server`, under the remote scratch
and/or artifact path. Do not copy raw matched outcomes into the local repo.

## Required Preflight Report

Create `docs/module5_remote_smoke_preflight.md` with:

- current state and non-claims;
- local action-repo starting state;
- remote target, alias used, host facts, and environment facts;
- remote source-mirror policy and actual paths;
- smoke input artifact path, size, and SHA-256;
- exact smoke shape and expected row count;
- exact commands run or command script path;
- `tmux` session name and completion evidence;
- remote output paths;
- disk-inspection evidence;
- row-count, replicate-coverage, seed-pairing, proposal, and intervention
  summaries;
- generated remote artifact inventory and checksums;
- wall-time and rough storage footprint;
- deviations, blockers, or warnings;
- recommendation for the next goal.

The report should be compact but concrete enough for Galaxias to decide
whether production execution is ready to be authorized.

## Required Validation

Run and log local checks:

- `git status --short --branch`
- `git diff --check`
- a direct trailing-whitespace scan over:
  - `docs/goals/010-module5-deep-server-remote-smoke-preflight/`
  - `docs/module5_remote_smoke_preflight.md`
- a marker scan over Goal 010 files for:
  - `production attribution`
  - `production-ready`
  - `deep-server`
  - `tmux`
  - `outputs/`
  - `manuscript`
  - `commit`
  - `push`

Run and log remote checks:

- access and host identity;
- `df -h /data`;
- `command -v uv` and `uv --version`;
- `python3 --version`;
- remote source `git rev-parse HEAD`;
- remote source `git status --short --branch`;
- SHA-256 check for the required smoke parameter-values artifact;
- remote smoke command exit status;
- remote inspection command exit status;
- direct disk check of row counts, proposal counts, intervention counts,
  replicate coverage, seed-pairing mismatches, and provenance boundary flag.

Do not run tests, `make` targets, broad validation suites, production
execution, or non-smoke simulations for this goal unless Galaxias explicitly
authorizes a review iteration.

## Stop Points

Stop and wake Galaxias before:

- using any compute target other than `deep-server` via `deep-server-ts` or
  `utas-ubuntu`;
- using a stale remote checkout instead of the current accepted local dirty
  source surface;
- continuing if source mirror status cannot be recorded or is unexpectedly
  different;
- continuing if the required smoke parameter-values artifact is missing or its
  hash differs;
- editing code, tests, Makefile, scripts, runner, inspector, proposal resolver,
  tracked CSVs, or data contracts;
- modifying pressure-removal semantics or adding scenario hooks;
- running a 25-replicate rehearsal or 279,500-row production execution;
- copying raw matched outcomes back into the local repo;
- staging, committing, pushing, publishing, or opening a PR;
- making final causal, production attribution, production-ready, or
  manuscript-level claims.

## Done When

- The remote smoke either passes with evidence or the blocker is precisely
  reported.
- `docs/module5_remote_smoke_preflight.md` records the remote evidence.
- The goal log records starting state, files read, files changed, remote
  commands, validation checks, final status, generated remote paths, and
  risks/questions.
- The action repo remains uncommitted and unstaged.
- Local tracked changes are limited to the Goal 010 packet, the preflight
  report, and `Log.md`.
- Remote generated outputs remain under `/data/codex/scratch` and
  `/data/codex/artifacts`.
- No full production execution, local raw-output pull-back, staging, commit,
  push, PR, publication, or manuscript/production-attribution claim occurs.
- `pedder` sends a short wake-up to the Galaxias orchestrator thread on
  completion or blockage.
