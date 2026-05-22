from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model import Module3Config
from galaxias_model.review import write_module3_5_diagnostic_bundle


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write the Module 3.5 diagnostic bundle.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--stage-a-draws-per-family", type=int, default=250)
    parser.add_argument("--stage-a-keep-per-family", type=int, default=20)
    parser.add_argument("--stage-b-historical-replicates", type=int, default=5)
    parser.add_argument("--final-acceptance-fraction", type=float, default=0.10)
    parser.add_argument("--final-acceptance-cap", type=int, default=10)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260410)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir or (ROOT / "outputs" / "module3_5" / "diagnostic_primary")
    config = Module3Config(
        stage_a_draws_per_family=args.stage_a_draws_per_family,
        stage_a_keep_per_family=args.stage_a_keep_per_family,
        stage_b_historical_replicates=args.stage_b_historical_replicates,
        final_acceptance_fraction=args.final_acceptance_fraction,
        final_acceptance_cap=args.final_acceptance_cap,
        workers=args.workers,
        batch_size=args.batch_size,
        master_seed=args.seed,
        stochastic_baselines=False,
        output_dir=output_dir,
        resume=False,
    )
    outputs = write_module3_5_diagnostic_bundle(ROOT, output_root=args.output_root, config=config)
    print("Wrote Module 3.5 diagnostic bundle:")
    print(f"- {outputs['family_summary']}")
    print(f"- {outputs['sampler_failures']}")
    print(f"- {outputs['stage_b_frontier']}")
    print(f"- {outputs['family_best_stage_b']}")
    print(f"- {outputs['target_leverage']}")
    print(f"- {outputs['accepted_target_penalties']}")
    print(f"- {outputs['best_proposal_target_penalties']}")
    print(f"- {outputs['target_omission_sensitivity']}")
    print(f"- {outputs['review_doc']}")
    print(f"- winning_family={outputs['winning_family']}")
    print(f"- target_omission_flip_count={outputs['target_omission_flip_count']}")
    print(f"- recommended_next_step={outputs['recommended_next_step']}")


if __name__ == "__main__":
    main()
