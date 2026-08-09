# Goal 026 Runbook

## Baseline

Record:

```bash
pwd
git branch --show-current
git rev-parse HEAD
git status --short --branch
git rev-list --left-right --count HEAD...origin/main
```

Expected baseline is clean synchronized `main` at
`3bd828d8ca1c1386c65f37ff985468838880a9ad` before this packet.

## Local Implementation Gate

Run:

```bash
uv run pytest tests/test_module5_interaction_stability.py -q
uv run pytest \
  tests/test_module5_production_summary.py \
  tests/test_module5_output_checks.py \
  tests/test_module5_source_identity.py -q
uv run python scripts/audit_module5_interaction_stability.py --help
```

## Remote Gate

Use `deep-server-ts`. Before creating a workspace, verify hostname, available
`/data` space, Python/`uv`, and the immutable Goal 014 artifact checksum.

Source raw output:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/matched_outcomes.csv
```

Expected SHA-256:

```text
ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727
```

Create a dated run-specific directory under:

```text
/data/codex/scratch/galaxias/module5_interaction_stability_<RUN_ID>
```

Write compact remote outputs under a new Goal 026 artifact path. Do not write
inside the Goal 014 artifact. No `tmux` session is required unless the compact
audit proves unexpectedly long-running.

## Required Result Checks

- both factorial families have the same proposal-source set across all three
  removal interventions;
- every source/intervention unit has replicate IDs `0..99` exactly once;
- baseline and intervention seeds match inside each pair;
- cross-intervention streams are not described as paired;
- all required endpoints are finite;
- prefixes and disjoint batches have their expected row counts;
- all compact output files are below 20 MB;
- raw `matched_outcomes.csv` is absent locally;
- audit metadata records source path, source hash, source execution SHA,
  analysis command, endpoint definitions, tolerances, weighting, and seed
  collision facts.

## Final Local Gates

Run once after pulling compact outputs:

```bash
make fast-check
git diff --check
rg -n "[ \t]+$" \
  docs/goals/026-module5-factorial-interaction-monte-carlo-audit \
  docs/module5_interaction_stability_audit.md \
  data/module5_interaction_stability \
  src/galaxias_model/module5_interaction_stability.py \
  scripts/audit_module5_interaction_stability.py \
  tests/test_module5_interaction_stability.py
```

Review language markers for posterior, attributable-fraction, final causal,
synergy-proof, manuscript, and publication-ready claims. Boundary statements
are allowed; scientific overclaim is not.

Leave all Goal 026 changes unstaged and uncommitted.
