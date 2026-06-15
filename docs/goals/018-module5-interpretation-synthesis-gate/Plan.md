# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`.

Treat repo-local instructions and this Goal 018 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, sibling projects, or archive material.

This is an internal synthesis gate. It is not manuscript work, not figure
production, and not a new audit.

## Starting State Guard

Record:

- `pwd`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git status --short --branch`
- `git rev-list --left-right --count HEAD...origin/main`

Expected:

- branch `main`;
- HEAD `cb4e601ff4ff6f04035995306b83f777ff92217a`;
- `HEAD...origin/main` count `0 0`;
- only this Goal 018 packet untracked.

Stop if state differs materially.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- Goal 018 packet files
- `docs/module5_production_summary_review.md`
- `docs/module5_interpretation_gate_review.md`
- `docs/module5_targeted_source_intervention_audit.md`
- `data/module5_production_summaries/summary_metadata.json`
- `data/module5_production_summaries/qc_summary.csv`
- `data/module5_production_summaries/partition_endpoint_summary.csv`
- `data/module5_production_summaries/direction_summary.csv`
- `data/module5_interpretation_audits/endpoint_priority_matrix.csv`
- `data/module5_interpretation_audits/source_intervention_audit_targets.csv`
- `data/module5_interpretation_audits/wording_boundary_matrix.csv`
- `data/module5_source_intervention_audits/audit_metadata.json`
- `data/module5_source_intervention_audits/replicate_distribution_summary.csv`
- `data/module5_source_intervention_audits/negative_subset_sources.csv`
- Goal 014 to Goal 017 logs for provenance only.

## Task 1: Verify Evidence Stack

Run a structured parse check confirming:

- Goal 015 summary metadata still reports:
  - `qc_all_passed=true`;
  - `row_count=279500`;
  - `source_intervention_units=2795`;
  - `distinct_proposal_source_keys=780`;
  - `raw_matched_outcomes_copied_locally=false`.
- Goal 016 endpoint-priority table has 6 rows.
- Goal 016 source/intervention audit targets have 14 rows.
- Goal 017 audit metadata reports:
  - selected IDs `A01`, `A02`, `A03`, `A04`, `A05`, `A10`;
  - `endpoint_bundle_survived_targeted_audit=true`;
  - `raw_matched_outcomes_copied_locally=false`;
  - `broad_raw_extract_created=false`.
- Goal 017 replicate summary has 6 rows.
- Goal 017 negative-subset list has 40 rows.

Stop if any check differs.

## Task 2: Create Decision Tables

Create:

```text
data/module5_interpretation_synthesis/
```

Write these CSV files:

- `synthesis_decision_matrix.csv`
- `endpoint_bundle_evidence.csv`
- `sensitivity_treatment_matrix.csv`
- `future_artifact_recommendations.csv`
- `wording_boundary_decisions.csv`

Required decision rows:

- endpoint bundle accepted for internal synthesis;
- source audit sufficient for synthesis gate;
- primary partition remains headline review basis;
- sensitivity partitions remain robustness/contrast-shape checks;
- `A03` carried as primary no-trout caution;
- `A10` carried as transient-perfect-storm no-trout sensitivity caution;
- extirpation timing remains secondary/audit-selector only;
- diagnostic sidecar and negative references retained as QC context;
- no manuscript/public wording authorized.

Future artefact recommendations may include design notes for:

- endpoint-bundle summary table;
- pressure-removal contrast figure concept;
- source-audit appendix table;
- sensitivity/diagnostic context table.

Do not create those artefacts in this goal.

## Task 3: Write Synthesis Memo

Create:

```text
docs/module5_interpretation_synthesis_gate.md
```

Required structure:

- boundary;
- evidence stack;
- accepted synthesis decisions;
- endpoint bundle decision;
- primary partition treatment;
- sensitivity treatment;
- diagnostic and negative-reference treatment;
- source-audit sufficiency;
- extirpation timing decision;
- future artefact recommendations;
- wording boundaries;
- unresolved decisions for Galaxias/Barry;
- recommended Goal 019.

Tone: decisive, careful, and internal. Do not write manuscript-style prose.

## Task 4: Validate Local Outputs

Run:

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

meta = json.loads(Path("data/module5_production_summaries/summary_metadata.json").read_text(encoding="utf-8"))
assert meta["qc_all_passed"] is True
assert meta["row_count"] == 279500
assert meta["source_intervention_units"] == 2795
assert meta["distinct_proposal_source_keys"] == 780
assert meta["raw_matched_outcomes_copied_locally"] is False

expected_existing = {
    "data/module5_interpretation_audits/endpoint_priority_matrix.csv": 6,
    "data/module5_interpretation_audits/source_intervention_audit_targets.csv": 14,
    "data/module5_source_intervention_audits/replicate_distribution_summary.csv": 6,
    "data/module5_source_intervention_audits/negative_subset_sources.csv": 40,
}
for path, expected in expected_existing.items():
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == expected, (path, len(rows), expected)

audit_meta = json.loads(Path("data/module5_source_intervention_audits/audit_metadata.json").read_text(encoding="utf-8"))
assert audit_meta["selected_audit_ids"] == ["A01", "A02", "A03", "A04", "A05", "A10"]
assert audit_meta["endpoint_bundle_survived_targeted_audit"] is True
assert audit_meta["raw_matched_outcomes_copied_locally"] is False
assert audit_meta["broad_raw_extract_created"] is False

expected_new = {
    "data/module5_interpretation_synthesis/synthesis_decision_matrix.csv": 9,
    "data/module5_interpretation_synthesis/endpoint_bundle_evidence.csv": 3,
    "data/module5_interpretation_synthesis/sensitivity_treatment_matrix.csv": 4,
    "data/module5_interpretation_synthesis/future_artifact_recommendations.csv": 4,
    "data/module5_interpretation_synthesis/wording_boundary_decisions.csv": 8,
}
for path, expected in expected_new.items():
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == expected, (path, len(rows), expected)
print("goal018_synthesis_inputs_outputs_ok")
PY
```

Run:

```bash
git diff --check
rg -n "[ \t]+$" docs/goals/018-module5-interpretation-synthesis-gate docs/module5_interpretation_synthesis_gate.md data/module5_interpretation_synthesis
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final attribution|final causal claim|figure|caption|abstract|supplement" docs/goals/018-module5-interpretation-synthesis-gate docs/module5_interpretation_synthesis_gate.md data/module5_interpretation_synthesis
```

Review marker hits manually. Boundary and future-artefact design language is
allowed. Manuscript-ready or final-claim language is not.

## Task 5: Stage, Commit, Push

Stage only:

```bash
git add \
  docs/goals/018-module5-interpretation-synthesis-gate \
  docs/module5_interpretation_synthesis_gate.md \
  data/module5_interpretation_synthesis
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
docs/goals/018-module5-interpretation-synthesis-gate/Goal.md
docs/goals/018-module5-interpretation-synthesis-gate/Log.md
docs/goals/018-module5-interpretation-synthesis-gate/Plan.md
docs/goals/018-module5-interpretation-synthesis-gate/Runbook.md
docs/module5_interpretation_synthesis_gate.md
data/module5_interpretation_synthesis/synthesis_decision_matrix.csv
data/module5_interpretation_synthesis/endpoint_bundle_evidence.csv
data/module5_interpretation_synthesis/sensitivity_treatment_matrix.csv
data/module5_interpretation_synthesis/future_artifact_recommendations.csv
data/module5_interpretation_synthesis/wording_boundary_decisions.csv
```

Commit:

```bash
git commit -m "Synthesize Module 5 interpretation gate"
```

Push `main`.

## Task 6: Wake-Up

Wake Galaxias with:

- final branch, HEAD, status, and pushed commit SHA;
- committed file list;
- evidence-stack verification;
- decision-table row counts;
- accepted endpoint bundle decision;
- source-audit sufficiency decision;
- primary/sensitivity/diagnostic treatment decisions;
- future artefact recommendations;
- wording boundaries;
- unresolved decisions and recommended Goal 019 shape.

Then wait.
