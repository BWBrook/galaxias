from __future__ import annotations

import argparse
from pathlib import Path

from galaxias_model import Module3Config
from galaxias_model.review import write_module3_readiness_bundle


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write the Module 3 readiness bundle.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Calibration output directory (default: OUTPUT_ROOT/outputs/module3/readiness_primary).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = Module3Config.readiness_defaults(output_dir=args.output_dir) if args.output_dir is not None else None
    outputs = write_module3_readiness_bundle(ROOT, output_root=args.output_root, config=config)
    print("Wrote Module 3 readiness bundle:")
    print(f"- {outputs['family_summary']}")
    print(f"- {outputs['accepted_summary']}")
    print(f"- {outputs['review_doc']}")
    print(f"- scientific_ready_for_module4={outputs['scientific_ready_for_module4']}")
    print(f"- needs_module_3_5={outputs['needs_module_3_5']}")


if __name__ == "__main__":
    main()
