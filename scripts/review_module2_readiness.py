from __future__ import annotations

from pathlib import Path

from galaxias_model.review import write_module2_readiness_bundle


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    outputs = write_module2_readiness_bundle(ROOT)
    print("Wrote Module 2 readiness bundle:")
    print(f"- {outputs['default_target_scores']}")
    print(f"- {outputs['transient_replicate_scores']}")
    print(f"- {outputs['review_doc']}")
    print(f"- historical_core_ready={outputs['historical_core_ready']}")
    print(f"- full_ready_for_module3={outputs['full_ready_for_module3']}")
    print(f"- needs_module_2_5={outputs['needs_module_2_5']}")


if __name__ == "__main__":
    main()
