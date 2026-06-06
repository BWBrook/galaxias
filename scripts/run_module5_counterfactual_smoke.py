from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.module5_counterfactual import (
    DEFAULT_INTERVENTIONS_PATH,
    DEFAULT_OUTCOME_SCHEMA_PATH,
    DEFAULT_OUTPUT_DIR,
    run_module5_counterfactual_smoke,
)


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the tiny local Module 5 counterfactual smoke prototype.",
    )
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    parser.add_argument("--interventions", default=str(ROOT / DEFAULT_INTERVENTIONS_PATH))
    parser.add_argument("--outcome-schema", default=str(ROOT / DEFAULT_OUTCOME_SCHEMA_PATH))
    parser.add_argument("--output-dir", default=str(ROOT / DEFAULT_OUTPUT_DIR))
    parser.add_argument("--intervention-id", action="append", default=[])
    parser.add_argument("--replicates", type=int, default=2)
    parser.add_argument("--proposal-seed", type=int, default=20260605)
    parser.add_argument(
        "--deterministic",
        action="store_true",
        help="Use deterministic simulator mode while preserving matched-pair structure.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_file = run_module5_counterfactual_smoke(
        data_dir=Path(args.data_dir),
        interventions_path=Path(args.interventions),
        outcome_schema_path=Path(args.outcome_schema),
        output_dir=Path(args.output_dir),
        intervention_ids=tuple(args.intervention_id),
        replicates=args.replicates,
        proposal_seed=args.proposal_seed,
        stochastic=not args.deterministic,
    )
    print(f"Wrote Module 5 smoke output: {output_file}")
    print(f"Wrote Module 5 smoke provenance: {output_file.parent / 'provenance.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
