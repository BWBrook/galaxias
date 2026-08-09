from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

from galaxias_model.module5_interaction_stability import (
    write_interaction_stability_audit,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Module 5 factorial interaction and Monte Carlo stability "
            "from existing matched outcomes."
        )
    )
    parser.add_argument("--matched-outcomes", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--source-artifact", required=True)
    parser.add_argument("--source-execution-sha", required=True)
    parser.add_argument("--goal014-record-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-row-count", type=int, default=279500)
    parser.add_argument("--expected-replicates", type=int, default=100)
    parser.add_argument("--expected-contexts", type=int, default=15)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = write_interaction_stability_audit(
        matched_outcomes_path=Path(args.matched_outcomes),
        output_dir=Path(args.output_dir),
        expected_sha256=args.expected_sha256,
        source_artifact=Path(args.source_artifact),
        source_execution_sha=args.source_execution_sha,
        goal014_record_sha=args.goal014_record_sha,
        run_id=args.run_id,
        command=" ".join(shlex.quote(part) for part in sys.argv),
        expected_row_count=args.expected_row_count,
        expected_replicates=args.expected_replicates,
        expected_contexts=args.expected_contexts,
    )
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
