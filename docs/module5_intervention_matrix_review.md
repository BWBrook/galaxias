# Module 5 Intervention Matrix Review

## Current State And Non-Claims

Goal 006 showed that the current 10-row Module 5 intervention matrix can be
consumed by the local real-proposal dry-run path. That is a plumbing and
inspection result. It is not approval of the current asymmetric matrix for
production attribution, not manuscript evidence, and not a causal result.

The current family roles remain:

- primary: `persistent_joint_cause`;
- sensitivity: `climbing_only`, `transient_perfect_storm`;
- negative references: `habitat_only_null`, `trout_only`.

This review makes a matrix recommendation only. It does not edit tracked CSV
contracts, choose production proposal sampling, choose family weighting,
choose replicate counts, plan remote compute, promote outputs, or interpret
dry-run outcomes.

Goal 006 used the local `apply_module5_intervention_overrides` hook for
`no_trout_pressure`, `no_climbing_pressure`, and
`no_trout_or_climbing_pressure` in the real-proposal dry run. The stale point
is not missing local hook implementation. The remaining matrix issue is that
the tracked intervention contract still labels pressure-removal rows
`design_only`, and production suitability still requires a contract-revision
and approval gate.

## Evidence Inputs Reviewed

- `AGENTS.md`
- `README.md`
- `docs/module5_counterfactual_attribution_plan.md`
- `docs/module5_dry_run_production_spec.md`
- `docs/goals/004-module5-production-readiness/Goal.md`
- `docs/goals/004-module5-production-readiness/Runbook.md`
- `docs/goals/005-module5-dry-run-production-spec/Log.md`
- `docs/goals/006-module5-real-proposal-dry-run/Log.md`
- `data/module5_counterfactual_interventions.csv`
- `data/module4_5_family_decision_table.csv`
- `data/module4_5_proposal_set_membership.csv`
- Existing ignored Goal 006 inspection summary and checks under
  `outputs/module5_dry_run_baseline_current_20260410/inspection/`

The Goal 006 inspection summary reports `all_checks_passed: true`,
`row_count: 50`, `intervention_count: 10`, `expected_replicates: 5`, and
`replicate_coverage: true`. Those facts show coverage of the current matrix,
not production suitability.

## Current Matrix Summary

| family_id | module5_role | current axes | current use |
| --- | --- | --- | --- |
| `persistent_joint_cause` | primary | `status_quo`, `no_trout_pressure`, `no_climbing_pressure`, `no_trout_or_climbing_pressure` | Complete primary pressure-removal block. |
| `climbing_only` | sensitivity | `status_quo`, `no_trout_pressure` | Asymmetric sensitivity block; missing the active-mechanism removal row. |
| `transient_perfect_storm` | sensitivity | `status_quo`, `no_climbing_pressure` | Partial sensitivity block; missing trout and dual-removal separation rows. |
| `habitat_only_null` | negative_reference | `status_quo` | Negative-reference diagnostic only. |
| `trout_only` | negative_reference | `status_quo` | Negative-reference diagnostic only. |

The asymmetry is acceptable for a dry-run/diagnostic matrix because it touches
all current rows and family roles. It is not decision-ready as the production
attribution matrix because the sensitivity-family contrasts do not yet align
cleanly with each family mechanism question.

## Row-By-Row Audit

| intervention_id | current status | recommended label | audit |
| --- | --- | --- | --- |
| `m5_persistent_joint_cause_status_quo` | `implemented` | `production_candidate` | Keep as the primary family baseline. It is a necessary reference row, not an attribution contrast by itself. |
| `m5_persistent_joint_cause_no_trout_pressure` | `design_only` | `production_candidate` | Keep in the primary production block because trout pressure is one of the joint-cause axes. Local hook support exists and was exercised in Goal 006; production use still needs contract promotion and approval. |
| `m5_persistent_joint_cause_no_climbing_pressure` | `design_only` | `production_candidate` | Keep in the primary production block because climbing pressure is one of the joint-cause axes. Local hook support exists and was exercised in Goal 006; production use still needs contract promotion and approval. |
| `m5_persistent_joint_cause_no_trout_or_climbing_pressure` | `design_only` | `production_candidate` | Keep in the primary production block as the joint-removal contrast. Local hook support exists and was exercised in Goal 006; production use still needs contract promotion and approval. |
| `m5_climbing_only_status_quo` | `implemented` | `sensitivity_candidate` | Keep as the climbing-only sensitivity baseline. |
| `m5_climbing_only_no_trout_pressure` | `design_only` | `diagnostic_only` | Keep as a diagnostic/control contrast only. It does not remove the active climbing mechanism and should not be the headline climbing-only sensitivity contrast. |
| `m5_transient_perfect_storm_status_quo` | `implemented` | `sensitivity_candidate` | Keep as the transient-perfect-storm sensitivity baseline. |
| `m5_transient_perfect_storm_no_climbing_pressure` | `design_only` | `sensitivity_candidate` | Keep, because it tests later climbing pressure within the transient family. Local hook support exists and was exercised in Goal 006; the matrix is incomplete without trout and dual-removal companions. |
| `m5_habitat_only_null_negative_reference` | `implemented` | `diagnostic_only` | Keep as a status-quo falsification/reference diagnostic. Exclude from the production attribution ensemble unless a later approval gate says otherwise. |
| `m5_trout_only_negative_reference` | `implemented` | `diagnostic_only` | Keep as a status-quo falsification/reference diagnostic. Exclude from the production attribution ensemble unless a later approval gate says otherwise. |

## Review Question Answers

1. The current `persistent_joint_cause` four-row block is locally executable
   and was exercised/inspected by Goal 006. It is conceptually the right
   primary block, but it is not yet production-ready because the tracked
   contract still labels pressure-removal rows `design_only`, and production
   use requires contract promotion, approval, proportionate validation, and
   later production planning.
2. `climbing_only` should include `no_climbing_pressure` before production
   attribution, because climbing pressure is its active mechanism.
3. `climbing_only` should retain `no_trout_pressure` only as a
   `diagnostic_only` or sensitivity-control row, not as the headline
   climbing-only production contrast.
4. `transient_perfect_storm` should include `no_trout_pressure` and
   `no_trout_or_climbing_pressure` before production attribution, because the
   family needs separation between early trout overshoot, later climbing
   pressure, and their combined removal.
5. Negative references should remain status-quo diagnostics only for the next
   production-matrix revision. They should be outside the production
   attribution ensemble because they have no accepted frontier support.
6. Production should eventually distinguish pressure-removal contrasts from
   state/removal scenarios such as no stocking, no invasion, no transient
   overshoot, or habitat-buffer interventions, but that should be a later
   model-design goal rather than this matrix revision.
7. Current rows should be labelled as in the audit table: primary
   `production_candidate`, sensitivity `sensitivity_candidate`, and negative
   or control rows `diagnostic_only`. No current row needs to be deleted for
   dry-run diagnostics, but the current matrix should not be promoted
   unchanged to production attribution.

## Candidate Row Changes

| candidate change | recommendation | rationale | next action |
| --- | --- | --- | --- |
| Add `climbing_only` / `no_climbing_pressure` | Add before production. | This is the direct active-mechanism removal for the climbing-only sensitivity family. | Add a tracked intervention row in a future contract-revision goal after approval. |
| Keep `climbing_only` / `no_trout_pressure` | Keep only as `diagnostic_only`. | It is useful as a control contrast but does not answer the active climbing-only mechanism question. | Relabel or document as diagnostic in the future contract-revision goal. |
| Add `transient_perfect_storm` / `no_trout_pressure` | Add before production. | It separates early trout-overshoot pressure from later climbing pressure. | Add a tracked intervention row in the future contract-revision goal. |
| Add `transient_perfect_storm` / `no_trout_or_climbing_pressure` | Add before production. | It gives the transient family the same joint-removal contrast available for the primary family. | Add a tracked intervention row in the future contract-revision goal. |
| Keep negative references as status-quo diagnostics | Keep. | They are useful falsification/reference rows but have no accepted frontier support. | Retain outside the production attribution ensemble. |
| Exclude negative references from production attribution | Recommended. | Negative-reference families should not be weighted with accepted-frontier families. | State this explicitly in the production run specification. |
| Add diagnostic interventions for negative references | Not recommended for the next revision. | Extra rows would broaden the design without answering the primary production-matrix gap. | Revisit only in a later falsification/diagnostic goal. |
| Add no-stocking, no-invasion, no-transient-overshoot, or habitat-buffer state scenarios | Defer. | These are model-design scenarios, not simple pressure-removal rows under the current contract. | Create a later design goal if Galaxias/Barry want state/removal scenarios. |

## Negative-Reference Treatment

`habitat_only_null` and `trout_only` should remain in the dry-run/diagnostic
surface as status-quo checks. They should not be part of the production
attribution ensemble unless a later approval gate explicitly changes their
role.

Recommended treatment:

- retain both status-quo rows as `diagnostic_only`;
- do not add pressure-removal rows for negative references in the next matrix
  revision;
- do not weight negative references with accepted-frontier families;
- use negative references only to check that the pipeline can still carry
  non-competitive family contexts without turning them into attribution
  claims.

## Dry-Run Versus Production Matrix

The current matrix should be split into two conceptual surfaces:

| surface | recommended content | status |
| --- | --- | --- |
| Dry-run/diagnostic matrix | Keep the current 10 rows. | Already exercised by Goal 006. Suitable for plumbing, provenance, row coverage, and diagnostic checks. |
| Production attribution matrix | Use accepted-frontier families only and revise sensitivity-family rows before execution. | Not yet approved. Requires a tracked CSV contract-revision goal before production-sized execution. |
| Diagnostic sidecar | Keep `climbing_only` / `no_trout_pressure` and negative-reference status-quo rows outside the headline attribution ensemble. | Useful for review, but not production attribution weighting. |

This split avoids treating the Goal 006 dry-run contract as a silent
production decision.

## Recommendation

Primary recommendation: split the current dry-run/diagnostic matrix from a
future production attribution matrix, and revise the production matrix before
any production-sized execution.

Recommended production-matrix direction after approval:

- keep all four `persistent_joint_cause` rows;
- keep `climbing_only` / `status_quo`;
- add `climbing_only` / `no_climbing_pressure`;
- demote current `climbing_only` / `no_trout_pressure` to a diagnostic sidecar
  unless Galaxias/Barry explicitly want it in a sensitivity appendix;
- keep `transient_perfect_storm` / `status_quo`;
- keep `transient_perfect_storm` / `no_climbing_pressure`;
- add `transient_perfect_storm` / `no_trout_pressure`;
- add `transient_perfect_storm` / `no_trout_or_climbing_pressure`;
- keep `habitat_only_null` and `trout_only` as status-quo diagnostics only,
  outside the production attribution ensemble.

This recommendation is narrower than a production run specification. It does
not decide proposal sampling, weighting, replicate count, compute target,
remote paths, artifact retention, or claim language beyond preserving existing
non-claim boundaries.

## Proposed Next Goal

Recommended next goal: a docs-and-contract revision goal for the Module 5
production intervention matrix.

Suggested scope:

- edit `data/module5_counterfactual_interventions.csv` only after
  Galaxias/Barry approve this recommendation;
- add `m5_climbing_only_no_climbing_pressure`;
- add `m5_transient_perfect_storm_no_trout_pressure`;
- add `m5_transient_perfect_storm_no_trout_or_climbing_pressure`;
- relabel or document `m5_climbing_only_no_trout_pressure` as diagnostic-only;
- keep negative-reference rows as status-quo diagnostics;
- update any validator expectations or docs needed for the revised contract;
- run only proportionate contract/docs validation authorised by that future
  packet;
- stop before production attribution, generated-output promotion, remote
  compute, manuscript claims, commit, or push unless explicitly authorised.

If Galaxias/Barry want no contract edit yet, the fallback is to leave the
current matrix as a dry-run/diagnostic artifact and defer production planning.

## Approval Gates And Stop Points

Stop for explicit approval before:

- editing tracked intervention or outcome-schema CSV contracts;
- adding, removing, renaming, or relabelling intervention rows;
- changing family roles;
- selecting a production proposal source, sample size, family weighting, or
  replicate count;
- changing pressure-removal semantics or adding new scenario hooks;
- running simulations, dry-run commands, production-sized execution, or remote
  probes;
- regenerating or promoting outputs;
- staging, committing, pushing, publishing, or opening a PR;
- making production attribution, final causal, or manuscript-level claims.

Approval should record whether the next matrix is meant to be:

- a revised production attribution matrix;
- a dry-run/diagnostic matrix only;
- or a two-surface design with a production matrix plus diagnostic sidecar.
