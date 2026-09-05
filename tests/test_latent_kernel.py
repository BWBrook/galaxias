from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from galaxias_model import (
    SimulationConfig,
    build_historical_forcing,
    load_model_inputs,
    resolve_family_parameters,
    run_historical_simulation,
)
from galaxias_model.types import ModelInputs


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FAMILY_IDS = [
    "habitat_only_null",
    "trout_only",
    "climbing_only",
    "persistent_joint_cause",
    "transient_perfect_storm",
]


@pytest.fixture(scope="module")
def model_inputs() -> ModelInputs:
    return load_model_inputs(DATA_DIR)


def test_resolve_all_families(model_inputs: ModelInputs) -> None:
    for family_id in FAMILY_IDS:
        params = resolve_family_parameters(model_inputs, family_id)
        assert len(params.manifest) == 40
        assert len(params.values) == 40
        assert len(params.statuses) == 40
        assert params.manifest["parameter_id"].is_unique
        assert {"PR039", "PR040"}.issubset(set(params.manifest["parameter_id"]))


def test_constraint_violations_fail_before_simulation(model_inputs: ModelInputs) -> None:
    broken_priors = model_inputs.parameter_priors.copy()
    broken_priors.loc[broken_priors["parameter_id"] == "PR020", "default_value"] = "0.01"
    broken_priors.loc[broken_priors["parameter_id"] == "PR021", "default_value"] = "0.05"
    broken_inputs = replace(model_inputs, parameter_priors=broken_priors)

    with pytest.raises(ValueError, match="PC001"):
        resolve_family_parameters(broken_inputs, "transient_perfect_storm")


def test_forcing_schedule_matches_expected_shape(model_inputs: ModelInputs) -> None:
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    years = list(range(1965, 2003))
    forcing = build_historical_forcing(years, params).table
    lag_year = 1972 + int(params.value("PR040"))

    assert (forcing.loc[forcing["year"] < 1972, "U"] == 0).all()
    assert (forcing.loc[forcing["year"] < 1972, "H"] == 0).all()
    assert int(forcing.loc[forcing["U"].idxmax(), "year"]) == 1977
    assert forcing.loc[forcing["year"] == lag_year, "H"].iloc[0] == pytest.approx(1.0)
    assert (forcing.loc[forcing["year"] != 1972, "stocking_input"] == 0).all()
    assert forcing.loc[forcing["year"] == 1972, "stocking_input"].iloc[0] > 0


def test_family_specific_states_toggle_cleanly(model_inputs: ModelInputs) -> None:
    config = SimulationConfig(stochastic=False)

    habitat = run_historical_simulation(
        resolve_family_parameters(model_inputs, "habitat_only_null"),
        "habitat_only_null",
        config,
        seed=1,
    ).trajectory_table
    assert (habitat[["T", "P", "C_L", "C_R"]] == 0).all().all()

    trout = run_historical_simulation(
        resolve_family_parameters(model_inputs, "trout_only"),
        "trout_only",
        config,
        seed=1,
    ).trajectory_table
    assert (trout[["C_L", "C_R"]] == 0).all().all()

    climbing = run_historical_simulation(
        resolve_family_parameters(model_inputs, "climbing_only"),
        "climbing_only",
        config,
        seed=1,
    ).trajectory_table
    assert (climbing[["T", "P"]] == 0).all().all()

    persistent = run_historical_simulation(
        resolve_family_parameters(model_inputs, "persistent_joint_cause"),
        "persistent_joint_cause",
        config,
        seed=1,
    ).trajectory_table
    post_connection = persistent.loc[persistent["year"] >= 1972, "P"]
    pr017 = resolve_family_parameters(model_inputs, "persistent_joint_cause").value("PR017")
    assert np.allclose(post_connection.to_numpy(), pr017)


def test_kernel_invariants_hold_across_families(model_inputs: ModelInputs) -> None:
    config = SimulationConfig(stochastic=False)
    for family_id in FAMILY_IDS:
        result = run_historical_simulation(
            resolve_family_parameters(model_inputs, family_id),
            family_id,
            config,
            seed=1,
        )
        trajectory = result.trajectory_table

        assert (trajectory[["J_L", "A_L", "J_R", "A_R", "N_L", "N_R", "N_total"]] >= 0).all().all()
        assert (trajectory.loc[trajectory["year"] < 1972, "N_total"] > 0).all()
        assert trajectory["pedder_lake_index"].between(0, 1).all()
        assert trajectory["pedder_refuge_index"].between(0, 1).all()
        assert (trajectory[["K_L_count", "K_R_count"]] > 0).all().all()
        assert set(result.summary).issuperset(
            {
                "peak_year_pedder_lake_index",
                "peak_value_pedder_lake_index",
                "first_year_climbing_ratio_gt_one",
                "first_year_lake_absent",
                "last_year_total_present",
                "first_year_total_absent",
                "peak_trout_year",
                "peak_upsurge_year",
                "pre1972_min_total",
                "boom_ratio_1977_vs_1965",
                "final_to_peak_ratio",
            }
        )


def test_default_deterministic_review_gates_hold(model_inputs: ModelInputs) -> None:
    config = SimulationConfig(stochastic=False)
    habitat = run_historical_simulation(
        resolve_family_parameters(model_inputs, "habitat_only_null"),
        "habitat_only_null",
        config,
        seed=1,
    )
    transient = run_historical_simulation(
        resolve_family_parameters(model_inputs, "transient_perfect_storm"),
        "transient_perfect_storm",
        config,
        seed=1,
    )

    assert 1975 <= habitat.summary["peak_year_pedder_lake_index"] <= 1978
    assert 1975 <= transient.summary["peak_year_pedder_lake_index"] <= 1978
    assert habitat.summary["boom_ratio_1977_vs_1965"] > 1
    assert transient.summary["boom_ratio_1977_vs_1965"] > 1
    assert transient.trajectory_table["N_total"].iloc[-1] < habitat.trajectory_table["N_total"].iloc[-1]
    assert 1980 <= transient.summary["first_year_climbing_ratio_gt_one"] <= 1984


def test_default_stochastic_review_gates_hold(model_inputs: ModelInputs) -> None:
    config = SimulationConfig(stochastic=True)
    summaries: list[dict[str, int | float | None | str]] = []
    present_in_1980 = 0
    for seed in range(1, 21):
        result = run_historical_simulation(
            resolve_family_parameters(model_inputs, "transient_perfect_storm"),
            "transient_perfect_storm",
            config,
            seed=seed,
        )
        summaries.append(result.summary)
        present_in_1980 += int(
            result.trajectory_table.loc[result.trajectory_table["year"] == 1980, "total_present"].iloc[0] == 1
        )

    summary_frame = pd.DataFrame(summaries)
    assert (summary_frame["pre1972_min_total"] > 0).all()
    assert (summary_frame["peak_year_pedder_lake_index"].between(1975, 1978)).median() >= 0.5
    assert summary_frame["peak_year_pedder_lake_index"].median() >= 1975
    assert summary_frame["peak_year_pedder_lake_index"].median() <= 1978

    assert present_in_1980 >= 18


def test_stochastic_seed_is_reproducible_and_deterministic_mode_ignores_seed(
    model_inputs: ModelInputs,
) -> None:
    stochastic_config = SimulationConfig(stochastic=True)
    params = resolve_family_parameters(model_inputs, "transient_perfect_storm")
    stochastic_a = run_historical_simulation(params, "transient_perfect_storm", stochastic_config, seed=42)
    stochastic_b = run_historical_simulation(params, "transient_perfect_storm", stochastic_config, seed=42)
    pd.testing.assert_frame_equal(stochastic_a.trajectory_table, stochastic_b.trajectory_table)

    deterministic_config = SimulationConfig(stochastic=False)
    deterministic_a = run_historical_simulation(params, "transient_perfect_storm", deterministic_config, seed=1)
    deterministic_b = run_historical_simulation(params, "transient_perfect_storm", deterministic_config, seed=999)
    pd.testing.assert_frame_equal(
        deterministic_a.trajectory_table.drop(columns=["seed"]),
        deterministic_b.trajectory_table.drop(columns=["seed"]),
    )


def test_cli_writes_expected_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "latent_run"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_latent_simulation.py"),
            "--family-id",
            "transient_perfect_storm",
            "--seed",
            "7",
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        check=True,
    )

    trajectory_path = output_dir / "trajectory.csv"
    summary_path = output_dir / "summary.json"
    resolved_path = output_dir / "resolved_parameters.json"

    assert trajectory_path.exists()
    assert summary_path.exists()
    assert resolved_path.exists()

    trajectory = pd.read_csv(trajectory_path)
    with summary_path.open(encoding="utf-8") as handle:
        summary = json.load(handle)
    with resolved_path.open(encoding="utf-8") as handle:
        resolved = json.load(handle)

    assert len(trajectory) == 38
    assert summary["family_id"] == "transient_perfect_storm"
    assert resolved["family_id"] == "transient_perfect_storm"
    assert len(resolved["parameters"]) == 40
