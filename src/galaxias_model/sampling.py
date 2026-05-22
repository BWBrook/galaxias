from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from galaxias_model.io import (
    _apply_family_status,
    _parse_float,
    _resolve_family_parameter_rows,
    _validate_resolved_constraints,
)
from galaxias_model.types import ModelInputs, ResolvedParameters


EPS = 1e-9
MAX_PARAMETER_ATTEMPTS = 1000
MAX_PROPOSAL_ATTEMPTS = 1000


def transform_parameter_value(value: float, sampling_transform: str) -> float:
    value = float(value)
    if sampling_transform == "identity":
        return value
    if sampling_transform == "log":
        if value <= 0:
            raise ValueError("log transform requires a positive value")
        return math.log(value)
    if sampling_transform == "logit":
        if not 0 < value < 1:
            raise ValueError("logit transform requires a value in (0, 1)")
        return math.log(value / (1.0 - value))
    raise ValueError(f"Unsupported sampling_transform: {sampling_transform}")


def inverse_transform_parameter_value(value: float, sampling_transform: str) -> float:
    value = float(value)
    if sampling_transform == "identity":
        return value
    if sampling_transform == "log":
        return math.exp(value)
    if sampling_transform == "logit":
        return 1.0 / (1.0 + math.exp(-value))
    raise ValueError(f"Unsupported sampling_transform: {sampling_transform}")


def _safe_transform_or_nan(value: float, sampling_transform: str) -> float:
    try:
        return transform_parameter_value(value, sampling_transform)
    except ValueError:
        return float("nan")


def _sample_estimated_parameter(row: dict[str, Any], rng: np.random.Generator) -> tuple[float, float]:
    family = str(row["distribution_family"])
    lower = _parse_float(row["lower_bound"])
    upper = _parse_float(row["upper_bound"])
    param_1 = _parse_float(row["param_1"])
    param_2 = _parse_float(row["param_2"])
    transform = str(row["sampling_transform"])

    for _ in range(MAX_PARAMETER_ATTEMPTS):
        if family == "uniform":
            natural_value = float(rng.uniform(lower, upper))
        elif family == "discrete_uniform":
            natural_value = float(rng.integers(int(lower), int(upper) + 1))
        elif family == "beta":
            draw = float(rng.beta(param_1, param_2))
            natural_value = lower + draw * (upper - lower)
        elif family == "normal":
            natural_value = float(rng.normal(param_1, param_2))
        elif family == "lognormal":
            natural_value = float(rng.lognormal(param_1, param_2))
        elif family == "gamma":
            natural_value = float(rng.gamma(param_1, param_2))
        elif family == "half_normal":
            natural_value = abs(float(rng.normal(0.0, param_2)))
        else:
            raise ValueError(f"Unsupported distribution_family: {family}")

        if lower <= natural_value <= upper:
            return natural_value, transform_parameter_value(natural_value, transform)

    raise RuntimeError(
        f"Sampling failed after {MAX_PARAMETER_ATTEMPTS} attempts for {row['parameter_id']} "
        f"using {family} within bounds [{lower}, {upper}]"
    )


def _draw_proposal_rows_once(
    merged_rows: list[dict[str, Any]],
    family_id: str,
    family_label: str,
    proposal_index: int,
    rng: np.random.Generator,
) -> tuple[list[dict[str, Any]], dict[str, float], dict[str, str], str]:
    output_rows: list[dict[str, Any]] = []
    values: dict[str, float] = {}
    statuses: dict[str, str] = {}
    failure_reason = ""

    for row in merged_rows:
        parameter_id = str(row["parameter_id"])
        status = str(row["parameter_status"])
        default_value = _parse_float(row["default_value"])
        sampled_flag = status == "estimate"

        if sampled_flag and not failure_reason:
            try:
                value_natural, value_sampling = _sample_estimated_parameter(row, rng)
            except RuntimeError as exc:
                failure_reason = str(exc)
                value_natural = float("nan")
                value_sampling = float("nan")
        elif sampled_flag:
            value_natural = float("nan")
            value_sampling = float("nan")
        else:
            value_natural = _apply_family_status(default_value, status, row["fixed_value"])
            value_sampling = float("nan")

        values[parameter_id] = value_natural
        statuses[parameter_id] = status
        output_rows.append(
            {
                "proposal_index": proposal_index,
                "family_id": family_id,
                "family_label": family_label,
                "parameter_id": parameter_id,
                "parameter_status": status,
                "value_natural": value_natural,
                "value_sampling": value_sampling,
                "sampled_flag": bool(sampled_flag),
                "proposal_sampling_failed": False,
                "failure_reason": "",
                "distribution_family": str(row["distribution_family"]),
                "sampling_transform": str(row["sampling_transform"]),
            }
        )

    return output_rows, values, statuses, failure_reason


def sample_family_parameter_table(
    model_inputs: ModelInputs,
    family_id: str,
    rng: np.random.Generator,
    n_samples: int,
) -> pd.DataFrame:
    merged = _resolve_family_parameter_rows(model_inputs, family_id)
    merged_rows = merged.to_dict(orient="records")
    family_label = str(merged["family_label"].iloc[0])
    rows: list[dict[str, Any]] = []

    for proposal_index in range(1, n_samples + 1):
        last_rows: list[dict[str, Any]] = []
        last_failure_reason = ""
        for _ in range(MAX_PROPOSAL_ATTEMPTS):
            proposal_rows, values, statuses, failure_reason = _draw_proposal_rows_once(
                merged_rows,
                family_id,
                family_label,
                proposal_index,
                rng,
            )
            last_rows = proposal_rows
            last_failure_reason = failure_reason
            if failure_reason:
                continue
            try:
                _validate_resolved_constraints(model_inputs.constraints, values, family_id, statuses)
            except ValueError as exc:
                last_failure_reason = str(exc)
                continue

            rows.extend(proposal_rows)
            break
        else:
            if not last_failure_reason:
                last_failure_reason = (
                    f"Proposal sampling failed after {MAX_PROPOSAL_ATTEMPTS} attempts "
                    f"for {family_id}"
                )
            for output_row in last_rows:
                output_row["proposal_sampling_failed"] = True
                output_row["failure_reason"] = last_failure_reason
            rows.extend(last_rows)

    return pd.DataFrame(rows)


def _sample_lookup_from_input(sampled_values: Mapping[str, float] | pd.DataFrame | pd.Series) -> dict[str, float]:
    if isinstance(sampled_values, pd.DataFrame):
        if "parameter_id" not in sampled_values.columns or "value_natural" not in sampled_values.columns:
            raise ValueError("Sample DataFrame must contain parameter_id and value_natural columns")
        return {
            str(row["parameter_id"]): float(row["value_natural"])
            for row in sampled_values.to_dict(orient="records")
            if pd.notna(row["value_natural"])
        }
    if isinstance(sampled_values, pd.Series):
        if "parameter_id" in sampled_values.index and "value_natural" in sampled_values.index:
            return {str(sampled_values["parameter_id"]): float(sampled_values["value_natural"])}
        return {str(key): float(value) for key, value in sampled_values.to_dict().items()}
    return {str(key): float(value) for key, value in sampled_values.items()}


def build_resolved_parameters_from_sample(
    model_inputs: ModelInputs,
    family_id: str,
    sampled_values: Mapping[str, float] | pd.DataFrame | pd.Series,
) -> ResolvedParameters:
    merged = _resolve_family_parameter_rows(model_inputs, family_id)
    family_label = str(merged["family_label"].iloc[0])
    sample_lookup = _sample_lookup_from_input(sampled_values)

    values: dict[str, float] = {}
    statuses: dict[str, str] = {}
    manifest_records: list[dict[str, Any]] = []

    for row in merged.to_dict(orient="records"):
        parameter_id = str(row["parameter_id"])
        status = str(row["parameter_status"])
        default_value = _parse_float(row["default_value"])
        if status == "estimate":
            if parameter_id not in sample_lookup or not math.isfinite(sample_lookup[parameter_id]):
                raise ValueError(f"Missing sampled value for estimated parameter {parameter_id}")
            effective_value = float(sample_lookup[parameter_id])
        else:
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
                "sampled_flag": status == "estimate",
                "effective_value_sampling": (
                    transform_parameter_value(effective_value, str(row["sampling_transform"]))
                    if status == "estimate"
                    else _safe_transform_or_nan(effective_value, str(row["sampling_transform"]))
                ),
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
