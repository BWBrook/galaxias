from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.module5_counterfactual import (
    DEFAULT_INTERVENTIONS_PATH,
    DEFAULT_OUTCOME_SCHEMA_PATH,
    run_module5_real_proposal_dry_run,
)
from galaxias_model.module5_proposals import (
    DEFAULT_DRY_RUN_OUTPUT_DIR,
    DEFAULT_DRY_RUN_REPLICATES,
    DEFAULT_MODULE4_MANIFEST_PATH,
    DEFAULT_PARAMETER_VALUES_PATH,
    DEFAULT_PROPOSAL_MEMBERSHIP_PATH,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the approved local Module 5 real-proposal dry run.",
    )
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    parser.add_argument("--proposal-membership", default=str(ROOT / DEFAULT_PROPOSAL_MEMBERSHIP_PATH))
    parser.add_argument("--module4-manifest", default=str(ROOT / DEFAULT_MODULE4_MANIFEST_PATH))
    parser.add_argument("--parameter-values", default=str(ROOT / DEFAULT_PARAMETER_VALUES_PATH))
    parser.add_argument("--interventions", default=str(ROOT / DEFAULT_INTERVENTIONS_PATH))
    parser.add_argument("--outcome-schema", default=str(ROOT / DEFAULT_OUTCOME_SCHEMA_PATH))
    parser.add_argument("--output-dir", default=str(ROOT / DEFAULT_DRY_RUN_OUTPUT_DIR))
    parser.add_argument("--replicates", type=int, default=DEFAULT_DRY_RUN_REPLICATES)
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Use deterministic simulator mode while preserving matched-pair structure.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_file = run_module5_real_proposal_dry_run(
        data_dir=Path(args.data_dir),
        proposal_membership_path=Path(args.proposal_membership),
        module4_manifest_path=Path(args.module4_manifest),
        parameter_values_path=Path(args.parameter_values),
        interventions_path=Path(args.interventions),
        outcome_schema_path=Path(args.outcome_schema),
        output_dir=Path(args.output_dir),
        replicates=args.replicates,
        stochastic=not args.deterministic,
    )
    print(f"Wrote Module 5 real-proposal dry-run output: {output_file}")
    print(f"Wrote Module 5 real-proposal dry-run provenance: {output_file.parent / 'provenance.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
