# Runbook

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short=12 HEAD
git status --short --branch
```

Stop before editing if dirty state differs from the expected Goal 005/006/007
/008 surface plus this Goal 009 packet described in `Plan.md`.

## Useful Read-Only Summaries

Proposal-set summary:

```bash
uv run python - <<'PY'
import pandas as pd

proposals = pd.read_csv("data/module4_5_proposal_set_membership.csv")
families = pd.read_csv("data/module4_5_family_decision_table.csv")

print("accepted by family")
print(
    proposals.loc[proposals["in_accepted"]]
    .groupby("family_id")
    .size()
    .to_string()
)

print("\nproposal sets by family")
for column in [
    "in_accepted",
    "in_family_winners",
    "in_global_winners",
    "in_near_frontier_absolute",
    "in_near_frontier_relative",
]:
    print(f"\n{column}")
    print(proposals.loc[proposals[column]].groupby("family_id").size().to_string())

print("\nfamily decision table")
print(families.to_string(index=False))
PY
```

Intervention matrix summary:

```bash
uv run python - <<'PY'
import pandas as pd

matrix = pd.read_csv("data/module5_counterfactual_interventions.csv")
print(matrix[[
    "intervention_id",
    "family_id",
    "module5_role",
    "intervention_axis",
    "negative_reference_flag",
    "production_status",
]].to_string(index=False))
print("\nrow counts by family")
print(matrix.groupby(["family_id", "module5_role"]).size().to_string())
PY
```

Expected row-count helper:

```bash
uv run python - <<'PY'
import pandas as pd

proposals = pd.read_csv("data/module4_5_proposal_set_membership.csv")
matrix = pd.read_csv("data/module5_counterfactual_interventions.csv")

accepted_families = {"persistent_joint_cause", "climbing_only", "transient_perfect_storm"}
accepted_counts = (
    proposals.loc[proposals["in_accepted"] & proposals["family_id"].isin(accepted_families)]
    .groupby("family_id")
    .size()
    .to_dict()
)
intervention_counts = (
    matrix.loc[matrix["family_id"].isin(accepted_families)]
    .groupby("family_id")
    .size()
    .to_dict()
)
proposal_intervention_pairs = sum(
    accepted_counts[family] * intervention_counts[family]
    for family in accepted_families
)
print("accepted_counts", accepted_counts)
print("intervention_counts", intervention_counts)
print("accepted proposal/intervention pairs", proposal_intervention_pairs)
for replicates in [10, 20, 50, 100]:
    print(f"replicates={replicates}: rows={proposal_intervention_pairs * replicates}")
PY
```

## Docs-Only Validation

Run:

```bash
git status --short --branch
git diff --check
```

Trailing-whitespace scan:

```bash
rg -n "[ \t]+$" docs/goals/009-module5-production-run-spec docs/module5_production_run_spec.md
```

Marker scan:

```bash
rg -n "production attribution|production-ready|remote compute|deep-server|tmux|outputs/|manuscript|commit|push" docs/goals/009-module5-production-run-spec docs/module5_production_run_spec.md
```

Review marker hits manually. They should be recommendation, boundary,
non-claim, stop-point, or future-gate language.

## Commands Not Authorized

Do not run:

```bash
make module5-dry-run
make module5-dry-run-inspect
make fast-check
ssh deep-server-ts
ssh utas-ubuntu
tmux
rsync
scp
```

Do not run tests, simulations, dry-run commands, production attribution,
remote probes, generated-output commands, staging, commit, push, or PR
commands.

## Stop Points

Stop and wake Galaxias before:

- editing code, tests, Makefile, or tracked CSV contracts;
- changing the Goal 008 intervention matrix;
- running simulations, dry runs, tests, broad validation suites, or generated
  output commands;
- running SSH, `tmux`, `rsync`, `scp`, remote probes, or remote setup;
- deciding to use `kunanyi`, Nectar GPU, Alien WSL, or another compute target
  instead of `deep-server`;
- staging, committing, pushing, publishing, or opening a PR;
- making final causal, manuscript-level, or production attribution claims.

## Wake-Up Content

Report:

- final branch, HEAD, and status;
- changed files;
- recommended production run shape;
- expected row count(s);
- recommended remote target/session model;
- validation commands and outcomes;
- risks/questions.
