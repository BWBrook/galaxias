from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

from galaxias_model.module5_production_summary import write_production_summaries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write compact Module 5 production summaries from remote matched outcomes.",
    )
    parser.add_argument("--matched-outcomes", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--source-artifact", required=True)
    parser.add_argument("--source-execution-sha", required=True)
    parser.add_argument("--goal014-record-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--label", default="goal015-module5-production-summary")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = " ".join(shlex.quote(item) for item in sys.argv)
    result = write_production_summaries(
        matched_outcomes_path=Path(args.matched_outcomes),
        output_dir=Path(args.output_dir),
        expected_sha256=args.expected_sha256,
        source_artifact=Path(args.source_artifact),
        source_execution_sha=args.source_execution_sha,
        goal014_record_sha=args.goal014_record_sha,
        run_id=args.run_id,
        command=command,
        label=args.label,
    )
    print(f"Wrote Module 5 production summary metadata: {result.metadata_path}")
    print(f"Wrote Module 5 production QC summary: {result.qc_summary_path}")
    print(
        "Wrote Module 5 partition endpoint summary: "
        f"{result.partition_endpoint_summary_path}"
    )
    print(
        "Wrote Module 5 source/intervention endpoint summary: "
        f"{result.source_intervention_endpoint_summary_path}"
    )
    print(f"Wrote Module 5 direction summary: {result.direction_summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
