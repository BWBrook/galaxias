# Goal 022: Module 5 Validation Consolidation

## Objective

Reduce the maintenance burden of Module 5 validation while preserving every
scientifically consequential check and existing user-facing inspection output.

## Product Promise

Module 5 should have one partition contract, one implementation of each common
output invariant, and thin run-specific inspectors that add only the checks
unique to smoke, dry-run, or matched-counterfactual execution.

## Required Outcomes

1. Move Module 5 partition definitions and intervention-to-partition mapping
   out of the rehearsal implementation into one neutral source of truth.
2. Implement one shared pure check for each common invariant:
   - ordered schema;
   - source-context identity;
   - matched-pair and run identifiers;
   - common-random-number seed pairing.
3. Make smoke, dry-run, execution, and production-summary validation call those
   shared checks while retaining their genuinely profile-specific rules.
4. Move disk-first execution inspection and reporting out of
   `module5_rehearsal.py`; the rehearsal module should retain planning,
   artifact verification, provenance, and execution only.
5. Remove only the confirmed nearby residue:
   - the duplicate uncertainty-summary pass;
   - the caller-free parameter-loading helper;
   - unused execution-task payload fields;
   - the caller-free rehearsal-plan partition mapping property.
6. Preserve existing inspection filenames, check names, summary facts, CLI
   behavior, and scientific failure detection.

## Protected Invariants

- Exact ordered schema validation.
- Proposal source identity and collision detection.
- Matched-pair and baseline/counterfactual run-ID reconstruction.
- Equal baseline and counterfactual stochastic seeds.
- Replicate coverage, intervention/family mapping, partition counts, provenance
  boundaries, and production-summary QC.
- The accepted Module 5 scientific contract and Goal 021's 50-column schema.

## Non-Goals

- No generic validation framework, plugin system, registry, or configuration
  layer.
- No compatibility wrappers for moved private/internal functions.
- No renaming of the rehearsal runner, CLI scripts, public output files, or
  historical reports.
- No production rerun, remote access, scientific reinterpretation, or output
  regeneration.
- No work on `review.py`, prior validation, builder scripts, dependencies,
  administrative history, or Goal 001-021 packets.
- No staging, commit, or push.

## Completion Standard

There is a single production implementation of each common invariant and one
partition mapping. All three inspectors still emit their existing
summary/check/report surfaces. Focused Module 5 tests and `make fast-check`
pass. One focused self-review and at most one material repair pass are enough.
