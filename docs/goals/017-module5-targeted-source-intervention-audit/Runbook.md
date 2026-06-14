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
597de181bbb2e3dd29ddf08f4389884217041b3c
## main...origin/main
0 0
```

## Local Input Check

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

selected = {"A01", "A02", "A03", "A04", "A05", "A10"}
targets_path = Path("data/module5_interpretation_audits/source_intervention_audit_targets.csv")
with targets_path.open(newline="", encoding="utf-8") as handle:
    targets = {row["audit_id"]: row for row in csv.DictReader(handle)}
print("selected_present", selected <= set(targets))
print("selected_ids", ",".join(sorted(selected)))
for key in ["A01", "A02", "A04", "A05"]:
    print(key, targets[key]["proposal_source_key"] != "aggregate")
for key in ["A03", "A10"]:
    print(key, targets[key]["proposal_source_key"] == "aggregate")

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
if not (selected <= set(targets) and all(checks.values())):
    raise SystemExit(1)
PY
```

## Remote Verification

Run on `deep-server-ts` with read-only commands:

```bash
ART=/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production
RAW=$ART/outputs/module5_100rep_production/matched_outcomes.csv
test -d "$ART"
test -f "$ART/checksums.sha256"
cd "$ART" && sha256sum -c checksums.sha256
test -f "$RAW"
sha256sum "$RAW"
stat -c '%s' "$RAW"
```

Expected raw SHA:

```text
ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727
```

Expected raw size:

```text
435867556
```

## Remote Audit Rule

The remote audit may read the raw matched outcomes but must write only compact
audit outputs. It must not modify the Goal 014 artifact and must not copy the
raw matched-output table locally.

Use a run-specific scratch directory:

```text
/data/codex/scratch/galaxias/module5_goal017_audit_<timestamp>
```

Required remote output files:

```text
audit_metadata.json
selected_audit_targets.csv
replicate_distribution_summary.csv
negative_subset_sources.csv
```

## Local Validation

After pulling back compact outputs only:

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

selected = {"A01", "A02", "A03", "A04", "A05", "A10"}
base = Path("data/module5_source_intervention_audits")
meta = json.loads((base / "audit_metadata.json").read_text(encoding="utf-8"))
assert meta["selected_audit_ids"] == sorted(selected)
assert meta["raw_matched_outcomes_copied_locally"] is False
assert meta["raw_matched_sha256"] == "ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727"
for name in [
    "selected_audit_targets.csv",
    "replicate_distribution_summary.csv",
    "negative_subset_sources.csv",
]:
    with (base / name).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    print(name, len(rows))
    assert rows
print("goal017_audit_outputs_ok")
PY
```

Compact size check:

```bash
python3 - <<'PY'
from pathlib import Path
base = Path("data/module5_source_intervention_audits")
for path in sorted(base.iterdir()):
    if path.is_file():
        size = path.stat().st_size
        print(f"{path}: {size}")
        assert size < 20_000_000
PY
```

Diff and language checks:

```bash
git diff --check
rg -n "[ \t]+$" \
  docs/goals/017-module5-targeted-source-intervention-audit \
  docs/module5_targeted_source_intervention_audit.md \
  data/module5_source_intervention_audits
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final attribution|final causal claim|figure|caption|abstract|supplement" \
  docs/goals/017-module5-targeted-source-intervention-audit \
  docs/module5_targeted_source_intervention_audit.md \
  data/module5_source_intervention_audits
```

Review marker hits manually. Boundary language is allowed; final-claim or
manuscript-artefact language is not.

## Stage And Publish

```bash
git add \
  docs/goals/017-module5-targeted-source-intervention-audit \
  docs/module5_targeted_source_intervention_audit.md \
  data/module5_source_intervention_audits
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
git commit -m "Audit Module 5 source intervention targets"
git push origin main
```

Do not stage raw outputs, caches, figures, manuscript artefacts, or unrelated
files.

## Wake-Up Content

Report:

- final branch, HEAD, status, and pushed commit SHA;
- committed file list;
- remote artifact checksum facts;
- selected audit IDs;
- compact audit output row counts and sizes;
- key findings for `A01` to `A05` and `A10`;
- whether the Goal 016 endpoint bundle survived the audit;
- unresolved interpretation decisions;
- recommended Goal 018 shape.
