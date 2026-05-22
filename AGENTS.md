# AGENTS.md for `/Users/bwbrook/papers/galaxias`

This repo is the Pedder galaxias modelling and evidence workflow.

## Operating Boundary

- Treat this MacBook as a control plane and smoke-test host only.
- Local runs should stay small: setup checks, compile checks, unit tests, tiny
  deterministic/stochastic smokes, document generation, and repo maintenance.
- Do not run heavy ABC calibration, large simulation batches, big data pulls,
  or long parallel jobs on the MacBook.
- Offload meaningful compute through SSH to `nectar`/`nectar-codex` or
  `kunanyi` as appropriate.
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
- Preserve Python 3.12 compatibility as the shared baseline; newer local Python
  versions are useful for extra checks but should not become required without
  a deliberate decision.
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
