# Goal 021 Runbook

## Baseline

```bash
pwd
git branch --show-current
git rev-parse HEAD
git status --short --branch
```

Stop if the baseline is not clean `main` at the delegated SHA.

## Focused Validation

```bash
uv run pytest \
  tests/test_module5_counterfactual_contract.py \
  tests/test_module5_production_rehearsal.py \
  tests/test_module5_production_summary.py \
  tests/test_module5_runner_prototype.py \
  tests/test_module5_real_proposal_dry_run.py -q
uv run python scripts/validate_module5_counterfactual_contract.py
make fast-check
git diff --check
```

Also parse the compact summaries and verify:

- schema rows: 50;
- `detection_summary_*` absent from the active schema;
- partition summary rows: 65;
- source/intervention summary rows: 13,975;
- direction summary rows: 65;
- summary metadata lists five endpoints and matching row counts;
- Goal 018-020 accepted endpoint-bundle and packet tables are byte-for-byte
  unchanged from the delegated baseline.

## Stop Conditions

Stop and report rather than:

- reading or mutating remote production artifacts;
- rerunning production;
- changing the accepted endpoint bundle;
- rewriting Goal 001-020 packets or frozen execution reports;
- consolidating inspectors or renaming rehearsal files/APIs;
- adding compatibility branches for old fields/status;
- staging, committing, or pushing.

After the core checks, perform one focused review and one material repair pass
only if needed. Further polish is out of scope.

## Report

Report the final branch, HEAD, status, exact changed paths, semantic decisions,
compact-summary row counts, validation evidence, protected historical evidence,
deviations, and residual risks. Send a wake-up to the Galaxias orchestrator on
completion or blockage.
