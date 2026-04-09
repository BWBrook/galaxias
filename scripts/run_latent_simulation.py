from __future__ import annotations

import argparse
import json
from pathlib import Path

from galaxias_model import (
    SimulationConfig,
    load_model_inputs,
    resolve_family_parameters,
    run_historical_simulation,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Tier 1 latent Pedder galaxias simulation kernel.")
    parser.add_argument("--family-id", required=True)
    parser.add_argument("--seed", type=int, default=1)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--deterministic", action="store_true")
    mode.add_argument("--stochastic", action="store_true")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stochastic = not args.deterministic
    config = SimulationConfig(stochastic=stochastic)

    model_inputs = load_model_inputs(DATA_DIR)
    params = resolve_family_parameters(model_inputs, args.family_id)
    result = run_historical_simulation(params, args.family_id, config, seed=args.seed)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    result.trajectory_table.to_csv(output_dir / "trajectory.csv", index=False)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(result.summary, handle, indent=2)
    with (output_dir / "resolved_parameters.json").open("w", encoding="utf-8") as handle:
        json.dump(result.resolved_parameters.as_jsonable(), handle, indent=2)


if __name__ == "__main__":
    main()
