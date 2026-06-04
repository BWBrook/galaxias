# Agent Handoff: Pedder Galaxias

Created: 2026-06-04

Purpose: this note is for the next Codex/action-agent thread after the current
thread is closed and archived. It is intentionally a handoff note only, not a
new goal packet and not a change in scientific direction.

## Current Repository State

- Working repo: `/Users/bwbrook/papers/galaxias`.
- Observed state before creating this handoff: `main...origin/main`, clean.
- Latest project commit before this handoff:
  `4f78279 Add Module 5 counterfactual design contract`.
- Python baseline is Python 3.14 through `uv`; keep `uv.lock` authoritative.
- Modules 1 through 4.5 are complete to the current project standard.
- Goal 001, `docs/goals/001-module5-counterfactual-design-and-smoke/`, has
  been completed and pushed. Its `Log.md` records the validation evidence.
- No Goal 002 packet is present in this repo at handoff time.

## Files To Read First

Start with these, in order, before changing anything:

1. `AGENTS.md`
2. `README.md`
3. `AGENT_HANDOFF.md`
4. `docs/gated_action_plan_module4_5_and_beyond.md`
5. `docs/module4_5_mechanism_interpretation_plan.md`
6. `docs/module4_5_mechanism_interpretation_review.md`
7. `docs/module5_counterfactual_attribution_plan.md`
8. `docs/goals/001-module5-counterfactual-design-and-smoke/Goal.md`
9. `docs/goals/001-module5-counterfactual-design-and-smoke/Plan.md`
10. `docs/goals/001-module5-counterfactual-design-and-smoke/Runbook.md`
11. `docs/goals/001-module5-counterfactual-design-and-smoke/Log.md`
12. `data/README.md`

For host and compute routing context, use `/Users/bwbrook/.codex/AGENTS.md`
and the `/Users/bwbrook/work/nectar` control-plane docs named there.

## Scientific And Workflow Context

- Module 4 found `persistent_joint_cause` as the stable winning family across
  most observation-bridge variant/seed runs.
- Module 4.5 converted that into a mechanism audit and selected the current
  Module 5 ensemble:
  - primary: `persistent_joint_cause`
  - sensitivity: `climbing_only`, `transient_perfect_storm`
  - negative references: `habitat_only_null`, `trout_only`
- Module 5 has not produced attribution results yet. The current repo only has
  a design contract and validator for the next attribution stage.
- The Module 4.5 caveat remains important: deterministic landmark trajectories
  retained positive latent abundance through 2002, so future attribution should
  focus on matched stochastic counterfactual outcomes and detection-linked
  endpoints, not deterministic extinction narratives.
- Do not upgrade scientific language into a final causal claim. The current
  licensed claim is narrower: within the current model-family and target
  framework, habitat-only and trout-only explanations are not competitive, and
  joint trout-plus-climbing explanations are the most stable calibration result
  so far.

## Module 5 Contract State

Goal 001 added:

- `docs/module5_counterfactual_attribution_plan.md`
- `data/module5_counterfactual_interventions.csv`
- `data/module5_counterfactual_outcome_schema.csv`
- `scripts/validate_module5_counterfactual_contract.py`
- `tests/test_module5_counterfactual_contract.py`

The contract validator checks required columns, intervention ID uniqueness,
required intervention axes, Module 5 role compatibility with
`data/module4_5_family_decision_table.csv`, and required future output schema
fields.

The last completed validation set was:

- `uv run python scripts/validate_module5_counterfactual_contract.py`
- `uv run pytest tests/test_module5_counterfactual_contract.py -q`
- `make fast-check`
- `git diff --check`
- `git status --short --branch`

## Key Risks And Caveats

- Do not run full Module 5 production, remote/HPC jobs, new calibration grids,
  or Module 4 reruns unless a new formal goal explicitly authorizes them.
- Do not alter scientific defaults, priors, target weights, family definitions,
  observation-bridge assumptions, or Module 4.5 outputs without explicit
  authorization.
- Module 5 non-`status_quo` axes are still design-only until runner-level
  intervention hooks exist:
  - `no_trout_pressure`
  - `no_climbing_pressure`
  - `no_trout_or_climbing_pressure`
- Raw Module 4 artifacts are not tracked. The tracked manifest is
  `data/module4_raw_artifact_manifest.csv`; the local ignored mirror, when
  present, is `outputs/remote/module4_observation_sensitivity_20260522T101942Z`.
- The original Module 4 run manifests did not capture exact source git commit
  or exact Python patch version. Keep those provenance fields explicitly
  historical/inferred rather than presenting them as captured facts.
- Meaningful compute should be routed deliberately through the remote-compute
  ladder in `/Users/bwbrook/work/nectar`, usually `deep-server` first for large
  single-host CPU/RAM work.

## Thread And Project Relationships

- Treat this repo as the action-repo workspace, not the orchestration source of
  truth.
- Orchestration locations and management are being reorganized. Do not assume
  old thread, goal-composer, or supervisor paths remain authoritative.
- If a new `docs/goals/...` packet appears, read its `Goal.md`, `Plan.md`,
  `Runbook.md`, and `Log.md` first and treat that packet as the active source
  of truth.
- Keep repo-specific scientific decisions here. Keep machine/access and reusable
  compute-routing lessons in `/Users/bwbrook/work/nectar`.

## Recommended Next Action

The next useful scientific/software step is likely Goal 002: a bounded Module 5
runner prototype that consumes `data/module5_counterfactual_interventions.csv`
and produces tiny, contract-conforming matched baseline/intervention smoke
outputs. That goal should be written as a formal packet before execution.

A good Goal 002 should probably:

- keep all outputs under ignored `outputs/`;
- implement only tiny local smoke runs first;
- add intervention override hooks without changing existing scientific
  defaults;
- validate generated rows against
  `data/module5_counterfactual_outcome_schema.csv`;
- preserve matched proposal/seed/replicate pairing;
- avoid production attribution and manuscript claims until a later gate.

## Closing Note

This handoff was created during a thread-archive transition and did not start
new project work. The successor should confirm live git state before acting.
