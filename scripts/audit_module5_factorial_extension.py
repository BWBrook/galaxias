from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

from galaxias_model.module5_factorial_extension_audit import (
    write_factorial_extension_audit,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect and audit a Module 5 shared four-arm extension.",
    )
    parser.add_argument("--matched-outcomes", required=True)
    parser.add_argument("--provenance", required=True)
    parser.add_argument(
        "--outcome-schema",
        default=str(ROOT / "data/module5_counterfactual_outcome_schema.csv"),
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--source-artifact", required=True)
    parser.add_argument("--source-execution-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-row-count", type=int, required=True)
    parser.add_argument("--expected-replicates", type=int, required=True)
    parser.add_argument(
        "--goal026-prefix-summary",
        default=str(
            ROOT
            / "data/module5_interaction_stability/prefix_stability_summary.csv"
        ),
    )
    parser.add_argument(
        "--qc-only",
        action="store_true",
        help="Run structural shared-block checks without stability summaries.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = write_factorial_extension_audit(
        matched_outcomes_path=Path(args.matched_outcomes),
        provenance_path=Path(args.provenance),
        outcome_schema_path=Path(args.outcome_schema),
        output_dir=Path(args.output_dir),
        expected_sha256=args.expected_sha256,
        source_artifact=Path(args.source_artifact),
        source_execution_sha=args.source_execution_sha,
        run_id=args.run_id,
        command=" ".join(shlex.quote(part) for part in sys.argv),
        expected_row_count=args.expected_row_count,
        expected_replicates=args.expected_replicates,
        qc_only=args.qc_only,
        goal026_prefix_summary_path=(
            None if args.qc_only else Path(args.goal026_prefix_summary)
        ),
    )
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
