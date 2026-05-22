from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.review import write_module1_5_review_bundle


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write the Module 1.5 review bundle.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = write_module1_5_review_bundle(ROOT, output_root=args.output_root)
    print("Wrote Module 1.5 review bundle:")
    print(f"- {outputs['example_summary']}")
    print(f"- {outputs['stochastic_summary']}")
    print(f"- {outputs['review_doc']}")
    print(f"- overall_ready_for_module2={outputs['overall_ready_for_module2']}")


if __name__ == "__main__":
    main()
