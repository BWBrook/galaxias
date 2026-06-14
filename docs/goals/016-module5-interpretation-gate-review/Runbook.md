# Runbook

## Starting Commands

```bash
pwd
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short --branch
git rev-list --left-right --count HEAD...origin/main
```

Expected:

```text
main
08de1abde045809954a63b8df5829bde4c9225b2
## main...origin/main
0 0
```

## Summary Input Check

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

base = Path("data/module5_production_summaries")
meta = json.loads((base / "summary_metadata.json").read_text(encoding="utf-8"))
checks = {
    "qc_all_passed": meta["qc_all_passed"] is True,
    "row_count": meta["row_count"] == 279500,
    "source_intervention_units": meta["source_intervention_units"] == 2795,
    "distinct_proposal_source_keys": meta["distinct_proposal_source_keys"] == 780,
    "raw_not_local": meta["raw_matched_outcomes_copied_locally"] is False,
}
expected_rows = {
    "qc_summary.csv": 12,
    "partition_endpoint_summary.csv": 78,
    "source_intervention_endpoint_summary.csv": 16770,
    "direction_summary.csv": 78,
}
for name, expected in expected_rows.items():
    with (base / name).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    checks[name] = len(rows) == expected
for key, passed in checks.items():
    print(f"{key}={passed}")
if not all(checks.values()):
    raise SystemExit(1)
PY
```

## Optional Remote Audit Rule

Do not inspect raw remote rows unless the compact summaries identify a specific
source/intervention question that cannot be answered from tracked summaries.

If used, remote audit must:

- read from the Goal 014 artifact only;
- write compact audit rows only;
- pull back no raw matched-output table;
- be recorded in `Log.md`.

## Validation Commands

```bash
git diff --check
```

Trailing whitespace:

```bash
rg -n "[ \t]+$" \
  docs/goals/016-module5-interpretation-gate-review \
  docs/module5_interpretation_gate_review.md \
  data/module5_interpretation_audits
```

No matches expected. `rg` exit 1 with no output is pass.

Marker scan:

```bash
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final causal claim|figure|table|caption|abstract|supplement" \
  docs/goals/016-module5-interpretation-gate-review \
  docs/module5_interpretation_gate_review.md \
  data/module5_interpretation_audits
```

Review hits manually. Boundary language is allowed; final-claim or
manuscript-artefact language is not.

## Stage And Publish

```bash
git add \
  docs/goals/016-module5-interpretation-gate-review \
  docs/module5_interpretation_gate_review.md \
  data/module5_interpretation_audits
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
git commit -m "Review Module 5 production interpretation gate"
git push origin main
```

Do not stage raw outputs, caches, figures, manuscript artefacts, or unrelated
files.

## Wake-Up Content

Report:

- final branch, HEAD, status, and pushed commit SHA;
- committed file list;
- summary input verification;
- audit tables and memo created;
- endpoint-priority recommendation;
- partition treatment recommendation;
- source/intervention audit targets;
- wording boundaries;
- unresolved decisions for Barry/Galaxias;
- recommended Goal 017 shape.
