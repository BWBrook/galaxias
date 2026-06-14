# Module 5 Targeted Source/Intervention Audit

## Boundary

This memo records a targeted, read-only remote audit of selected Module 5
production source/intervention units. It is an audit-readiness record for the
Goal 016 endpoint bundle, not final results prose, public-facing wording, or a
final conclusion.

Raw matched outcomes remained on `deep-server-ts`. Only compact audit outputs
were pulled back into the local repository.

## Evidence Basis

Inputs:

- Goal 016 interpretation-gate memo:
  `docs/module5_interpretation_gate_review.md`
- Goal 016 audit targets:
  `data/module5_interpretation_audits/source_intervention_audit_targets.csv`
- Goal 014 production artifact:
  `/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production`

Compact Goal 017 outputs:

- `data/module5_source_intervention_audits/audit_metadata.json`
- `data/module5_source_intervention_audits/selected_audit_targets.csv`
- `data/module5_source_intervention_audits/replicate_distribution_summary.csv`
- `data/module5_source_intervention_audits/negative_subset_sources.csv`

The remote audit workspace was:

```text
/data/codex/scratch/galaxias/module5_goal017_audit_20260614T053513Z
```

## Remote Artifact Verification

Read-only verification on `deep-server-ts` passed before raw-row inspection.

- `sha256sum -c checksums.sha256`: all listed Goal 014 artifact files passed
- raw matched-output SHA:
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`
- raw matched-output size: 435,867,556 bytes
- raw rows scanned remotely by the audit: 279,500
- local raw matched-output copy: none
- broad raw extract: none

## Selected Audit Targets

The authorized audit IDs were exactly:

- `A01`
- `A02`
- `A03`
- `A04`
- `A05`
- `A10`

`A01`, `A02`, `A04`, and `A05` are source-specific primary
persistent-joint-cause checks. `A03` is the primary no-trout negative
persistence subset. `A10` is the transient-perfect-storm no-trout negative
persistence subset.

No `A06` to `A09` sensitivity comparator expansion was performed. No `A11` to
`A14` status/control audit was performed.

## Primary Source-Specific Findings

`A01`: primary combined-pressure persistence source

- source/intervention units audited: 1
- replicate rows summarized: 100
- replicate coverage: 0 to 99
- endpoint: `persistence_2002_contrast`
- min/median/mean/max: 0 / 1 / 0.81 / 1
- negative/zero/positive counts: 0 / 19 / 81
- consistency with Goal 016 compact summary: true

This supports carrying 2002 persistence forward as the lead endpoint example
for source-level review.

`A02`: primary no-climbing persistence source

- source/intervention units audited: 1
- replicate rows summarized: 100
- replicate coverage: 0 to 99
- endpoint: `persistence_2002_contrast`
- min/median/mean/max: -1 / 1 / 0.82 / 1
- negative/zero/positive counts: 1 / 16 / 83
- consistency with Goal 016 compact summary: true

This source remains mostly positive, but the one negative replicate is a useful
caution for single-pressure wording.

`A04`: primary combined-pressure abundance source

- source/intervention units audited: 1
- replicate rows summarized: 100
- replicate coverage: 0 to 99
- endpoint: `min_abundance_1992_2002_contrast`
- min/median/mean/max: 553 / 856.5 / 856.92 / 1,168
- negative/zero/positive counts: 0 / 0 / 100
- consistency with Goal 016 compact summary: true

This supports carrying minimum-abundance contrast as a primary support endpoint
after source-level review.

`A05`: primary combined-pressure lake-refuge source

- source/intervention units audited: 1
- replicate rows summarized: 100
- replicate coverage: 0 to 99
- endpoint: `lake_refuge_share_2002_contrast`
- min/median/mean/max: 0.2436 / 0.7520 / 0.6892 / 0.8966
- negative/zero/positive counts: 0 / 0 / 100
- consistency with Goal 016 compact summary: true

This supports carrying lake-refuge share as the spatial-refuge support endpoint
after source-level review.

## Primary Negative-Subset Findings

`A03`: primary no-trout negative persistence subset

- negative-subset source/intervention units: 40
- replicate rows summarized: 4,000
- units with full replicate coverage: 40
- endpoint: `persistence_2002_contrast`
- min/median/mean/max: -1 / 0 / 0.11075 / 1
- negative/zero/positive counts: 147 / 3,263 / 590
- negative/zero/positive proportions: 0.03675 / 0.81575 / 0.14750
- consistency with Goal 016 compact summary: true

The most negative listed source is
`persistent_joint_cause:p00737` under `ct007_occupancy_primary` seed 20260411:
22 negative, 52 zero, and 26 positive persistence replicates.

This does not overturn the endpoint bundle, but it keeps the primary no-trout
single-pressure row in the "carry with caution" category.

## Transient-Perfect-Storm Negative-Subset Findings

`A10`: transient-perfect-storm no-trout negative persistence subset

- negative-subset source/intervention units: 23
- replicate rows summarized: 2,300
- units with full replicate coverage: 23
- endpoint: `persistence_2002_contrast`
- min/median/mean/max: -1 / 0 / 0.12 / 1
- negative/zero/positive counts: 150 / 1,724 / 426
- negative/zero/positive proportions: 0.06522 / 0.74957 / 0.18522
- consistency with Goal 016 compact summary: true

The most negative listed source is
`transient_perfect_storm:p00726` under `late_bridge_soft` seed 20260410:
22 negative, 55 zero, and 23 positive persistence replicates.

This supports keeping transient-perfect-storm as a sensitivity partition with
explicit caution around the no-trout single-pressure row.

## Endpoint-Bundle Assessment

The Goal 016 endpoint bundle survives the targeted source/intervention audit.

Recommended next review burden remains:

1. `persistence_2002_contrast` as the lead endpoint.
2. `min_abundance_1992_2002_contrast` as primary magnitude support.
3. `lake_refuge_share_2002_contrast` as spatial-refuge support.

The source-specific primary checks are consistent with the compact summaries,
with full replicate coverage and no mismatch against the selected Goal 016
target descriptions. The primary negative subset is real but bounded: it is
concentrated in 40 source/intervention units and remains mostly zero across
replicates.

## Extirpation-Timing Treatment

`extirpation_year_contrast` was not part of the selected Goal 017 target set.
It should remain a secondary heterogeneity and audit-selector endpoint unless
Galaxias authorizes an extirpation-specific audit. This Goal 017 audit does
not justify promoting it above the Goal 016 endpoint bundle.

## Sensitivity And Diagnostic Implications

The A10 audit confirms that the transient-perfect-storm no-trout negative
persistence subset is present in raw replicate distributions and should remain
a caution flag for sensitivity wording.

No selected target changes the Goal 016 treatment of:

- climbing-only as a sensitivity partition;
- transient-perfect-storm as a sensitivity partition;
- diagnostic sidecar rows as diagnostic checks;
- negative-reference rows as QC/context checks.

## Decisions For Galaxias And Barry

1. Confirm whether the endpoint bundle is now accepted for the next
   interpretation review.
2. Decide whether `A03` and `A10` require any additional source-level audit or
   whether their compact negative-subset summaries are sufficient.
3. Decide whether to authorize a narrow extirpation-timing audit or leave
   `extirpation_year_contrast` as secondary/audit-selector only.
4. Decide whether sensitivity wording should mention the A10 negative subset
   explicitly or keep it as internal review context.
5. Decide whether Goal 018 should start interpretation synthesis or first run a
   very small extirpation-specific audit.

## Recommended Goal 018

Recommended default: an interpretation-synthesis gate using the Goal 015
summaries, Goal 016 audit priorities, and Goal 017 compact source/intervention
audit outputs. It should decide the endpoint bundle, source-audit sufficiency,
sensitivity treatment, and exact wording boundaries for any later internal
results memo.

Optional alternative: if Galaxias wants one more raw-row check before
synthesis, Goal 018 should be a narrow extirpation-timing audit on the already
selected source/intervention units, still read-only on `deep-server-ts` and
still pulling back only compact audit outputs.
