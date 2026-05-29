# Module 3.5 Sensitivity Sweep Plan

## Purpose

The local Module 3.5 pass fixed the proposal-validity problem and showed that
the accepted readiness frontier now contains climbing-only, persistent
joint-cause, and transient perfect-storm proposals. The next sweep should test
whether that mixed accepted set is stable, or whether it is a small-run artifact
of the retained proposal budget and late-history target leverage.

Do not change biological target weights before this sweep. The first goal is to
separate sampling noise, stochastic-run noise, and target-leverage effects.

## What The Sweep Must Show

### 1. Sampler Health

Required:

- `stage_a_valid_rate = 1.0` for all five model families.
- `module3_5_sampler_failures.csv` remains header-only or empty.
- All Module 3 readiness gates remain passable at the larger run size.

Interpretation:

- If sampler failures reappear, fix sampling before interpreting family
  ranking.
- If sampler validity stays clean, any family differences are model/scoring
  behaviour rather than proposal-geometry waste.

### 2. Family Ranking Stability

Primary quantities:

- accepted proposal counts by family;
- top 10, top 25, and top 50 family composition;
- best proposal per family and its distance gap from the global best;
- deterministic-vs-stochastic rank consistency, especially for
  `transient_perfect_storm`;
- sensitivity of rankings to independent master seeds.

Desired evidence before Module 4:

- The accepted set should not be dominated by a single family because of one
  lucky stochastic realization.
- Persistent joint-cause and transient perfect-storm proposals should remain in
  the accepted frontier if their readiness-scale appearance was real.
- If climbing-only still leads, the distance gap should be explicit and stable
  across seeds.

### 3. Late-History Target Leverage

Current local finding:

- `CT007`, `CT009`, and `CT010` dominate the accepted weighted penalties.
- Omitting `CT007`, `CT010`, or the late-terminal block can move the best
  retained proposal toward `persistent_joint_cause`.

Sweep readout required:

- target-level penalty medians for accepted proposals;
- target-omission winners for each target and for the late-terminal block;
- family-specific distributions of `CT007`, `CT009`, and `CT010` penalties;
- whether any mechanism-rich family can reduce late-history penalties without
  losing `CT004`/`CT005` behaviour.

Interpretation:

- If family ranking flips only when late-history targets are omitted, keep
  target weights unchanged but treat late survey/detection modelling as the
  next observation-bridge question.
- If family ranking is stable even under late-target omissions, then the
  mechanism ranking is more robust.

### 4. Mechanism Parameter Plausibility

Inspect accepted and near-accepted proposals for:

- trout piscivory and vulnerability: `PR017`, `PR018`, `PR020`, `PR021`;
- climbing invasion timing and impact: `PR024`, `PR027`, `PR028`;
- trophic upsurge: `PR029`, `PR031`;
- habitat/refuge protection: `PR033`, `PR034`;
- observation bridge and count scale: `PR035`, `PR036`, `PR037`, `PR038`,
  `PR039`, `PR040`.

Red flags:

- accepted fits require implausibly extreme observation scaling;
- mechanism-rich proposals fit only through very delayed habitat penalties;
- one family wins entirely by exploiting nuisance parameters.

### 5. Module 4 Go/No-Go

Proceed to Module 4 posterior/counterfactual summaries only if:

- sampler validity remains clean;
- accepted proposal sets are not seed-fragile;
- accepted families and target-leverage behaviour are understood;
- late-history target dominance is quantified rather than surprising;
- enough accepted mechanism-rich proposals exist to support counterfactual
  comparisons.

If these are not met, the next step is not Module 4. It is an observation-bridge
Module 3.75 focused on `CT007`/`CT009`/`CT010`.

## Compute Plan

### Local Mac mini

Use for local validation only:

- `make check`;
- `make smoke`;
- report inspection;
- small code fixes.

Do not run the sensitivity sweep locally.

### Nectar: First Choice

Use Nectar for the first larger sweep because the workload is ordinary
multi-process Python, the artifacts are modest, and we want interactive access
to inspect partial logs if it runs long. Because this may run overnight, run it
inside `tmux`.

Do not launch the sweep on the parked VM. The current Nectar runbook records the
idle state as `c3.xsmall` with 1 vCPU and 2 GiB RAM; that is for access checks,
not meaningful calibration. Resize first, verify the guest, and only then start
the tmux session.

Recommended flavor:

- first 1000-draw sensitivity sweep: `c3.large` (8 vCPU, 16 GiB RAM), using
  4 to 6 workers;
- three-seed or 2500-draw confirmation: `c3.xlarge` (16 vCPU, 32 GiB RAM),
  using 8 to 12 workers;
- `c3.3xlarge` is probably unnecessary for this Python workflow unless a
  later profiling run shows poor walltime at `c3.xlarge`.

Resize gate from the Mac mini control-plane:

```bash
cd /Users/bwbrook/work/nectar
scripts/nectar/openstack-status.sh deep-vm
scripts/nectar/flavors.sh '^c3\.'
scripts/nectar/resize.sh --yes deep-vm c3.large
scripts/check-access.sh nectar-codex
ssh nectar-codex 'nproc; free -h; df -hT / /data; systemctl --failed --no-pager'
```

If SSH is briefly unavailable after resize, follow the Nectar VM runbook: check
OpenStack status/console first, then verify `ssh.service` rather than treating
it as an SSH-key problem.

Keep:

- repo clone under `/data/codex/repos/galaxias`;
- transient run internals under `/data/codex/scratch/galaxias`;
- kept CSV/report/log artifacts under `/data/codex/artifacts/galaxias`.

Primary Nectar run:

```bash
ssh -t nectar-codex 'tmux new -A -s galaxias-m35'
```

Inside tmux:

```bash
set -euo pipefail

cd /data/codex/repos/galaxias
git fetch origin
git status --short --branch
uv sync --locked --python 3.14
make check

RUN_ID=module3_5_sensitivity_$(date -u +%Y%m%dT%H%M%SZ)
SCRATCH=/data/codex/scratch/galaxias/$RUN_ID
ARTIFACTS=/data/codex/artifacts/galaxias/$RUN_ID
mkdir -p "$SCRATCH" "$ARTIFACTS/logs"

uv run python scripts/review_module3_5_diagnostics.py \
  --stage-a-draws-per-family 1000 \
  --stage-a-keep-per-family 100 \
  --stage-b-historical-replicates 20 \
  --final-acceptance-cap 50 \
  --workers 4 \
  --batch-size 100 \
  --seed 20260410 \
  --output-dir "$SCRATCH/run" \
  --output-root "$ARTIFACTS" \
  2>&1 | tee "$ARTIFACTS/logs/module3_5_sensitivity.log"
```

Detach safely with `Ctrl-b d`. Reattach later:

```bash
ssh -t nectar-codex 'tmux attach -t galaxias-m35'
```

If the primary run finishes comfortably, run two additional seeds in the same
tmux session with separate `RUN_ID`s:

- `20260411`
- `20260412`

This gives a first seed-stability check without needing PBS.

After the Nectar run is validated and artifacts are safely recorded or copied
back, park the VM back down if no further remote work is queued:

```bash
cd /Users/bwbrook/work/nectar
scripts/nectar/resize.sh --yes deep-vm c3.xsmall
scripts/nectar/openstack-status.sh deep-vm
```

### Kunanyi: Escalation Path

Use `kunanyi` if either:

- Nectar is still parked and cannot be resized promptly;
- the 1000-draw Nectar sweep looks likely to become an overnighter-plus;
- we decide to run a grid of seeds and target-block variants.

Kunanyi should be PBS-only:

- stage under `/scratch/bwbrook/galaxias`;
- submit from the login node, but run no simulations there;
- use PBS completion mail and preserve stdout/stderr artifacts;
- use one PBS job per seed or a small PBS array if convenient.

Candidate PBS scale:

- 3 seeds;
- 1000 to 2500 Stage A draws per family;
- 100 to 200 retained proposals per family;
- 20 to 50 Stage B replicates;
- one single-node job per seed is probably enough unless profiling says
  otherwise.

### Decision Rule After Nectar

Use Nectar results to choose the next branch:

- Stable accepted family mix and interpretable target leverage: prepare Module 4.
- Mixed family rankings but stable target-leverage story: run a larger
  Kunanyi/PBS confirmation.
- Rankings hinge on `CT007`/`CT010`: build Module 3.75 observation-bridge
  diagnostics before Module 4.
- Rankings hinge on nuisance parameters: tighten or re-express nuisance priors
  before Module 4.
