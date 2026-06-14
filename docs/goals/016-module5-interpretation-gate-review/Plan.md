# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`, except for optional
read-only remote inspection on `deep-server-ts` if the compact summaries reveal
a specific source/intervention audit need.

Treat repo-local instructions and this Goal 016 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, sibling projects, or archive material.

This is an interpretation-gate review. It is not manuscript work.

## Starting State Guard

Record:

- `pwd`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git status --short --branch`
- `git rev-list --left-right --count HEAD...origin/main`

Expected:

- branch `main`;
- HEAD `08de1abde045809954a63b8df5829bde4c9225b2`;
- `HEAD...origin/main` count `0 0`;
- only this Goal 016 packet untracked.

Stop if state differs materially.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- Goal 016 packet files
- `docs/module5_production_summary_review.md`
- `docs/module5_100rep_production_execution_report.md`
- `docs/goals/014-module5-100rep-production-execution/Log.md`
- `docs/goals/015-module5-production-summary-review/Log.md`
- `data/module5_production_summaries/summary_metadata.json`
- `data/module5_production_summaries/qc_summary.csv`
- `data/module5_production_summaries/partition_endpoint_summary.csv`
- `data/module5_production_summaries/source_intervention_endpoint_summary.csv`
- `data/module5_production_summaries/direction_summary.csv`

## Task 1: Verify Summary Inputs

Run a structured parse check that confirms:

- `summary_metadata.json` reports `qc_all_passed=true`;
- row count is 279,500;
- source/intervention units are 2,795;
- distinct source keys are 780;
- raw matched outcomes were not copied locally;
- required summary CSV files parse and have expected row counts:
  - `qc_summary.csv`: 12 rows;
  - `partition_endpoint_summary.csv`: 78 rows;
  - `source_intervention_endpoint_summary.csv`: 16,770 rows;
  - `direction_summary.csv`: 78 rows.

Stop if any check differs.

## Task 2: Build Audit Tables

Create compact audit tables under:

```text
data/module5_interpretation_audits/
```

Suggested tables:

- `endpoint_priority_matrix.csv`
  - endpoint;
  - interpretive role;
  - strengths;
  - weaknesses;
  - recommended review priority;
  - reason.
- `source_intervention_audit_targets.csv`
  - partition;
  - family;
  - intervention;
  - endpoint;
  - source key or source count;
  - trigger;
  - recommended audit action.
- `wording_boundary_matrix.csv`
  - topic;
  - allowed wording;
  - not-yet wording;
  - reason.

Use compact summaries only unless a specific remote source/intervention audit
is needed. If remote audit is needed, pull back only the compact audit rows
needed to support the table and record the exact remote command.

## Task 3: Write Interpretation-Gate Memo

Create:

```text
docs/module5_interpretation_gate_review.md
```

Required structure:

- boundary;
- evidence basis;
- QC recap;
- endpoint priority;
- primary partition readiness;
- sensitivity partition treatment;
- diagnostic sidecar and negative-reference treatment;
- source/intervention audit targets;
- wording boundaries;
- decisions for Barry/Galaxias;
- recommended next goal.

Keep tone analytical and provisional. Do not write results-section prose.

## Task 4: Validate Language And Files

Run:

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

base = Path("data/module5_production_summaries")
meta = json.loads((base / "summary_metadata.json").read_text(encoding="utf-8"))
assert meta["qc_all_passed"] is True
assert meta["row_count"] == 279500
assert meta["source_intervention_units"] == 2795
assert meta["distinct_proposal_source_keys"] == 780
assert meta["raw_matched_outcomes_copied_locally"] is False
expected = {
    "qc_summary.csv": 12,
    "partition_endpoint_summary.csv": 78,
    "source_intervention_endpoint_summary.csv": 16770,
    "direction_summary.csv": 78,
}
for name, count in expected.items():
    with (base / name).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == count, (name, len(rows), count)
print("summary_inputs_ok")
PY
git diff --check
rg -n "[ \t]+$" docs/goals/016-module5-interpretation-gate-review docs/module5_interpretation_gate_review.md data/module5_interpretation_audits
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final causal claim" docs/goals/016-module5-interpretation-gate-review docs/module5_interpretation_gate_review.md data/module5_interpretation_audits
```

Review marker hits manually. Boundary warnings are allowed. Final-claim prose
is not.

## Task 5: Stage, Commit, Push

Stage only:

```bash
git add \
  docs/goals/016-module5-interpretation-gate-review \
  docs/module5_interpretation_gate_review.md \
  data/module5_interpretation_audits
```

Verify:

```bash
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
```

Expected staged surface:

```text
docs/goals/016-module5-interpretation-gate-review/Goal.md
docs/goals/016-module5-interpretation-gate-review/Log.md
docs/goals/016-module5-interpretation-gate-review/Plan.md
docs/goals/016-module5-interpretation-gate-review/Runbook.md
docs/module5_interpretation_gate_review.md
data/module5_interpretation_audits/endpoint_priority_matrix.csv
data/module5_interpretation_audits/source_intervention_audit_targets.csv
data/module5_interpretation_audits/wording_boundary_matrix.csv
```

Commit:

```bash
git commit -m "Review Module 5 production interpretation gate"
```

Push `main`.

## Task 6: Wake-Up

Wake Galaxias with:

- final branch, HEAD, status, and pushed commit SHA;
- files committed;
- summary input verification;
- audit tables created;
- key interpretation-gate recommendations;
- wording boundaries;
- unresolved questions for Barry/Galaxias;
- deviations and risks;
- recommended Goal 017 shape.

Then wait.
