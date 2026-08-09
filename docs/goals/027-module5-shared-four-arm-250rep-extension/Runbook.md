# Goal 027 Runbook

## Baseline

Expected starting state is clean synchronized `main` at
`825bdb75cb066d92169724fdbec5efc075e23755`.

Record:

```bash
pwd
git branch --show-current
git rev-parse HEAD
git status --short --branch
git rev-list --left-right --count HEAD...origin/main
```

## Local Execution-Source Gate

Run:

```bash
uv run pytest tests/test_module5_factorial_extension.py -q
uv run pytest \
  tests/test_module5_interaction_stability.py \
  tests/test_module5_production_rehearsal.py \
  tests/test_module5_output_checks.py \
  tests/test_module5_source_identity.py -q
uv run python scripts/run_module5_factorial_extension.py --help
uv run python scripts/audit_module5_factorial_extension.py --help
uv run python scripts/validate_module5_counterfactual_contract.py
make fast-check
git diff --check
```

Stage only the Goal 027 packet, implementation, scripts, focused test, and any
explicitly authorized shared-helper change. Commit and push the frozen source,
then verify `HEAD...origin/main` is `0 0`.

## Remote Source And Preflight

Use `deep-server-ts`. Verify hostname, user, `/data` capacity, `git`, `uv`,
Python, and `tmux`. Verify local `HEAD` is the frozen execution SHA, create a
Git bundle from `HEAD`, checksum it locally and remotely, clone it into a new
run-specific checkout, detach at the frozen SHA, and verify a clean status.

Use unique paths under:

```text
/data/codex/repos/galaxias-goal027-<RUN_ID>
/data/codex/scratch/galaxias/module5_factorial_extension_<RUN_ID>
/data/codex/artifacts/galaxias/module5_factorial_extension_<RUN_ID>
```

Run plan-only preflight with remote artifact preference. It must verify all 15
parameter artifacts and report 515 sources, 15 contexts, and the expected row
and simulation counts.

## Smoke Gate

Use a new smoke run ID and `tmux` session, all 515 sources, five replicates,
and 32 workers. Expected stored rows: `7,725`; expected simulations: `10,300`.

The smoke must pass:

- exact schema and source/intervention/replicate coverage;
- exactly three removal rows per source-replicate block;
- one identical 63-bit seed across those rows;
- identical stored baseline endpoint values across those rows;
- zero source-replicate seed collisions;
- finite endpoint values and correct provenance;
- artifact inventory and checksum verification.

If any smoke check fails, stop. Do not start the 250-replicate run.

## 250-Replicate Gate

Use a new run ID and `tmux` session, 250 replicates, 32 workers, and the same
frozen checkout. Expected stored rows: `386,250`; expected simulations:
`515,000`.

After execution:

1. copy durable run outputs into the new run-specific artifact directory;
2. run the full shared-block audit with prefixes `100,175,250` and five
   50-replicate batches;
3. record raw size and SHA-256, inspection facts, elapsed time, worker count,
   source counts, and decision-table results;
4. generate and verify an artifact checksum manifest without self-including
   the manifest;
5. retain raw matched outcomes remotely and pull back only compact audit
   outputs.

Stop at 250 even if the stability gate fails.

## Completion Gate

Write the compact report and update this goal log. Check structured output row
counts and all recorded claims against the compact files. Run:

```bash
git diff --check
rg -n "[ \t]+$" \
  docs/goals/027-module5-shared-four-arm-250rep-extension \
  docs/module5_shared_four_arm_250rep_extension.md \
  data/module5_factorial_250rep_extension
```

Review markers for posterior, attributable fraction, proof of synergy,
manuscript, final causal, publication-ready, 500, and 1000. Boundary and
stop-rule statements are allowed; stronger claims or silent escalation are
not.

Stage only the compact completion record and any material repair explicitly
justified by the review. Commit, push, and verify clean synchronized `main`.
