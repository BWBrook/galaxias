# Runbook

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short=12 HEAD
git status --short --branch
```

Stop before editing if the dirty state is not the accepted Goal
005/006/007/008/009/010/011 surface plus this Goal 012 packet.

## Rehearsal Count Check

Run a structured CSV check equivalent to:

```bash
python3 - <<'PY'
import csv
from collections import Counter
from pathlib import Path

root = Path(".")
membership = list(csv.DictReader(
    (root / "data/module4_5_proposal_set_membership.csv").open(
        newline="", encoding="utf-8"
    )
))
interventions = list(csv.DictReader(
    (root / "data/module5_counterfactual_interventions.csv").open(
        newline="", encoding="utf-8"
    )
))
manifest = list(csv.DictReader(
    (root / "data/module4_raw_artifact_manifest.csv").open(
        newline="", encoding="utf-8"
    )
))

def as_bool(value):
    return str(value).strip().lower() == "true"

accepted = [
    row for row in membership
    if as_bool(row["in_accepted"])
    and row["family_id"] in {
        "persistent_joint_cause",
        "climbing_only",
        "transient_perfect_storm",
    }
]
winners = [row for row in membership if as_bool(row["in_family_winners"])]
contexts = {
    (row["module4_run_id"], row["variant_id"], row["seed"], row["run_dir_name"])
    for row in accepted + winners
}
param_contexts = {
    (row["run_id"], row["variant_id"], row["seed"], row["run_dir_name"])
    for row in manifest
    if row["file_role"] == "parameter_values"
}

print("accepted=" + str(len(accepted)))
print("accepted_by_family=" + str(dict(Counter(row["family_id"] for row in accepted))))
print("family_winners_by_family=" + str(dict(Counter(row["family_id"] for row in winners))))
print("source_contexts=" + str(len(contexts)))
print("missing_parameter_contexts=" + str(len(contexts - param_contexts)))
print("interventions_by_family=" + str(dict(Counter(row["family_id"] for row in interventions))))

replicates = 25
row_total = (
    265 * 4 * replicates
    + 235 * 2 * replicates
    + 250 * 4 * replicates
    + 235 * 1 * replicates
    + 15 * 1 * replicates
    + 15 * 1 * replicates
)
print("expected_rehearsal_rows=" + str(row_total))
PY
```

Expected high-level facts:

```text
accepted=750
accepted_by_family={'persistent_joint_cause': 265, 'climbing_only': 235, 'transient_perfect_storm': 250}
source_contexts=15
missing_parameter_contexts=0
expected_rehearsal_rows=69875
```

## Local Validation Commands

Run the new focused rehearsal tests. Record the exact command, for example:

```bash
uv run pytest tests/test_module5_production_rehearsal.py -q
```

Run the affected existing focused tests:

```bash
uv run pytest \
  tests/test_module5_source_identity.py \
  tests/test_module5_real_proposal_dry_run.py \
  tests/test_module5_dry_run_inspection.py \
  tests/test_module5_counterfactual_contract.py \
  -q
```

Run contract and smoke validation:

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
make module5-dry-run
make module5-dry-run-inspect
make fast-check
git diff --check
```

If `make module5-dry-run` regenerates ignored outputs under
`outputs/module5_dry_run_baseline_current_20260410/`, leave them ignored and
report compact facts only.

## Remote Preflight Pattern

Use `deep-server-ts` first:

```bash
ssh deep-server-ts 'hostname; whoami; df -h /data; uv --version; python3 --version; tmux -V'
```

If `deep-server-ts` fails, try `utas-ubuntu` only as the approved fallback and
record the exact failure and fallback reason.

Recommended run variables:

```bash
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="${RUN_STAMP}-goal012-m5-25rep-rehearsal"
SESSION="galaxias-m5-25rep-${RUN_STAMP}"
REMOTE_REPO="/data/codex/repos/galaxias-goal012-m5-25rep-rehearsal-${RUN_ID}"
REMOTE_SCRATCH="/data/codex/scratch/galaxias/module5_25rep_rehearsal_${RUN_ID}"
REMOTE_ARTIFACT="/data/codex/artifacts/galaxias/module5_25rep_rehearsal_${RUN_ID}"
```

Create the remote source mirror from the local accepted dirty checkout. Use a
transport pattern equivalent to `rsync` and exclude only bulky/cache paths not
needed for execution, such as:

```text
.venv/
.pytest_cache/
.ruff_cache/
__pycache__/
outputs/
```

Do not create a new Git branch, commit, or push.

## Artifact Verification Pattern

Before execution, verify the 15 required `parameter_values` artifacts against
`data/module4_raw_artifact_manifest.csv`.

For each required source context:

- locate exactly one manifest row with `file_role == parameter_values`;
- verify the remote artifact if `remote_artifact_path` exists;
- otherwise transfer the `local_path` artifact and verify size and SHA-256;
- make the verified artifact available at the path expected by the runner or
  record the explicit path map in provenance.

Stop if any artifact is missing or hash-mismatched.

## Remote Execution Pattern

Run the rehearsal inside `tmux` and capture logs.

The exact command is implementation-dependent, but it must include:

- source selection from the real tracked CSV contracts;
- 25 replicates;
- the partition layout in `Goal.md`;
- scratch and artifact output paths under the Goal 012 run ID;
- production-attribution flag false or equivalent non-claim status;
- provenance output;
- inspection output.

If the runner does not return promptly, leave the tmux session running and
report enough information in the wake-up only if blocked. Otherwise, complete
the run and inspection before waking Galaxias.

## Inspection Pass Criteria

The inspection summary must report:

```text
row_count=69875
expected_replicates=25
replicate_ids=0..24
source_intervention_units=2795
distinct_proposal_source_keys=780
seed_mismatches=0
source_identity=true
replicate_coverage=true
all_checks_passed=true
production_attribution=false
```

Partition rows must be:

```text
headline/persistent_joint_cause=26500
headline/climbing_only=11750
headline/transient_perfect_storm=25000
diagnostic_sidecar/climbing_only_no_trout_pressure=5875
negative_reference/habitat_only_null=375
negative_reference/trout_only=375
```

Record output column count and schema validation result. The expected current
post-Goal011 matched-outcome schema has 53 columns, but if code changes alter
the schema deliberately, explain and validate the new contract.

## Compact Pull-Back Policy

Allowed local tracked pull-back:

- `docs/module5_25rep_rehearsal_report.md`;
- this goal `Log.md`;
- source code, tests, scripts, and docs needed to reproduce or inspect the
  rehearsal.

Allowed local untracked or ignored pull-back only if needed:

- compact JSON or CSV summaries small enough to support the tracked report.

Not allowed:

- raw `matched_outcomes.csv` in tracked files;
- broad remote artifact copies into the local repo;
- generated-output promotion;
- staging, commit, push, PR, or publication.

## Whitespace Scan

Run a direct trailing-whitespace scan over changed files. Adjust the list to
match actual edits:

```bash
rg -n "[ \t]+$" \
  docs/goals/012-module5-25rep-production-rehearsal \
  docs/module5_25rep_rehearsal_report.md \
  docs/module5_production_run_spec.md \
  scripts \
  src/galaxias_model \
  tests
```

No matches are expected in files changed by this goal. If broad directories
include pre-existing matches outside the changed files, rerun on exact changed
files and record that distinction.

## Marker Scan

Run over Goal 012 docs and changed project docs:

```bash
rg -n "production attribution|production-ready|deep-server|tmux|outputs/|manuscript|commit|push|production run" \
  docs/goals/012-module5-25rep-production-rehearsal \
  docs/module5_25rep_rehearsal_report.md \
  docs/module5_production_run_spec.md \
  docs/module5_remote_smoke_preflight.md \
  docs/module5_source_identity_contract.md
```

Review hits manually. They should be boundary, non-claim, remote-rehearsal,
artifact-path, stop-point, risk, or future-gate language.

## Commands Not Authorized

Do not run the 100-replicate production execution.

Do not run staging, commit, push, PR, publication, manuscript, or claim-making
commands.

Do not alter the tracked intervention matrix, pressure-removal semantics,
proposal-source selection policy, family weighting, or the 25-replicate
rehearsal count without waking Galaxias first.

## Wake-Up Content

Report:

- final branch, HEAD, and status;
- changed local files;
- generated ignored local outputs, if any;
- remote alias, run ID, tmux session, source mirror, scratch path, and artifact
  path;
- artifact verification summary;
- local validation outcomes;
- remote execution outcome and duration;
- rehearsal row counts by partition and total;
- source identity, replicate coverage, seed-pairing, matched-pair, and schema
  inspection facts;
- artifact inventory and checksums;
- deviations from the packet;
- risks/questions;
- recommended next-goal shape.
