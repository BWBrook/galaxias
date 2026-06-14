# Runbook

## Operating Mode

Spec/decision-only. Work inside `/Users/bwbrook/papers/galaxias` only.

Do not read:

- `/Users/bwbrook/chief_of_staff`
- `/Users/bwbrook/work/goal_composer`

Do not run Module 5, remote compute, production attribution, broad
simulations, tests, validation suites, commits, pushes, staging, or generated
output creation.

## Step 1: Starting State

Record in `Log.md`:

```bash
pwd
git branch --show-current
git rev-parse --short HEAD
git status --short --branch
```

If status shows dirty files outside this Goal 005 packet, pause and report.

## Step 2: Read First

Read the files listed in `Goal.md`.

Suggested order:

1. `AGENTS.md`
2. `README.md`
3. `docs/gated_action_plan_module4_5_and_beyond.md`
4. `docs/module4_5_mechanism_interpretation_review.md`
5. `docs/module5_counterfactual_attribution_plan.md`
6. Goal 001-004 logs and Goal 004 runbook
7. Module 4.5 and Module 5 CSV contracts
8. Module 5 runner, inspector, scripts, and focused tests

Record any stale or superseded management wording as historical context, not
as a live authority chain.

## Step 3: Inspect Proposal-Source Options

Use tracked CSVs only. You may run read-only commands to summarise:

- counts by `family_id` and proposal set in
  `data/module4_5_proposal_set_membership.csv`;
- family roles and accepted counts in
  `data/module4_5_family_decision_table.csv`;
- intervention rows by family, role, and axis in
  `data/module5_counterfactual_interventions.csv`;
- output schema fields in `data/module5_counterfactual_outcome_schema.csv`.

Do not write generated summaries outside the final specification document and
`Log.md`.

## Step 4: Draft The Specification

Create:

```text
docs/module5_dry_run_production_spec.md
```

Use the section list from `Goal.md`.

Be opinionated. Galaxias wants a recommendation, not a neutral catalogue. If
there are trade-offs, state them and then choose.

## Step 5: Validate Docs-Only Work

Run:

```bash
git status --short --branch
git diff --check
```

Because this goal may create untracked docs, run a direct trailing-whitespace
scan over the goal/spec text as well:

```bash
{ git diff --name-only --diff-filter=ACM; git ls-files --others --exclude-standard; } | \
  rg '(^docs/goals/005-module5-dry-run-production-spec/|^docs/module5_dry_run_production_spec.md$)' | \
  xargs rg -n "[ \t]+$"
```

Expected: no matches.

Run a narrow marker scan over changed and untracked goal/spec text. One
acceptable pattern is:

```bash
{ git diff --name-only --diff-filter=ACM; git ls-files --others --exclude-standard; } | \
  rg '(^docs/goals/005-module5-dry-run-production-spec/|^docs/module5_dry_run_production_spec.md$)' | \
  xargs rg -n "production attribution|production-sized|remote compute|deep-server|Nectar|outputs/|manuscript|causal proof|commit|push"
```

Expected boundary/non-claim hits are acceptable. Unexpected instructions to
run production work, remote work, commit, push, or make manuscript claims are
not acceptable.

Do not run tests. Do not run `make` targets. Do not create generated outputs.

## Step 6: Final Log And Response

Update `Log.md` with:

- files changed;
- recommendation summary;
- validation evidence;
- final status;
- whether the Galaxias wake-up was sent.

Final response to Galaxias should report:

- what was produced;
- recommended dry-run subset;
- recommended production source;
- intervention-matrix recommendation;
- validation run;
- final git status;
- questions or approval points.

## Step 7: Wake Galaxias

After finalising the response, send a short wake-up to the Galaxias
orchestrator thread:

```text
thread id = 019eaac3-85f6-7853-bc28-a4d905dadfc3
```

The wake-up should be brief:

```text
Goal 005 is complete or blocked. Please review my final report and the action
repo changes in /Users/bwbrook/papers/galaxias.
```

If thread tools are unavailable, do not improvise by reading Chief of Staff.
Report that the wake-up could not be sent.
