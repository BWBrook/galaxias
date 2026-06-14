from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.module5_dry_run_inspect import (
    DEFAULT_INTERVENTIONS_PATH,
    DEFAULT_OUTCOME_SCHEMA_PATH,
    inspect_module5_real_proposal_dry_run,
)
from galaxias_model.module5_proposals import DEFAULT_DRY_RUN_OUTPUT_DIR, DEFAULT_DRY_RUN_REPLICATES


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect approved local Module 5 real-proposal dry-run outputs from disk.",
    )
    parser.add_argument("--dry-run-dir", default=str(ROOT / DEFAULT_DRY_RUN_OUTPUT_DIR))
    parser.add_argument("--interventions", default=str(ROOT / DEFAULT_INTERVENTIONS_PATH))
    parser.add_argument("--outcome-schema", default=str(ROOT / DEFAULT_OUTCOME_SCHEMA_PATH))
    parser.add_argument("--inspection-dir", default=None)
    parser.add_argument("--expected-replicates", type=int, default=DEFAULT_DRY_RUN_REPLICATES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = inspect_module5_real_proposal_dry_run(
        dry_run_dir=Path(args.dry_run_dir),
        interventions_path=Path(args.interventions),
        outcome_schema_path=Path(args.outcome_schema),
        inspection_dir=Path(args.inspection_dir) if args.inspection_dir else None,
        expected_replicates=args.expected_replicates,
    )
    print(f"Wrote Module 5 dry-run inspection summary: {result.summary_path}")
    print(f"Wrote Module 5 dry-run inspection checks: {result.checks_path}")
    print(f"Wrote Module 5 dry-run inspection report: {result.report_path}")
    if not result.all_checks_passed:
        print("Module 5 real-proposal dry-run inspection failed one or more checks.")
        return 1
    print("Module 5 real-proposal dry-run inspection passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
