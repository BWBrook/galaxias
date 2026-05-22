# Compute workflow

## Roles

The MacBook is the control plane for `galaxias`: use it for repo maintenance,
document work, package setup, portability checks, and smoke-sized runs. Heavy
calibration, large simulation batches, or bulky data work should be launched
remotely over SSH.

Use `/Users/bwbrook/work/nectar` as the live operating reference for machine
access, storage locations, PBS submission patterns, and smoke-test ladders.

## Local smoke path

Use the locked Python environment:

```bash
make setup
make check
make smoke
```

`make smoke` deliberately runs tiny jobs only and writes to ignored
`outputs/smoke_*` directories.

## Nectar path

Use Nectar for interactive Linux bring-up, medium remote work, and rehearsal
before larger HPC jobs. Follow the control-plane data-placement rule: project
clones under `/data/codex/repos`, scratch runs under `/data/codex/scratch`, and
kept artifacts under `/data/codex/artifacts`.

Representative command shape:

```bash
ssh nectar-codex 'cd /data/codex/repos/galaxias && make setup && make check'
```

For heavier Module 3 calibration runs, keep outputs in a run-specific remote
scratch or artifact directory rather than the MacBook checkout.

After the Module 3.5 sampler repair, the next useful remote rehearsal is a
larger sensitivity sweep before changing biological target weights:

Hard gate: do not run this on the parked `c3.xsmall` Nectar flavor. From
`/Users/bwbrook/work/nectar`, verify current state with
`scripts/nectar/openstack-status.sh deep-vm`, resize with
`scripts/nectar/resize.sh --yes deep-vm c3.large` for the first sweep, then
confirm SSH/CPU/RAM/disk before starting the run.

```bash
ssh -t nectar-codex 'tmux new -A -s galaxias-m35'
```

Then launch the sweep from inside tmux, keeping the run internals under
`/data/codex/scratch` and durable outputs under `/data/codex/artifacts`. See
`docs/module3_5_sensitivity_plan.md` for the full run command and decision
criteria.

Treat the exact worker count as machine-size dependent: use 4 to 6 workers on
`c3.large`, or 8 to 12 workers on `c3.xlarge` if running multiple seeds or a
larger confirmation.

## Kunanyi path

Use Kunanyi for PBS-backed production-scale work. Keep login-node commands to
staging, environment checks, and `qsub`; do not run simulations directly on the
login node.

Follow the PBS and transfer conventions in `/Users/bwbrook/work/nectar`,
especially the `/scratch/bwbrook` working directory pattern and the validated
jumpbox/Nectar-bastion access notes.

## Portability checks

The project portability check currently verifies:

- no case-insensitive tracked path collisions;
- no Windows-reserved path names or forbidden filename characters;
- no CRLF line endings or UTF-8 BOMs in tracked text files;
- all `data/source_register.csv` local paths are repo-relative and exist.

Run it directly with:

```bash
make portability
```
