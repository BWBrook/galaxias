# Goal 023 Log

## Delegation State

- Baseline: `main` at `1f46d8809761a1eae018e8683942befa941bf165`.
- Publish boundary: none; leave all Goal 023 changes unstaged and uncommitted.
- Scope: retire two duplicate embedded-data builders while preserving seven
  canonical tracked CSVs and their scientific validation.

## Orchestrator Reconnaissance

- `scripts/build_evidence_ledger.py`: 2,024 lines; writes four tracked evidence
  tables.
- `scripts/build_prior_pack.py`: 1,136 lines; writes three tracked prior
  tables.
- No Makefile target, runtime code, or test invokes either builder.
- Active model and validation code consume the tracked CSV outputs directly.
- `scripts/validate_prior_pack.py` independently validates the prior pack and
  is retained.
- Decision: tracked CSVs are the canonical curated scientific inputs. Git
  preserves the historical construction; active Python should not duplicate
  every row or overwrite subsequent curation.

## Action-Agent Record

### Baseline And Audit

- Confirmed `main` at `1f46d8809761a1eae018e8683942befa941bf165` with
  only this untracked Goal 023 packet present.
- Baseline SHA-256 receipt:

```text
f4108817336ccb36b8c0166850b4ee1a03f2179492daa11b954ef5bfafa51fbf  data/source_register.csv
d7e030a3225e567504f86fc06b5cb5c943f6ff0db4cad4fce6c837fa69fac6ec  data/evidence_ledger.csv
19eb40b2eecdce0117adecd854eb54ba30970f3817b68a71e7a83bcb7e022f86  data/proxy_evidence_leads.csv
2a9fcc63dd275afb2a4af79cffe347fbe1b084ebff1aca45bfa34a0aa1d44f50  data/priority_source_gaps.csv
0430990010becb5c1dbbad5a60a64ab87a754657afa4ac902914c101dde3e718  data/parameter_priors.csv
eca7781b2b3c59232a0f3e0adb56569fa5a627daa5342b3d07da1f43d1ff13a0  data/model_family_parameter_map.csv
b4aa87f4d4972a287ecb68958033694d5535c1e8ddfaf3a46f4d70885d356816  data/parameter_constraints.csv
```

- Repository search found no Makefile target, test, runtime path, or active
  command invoking either builder. The only current instructional reference
  was the stale generated-output statement in `data/README.md`; the remaining
  builder reference is clearly historical audit prose.
- Read-only row comparison confirmed that every tracked CSV has the builder's
  exact schema and embedded rows: 29 sources, 56 evidence rows, 14 proxy
  leads, 5 priority gaps, 40 priors, 200 family-map rows, and 10 constraints.
- Current consumers read the CSVs directly: `src/galaxias_model/io.py` loads
  the evidence ledger and three prior-pack tables; the independent prior
  validator loads the same four tables; portability checks consume the source
  register; and `scripts/build_model_spec_pack.py` consumes the evidence
  ledger.
- The prior builder alone required every `direct_pedder` prior to cite at
  least one evidence identifier. This is consequential provenance protection,
  so it will be transferred minimally to the retained validator with focused
  coverage before the builder is deleted.

### Execution State

- Deleted `scripts/build_evidence_ledger.py` and
  `scripts/build_prior_pack.py`; both are absent from the working tree and
  appear as intended deletions. The real Git index remains untouched.
- Updated `data/README.md` to identify all seven protected tables as canonical
  curated inputs and removed the stale prior-builder instruction.
- Added the builder-only `direct_pedder` evidence-link invariant to
  `scripts/validate_prior_pack.py` and covered it in the narrowly scoped
  `tests/test_validate_prior_pack.py`.

### Validation And Final Receipt

- `uv run python scripts/validate_prior_pack.py`: passed with 40 priors, 200
  family-map rows, and 10 constraints.
- A first literal `make fast-check` reached the portability check and stopped
  because its `git ls-files` discovery includes deleted-but-unstaged paths.
  This is an index-state limitation, not a portability defect in the final
  tree.
- Re-ran `make fast-check` against a temporary external Git index representing
  the post-deletion tree; the actual repository index was not modified.
  Portability passed for 316 files, compile passed, and pytest reported 95
  passed with 5 slow tests deselected.
- The first focused test version assumed `scripts` was importable as a package.
  The one allowed repair pass changed the test to load the standalone
  validator by file path, after which the full fast gate passed.
- `git diff --check`: passed.
- Final SHA-256 values for all seven canonical CSVs exactly match the baseline
  receipt above; `git diff` reports no change to any protected CSV.
- Final search found no active builder command or current data documentation.
  The sole reference outside the Goal packet is historical audit prose in
  `docs/galaxias_repo_audit_module45_feedback.md` and was intentionally left
  unchanged.

### Retained Flow And Residual Risk

- Curated evidence remains in the four evidence CSVs. Model-spec construction,
  portability checking, prior validation, and runtime loading continue to read
  their required canonical CSVs directly.
- Curated prior contracts remain in the three prior-pack CSVs. The independent
  validator remains authoritative and now preserves every consequential check
  formerly present in the builder, including the direct-evidence provenance
  requirement.
- Historical reconstruction remains available through Git history. No archive,
  replacement builder, compatibility layer, manifest, simulation, remote work,
  staging, commit, or push was introduced.
- Material residual risk is low: the normal portability target cannot inspect
  an unstaged-deletion worktree without seeing the deleted index entries. The
  temporary-index pass validates the exact post-retirement file set, and the
  normal target will use that same set once an authorized later commit records
  the deletions.
