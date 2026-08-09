from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from galaxias_model.module5_counterfactual import read_outcome_schema_columns
from galaxias_model.module5_factorial_extension import (
    FACTORIAL_EXTENSION_SOURCE_COUNTS,
    build_factorial_extension_plan,
    derive_factorial_block_seed,
    _run_four_arm_block,
)
from galaxias_model.module5_factorial_extension_audit import (
    BASELINE_COLUMNS,
    build_250_replication_decision,
    build_shared_block_qc,
    compute_shared_block_source_effects,
    run_factorial_extension_audit,
)
from galaxias_model.module5_interaction_stability import EFFECT_COLUMNS, ENDPOINTS
from galaxias_model.module5_proposals import PROPOSAL_SOURCE_KEY_FIELDS
from galaxias_model.types import ResolvedParameters, SimulationConfig


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MEMBERSHIP = DATA_DIR / "module4_5_proposal_set_membership.csv"
MANIFEST = DATA_DIR / "module4_raw_artifact_manifest.csv"
INTERVENTIONS = DATA_DIR / "module5_counterfactual_interventions.csv"
OUTCOME_SCHEMA = DATA_DIR / "module5_counterfactual_outcome_schema.csv"


def test_factorial_plan_and_seed_contract() -> None:
    plan = build_factorial_extension_plan(
        MEMBERSHIP,
        INTERVENTIONS,
        MANIFEST,
        replicates=250,
    )
    assert plan.source_count_by_family == FACTORIAL_EXTENSION_SOURCE_COUNTS
    assert plan.source_count == 515
    assert plan.source_context_count == 15
    assert len(plan.required_artifacts) == 15
    assert plan.expected_source_replicate_blocks == 128750
    assert plan.expected_source_intervention_units == 1545
    assert plan.expected_simulation_count == 515000
    assert plan.expected_row_count == 386250
    assert plan.expected_family_row_counts == {
        "persistent_joint_cause": 198750,
        "transient_perfect_storm": 187500,
    }

    source_key = plan.sources[0].proposal_source_key
    seed = derive_factorial_block_seed(source_key, 0)
    assert seed == derive_factorial_block_seed(source_key, 0)
    assert 0 <= seed < 2**63
    assert seed != derive_factorial_block_seed(source_key, 1)
    assert seed != derive_factorial_block_seed(plan.sources[1].proposal_source_key, 0)
    with pytest.raises(ValueError, match="replicate_id"):
        derive_factorial_block_seed(source_key, -1)


def test_four_arm_block_runs_status_quo_once_with_one_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    parameter_ids = ["PR020", "PR021", "PR027", "PR028"]
    params = ResolvedParameters(
        family_id="persistent_joint_cause",
        family_label="Persistent joint cause",
        manifest=pd.DataFrame(
            {
                "parameter_id": parameter_ids,
                "effective_value": [1.0, 2.0, 3.0, 4.0],
            }
        ),
        values=dict(zip(parameter_ids, [1.0, 2.0, 3.0, 4.0], strict=True)),
        statuses={parameter_id: "direct_pedder" for parameter_id in parameter_ids},
    )
    rows = tuple(
        {"intervention_axis": axis}
        for axis in (
            "no_trout_pressure",
            "no_climbing_pressure",
            "no_trout_or_climbing_pressure",
        )
    )
    calls: list[tuple[int, dict[str, float]]] = []

    def fake_run(resolved, family_id, config, *, seed):
        assert family_id == "persistent_joint_cause"
        assert config.stochastic
        calls.append((seed, dict(resolved.values)))
        return object()

    monkeypatch.setattr(
        "galaxias_model.module5_factorial_extension.run_historical_simulation",
        fake_run,
    )
    results = _run_four_arm_block(
        params,
        "persistent_joint_cause",
        SimulationConfig(stochastic=True),
        rows,
        seed=12345,
    )

    assert set(results) == {
        "status_quo",
        "no_trout_pressure",
        "no_climbing_pressure",
        "no_trout_or_climbing_pressure",
    }
    assert len(calls) == 4
    assert {seed for seed, _ in calls} == {12345}
    assert calls[0][1] == params.values
    assert calls[1][1]["PR020"] == calls[1][1]["PR021"] == 0.0
    assert calls[1][1]["PR027"] == 3.0
    assert calls[2][1]["PR027"] == calls[2][1]["PR028"] == 0.0
    assert all(value == 0.0 for value in calls[3][1].values())


def _source_key(family: str, variant: str, seed: int, proposal: str) -> str:
    return f"m4|{variant}|{seed}|{variant}_seed{seed}|{family}|{proposal}"


def _effect_frame(replicates: int = 10) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for family, variant, calibration_seed, proposal in (
        ("persistent_joint_cause", "v1", 1, "p1"),
        ("transient_perfect_storm", "v2", 2, "p2"),
    ):
        source_key = _source_key(family, variant, calibration_seed, proposal)
        for replicate in range(replicates):
            value = -1.0 if replicate % 2 == 0 else 1.0
            for axis, multiplier in (
                ("no_trout_pressure", 1.0),
                ("no_climbing_pressure", 1.0),
                ("no_trout_or_climbing_pressure", 2.0),
            ):
                row = {
                    "proposal_source_key": source_key,
                    "module4_run_id": "m4",
                    "variant_id": variant,
                    "seed": calibration_seed,
                    "run_dir_name": f"{variant}_seed{calibration_seed}",
                    "family_id": family,
                    "proposal_id": proposal,
                    "proposal_seed": calibration_seed,
                    "stochastic_replicate_id": replicate,
                    "intervention_axis": axis,
                }
                row.update(
                    {endpoint: multiplier * value for endpoint in ENDPOINTS}
                )
                rows.append(row)
    return pd.DataFrame(rows)


def test_shared_block_interaction_variance_uses_replicate_covariance() -> None:
    frame = _effect_frame()
    tolerances = {
        (family, endpoint): 0.01
        for family in ("persistent_joint_cause", "transient_perfect_storm")
        for endpoint in ENDPOINTS
    }
    effects = compute_shared_block_source_effects(
        frame,
        replicate_start=0,
        replicate_stop=10,
        window_label="prefix_10",
        window_type="prefix",
        tolerances=tolerances,
    )
    row = effects.loc[
        (effects["family_id"] == "persistent_joint_cause")
        & (effects["endpoint"] == "persistence_2002_contrast")
    ].iloc[0]
    assert row["additive_interaction"] == pytest.approx(0.0)
    assert row["additive_interaction_mc_variance"] == pytest.approx(0.0)
    assert row["trout_removal_mc_variance"] > 0
    assert row["climbing_removal_mc_variance"] > 0
    assert row["joint_removal_mc_variance"] > 0


def _complete_outcome_frame(replicates: int = 5) -> tuple[pd.DataFrame, dict[str, object]]:
    schema = read_outcome_schema_columns(OUTCOME_SCHEMA)
    source_definitions = (
        ("persistent_joint_cause", "v1", 1, "p1"),
        ("transient_perfect_storm", "v2", 2, "p2"),
    )
    rows: list[dict[str, object]] = []
    source_keys: list[str] = []
    for family, variant, calibration_seed, proposal in source_definitions:
        source_key = _source_key(family, variant, calibration_seed, proposal)
        source_keys.append(source_key)
        for replicate in range(replicates):
            block_seed = 100000 + calibration_seed * 1000 + replicate
            for axis in (
                "no_trout_pressure",
                "no_climbing_pressure",
                "no_trout_or_climbing_pressure",
            ):
                intervention_id = f"m5_{family}_{axis}"
                matched_pair_id = f"{source_key}|{intervention_id}|r{replicate}"
                row = {column: 0 for column in schema}
                row.update(
                    {
                        "family_id": family,
                        "family_role": "primary" if family == "persistent_joint_cause" else "sensitivity",
                        "proposal_id": proposal,
                        "proposal_source_key": source_key,
                        "module4_run_id": "m4",
                        "variant_id": variant,
                        "seed": calibration_seed,
                        "run_dir_name": f"{variant}_seed{calibration_seed}",
                        "proposal_seed": calibration_seed,
                        "stochastic_replicate_id": replicate,
                        "intervention_id": intervention_id,
                        "intervention_axis": axis,
                        "scenario_class": "historical_match",
                        "matched_pair_id": matched_pair_id,
                        "run_id_baseline": f"{matched_pair_id}|baseline",
                        "run_id_counterfactual": f"{matched_pair_id}|counterfactual",
                        "baseline_stochastic_seed": block_seed,
                        "intervention_stochastic_seed": block_seed,
                        "year": 2002,
                        "persistence_2002_baseline": 1,
                        "persistence_1996_baseline": 1,
                        "min_abundance_1992_2002_baseline": 100.0,
                        "lake_refuge_share_2002_baseline": 0.5,
                        "persistence_2002_contrast": 0.0,
                        "min_abundance_1992_2002_contrast": 1.0,
                        "lake_refuge_share_2002_contrast": 0.01,
                        "processing_timestamp": "2026-08-09T00:00:00+00:00",
                        "provenance_source_file": INTERVENTIONS.as_posix(),
                        "provenance_git_sha": "test",
                        "provenance_script": "scripts/run_module5_factorial_extension.py",
                        "provenance_module4_manifest": MANIFEST.as_posix(),
                    }
                )
                rows.append(row)
    provenance = {
        "status": "module5_shared_four_arm_extension",
        "production_attribution": False,
        "status_quo_executed_once_per_block": True,
        "expected_replicates": replicates,
        "expected_row_count": len(rows),
        "stored_contrast_axes": [
            "no_trout_pressure",
            "no_climbing_pressure",
            "no_trout_or_climbing_pressure",
        ],
        "selected_proposal_source_keys": source_keys,
        "source_identity_fields": list(PROPOSAL_SOURCE_KEY_FIELDS),
    }
    return pd.DataFrame(rows, columns=schema), provenance


def test_shared_block_qc_detects_seed_and_baseline_breaks() -> None:
    frame, provenance = _complete_outcome_frame()
    expected_counts = {
        "persistent_joint_cause": 1,
        "transient_perfect_storm": 1,
    }
    qc = build_shared_block_qc(
        frame,
        provenance,
        schema_columns=read_outcome_schema_columns(OUTCOME_SCHEMA),
        expected_row_count=len(frame),
        expected_replicates=5,
        expected_contexts=1,
        expected_source_counts=expected_counts,
    )
    assert qc["passed"].all(), qc.loc[~qc["passed"].astype(bool)].to_dict("records")

    broken = frame.copy()
    broken.loc[0, "baseline_stochastic_seed"] += 1
    broken.loc[1, BASELINE_COLUMNS[0]] = 0
    failed = build_shared_block_qc(
        broken,
        provenance,
        schema_columns=read_outcome_schema_columns(OUTCOME_SCHEMA),
        expected_row_count=len(frame),
        expected_replicates=5,
        expected_contexts=1,
        expected_source_counts=expected_counts,
    ).set_index("check_name")
    assert not bool(failed.loc["one_seed_across_stored_arms", "passed"])
    assert not bool(failed.loc["shared_status_quo_baseline_values", "passed"])


def _decision_frame(*, source_drift: bool = False) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for weighting in ("context_equal", "source_equal"):
        for effect in EFFECT_COLUMNS:
            for replicates in (100, 175, 250):
                near_zero = 0.8
                if source_drift and replicates == 250:
                    near_zero = 0.7
                estimate = -0.02 if effect == "additive_interaction" else 0.03
                rows.append(
                    {
                        "family_id": "persistent_joint_cause",
                        "endpoint": "persistence_2002_contrast",
                        "window_label": f"prefix_{replicates}",
                        "window_type": "prefix",
                        "replicate_start": 0,
                        "replicate_stop_exclusive": replicates,
                        "n_replicates_per_intervention": replicates,
                        "tolerance": 0.01,
                        "effect": effect,
                        "weighting": weighting,
                        "estimate": estimate,
                        "mc_se": 0.001,
                        "mc_95_half_width": 0.00196,
                        "mc_95_low": estimate - 0.00196,
                        "mc_95_high": estimate + 0.00196,
                        "classification": (
                            "less_than_additive"
                            if effect == "additive_interaction"
                            else "positive"
                        ),
                        "source_negative_proportion": 0.2,
                        "source_near_zero_proportion": near_zero,
                        "source_positive_proportion": 0.8 - near_zero,
                        "source_count": 10,
                        "context_count": 2,
                        "context_min": estimate,
                        "context_max": estimate,
                    }
                )
    return pd.DataFrame(rows)


def test_250_decision_stops_and_distinguishes_source_distribution_drift() -> None:
    stable = build_250_replication_decision(_decision_frame()).iloc[0]
    assert stable["decision"] == "stable_at_250"
    assert stable["stop_replicates"] == 250

    drifting = build_250_replication_decision(
        _decision_frame(source_drift=True)
    ).iloc[0]
    assert drifting["family_level_stable_at_250"]
    assert not drifting["source_class_proportion_pass"]
    assert drifting["decision"] == (
        "family_level_stable_source_distribution_unstable"
    )


def test_full_250_audit_runs_on_complete_shared_blocks() -> None:
    frame, provenance = _complete_outcome_frame(replicates=250)
    result = run_factorial_extension_audit(
        frame,
        provenance,
        schema_columns=read_outcome_schema_columns(OUTCOME_SCHEMA),
        expected_row_count=len(frame),
        expected_replicates=250,
        expected_contexts=1,
        expected_source_counts={
            "persistent_joint_cause": 1,
            "transient_perfect_storm": 1,
        },
    )
    assert result["qc"]["passed"].all()
    assert set(result["prefix_summary"]["window_label"]) == {
        "prefix_100",
        "prefix_175",
        "prefix_250",
        "batch_000_049",
        "batch_050_099",
        "batch_100_149",
        "batch_150_199",
        "batch_200_249",
    }
    assert len(result["decision"]) == 6
    assert set(result["decision"]["stop_replicates"]) == {250}
