# Module 5 100-Replicate Production Execution Report

## Boundary

Goal 014 executed and inspected the full 100-replicate Module 5 production
run on `deep-server-ts` from frozen source SHA
`ddb8a6de583e85f170f46c9dec9b1246baa6dccc`.

This report is an execution and disk-inspection record only. It is not
production attribution interpretation, not a final causal effect claim, not
manuscript evidence, and not figure, table, abstract, or supplement language.
Raw matched outcomes remain remote-only.

## Source Transport

The initial GitHub SSH clone path was blocked by remote GitHub public-key
authentication. In the authorized review iteration, the remote source checkout
was created from a local Git bundle rather than from GitHub.

Source-transport evidence:

- local HEAD before bundling:
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`;
- Goal 014 packet absent from the frozen commit tree: true;
- final bundle source: local Git object database, via `HEAD` after verifying
  local `HEAD` exactly matched the frozen SHA;
- local bundle:
  `/tmp/galaxias-ddb8a6de583e85f170f46c9dec9b1246baa6dccc-20260614T031501Z.bundle`;
- local bundle SHA-256:
  `0e61facae852b4fe2a6c3a08ab9c9b7a8bbca54358726e13dc225dcd3616d1b9`;
- bundle head:
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc HEAD`;
- remote bundle:
  `/data/codex/scratch/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/source_bundle/galaxias-ddb8a6de583e85f170f46c9dec9b1246baa6dccc.bundle`;
- remote source checkout:
  `/data/codex/repos/galaxias-goal014-m5-100rep-production-20260614T031501Z-goal014-m5-100rep-production`;
- remote checkout HEAD:
  `ddb8a6de583e85f170f46c9dec9b1246baa6dccc`;
- remote checkout status: clean detached `HEAD`;
- Goal 014 packet absent from remote execution source: true.

## Run Identity

- remote alias: `deep-server-ts`;
- host/user: `deep-server` / `bwbrook`;
- run ID: `20260614T031501Z-goal014-m5-100rep-production`;
- tmux session: `galaxias-m5-prod-20260614T031501Z`;
- scratch:
  `/data/codex/scratch/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production`;
- artifact:
  `/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production`;
- output directory:
  `/data/codex/scratch/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production`;
- worker count: 32;
- replicate count: 100;
- start UTC: `2026-06-14T03:18:07Z`;
- end UTC: `2026-06-14T03:30:51Z`;
- duration: 764 seconds;
- execution exit: 0;
- tmux command exit: 0.

## Preflight

Local and remote plan-only preflights matched the Goal 014 invariants:

- expected rows: 279,500;
- source/intervention units: 2,795;
- distinct `proposal_source_key` values: 780;
- source contexts: 15;
- artifact verification rows: 15;
- all artifacts verified: true;
- total verified parameter bytes: 57,941,680.

The remote plan-only preflight used `remote_artifact_path` for all 15
`parameter_values.csv.gz` artifacts.

Partition row counts:

| partition | rows |
| --- | ---: |
| `headline/persistent_joint_cause` | 106,000 |
| `headline/climbing_only` | 47,000 |
| `headline/transient_perfect_storm` | 100,000 |
| `diagnostic_sidecar/climbing_only_no_trout_pressure` | 23,500 |
| `negative_reference/habitat_only_null` | 1,500 |
| `negative_reference/trout_only` | 1,500 |

## Inspection

The disk inspection passed all required checks.

| fact | value |
| --- | --- |
| all checks passed | true |
| row count | 279,500 |
| column count | 53 |
| expected replicates | 100 |
| replicate IDs | `0..99` |
| source/intervention units | 2,795 |
| distinct `proposal_source_key` values | 780 |
| source identity | true |
| replicate coverage | true |
| matched-pair IDs | true |
| schema columns | true |
| seed mismatches | 0 |
| provenance status | `module5_25rep_rehearsal` |
| `production_attribution` | false |

The provenance status string remains `module5_25rep_rehearsal` because the
frozen accepted runner was reused with `--replicates 100`, as allowed by the
Goal 014 packet.

## Remote Artifacts

Raw matched outcomes remain remote-only:

- path:
  `/data/codex/artifacts/galaxias/module5_100rep_production_20260614T031501Z-goal014-m5-100rep-production/outputs/module5_100rep_production/matched_outcomes.csv`;
- size: 435,867,556 bytes;
- SHA-256:
  `ef8d9a5fca70a253c972c7d8483654b42f0351e361e852258b5c814dfebdc727`.

Remote footprint:

- source checkout: 326M;
- scratch: 422M;
- artifact: 416M.

The artifact directory includes the run scripts, execution log, timing file,
source-transport note, matched-output checksum, output plan, artifact
verification CSV, provenance JSON, inspection summary/checks/report, artifact
inventory, and `checksums.sha256`.

Final checksum verification:

- `sha256sum -c checksums.sha256`: passed for all listed files.

## Deviations And Notes

- The previous blocked run
  `20260614T031037Z-goal014-m5-100rep-production` was left untouched as
  blocker evidence; it produced no source checkout, artifact directory, tmux
  session, or matched outcomes.
- The literal raw-SHA bundle command returned Git's empty-bundle guard because
  a bare object ID was not a named ref for bundle export. The final bundle used
  `HEAD` only after verifying local `HEAD` exactly matched the frozen source
  SHA, and the frozen commit tree excluded the untracked Goal 014 packet.
- A remote `git bundle verify` attempt outside a Git repository failed before
  clone; verification was then run successfully inside the bundle-created
  checkout.
- One local here-doc quoting attempt failed before SSH while preparing the
  tmux launch command. No remote launch or artifact mutation occurred from
  that attempt.
- The artifact inventory was regenerated with a temporary file outside the
  artifact tree, then checksums were regenerated and verified.

These operational notes did not change the frozen source SHA, remote target,
replicate count, worker count, intervention contract, proposal selection,
family treatment, pressure-removal semantics, inspection gates, or raw-output
policy.

## Stop Point

Goal 014 stops at production execution and inspection. A later Goal 015 should
review the remote inspection artifacts and define any compact summary or
interpretation workflow before any production attribution interpretation,
causal language, manuscript text, figure/table work, or raw-output pull-back.
