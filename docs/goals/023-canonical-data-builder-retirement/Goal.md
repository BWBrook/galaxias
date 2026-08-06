# Goal 023: Canonical Data Builder Retirement

## Objective

Remove the two legacy scripts that duplicate the canonical evidence and prior
tables as thousands of lines of embedded Python data, while preserving the
scientific tables, their active consumers, and their independent validation.

## Product Promise

The repository should have one current source of truth for curated evidence
and prior contracts: the tracked CSV tables themselves. Historical
construction remains recoverable from Git; active code should not retain a
second, stale copy capable of overwriting later curation.

## Required Outcomes

1. Verify the exact seven tracked outputs and current repository consumers of:
   - `scripts/build_evidence_ledger.py`;
   - `scripts/build_prior_pack.py`.
2. Record hashes of the seven canonical CSVs before any deletion and confirm
   that they remain byte-for-byte unchanged at completion.
3. Delete both legacy builders once the audit confirms that no live command,
   test, or runtime path invokes them and that their embedded scientific rows
   already exist in the tracked CSVs.
4. Update `data/README.md` so the seven tables are described as canonical
   curated inputs, not generated outputs. Keep the independent prior-pack
   validator authoritative.
5. If a scientifically consequential invariant exists only in a builder,
   either retain that builder and report the blocker or move only that minimal
   invariant into the existing validator with focused coverage. Do not retain
   a builder merely as a historical reconstruction recipe.
6. Remove stale active references to the deleted builder commands, while
   leaving clearly historical audit prose untouched.

## Canonical Tables And Protected Invariants

- `data/source_register.csv`
- `data/evidence_ledger.csv`
- `data/proxy_evidence_leads.csv`
- `data/priority_source_gaps.csv`
- `data/parameter_priors.csv`
- `data/model_family_parameter_map.csv`
- `data/parameter_constraints.csv`
- Evidence identifiers consumed by model-specification and prior validation.
- Prior schema, family completeness, constraints, source strategies,
  transforms, bounds, defaults, and evidence links enforced by
  `scripts/validate_prior_pack.py`.
- Existing runtime loading through `src/galaxias_model/io.py`.

## Non-Goals

- No deletion or content change to any canonical CSV.
- No archive, compatibility wrapper, migration, data manifest, replacement
  generator, or deletion ledger.
- No redesign of the evidence ledger, priors, model families, constraints, or
  scientific interpretation.
- No work on `src/galaxias_model/review.py`, other builders, goal history, or
  generated outputs.
- No remote access, simulation, staging, commit, or push.

## Completion Standard

The two redundant builders and active references are absent; all seven tables
match their baseline hashes; the prior validator and full fast gate pass; and
the retained data flow is documented plainly. Perform one focused self-review
and at most one material repair pass.
