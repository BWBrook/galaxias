from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INTERVENTIONS = ROOT / "data" / "module5_counterfactual_interventions.csv"
DEFAULT_OUTCOME_SCHEMA = ROOT / "data" / "module5_counterfactual_outcome_schema.csv"
DEFAULT_MODULE4_DECISION = ROOT / "data" / "module4_5_family_decision_table.csv"


REQUIRED_INTERVENTION_COLUMNS = {
    "intervention_id",
    "family_id",
    "module5_role",
    "scenario_class",
    "baseline_source",
    "intervention_axis",
    "intervention_label",
    "held_constant",
    "modified_parameters",
    "expected_counterfactual_question",
    "primary_endpoint",
    "secondary_endpoints",
    "negative_reference_flag",
    "production_status",
    "notes",
}

REQUIRED_OUTCOME_SCHEMA_COLUMNS = {
    "column_name",
    "required",
    "dtype",
    "unit",
    "description",
    "source_or_derivation",
}

REQUIRED_MODULE5_ROLES = {"primary", "sensitivity", "negative_reference"}
REQUIRED_INTERVENTION_AXES = {
    "status_quo",
    "no_trout_pressure",
    "no_climbing_pressure",
    "no_trout_or_climbing_pressure",
}
ALLOWED_PRODUCTION_STATUS = {"implemented", "design_only", "not_applicable", "not yet implemented"}
ALLOWED_BOOLEAN_VALUES = {"true", "false", "1", "0", "yes", "no", "y", "n", "t", "f"}
ALLOWED_DTYPE_VALUES = {
    "string",
    "integer",
    "int",
    "float",
    "boolean",
    "bool",
    "path",
    "identifier",
    "index",
    "timestamp",
    "year",
    "count",
    "fraction",
}

REQUIRED_OUTCOME_FIELD_NAMES = {
    "family_id",
    "family_role",
    "proposal_id",
    "proposal_source_key",
    "module4_run_id",
    "variant_id",
    "seed",
    "run_dir_name",
    "proposal_seed",
    "stochastic_replicate_id",
    "intervention_id",
    "intervention_axis",
    "matched_pair_id",
    "extirpation_year_raw",
    "extirpation_year_contrast",
    "persistence_2002_baseline",
    "persistence_2002_counterfactual",
    "persistence_2002_contrast",
    "persistence_1996_baseline",
    "persistence_1996_counterfactual",
    "persistence_1996_contrast",
    "min_abundance_1992_2002_baseline",
    "min_abundance_1992_2002_counterfactual",
    "min_abundance_1992_2002_contrast",
    "lake_refuge_share_2002_baseline",
    "lake_refuge_share_2002_counterfactual",
    "lake_refuge_share_2002_contrast",
    "uncertainty_n_replicates",
    "uncertainty_extirpation_median",
    "uncertainty_extirpation_ci_low",
    "uncertainty_extirpation_ci_high",
    "uncertainty_persistence_2002_delta_median",
    "uncertainty_persistence_2002_ci_low",
    "uncertainty_persistence_2002_ci_high",
    "processing_timestamp",
    "provenance_source_file",
    "provenance_git_sha",
    "provenance_script",
    "provenance_module4_manifest",
}


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if reader.fieldnames is None:
            raise ValueError(f"CSV missing header: {path}")
        return rows, reader.fieldnames


def parse_boolish(value: str, context: str) -> str:
    normalised = (value or "").strip().lower()
    if normalised in ALLOWED_BOOLEAN_VALUES:
        return normalised
    raise ValueError(f"{context}: not boolean-like -> {value}")


def load_family_roles(path: Path) -> tuple[dict[str, str], list[str]]:
    rows, columns = read_csv_rows(path)
    if "family_id" not in columns or "module5_role" not in columns:
        missing = []
        if "family_id" not in columns:
            missing.append("family_id")
        if "module5_role" not in columns:
            missing.append("module5_role")
        raise ValueError(f"module4 decision table missing required columns {missing}: {path}")

    family_to_role: dict[str, str] = {}
    for row in rows:
        family_to_role[row["family_id"].strip()] = row["module5_role"].strip()
    return family_to_role, columns


def validate_interventions(
    interventions_path: Path,
    family_roles: dict[str, str],
) -> list[str]:
    rows, columns = read_csv_rows(interventions_path)
    errors: list[str] = []

    missing_columns = sorted(REQUIRED_INTERVENTION_COLUMNS - set(columns))
    if missing_columns:
        errors.append(f"Interventions file missing required columns: {missing_columns}")
        return errors

    if not rows:
        errors.append("Interventions file is empty.")
        return errors

    seen_ids: set[str] = set()
    seen_axes = set()
    for row in rows:
        intervention_id = row["intervention_id"].strip()
        family_id = row["family_id"].strip()
        role = row["module5_role"].strip()
        axis = row["intervention_axis"].strip()
        parse_boolish(row["negative_reference_flag"], f"{intervention_id}: negative_reference_flag")
        production_status = row["production_status"].strip().lower()

        if intervention_id in seen_ids:
            errors.append(f"Duplicate intervention_id: {intervention_id}")
        else:
            seen_ids.add(intervention_id)

        if family_id not in family_roles:
            errors.append(f"Unknown family_id in interventions: {family_id}")
        else:
            if role != family_roles[family_id]:
                errors.append(
                    f"module5_role mismatch for family_id={family_id}:"
                    f" interventions={role} family_decision={family_roles[family_id]}"
                )

        if role not in REQUIRED_MODULE5_ROLES:
            errors.append(f"intervention_id={intervention_id} has invalid module5_role={role}")

        if axis not in REQUIRED_INTERVENTION_AXES:
            errors.append(f"intervention_id={intervention_id} has unsupported intervention_axis={axis}")
        else:
            seen_axes.add(axis)

        if production_status not in ALLOWED_PRODUCTION_STATUS:
            errors.append(
                f"intervention_id={intervention_id} has invalid production_status={production_status}"
            )
        if axis and production_status == "implemented" and row["notes"].strip().lower().startswith("requires"):
            errors.append(
                f"intervention_id={intervention_id} production_status=implemented but notes indicate implementation is pending"
            )

        if not row["held_constant"].strip():
            errors.append(f"intervention_id={intervention_id} must specify held_constant")
        if not row["expected_counterfactual_question"].strip():
            errors.append(f"intervention_id={intervention_id} must specify expected_counterfactual_question")
        if not row["primary_endpoint"].strip():
            errors.append(f"intervention_id={intervention_id} must specify primary_endpoint")

        # parse_boolish above guarantees a valid boolean-like value.

    missing_axes = sorted(REQUIRED_INTERVENTION_AXES - seen_axes)
    if missing_axes:
        errors.append(f"Missing required intervention axes in interventions file: {missing_axes}")

    roles_count = Counter(row["module5_role"].strip() for row in rows if row.get("module5_role"))
    for required_role in REQUIRED_MODULE5_ROLES:
        if roles_count[required_role] == 0:
            errors.append(f"No interventions found for required module5_role={required_role}")

    return errors


def validate_schema(schema_path: Path) -> list[str]:
    rows, columns = read_csv_rows(schema_path)
    errors: list[str] = []

    missing_columns = sorted(REQUIRED_OUTCOME_SCHEMA_COLUMNS - set(columns))
    if missing_columns:
        errors.append(f"Outcome-schema file missing required columns: {missing_columns}")
        return errors

    if not rows:
        errors.append("Outcome-schema file is empty.")
        return errors

    seen: set[str] = set()
    row_names: dict[str, dict[str, str]] = {}

    for row in rows:
        column_name = row["column_name"].strip()
        if column_name in seen:
            errors.append(f"Duplicate outcome schema column_name: {column_name}")
        seen.add(column_name)
        row_names[column_name] = row

        if not row["description"].strip():
            errors.append(f"Schema row missing description for column_name={column_name}")

        if not row["unit"].strip():
            errors.append(f"Schema row missing unit for column_name={column_name}")

        parse_boolish(row["required"], f"column_name={column_name}: required")

        dtype = row["dtype"].strip().lower()
        if dtype not in ALLOWED_DTYPE_VALUES:
            errors.append(f"Unexpected dtype '{dtype}' for column_name={column_name}")

        if not row["source_or_derivation"].strip():
            errors.append(f"Schema row missing source_or_derivation for column_name={column_name}")

    missing_fields = sorted(REQUIRED_OUTCOME_FIELD_NAMES - set(row_names))
    if missing_fields:
        errors.append(f"Outcome-schema file missing required column_name entries: {missing_fields}")

    return errors


def validate_module5_counterfactual_contract(
    interventions_path: Path,
    outcome_schema_path: Path,
    module4_decision_path: Path,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    for path in [interventions_path, outcome_schema_path, module4_decision_path]:
        if not path.exists():
            errors.append(f"Missing required file: {path}")

    if errors:
        return False, errors

    family_roles, _ = load_family_roles(module4_decision_path)
    errors.extend(validate_interventions(interventions_path, family_roles))
    errors.extend(validate_schema(outcome_schema_path))
    return len(errors) == 0, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Module 5 counterfactual design contracts.")
    parser.add_argument("--interventions", default=str(DEFAULT_INTERVENTIONS))
    parser.add_argument("--outcome-schema", default=str(DEFAULT_OUTCOME_SCHEMA))
    parser.add_argument("--module4-decision", default=str(DEFAULT_MODULE4_DECISION))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ok, errors = validate_module5_counterfactual_contract(
        interventions_path=Path(args.interventions),
        outcome_schema_path=Path(args.outcome_schema),
        module4_decision_path=Path(args.module4_decision),
    )

    if not ok:
        print("Module 5 counterfactual contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Module 5 counterfactual contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
