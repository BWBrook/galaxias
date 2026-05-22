# Module 4 Observation-Bridge Sensitivity Plan

Last updated: 2026-05-22

## Purpose

Module 4 promotes the Module 3.75 late-observation diagnostics from post-hoc
analysis into first-class calibration variants. Chris is currently away, so we
will proceed with documented best assumptions from the repo literature and
carry the important judgement calls as explicit sensitivity axes rather than
blocking on collaborator input.

The scientific question is:

> Which mechanism-family conclusions survive transparent alternative treatments
> of the late survey/capture evidence?

The operational question is:

> Can we run this as a repeatable calibration grid on `deep-server`, with a
> clear path to `kunanyi` only if the grid expands beyond single-host scale?

## Working Assumptions

Until Chris can comment, use these assumptions:

- Keep the five Tier 1 mechanism families unchanged.
- Keep `CT004` and `CT005` active because they prevent mechanism-poor families
  from becoming misleadingly competitive.
- Treat the 1990-1991 evidence as both contraction and abundance/detection
  evidence, but test whether the `CT007` score should be occupancy-primary.
- Treat the 1996 record as the best endpoint evidence, but test a soft
  terminal-window alternative rather than relying only on exact-year matching.
- Treat 1998-2002 non-detection as strong evidence, but test a lower-detection
  observation bridge because the penalty scales directly with expected capture
  intensity.
- Do not tune target weights to favor a mechanism family.

## Observation-Bridge Variants

| variant | `CT007` contraction | `CT009` endpoint | `CT010` no-detection |
| --- | --- | --- | --- |
| `baseline_current` | 50% occupancy range, 50% Bonnet Bay count | exact 1996 match | current detection bridge |
| `ct007_occupancy_primary` | 75% occupancy range, 25% Bonnet Bay count | exact 1996 match | current detection bridge |
| `ct009_terminal_window_gap3` | baseline | zero penalty for 1992-1996, 3-year late soft gap | current detection bridge |
| `ct010_detection_half` | baseline | exact 1996 match | halve expected detections |
| `late_bridge_soft` | occupancy-primary | terminal-window gap 3 | halve expected detections |

These are deliberately few. They span the main judgement calls without
creating an unstructured tuning exercise.

## Run Tiers

### Tier 0: local smoke

Run on the MacBook or Mac Mini only with tiny settings:

- 2-5 Stage A draws per family;
- 1-2 retained proposals per family;
- 1-2 Stage B replicates;
- all variants if feasible, otherwise one baseline plus one soft variant.

Purpose: verify code paths, manifests, output files, and summary rendering.

### Tier 1: deep-server sensitivity grid

Run on `deep-server` under `tmux`, with repos and outputs under `/data/codex`.

Initial recommended grid:

- variants: all five above;
- seeds: `20260410`, `20260411`, `20260412`;
- Stage A: 1000 draws per family;
- Stage A retention: 100 proposals per family;
- Stage B: 20 historical stochastic replicates;
- final acceptance cap: 50;
- workers: 8-16, depending on observed load.

This mirrors the successful Nectar Module 3.5 tier while keeping the work on a
persistent 64-thread Linux host.

### Tier 2: kunanyi production grid

Escalate to `kunanyi` only if Module 4 expands to a much larger seed/variant
grid or if we need embarrassingly parallel production runs that benefit from
PBS scheduling.

Possible trigger:

- more than about 30 independent calibration runs;
- hundreds of seeds;
- larger Stage A budgets per family;
- repeated production summaries needed for publication-grade robustness.

## Resource Choice

Use:

- MacBook for orchestration, docs, and tiny smoke tests;
- Mac Mini for heavier macOS development loops if the MacBook is being tied up;
- `deep-server` for the first serious Module 4 grid;
- `kunanyi` only after the run definition is stable and the grid is large
  enough to justify PBS;
- Nectar only as a fallback/rehearsal path for this project, because the
  current Nectar VM needs rebuild/alias refresh.

## Expected Outputs

Module 4 should produce:

- per-run raw calibration outputs under `outputs/module4/...` or remote
  `/data/codex/scratch/galaxias/module4/...`;
- a combined variant/seed family summary CSV;
- a combined accepted-family mix CSV;
- a variant winner/ranking CSV;
- a plain-language review document under `docs/`;
- an updated `docs/notes_for_chris.md` section once results are interpreted.

## Success Criteria

The next scientific decision is stronger if:

- `persistent_joint_cause` remains competitive or winning across the combined
  late-observation variants;
- `transient_perfect_storm` remains interpretable rather than disappearing
  solely because of endpoint scoring;
- `habitat_only_null` and `trout_only` remain outside the accepted frontier;
- any `climbing_only` wins can be traced to a transparent observation-bridge
  assumption rather than a hidden scoring artefact.
