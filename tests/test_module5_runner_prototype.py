from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from galaxias_model.io import load_model_inputs, resolve_family_parameters
from galaxias_model.module5_counterfactual import (
    apply_module5_intervention_overrides,
    run_module5_counterfactual_smoke,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
INTERVENTIONS = DATA_DIR / "module5_counterfactual_interventions.csv"
OUTCOME_SCHEMA = DATA_DIR / "module5_counterfactual_outcome_schema.csv"


def test_module5_intervention_overrides_only_null_requested_pressure_axes() -> None:
    model_inputs = load_model_inputs(DATA_DIR)
    params = resolve_family_parameters(model_inputs, "persistent_joint_cause")

    no_trout = apply_module5_intervention_overrides(params, "no_trout_pressure")
    assert no_trout.value("PR020") == 0.0
    assert no_trout.value("PR021") == 0.0
    assert no_trout.value("PR027") == params.value("PR027")
    assert no_trout.value("PR028") == params.value("PR028")

    no_climbing = apply_module5_intervention_overrides(params, "no_climbing_pressure")
    assert no_climbing.value("PR020") == params.value("PR020")
    assert no_climbing.value("PR021") == params.value("PR021")
    assert no_climbing.value("PR027") == 0.0
    assert no_climbing.value("PR028") == 0.0

    no_biotic_pressure = apply_module5_intervention_overrides(
        params,
        "no_trout_or_climbing_pressure",
    )
    assert no_biotic_pressure.value("PR020") == 0.0
    assert no_biotic_pressure.value("PR021") == 0.0
    assert no_biotic_pressure.value("PR027") == 0.0
    assert no_biotic_pressure.value("PR028") == 0.0


def test_module5_smoke_runner_writes_schema_conforming_matched_pairs(tmp_path: Path) -> None:
    output_dir = tmp_path / "module5_smoke"
    output_file = run_module5_counterfactual_smoke(
        data_dir=DATA_DIR,
        interventions_path=INTERVENTIONS,
        outcome_schema_path=OUTCOME_SCHEMA,
        output_dir=output_dir,
        intervention_ids=("m5_persistent_joint_cause_no_trout_pressure",),
        replicates=2,
        proposal_seed=20260605,
        stochastic=True,
    )

    assert output_file == output_dir / "matched_outcomes.csv"
    assert output_file.exists()
    assert (output_dir / "provenance.json").exists()

    rows = list(csv.DictReader(output_file.open(newline="", encoding="utf-8")))
    assert len(rows) == 2

    schema_columns = set(pd.read_csv(OUTCOME_SCHEMA)["column_name"])
    assert set(rows[0]) == schema_columns

    matched_pair_ids = {row["matched_pair_id"] for row in rows}
    assert len(matched_pair_ids) == 2
    for row in rows:
        assert row["baseline_stochastic_seed"] == row["intervention_stochastic_seed"]
        assert row["run_id_baseline"] != row["run_id_counterfactual"]
        assert row["intervention_axis"] == "no_trout_pressure"
        assert row["provenance_source_file"] == "data/module5_counterfactual_interventions.csv"
