from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.module5_smoke_inspect import (
    DEFAULT_OUTCOME_SCHEMA_PATH,
    DEFAULT_SMOKE_DIR,
    inspect_module5_counterfactual_smoke,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect tiny local Module 5 counterfactual smoke outputs from disk.",
    )
    parser.add_argument("--smoke-dir", default=str(ROOT / DEFAULT_SMOKE_DIR))
    parser.add_argument("--outcome-schema", default=str(ROOT / DEFAULT_OUTCOME_SCHEMA_PATH))
    parser.add_argument("--inspection-dir", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = inspect_module5_counterfactual_smoke(
        smoke_dir=Path(args.smoke_dir),
        outcome_schema_path=Path(args.outcome_schema),
        inspection_dir=Path(args.inspection_dir) if args.inspection_dir else None,
    )
    print(f"Wrote Module 5 smoke inspection summary: {result.summary_path}")
    print(f"Wrote Module 5 smoke inspection checks: {result.checks_path}")
    print(f"Wrote Module 5 smoke inspection report: {result.report_path}")
    if not result.all_checks_passed:
        print("Module 5 smoke inspection failed one or more checks.")
        return 1
    print("Module 5 smoke inspection passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
