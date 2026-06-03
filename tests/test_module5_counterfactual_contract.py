from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_module5_counterfactual_contract.py"

validator_module: Any | None = None


def _load_validator_module() -> Any:
    global validator_module
    if validator_module is None:
        spec = importlib.util.spec_from_file_location("module5_counterfactual_contract", SCRIPT_PATH)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load validator module from {SCRIPT_PATH}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        validator_module = module
    return validator_module


DEFAULT_INTERVENTIONS = (ROOT / "data" / "module5_counterfactual_interventions.csv")
DEFAULT_OUTCOME_SCHEMA = (ROOT / "data" / "module5_counterfactual_outcome_schema.csv")
DEFAULT_MODULE4_DECISION = (ROOT / "data" / "module4_5_family_decision_table.csv")


def _validate_contract(interventions_path: Path, outcome_schema_path: Path, module4_decision_path: Path) -> tuple[bool, list[str]]:
    module = _load_validator_module()
    return module.validate_module5_counterfactual_contract(
        interventions_path=interventions_path,
        outcome_schema_path=outcome_schema_path,
        module4_decision_path=module4_decision_path,
    )


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_validate_module5_counterfactual_contract_passes() -> None:
    module = _load_validator_module()
    ok, errors = module.validate_module5_counterfactual_contract(
        interventions_path=DEFAULT_INTERVENTIONS,
        outcome_schema_path=DEFAULT_OUTCOME_SCHEMA,
        module4_decision_path=DEFAULT_MODULE4_DECISION,
    )
    assert ok
    assert errors == []


def test_validate_module5_counterfactual_contract_detects_duplicate_intervention_id(tmp_path: Path) -> None:
    interventions = Path(tmp_path / "module5_counterfactual_interventions.csv")
    original_rows = list(csv.DictReader(DEFAULT_INTERVENTIONS.open(newline="", encoding="utf-8")))

    duplicate = original_rows[0].copy()
    duplicate["intervention_id"] = original_rows[1]["intervention_id"]
    modified = original_rows + [duplicate]
    _write_rows(interventions, modified)

    ok, errors = _validate_contract(
        interventions_path=interventions,
        outcome_schema_path=DEFAULT_OUTCOME_SCHEMA,
        module4_decision_path=DEFAULT_MODULE4_DECISION,
    )
    assert not ok
    assert any("Duplicate intervention_id" in error for error in errors)


def test_validate_module5_counterfactual_contract_detects_missing_axis(tmp_path: Path) -> None:
    interventions = Path(tmp_path / "module5_counterfactual_interventions.csv")
    rows = list(csv.DictReader(DEFAULT_INTERVENTIONS.open(newline="", encoding="utf-8")))
    rows = [row for row in rows if row["intervention_axis"] != "status_quo"]
    _write_rows(interventions, rows)

    ok, errors = _validate_contract(
        interventions_path=interventions,
        outcome_schema_path=DEFAULT_OUTCOME_SCHEMA,
        module4_decision_path=DEFAULT_MODULE4_DECISION,
    )
    assert not ok
    assert any("Missing required intervention axes" in error for error in errors)
