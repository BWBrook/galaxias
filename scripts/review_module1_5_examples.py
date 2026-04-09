from __future__ import annotations

from pathlib import Path

from galaxias_model.review import write_module1_5_review_bundle


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    outputs = write_module1_5_review_bundle(ROOT)
    print("Wrote Module 1.5 review bundle:")
    print(f"- {outputs['example_summary']}")
    print(f"- {outputs['stochastic_summary']}")
    print(f"- {outputs['review_doc']}")
    print(f"- overall_ready_for_module2={outputs['overall_ready_for_module2']}")


if __name__ == "__main__":
    main()
