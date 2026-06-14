# Goal: Module 5 Production Run Specification

## Objective

Create a decision-ready Module 5 production-run specification that Barry and
Galaxias can approve before any production attribution execution begins.

This is a docs/specification goal. It does not authorize production execution,
remote probes, simulations, generated-output changes, code changes, staging,
commit, push, or manuscript claims.

## Why This Matters

Goals 005-008 moved Module 5 from design contract to real-proposal dry-run
plumbing and then to an approved 13-row intervention matrix contract. The next
question is no longer whether the plumbing can touch real proposal rows. It is
what exact production run should be authorized.

Barry and Galaxias have agreed that the likely production execution target is
`deep-server` in a durable `tmux` session. That should now be made explicit in
the project run specification, together with proposal sampling, replicate
count, seed policy, validation gates, output policy, and claim-language
boundaries.

The result should be a runbook-quality decision document, not a remote run.

## Scope

In scope:

- Create `docs/module5_production_run_spec.md`.
- Update this goal `Log.md`.
- Review the accepted Goal 005-008 Module 5 state.
- Recommend a production proposal source and sampling rule.
- Recommend how to treat:
  - primary `persistent_joint_cause`;
  - sensitivity families `climbing_only` and `transient_perfect_storm`;
  - the `m5_climbing_only_no_trout_pressure` diagnostic sidecar;
  - negative-reference status-quo diagnostics.
- Recommend family weighting or, if a single weighted estimate is not
  defensible, recommend reporting family-specific summaries instead.
- Recommend a stochastic replicate count and deterministic seed policy.
- Estimate expected production row counts under the recommended design.
- Specify the provisional remote execution model:
  - target: `deep-server` via `deep-server-ts` or `utas-ubuntu`;
  - supervision: named `tmux` session;
  - remote source location: `/data/codex/repos`;
  - remote scratch/artifact locations: `/data/codex/scratch` and
    `/data/codex/artifacts`;
  - logs and provenance written to disk.
- Specify the later remote-smoke and production-execution gates.
- Specify output-retention and pull-back policy.
- Specify claim-language boundaries for reviewed outputs.

Out of scope:

- No code, test, runner, simulator, proposal-resolver, Makefile, or tracked CSV
  changes.
- No edits to `data/module5_counterfactual_interventions.csv` or
  `data/module5_counterfactual_outcome_schema.csv`.
- No local or remote simulations.
- No Module 5 dry-run reruns.
- No generated-output creation, deletion, regeneration, promotion, or
  inspection beyond reading existing small logs/docs if needed.
- No remote SSH checks, remote probes, remote clone setup, `tmux` creation, or
  Nectar/deep-server command execution.
- No production attribution execution.
- No manuscript claims, final causal interpretation, or publication language.
- No staging, commit, push, PR, or publication.

## Boundary On External Control-Plane Docs

For this goal, Galaxias has already consulted the Nectar control-plane docs and
provides the relevant remote-compute summary below. Do not read
`/Users/bwbrook/work/nectar`, `/Users/bwbrook/chief_of_staff`, or
`/Users/bwbrook/work/goal_composer` in this action-agent goal. If you believe a
live control-plane detail is essential, stop and ask Galaxias.

Orchestrator-provided compute summary:

- `deep-server` is a physical UTAS Linux host suitable for durable
  single-host CPU/RAM jobs.
- Use Tailscale aliases `deep-server-ts` or `utas-ubuntu` from Barry-controlled
  machines.
- Treat `deep-server` as a direct-shell host, not a scheduler-backed HPC
  system.
- Current baseline from the control-plane docs: about 64 logical CPU threads,
  about 125 GiB RAM, and substantial `/data` storage.
- GPU compute on `deep-server` is not validated and should not be assumed.
- Standard remote layout:
  - `/data/codex/repos` for working clones;
  - `/data/codex/scratch` for run-specific scratch directories;
  - `/data/codex/artifacts` for durable generated artifacts worth keeping;
  - `/data/codex/tmp` for disposable temporary work.
- Use Git for source state and `rsync`/`scp` for large generated payloads.
- Use a durable `tmux` session for long interactive supervision.
- Future execution should start with a tiny remote smoke that proves access,
  environment, source checkout, input paths, output paths, logging, provenance,
  and cleanup before production execution is authorized.

## Required Decisions In The Spec

`docs/module5_production_run_spec.md` must make recommendations on these
points. Do not leave them as an undecided brainstorm unless the evidence shows
that Galaxias/Barry must choose between named alternatives.

1. Proposal source:
   - all `accepted` proposals from accepted-frontier families;
   - a stratified sample from `accepted`;
   - or another explicitly justified source.

2. Family treatment:
   - primary versus sensitivity reporting;
   - whether to report family-specific summaries instead of a single blended
     estimate;
   - if a blended estimate is recommended, the weighting rule and rationale.

3. Diagnostic sidecar:
   - whether `m5_climbing_only_no_trout_pressure` is run;
   - whether it is excluded from headline attribution weighting;
   - how it is labelled in outputs and summaries.

4. Negative references:
   - whether status-quo negative-reference rows are run as diagnostics;
   - what proposal source they use, if any;
   - how they are excluded from production attribution claims.

5. Replicate count:
   - recommended number of stochastic replicates per proposal/intervention;
   - rationale using existing Module 4.5 replicate context and Goal 006 dry-run
     evidence;
   - expected row count under the recommendation.

6. Seed policy:
   - deterministic base label;
   - stable matched-pair seed derivation;
   - restart/reproducibility expectations;
   - provenance fields that must be recorded.

7. Remote execution model:
   - `deep-server` alias preference;
   - `tmux` session naming convention;
   - remote repo/scratch/artifact paths;
   - log files and provenance manifests;
   - expected clean-start and cleanup checks.

8. Validation ladder:
   - pre-execution contract checks;
   - tiny remote smoke requirements;
   - production execution completion checks;
   - disk-first inspection requirements;
   - criteria for pulling summaries back to the local repo.

9. Output policy:
   - ignored local outputs versus remote artifacts;
   - what may be tracked later, if anything;
   - what must remain outside git.

10. Claim-language boundary:
    - what the production run can support after review;
    - what remains non-claim, exploratory, or manuscript-premature.

## Expected Spec Structure

`docs/module5_production_run_spec.md` should include:

- current state and non-claims;
- production input contracts reviewed;
- recommended proposal source and sampling rule;
- family and diagnostic-sidecar treatment;
- negative-reference treatment;
- replicate and seed policy;
- expected row-count and artifact-size estimates;
- provisional `deep-server` + `tmux` execution model;
- remote smoke gate;
- production execution gate;
- validation and inspection ladder;
- output retention and pull-back policy;
- claim-language boundary;
- open decisions for Galaxias/Barry, if any;
- proposed next goal.

## Required Validation

Run and log:

- `git status --short --branch`
- `git diff --check`
- a direct trailing-whitespace scan over:
  - `docs/goals/009-module5-production-run-spec/`
  - `docs/module5_production_run_spec.md`
- a marker scan over Goal 009 files for:
  - `production attribution`
  - `production-ready`
  - `remote compute`
  - `deep-server`
  - `tmux`
  - `outputs/`
  - `manuscript`
  - `commit`
  - `push`

Marker hits are allowed only when they are recommendation, boundary,
non-claim, stop-point, or future-gate language.

You may run read-only Python summaries over tracked CSV files to calculate
proposal counts and expected row counts. Do not write generated outputs.

Do not run tests, `make` targets, simulations, dry-run commands, remote probes,
or production commands for this docs/specification goal.

## Done When

- `docs/module5_production_run_spec.md` is decision-ready for Galaxias review.
- The spec makes a clear recommendation on proposal source, family treatment,
  diagnostic-sidecar handling, negative-reference handling, replicate count,
  seed policy, remote execution model, validation ladder, output policy, and
  claim-language boundary.
- Expected row counts are calculated and documented.
- The next goal shape is clear.
- The goal log records starting state, files read, files changed, validation
  checks, final status, and risks/questions.
- The action repo remains uncommitted and unstaged.
- No code, tests, CSV contracts, generated outputs, simulations, remote
  probes, remote sessions, production execution, staging, commit, push, PR,
  publication, or manuscript claims occur.
- `pedder` sends a short wake-up to the Galaxias orchestrator thread on
  completion or blockage.
