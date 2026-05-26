# Mac Mini Handover: Pedder Galaxias Workflow

Date: 2026-05-26

This note captures the working context for moving the Pedder galaxias repo from
the MacBook to the always-on Mac Mini control plane.

## Why The Handover Is Happening

The MacBook is a good local smoke-test and review machine, but it is often
closed and therefore unreliable for continuing Codex work from the phone app.
The Mac Mini is always on, reachable over Tailscale as `dev-box-ts`, and should
now become the normal macOS control-plane host for this repo.

The Mac Mini is still not the heavy compute target. Use it for interactive
development, docs, light pandas work, smokes, and orchestration. Use
`deep-server` for serious single-host Linux runs, and reserve `kunanyi` for
large PBS-scale sweeps.

## Current Scientific State

Modules 1 through 4 have been completed to the current standard.

The strongest current result is from Module 4:

- `persistent_joint_cause` won 12 of 15 observation-bridge variant/seed runs.
- It won all baseline runs and all combined soft late-observation runs.
- `climbing_only` won 3 of 15 runs, only under single-axis late-observation
  relaxations.
- `transient_perfect_storm` remained represented in accepted proposal mixes,
  but did not win target-sum ranking in the Module 4 grid.
- `habitat_only_null` and `trout_only` had zero accepted proposals across the
  Module 4 sensitivity grid.

This is a strong calibration result, but not yet a final causal attribution.
The next major analysis must test whether the surviving mechanism-rich
families are biologically coherent rather than being carried mainly by
late-observation nuisance terms.

## Must-Read Files For The Next Session

Read these first on the Mac Mini:

1. `AGENTS.md`
2. `docs/mac_mini_handover_2026-05-26.md`
3. `docs/galaxias_repo_audit_module45_feedback.md`
4. `docs/gated_action_plan_module4_5_and_beyond.md`
5. `docs/module4_5_mechanism_interpretation_plan.md`
6. `docs/module4_observation_sensitivity_review.md`
7. `docs/notes_for_chris.md`

The audit file should be treated as review input, not mutable working prose.
Use separate planning or implementation docs for responses to the audit.

## Current Planning State

The current roadmap is:

- Gate 0: feedback intake and plan freeze.
- Gate 1: reproducibility and repo-health foundation.
- Gate 2: Module 4.5 design lock.
- Gate 3: Module 4.5 implementation.
- Gate 4: Module 4.5 diagnostic execution.
- Gate 4.75: conditional refinement if nuisance or target issues block
  counterfactuals.
- Gate 5: matched counterfactual attribution.
- Gate 5.5: present-day coexistence envelope.
- Gate 6: robustness and prior/target sensitivity.
- Gate 7: manuscript and communication package.
- Gate 8: genetics and identity sidecar.

Do not begin Module 5 until Gate 4 passes.

## Immediate Next Task

After verifying the Mac Mini migration, the recommended next task is Gate 1A:
create the compact Module 4 raw artefact manifest.

That manifest should record, for every Module 4 variant/seed run:

- local and remote paths;
- file sizes and hashes;
- source command;
- run date;
- Git commit;
- Python version;
- seed and observation-bridge variant;
- presence of `proposal_summary.csv.gz`, `parameter_values.csv.gz`,
  `target_scores.csv.gz`, `accepted_proposals.csv`, `family_summary.csv`, and
  `run_manifest.json`.

Suggested tracked output:

- `data/module4_raw_artifact_manifest.csv`

## Artifact Locations

On the MacBook before migration:

- ignored local artifacts: `outputs/`
- Module 4 local mirror:
  `outputs/remote/module4_observation_sensitivity_20260522T101942Z`

On `deep-server`:

- Module 4 scratch:
  `/data/codex/scratch/galaxias/module4_observation_sensitivity_20260522T101942Z`
- Module 4 artifact:
  `/data/codex/artifacts/galaxias/module4_observation_sensitivity_20260522T101942Z`

After migration, the Mini should have the same `outputs/` tree copied into:

- `/Users/bwbrook/papers/galaxias/outputs`

The raw artifacts are ignored by git. Do not assume a fresh clone has them
unless they have been copied or re-fetched from `deep-server`.

## Operating Protocols

Use the Mac Mini for:

- Codex phone-app continuity;
- repo maintenance;
- docs;
- small smoke tests;
- light-to-medium pandas/report generation;
- orchestration of remote jobs.

Use `deep-server` for:

- full Module 4.5 extraction if local joins or trajectory regeneration are
  slow;
- serious single-host Linux runs;
- staged remote artifacts under `/data/codex`.

Use `kunanyi` only for:

- large PBS-backed sweeps;
- many independent calibration jobs;
- multi-node or queue-managed production workloads.

From home, the preferred Kunanyi path is:

`Mac Mini -> Tailscale deep-server-ts / utas-ubuntu -> TPAC jumpbox -> kunanyi`

Do not keep retrying direct home-network SSH to the TPAC jumpbox if it times
out.

## Validation Commands

Routine local checks:

```bash
make check
git diff --check
```

Module 4 smoke:

```bash
make module4-smoke
```

Current expected test count before Gate 1 test-tier changes:

- `60 passed`

## Notes For The Next Codex Session

- Start by checking `git status --short --branch`.
- Confirm the Mini checkout is clean and at `origin/main`.
- Confirm `outputs/remote/module4_observation_sensitivity_20260522T101942Z`
  exists if working on Module 4.5.
- Keep generated heavy outputs out of git.
- Keep `docs/notes_for_chris.md` updated after each completed module or
  diagnostic gate.
- End every module report with the recommended next task.

