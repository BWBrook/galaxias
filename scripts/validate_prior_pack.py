from __future__ import annotations

import ast
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_float(value: str) -> float:
    return float(value)


def split_ids(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def load_evidence_ids() -> set[str]:
    return {row["evidence_id"] for row in read_csv(DATA_DIR / "evidence_ledger.csv")}


def extract_parameter_ids(expression: str) -> set[str]:
    return set(EXPRESSION_PARAMETER_RE.findall(expression))


def safe_eval_expression(expression: str, values: dict[str, float]) -> float:
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


def compare(left: float, operator: str, right: float) -> bool:
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


def validate_prior_rows(rows: list[dict[str, str]], evidence_ids: set[str]) -> dict[str, float]:
    if len(rows) != EXPECTED_PARAMETER_COUNT:
        raise ValueError(f"Expected {EXPECTED_PARAMETER_COUNT} parameter rows, found {len(rows)}")

    groups = {row["parameter_group"] for row in rows}
    if groups != REQUIRED_PARAMETER_GROUPS:
        missing = REQUIRED_PARAMETER_GROUPS - groups
        extra = groups - REQUIRED_PARAMETER_GROUPS
        raise ValueError(f"Parameter groups mismatch. Missing={missing}, extra={extra}")

    seen_ids: set[str] = set()
    defaults: dict[str, float] = {}
    for row in rows:
        parameter_id = row["parameter_id"]
        if parameter_id in seen_ids:
            raise ValueError(f"Duplicate parameter_id: {parameter_id}")
        seen_ids.add(parameter_id)

        if row["source_strategy"] not in ALLOWED_SOURCE_STRATEGIES:
            raise ValueError(f"Invalid source_strategy for {parameter_id}: {row['source_strategy']}")

        if row["sampling_transform"] not in ALLOWED_SAMPLING_TRANSFORMS:
            raise ValueError(f"Invalid sampling_transform for {parameter_id}: {row['sampling_transform']}")

        missing_evidence = [eid for eid in split_ids(row["evidence_ids"]) if eid not in evidence_ids]
        if missing_evidence:
            raise ValueError(f"Unknown evidence_ids for {parameter_id}: {missing_evidence}")
        if row["source_strategy"] == "direct_pedder" and not split_ids(row["evidence_ids"]):
            raise ValueError(f"{parameter_id} cannot be direct_pedder without evidence_ids")

        lower = parse_float(row["lower_bound"])
        upper = parse_float(row["upper_bound"])
        default = parse_float(row["default_value"])
        defaults[parameter_id] = default

        if not lower <= default <= upper:
            raise ValueError(f"Default outside bounds for {parameter_id}: {default} not in [{lower}, {upper}]")

        transform = row["sampling_transform"]
        family = row["distribution_family"]
        if transform == "log":
            if lower <= 0 or upper <= 0 or default <= 0:
                raise ValueError(f"log transform requires positive bounds/default for {parameter_id}")
        if transform == "logit":
            if lower < 0 or upper > 1 or default < 0 or default > 1:
                raise ValueError(f"logit transform requires [0, 1] bounded values for {parameter_id}")
            if family != "beta":
                raise ValueError(f"logit transform is only expected for beta priors in {parameter_id}")
        if family == "lognormal" and transform != "log":
            raise ValueError(f"lognormal prior should use log transform for {parameter_id}")
        if family == "gamma" and transform != "log":
            raise ValueError(f"gamma prior should use log transform for {parameter_id}")
        if family == "half_normal" and transform != "log":
            raise ValueError(f"half_normal prior should use log transform for {parameter_id}")
        if family == "discrete_uniform" and transform != "identity":
            raise ValueError(f"discrete_uniform prior should use identity transform for {parameter_id}")

    return defaults


def validate_family_map(
    rows: list[dict[str, str]],
    parameter_defaults: dict[str, float],
) -> dict[str, dict[str, float]]:
    expected_row_count = EXPECTED_PARAMETER_COUNT * len(EXPECTED_FAMILY_IDS)
    if len(rows) != expected_row_count:
        raise ValueError(f"Expected {expected_row_count} family-map rows, found {len(rows)}")

    expected_parameter_ids = set(parameter_defaults)
    family_ids = {row["family_id"] for row in rows}
    if family_ids != EXPECTED_FAMILY_IDS:
        raise ValueError(f"Family ids mismatch. Expected {EXPECTED_FAMILY_IDS}, found {family_ids}")

    family_value_maps: dict[str, dict[str, float]] = {}
    for family_id in EXPECTED_FAMILY_IDS:
        family_rows = [row for row in rows if row["family_id"] == family_id]
        if len(family_rows) != EXPECTED_PARAMETER_COUNT:
            raise ValueError(
                f"Family {family_id} should have {EXPECTED_PARAMETER_COUNT} rows, found {len(family_rows)}"
            )

        seen_ids: set[str] = set()
        effective_values: dict[str, float] = {}
        for row in family_rows:
            parameter_id = row["parameter_id"]
            if parameter_id in seen_ids:
                raise ValueError(f"Duplicate {parameter_id} in family {family_id}")
            seen_ids.add(parameter_id)

            status = row["parameter_status"]
            fixed_value = row["fixed_value"]
            if status not in ALLOWED_PARAMETER_STATUSES:
                raise ValueError(f"Invalid parameter_status for {family_id}/{parameter_id}: {status}")

            if status == "estimate":
                if fixed_value:
                    raise ValueError(f"Estimate row should not have fixed_value for {family_id}/{parameter_id}")
                effective_values[parameter_id] = parameter_defaults[parameter_id]
            elif status == "unused":
                if fixed_value:
                    raise ValueError(f"Unused row should not have fixed_value for {family_id}/{parameter_id}")
            elif status == "fixed_zero":
                if parse_float(fixed_value) != 0:
                    raise ValueError(f"fixed_zero row must have fixed_value 0 for {family_id}/{parameter_id}")
                effective_values[parameter_id] = 0.0
            elif status == "fixed_one":
                if parse_float(fixed_value) != 1:
                    raise ValueError(f"fixed_one row must have fixed_value 1 for {family_id}/{parameter_id}")
                effective_values[parameter_id] = 1.0
            elif status == "fixed_value":
                effective_values[parameter_id] = parse_float(fixed_value)

        if seen_ids != expected_parameter_ids:
            raise ValueError(f"Family {family_id} is missing or has extra parameter ids")
        family_value_maps[family_id] = effective_values

    return family_value_maps


def validate_constraints(
    rows: list[dict[str, str]],
    parameter_defaults: dict[str, float],
    family_value_maps: dict[str, dict[str, float]],
    family_map_rows: list[dict[str, str]],
) -> None:
    seen_ids: set[str] = set()
    family_lookup = {
        (row["family_id"], row["parameter_id"]): row for row in family_map_rows
    }

    for row in rows:
        constraint_id = row["constraint_id"]
        if constraint_id in seen_ids:
            raise ValueError(f"Duplicate constraint_id: {constraint_id}")
        seen_ids.add(constraint_id)

        applies_to = row["applies_to"]
        if applies_to != "all" and applies_to not in EXPECTED_FAMILY_IDS:
            raise ValueError(f"Invalid applies_to for {constraint_id}: {applies_to}")

        operator = row["operator"]
        if operator not in ALLOWED_OPERATORS:
            raise ValueError(f"Invalid operator for {constraint_id}: {operator}")

        referenced = extract_parameter_ids(row["lhs"]) | extract_parameter_ids(row["rhs"])
        unknown = referenced - set(parameter_defaults)
        if unknown:
            raise ValueError(f"Constraint {constraint_id} references unknown parameters: {sorted(unknown)}")

        if applies_to == "all":
            value_map = parameter_defaults
        else:
            value_map = family_value_maps[applies_to]

        lhs_value = safe_eval_expression(row["lhs"], value_map)
        try:
            rhs_value = safe_eval_expression(row["rhs"], value_map)
        except (ValueError, SyntaxError):
            rhs_value = parse_float(row["rhs"])

        if row["constraint_type"] != "family_definition" and not compare(lhs_value, operator, rhs_value):
            raise ValueError(f"Default values do not satisfy {constraint_id}")

        if row["constraint_type"] == "family_definition":
            if applies_to == "all":
                raise ValueError(f"Family-definition constraint must target a single family: {constraint_id}")
            lhs_ids = extract_parameter_ids(row["lhs"])
            if len(lhs_ids) != 1:
                raise ValueError(f"Family-definition lhs should reference one parameter: {constraint_id}")
            parameter_id = next(iter(lhs_ids))
            family_row = family_lookup[(applies_to, parameter_id)]
            expected_status = family_row["parameter_status"]
            rhs_numeric = parse_float(row["rhs"])
            if rhs_numeric == 0 and expected_status != "fixed_zero":
                raise ValueError(f"{constraint_id} expects fixed_zero but found {expected_status}")
            if rhs_numeric == 1 and expected_status != "fixed_one":
                raise ValueError(f"{constraint_id} expects fixed_one but found {expected_status}")


def main() -> None:
    evidence_ids = load_evidence_ids()
    prior_rows = read_csv(DATA_DIR / "parameter_priors.csv")
    family_map_rows = read_csv(DATA_DIR / "model_family_parameter_map.csv")
    constraint_rows = read_csv(DATA_DIR / "parameter_constraints.csv")

    parameter_defaults = validate_prior_rows(prior_rows, evidence_ids)
    family_value_maps = validate_family_map(family_map_rows, parameter_defaults)
    validate_constraints(constraint_rows, parameter_defaults, family_value_maps, family_map_rows)

    print(
        "Validated prior pack: "
        f"{len(prior_rows)} priors, "
        f"{len(family_map_rows)} family-map rows, "
        f"{len(constraint_rows)} constraints."
    )


if __name__ == "__main__":
    main()
