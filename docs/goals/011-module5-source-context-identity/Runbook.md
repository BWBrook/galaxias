# Runbook

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse --short=12 HEAD
git status --short --branch
```

Stop before editing if dirty state differs from the expected accepted
Goal 005/006/007/008/009/010 surface plus this Goal 011 packet described in
`Plan.md`.

## Source-Identity Count Check

Use a structured CSV check equivalent to:

```bash
python3 - <<'PY'
import csv
from collections import Counter
from pathlib import Path

path = Path("data/module4_5_proposal_set_membership.csv")
rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
accepted = [
    row
    for row in rows
    if row["in_accepted"].strip().lower() == "true"
    and row["family_id"] in {
        "persistent_joint_cause",
        "climbing_only",
        "transient_perfect_storm",
    }
]
proposal_counts = Counter(row["proposal_id"] for row in accepted)
source_keys = Counter(
    (
        row["module4_run_id"],
        row["variant_id"],
        row["seed"],
        row["run_dir_name"],
        row["family_id"],
        row["proposal_id"],
    )
    for row in accepted
)
duplicates = {key: value for key, value in proposal_counts.items() if value > 1}
print(f"accepted_rows={len(accepted)}")
print(f"unique_proposal_ids={len(proposal_counts)}")
print(f"duplicate_proposal_id_count={len(duplicates)}")
print(f"max_reuse={max(duplicates.values()) if duplicates else 0}")
print(f"unique_candidate_source_keys={len(source_keys)}")
print(f"duplicate_source_keys={sum(1 for value in source_keys.values() if value > 1)}")
print("duplicate_examples=" + ",".join(f"{key}:{duplicates[key]}" for key in sorted(duplicates)[:5]))
PY
```

Expected high-level facts:

```text
accepted_rows=750
unique_proposal_ids=246
duplicate_proposal_id_count=158
max_reuse=7
unique_candidate_source_keys=750
duplicate_source_keys=0
```

## RED-First Test Pattern

After writing the source-identity tests but before implementation, run the
focused test command that covers them. Record the failing tests and failure
messages in `Log.md`.

Expected RED failures should be about missing `proposal_source_key`, seed
collisions, matched-pair/run-ID collisions, stale 10-intervention assumptions,
or missing inspector checks. If failures are unrelated, stop and report.

## Focused Validation

Run:

```bash
uv run pytest tests/test_module5_real_proposal_dry_run.py tests/test_module5_dry_run_inspection.py tests/test_module5_counterfactual_contract.py -q
```

Run any new focused source-identity test file, for example:

```bash
uv run pytest tests/test_module5_source_identity.py -q
```

If you choose a different test file name, record the exact command.

## Contract Validation

```bash
uv run python scripts/validate_module5_counterfactual_contract.py
```

The validator should require the new source-identity output fields and the
schema should still validate.

## Smoke Validation

```bash
make module5-dry-run
make module5-dry-run-inspect
```

Expected smoke shape after Goal 008:

- 13 intervention rows;
- 5 replicates;
- 65 matched-outcome rows;
- zero seed mismatches;
- source-identity checks pass;
- inspection `all_checks_passed` true;
- provenance `production_attribution` false.

Generated outputs should remain ignored under:

```text
outputs/module5_dry_run_baseline_current_20260410/
```

Do not copy, promote, stage, or summarize raw matched outcomes beyond compact
validation facts in `Log.md`.

## Full Local Gate

```bash
make fast-check
git diff --check
```

If `make fast-check` fails outside Goal 011 scope, stop and wake Galaxias with
the exact failure. Do not broaden into unrelated repairs.

## Whitespace Scan

Run a direct trailing-whitespace scan over changed files. Adjust the file list
to match actual edits:

```bash
rg -n "[ \t]+$" \
  docs/goals/011-module5-source-context-identity \
  docs/module5_source_identity_contract.md \
  docs/module5_production_run_spec.md \
  data/module5_counterfactual_outcome_schema.csv \
  scripts/validate_module5_counterfactual_contract.py \
  src/galaxias_model/module5_proposals.py \
  src/galaxias_model/module5_counterfactual.py \
  src/galaxias_model/module5_dry_run_inspect.py \
  tests/test_module5_counterfactual_contract.py \
  tests/test_module5_real_proposal_dry_run.py \
  tests/test_module5_dry_run_inspection.py
```

No matches are expected.

## Marker Scan

Run over Goal 011 docs and changed project docs:

```bash
rg -n "production attribution|production-ready|deep-server|tmux|outputs/|manuscript|commit|push" \
  docs/goals/011-module5-source-context-identity \
  docs/module5_source_identity_contract.md \
  docs/module5_production_run_spec.md
```

Review hits manually. They should be boundary, non-claim, local-validation,
artifact-path, stop-point, risk, or future-gate language.

## Commands Not Authorized

Do not run:

```bash
ssh deep-server-ts
ssh utas-ubuntu
tmux
make check
make integration-check
make integration-test
```

Do not run the 25-replicate rehearsal, the 279,500-row production execution,
remote probes, staging, commit, push, PR, publication, or
manuscript/publishing commands.

## Wake-Up Content

Report:

- final branch, HEAD, and status;
- changed local files;
- generated ignored output paths, if any;
- source-identity contract chosen;
- accepted-frontier duplicate-ID facts;
- RED-first evidence;
- validation outcomes;
- smoke row count, proposal count, intervention count, replicate coverage,
  seed mismatch count, and identity-check facts;
- any deviations from the packet;
- risks/questions;
- recommended next-goal shape.
