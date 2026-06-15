# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`.

Treat repo-local instructions and this Goal 019 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, sibling projects, or archive material.

This is an internal artefact-design goal. It is not artefact production,
manuscript drafting, remote auditing, or new simulation work.

## Starting State Guard

Record:

- `pwd`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git status --short --branch`
- `git rev-list --left-right --count HEAD...origin/main`

Expected:

- branch `main`;
- HEAD `922b8e84b22c072b6559adf2c969cdbcc4185eb4`;
- `HEAD...origin/main` count `0 0`;
- only this Goal 019 packet untracked.

Stop if state differs materially.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- Goal 019 packet files
- `docs/module5_interpretation_synthesis_gate.md`
- `data/module5_interpretation_synthesis/synthesis_decision_matrix.csv`
- `data/module5_interpretation_synthesis/endpoint_bundle_evidence.csv`
- `data/module5_interpretation_synthesis/sensitivity_treatment_matrix.csv`
- `data/module5_interpretation_synthesis/future_artifact_recommendations.csv`
- `data/module5_interpretation_synthesis/wording_boundary_decisions.csv`
- `docs/module5_targeted_source_intervention_audit.md`
- `data/module5_source_intervention_audits/replicate_distribution_summary.csv`
- `data/module5_source_intervention_audits/negative_subset_sources.csv`
- `docs/module5_production_summary_review.md`
- `data/module5_production_summaries/partition_endpoint_summary.csv`
- `data/module5_production_summaries/direction_summary.csv`
- Goal 018 log for provenance context.

## Task 1: Verify Design Inputs

Run a structured parse check confirming:

- Goal 018 decision outputs have expected row counts:
  - `synthesis_decision_matrix.csv`: 9 rows;
  - `endpoint_bundle_evidence.csv`: 3 rows;
  - `sensitivity_treatment_matrix.csv`: 4 rows;
  - `future_artifact_recommendations.csv`: 4 rows;
  - `wording_boundary_decisions.csv`: 8 rows.
- Goal 017 audit summary has 6 rows.
- Goal 017 negative subset list has 40 rows.
- Goal 015 compact summary metadata still reports no local raw matched-output
  copy.

Stop if any check differs.

## Task 2: Create Design Tables

Create:

```text
data/module5_results_review_design/
```

Write these CSV files:

- `artifact_specifications.csv`
- `review_question_checklist.csv`
- `data_dependency_matrix.csv`
- `wording_guardrails.csv`

Minimum row counts:

- `artifact_specifications.csv`: 5 rows, one for each artefact design named in
  `Goal.md`;
- `review_question_checklist.csv`: at least 8 rows;
- `data_dependency_matrix.csv`: at least 8 rows;
- `wording_guardrails.csv`: at least 8 rows.

Each artefact specification should include:

- artefact ID;
- artefact name;
- purpose;
- primary inputs;
- proposed structure;
- key caveats;
- allowed output status;
- stop condition.

Do not create polished figures or display tables.

## Task 3: Optional Internal Scaffolds

Optional scaffold files are allowed only if they clarify a design.

Rules:

- filename must begin with `internal_scaffold_`;
- first column must be `scaffold_status`;
- every row must have `scaffold_status=internal_non_display`;
- scaffold must not be manuscript-ready or public-facing.

If scaffolds are not needed, record that decision in the memo and log.

## Task 4: Write Design Memo

Create:

```text
docs/module5_results_review_artifact_design.md
```

Required structure:

- boundary;
- evidence basis;
- Goal 018 decisions carried forward;
- artefact design summary;
- endpoint-bundle summary grid specification;
- pressure-removal contrast visual concept specification;
- source-audit appendix grid specification;
- sensitivity/diagnostic context grid specification;
- wording boundary checklist specification;
- construction order recommendation;
- review questions for Barry/Galaxias;
- validation expectations for a future artefact-building goal;
- recommended Goal 020.

Keep the memo concise and specification-oriented.

## Task 5: Validate Local Outputs

Run:

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

expected_inputs = {
    "data/module5_interpretation_synthesis/synthesis_decision_matrix.csv": 9,
    "data/module5_interpretation_synthesis/endpoint_bundle_evidence.csv": 3,
    "data/module5_interpretation_synthesis/sensitivity_treatment_matrix.csv": 4,
    "data/module5_interpretation_synthesis/future_artifact_recommendations.csv": 4,
    "data/module5_interpretation_synthesis/wording_boundary_decisions.csv": 8,
    "data/module5_source_intervention_audits/replicate_distribution_summary.csv": 6,
    "data/module5_source_intervention_audits/negative_subset_sources.csv": 40,
}
for path, expected in expected_inputs.items():
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == expected, (path, len(rows), expected)

meta = json.loads(Path("data/module5_production_summaries/summary_metadata.json").read_text(encoding="utf-8"))
assert meta["raw_matched_outcomes_copied_locally"] is False

expected_outputs_min = {
    "data/module5_results_review_design/artifact_specifications.csv": 5,
    "data/module5_results_review_design/review_question_checklist.csv": 8,
    "data/module5_results_review_design/data_dependency_matrix.csv": 8,
    "data/module5_results_review_design/wording_guardrails.csv": 8,
}
for path, minimum in expected_outputs_min.items():
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) >= minimum, (path, len(rows), minimum)

for path in Path("data/module5_results_review_design").glob("internal_scaffold_*.csv"):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames and reader.fieldnames[0] == "scaffold_status", path
        rows = list(reader)
    assert rows, path
    assert all(row["scaffold_status"] == "internal_non_display" for row in rows), path
print("goal019_design_inputs_outputs_ok")
PY
```

Run:

```bash
git diff --check
rg -n "[ \t]+$" docs/goals/019-module5-results-review-artifact-design docs/module5_results_review_artifact_design.md data/module5_results_review_design
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final attribution|final causal claim|public-facing conclusion|caption|abstract|supplement" docs/goals/019-module5-results-review-artifact-design docs/module5_results_review_artifact_design.md data/module5_results_review_design
```

Review marker hits manually. Boundary, guardrail, and future-design language is
allowed. Final-claim or manuscript-ready language is not.

## Task 6: Stage, Commit, Push

Stage only:

```bash
git add \
  docs/goals/019-module5-results-review-artifact-design \
  docs/module5_results_review_artifact_design.md \
  data/module5_results_review_design
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
docs/goals/019-module5-results-review-artifact-design/Goal.md
docs/goals/019-module5-results-review-artifact-design/Log.md
docs/goals/019-module5-results-review-artifact-design/Plan.md
docs/goals/019-module5-results-review-artifact-design/Runbook.md
docs/module5_results_review_artifact_design.md
data/module5_results_review_design/artifact_specifications.csv
data/module5_results_review_design/review_question_checklist.csv
data/module5_results_review_design/data_dependency_matrix.csv
data/module5_results_review_design/wording_guardrails.csv
```

Optional scaffold CSVs may also be staged if they obey the scaffold rules.

Commit:

```bash
git commit -m "Design Module 5 results review artifacts"
```

Push `main`.

## Task 7: Wake-Up

Wake Galaxias with:

- final branch, HEAD, status, and pushed commit SHA;
- committed file list;
- input verification;
- design output row counts;
- whether optional scaffolds were created;
- artefact design recommendations;
- construction order;
- wording guardrails;
- unresolved decisions for Barry/Galaxias;
- recommended Goal 020 shape.

Then wait.
