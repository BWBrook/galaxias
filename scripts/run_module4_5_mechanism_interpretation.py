from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.mechanism_interpretation import (
    MODULE4_5_MANDATORY_OUTPUTS,
    generate_module4_5_outputs,
    module4_5_output_paths,
    render_module4_5_review_from_outputs,
    validate_module4_raw_artifact_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODULE4_ROOT = ROOT / "outputs" / "remote" / "module4_observation_sensitivity_20260522T101942Z"
DEFAULT_MANIFEST = ROOT / "data" / "module4_raw_artifact_manifest.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Module 4.5 mechanism interpretation workflow.")
    parser.add_argument("--module4-root", type=Path, default=DEFAULT_MODULE4_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--publish-root", type=Path, default=ROOT)
    parser.add_argument("--near-frontier-delta", type=float, default=10.0)
    parser.add_argument("--near-frontier-relative", type=float, default=1.05)
    parser.add_argument("--trajectory-sample", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260523)
    parser.add_argument("--verify-hashes", action="store_true")
    parser.add_argument(
        "--summarize-only",
        action="store_true",
        help="Re-render the Markdown review from already-derived Module 4.5 tables.",
    )
    parser.add_argument(
        "--smoke-only",
        action="store_true",
        help="Validate inputs and output contract without generating Module 4.5 result tables.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.summarize_only:
        review_path = render_module4_5_review_from_outputs(args.publish_root)
        print(f"Module 4.5 review re-rendered: {review_path}")
        return 0

    validation = validate_module4_raw_artifact_manifest(
        args.manifest,
        args.module4_root,
        verify_hashes=args.verify_hashes,
    )
    if not validation.passed:
        print("Module 4.5 input validation failed:")
        for label, values in [
            ("missing files", validation.missing_files),
            ("missing roles", validation.missing_roles),
            ("hash mismatches", validation.hash_mismatches),
        ]:
            if values:
                print(f"- {label}:")
                for value in values:
                    print(f"  - {value}")
        return 1

    output_paths = module4_5_output_paths(args.publish_root)
    print("Module 4.5 input validation passed:")
    print(f"- manifest: {args.manifest}")
    print(f"- module4_root: {args.module4_root}")
    print(f"- runs: {validation.run_count}")
    print(f"- artifact_records: {validation.record_count}")
    print(f"- near_frontier_delta: {args.near_frontier_delta:g}")
    print(f"- near_frontier_relative: {args.near_frontier_relative:g}")
    print(f"- trajectory_sample: {args.trajectory_sample}")
    print(f"- seed: {args.seed}")
    print("- mandatory_outputs:")
    for output in MODULE4_5_MANDATORY_OUTPUTS:
        print(f"  - {output_paths[output]}")

    if args.smoke_only:
        return 0

    result = generate_module4_5_outputs(
        module4_root=args.module4_root,
        manifest_path=args.manifest,
        publish_root=args.publish_root,
        near_frontier_delta=args.near_frontier_delta,
        near_frontier_relative=args.near_frontier_relative,
        trajectory_sample=args.trajectory_sample,
        seed=args.seed,
        verify_hashes=args.verify_hashes,
    )
    print("Module 4.5 outputs generated:")
    for output in MODULE4_5_MANDATORY_OUTPUTS:
        print(f"- {result.output_paths[output]} ({result.row_counts.get(output, 'written')} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
