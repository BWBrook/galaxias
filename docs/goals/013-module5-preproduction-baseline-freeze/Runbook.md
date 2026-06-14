# Runbook

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short=12 HEAD
git status --short --branch
git fetch --prune origin
git rev-list --left-right --count HEAD...origin/main
```

Expected before committing:

```text
0 0
```

Stop if the count differs.

## Validation Commands

Focused Module 5 validation:

```bash
uv run pytest tests/test_module5_production_rehearsal.py tests/test_module5_source_identity.py tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q
```

Contract validation:

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
```

Plan-only Goal 012 rehearsal preflight outside the repo:

```bash
TMPDIR_GOAL013="$(mktemp -d /tmp/galaxias-goal013-plan.XXXXXX)"
uv run python scripts/run_module5_25rep_rehearsal.py \
  --plan-only \
  --output-dir "$TMPDIR_GOAL013" \
  --run-id goal013-plan-only
python3 - <<'PY' "$TMPDIR_GOAL013"
import csv
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
plan = json.loads((root / "rehearsal_plan.json").read_text(encoding="utf-8"))
artifacts = list(csv.DictReader((root / "artifact_verification.csv").open(newline="", encoding="utf-8")))
print(f"expected_row_count={plan['expected_row_count']}")
print(f"source_intervention_unit_count={plan['source_intervention_unit_count']}")
print(f"distinct_proposal_source_key_count={plan['distinct_proposal_source_key_count']}")
print(f"source_context_count={plan['source_context_count']}")
print(f"artifact_verification_rows={len(artifacts)}")
print(f"all_artifacts_verified={all(row['verified'].lower() == 'true' for row in artifacts)}")
PY
```

Expected output facts:

```text
expected_row_count=69875
source_intervention_unit_count=2795
distinct_proposal_source_key_count=780
source_context_count=15
artifact_verification_rows=15
all_artifacts_verified=True
```

Dry-run and full fast gate:

```bash
make module5-dry-run
make module5-dry-run-inspect
make fast-check
git diff --check
```

Trailing-whitespace scan:

```bash
rg -n "[ \t]+$" \
  docs/goals/005-module5-dry-run-production-spec \
  docs/goals/006-module5-real-proposal-dry-run \
  docs/goals/007-module5-intervention-matrix-review \
  docs/goals/008-module5-production-matrix-contract-revision \
  docs/goals/009-module5-production-run-spec \
  docs/goals/010-module5-deep-server-remote-smoke-preflight \
  docs/goals/011-module5-source-context-identity \
  docs/goals/012-module5-25rep-production-rehearsal \
  docs/goals/013-module5-preproduction-baseline-freeze \
  docs/module5_dry_run_production_spec.md \
  docs/module5_intervention_matrix_review.md \
  docs/module5_production_matrix_contract.md \
  docs/module5_production_run_spec.md \
  docs/module5_remote_smoke_preflight.md \
  docs/module5_source_identity_contract.md \
  docs/module5_25rep_rehearsal_report.md \
  scripts/validate_module5_counterfactual_contract.py \
  scripts/run_module5_real_proposal_dry_run.py \
  scripts/inspect_module5_real_proposal_dry_run.py \
  scripts/run_module5_25rep_rehearsal.py \
  scripts/inspect_module5_25rep_rehearsal.py \
  src/galaxias_model/module5_counterfactual.py \
  src/galaxias_model/module5_dry_run_inspect.py \
  src/galaxias_model/module5_proposals.py \
  src/galaxias_model/module5_rehearsal.py \
  tests/test_module5_counterfactual_contract.py \
  tests/test_module5_real_proposal_dry_run.py \
  tests/test_module5_dry_run_inspection.py \
  tests/test_module5_source_identity.py \
  tests/test_module5_production_rehearsal.py
```

No matches are expected. Remember `rg` exits 1 when there are no matches; treat
that as pass after confirming no output.

Marker scan:

```bash
rg -n "production attribution|production-ready|deep-server|tmux|outputs/|manuscript|commit|push|production run" \
  docs/goals/005-module5-dry-run-production-spec \
  docs/goals/006-module5-real-proposal-dry-run \
  docs/goals/007-module5-intervention-matrix-review \
  docs/goals/008-module5-production-matrix-contract-revision \
  docs/goals/009-module5-production-run-spec \
  docs/goals/010-module5-deep-server-remote-smoke-preflight \
  docs/goals/011-module5-source-context-identity \
  docs/goals/012-module5-25rep-production-rehearsal \
  docs/goals/013-module5-preproduction-baseline-freeze \
  docs/module5_dry_run_production_spec.md \
  docs/module5_intervention_matrix_review.md \
  docs/module5_production_matrix_contract.md \
  docs/module5_production_run_spec.md \
  docs/module5_remote_smoke_preflight.md \
  docs/module5_source_identity_contract.md \
  docs/module5_25rep_rehearsal_report.md
```

Review hits manually. They should be boundary, remote-path, stop-point,
non-claim, validation, or publication-control language.

## Read-Only Remote Artifact Check

Use only if `deep-server-ts` is reachable:

```bash
ssh deep-server-ts 'bash -lc '"'"'
set -euo pipefail
ART=/data/codex/artifacts/galaxias/module5_25rep_rehearsal_20260613T115519Z-goal012-m5-25rep-rehearsal
cd "$ART"
sha256sum -c checksums.sha256
python3 - << "PY"
import json
from pathlib import Path

root = Path(".")
summary = json.loads((root / "outputs/module5_25rep_rehearsal/inspection/inspection_summary.json").read_text())
provenance = json.loads((root / "outputs/module5_25rep_rehearsal/provenance.json").read_text())
keys = [
    "all_checks_passed",
    "row_count",
    "column_count",
    "expected_replicates",
    "source_intervention_units",
    "distinct_proposal_source_keys",
    "seed_mismatches",
    "source_identity",
    "replicate_coverage",
    "matched_pair_ids",
    "schema_columns",
    "production_attribution",
    "status",
]
for key in keys:
    print(f"summary_{key}={summary.get(key)}")
print(f"provenance_status={provenance.get('status')}")
print(f"provenance_production_attribution={provenance.get('production_attribution')}")
print(f"provenance_workers={provenance.get('workers')}")
print(f"provenance_artifact_verification_count={provenance.get('artifact_verification_count')}")
print(f"provenance_matched_sha={provenance.get('matched_outcomes_sha256')}")
PY
'"'"''
```

Required facts:

```text
summary_all_checks_passed=True
summary_row_count=69875
summary_column_count=53
summary_expected_replicates=25
summary_source_intervention_units=2795
summary_distinct_proposal_source_keys=780
summary_seed_mismatches=0
summary_source_identity=True
summary_replicate_coverage=True
summary_matched_pair_ids=True
summary_schema_columns=True
summary_production_attribution=False
summary_status=module5_25rep_rehearsal
provenance_status=module5_25rep_rehearsal
provenance_production_attribution=False
provenance_workers=32
provenance_artifact_verification_count=15
```

Do not create or attach to `tmux`. Do not modify remote files.

## Exact Paths To Stage

Stage exactly these paths after validation passes and after updating this Goal
013 `Log.md`:

```text
Makefile
README.md
data/module5_counterfactual_interventions.csv
data/module5_counterfactual_outcome_schema.csv
scripts/validate_module5_counterfactual_contract.py
src/galaxias_model/module5_counterfactual.py
tests/test_module5_counterfactual_contract.py
docs/goals/005-module5-dry-run-production-spec/Goal.md
docs/goals/005-module5-dry-run-production-spec/Log.md
docs/goals/005-module5-dry-run-production-spec/Plan.md
docs/goals/005-module5-dry-run-production-spec/Runbook.md
docs/goals/006-module5-real-proposal-dry-run/Goal.md
docs/goals/006-module5-real-proposal-dry-run/Log.md
docs/goals/006-module5-real-proposal-dry-run/Plan.md
docs/goals/006-module5-real-proposal-dry-run/Runbook.md
docs/goals/007-module5-intervention-matrix-review/Goal.md
docs/goals/007-module5-intervention-matrix-review/Log.md
docs/goals/007-module5-intervention-matrix-review/Plan.md
docs/goals/007-module5-intervention-matrix-review/Runbook.md
docs/goals/008-module5-production-matrix-contract-revision/Goal.md
docs/goals/008-module5-production-matrix-contract-revision/Log.md
docs/goals/008-module5-production-matrix-contract-revision/Plan.md
docs/goals/008-module5-production-matrix-contract-revision/Runbook.md
docs/goals/009-module5-production-run-spec/Goal.md
docs/goals/009-module5-production-run-spec/Log.md
docs/goals/009-module5-production-run-spec/Plan.md
docs/goals/009-module5-production-run-spec/Runbook.md
docs/goals/010-module5-deep-server-remote-smoke-preflight/Goal.md
docs/goals/010-module5-deep-server-remote-smoke-preflight/Log.md
docs/goals/010-module5-deep-server-remote-smoke-preflight/Plan.md
docs/goals/010-module5-deep-server-remote-smoke-preflight/Runbook.md
docs/goals/011-module5-source-context-identity/Goal.md
docs/goals/011-module5-source-context-identity/Log.md
docs/goals/011-module5-source-context-identity/Plan.md
docs/goals/011-module5-source-context-identity/Runbook.md
docs/goals/012-module5-25rep-production-rehearsal/Goal.md
docs/goals/012-module5-25rep-production-rehearsal/Log.md
docs/goals/012-module5-25rep-production-rehearsal/Plan.md
docs/goals/012-module5-25rep-production-rehearsal/Runbook.md
docs/goals/013-module5-preproduction-baseline-freeze/Goal.md
docs/goals/013-module5-preproduction-baseline-freeze/Log.md
docs/goals/013-module5-preproduction-baseline-freeze/Plan.md
docs/goals/013-module5-preproduction-baseline-freeze/Runbook.md
docs/module5_25rep_rehearsal_report.md
docs/module5_dry_run_production_spec.md
docs/module5_intervention_matrix_review.md
docs/module5_production_matrix_contract.md
docs/module5_production_run_spec.md
docs/module5_remote_smoke_preflight.md
docs/module5_source_identity_contract.md
scripts/inspect_module5_25rep_rehearsal.py
scripts/inspect_module5_real_proposal_dry_run.py
scripts/run_module5_25rep_rehearsal.py
scripts/run_module5_real_proposal_dry_run.py
src/galaxias_model/module5_dry_run_inspect.py
src/galaxias_model/module5_proposals.py
src/galaxias_model/module5_rehearsal.py
tests/test_module5_dry_run_inspection.py
tests/test_module5_production_rehearsal.py
tests/test_module5_real_proposal_dry_run.py
tests/test_module5_source_identity.py
```

Do not stage:

```text
outputs/
.venv/
.pytest_cache/
.ruff_cache/
__pycache__/
remote artifact directories
```

## Staging Commands

Use exact-path staging. A safe pattern is:

```bash
git add \
  Makefile \
  README.md \
  data/module5_counterfactual_interventions.csv \
  data/module5_counterfactual_outcome_schema.csv \
  scripts/validate_module5_counterfactual_contract.py \
  src/galaxias_model/module5_counterfactual.py \
  tests/test_module5_counterfactual_contract.py \
  docs/goals/005-module5-dry-run-production-spec \
  docs/goals/006-module5-real-proposal-dry-run \
  docs/goals/007-module5-intervention-matrix-review \
  docs/goals/008-module5-production-matrix-contract-revision \
  docs/goals/009-module5-production-run-spec \
  docs/goals/010-module5-deep-server-remote-smoke-preflight \
  docs/goals/011-module5-source-context-identity \
  docs/goals/012-module5-25rep-production-rehearsal \
  docs/goals/013-module5-preproduction-baseline-freeze \
  docs/module5_25rep_rehearsal_report.md \
  docs/module5_dry_run_production_spec.md \
  docs/module5_intervention_matrix_review.md \
  docs/module5_production_matrix_contract.md \
  docs/module5_production_run_spec.md \
  docs/module5_remote_smoke_preflight.md \
  docs/module5_source_identity_contract.md \
  scripts/inspect_module5_25rep_rehearsal.py \
  scripts/inspect_module5_real_proposal_dry_run.py \
  scripts/run_module5_25rep_rehearsal.py \
  scripts/run_module5_real_proposal_dry_run.py \
  src/galaxias_model/module5_dry_run_inspect.py \
  src/galaxias_model/module5_proposals.py \
  src/galaxias_model/module5_rehearsal.py \
  tests/test_module5_dry_run_inspection.py \
  tests/test_module5_production_rehearsal.py \
  tests/test_module5_real_proposal_dry_run.py \
  tests/test_module5_source_identity.py
```

Then verify:

```bash
git diff --cached --name-only
git diff --cached --stat
git status --short --branch
```

The cached name list must match the exact path list above. Stop if it differs.

## Commit And Push

Commit:

```bash
git commit -m "Prepare Module 5 production baseline"
```

Record:

```bash
git rev-parse HEAD
git status --short --branch
```

Push:

```bash
git push origin main
```

Record:

```bash
git status --short --branch
git rev-parse HEAD
```

Do not force-push, amend, rebase, reset, create a PR, or run production.

## Wake-Up Content

Report:

- final branch, HEAD, and status;
- pushed commit SHA;
- staged/committed path count and list;
- validation command outcomes;
- plan-only rehearsal preflight facts;
- read-only remote artifact evidence or exact remote-unavailable error;
- ignored local generated outputs that remain untracked;
- confirmation that no production run, interpretation, PR, or generated-output
  promotion occurred;
- recommended Goal 014 shape.
