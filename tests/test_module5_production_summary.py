from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from galaxias_model.module5_production_summary import (
    DEFAULT_CONTRAST_ENDPOINTS,
    ProductionSummaryExpectations,
    file_sha256,
    write_production_summaries,
)


def _source_key(family_id: str, proposal_id: str) -> str:
    return (
        "module4_observation_sensitivity_20260522T101942Z|baseline_current|"
        f"20260410|baseline_current_seed20260410|{family_id}|{proposal_id}"
    )


def _row(
    *,
    source_key: str,
    intervention_id: str,
    partition_label: str,
    replicate_id: int,
    extirpation: float,
    persistence_2002: float,
) -> dict[str, object]:
    (
        module4_run_id,
        variant_id,
        seed,
        run_dir_name,
        family_id,
        proposal_id,
    ) = source_key.split("|")
    matched_pair_id = f"{source_key}|{intervention_id}|r{replicate_id}"
    return {
        "partition_label": partition_label,
        "family_id": family_id,
        "family_role": "primary" if family_id == "persistent_joint_cause" else "sensitivity",
        "proposal_id": proposal_id,
        "proposal_source_key": source_key,
        "module4_run_id": module4_run_id,
        "variant_id": variant_id,
        "seed": int(seed),
        "run_dir_name": run_dir_name,
        "proposal_seed": 101,
        "stochastic_replicate_id": replicate_id,
        "intervention_id": intervention_id,
        "intervention_axis": "status_quo",
        "scenario_class": partition_label.split("/")[0],
        "matched_pair_id": matched_pair_id,
        "run_id_baseline": f"{matched_pair_id}|baseline",
        "run_id_counterfactual": f"{matched_pair_id}|counterfactual",
        "baseline_stochastic_seed": 8000 + replicate_id,
        "intervention_stochastic_seed": 8000 + replicate_id,
        "extirpation_year_contrast": extirpation,
        "persistence_2002_contrast": persistence_2002,
        "persistence_1996_contrast": persistence_2002,
        "min_abundance_1992_2002_contrast": extirpation * 10.0,
        "lake_refuge_share_2002_contrast": persistence_2002 / 10.0,
    }


def _matched_frame() -> pd.DataFrame:
    persistent = _source_key("persistent_joint_cause", "persistent_joint_cause:p00001")
    climbing = _source_key("climbing_only", "climbing_only:p00002")
    rows: list[dict[str, object]] = []
    for replicate_id, value in enumerate([1.0, 2.0, 3.0]):
        rows.append(
            _row(
                source_key=persistent,
                intervention_id="m5_persistent_joint_cause_no_trout_pressure",
                partition_label="headline/persistent_joint_cause",
                replicate_id=replicate_id,
                extirpation=value,
                persistence_2002=1.0,
            )
        )
    for replicate_id, value in enumerate([-1.0, 0.0, 1.0]):
        rows.append(
            _row(
                source_key=climbing,
                intervention_id="m5_climbing_only_no_climbing_pressure",
                partition_label="headline/climbing_only",
                replicate_id=replicate_id,
                extirpation=value,
                persistence_2002=value,
            )
        )
    return pd.DataFrame(rows)


def _expectations(frame: pd.DataFrame) -> ProductionSummaryExpectations:
    return ProductionSummaryExpectations(
        row_count=len(frame),
        column_count=len(frame.columns),
        expected_replicates=3,
        source_intervention_units=2,
        distinct_proposal_source_keys=2,
        partition_row_counts={
            "headline/persistent_joint_cause": 3,
            "headline/climbing_only": 3,
        },
        schema_columns=tuple(frame.columns),
    )


def test_write_production_summaries_records_qc_and_endpoint_tables(tmp_path: Path) -> None:
    assert DEFAULT_CONTRAST_ENDPOINTS == (
        "extirpation_year_contrast",
        "persistence_2002_contrast",
        "persistence_1996_contrast",
        "min_abundance_1992_2002_contrast",
        "lake_refuge_share_2002_contrast",
    )
    frame = _matched_frame().drop(columns=["partition_label"])
    matched = tmp_path / "artifact" / "matched_outcomes.csv"
    matched.parent.mkdir()
    frame.to_csv(matched, index=False)

    output_dir = tmp_path / "summary"
    result = write_production_summaries(
        matched_outcomes_path=matched,
        output_dir=output_dir,
        expected_sha256=file_sha256(matched),
        source_artifact=matched.parent,
        source_execution_sha="ddb8a6de583e85f170f46c9dec9b1246baa6dccc",
        goal014_record_sha="a96cfed24800823b77cbafeed5e9603e9dd6d33c",
        run_id="synthetic-goal015",
        command="synthetic command",
        expectations=_expectations(frame),
    )

    assert result.all_qc_passed
    metadata = json.loads((output_dir / "summary_metadata.json").read_text(encoding="utf-8"))
    assert metadata["row_count"] == 6
    assert metadata["non_interpretation_boundary"]
    assert metadata["raw_matched_outcomes_copied_locally"] is False
    assert set(metadata["contrast_endpoints"]) == set(DEFAULT_CONTRAST_ENDPOINTS)

    qc = pd.read_csv(output_dir / "qc_summary.csv")
    assert qc["passed"].all()
    assert set(qc["check_name"]) >= {
        "raw_file_exists",
        "raw_sha256",
        "row_count",
        "replicate_ids",
        "replicate_coverage",
        "seed_mismatches",
        "partition_counts",
    }

    partition = pd.read_csv(output_dir / "partition_endpoint_summary.csv")
    persistent_extirpation = partition.loc[
        (partition["partition"] == "headline/persistent_joint_cause")
        & (partition["endpoint"] == "extirpation_year_contrast")
    ].iloc[0]
    assert persistent_extirpation["row_count"] == 3
    assert persistent_extirpation["source_count"] == 1
    assert persistent_extirpation["unit_count"] == 1
    assert persistent_extirpation["mean"] == 2.0
    assert persistent_extirpation["median"] == 2.0

    source_summary = pd.read_csv(output_dir / "source_intervention_endpoint_summary.csv")
    assert set(source_summary["proposal_source_key"]) == set(frame["proposal_source_key"])
    assert set(source_summary["n_replicates"]) == {3}

    directions = pd.read_csv(output_dir / "direction_summary.csv")
    climbing_extirpation = directions.loc[
        (directions["intervention_id"] == "m5_climbing_only_no_climbing_pressure")
        & (directions["endpoint"] == "extirpation_year_contrast")
    ].iloc[0]
    assert climbing_extirpation["negative_count"] == 1
    assert climbing_extirpation["zero_count"] == 1
    assert climbing_extirpation["positive_count"] == 1
    assert climbing_extirpation["negative_proportion"] == pytest.approx(1 / 3)

    for csv_name in [
        "partition_endpoint_summary.csv",
        "source_intervention_endpoint_summary.csv",
        "direction_summary.csv",
    ]:
        columns = pd.read_csv(output_dir / csv_name, nrows=0).columns
        assert "matched_pair_id" not in columns
        assert "run_id_baseline" not in columns
    assert not (output_dir / "matched_outcomes.csv").exists()


def test_write_production_summaries_fails_on_broken_qc(tmp_path: Path) -> None:
    frame = _matched_frame()
    frame.loc[0, "intervention_stochastic_seed"] = 999999
    frame = frame.drop(index=frame.index[-1])
    matched = tmp_path / "artifact" / "matched_outcomes.csv"
    matched.parent.mkdir()
    frame.to_csv(matched, index=False)

    with pytest.raises(ValueError, match="QC checks failed"):
        write_production_summaries(
            matched_outcomes_path=matched,
            output_dir=tmp_path / "summary",
            expected_sha256=file_sha256(matched),
            source_artifact=matched.parent,
            source_execution_sha="ddb8a6de583e85f170f46c9dec9b1246baa6dccc",
            goal014_record_sha="a96cfed24800823b77cbafeed5e9603e9dd6d33c",
            run_id="synthetic-goal015",
            command="synthetic command",
            expectations=_expectations(_matched_frame()),
        )
