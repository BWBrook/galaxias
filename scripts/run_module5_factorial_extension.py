from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.module5_counterfactual import (
    DEFAULT_INTERVENTIONS_PATH,
    DEFAULT_OUTCOME_SCHEMA_PATH,
)
from galaxias_model.module5_factorial_extension import (
    DEFAULT_FACTORIAL_EXTENSION_OUTPUT_DIR,
    DEFAULT_FACTORIAL_EXTENSION_REPLICATES,
    run_module5_factorial_extension,
)
from galaxias_model.module5_proposals import (
    DEFAULT_MODULE4_MANIFEST_PATH,
    DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run or preflight the Module 5 shared four-arm extension.",
    )
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    parser.add_argument(
        "--proposal-membership",
        default=str(ROOT / DEFAULT_PROPOSAL_MEMBERSHIP_PATH),
    )
    parser.add_argument(
        "--module4-manifest",
        default=str(ROOT / DEFAULT_MODULE4_MANIFEST_PATH),
    )
    parser.add_argument(
        "--interventions",
        default=str(ROOT / DEFAULT_INTERVENTIONS_PATH),
    )
    parser.add_argument(
        "--outcome-schema",
        default=str(ROOT / DEFAULT_OUTCOME_SCHEMA_PATH),
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / DEFAULT_FACTORIAL_EXTENSION_OUTPUT_DIR),
    )
    parser.add_argument("--run-id", default="local-module5-factorial-extension")
    parser.add_argument(
        "--replicates",
        type=int,
        default=DEFAULT_FACTORIAL_EXTENSION_REPLICATES,
    )
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--artifact-path-preference",
        choices=("auto", "local", "remote"),
        default="auto",
    )
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = run_module5_factorial_extension(
        data_dir=Path(args.data_dir),
        proposal_membership_path=Path(args.proposal_membership),
        module4_manifest_path=Path(args.module4_manifest),
        interventions_path=Path(args.interventions),
        outcome_schema_path=Path(args.outcome_schema),
        output_dir=Path(args.output_dir),
        run_id=args.run_id,
        replicates=args.replicates,
        stochastic=not args.deterministic,
        path_preference=args.artifact_path_preference,
        plan_only=args.plan_only,
        overwrite=args.overwrite,
        workers=args.workers,
    )
    if args.plan_only:
        print(f"Wrote factorial extension plan: {output}")
        print(f"Wrote artifact verification: {output.parent / 'artifact_verification.csv'}")
    else:
        print(f"Wrote factorial extension matched outcomes: {output}")
        print(f"Wrote factorial extension provenance: {output.parent / 'provenance.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
