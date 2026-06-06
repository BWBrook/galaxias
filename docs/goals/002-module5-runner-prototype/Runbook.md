# Runbook

## Read First

- `AGENTS.md`
- `AGENT_HANDOFF.md`
- `docs/module5_counterfactual_attribution_plan.md`
- `docs/goals/001-module5-counterfactual-design-and-smoke/Goal.md`
- `docs/goals/001-module5-counterfactual-design-and-smoke/Plan.md`
- `docs/goals/001-module5-counterfactual-design-and-smoke/Runbook.md`
- `docs/goals/001-module5-counterfactual-design-and-smoke/Log.md`
- `scripts/validate_module5_counterfactual_contract.py`
- `tests/test_module5_counterfactual_contract.py`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`

## Operating Mode

Tiny local runner prototype only. Generated smoke files stay under ignored
`outputs/`.

Work from this branch:

```bash
git switch codex/galaxias-goal002-module5-runner-prototype
```

## Smoke Command

Default tiny local smoke:

```bash
uv run python scripts/run_module5_counterfactual_smoke.py \
  --output-dir outputs/module5_runner_smoke \
  --replicates 2
```

Focused one-intervention smoke:

```bash
uv run python scripts/run_module5_counterfactual_smoke.py \
  --intervention-id m5_persistent_joint_cause_no_trout_pressure \
  --output-dir outputs/module5_runner_smoke \
  --replicates 2
```

Expected generated files:

- `outputs/module5_runner_smoke/matched_outcomes.csv`
- `outputs/module5_runner_smoke/provenance.json`

These outputs are ignored by git and are not production attribution results.

## Validation Commands

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
uv run pytest tests/test_module5_runner_prototype.py -q
make fast-check
git diff --check
git status --short --branch
```

## Boundaries

Pause before:

- production Module 5 analysis;
- broad simulation batches;
- remote compute or HPC work;
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
