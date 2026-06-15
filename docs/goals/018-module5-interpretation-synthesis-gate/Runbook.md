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
cb4e601ff4ff6f04035995306b83f777ff92217a
## main...origin/main
0 0
```

## Evidence Stack Check

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

meta = json.loads(Path("data/module5_production_summaries/summary_metadata.json").read_text(encoding="utf-8"))
checks = {
    "qc_all_passed": meta["qc_all_passed"] is True,
    "row_count": meta["row_count"] == 279500,
    "source_intervention_units": meta["source_intervention_units"] == 2795,
    "distinct_proposal_source_keys": meta["distinct_proposal_source_keys"] == 780,
    "raw_not_local": meta["raw_matched_outcomes_copied_locally"] is False,
}
for key, passed in checks.items():
    print(f"{key}={passed}")

expected_existing = {
    "data/module5_interpretation_audits/endpoint_priority_matrix.csv": 6,
    "data/module5_interpretation_audits/source_intervention_audit_targets.csv": 14,
    "data/module5_source_intervention_audits/replicate_distribution_summary.csv": 6,
    "data/module5_source_intervention_audits/negative_subset_sources.csv": 40,
}
for path, expected in expected_existing.items():
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    print(f"{path}={len(rows)}")
    if len(rows) != expected:
        raise SystemExit(1)

audit_meta = json.loads(Path("data/module5_source_intervention_audits/audit_metadata.json").read_text(encoding="utf-8"))
assert audit_meta["selected_audit_ids"] == ["A01", "A02", "A03", "A04", "A05", "A10"]
assert audit_meta["endpoint_bundle_survived_targeted_audit"] is True
assert audit_meta["raw_matched_outcomes_copied_locally"] is False
assert audit_meta["broad_raw_extract_created"] is False
if not all(checks.values()):
    raise SystemExit(1)
print("goal018_evidence_stack_ok")
PY
```

## Local Output Validation

```bash
python3 - <<'PY'
import csv
from pathlib import Path

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
    print(f"{path}={len(rows)}")
    if len(rows) != expected:
        raise SystemExit(1)
print("goal018_synthesis_outputs_ok")
PY
```

Diff and language checks:

```bash
git diff --check
rg -n "[ \t]+$" \
  docs/goals/018-module5-interpretation-synthesis-gate \
  docs/module5_interpretation_synthesis_gate.md \
  data/module5_interpretation_synthesis
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final attribution|final causal claim|figure|caption|abstract|supplement" \
  docs/goals/018-module5-interpretation-synthesis-gate \
  docs/module5_interpretation_synthesis_gate.md \
  data/module5_interpretation_synthesis
```

Review marker hits manually. Boundary and future-artefact design language is
allowed; final-claim or manuscript-artefact language is not.

## Stage And Publish

```bash
git add \
  docs/goals/018-module5-interpretation-synthesis-gate \
  docs/module5_interpretation_synthesis_gate.md \
  data/module5_interpretation_synthesis
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
git commit -m "Synthesize Module 5 interpretation gate"
git push origin main
```

Do not stage raw outputs, caches, figures, manuscript artefacts, or unrelated
files.

## Wake-Up Content

Report:

- final branch, HEAD, status, and pushed commit SHA;
- committed file list;
- evidence-stack verification;
- synthesis decision table row counts;
- endpoint bundle acceptance decision;
- source-audit sufficiency decision;
- primary, sensitivity, diagnostic, and extirpation-timing treatment;
- future artefact recommendations;
- wording boundaries;
- unresolved decisions for Galaxias/Barry;
- recommended Goal 019 shape.
