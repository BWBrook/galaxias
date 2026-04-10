from __future__ import annotations

from pathlib import Path

from galaxias_model.review import write_module2_5_readiness_bundle


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    outputs = write_module2_5_readiness_bundle(ROOT)
    print("Wrote Module 2.5 readiness bundle:")
    print(f"- {outputs['default_bundle_scores']}")
    print(f"- {outputs['transient_bundle_scores']}")
    print(f"- {outputs['review_doc']}")
    print(f"- historical_core_ready={outputs['historical_core_ready']}")
    print(f"- full_ready_for_module3={outputs['full_ready_for_module3']}")
    print(f"- needs_module_2_75={outputs['needs_module_2_75']}")


if __name__ == "__main__":
    main()
