# Runbook

## Read First

- `AGENTS.md`
- `AGENT_HANDOFF.md`
- `README.md`
- `docs/module5_counterfactual_attribution_plan.md`
- `docs/goals/001-module5-counterfactual-design-and-smoke/`
- `docs/goals/002-module5-runner-prototype/`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`
- `scripts/run_module5_counterfactual_smoke.py`
- `src/galaxias_model/module5_counterfactual.py`
- `tests/test_module5_runner_prototype.py`

## Operating Mode

Disk-first inspection of tiny local smoke output only. Generated files stay
under ignored `outputs/`.

## Commands

Regenerate the tiny local smoke output if missing:

```bash
make module5-smoke
```

Inspect existing smoke output:

```bash
uv run python scripts/inspect_module5_counterfactual_smoke.py \
  --smoke-dir outputs/module5_runner_smoke \
  --outcome-schema data/module5_counterfactual_outcome_schema.csv
```

If available, the Makefile shortcut is:

```bash
make module5-inspect
```

Expected generated inspection files:

- `outputs/module5_runner_smoke/inspection/inspection_summary.json`
- `outputs/module5_runner_smoke/inspection/inspection_checks.csv`
- `outputs/module5_runner_smoke/inspection/inspection_report.md`

These outputs are ignored by git and are not production attribution results.

## Validation Commands

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
uv run pytest tests/test_module5_smoke_inspection.py -q
make fast-check
make module5-smoke
make module5-inspect
git diff --check
git status --short --branch
```

Marker scan over changed/new tracked text:

```bash
git diff --name-only --diff-filter=ACM origin/main...HEAD
git ls-files --others --exclude-standard
```

Use the resulting tracked text paths for a narrow scan of production-claim
phrases before reporting.

## Boundaries

Pause before:

- production Module 5 attribution;
- broad simulation batches;
- remote compute;
- calibration reruns;
- changes to scientific defaults, priors, target weights, family definitions,
  observation-bridge assumptions, or Module 4.5 outputs;
- manuscript-level causal claims;
- commit, push, or staging.

## Reporting

Report:

- branch/worktree state;
- files changed;
- validation commands and outcomes;
- generated output locations and ignored status;
- explicit boundary confirmation;
- blockers and recommended next step.
