from __future__ import annotations

import argparse
import json
from pathlib import Path

from galaxias_model import (
    ScoringConfig,
    SimulationConfig,
    aggregate_replicate_scores,
    load_model_inputs,
    resolve_family_parameters,
    run_historical_simulation,
    score_historical_run,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score one or more historical latent runs against CT001-CT012.")
    parser.add_argument("--family-id", required=True)
    parser.add_argument("--seed", type=int, default=1)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--deterministic", action="store_true")
    mode.add_argument("--stochastic", action="store_true")
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stochastic = not args.deterministic
    sim_config = SimulationConfig(stochastic=stochastic)
    scoring_config = ScoringConfig()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    model_inputs = load_model_inputs(DATA_DIR)
    params = resolve_family_parameters(model_inputs, args.family_id)

    scoring_results = []
    for offset in range(args.replicates):
        seed = args.seed + offset
        simulation_result = run_historical_simulation(params, args.family_id, sim_config, seed=seed)
        scoring_results.append(score_historical_run(simulation_result, model_inputs, scoring_config))

    if args.replicates == 1:
        result = scoring_results[0]
        result.projection_table.to_csv(output_dir / "projection.csv", index=False)
        result.target_score_table.to_csv(output_dir / "target_scores.csv", index=False)
        with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
            json.dump(result.summary, handle, indent=2)
    else:
        aggregate = aggregate_replicate_scores(scoring_results, scoring_config)
        aggregate.replicate_score_table.to_csv(output_dir / "replicate_target_scores.csv", index=False)
        aggregate.aggregate_target_score_table.to_csv(output_dir / "aggregate_target_scores.csv", index=False)
        with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
            json.dump(aggregate.summary, handle, indent=2)


if __name__ == "__main__":
    main()
