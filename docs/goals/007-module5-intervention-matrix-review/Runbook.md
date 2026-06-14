# Runbook

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short=12 HEAD
git status --short --branch
```

Stop before editing if dirty state differs from the expected Goal 005/006/007
surface described in `Plan.md`.

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
    "coherent_pressure_history",
    "transient_overshoot_signature",
    "module5_role",
    "decision_note",
]].to_string(index=False))
PY
```

Do not run Module 5 dry-run commands or tests for this docs-only goal.

## Memo Requirements

The memo must make a single primary recommendation. It may list alternatives,
but it should not end as an open-ended brainstorm.

Use direct labels:

- `production_candidate`
- `sensitivity_candidate`
- `diagnostic_only`
- `dry_run_only`
- `requires_revision`
- `not_recommended`

Use cautious claim language:

- acceptable: "decision package", "candidate", "recommend", "requires review";
- avoid: "proves", "final causal", "manuscript-ready", "production result".

## Docs-Only Validation

Run:

```bash
git status --short --branch
git diff --check
```

Trailing-whitespace scan:

```bash
rg -n "[ \t]+$" docs/goals/007-module5-intervention-matrix-review docs/module5_intervention_matrix_review.md
```

Marker scan:

```bash
rg -n "production attribution|production-ready|remote compute|outputs/|manuscript|commit|push" docs/goals/007-module5-intervention-matrix-review docs/module5_intervention_matrix_review.md
```

Review marker hits manually. They should be boundary or stop-point language.

## Stop Points

Stop and wake Galaxias before:

- editing any tracked CSV contract;
- adding, removing, or renaming intervention rows;
- editing code, tests, scripts, Makefile, or generated outputs;
- running simulations, dry-run commands, validation suites, or remote probes;
- staging, committing, pushing, or publishing;
- turning this review into production attribution or manuscript interpretation.

## Wake-Up Content

Report:

- final branch, HEAD, and status;
- changed files;
- validation commands and outcomes;
- primary recommendation;
- next-goal shape;
- risks/questions.
