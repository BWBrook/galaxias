# Log

## 2026-06-14 - Packet Created By Galaxias

Barry approved proceeding from the frozen Goal 013 baseline to the full
100-replicate Module 5 production execution.

Galaxias created this Goal 014 packet to authorize production execution and
inspection only.

Pre-delegation facts:

- repo: `/Users/bwbrook/papers/galaxias`
- branch: `main`
- HEAD: `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`
- `HEAD...origin/main`: `0 0`
- status before packet: clean
- source SHA for remote execution:
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`
- expected production rows: 279,500
- expected source/intervention units: 2,795
- expected distinct `proposal_source_key` values: 780
- expected replicates: 100
- expected worker count: 32

Boundary:

- production execution and inspection are authorized;
- interpretation, final causal claims, manuscript language, code changes,
  scientific contract changes, generated-output promotion, PR creation, and
  destructive Git actions are not authorized.

Awaiting action-agent execution.

## 2026-06-14 - Action-Agent Attempt Blocked At Remote Clone

### Local Starting Guard

Recorded before remote commands:

- `pwd`: `/Users/bwbrook/papers/galaxias`
- branch: `main`
- HEAD: `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`
- `git status --short --branch`:
  - `## main...origin/main`
  - `?? docs/goals/014-module5-100rep-production-execution/`
- `git rev-list --left-right --count HEAD...origin/main`: `0 0`

This matched the Goal 014 starting-state guard: the repo was at the frozen
Goal 013 baseline with only the untracked Goal 014 packet present.

### Local Plan-Only Preflight

Ran the authorized local plan-only preflight into `/tmp`, not into tracked or
ignored project outputs:

```bash
uv run python scripts/run_module5_25rep_rehearsal.py \
  --plan-only \
  --output-dir /tmp/galaxias-goal014-plan.9U5CSv \
  --run-id goal014-local-plan-only \
  --replicates 100
```

Parsed facts:

- expected row count: 279,500
- source/intervention units: 2,795
- distinct `proposal_source_key` values: 780
- source contexts: 15
- artifact verification rows: 15
- all artifacts verified: true
- artifact source: `local_path`
- total verified bytes: 57,941,680

Partition row counts matched the Goal 014 packet:

- `headline/persistent_joint_cause`: 106,000
- `headline/climbing_only`: 47,000
- `headline/transient_perfect_storm`: 100,000
- `diagnostic_sidecar/climbing_only_no_trout_pressure`: 23,500
- `negative_reference/habitat_only_null`: 1,500
- `negative_reference/trout_only`: 1,500

### Remote Preflight

Remote alias used: `deep-server-ts`. No fallback alias was used.

Run identity selected:

- run ID: `20260614T031037Z-goal014-m5-100rep-production`
- tmux session planned: `galaxias-m5-prod-20260614T031037Z`
- source checkout:
  `/data/codex/repos/galaxias-goal014-m5-100rep-production-20260614T031037Z-goal014-m5-100rep-production`
- scratch:
  `/data/codex/scratch/galaxias/module5_100rep_production_20260614T031037Z-goal014-m5-100rep-production`
- artifact:
  `/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031037Z-goal014-m5-100rep-production`

Remote preflight facts:

- host: `deep-server`
- user: `bwbrook`
- `/data`: 13T total, 4.5T available
- `git`: 2.43.0
- `uv`: 0.11.14
- system Python: 3.12.3
- `tmux`: 3.4

Before clone, the intended source, scratch, and artifact paths were absent.

### Blocker

The fresh pinned checkout could not be created because remote GitHub SSH
authentication failed on `deep-server-ts`:

```text
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

The failure occurred before checkout, before the remote plan-only command,
before any `tmux` session, before production execution, before inspection, and
before checksum generation.

Per the Goal 014 Runbook stop point, I stopped rather than switching clone
method, using a fallback source path, changing target, rsyncing a source tree,
or otherwise repairing the remote checkout without Galaxias authorization.

Post-failure path state:

- source checkout path: absent
- scratch path: exists but contains no files
- artifact path: absent
- `matched_outcomes.csv` for this run ID: absent

No raw matched outcomes were produced or copied, no generated outputs were
promoted, no commit or push was attempted, and no production attribution or
manuscript claim language was created.

## 2026-06-14 - Review Iteration: Bundle Source Transport

Galaxias accepted the stop at the GitHub SSH clone blocker and authorized a
narrow source-transport remedy: create the fresh pinned `deep-server-ts`
checkout from a local Git bundle of the frozen commit, not from GitHub SSH.

The hard production shape remained unchanged:

- source SHA:
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`
- remote target: `deep-server-ts`
- replicates: 100
- workers: 32
- intervention contracts, proposal selection, family treatment, pressure
  semantics, inspection gates, and raw-output policy: unchanged

### Source-Transport Evidence

Local checks before bundling:

- `pwd`: `/Users/bwbrook/papers/galaxias`
- branch: `main`
- HEAD: `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`
- `git status --short --branch`:
  - `## main...origin/main`
  - `?? docs/goals/014-module5-100rep-production-execution/`
- `HEAD...origin/main`: `0 0`
- Goal 014 packet absent from the frozen commit tree: true

The literal raw-SHA bundle command returned Git's empty-bundle guard:

```text
fatal: Refusing to create empty bundle.
```

That occurred before transfer or remote mutation. I then created the bundle
from `HEAD` only after verifying that local `HEAD` exactly matched the frozen
source SHA. This still used the local Git object database rather than the
working tree, so the untracked Goal 014 packet could not enter the remote
execution source.

Final bundle facts:

- local bundle:
  `/tmp/galaxias-ddb8a6de583e85f170f46c9dec9b1246baa6dccc-20260614T031501Z.bundle`
- local bundle SHA-256:
  `0e61facae852b4fe2a6c3a08ab9c9b7a8bbca54358726e13dc225dcd3616d1b9`
- bundle head:
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc HEAD`
- remote bundle:
  `/data/codex/scratch/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/source_bundle/galaxias-ddb8a6de583e85f170f46c9dec9b1246baa6dccc.bundle`
- remote bundle SHA check against the local bundle SHA: passed

Remote checkout:

- source checkout:
  `/data/codex/repos/galaxias-goal014-m5-100rep-production-20260614T031501Z-goal014-m5-100rep-production`
- `git rev-parse HEAD`:
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`
- `git status --short --branch`: `## HEAD (no branch)`
- Goal 014 packet absent from remote execution source: true

A remote `git bundle verify` attempt outside a Git repository failed before
clone with `error: need a repository to verify a bundle`. The same bundle was
then verified successfully from inside the bundle-created checkout before
execution.

### Remote Plan-Only Preflight

Remote preflight facts:

- host: `deep-server`
- user: `bwbrook`
- `/data`: 13T total, 4.5T available
- `git`: 2.43.0
- `uv`: 0.11.14
- system Python: 3.12.3
- `tmux`: 3.4

Remote plan-only preflight used `--replicates 100` and
`--artifact-path-preference remote`.

Parsed facts:

- expected row count: 279,500
- source/intervention units: 2,795
- distinct `proposal_source_key` values: 780
- source contexts: 15
- artifact verification rows: 15
- all artifacts verified: true
- artifact source: `remote_artifact_path`
- total verified bytes: 57,941,680

Partition row counts:

- `headline/persistent_joint_cause`: 106,000
- `headline/climbing_only`: 47,000
- `headline/transient_perfect_storm`: 100,000
- `diagnostic_sidecar/climbing_only_no_trout_pressure`: 23,500
- `negative_reference/habitat_only_null`: 1,500
- `negative_reference/trout_only`: 1,500

### Production Execution

Run identity:

- run ID: `20260614T031501Z-goal014-m5-100rep-production`
- tmux session: `galaxias-m5-prod-20260614T031501Z`
- scratch:
  `/data/codex/scratch/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production`
- artifact:
  `/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production`
- output directory:
  `/data/codex/scratch/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production`

Primary command:

```bash
uv run python scripts/run_module5_25rep_rehearsal.py \
  --output-dir /data/codex/scratch/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production \
  --run-id 20260614T031501Z-goal014-m5-100rep-production \
  --replicates 100 \
  --workers 32 \
  --artifact-path-preference remote
```

Execution facts:

- start UTC: `2026-06-14T03:18:07Z`
- end UTC: `2026-06-14T03:30:51Z`
- duration: 764 seconds
- worker count: 32
- `rehearsal.exit`: 0
- `tmux_command.exit`: 0
- remote source checkout footprint: 326M
- remote scratch footprint: 422M
- remote artifact footprint: 416M

### Inspection And Checksums

Inspection command:

```bash
uv run python scripts/inspect_module5_25rep_rehearsal.py \
  --rehearsal-dir /data/codex/scratch/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production \
  --inspection-dir /data/codex/scratch/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/inspection
```

Inspection facts:

- all checks passed: true
- matched rows: 279,500
- columns: 53
- expected replicates: 100
- replicate IDs: `0..99`
- source/intervention units: 2,795
- distinct `proposal_source_key` values: 780
- source identity: true
- replicate coverage: true
- matched-pair IDs: true
- schema columns: true
- seed mismatches: 0
- partition counts: matched expected counts
- status: `module5_25rep_rehearsal`
- `production_attribution`: false

The status string remains `module5_25rep_rehearsal` because the frozen
accepted runner was reused with `--replicates 100`, as allowed by the Goal 014
packet.

Remote raw matched outcomes:

- path:
  `/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/matched_outcomes.csv`
- size: 435,867,556 bytes
- SHA-256:
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`
- local repo copy: none

The artifact directory includes the run scripts, execution log, run timing,
source-transport note, output plan, artifact verification CSV, provenance JSON,
matched outcomes, inspection summary/checks/report, matched-output checksum,
artifact inventory, and `checksums.sha256`.

Checksum verification:

```bash
sha256sum -c checksums.sha256
```

Result: passed for all listed artifact files.

The artifact inventory was regenerated with a temporary file outside the
artifact tree after an initial in-place inventory listed its temporary file.
Checksums were regenerated and verified after that correction.

### Local Tracked Record

Created compact local report:

- `docs/module5_100rep_production_execution_report.md`

No raw matched outcomes were copied into the local repo. No code, tests,
contracts, Makefile, scripts, generated outputs, or scientific semantics were
changed in this review iteration.

Local publication checks and the exact Goal 014 docs-only commit/push remain
to be run after this log update.

### Local Publication Validation

Docs-only checks after creating the compact report and updating this log:

```bash
git diff --check
```

Result: passed.

```bash
rg -n "[ \t]+$" docs/goals/014-module5-100rep-production-execution docs/module5_100rep_production_execution_report.md
```

Result: no matches.

Marker scan:

```bash
rg -n "production attribution|production-ready|manuscript|causal|claim|outputs/|commit|push|tmux|deep-server" docs/goals/014-module5-100rep-production-execution docs/module5_100rep_production_execution_report.md
```

Result: hits reviewed as expected boundary, path, execution, stop-point, and
commit/push authorization language only.

Exact staged files:

```text
docs/goals/014-module5-100rep-production-execution/Goal.md
docs/goals/014-module5-100rep-production-execution/Log.md
docs/goals/014-module5-100rep-production-execution/Plan.md
docs/goals/014-module5-100rep-production-execution/Runbook.md
docs/module5_100rep_production_execution_report.md
```

Initial staged count after exact-path staging: 5.

Initial cached checks:

- `git diff --cached --check`: passed
- `git diff --cached --stat`:
  `5 files changed, 1300 insertions(+)`
- `git status --short --branch`: only the five intended staged Goal 014
  paths
- `git status --ignored --short outputs .pytest_cache .venv`: ignored
  `.pytest_cache/`, `.venv/`, and `outputs/` only

This log was then restaged exactly before the final cached checks, commit, and
push.
