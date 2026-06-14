from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.module5_counterfactual import (
    DEFAULT_INTERVENTIONS_PATH,
    DEFAULT_OUTCOME_SCHEMA_PATH,
)
from galaxias_model.module5_proposals import (
    DEFAULT_MODULE4_MANIFEST_PATH,
    DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
)
from galaxias_model.module5_rehearsal import (
    DEFAULT_REHEARSAL_OUTPUT_DIR,
    DEFAULT_REHEARSAL_REPLICATES,
    run_module5_25rep_rehearsal,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run or preflight the Module 5 25-replicate production rehearsal.",
    )
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    parser.add_argument("--proposal-membership", default=str(ROOT / DEFAULT_PROPOSAL_MEMBERSHIP_PATH))
    parser.add_argument("--module4-manifest", default=str(ROOT / DEFAULT_MODULE4_MANIFEST_PATH))
    parser.add_argument("--interventions", default=str(ROOT / DEFAULT_INTERVENTIONS_PATH))
    parser.add_argument("--outcome-schema", default=str(ROOT / DEFAULT_OUTCOME_SCHEMA_PATH))
    parser.add_argument("--output-dir", default=str(ROOT / DEFAULT_REHEARSAL_OUTPUT_DIR))
    parser.add_argument("--run-id", default="local-module5-25rep-rehearsal")
    parser.add_argument("--replicates", type=int, default=DEFAULT_REHEARSAL_REPLICATES)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--artifact-path-preference",
        choices=("auto", "local", "remote"),
        default="auto",
    )
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Use deterministic simulator mode while preserving matched-pair structure.",
    )
    parser.add_argument(
        "--plan-only",
        action="store_true",
        help="Write the rehearsal plan and artifact verification without running simulations.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing matched_outcomes.csv in the output directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_file = run_module5_25rep_rehearsal(
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
        print(f"Wrote Module 5 rehearsal preflight plan: {output_file}")
        print(f"Wrote Module 5 rehearsal artifact verification: {output_file.parent / 'artifact_verification.csv'}")
    else:
        print(f"Wrote Module 5 rehearsal matched outcomes: {output_file}")
        print(f"Wrote Module 5 rehearsal provenance: {output_file.parent / 'provenance.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
