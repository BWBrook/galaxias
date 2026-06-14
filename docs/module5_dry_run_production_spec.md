# Module 5 Dry-Run And Production Specification

## Current State And Non-Claims

Modules 1 through 4.5 are complete to the current project standard. Module 4
found `persistent_joint_cause` as the stable target-sum winner in 12 of 15
variant/seed runs, with `climbing_only` winning 3 single-axis
late-observation relaxations and with no accepted proposals for
`habitat_only_null` or `trout_only`.

Module 4.5 converted that calibration result into a mechanism audit. Its
current Module 5 family roles are:

- primary: `persistent_joint_cause`;
- sensitivity: `climbing_only`, `transient_perfect_storm`;
- negative references: `habitat_only_null`, `trout_only`.

Goals 001-004 added the Module 5 design contract, the current intervention and
outcome-schema tables, a tiny local smoke runner, disk-first smoke inspection,
and a production-readiness gate. Those goals prove contract and smoke wiring,
not attribution. The current smoke runner still uses `smoke_default:<family>`
proposal identifiers, so Module 5 has not yet consumed real Module 4.5
proposal rows. Module 5 attribution has not begun.

The licensed statement remains narrow: within the current model-family and
target framework, habitat-only and trout-only explanations are not competitive,
and joint trout-plus-climbing explanations are the most stable calibration
result so far. No production attribution result, manuscript causal claim, or
final proof statement follows from this specification.

## Proposal-Source Options

| source | scale from tracked table | scientific meaning | strengths | risks |
| --- | ---: | --- | --- | --- |
| `accepted` | 750 proposals: 265 `persistent_joint_cause`, 235 `climbing_only`, 250 `transient_perfect_storm` | Main accepted frontier from Module 4.5 for the mechanism-rich families. | Best source for later attribution because it carries accepted-frontier uncertainty rather than only rank winners. Covers all observation-bridge variants and seeds. | Too large for an unreviewed local dry run. Excludes negative-reference families because they have no accepted frontier support. Requires explicit production sampling, weighting, and compute approval. |
| `family_winners` | 75 proposals: 15 per family across all five families | Best proposal for each family, variant, and seed. | Exercises every current Module 5 role, including negative references. Good for real-proposal plumbing and contract checks. | Not an inferential ensemble. Negative-reference winners are diagnostic only because those families have no accepted support. |
| `global_winners` | 15 proposals: 12 `persistent_joint_cause`, 3 `climbing_only` | Winning family proposal for each Module 4 variant/seed. | Very compact and aligned to the headline rank result. | Misses `transient_perfect_storm` and both negative-reference families, so it cannot exercise the full current intervention matrix or sensitivity structure. |
| `near_frontier_absolute` | 35 proposals: 18 `persistent_joint_cause`, 14 `climbing_only`, 3 `transient_perfect_storm` | Proposals within 10 target-sum units of each variant/seed best. | Compact set of close contenders; useful as a later robustness sidecar. | Absolute threshold is partly scale-dependent and leaves `transient_perfect_storm` sparse. No negative references. |
| `near_frontier_relative` | 24 proposals: 13 `persistent_joint_cause`, 9 `climbing_only`, 2 `transient_perfect_storm` | Proposals within 1.05 times each variant/seed best target sum. | Tighter close-contender set; useful for sensitivity to rank-frontier definition. | Too sparse for the first real-proposal dry run and not representative enough for production attribution. No negative references. |

Recommendation:

- Dry-run source: a deliberately tiny `family_winners` subset from
  `variant_id = baseline_current` and `seed = 20260410`, one proposal per
  current Module 5 family role.
- Later production source: the `accepted` proposal set for
  `persistent_joint_cause`, `climbing_only`, and `transient_perfect_storm`,
  with negative references handled separately as diagnostics if Barry/Galaxias
  still want them.

This split keeps the next dry run focused on real-proposal wiring, while
preserving the accepted frontier as the production attribution source.

## Dry-Run Specification

Recommended dry-run subset:

| family_id | module5_role | proposal_id | proposal source |
| --- | --- | --- | --- |
| `persistent_joint_cause` | primary | `persistent_joint_cause:p00162` | `family_winners`, `baseline_current`, seed `20260410` |
| `climbing_only` | sensitivity | `climbing_only:p00216` | `family_winners`, `baseline_current`, seed `20260410` |
| `transient_perfect_storm` | sensitivity | `transient_perfect_storm:p00144` | `family_winners`, `baseline_current`, seed `20260410` |
| `habitat_only_null` | negative_reference | `habitat_only_null:p00761` | `family_winners`, `baseline_current`, seed `20260410` |
| `trout_only` | negative_reference | `trout_only:p00814` | `family_winners`, `baseline_current`, seed `20260410` |

Recommended dry-run shape:

- Families: all five current Module 5 role families.
- Proposal count: 5 total, one per family.
- Intervention rows: all 10 current rows in
  `data/module5_counterfactual_interventions.csv`.
- Matched proposal/intervention combinations: 10, because each intervention
  row applies to one family.
- Stochastic replicates: 5 per proposal/intervention combination.
- Expected matched-pair output rows: 50.
- Output location for a future implementation goal:
  `outputs/module5_dry_run_baseline_current_20260410/`.
- Output status: ignored raw output only; no generated dry-run file should be
  tracked without a later review gate.

This dry run should be treated as a real-proposal execution contract check. It
should verify that the runner can resolve proposal rows from
`data/module4_5_proposal_set_membership.csv`, load proposal-specific parameter
values, preserve matched baseline/intervention pairing, write rows conforming
to `data/module5_counterfactual_outcome_schema.csv`, and produce inspectable
provenance. It should not be interpreted as attribution evidence.

Future implementation validation should include the contract validator,
focused runner tests for proposal resolution, focused inspection tests,
`make fast-check`, the dry-run command, disk-first dry-run inspection, and a
docs/status check. This Goal 005 does not run those checks.

## Production Specification Sketch

Before production-scale execution, Barry/Galaxias must decide:

- whether production uses all 750 accepted proposals or a pre-registered
  stratified sample from the accepted frontier;
- family weighting: primary-only headline with sensitivity appendices, equal
  family weighting, accepted-count weighting, or another documented rule;
- proposals per family and per variant/seed if sampling is needed;
- stochastic replicates per proposal/intervention;
- whether negative references remain status-quo diagnostics or receive a
  separate diagnostic scenario plan;
- whether near-frontier sets are included as robustness sidecars;
- compute target, wall-time budget, storage budget, stop rules, and artifact
  retention;
- exact output partitions and reviewable summary products.

Recommended production source:

- Use `accepted` as the production attribution source for
  `persistent_joint_cause`, `climbing_only`, and
  `transient_perfect_storm`.
- Keep `family_winners` available for negative-reference diagnostics, not as
  part of the accepted-frontier attribution ensemble.
- Treat `near_frontier_absolute` and `near_frontier_relative` as optional
  robustness summaries after the accepted-frontier production run is reviewed.
- Do not use `global_winners` as the production source; it is too narrow and
  omits the transient sensitivity family.

Dry-run decisions should not silently become production decisions. A later
production goal must restate proposal source, replicate count, intervention
matrix, compute target, validation ladder, and claim-language boundary.

## Intervention Matrix Audit

The current intervention table has 10 rows:

- `persistent_joint_cause`: `status_quo`, `no_trout_pressure`,
  `no_climbing_pressure`, `no_trout_or_climbing_pressure`;
- `climbing_only`: `status_quo`, `no_trout_pressure`;
- `transient_perfect_storm`: `status_quo`, `no_climbing_pressure`;
- `habitat_only_null`: `status_quo` negative reference;
- `trout_only`: `status_quo` negative reference.

The matrix is intentionally or at least currently asymmetric. It is adequate
for the next dry-run implementation if the dry run is framed as a contract and
runner-wiring exercise, because it touches every current row and every current
family role without changing the data contract.

It is not yet adequate as an unreviewed production attribution matrix. Before
production, Barry/Galaxias should either approve the current asymmetric
hypothesis matrix or authorise a contract-revision goal. The most likely
revision questions are:

- should `climbing_only` also include `no_climbing_pressure`, since that is
  its active mechanism?
- should `transient_perfect_storm` include `no_trout_pressure` and
  `no_trout_or_climbing_pressure` to separate early trout overshoot from later
  climbing pressure?
- should negative references remain status-quo diagnostics only, or should
  they be excluded from dry-run intervention contrasts entirely?
- should the table distinguish pressure removal from state/removal scenarios
  such as no stocking, no invasion, no transient overshoot, or habitat-buffer
  interventions?

Recommendation: do not expand the matrix before the next dry-run
implementation goal. Use the dry run to prove real-proposal wiring against the
current contract. Require an explicit matrix review or contract-revision gate
before production-sized execution.

## Seed And Restart Policy

Module 5 should preserve common-random-number pairing. For each
proposal/intervention/replicate unit, the baseline arm and counterfactual arm
should use the same stochastic seed. Different replicate indices should use
different seeds.

Recommended deterministic seed rule:

- define a project-level base label such as `galaxias-module5-dry-run-v1`;
- derive a stable unsigned integer seed from the tuple
  `(base_label, proposal_id, intervention_id, stochastic_replicate_id)`;
- use a stable digest such as SHA-256, not Python's process-randomised
  `hash()`;
- record both the base label and the resolved per-pair seeds in provenance.

Restart/resume expectations:

- every matched pair must have a stable `matched_pair_id`;
- reruns should skip already valid matched pairs only after schema,
  provenance, and checksum checks pass;
- partial outputs should be written to a temporary path and promoted
  atomically;
- if an intervention or proposal definition changes, prior dry-run outputs
  should be marked stale rather than resumed.

## Output And Provenance Policy

Raw dry-run and production outputs should remain outside git under ignored
`outputs/` locally or later remote artifact/scratch paths. The dry-run output
directory should contain, at minimum:

- matched outcome rows conforming to
  `data/module5_counterfactual_outcome_schema.csv`;
- provenance JSON;
- inspection summary, checks, and report;
- checksums for emitted CSV/JSON/Markdown artifacts.

Required provenance fields:

- git SHA;
- branch or detached-HEAD state;
- dirty-state summary;
- command line and runner script path;
- proposal-source table path and proposal-set filter;
- intervention contract path;
- outcome schema path;
- Module 4 raw artifact manifest path;
- Module 4.5 proposal membership table path;
- family decision table path;
- Python version and package/environment summary;
- compute host;
- output directory;
- replicate count and seed derivation rule;
- output checksums.

Compact summaries may be tracked later only after review. Good candidates are
a small dry-run inspection report, a provenance summary, and a row-count/schema
summary. Raw matched outcomes should remain ignored unless a later goal
explicitly promotes a compact reviewed subset.

## Validation Ladder

For this Goal 005, validation is docs-only: status, whitespace, diff, and
marker scans over changed goal/spec text.

For the next dry-run implementation goal, the validation ladder should be:

1. Docs and contract checks:
   - verify no unintended data-contract changes;
   - run the Module 5 contract validator.
2. Focused tests:
   - proposal-source resolver tests;
   - intervention override tests;
   - matched seed-pairing tests;
   - schema-conforming writer tests;
   - disk-first inspector tests.
3. Repo fast gate:
   - run `make fast-check` only after code/test changes are in scope.
4. Tiny smoke carry-forward:
   - preserve the existing smoke runner/inspection tests.
5. Real-proposal dry run:
   - run the recommended 5-proposal, 10-intervention-row, 5-replicate dry
     run only after the implementation goal authorises generated output.
6. Dry-run inspection:
   - inspect schema, pair IDs, common-random-number pairing, provenance,
     row counts, missing/duplicate pairs, and smoke/dry-run boundary labels.
7. Remote smoke:
   - only after Barry/Galaxias approve remote planning through the existing
     compute-routing boundary.
8. Production validation:
   - run only after production proposal source, replicate count, compute
     target, output handling, and claim language are approved.

## Approval Gates And Stop Points

Galaxias may decide:

- whether this specification is internally coherent;
- whether the recommended dry-run subset is the right next implementation
  target;
- whether stale `SRF-A` wording in older packets should be treated as
  historical approval context.

Barry/Galaxias must approve before:

- changing the intervention matrix;
- changing the family set or family roles;
- choosing production sample size or family weighting;
- choosing production replicate count;
- running a real dry run or creating generated outputs;
- planning or probing remote compute;
- promoting any generated output into tracked files;
- making any attribution or manuscript-level claim.

Pause before implementation if:

- the dry-run subset is changed from the 5-proposal `family_winners` subset;
- the intervention matrix is expanded or reduced;
- real proposal values cannot be resolved from tracked Module 4.5 sources;
- common-random-number pairing cannot be inspected from disk;
- output schema changes are needed;
- a future goal would require remote compute, production-sized execution, or
  interpretation of dry-run outputs as evidence.

## Recommended Next Goal

Recommended next goal: a bounded implementation goal for a real-proposal
Module 5 local dry run.

That goal should:

- implement or wire proposal resolution from
  `data/module4_5_proposal_set_membership.csv`;
- use the five `baseline_current`/`20260410` `family_winners` proposals listed
  above;
- consume the current intervention matrix unchanged;
- use 5 matched stochastic replicates per intervention row;
- write only ignored dry-run outputs under
  `outputs/module5_dry_run_baseline_current_20260410/`;
- extend focused runner and inspection tests;
- run the approved validation ladder for code/test changes;
- stop without production attribution, remote compute, manuscript claims,
  commit, or push unless explicitly authorised by that future packet.

If Barry/Galaxias want a scientifically symmetric intervention matrix before
any further implementation, insert a contract-revision goal before the dry-run
implementation. Otherwise, the dry-run implementation can proceed first and
feed a sharper production-matrix review.
