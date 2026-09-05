# Pedder Galaxias Evidence And Modelling Workflow

This repository builds a staged, auditable modelling workflow for the historical
extirpation of Pedder galaxias (`Galaxias pedderensis`) from the natural Lake
Pedder system.

## Biological Question

The project asks whether a simple mechanistic stochastic model, calibrated to
sparse historical evidence, can distinguish among:

- habitat-only decline after inundation;
- brown-trout-only pressure;
- climbing-galaxias-only pressure;
- sustained joint trout plus climbing-galaxias pressure;
- a transient inundation, trophic-upsurge, trout-overshoot, and later
  climbing-galaxias perfect storm.

The workflow is deliberately cautious: historical fit and mechanism coherence
come before counterfactual attribution.

## Current Status

Modules 1 through 4.5 are complete to the current standard. Module 4 found
that `persistent_joint_cause` won 12 of 15 observation-bridge variant/seed
runs, including all baseline and combined soft late-observation runs.
`climbing_only` won 3 of 15 runs under single-axis late-observation
relaxations. `habitat_only_null` and `trout_only` had zero accepted proposals
across the Module 4 grid.

Module 4.5 turned that calibration result into a mechanism audit. Its current
decision table carries `persistent_joint_cause` as the primary Module 5
ensemble, keeps `climbing_only` and `transient_perfect_storm` as sensitivity
cases, and keeps `habitat_only_null` and `trout_only` as negative references.
Module 5 has since completed the matched pressure-removal experiments,
including the shared four-arm, 250-replicate extension. Its scale-dependent
interaction results are under internal scientific review. See
`docs/module5_shared_four_arm_250rep_extension.md` for the current evidence and
`AGENT_HANDOFF.md` for the unresolved observation-context and endpoint choices.

## Module Map

- Module 1: Tier 1 model design and data pack.
- Module 1.5: latent-kernel sanity checks.
- Module 2: observation bridge and target scoring.
- Module 2.5: Lake Oberon and Strathgordon intrinsic-baseline scoring.
- Module 3: two-stage ABC/history-matching calibration harness.
- Module 3.5: calibration diagnostics and sensitivity sweep.
- Module 3.75: late-observation bridge diagnostics for `CT007`, `CT009`, and
  `CT010`.
- Module 4: observation-bridge sensitivity calibration.
- Module 4.5: mechanism interpretation audit.
- Module 5: matched pressure-removal counterfactuals and interaction stability.
- Later work: coexistence envelope, robustness, manuscript, and genetics sidecar.

## Quick Start

Use the locked `uv` environment:

```bash
make setup
make fast-check
make integration-check
make check
```

`make fast-check` runs portability, compile, and tests not marked `slow`.
`make integration-check` runs the slower calibration/reproducibility tests.
`make check` runs both.

The Module 3 readiness report runs one calibration and assesses its scientific
gates. Serial/parallel and resumed/clean equivalence belong to the integration
tests. Its CLI accepts `--output-root` for the review bundle and `--output-dir`
for calibration output; it preserves unrelated files in those directories.

Small smoke jobs stay local and write ignored outputs:

```bash
make smoke
make module4-smoke
make module4-5-smoke
make module5-smoke
make module5-inspect
```

`make module5-inspect` reads the tiny Module 5 smoke output from disk and
writes an ignored inspection bundle. It is a runner-output contract check, not
production attribution.

The fixed Goal 006 five-proposal dry-run commands have been retired. A bounded
real-source test exercises the current matched-pair runner, parameter loading,
provenance and disk inspection. The full matched-pair and shared four-arm
runners remain in `scripts/run_module5_25rep_rehearsal.py` and
`scripts/run_module5_factorial_extension.py`; even at one replicate they select
the full source ensembles and are not tiny local smoke commands.

Historical run packets retain execution provenance. New meaningful compute
and manuscript work follow the current scientific scope and compute policy.

The full Module 4.5 diagnostic can be regenerated from the raw Module 4
artifact manifest:

```bash
uv run python scripts/run_module4_5_mechanism_interpretation.py \
  --module4-root outputs/remote/module4_observation_sensitivity_20260522T101942Z \
  --manifest data/module4_raw_artifact_manifest.csv \
  --publish-root . \
  --verify-hashes
```

## Offline Or Cluster-Safe Python

The repo targets Python 3.14. On machines where `uv` should not download a
managed Python, point it at a pre-installed interpreter or forbid downloads:

```bash
UV_PYTHON_DOWNLOADS=never uv run --python /path/to/python3.14 pytest -m "not slow"
```

Keep `uv.lock` authoritative; do not replace the host Python to make this repo
work.

## Source And Generated Files

Source inputs live mainly under:

- `literature/`
- `data/source_register.csv`
- `data/evidence_ledger.csv`
- `data/calibration_targets.csv`
- `data/calibration_target_details.json`
- `data/parameter_priors.csv`
- `data/model_family_parameter_map.csv`
- `data/parameter_constraints.csv`
- `data/scenario_definitions.json`

Tracked generated summaries live under `data/` and `docs/`. Large raw
calibration outputs live under ignored `outputs/` or remote artifact paths and
should not be committed.

## Raw Module 4 Artifacts

Module 4.5 depends on the raw Module 4 variant/seed outputs indexed by:

- `data/module4_raw_artifact_manifest.csv`

The local mirror, when present, is:

- `outputs/remote/module4_observation_sensitivity_20260522T101942Z`

The durable remote artifact location is:

- `/data/codex/artifacts/galaxias/module4_observation_sensitivity_20260522T101942Z`

A fresh clone can identify required raw files from the manifest even if the
ignored `outputs/` mirror has not yet been copied locally.

## Compute Policy

Use this Mac for repo maintenance, docs, compile checks, unit tests, tiny smoke
runs, and light pandas/report generation. Use `deep-server` or Nectar for
meaningful calibration or full Module 4.5 extraction if local joins become
clumsy. Use Kunanyi only for PBS-backed production sweeps; do not run
simulations on the login node.

The live machine/access runbooks are in `/Users/bwbrook/work/nectar`.

## Current Non-Claims

The current result does not prove that sustained joint predation caused
extinction in a final causal sense. It supports the narrower statement that,
within the current model-family and target framework, habitat-only and
trout-only explanations are not competitive, and joint trout-plus-climbing
explanations are the most stable calibration result so far.
