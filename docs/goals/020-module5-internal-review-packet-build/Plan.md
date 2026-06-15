# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`.

Treat repo-local instructions and this Goal 020 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, sibling projects, or archive material.

This is an internal packet-build goal. It is not manuscript drafting, figure
production, remote auditing, or new simulation work.

## Starting State Guard

Record:

- `pwd`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git status --short --branch`
- `git rev-list --left-right --count HEAD...origin/main`

Expected:

- branch `main`;
- HEAD `e0f39eac798fe83fa48fb8a853dd8b6ee9c6f817`;
- `HEAD...origin/main` count `0 0`;
- only this Goal 020 packet untracked.

Stop if state differs materially.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- Goal 020 packet files
- `docs/module5_results_review_artifact_design.md`
- Goal 019 design CSVs under `data/module5_results_review_design/`
- `docs/module5_interpretation_synthesis_gate.md`
- Goal 018 synthesis CSVs under `data/module5_interpretation_synthesis/`
- `docs/module5_targeted_source_intervention_audit.md`
- Goal 017 audit CSVs under `data/module5_source_intervention_audits/`
- Goal 015 compact summary CSVs under `data/module5_production_summaries/`
- Goal 019 log for provenance context.

## Task 1: Verify Inputs

Run a structured parse check confirming:

- Goal 019 design outputs have expected row counts:
  - `artifact_specifications.csv`: 5 rows;
  - `review_question_checklist.csv`: 10 rows;
  - `data_dependency_matrix.csv`: 12 rows;
  - `wording_guardrails.csv`: 10 rows.
- Goal 018 decision outputs have expected row counts:
  - `synthesis_decision_matrix.csv`: 9 rows;
  - `endpoint_bundle_evidence.csv`: 3 rows;
  - `sensitivity_treatment_matrix.csv`: 4 rows;
  - `wording_boundary_decisions.csv`: 8 rows.
- Goal 017 audit summary has 6 rows.
- Goal 015 metadata reports no local raw matched-output copy.

Stop if any check differs.

## Task 2: Build Internal Review Tables

Create:

```text
data/module5_internal_review_packet/
```

Write:

- `wording_boundary_checklist.csv`
- `endpoint_bundle_summary_grid.csv`
- `source_audit_appendix_grid.csv`
- `pressure_removal_contrast_matrix.csv`
- `sensitivity_diagnostic_context_grid.csv`
- `review_packet_manifest.json`

Every CSV first column must be `packet_status`, and every row in that column
must be `internal_non_display`.

Minimum row counts:

- `wording_boundary_checklist.csv`: at least 8 rows;
- `endpoint_bundle_summary_grid.csv`: at least 3 rows;
- `source_audit_appendix_grid.csv`: exactly 6 rows;
- `pressure_removal_contrast_matrix.csv`: at least 6 rows;
- `sensitivity_diagnostic_context_grid.csv`: at least 4 rows.

The manifest must list every packet table, row count, source inputs, and
`packet_status="internal_non_display"`.

## Task 3: Write Review Packet Memo

Create:

```text
docs/module5_internal_results_review_packet.md
```

Required structure:

- boundary;
- evidence basis;
- packet contents;
- recommended reading order;
- wording boundary checklist use;
- endpoint-bundle summary grid use;
- source-audit appendix grid use;
- pressure-removal contrast matrix use;
- sensitivity/diagnostic context grid use;
- skeptical review questions for Barry/Galaxias;
- stop conditions before stronger wording;
- recommended next step.

The memo should help Barry and Galaxias inspect the packet. It should not
answer the science as a final result.

## Task 4: Validate Local Outputs

Run:

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

expected_inputs = {
    "data/module5_results_review_design/artifact_specifications.csv": 5,
    "data/module5_results_review_design/review_question_checklist.csv": 10,
    "data/module5_results_review_design/data_dependency_matrix.csv": 12,
    "data/module5_results_review_design/wording_guardrails.csv": 10,
    "data/module5_interpretation_synthesis/synthesis_decision_matrix.csv": 9,
    "data/module5_interpretation_synthesis/endpoint_bundle_evidence.csv": 3,
    "data/module5_interpretation_synthesis/sensitivity_treatment_matrix.csv": 4,
    "data/module5_interpretation_synthesis/wording_boundary_decisions.csv": 8,
    "data/module5_source_intervention_audits/replicate_distribution_summary.csv": 6,
}
for path, expected in expected_inputs.items():
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == expected, (path, len(rows), expected)

meta = json.loads(Path("data/module5_production_summaries/summary_metadata.json").read_text(encoding="utf-8"))
assert meta["raw_matched_outcomes_copied_locally"] is False

packet_base = Path("data/module5_internal_review_packet")
expected_packet = {
    "wording_boundary_checklist.csv": 8,
    "endpoint_bundle_summary_grid.csv": 3,
    "source_audit_appendix_grid.csv": 6,
    "pressure_removal_contrast_matrix.csv": 6,
    "sensitivity_diagnostic_context_grid.csv": 4,
}
row_counts = {}
for name, minimum in expected_packet.items():
    with (packet_base / name).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames and reader.fieldnames[0] == "packet_status", name
        rows = list(reader)
    assert len(rows) >= minimum, (name, len(rows), minimum)
    assert all(row["packet_status"] == "internal_non_display" for row in rows), name
    row_counts[name] = len(rows)

manifest = json.loads((packet_base / "review_packet_manifest.json").read_text(encoding="utf-8"))
assert manifest["packet_status"] == "internal_non_display"
for name, count in row_counts.items():
    assert manifest["tables"][name]["row_count"] == count, (name, manifest["tables"][name]["row_count"], count)
print("goal020_internal_review_packet_ok")
PY
```

Run:

```bash
git diff --check
rg -n "[ \t]+$" docs/goals/020-module5-internal-review-packet-build docs/module5_internal_results_review_packet.md data/module5_internal_review_packet
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final attribution|final causal claim|public-facing conclusion|caption|abstract|supplement" docs/goals/020-module5-internal-review-packet-build docs/module5_internal_results_review_packet.md data/module5_internal_review_packet
```

Review marker hits manually. Boundary and guardrail hits are allowed.
Final-claim or manuscript-ready language is not.

## Task 5: Stage, Commit, Push

Stage only:

```bash
git add \
  docs/goals/020-module5-internal-review-packet-build \
  docs/module5_internal_results_review_packet.md \
  data/module5_internal_review_packet
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
docs/goals/020-module5-internal-review-packet-build/Goal.md
docs/goals/020-module5-internal-review-packet-build/Log.md
docs/goals/020-module5-internal-review-packet-build/Plan.md
docs/goals/020-module5-internal-review-packet-build/Runbook.md
docs/module5_internal_results_review_packet.md
data/module5_internal_review_packet/wording_boundary_checklist.csv
data/module5_internal_review_packet/endpoint_bundle_summary_grid.csv
data/module5_internal_review_packet/source_audit_appendix_grid.csv
data/module5_internal_review_packet/pressure_removal_contrast_matrix.csv
data/module5_internal_review_packet/sensitivity_diagnostic_context_grid.csv
data/module5_internal_review_packet/review_packet_manifest.json
```

Commit:

```bash
git commit -m "Build Module 5 internal review packet"
```

Push `main`.

## Task 6: Wake-Up

Wake Galaxias with:

- final branch, HEAD, status, and pushed commit SHA;
- committed file list;
- input verification;
- review packet table row counts;
- manifest facts;
- reading order;
- key skeptical review questions;
- stop conditions before stronger wording;
- deviations and risks;
- recommended next step for Barry/Galaxias review.

Then wait.
