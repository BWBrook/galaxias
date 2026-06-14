# Runbook

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short=12 HEAD
git status --short --branch
```

Stop before editing if dirty state differs from the expected Goal 005/006/007
surface plus this Goal 008 packet described in `Plan.md`.

## Read Commands

Useful read-only summaries:

```bash
uv run python - <<'PY'
import pandas as pd

matrix = pd.read_csv("data/module5_counterfactual_interventions.csv")
print(matrix[[
    "intervention_id",
    "family_id",
    "module5_role",
    "intervention_axis",
    "production_status",
    "negative_reference_flag",
]].to_string(index=False))
PY
```

```bash
uv run python - <<'PY'
import pandas as pd

families = pd.read_csv("data/module4_5_family_decision_table.csv")
print(families[[
    "family_id",
    "accepted_proposal_count",
    "accepted_frontier",
    "module5_role",
    "decision_note",
]].to_string(index=False))
PY
```

## Focused Matrix-Shape Check

Use either a focused pytest assertion or this direct check, and record the
result in `Log.md`:

```bash
uv run python - <<'PY'
import csv
from collections import defaultdict
from pathlib import Path

path = Path("data/module5_counterfactual_interventions.csv")
rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))

expected_shape = {
    "persistent_joint_cause": {
        "status_quo",
        "no_trout_pressure",
        "no_climbing_pressure",
        "no_trout_or_climbing_pressure",
    },
    "climbing_only": {
        "status_quo",
        "no_trout_pressure",
        "no_climbing_pressure",
    },
    "transient_perfect_storm": {
        "status_quo",
        "no_trout_pressure",
        "no_climbing_pressure",
        "no_trout_or_climbing_pressure",
    },
    "habitat_only_null": {"status_quo"},
    "trout_only": {"status_quo"},
}
expected_new_ids = {
    "m5_climbing_only_no_climbing_pressure",
    "m5_transient_perfect_storm_no_trout_pressure",
    "m5_transient_perfect_storm_no_trout_or_climbing_pressure",
}

ids = [row["intervention_id"] for row in rows]
if len(rows) != 13:
    raise SystemExit(f"expected 13 rows, found {len(rows)}")
if len(ids) != len(set(ids)):
    raise SystemExit("duplicate intervention_id values found")
missing_ids = expected_new_ids - set(ids)
if missing_ids:
    raise SystemExit(f"missing new intervention IDs: {sorted(missing_ids)}")

actual_shape = defaultdict(set)
for row in rows:
    actual_shape[row["family_id"]].add(row["intervention_axis"])
if {key: set(value) for key, value in actual_shape.items()} != expected_shape:
    raise SystemExit(f"unexpected family-axis shape: {dict(actual_shape)}")

negative_axes = {
    row["family_id"]: row["intervention_axis"]
    for row in rows
    if row["negative_reference_flag"].strip().upper() == "TRUE"
}
if set(negative_axes.values()) != {"status_quo"}:
    raise SystemExit(f"negative-reference rows are not status_quo only: {negative_axes}")

print("matrix shape ok")
PY
```

## Required Validation

Run:

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
uv run pytest tests/test_module5_counterfactual_contract.py -q
git diff --check
git status --short --branch
```

Trailing-whitespace scan:

```bash
rg -n "[ \t]+$" docs/goals/008-module5-production-matrix-contract-revision docs/module5_production_matrix_contract.md data/module5_counterfactual_interventions.csv tests/test_module5_counterfactual_contract.py
```

If `tests/test_module5_counterfactual_contract.py` is not changed, it may still
be included in the scan. If you change additional contract/docs files, add them
to the scan.

Marker scan:

```bash
rg -n "production attribution|production-ready|remote compute|outputs/|manuscript|commit|push|hook|design_only|diagnostic" docs/goals/008-module5-production-matrix-contract-revision docs/module5_production_matrix_contract.md data/module5_counterfactual_interventions.csv tests/test_module5_counterfactual_contract.py
```

Review marker hits manually. They should be boundary, non-claim, hook-status,
contract-status, diagnostic-sidecar, or stop-point language.

## Commands Not Authorized

Do not run:

```bash
make module5-dry-run
make module5-dry-run-inspect
make fast-check
```

Do not run production attribution, remote compute probes, generated-output
commands, staging, commit, push, or PR commands.

## Stop Points

Stop and wake Galaxias before:

- changing `production_status` vocabulary or validator enum semantics;
- deleting, renaming, or reinterpreting existing intervention IDs;
- adding pressure-removal rows for negative-reference families;
- changing pressure-removal semantics or adding new scenario hooks;
- editing runner, simulator, proposal, dry-run, Makefile, or generated-output
  code;
- running simulations, dry runs, broad validation suites, remote probes, or
  production-sized work;
- staging, committing, pushing, publishing, or opening a PR;
- making final causal, manuscript-level, or production attribution claims.

## Wake-Up Content

Report:

- final branch, HEAD, and status;
- changed files;
- final row count and family-axis shape;
- validation commands and outcomes;
- any deviations from the expected contract;
- risks/questions.
