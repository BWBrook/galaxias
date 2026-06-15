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
e0f39eac798fe83fa48fb8a853dd8b6ee9c6f817
## main...origin/main
0 0
```

## Input And Packet Checks

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
    print(f"{path}={len(rows)}")
    if len(rows) != expected:
        raise SystemExit(1)

meta = json.loads(Path("data/module5_production_summaries/summary_metadata.json").read_text(encoding="utf-8"))
print("raw_not_local", meta["raw_matched_outcomes_copied_locally"] is False)
if meta["raw_matched_outcomes_copied_locally"] is not False:
    raise SystemExit(1)

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
        if not reader.fieldnames or reader.fieldnames[0] != "packet_status":
            raise SystemExit(f"bad first column: {name}")
        rows = list(reader)
    print(f"{name}={len(rows)}")
    if len(rows) < minimum:
        raise SystemExit(1)
    if any(row["packet_status"] != "internal_non_display" for row in rows):
        raise SystemExit(f"bad packet_status: {name}")
    row_counts[name] = len(rows)

manifest = json.loads((packet_base / "review_packet_manifest.json").read_text(encoding="utf-8"))
if manifest["packet_status"] != "internal_non_display":
    raise SystemExit("bad manifest packet_status")
for name, count in row_counts.items():
    if manifest["tables"][name]["row_count"] != count:
        raise SystemExit(f"manifest count mismatch: {name}")
print("goal020_internal_review_packet_ok")
PY
```

## Diff And Language Checks

```bash
git diff --check
rg -n "[ \t]+$" \
  docs/goals/020-module5-internal-review-packet-build \
  docs/module5_internal_results_review_packet.md \
  data/module5_internal_review_packet
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final attribution|final causal claim|public-facing conclusion|caption|abstract|supplement" \
  docs/goals/020-module5-internal-review-packet-build \
  docs/module5_internal_results_review_packet.md \
  data/module5_internal_review_packet
```

Review marker hits manually. Boundary and guardrail hits are allowed;
final-claim or manuscript-ready language is not.

## Stage And Publish

```bash
git add \
  docs/goals/020-module5-internal-review-packet-build \
  docs/module5_internal_results_review_packet.md \
  data/module5_internal_review_packet
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
git commit -m "Build Module 5 internal review packet"
git push origin main
```

Do not stage raw outputs, caches, polished figures, manuscript artefacts, or
unrelated files.

## Wake-Up Content

Report:

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
