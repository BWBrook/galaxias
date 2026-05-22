from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model.review import write_module3_readiness_bundle


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write the Module 3 readiness bundle.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = write_module3_readiness_bundle(ROOT, output_root=args.output_root)
    print("Wrote Module 3 readiness bundle:")
    print(f"- {outputs['family_summary']}")
    print(f"- {outputs['accepted_summary']}")
    print(f"- {outputs['review_doc']}")
    print(f"- full_ready_for_module4={outputs['full_ready_for_module4']}")
    print(f"- needs_module_3_5={outputs['needs_module_3_5']}")


if __name__ == "__main__":
    main()
