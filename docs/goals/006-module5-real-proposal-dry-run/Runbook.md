# Runbook

## Read First

- `AGENTS.md`
- `README.md`
- `docs/goals/006-module5-real-proposal-dry-run/Goal.md`
- `docs/goals/006-module5-real-proposal-dry-run/Plan.md`
- `docs/goals/006-module5-real-proposal-dry-run/Log.md`
- `docs/module5_dry_run_production_spec.md`
- `docs/module5_counterfactual_attribution_plan.md`
- `docs/goals/001-module5-counterfactual-design-and-smoke/Log.md`
- `docs/goals/002-module5-runner-prototype/Log.md`
- `docs/goals/003-module5-smoke-inspection/Log.md`
- `docs/goals/004-module5-production-readiness/Log.md`
- `docs/goals/005-module5-dry-run-production-spec/Log.md`

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short=12 HEAD
git status --short --branch
```

Expected branch is `main`. Expected pre-work dirty state is limited to the
Goal 005 context and this Goal 006 packet. Stop before editing if anything
else is dirty.

## Required Input Checks

Confirm the selected proposal rows:

```bash
uv run python - <<'PY'
import pandas as pd

selected = {
    "persistent_joint_cause:p00162",
    "climbing_only:p00216",
    "transient_perfect_storm:p00144",
    "habitat_only_null:p00761",
    "trout_only:p00814",
}
membership = pd.read_csv("data/module4_5_proposal_set_membership.csv")
subset = membership[
    membership["proposal_id"].isin(selected)
    & (membership["variant_id"] == "baseline_current")
    & (membership["seed"] == 20260410)
]
print(subset[["proposal_id", "family_id", "in_family_winners", "in_accepted", "target_sum_rank"]].to_string(index=False))
assert set(subset["proposal_id"]) == selected
assert subset["in_family_winners"].all()
PY
```

Confirm the local raw parameter-values artifact:

```bash
uv run python - <<'PY'
import hashlib
from pathlib import Path

import pandas as pd

artifact = Path("outputs/remote/module4_observation_sensitivity_20260522T101942Z/baseline_current_seed20260410/parameter_values.csv.gz")
expected_sha = "49e080a23dcaca2f29874c0e3825bd806406f494b2db046307a84a74e8673c4c"
if not artifact.exists():
    raise SystemExit(f"missing artifact: {artifact}")
actual_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
print(f"{artifact} sha256={actual_sha}")
assert actual_sha == expected_sha

selected = {
    "persistent_joint_cause:p00162",
    "climbing_only:p00216",
    "transient_perfect_storm:p00144",
    "habitat_only_null:p00761",
    "trout_only:p00814",
}
values = pd.read_csv(artifact)
counts = values[values["proposal_id"].isin(selected)].groupby("proposal_id")["parameter_id"].nunique()
print(counts.to_string())
assert set(counts.index) == selected
assert (counts == 40).all()
PY
```

## Validation Ladder

Run focused tests as they are introduced. The final validation ladder is:

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
uv run pytest tests/test_module5_runner_prototype.py tests/test_module5_smoke_inspection.py -q
uv run pytest tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py -q
make fast-check
make module5-dry-run
make module5-dry-run-inspect
git diff --check
git status --short --branch
```

If test file names differ because the implementation uses a cleaner local
decomposition, run the equivalent focused tests and record the actual commands
in `Log.md`.

## Expected Dry-Run Outputs

After `make module5-dry-run` and `make module5-dry-run-inspect`, expect:

```text
outputs/module5_dry_run_baseline_current_20260410/matched_outcomes.csv
outputs/module5_dry_run_baseline_current_20260410/provenance.json
outputs/module5_dry_run_baseline_current_20260410/inspection/inspection_summary.json
outputs/module5_dry_run_baseline_current_20260410/inspection/inspection_checks.csv
outputs/module5_dry_run_baseline_current_20260410/inspection/inspection_report.md
```

Expected dry-run facts:

- 50 outcome rows.
- 10 unique intervention IDs.
- 5 unique proposal IDs.
- 5 stochastic replicates per intervention row.
- `baseline_stochastic_seed == intervention_stochastic_seed` for every row.
- `production_attribution` is false.
- Boundary language says this is not production attribution and not manuscript
  evidence.

## Stop Points

Stop and wake Galaxias before:

- fetching, copying, or reconstructing raw Module 4 artifacts;
- changing any tracked CSV contract;
- changing the selected proposal set, replicate count, or intervention matrix;
- running remote compute or remote probes;
- launching any production-sized run;
- staging, committing, pushing, or publishing;
- making manuscript or causal proof claims.

## Final Wake-Up

Send Galaxias a concise completion or blockage note with:

- final branch, HEAD, and status;
- files changed;
- generated output paths;
- validation commands and pass/fail outcomes;
- any unresolved risks or questions.
