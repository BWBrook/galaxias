from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.review import write_module2_readiness_bundle


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write the Module 2 readiness bundle.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = write_module2_readiness_bundle(ROOT, output_root=args.output_root)
    print("Wrote Module 2 readiness bundle:")
    print(f"- {outputs['default_target_scores']}")
    print(f"- {outputs['transient_replicate_scores']}")
    print(f"- {outputs['review_doc']}")
    print(f"- historical_core_ready={outputs['historical_core_ready']}")
    print(f"- full_ready_for_module3={outputs['full_ready_for_module3']}")
    print(f"- needs_module_2_5={outputs['needs_module_2_5']}")


if __name__ == "__main__":
    main()
