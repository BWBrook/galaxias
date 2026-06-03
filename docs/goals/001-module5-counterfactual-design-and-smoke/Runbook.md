# Runbook

## Read First

- `AGENTS.md`
- `README.md`
- `docs/gated_action_plan_module4_5_and_beyond.md`
- `docs/module4_5_mechanism_interpretation_plan.md`
- `docs/module4_5_mechanism_interpretation_review.md`
- `data/module4_5_family_decision_table.csv`
- `data/README.md`
- `Makefile`
- `pyproject.toml`

## Operating Mode

Scientific workflow design contract plus tiny local smoke/scaffold.

Work from:

```bash
cd /Users/bwbrook/papers/galaxias
```

## Git And Publication Policy

- Preserve pre-existing dirty work unless explicitly told otherwise.
- Commit: authorised after validation passes.
- Push: authorised to `origin main` after the commit succeeds and the branch is
  still aligned with `origin/main`.
- PR: not required for this goal.
- Stage exact paths only. Do not use `git add .`.

Suggested exact staging paths:

```bash
git add \
  docs/goals/001-module5-counterfactual-design-and-smoke \
  docs/module5_counterfactual_attribution_plan.md \
  data/module5_counterfactual_interventions.csv \
  data/module5_counterfactual_outcome_schema.csv \
  scripts/validate_module5_counterfactual_contract.py \
  tests/test_module5_counterfactual_contract.py \
  data/README.md \
  Makefile
```

Omit any optional path that was not changed. Include any narrow helper file only
if it was created for this goal.

## Preferred Commands

Starting state:

```bash
git status --short --branch
```

Contract inspection:

```bash
uv run python - <<'PY'
import pandas as pd
for path in [
    "data/module5_counterfactual_interventions.csv",
    "data/module5_counterfactual_outcome_schema.csv",
]:
    frame = pd.read_csv(path)
    print(path, frame.shape)
    print(", ".join(frame.columns))
PY
```

Focused validation:

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
uv run pytest tests/test_module5_counterfactual_contract.py -q
```

Repo gate:

```bash
make fast-check
git diff --check
git status --short --branch
```

Publish after validation:

```bash
git fetch --prune origin
git status --short --branch
git add <exact paths>
git commit -m "Add Module 5 counterfactual design contract"
git push origin main
git rev-parse --short HEAD
git status --short --branch
```

## Validation Commands

Run the minimum gate from `Goal.md`:

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
uv run pytest tests/test_module5_counterfactual_contract.py -q
make fast-check
git diff --check
git status --short --branch
```

If `make fast-check` reruns the focused test through `pytest -m "not slow"`,
that is expected. Record both focused and repo-level evidence.

## Escalation Rules

Pause and ask for direction before:

- destructive changes
- expensive compute
- remote/HPC jobs
- broad dependency upgrades
- production Module 5 simulations
- new calibration grids or Module 4 reruns
- changes to priors, target weights, family definitions, observation-bridge
  assumptions, or scientific defaults
- manuscript-level causal interpretation beyond the design contract
- broad refactors outside the Module 5 contract/scaffold surface

## Reporting Rules

Update `Log.md` after each milestone with:

- what changed
- what validation ran
- artefact paths
- blockers or caveats
- next step

On completion, update `Log.md` with:

- final status
- commits created
- push status
- artefacts produced
- validation evidence
- residual risks
- final branch and commit identifier

The final response should include tracked and untracked git status when working
inside this repo.
