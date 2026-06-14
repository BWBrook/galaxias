# Log

## 2026-06-14 - Packet Created By Galaxias

Barry approved proceeding from Goal 014 production execution to a summary and
interpretation-planning gate.

Galaxias created this Goal 015 packet to authorize compact summary extraction,
QC review, and interpretation planning only.

Pre-delegation facts:

- repo: `/Users/bwbrook/papers/galaxias`
- branch: `main`
- HEAD: `a96cfed24800823b77cbafeed5e9603e9dd6d33c`
- `HEAD...origin/main`: `0 0`
- status before packet: clean
- Goal 014 artifact:
  `/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production`
- raw matched-output SHA:
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`

Boundary:

- compact summaries and a review memo are authorized;
- raw matched-output local pull-back, final causal claims, manuscript language,
  figure/table work, production reruns, code changes to the production runner,
  and generated-output promotion are not authorized.

Awaiting action-agent execution.

## 2026-06-14 - Action Execution

Starting guard:

- `pwd`: `/Users/bwbrook/papers/galaxias`
- branch: `main`
- HEAD: `a96cfed24800823b77cbafeed5e9603e9dd6d33c`
- `git status --short --branch`: `## main...origin/main` plus only
  `?? docs/goals/015-module5-production-summary-review/`
- `git rev-list --left-right --count HEAD...origin/main`: `0 0`

Read-first surface completed: repo `AGENTS.md`, `README.md`,
`docs/module5_production_run_spec.md`,
`docs/module5_100rep_production_execution_report.md`, Goal 014 log, Goal 015
packet files, the Module 5 outcome schema, the rehearsal partition definitions,
and existing Module 5 tests for local style.

Implemented a focused production-summary module, CLI, and tests:

- `src/galaxias_model/module5_production_summary.py`
- `scripts/summarize_module5_production.py`
- `tests/test_module5_production_summary.py`

RED-first evidence:

- `uv run pytest tests/test_module5_production_summary.py -q` initially failed
  with `ModuleNotFoundError: No module named
  'galaxias_model.module5_production_summary'`.

Local implementation validation after adding the module and CLI:

- `uv run pytest tests/test_module5_production_summary.py -q`: `2 passed`
- `uv run python scripts/summarize_module5_production.py --help`: passed
- `git diff --check`: passed

Remote artifact verification on `deep-server-ts` was read-only. The Goal 014
artifact checksum file verified all listed files, including the remote raw
matched outcomes. Inspection facts recorded from the remote artifact:

- `all_checks_passed=True`
- `row_count=279500`
- `column_count=53`
- `expected_replicates=100`
- `source_intervention_units=2795`
- `distinct_proposal_source_keys=780`
- `seed_mismatches=0`
- `source_identity=True`
- `replicate_coverage=True`
- `matched_pair_ids=True`
- `schema_columns=True`
- `production_attribution=False`
- raw matched SHA:
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`
- raw matched size: `435867556` bytes

Remote summary extraction used a temporary summary workspace under the Goal 014
artifact:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/compact_summaries_goal015_workspace
```

The compact summary output directory was:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/compact_summaries_goal015
```

Remote summary command:

```bash
PYTHONPATH=src uv run python scripts/summarize_module5_production.py \
  --matched-outcomes /data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/matched_outcomes.csv \
  --output-dir /data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/compact_summaries_goal015 \
  --expected-sha256 ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727 \
  --source-artifact /data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production \
  --source-execution-sha ddb8a6de583e85f170f46c9dec9b1246baa6dccc \
  --goal014-record-sha a96cfed24800823b77cbafeed5e9603e9dd6d33c \
  --run-id 20260614T031501Z-goal014-m5-100rep-production
```

Remote summary QC:

- `qc_all_passed=True`
- `row_count=279500`
- `column_count=53`
- `expected_replicates=100`
- `source_intervention_units=2795`
- `distinct_proposal_source_keys=780`
- raw matched SHA matched the expected Goal 014 digest
- summary row counts:
  - `qc_summary.csv`: 12 rows
  - `partition_endpoint_summary.csv`: 78 rows
  - `source_intervention_endpoint_summary.csv`: 16,770 rows
  - `direction_summary.csv`: 78 rows

Pulled back only the five compact summary files into
`data/module5_production_summaries/`:

- `summary_metadata.json`: 2,762 bytes
- `qc_summary.csv`: 2,456 bytes
- `partition_endpoint_summary.csv`: 18,520 bytes
- `source_intervention_endpoint_summary.csv`: 8,734,938 bytes
- `direction_summary.csv`: 16,987 bytes

All compact files were below the 20 MB per-file guard. No local file named
`matched_outcomes.csv` was copied into the compact-summary directory.

Created `docs/module5_production_summary_review.md` as a descriptive QC and
interpretation-planning memo. The memo separates primary, sensitivity,
diagnostic sidecar, and negative-reference material, and stops before final
attribution interpretation, manuscript text, or figure/table work.

Deviations and recoveries:

- A first local attempt to run the remote verification command used bad zsh
  quoting and failed before SSH execution; reran with a quoted heredoc and no
  remote effect from the failed local command.
- A first temporary remote workspace copied only the new module and CLI; import
  failed because the package `__init__.py` imports existing package modules.
  Synced the repo package source into the temporary summary workspace and
  reran.
- A first remote summary attempt failed the `column_count` check because the
  implementation counted the inferred `partition_label` helper column. Fixed
  the summarizer to record the raw CSV column count before adding inferred
  labels, updated the focused test, and reran validation and summary extraction.
- A local `find -printf` file-size listing failed on macOS/BSD `find`; reran
  the listing with Python after the compact summary pull-back.

No production run, simulation, raw artifact mutation, raw matched-output
pull-back, production-runner change, scientific-contract change, staging,
commit, or push has occurred yet.
