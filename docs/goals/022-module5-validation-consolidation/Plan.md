# Goal 022 Plan

1. Confirm clean `main` at the delegated Goal 021 SHA.
2. Characterize the existing shared-check behavior with focused tests before
   moving code. Add new tests only for a distinct invariant not already
   protected.
3. Establish neutral partition and shared-output-check modules.
4. Convert smoke, dry-run, execution, and production-summary validation into
   thin consumers of the shared checks.
5. Extract execution inspection from the rehearsal module without changing its
   emitted files or check semantics.
6. Remove the four confirmed dead/redundant residues named in the Goal.
7. Run focused Module 5 validation, `make fast-check`, structural search checks,
   and diff checks once. Repair only material defects.
8. Leave the result unstaged and uncommitted for Galaxias review.

## Allowed Paths

- `src/galaxias_model/module5_partitions.py`
- `src/galaxias_model/module5_output_checks.py`
- `src/galaxias_model/module5_execution_inspect.py`
- `src/galaxias_model/module5_rehearsal.py`
- `src/galaxias_model/module5_smoke_inspect.py`
- `src/galaxias_model/module5_dry_run_inspect.py`
- `src/galaxias_model/module5_production_summary.py`
- `scripts/inspect_module5_25rep_rehearsal.py`
- `tests/test_module5_output_checks.py`
- `tests/test_module5_smoke_inspection.py`
- `tests/test_module5_dry_run_inspection.py`
- `tests/test_module5_production_rehearsal.py`
- `tests/test_module5_production_summary.py`
- `docs/goals/022-module5-validation-consolidation/Log.md`

The Goal 022 `Goal.md`, `Plan.md`, and `Runbook.md` are part of the authorised
packet but should not be edited by the action agent.
