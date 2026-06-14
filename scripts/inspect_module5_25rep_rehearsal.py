from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.module5_counterfactual import DEFAULT_OUTCOME_SCHEMA_PATH
from galaxias_model.module5_rehearsal import (
    DEFAULT_REHEARSAL_OUTPUT_DIR,
    inspect_rehearsal_output,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Module 5 25-replicate rehearsal outputs from disk.",
    )
    parser.add_argument("--rehearsal-dir", default=str(ROOT / DEFAULT_REHEARSAL_OUTPUT_DIR))
    parser.add_argument("--outcome-schema", default=str(ROOT / DEFAULT_OUTCOME_SCHEMA_PATH))
    parser.add_argument("--inspection-dir", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = inspect_rehearsal_output(
        rehearsal_dir=Path(args.rehearsal_dir),
        outcome_schema_path=Path(args.outcome_schema),
        inspection_dir=Path(args.inspection_dir) if args.inspection_dir else None,
    )
    print(f"Wrote Module 5 rehearsal inspection summary: {result.summary_path}")
    print(f"Wrote Module 5 rehearsal inspection checks: {result.checks_path}")
    print(f"Wrote Module 5 rehearsal inspection report: {result.report_path}")
    if not result.all_checks_passed:
        print("Module 5 25-replicate rehearsal inspection failed one or more checks.")
        return 1
    print("Module 5 25-replicate rehearsal inspection passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
