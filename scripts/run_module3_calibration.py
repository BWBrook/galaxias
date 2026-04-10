from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model import Module3Config, load_model_inputs, run_module3_calibration_stage


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Module 3 two-stage ABC calibration harness.")
    parser.add_argument("--stage", choices=["all", "stage_a", "stage_b"], default="all")
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--stage-a-draws-per-family", type=int, default=2000)
    parser.add_argument("--stage-a-keep-per-family", type=int, default=100)
    parser.add_argument("--stage-b-historical-replicates", type=int, default=20)
    parser.add_argument("--final-acceptance-fraction", type=float, default=0.10)
    parser.add_argument("--final-acceptance-cap", type=int, default=50)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260410)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--stochastic-baselines", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = ROOT / "data"
    model_inputs = load_model_inputs(data_dir)
    output_dir = args.output_dir if args.output_dir is not None else Module3Config().output_dir
    config = Module3Config(
        families=tuple(args.families) if args.families else Module3Config().families,
        stage_a_draws_per_family=args.stage_a_draws_per_family,
        stage_a_keep_per_family=args.stage_a_keep_per_family,
        stage_b_historical_replicates=args.stage_b_historical_replicates,
        final_acceptance_fraction=args.final_acceptance_fraction,
        final_acceptance_cap=args.final_acceptance_cap,
        workers=args.workers,
        batch_size=args.batch_size,
        master_seed=args.seed,
        stochastic_baselines=args.stochastic_baselines,
        output_dir=output_dir,
        resume=args.resume,
    )
    result = run_module3_calibration_stage(model_inputs, config, stage=args.stage)
    print("Wrote Module 3 calibration outputs:")
    print(f"- {config.output_dir / 'run_manifest.json'}")
    print(f"- {config.output_dir / 'proposal_summary.csv.gz'}")
    print(f"- {config.output_dir / 'parameter_values.csv.gz'}")
    print(f"- {config.output_dir / 'target_scores.csv.gz'}")
    print(f"- {config.output_dir / 'family_summary.csv'}")
    print(f"- {config.output_dir / 'accepted_proposals.csv'}")
    print(f"- stage={args.stage}")
    print(f"- accepted={len(result.accepted_proposals_table)}")


if __name__ == "__main__":
    main()
