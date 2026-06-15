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
/Users/bwbrook/papers/galaxias
main
922b8e84b22c072b6559adf2c969cdbcc4185eb4
## main...origin/main
0 0
```

## Input And Output Checks

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
    print(f"{path}={len(rows)}")
    if len(rows) != expected:
        raise SystemExit(1)

meta = json.loads(Path("data/module5_production_summaries/summary_metadata.json").read_text(encoding="utf-8"))
print("raw_not_local", meta["raw_matched_outcomes_copied_locally"] is False)
if meta["raw_matched_outcomes_copied_locally"] is not False:
    raise SystemExit(1)

expected_outputs_min = {
    "data/module5_results_review_design/artifact_specifications.csv": 5,
    "data/module5_results_review_design/review_question_checklist.csv": 8,
    "data/module5_results_review_design/data_dependency_matrix.csv": 8,
    "data/module5_results_review_design/wording_guardrails.csv": 8,
}
for path, minimum in expected_outputs_min.items():
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    print(f"{path}={len(rows)}")
    if len(rows) < minimum:
        raise SystemExit(1)

for path in Path("data/module5_results_review_design").glob("internal_scaffold_*.csv"):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or reader.fieldnames[0] != "scaffold_status":
            raise SystemExit(f"bad scaffold first column: {path}")
        rows = list(reader)
    if not rows or any(row["scaffold_status"] != "internal_non_display" for row in rows):
        raise SystemExit(f"bad scaffold status: {path}")
print("goal019_design_inputs_outputs_ok")
PY
```

## Diff And Language Checks

```bash
git diff --check
rg -n "[ \t]+$" \
  docs/goals/019-module5-results-review-artifact-design \
  docs/module5_results_review_artifact_design.md \
  data/module5_results_review_design
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final attribution|final causal claim|public-facing conclusion|caption|abstract|supplement" \
  docs/goals/019-module5-results-review-artifact-design \
  docs/module5_results_review_artifact_design.md \
  data/module5_results_review_design
```

Review marker hits manually. Boundary and design-guardrail hits are allowed;
final-claim or manuscript-ready language is not.

## Stage And Publish

```bash
git add \
  docs/goals/019-module5-results-review-artifact-design \
  docs/module5_results_review_artifact_design.md \
  data/module5_results_review_design
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
git commit -m "Design Module 5 results review artifacts"
git push origin main
```

Do not stage raw outputs, caches, polished figures, manuscript artefacts, or
unrelated files.

## Wake-Up Content

Report:

- final branch, HEAD, status, and pushed commit SHA;
- committed file list;
- input verification;
- design output row counts;
- whether optional scaffolds were created;
- artefact design recommendations;
- construction order;
- wording guardrails;
- unresolved decisions for Galaxias/Barry;
- recommended Goal 020 shape.
