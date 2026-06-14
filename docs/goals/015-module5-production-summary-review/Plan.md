# Plan

## Operating Rules

Work only inside `/Users/bwbrook/papers/galaxias` and the authorized
read-only Goal 014 artifact path on `deep-server-ts`.

Treat repo-local instructions and this Goal 015 packet as the source of truth.
Do not read `/Users/bwbrook/chief_of_staff`,
`/Users/bwbrook/work/goal_composer`, sibling projects, or archive material.

This goal is compact summary extraction and review planning only. Do not write
final interpretation.

## Starting State Guard

Record:

- `pwd`
- `git rev-parse --abbrev-ref HEAD`
- `git rev-parse HEAD`
- `git status --short --branch`
- `git rev-list --left-right --count HEAD...origin/main`

Expected:

- branch `main`;
- HEAD at the pushed Goal 014 record commit
  `a96cfed24800823b77cbafeed5e9603e9dd6d33c`;
- `HEAD...origin/main` count `0 0`;
- only this Goal 015 packet untracked at start.

Stop if state differs materially.

## Read-First Surface

Read:

- `AGENTS.md`
- `README.md`
- `docs/module5_production_run_spec.md`
- `docs/module5_100rep_production_execution_report.md`
- `docs/goals/014-module5-100rep-production-execution/Log.md`
- Goal 015 packet files
- `data/module5_counterfactual_outcome_schema.csv`
- `src/galaxias_model/module5_rehearsal.py`
- existing Module 5 tests for style and conventions

## Task 1: Write Summary Tests

Create `tests/test_module5_production_summary.py`.

Use a tiny synthetic matched-outcome table with:

- two partitions;
- two source keys;
- two interventions;
- two or three replicates;
- all required contrast endpoints;
- one intentional malformed case for replicate coverage or seed mismatch.

Test:

- QC detects expected row/source/unit/replicate facts;
- endpoint summary quantiles and medians are computed per
  partition/intervention/endpoint;
- source/intervention summaries retain source identity;
- direction summaries count negative, zero, and positive contrast values;
- raw-row-sized output is not produced by the summary writer.

Run the focused test and record RED/fail-first evidence if practical.

## Task 2: Implement Summary Module And CLI

Create:

- `src/galaxias_model/module5_production_summary.py`
- `scripts/summarize_module5_production.py`

The module should:

- read a matched-outcomes CSV path;
- verify raw SHA if supplied;
- infer partition labels using the same intervention-to-partition mapping as
  Goal 014 if `partition_label` is absent;
- compute QC checks;
- compute required endpoint summaries;
- write compact CSV/JSON outputs to a chosen output directory;
- avoid writing raw matched-outcome rows.

The CLI should accept:

- `--matched-outcomes`
- `--output-dir`
- `--expected-sha256`
- `--source-artifact`
- `--source-execution-sha`
- `--goal014-record-sha`
- `--label` or `--run-id`

## Task 3: Local Validation

Run:

```bash
uv run pytest tests/test_module5_production_summary.py -q
uv run python scripts/summarize_module5_production.py --help
git diff --check
```

Do not run the summarizer locally against the raw production CSV, because the
raw CSV should remain remote-only.

## Task 4: Remote Summary Extraction

On `deep-server-ts`, run the summarizer against:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/matched_outcomes.csv
```

Recommended remote compact-summary directory:

```text
/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/compact_summaries_goal015
```

Use the current local repo source with Goal 015 summarizer code. Since this is
summary code, not production execution source, it may be transferred to a
temporary remote summary workspace or run from an updated remote checkout after
committing the code if that is cleaner. Record which method is used.

Do not modify the raw production output directory. Do not overwrite existing
raw artifacts.

## Task 5: Pull Back Compact Summaries

Copy only compact summary files back into:

```text
data/module5_production_summaries/
```

Required files:

- `summary_metadata.json`
- `qc_summary.csv`
- `partition_endpoint_summary.csv`
- `source_intervention_endpoint_summary.csv`
- `direction_summary.csv`

Confirm none of these is a raw matched-outcome copy. As a guard, fail if any
pulled-back file is unexpectedly large; use 20 MB as the hard cap for any
single summary file unless Galaxias authorizes otherwise.

## Task 6: Write Review Memo

Create:

```text
docs/module5_production_summary_review.md
```

The memo should include:

- source artifact and SHA;
- QC pass/fail summary;
- where compact summary files live;
- descriptive patterns by primary/sensitivity/diagnostic/negative-reference
  groups;
- interpretation questions for Galaxias/Barry;
- explicit stop before final causal claims, manuscript text, and figures.

Use careful language:

- allowed: "descriptive contrast", "candidate pattern", "requires
  interpretation review", "diagnostic sidecar";
- avoid as final claims: "caused", "demonstrates", "proves", "the effect is",
  "manuscript result".

## Task 7: Final Validation And Publish

Run:

```bash
uv run pytest tests/test_module5_production_summary.py -q
uv run python scripts/summarize_module5_production.py --help
git diff --check
rg -n "[ \t]+$" docs/goals/015-module5-production-summary-review docs/module5_production_summary_review.md data/module5_production_summaries src/galaxias_model/module5_production_summary.py scripts/summarize_module5_production.py tests/test_module5_production_summary.py
rg -n "production attribution|production-ready|manuscript|causal|claim|caused|demonstrates|proves|outputs/|matched_outcomes.csv" docs/goals/015-module5-production-summary-review docs/module5_production_summary_review.md data/module5_production_summaries
```

Review marker hits manually. They should be source-path, boundary, stop-point,
or non-claim language only.

Stage only the allowed files. Verify:

```bash
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git status --short --branch
```

Commit:

```bash
git commit -m "Summarize Module 5 production execution"
```

Push `main`.

## Task 8: Wake-Up

Wake Galaxias with:

- final branch, HEAD, status, and pushed commit SHA;
- remote artifact verified;
- raw matched-output SHA confirmation;
- summary command and location;
- compact summary file list and sizes;
- QC facts;
- notable descriptive patterns without final claims;
- interpretation questions;
- deviations and risks;
- recommended Goal 016 shape.

Then wait.
