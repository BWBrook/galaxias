# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias`, except for read-only remote
inspection on `deep-server-ts` against the Goal 014 artifact path named in
`Goal.md`.

Treat repo-local instructions and this Goal 017 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, sibling projects, or archive material.

This is a targeted audit. It is not manuscript work and not a production rerun.

## Starting State Guard

Record:

- `pwd`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git status --short --branch`
- `git rev-list --left-right --count HEAD...origin/main`

Expected:

- branch `main`;
- HEAD `597de181bbb2e3dd29ddf08f4389884217041b3c`;
- `HEAD...origin/main` count `0 0`;
- only this Goal 017 packet untracked.

Stop if state differs materially.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- Goal 017 packet files
- `docs/module5_interpretation_gate_review.md`
- `data/module5_interpretation_audits/source_intervention_audit_targets.csv`
- `data/module5_interpretation_audits/endpoint_priority_matrix.csv`
- `data/module5_interpretation_audits/wording_boundary_matrix.csv`
- `docs/module5_production_summary_review.md`
- `docs/module5_100rep_production_execution_report.md`
- `docs/goals/014-module5-100rep-production-execution/Log.md`
- `docs/goals/015-module5-production-summary-review/Log.md`
- `docs/goals/016-module5-interpretation-gate-review/Log.md`

## Task 1: Verify Local Audit Inputs

Run a structured parse check that confirms:

- Goal 017 selected audit IDs are present in
  `source_intervention_audit_targets.csv`;
- selected IDs are exactly `A01`, `A02`, `A03`, `A04`, `A05`, and `A10`;
- `A01`, `A02`, `A04`, and `A05` have concrete `proposal_source_key` values;
- `A03` and `A10` are aggregate negative-subset targets;
- Goal 015 summary metadata still reports the expected production facts.

Stop if any check differs.

## Task 2: Verify Remote Artifact

On `deep-server-ts`, verify:

- artifact directory exists;
- `checksums.sha256` exists;
- `sha256sum -c checksums.sha256` passes;
- raw matched-output file exists at the expected path;
- raw matched-output SHA is
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`;
- raw matched-output size is `435867556` bytes.

Use read-only commands. Do not create tmux sessions, rerun simulations, or
modify remote artifact files.

## Task 3: Run Remote Compact Audit

Create a temporary remote workspace under:

```text
/data/codex/scratch/galaxias/module5_goal017_audit_<timestamp>
```

The workspace may contain only:

- a copied audit script;
- compact audit output files;
- logs for this Goal 017 audit.

Read the remote raw matched outcomes and write compact outputs only:

- `audit_metadata.json`
- `selected_audit_targets.csv`
- `replicate_distribution_summary.csv`
- `negative_subset_sources.csv`

Audit IDs:

- `A01`
- `A02`
- `A03`
- `A04`
- `A05`
- `A10`

For source-specific targets, filter by exact `proposal_source_key` and
`intervention_id`.

For `A03` and `A10`, identify source/intervention units in the matching
partition/family/intervention with negative `persistence_2002_contrast` values.
Summarize the negative subset compactly. Do not pull all matching raw rows
locally.

## Task 4: Pull Back Compact Outputs

Create:

```text
data/module5_source_intervention_audits/
```

Pull back only:

- `audit_metadata.json`
- `selected_audit_targets.csv`
- `replicate_distribution_summary.csv`
- `negative_subset_sources.csv`

Do not pull back `matched_outcomes.csv` or any broad raw-row extract.

## Task 5: Write Audit Memo

Create:

```text
docs/module5_targeted_source_intervention_audit.md
```

Required structure:

- boundary;
- evidence basis;
- remote artifact verification;
- selected audit targets;
- primary source-specific findings;
- primary negative-subset findings;
- transient-perfect-storm negative-subset findings;
- endpoint-bundle assessment;
- extirpation-timing treatment;
- sensitivity and diagnostic implications;
- decisions for Galaxias/Barry;
- recommended Goal 018.

Keep language provisional and audit-oriented.

## Task 6: Validate Local Outputs

Run:

```bash
python3 - <<'PY'
import csv
import json
from pathlib import Path

selected = {"A01", "A02", "A03", "A04", "A05", "A10"}
targets_path = Path("data/module5_interpretation_audits/source_intervention_audit_targets.csv")
with targets_path.open(newline="", encoding="utf-8") as handle:
    targets = {row["audit_id"]: row for row in csv.DictReader(handle)}
assert selected <= set(targets), sorted(selected - set(targets))
assert {key for key in targets if key in selected} == selected
for key in ["A01", "A02", "A04", "A05"]:
    assert targets[key]["proposal_source_key"] != "aggregate"
for key in ["A03", "A10"]:
    assert targets[key]["proposal_source_key"] == "aggregate"

meta = json.loads(Path("data/module5_production_summaries/summary_metadata.json").read_text(encoding="utf-8"))
assert meta["qc_all_passed"] is True
assert meta["row_count"] == 279500
assert meta["source_intervention_units"] == 2795
assert meta["distinct_proposal_source_keys"] == 780
assert meta["raw_matched_outcomes_copied_locally"] is False

audit_base = Path("data/module5_source_intervention_audits")
audit_meta = json.loads((audit_base / "audit_metadata.json").read_text(encoding="utf-8"))
assert audit_meta["selected_audit_ids"] == sorted(selected)
assert audit_meta["raw_matched_outcomes_copied_locally"] is False
assert audit_meta["raw_matched_sha256"] == "ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727"

expected_files = {
    "selected_audit_targets.csv",
    "replicate_distribution_summary.csv",
    "negative_subset_sources.csv",
}
for name in expected_files:
    with (audit_base / name).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows, name
print("goal017_audit_outputs_ok")
PY
```

Check compact output sizes:

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

Run:

```bash
git diff --check
rg -n "[ \t]+$" docs/goals/017-module5-targeted-source-intervention-audit docs/module5_targeted_source_intervention_audit.md data/module5_source_intervention_audits
rg -n "caused|demonstrates|proves|the effect is|the result shows|manuscript result|publication-ready|final attribution|final causal claim" docs/goals/017-module5-targeted-source-intervention-audit docs/module5_targeted_source_intervention_audit.md data/module5_source_intervention_audits
```

Review marker hits manually. Boundary warnings are allowed. Final-claim prose
is not.

## Task 7: Stage, Commit, Push

Stage only:

```bash
git add \
  docs/goals/017-module5-targeted-source-intervention-audit \
  docs/module5_targeted_source_intervention_audit.md \
  data/module5_source_intervention_audits
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
docs/goals/017-module5-targeted-source-intervention-audit/Goal.md
docs/goals/017-module5-targeted-source-intervention-audit/Log.md
docs/goals/017-module5-targeted-source-intervention-audit/Plan.md
docs/goals/017-module5-targeted-source-intervention-audit/Runbook.md
docs/module5_targeted_source_intervention_audit.md
data/module5_source_intervention_audits/audit_metadata.json
data/module5_source_intervention_audits/selected_audit_targets.csv
data/module5_source_intervention_audits/replicate_distribution_summary.csv
data/module5_source_intervention_audits/negative_subset_sources.csv
```

Commit:

```bash
git commit -m "Audit Module 5 source intervention targets"
```

Push `main`.

## Task 8: Wake-Up

Wake Galaxias with:

- final branch, HEAD, status, and pushed commit SHA;
- committed file list;
- remote checksum and raw-file verification facts;
- selected audit IDs and compact output row counts;
- key source-specific findings;
- negative-subset findings;
- whether the Goal 016 endpoint bundle survived audit;
- any changes to extirpation-timing or sensitivity treatment;
- deviations and risks;
- recommended Goal 018 shape.

Then wait.
