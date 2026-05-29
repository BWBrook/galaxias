# AGENTS.md for `/Users/bwbrook/papers/galaxias`

This repo is the Pedder galaxias modelling and evidence workflow.

## Operating Boundary

- Treat this Mac mini as the local development, validation, and orchestration
  host for this repo.
- Local runs can include setup checks, compile checks, unit tests, document
  generation, tiny deterministic/stochastic smokes, Module 4.5 report
  generation, and other small-to-moderate pandas/Python work.
- Do not run heavy ABC calibration, large simulation batches, big data pulls,
  or long parallel jobs on the Mac mini unless they have first been scoped as
  genuinely local-scale.
- Offload meaningful compute through the remote-compute ladder described in
  `/Users/bwbrook/work/nectar`: usually `deep-server` / `utas-ubuntu` for
  large single-host CPU/RAM work, `alien-wsl` for GPU work that fits dual RTX
  2080s, Nectar for elastic cloud CPU/GPU jobs, and `kunanyi` only for true
  PBS-scale multi-node jobs.
- Use `/Users/bwbrook/work/nectar` for the current machine runbooks, SSH paths,
  PBS conventions, data-placement rules, and smoke-test ladders.

## Project Commands

- `make setup`: create/update the locked `uv` environment.
- `make check`: run portability, compile, and test checks.
- `make smoke`: run only tiny project-native smoke jobs into ignored
  `outputs/`.
- `make clean`: remove generated smoke outputs and Python caches.

## Cross-Platform Rules

- Keep generated source paths repo-relative, not `/home/...`, `/Users/...`, or
  drive-letter paths.
- Keep text files LF-only so the repo behaves the same on WSL Ubuntu, macOS,
  Nectar Ubuntu, and Kunanyi/CentOS.
- Python 3.14 is now the intended local and repo baseline. Historical
  provenance records may still name Python 3.12 when they describe older
  Module 4 runs.
- Use `uv` for environment management. Keep `uv.lock` authoritative.
- Store generated heavy outputs outside git, normally under `outputs/` locally
  or remote scratch/artifact paths described in the Nectar control-plane repo.

## Remote Compute Pattern

- Use Nectar for interactive Linux bring-up, medium remote runs, and staging.
  Codex-managed clones should live under `/data/codex/repos`; outputs and
  caches should stay under `/data/codex/scratch` or `/data/codex/artifacts`.
- Use Kunanyi for PBS-backed production-scale work. Do not run simulations on
  the login node; submit PBS jobs from a scratch working directory.
- Keep project-specific run specs, parameters, and result interpretation in
  this repo. Keep reusable machine/access state in `/Users/bwbrook/work/nectar`.
