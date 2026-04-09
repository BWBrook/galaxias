from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pandas as pd

from galaxias_model.types import ModelInputs, ResolvedParameters


EXPECTED_PARAMETER_COUNT = 40
EXPECTED_FAMILY_IDS = {
    "habitat_only_null",
    "trout_only",
    "climbing_only",
    "persistent_joint_cause",
    "transient_perfect_storm",
}
REQUIRED_PARAMETER_GROUPS = {
    "Pedder life history",
    "Pedder lake-refuge movement / spawning allocation",
    "Pedder density dependence or carrying terms",
    "trout abundance trajectory",
    "trout piscivory modifier",
    "climbing-galaxias expansion",
    "trophic-upsurge amplitude and decay",
    "refuge habitat quality",
    "habitat transition timing",
    "observation / calibration nuisance terms",
}
ALLOWED_PARAMETER_STATUSES = {
    "estimate",
    "fixed_zero",
    "fixed_one",
    "fixed_value",
    "unused",
}
ALLOWED_SOURCE_STRATEGIES = {
    "direct_pedder",
    "insurance_population_proxy",
    "tasmanian_proxy",
    "comparative_proxy",
    "structural_assumption",
}
ALLOWED_SAMPLING_TRANSFORMS = {"identity", "log", "logit"}
ALLOWED_OPERATORS = {"==", ">=", "<=", ">", "<"}
EXPRESSION_PARAMETER_RE = re.compile(r"PR\d{3}")


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _read_json(path: Path) -> dict[str, dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected top-level object in {path}")
    return payload


def _split_ids(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def _parse_float(value: str) -> float:
    return float(value)


def _extract_parameter_ids(expression: str) -> set[str]:
    return set(EXPRESSION_PARAMETER_RE.findall(expression))


def _safe_eval_expression(expression: str, values: dict[str, float]) -> float:
    node = ast.parse(expression, mode="eval")

    def evaluate(current: ast.AST) -> float:
        if isinstance(current, ast.Expression):
            return evaluate(current.body)
        if isinstance(current, ast.Name):
            if current.id not in values:
                raise ValueError(f"Unknown parameter in expression: {current.id}")
            return values[current.id]
        if isinstance(current, ast.Constant) and isinstance(current.value, (int, float)):
            return float(current.value)
        if isinstance(current, ast.BinOp):
            left = evaluate(current.left)
            right = evaluate(current.right)
            if isinstance(current.op, ast.Add):
                return left + right
            if isinstance(current.op, ast.Sub):
                return left - right
            if isinstance(current.op, ast.Mult):
                return left * right
            if isinstance(current.op, ast.Div):
                return left / right
            raise ValueError(f"Unsupported operator in expression: {ast.dump(current.op)}")
        if isinstance(current, ast.UnaryOp) and isinstance(current.op, ast.USub):
            return -evaluate(current.operand)
        raise ValueError(f"Unsupported expression: {ast.dump(current)}")

    return evaluate(node)


def _compare(left: float, operator: str, right: float) -> bool:
    if operator == "==":
        return abs(left - right) < 1e-9
    if operator == ">=":
        return left >= right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    if operator == "<":
        return left < right
    raise ValueError(f"Unsupported operator: {operator}")


def _load_evidence_ids(data_dir: Path) -> set[str]:
    evidence = _read_csv(data_dir / "evidence_ledger.csv")
    return set(evidence["evidence_id"])


def _validate_prior_rows(rows: pd.DataFrame, evidence_ids: set[str]) -> None:
    if len(rows) != EXPECTED_PARAMETER_COUNT:
        raise ValueError(f"Expected {EXPECTED_PARAMETER_COUNT} parameter rows, found {len(rows)}")

    if rows["parameter_id"].nunique() != EXPECTED_PARAMETER_COUNT:
        raise ValueError("Parameter table contains duplicate parameter_id values")

    groups = set(rows["parameter_group"])
    if groups != REQUIRED_PARAMETER_GROUPS:
        missing = REQUIRED_PARAMETER_GROUPS - groups
        extra = groups - REQUIRED_PARAMETER_GROUPS
        raise ValueError(f"Parameter groups mismatch. Missing={missing}, extra={extra}")

    for row in rows.to_dict(orient="records"):
        parameter_id = row["parameter_id"]
        strategy = row["source_strategy"]
        transform = row["sampling_transform"]
        family = row["distribution_family"]
        lower = _parse_float(row["lower_bound"])
        upper = _parse_float(row["upper_bound"])
        default = _parse_float(row["default_value"])

        if strategy not in ALLOWED_SOURCE_STRATEGIES:
            raise ValueError(f"Invalid source_strategy for {parameter_id}: {strategy}")
        if transform not in ALLOWED_SAMPLING_TRANSFORMS:
            raise ValueError(f"Invalid sampling_transform for {parameter_id}: {transform}")
        if not lower <= default <= upper:
            raise ValueError(f"Default outside bounds for {parameter_id}: {default}")

        missing_evidence = [eid for eid in _split_ids(row["evidence_ids"]) if eid not in evidence_ids]
        if missing_evidence:
            raise ValueError(f"Unknown evidence_ids for {parameter_id}: {missing_evidence}")

        if transform == "log" and (lower <= 0 or upper <= 0 or default <= 0):
            raise ValueError(f"log transform requires positive bounds/default for {parameter_id}")
        if transform == "logit":
            if lower < 0 or upper > 1 or default < 0 or default > 1:
                raise ValueError(f"logit transform requires [0, 1] bounds for {parameter_id}")
            if family != "beta":
                raise ValueError(f"logit transform is only valid for beta priors in {parameter_id}")
        if family == "lognormal" and transform != "log":
            raise ValueError(f"lognormal prior should use log transform for {parameter_id}")
        if family == "gamma" and transform != "log":
            raise ValueError(f"gamma prior should use log transform for {parameter_id}")
        if family == "half_normal" and transform != "log":
            raise ValueError(f"half_normal prior should use log transform for {parameter_id}")
        if family == "discrete_uniform" and transform != "identity":
            raise ValueError(f"discrete_uniform prior should use identity transform for {parameter_id}")


def _validate_family_rows(rows: pd.DataFrame, parameter_ids: set[str]) -> None:
    expected_row_count = EXPECTED_PARAMETER_COUNT * len(EXPECTED_FAMILY_IDS)
    if len(rows) != expected_row_count:
        raise ValueError(f"Expected {expected_row_count} family-map rows, found {len(rows)}")

    family_ids = set(rows["family_id"])
    if family_ids != EXPECTED_FAMILY_IDS:
        raise ValueError(f"Family ids mismatch. Expected {EXPECTED_FAMILY_IDS}, found {family_ids}")

    for family_id in EXPECTED_FAMILY_IDS:
        subset = rows.loc[rows["family_id"] == family_id]
        if len(subset) != EXPECTED_PARAMETER_COUNT:
            raise ValueError(f"Family {family_id} has {len(subset)} rows, expected {EXPECTED_PARAMETER_COUNT}")
        if set(subset["parameter_id"]) != parameter_ids:
            raise ValueError(f"Family {family_id} does not cover the expected parameter ids")
        if not set(subset["parameter_status"]).issubset(ALLOWED_PARAMETER_STATUSES):
            raise ValueError(f"Family {family_id} contains invalid parameter_status values")


def _validate_constraint_rows(rows: pd.DataFrame, parameter_ids: set[str]) -> None:
    if rows["constraint_id"].nunique() != len(rows):
        raise ValueError("Constraint table contains duplicate constraint_id values")

    for row in rows.to_dict(orient="records"):
        operator = row["operator"]
        applies_to = row["applies_to"]
        referenced = _extract_parameter_ids(row["lhs"]) | _extract_parameter_ids(row["rhs"])
        if operator not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator for {row['constraint_id']}: {operator}")
        if applies_to != "all" and applies_to not in EXPECTED_FAMILY_IDS:
            raise ValueError(f"Invalid applies_to for {row['constraint_id']}: {applies_to}")
        unknown = referenced - parameter_ids
        if unknown:
            raise ValueError(f"Constraint {row['constraint_id']} references unknown parameters: {sorted(unknown)}")


def _validate_target_details(
    calibration_targets: pd.DataFrame | None,
    target_details: dict[str, dict[str, object]] | None,
) -> None:
    if calibration_targets is None:
        if target_details:
            raise ValueError("Target details were provided without calibration_targets.csv")
        return
    if target_details is None:
        raise ValueError("Missing calibration_target_details.json for Module 2 scoring")

    target_ids = set(calibration_targets["target_id"])
    detail_ids = set(target_details)
    if target_ids != detail_ids:
        missing = target_ids - detail_ids
        extra = detail_ids - target_ids
        raise ValueError(f"Target details mismatch. Missing={sorted(missing)}, extra={sorted(extra)}")

    required_keys = {"required_scenario_id", "observed_primary", "observed_secondary"}
    for target_id, details in target_details.items():
        missing_keys = required_keys - set(details)
        if missing_keys:
            raise ValueError(f"Target {target_id} is missing required detail keys: {sorted(missing_keys)}")


def load_model_inputs(data_dir: str | Path) -> ModelInputs:
    data_path = Path(data_dir).resolve()
    evidence_ids = _load_evidence_ids(data_path)
    priors = _read_csv(data_path / "parameter_priors.csv")
    family_map = _read_csv(data_path / "model_family_parameter_map.csv")
    constraints = _read_csv(data_path / "parameter_constraints.csv")
    calibration_targets_path = data_path / "calibration_targets.csv"
    calibration_targets = _read_csv(calibration_targets_path) if calibration_targets_path.exists() else None
    target_details_path = data_path / "calibration_target_details.json"
    target_details = _read_json(target_details_path) if target_details_path.exists() else None

    _validate_prior_rows(priors, evidence_ids)
    _validate_family_rows(family_map, set(priors["parameter_id"]))
    _validate_constraint_rows(constraints, set(priors["parameter_id"]))
    _validate_target_details(calibration_targets, target_details)

    return ModelInputs(
        data_dir=data_path,
        parameter_priors=priors,
        family_map=family_map,
        constraints=constraints,
        calibration_targets=calibration_targets,
        calibration_target_details=target_details,
    )


def _apply_family_status(default_value: float, status: str, fixed_value: str) -> float:
    if status == "fixed_zero":
        return 0.0
    if status == "fixed_one":
        return 1.0
    if status == "fixed_value":
        return _parse_float(fixed_value)
    return default_value


def _validate_resolved_constraints(
    constraints: pd.DataFrame,
    values: dict[str, float],
    family_id: str,
    statuses: dict[str, str],
) -> None:
    for row in constraints.to_dict(orient="records"):
        applies_to = row["applies_to"]
        if applies_to not in {"all", family_id}:
            continue

        lhs_value = _safe_eval_expression(row["lhs"], values)
        try:
            rhs_value = _safe_eval_expression(row["rhs"], values)
        except (ValueError, SyntaxError):
            rhs_value = _parse_float(row["rhs"])

        if not _compare(lhs_value, row["operator"], rhs_value):
            raise ValueError(
                f"Resolved parameter set for {family_id} violates {row['constraint_id']}: "
                f"{row['lhs']} {row['operator']} {row['rhs']}"
            )

        if row["constraint_type"] == "family_definition":
            lhs_ids = _extract_parameter_ids(row["lhs"])
            if len(lhs_ids) == 1:
                parameter_id = next(iter(lhs_ids))
                if rhs_value == 0 and statuses[parameter_id] != "fixed_zero":
                    raise ValueError(f"{row['constraint_id']} expects {parameter_id} to be fixed_zero")
                if rhs_value == 1 and statuses[parameter_id] != "fixed_one":
                    raise ValueError(f"{row['constraint_id']} expects {parameter_id} to be fixed_one")


def resolve_family_parameters(
    model_inputs: ModelInputs,
    family_id: str,
    source: str = "default",
) -> ResolvedParameters:
    if source != "default":
        raise ValueError("Module 1 only supports source='default'")
    if family_id not in EXPECTED_FAMILY_IDS:
        raise ValueError(f"Unknown family_id: {family_id}")

    family_rows = model_inputs.family_map.loc[model_inputs.family_map["family_id"] == family_id].copy()
    priors = model_inputs.parameter_priors.copy()
    merged = priors.merge(
        family_rows[["family_id", "family_label", "parameter_id", "parameter_status", "fixed_value", "notes"]],
        on="parameter_id",
        how="inner",
        suffixes=("", "_family"),
    )
    if len(merged) != EXPECTED_PARAMETER_COUNT:
        raise ValueError(f"Failed to resolve all parameters for family {family_id}")

    values: dict[str, float] = {}
    statuses: dict[str, str] = {}
    manifest_records: list[dict[str, object]] = []
    family_label = str(merged["family_label"].iloc[0])

    for row in merged.to_dict(orient="records"):
        parameter_id = row["parameter_id"]
        status = row["parameter_status"]
        default_value = _parse_float(row["default_value"])
        effective_value = _apply_family_status(default_value, status, row["fixed_value"])

        values[parameter_id] = effective_value
        statuses[parameter_id] = status

        manifest_records.append(
            {
                "parameter_id": parameter_id,
                "parameter_name": row["parameter_name"],
                "parameter_group": row["parameter_group"],
                "status": status,
                "active": status != "unused",
                "default_value": default_value,
                "effective_value": effective_value,
                "fixed_value": row["fixed_value"],
                "distribution_family": row["distribution_family"],
                "sampling_transform": row["sampling_transform"],
                "source_strategy": row["source_strategy"],
                "notes": row["notes"],
                "family_notes": row["notes_family"],
            }
        )

    _validate_resolved_constraints(model_inputs.constraints, values, family_id, statuses)

    manifest = pd.DataFrame(manifest_records).sort_values("parameter_id").reset_index(drop=True)
    return ResolvedParameters(
        family_id=family_id,
        family_label=family_label,
        manifest=manifest,
        values=values,
        statuses=statuses,
    )
