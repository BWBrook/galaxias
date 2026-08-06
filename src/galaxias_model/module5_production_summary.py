from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from galaxias_model.module5_rehearsal import PARTITION_DEFINITIONS


DEFAULT_CONTRAST_ENDPOINTS: tuple[str, ...] = (
    "extirpation_year_contrast",
    "persistence_2002_contrast",
    "persistence_1996_contrast",
    "min_abundance_1992_2002_contrast",
    "lake_refuge_share_2002_contrast",
)

DEFAULT_PARTITION_ROW_COUNTS: dict[str, int] = {
    "headline/persistent_joint_cause": 106000,
    "headline/climbing_only": 47000,
    "headline/transient_perfect_storm": 100000,
    "diagnostic_sidecar/climbing_only_no_trout_pressure": 23500,
    "negative_reference/habitat_only_null": 1500,
    "negative_reference/trout_only": 1500,
}


@dataclass(frozen=True)
class ProductionSummaryExpectations:
    row_count: int = 279500
    column_count: int = 50
    expected_replicates: int = 100
    source_intervention_units: int = 2795
    distinct_proposal_source_keys: int = 780
    partition_row_counts: dict[str, int] | None = None

    @property
    def expected_partition_row_counts(self) -> dict[str, int]:
        return self.partition_row_counts or DEFAULT_PARTITION_ROW_COUNTS


@dataclass(frozen=True)
class ProductionSummaryResult:
    output_dir: Path
    metadata_path: Path
    qc_summary_path: Path
    partition_endpoint_summary_path: Path
    source_intervention_endpoint_summary_path: Path
    direction_summary_path: Path
    qc_checks: tuple[dict[str, object], ...]

    @property
    def all_qc_passed(self) -> bool:
        return all(bool(check["passed"]) for check in self.qc_checks)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _partition_mapping() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for definition in PARTITION_DEFINITIONS:
        for intervention_id in definition.intervention_ids:
            mapping[intervention_id] = definition.label
    return mapping


def _with_partition_labels(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    mapping = _partition_mapping()
    inferred = output["intervention_id"].astype(str).map(mapping).fillna("unknown")
    if "partition_label" not in output.columns:
        output["partition_label"] = inferred
    else:
        labels = output["partition_label"].astype(str)
        output["partition_label"] = labels.where(labels.str.strip() != "", inferred)
    return output


def _json_value(value: object) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _check(
    name: str,
    observed: object,
    expected: object,
    passed: bool,
    details: str = "",
) -> dict[str, object]:
    return {
        "check_name": name,
        "observed_value": _json_value(observed),
        "expected_value": _json_value(expected),
        "passed": bool(passed),
        "details": details,
    }


def _required_columns(endpoints: Iterable[str]) -> tuple[str, ...]:
    return (
        "proposal_source_key",
        "module4_run_id",
        "variant_id",
        "seed",
        "run_dir_name",
        "family_id",
        "family_role",
        "proposal_id",
        "stochastic_replicate_id",
        "intervention_id",
        "intervention_axis",
        "scenario_class",
        "baseline_stochastic_seed",
        "intervention_stochastic_seed",
        *tuple(endpoints),
    )


def _replicate_coverage_details(
    frame: pd.DataFrame,
    *,
    expected_replicates: int,
) -> tuple[bool, int, list[str]]:
    expected_ids = set(range(expected_replicates))
    failures: list[str] = []
    unit_count = 0
    for (source_key, intervention_id), group in frame.groupby(
        ["proposal_source_key", "intervention_id"],
        sort=False,
    ):
        unit_count += 1
        replicates = pd.to_numeric(group["stochastic_replicate_id"], errors="coerce")
        valid = replicates.dropna().astype(int)
        replicate_ids = set(valid.tolist())
        duplicate_ids = sorted(
            int(index)
            for index, value in valid.value_counts().items()
            if int(value) != 1
        )
        if (
            len(group) != expected_replicates
            or replicate_ids != expected_ids
            or duplicate_ids
        ):
            failures.append(
                f"{source_key}|{intervention_id}: rows={len(group)} "
                f"replicate_ids={sorted(replicate_ids)} duplicate_ids={duplicate_ids}"
            )
            if len(failures) >= 5:
                break
    return not failures, unit_count, failures


def build_qc_checks(
    frame: pd.DataFrame,
    *,
    matched_outcomes_path: Path,
    source_artifact: Path,
    expected_sha256: str,
    actual_sha256: str,
    expectations: ProductionSummaryExpectations,
    endpoints: tuple[str, ...] = DEFAULT_CONTRAST_ENDPOINTS,
    raw_column_count: int | None = None,
) -> tuple[dict[str, object], ...]:
    checks: list[dict[str, object]] = []
    source_artifact_resolved = source_artifact.resolve()
    matched_resolved = matched_outcomes_path.resolve()
    try:
        under_source_artifact = matched_resolved.is_relative_to(source_artifact_resolved)
    except ValueError:
        under_source_artifact = False

    checks.append(
        _check(
            "raw_file_exists",
            matched_outcomes_path.exists(),
            True,
            matched_outcomes_path.exists(),
            matched_outcomes_path.as_posix(),
        )
    )
    checks.append(
        _check(
            "raw_path_under_source_artifact",
            matched_resolved.as_posix(),
            source_artifact_resolved.as_posix(),
            under_source_artifact,
            "Raw matched outcomes must be read from the authorized remote artifact tree.",
        )
    )
    checks.append(
        _check(
            "raw_sha256",
            actual_sha256,
            expected_sha256,
            actual_sha256 == expected_sha256,
        )
    )

    missing_columns = [
        column for column in _required_columns(endpoints) if column not in frame.columns
    ]
    checks.append(
        _check(
            "required_columns",
            missing_columns,
            [],
            not missing_columns,
        )
    )
    checks.append(
        _check(
            "row_count",
            len(frame),
            expectations.row_count,
            len(frame) == expectations.row_count,
        )
    )
    checks.append(
        _check(
            "column_count",
            raw_column_count if raw_column_count is not None else len(frame.columns),
            expectations.column_count,
            (raw_column_count if raw_column_count is not None else len(frame.columns))
            == expectations.column_count,
        )
    )

    replicate_values = pd.to_numeric(frame["stochastic_replicate_id"], errors="coerce")
    replicate_ids = sorted(set(replicate_values.dropna().astype(int).tolist()))
    expected_replicate_ids = list(range(expectations.expected_replicates))
    checks.append(
        _check(
            "replicate_ids",
            replicate_ids,
            expected_replicate_ids,
            replicate_ids == expected_replicate_ids,
        )
    )

    unit_count = frame.groupby(["proposal_source_key", "intervention_id"]).ngroups
    checks.append(
        _check(
            "source_intervention_units",
            unit_count,
            expectations.source_intervention_units,
            unit_count == expectations.source_intervention_units,
        )
    )
    source_key_count = int(frame["proposal_source_key"].nunique())
    checks.append(
        _check(
            "distinct_proposal_source_keys",
            source_key_count,
            expectations.distinct_proposal_source_keys,
            source_key_count == expectations.distinct_proposal_source_keys,
        )
    )

    seed_mismatches = int(
        (
            frame["baseline_stochastic_seed"].astype(str)
            != frame["intervention_stochastic_seed"].astype(str)
        ).sum()
    )
    checks.append(_check("seed_mismatches", seed_mismatches, 0, seed_mismatches == 0))

    expected_partitions = expectations.expected_partition_row_counts
    actual_partitions = {
        str(key): int(value)
        for key, value in frame["partition_label"].value_counts().sort_index().items()
    }
    checks.append(
        _check(
            "partition_counts",
            actual_partitions,
            expected_partitions,
            actual_partitions == expected_partitions,
        )
    )

    coverage_passed, coverage_units, coverage_failures = _replicate_coverage_details(
        frame,
        expected_replicates=expectations.expected_replicates,
    )
    checks.append(
        _check(
            "replicate_coverage",
            {
                "units": coverage_units,
                "failures": coverage_failures,
            },
            {
                "units": expectations.source_intervention_units,
                "replicates": expectations.expected_replicates,
            },
            coverage_passed and coverage_units == expectations.source_intervention_units,
            "; ".join(coverage_failures),
        )
    )
    return tuple(checks)


def _quantile(values: pd.Series, q: float) -> float:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    return float(numeric.quantile(q)) if not numeric.empty else float("nan")


def _summary_stats(values: pd.Series) -> dict[str, float]:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    return {
        "mean": float(numeric.mean()) if not numeric.empty else float("nan"),
        "median": _quantile(numeric, 0.5),
        "q025": _quantile(numeric, 0.025),
        "q25": _quantile(numeric, 0.25),
        "q75": _quantile(numeric, 0.75),
        "q975": _quantile(numeric, 0.975),
        "min": float(numeric.min()) if not numeric.empty else float("nan"),
        "max": float(numeric.max()) if not numeric.empty else float("nan"),
    }


def _endpoint_long(frame: pd.DataFrame, endpoints: tuple[str, ...]) -> pd.DataFrame:
    id_columns = [
        "partition_label",
        "family_id",
        "family_role",
        "proposal_source_key",
        "module4_run_id",
        "variant_id",
        "seed",
        "run_dir_name",
        "proposal_id",
        "intervention_id",
        "intervention_axis",
        "scenario_class",
        "stochastic_replicate_id",
    ]
    long = frame.melt(
        id_vars=id_columns,
        value_vars=list(endpoints),
        var_name="endpoint",
        value_name="contrast_value",
    )
    long["contrast_value"] = pd.to_numeric(long["contrast_value"], errors="coerce")
    return long.dropna(subset=["contrast_value"])


def _build_partition_summary(long: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        "partition_label",
        "family_id",
        "family_role",
        "intervention_id",
        "intervention_axis",
        "scenario_class",
        "endpoint",
    ]
    rows: list[dict[str, object]] = []
    for keys, group in long.groupby(group_columns, sort=True):
        row = dict(zip(group_columns, keys, strict=True))
        values = group["contrast_value"]
        row.update(
            {
                "partition": row.pop("partition_label"),
                "row_count": int(values.count()),
                "source_count": int(group["proposal_source_key"].nunique()),
                "unit_count": int(
                    group.groupby(["proposal_source_key", "intervention_id"]).ngroups
                ),
            }
        )
        row.update(_summary_stats(values))
        rows.append(row)
    columns = [
        "partition",
        "family_id",
        "family_role",
        "intervention_id",
        "intervention_axis",
        "scenario_class",
        "endpoint",
        "row_count",
        "source_count",
        "unit_count",
        "mean",
        "median",
        "q025",
        "q25",
        "q75",
        "q975",
        "min",
        "max",
    ]
    return pd.DataFrame(rows).loc[:, columns]


def _build_source_intervention_summary(long: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        "proposal_source_key",
        "module4_run_id",
        "variant_id",
        "seed",
        "run_dir_name",
        "proposal_id",
        "partition_label",
        "family_id",
        "family_role",
        "intervention_id",
        "intervention_axis",
        "scenario_class",
        "endpoint",
    ]
    rows: list[dict[str, object]] = []
    for keys, group in long.groupby(group_columns, sort=True):
        row = dict(zip(group_columns, keys, strict=True))
        values = group["contrast_value"]
        row.update({"partition": row.pop("partition_label"), "n_replicates": int(values.count())})
        stats = _summary_stats(values)
        row.update(
            {
                key: value
                for key, value in stats.items()
                if key in {"mean", "median", "q025", "q975", "min", "max"}
            }
        )
        rows.append(row)
    columns = [
        "proposal_source_key",
        "module4_run_id",
        "variant_id",
        "seed",
        "run_dir_name",
        "proposal_id",
        "partition",
        "family_id",
        "family_role",
        "intervention_id",
        "intervention_axis",
        "scenario_class",
        "endpoint",
        "n_replicates",
        "mean",
        "median",
        "q025",
        "q975",
        "min",
        "max",
    ]
    return pd.DataFrame(rows).loc[:, columns]


def _build_direction_summary(long: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        "partition_label",
        "family_id",
        "family_role",
        "intervention_id",
        "intervention_axis",
        "scenario_class",
        "endpoint",
    ]
    rows: list[dict[str, object]] = []
    for keys, group in long.groupby(group_columns, sort=True):
        row = dict(zip(group_columns, keys, strict=True))
        values = group["contrast_value"]
        total = int(values.count())
        negative = int((values < 0).sum())
        zero = int((values == 0).sum())
        positive = int((values > 0).sum())
        row.update(
            {
                "partition": row.pop("partition_label"),
                "value_count": total,
                "negative_count": negative,
                "zero_count": zero,
                "positive_count": positive,
                "negative_proportion": negative / total if total else 0.0,
                "zero_proportion": zero / total if total else 0.0,
                "positive_proportion": positive / total if total else 0.0,
            }
        )
        rows.append(row)
    columns = [
        "partition",
        "family_id",
        "family_role",
        "intervention_id",
        "intervention_axis",
        "scenario_class",
        "endpoint",
        "value_count",
        "negative_count",
        "zero_count",
        "positive_count",
        "negative_proportion",
        "zero_proportion",
        "positive_proportion",
    ]
    return pd.DataFrame(rows).loc[:, columns]


def write_production_summaries(
    *,
    matched_outcomes_path: Path,
    output_dir: Path,
    expected_sha256: str,
    source_artifact: Path,
    source_execution_sha: str,
    goal014_record_sha: str,
    run_id: str,
    command: str,
    expectations: ProductionSummaryExpectations = ProductionSummaryExpectations(),
    endpoints: tuple[str, ...] = DEFAULT_CONTRAST_ENDPOINTS,
    label: str = "goal015-module5-production-summary",
) -> ProductionSummaryResult:
    matched_outcomes_path = matched_outcomes_path.resolve()
    output_dir = output_dir.resolve()
    source_artifact = source_artifact.resolve()

    if not matched_outcomes_path.exists():
        raise FileNotFoundError(f"Missing matched outcomes: {matched_outcomes_path}")
    actual_sha = file_sha256(matched_outcomes_path)
    raw_frame = pd.read_csv(matched_outcomes_path, keep_default_na=False)
    raw_column_count = len(raw_frame.columns)
    frame = _with_partition_labels(raw_frame)
    qc_checks = build_qc_checks(
        frame,
        matched_outcomes_path=matched_outcomes_path,
        source_artifact=source_artifact,
        expected_sha256=expected_sha256,
        actual_sha256=actual_sha,
        expectations=expectations,
        endpoints=endpoints,
        raw_column_count=raw_column_count,
    )
    failed = [str(check["check_name"]) for check in qc_checks if not bool(check["passed"])]
    if failed:
        raise ValueError(f"QC checks failed: {failed}")

    output_dir.mkdir(parents=True, exist_ok=True)
    long = _endpoint_long(frame, endpoints)
    partition_summary = _build_partition_summary(long)
    source_summary = _build_source_intervention_summary(long)
    direction_summary = _build_direction_summary(long)

    metadata_path = output_dir / "summary_metadata.json"
    qc_summary_path = output_dir / "qc_summary.csv"
    partition_path = output_dir / "partition_endpoint_summary.csv"
    source_path = output_dir / "source_intervention_endpoint_summary.csv"
    direction_path = output_dir / "direction_summary.csv"

    pd.DataFrame(qc_checks).to_csv(qc_summary_path, index=False)
    partition_summary.to_csv(partition_path, index=False)
    source_summary.to_csv(source_path, index=False)
    direction_summary.to_csv(direction_path, index=False)

    metadata = {
        "label": label,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_artifact": source_artifact.as_posix(),
        "matched_outcomes_path": matched_outcomes_path.as_posix(),
        "source_execution_sha": source_execution_sha,
        "goal014_record_sha": goal014_record_sha,
        "raw_matched_outcomes_size": matched_outcomes_path.stat().st_size,
        "raw_matched_outcomes_sha256": actual_sha,
        "expected_raw_matched_outcomes_sha256": expected_sha256,
        "summarizer_command": command,
        "row_count": int(len(frame)),
        "column_count": int(raw_column_count),
        "expected_replicates": expectations.expected_replicates,
        "source_intervention_units": expectations.source_intervention_units,
        "distinct_proposal_source_keys": expectations.distinct_proposal_source_keys,
        "contrast_endpoints": list(endpoints),
        "qc_all_passed": True,
        "raw_matched_outcomes_copied_locally": False,
        "non_interpretation_boundary": (
            "Compact descriptive summaries only; no final causal conclusion, "
            "manuscript language, figure/table work, or production attribution "
            "interpretation is made by this Goal 015 artifact."
        ),
        "summary_files": {
            "qc_summary": qc_summary_path.name,
            "partition_endpoint_summary": partition_path.name,
            "source_intervention_endpoint_summary": source_path.name,
            "direction_summary": direction_path.name,
        },
        "summary_row_counts": {
            "qc_summary": len(qc_checks),
            "partition_endpoint_summary": int(len(partition_summary)),
            "source_intervention_endpoint_summary": int(len(source_summary)),
            "direction_summary": int(len(direction_summary)),
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return ProductionSummaryResult(
        output_dir=output_dir,
        metadata_path=metadata_path,
        qc_summary_path=qc_summary_path,
        partition_endpoint_summary_path=partition_path,
        source_intervention_endpoint_summary_path=source_path,
        direction_summary_path=direction_path,
        qc_checks=qc_checks,
    )
