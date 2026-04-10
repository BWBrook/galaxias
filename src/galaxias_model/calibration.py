from __future__ import annotations

import json
import math
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galaxias_model.io import load_model_inputs
from galaxias_model.sampling import build_resolved_parameters_from_sample, sample_family_parameter_table
from galaxias_model.scoring import aggregate_scenario_bundle_scores, score_family_scenario_bundle
from galaxias_model.simulation import get_scenario_definition, run_historical_simulation, run_scenario_simulation
from galaxias_model.types import (
    CalibrationRunResult,
    FamilyCalibrationResult,
    ModelInputs,
    Module3Config,
    ProposalResult,
    ScenarioBundleResult,
    ScoringConfig,
    SimulationConfig,
)


DEFAULT_FAMILY_ORDER = [
    "habitat_only_null",
    "trout_only",
    "climbing_only",
    "persistent_joint_cause",
    "transient_perfect_storm",
]
STAGE_A_CODE = 101
STAGE_B_CODE = 202
STAGE_B_BASELINE_CODE = 203
SCORED_STAGE_A_STATUSES = {"stage_a_rejected", "stage_a_retained", "stage_b_failed", "stage_b_rejected", "accepted"}
FINAL_STAGE_B_STATUSES = {"stage_b_failed", "stage_b_rejected", "accepted"}
STAGE_B_VALID_STATUSES = {"stage_b_rejected", "accepted"}
SUMMARY_COLUMNS = [
    "proposal_id",
    "family_id",
    "family_label",
    "proposal_index",
    "stage_status",
    "proposal_seed",
    "deterministic_overall_distance",
    "deterministic_historical_core_distance",
    "deterministic_intrinsic_baseline_distance",
    "stochastic_overall_distance_median",
    "stochastic_historical_core_distance_median",
    "stochastic_intrinsic_baseline_distance_median",
    "stochastic_historical_core_distance_iqr",
    "accepted_final",
    "failure_reason",
    "deterministic_full_ready_for_module3",
    "stochastic_full_ready_for_module3",
    "stage_a_rank",
    "stage_b_rank",
]
PARAMETER_COLUMNS = [
    "proposal_id",
    "family_id",
    "parameter_id",
    "parameter_status",
    "value_natural",
    "value_sampling",
    "sampled_flag",
]
TARGET_SCORE_COLUMNS = [
    "proposal_id",
    "family_id",
    "stage",
    "replicate_index",
    "target_id",
    "scenario_id",
    "evaluation_status",
    "raw_penalty",
    "weighted_penalty",
    "projected_primary",
    "projected_secondary",
]


def _empty_summary_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=SUMMARY_COLUMNS)


def _empty_parameter_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=PARAMETER_COLUMNS)


def _empty_target_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=TARGET_SCORE_COLUMNS)


def _family_index(family_id: str) -> int:
    if family_id not in DEFAULT_FAMILY_ORDER:
        raise ValueError(f"Unsupported family_id: {family_id}")
    return DEFAULT_FAMILY_ORDER.index(family_id) + 1


def _derive_seed(master_seed: int, *parts: int) -> int:
    modulus = 2**32 - 5
    value = int(master_seed) % modulus
    for part in parts:
        value = (value * 1664525 + 1013904223 + int(part) * 374761393) % modulus
    return int(value or 1)


def _proposal_id(family_id: str, proposal_index: int) -> str:
    return f"{family_id}:p{proposal_index:05d}"


def _selected_families(config: Module3Config) -> list[str]:
    families = list(config.families)
    unknown = [family_id for family_id in families if family_id not in DEFAULT_FAMILY_ORDER]
    if unknown:
        raise ValueError(f"Unknown families in Module3Config: {unknown}")
    return [family_id for family_id in DEFAULT_FAMILY_ORDER if family_id in families]


def _normalize_output_dir(output_dir: Path) -> Path:
    return output_dir.resolve()


def _config_to_jsonable(config: Module3Config) -> dict[str, Any]:
    return {
        "families": list(config.families),
        "stage_a_draws_per_family": int(config.stage_a_draws_per_family),
        "stage_a_keep_per_family": int(config.stage_a_keep_per_family),
        "stage_b_historical_replicates": int(config.stage_b_historical_replicates),
        "final_acceptance_fraction": float(config.final_acceptance_fraction),
        "final_acceptance_cap": int(config.final_acceptance_cap),
        "workers": int(config.workers),
        "batch_size": int(config.batch_size),
        "master_seed": int(config.master_seed),
        "stochastic_baselines": bool(config.stochastic_baselines),
        "output_dir": str(_normalize_output_dir(config.output_dir)),
        "resume": bool(config.resume),
    }


def _build_manifest(model_inputs: ModelInputs, config: Module3Config) -> dict[str, Any]:
    return {
        "module": "module3",
        "config": _config_to_jsonable(config),
        "parameter_count": int(len(model_inputs.parameter_priors)),
        "target_count": int(len(model_inputs.calibration_targets)) if model_inputs.calibration_targets is not None else 0,
        "scenario_ids": sorted(model_inputs.scenario_definitions) if model_inputs.scenario_definitions is not None else [],
    }


def _validate_module3_config(config: Module3Config) -> None:
    if config.stage_a_draws_per_family <= 0:
        raise ValueError("stage_a_draws_per_family must be positive")
    if config.stage_a_keep_per_family <= 0:
        raise ValueError("stage_a_keep_per_family must be positive")
    if config.stage_a_keep_per_family > config.stage_a_draws_per_family:
        raise ValueError("stage_a_keep_per_family cannot exceed stage_a_draws_per_family")
    if config.stage_b_historical_replicates <= 0:
        raise ValueError("stage_b_historical_replicates must be positive")
    if not 0 < config.final_acceptance_fraction <= 1:
        raise ValueError("final_acceptance_fraction must be in (0, 1]")
    if config.final_acceptance_cap <= 0:
        raise ValueError("final_acceptance_cap must be positive")
    if config.workers <= 0:
        raise ValueError("workers must be positive")
    if config.batch_size <= 0:
        raise ValueError("batch_size must be positive")


def _proposal_summary_row(
    proposal_id: str,
    family_id: str,
    family_label: str,
    proposal_index: int,
    proposal_seed: int,
    stage_status: str,
    failure_reason: str = "",
) -> dict[str, Any]:
    return {
        "proposal_id": proposal_id,
        "family_id": family_id,
        "family_label": family_label,
        "proposal_index": int(proposal_index),
        "stage_status": stage_status,
        "proposal_seed": int(proposal_seed),
        "deterministic_overall_distance": float("nan"),
        "deterministic_historical_core_distance": float("nan"),
        "deterministic_intrinsic_baseline_distance": float("nan"),
        "stochastic_overall_distance_median": float("nan"),
        "stochastic_historical_core_distance_median": float("nan"),
        "stochastic_intrinsic_baseline_distance_median": float("nan"),
        "stochastic_historical_core_distance_iqr": float("nan"),
        "accepted_final": False,
        "failure_reason": failure_reason,
        "deterministic_full_ready_for_module3": False,
        "stochastic_full_ready_for_module3": False,
        "stage_a_rank": float("nan"),
        "stage_b_rank": float("nan"),
    }


def _bundle_target_records(
    proposal_id: str,
    family_id: str,
    stage: str,
    replicate_index: int,
    bundle_target_score_table: pd.DataFrame,
) -> pd.DataFrame:
    table = bundle_target_score_table.copy()
    table["proposal_id"] = proposal_id
    table["family_id"] = family_id
    table["stage"] = stage
    table["replicate_index"] = replicate_index
    return table[TARGET_SCORE_COLUMNS].copy()


@lru_cache(maxsize=None)
def _load_inputs_cached(data_dir: str) -> ModelInputs:
    return load_model_inputs(data_dir)


def _scenario_config(model_inputs: ModelInputs, scenario_id: str, stochastic: bool) -> SimulationConfig:
    scenario_definition = get_scenario_definition(model_inputs, scenario_id)
    return SimulationConfig(
        stochastic=stochastic,
        scenario_id=scenario_id,
        scenario_definition=scenario_definition,
        start_year=scenario_definition.start_year,
        end_year=scenario_definition.end_year,
    )


def _run_bundle_from_params(
    params,
    family_id: str,
    model_inputs: ModelInputs,
    historical_stochastic: bool,
    historical_seed: int,
    stochastic_baselines: bool = False,
    baseline_seed_base: int | None = None,
) -> ScenarioBundleResult:
    results_by_scenario = {
        "historical_lake": run_historical_simulation(
            params,
            family_id,
            _scenario_config(model_inputs, "historical_lake", historical_stochastic),
            seed=historical_seed,
        ),
        "lake_oberon": run_scenario_simulation(
            params,
            family_id,
            _scenario_config(model_inputs, "lake_oberon", stochastic_baselines),
            seed=(baseline_seed_base or historical_seed),
        ),
        "strathgordon": run_scenario_simulation(
            params,
            family_id,
            _scenario_config(model_inputs, "strathgordon", stochastic_baselines),
            seed=(baseline_seed_base or historical_seed) + 1,
        ),
    }
    return score_family_scenario_bundle(results_by_scenario, model_inputs, ScoringConfig())


def run_deterministic_bundle(
    params,
    family_id: str,
    model_inputs: ModelInputs,
    seed: int,
) -> ScenarioBundleResult:
    return _run_bundle_from_params(
        params,
        family_id,
        model_inputs,
        historical_stochastic=False,
        historical_seed=seed,
        stochastic_baselines=False,
    )


def _stage_a_worker(task: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    model_inputs = _load_inputs_cached(task["data_dir"])
    parameter_rows = pd.DataFrame(task["parameter_rows"])
    proposal_id = str(task["proposal_id"])
    family_id = str(task["family_id"])
    family_label = str(task["family_label"])
    proposal_index = int(task["proposal_index"])
    proposal_seed = int(task["proposal_seed"])

    try:
        params = build_resolved_parameters_from_sample(model_inputs, family_id, parameter_rows)
    except Exception as exc:
        return (
            _proposal_summary_row(
                proposal_id=proposal_id,
                family_id=family_id,
                family_label=family_label,
                proposal_index=proposal_index,
                proposal_seed=proposal_seed,
                stage_status="constraint_failure",
                failure_reason=str(exc),
            ),
            [],
        )

    try:
        bundle = run_deterministic_bundle(params, family_id, model_inputs, proposal_seed)
    except Exception as exc:
        return (
            _proposal_summary_row(
                proposal_id=proposal_id,
                family_id=family_id,
                family_label=family_label,
                proposal_index=proposal_index,
                proposal_seed=proposal_seed,
                stage_status="stage_a_failed",
                failure_reason=str(exc),
            ),
            [],
        )

    summary = bundle.summary
    deterministic_values = [
        summary["overall_distance"],
        summary["historical_core_distance"],
        summary["intrinsic_baseline_distance"],
    ]
    if not all(value is not None and math.isfinite(float(value)) for value in deterministic_values):
        return (
            _proposal_summary_row(
                proposal_id=proposal_id,
                family_id=family_id,
                family_label=family_label,
                proposal_index=proposal_index,
                proposal_seed=proposal_seed,
                stage_status="stage_a_failed",
                failure_reason="Non-finite deterministic bundle distance",
            ),
            [],
        )

    score_rows = _bundle_target_records(
        proposal_id=proposal_id,
        family_id=family_id,
        stage="stage_a",
        replicate_index=0,
        bundle_target_score_table=bundle.bundle_target_score_table,
    )
    summary_row = _proposal_summary_row(
        proposal_id=proposal_id,
        family_id=family_id,
        family_label=family_label,
        proposal_index=proposal_index,
        proposal_seed=proposal_seed,
        stage_status="stage_a_scored",
    )
    summary_row.update(
        {
            "deterministic_overall_distance": float(summary["overall_distance"]),
            "deterministic_historical_core_distance": float(summary["historical_core_distance"]),
            "deterministic_intrinsic_baseline_distance": float(summary["intrinsic_baseline_distance"]),
            "deterministic_full_ready_for_module3": bool(summary["full_ready_for_module3"]),
            "failure_reason": "",
        }
    )
    return summary_row, score_rows.to_dict(orient="records")


def _stage_b_worker(task: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    model_inputs = _load_inputs_cached(task["data_dir"])
    parameter_rows = pd.DataFrame(task["parameter_rows"])
    proposal_id = str(task["proposal_id"])
    family_id = str(task["family_id"])
    family_label = str(task["family_label"])
    proposal_index = int(task["proposal_index"])
    proposal_seed = int(task["proposal_seed"])
    replicate_seeds = [int(seed) for seed in task["replicate_seeds"]]
    stochastic_baselines = bool(task["stochastic_baselines"])

    try:
        params = build_resolved_parameters_from_sample(model_inputs, family_id, parameter_rows)
    except Exception as exc:
        return (
            _proposal_summary_row(
                proposal_id=proposal_id,
                family_id=family_id,
                family_label=family_label,
                proposal_index=proposal_index,
                proposal_seed=proposal_seed,
                stage_status="stage_b_failed",
                failure_reason=str(exc),
            ),
            [],
        )

    bundle_results: list[ScenarioBundleResult] = []
    target_frames: list[pd.DataFrame] = []
    try:
        for replicate_index, historical_seed in enumerate(replicate_seeds, start=1):
            baseline_seed = _derive_seed(proposal_seed, replicate_index, STAGE_B_BASELINE_CODE)
            bundle = _run_bundle_from_params(
                params,
                family_id,
                model_inputs,
                historical_stochastic=True,
                historical_seed=historical_seed,
                stochastic_baselines=stochastic_baselines,
                baseline_seed_base=baseline_seed,
            )
            bundle_results.append(bundle)
            target_frames.append(
                _bundle_target_records(
                    proposal_id=proposal_id,
                    family_id=family_id,
                    stage="stage_b",
                    replicate_index=replicate_index,
                    bundle_target_score_table=bundle.bundle_target_score_table,
                )
            )
        aggregate = aggregate_scenario_bundle_scores(bundle_results, ScoringConfig())
    except Exception as exc:
        return (
            _proposal_summary_row(
                proposal_id=proposal_id,
                family_id=family_id,
                family_label=family_label,
                proposal_index=proposal_index,
                proposal_seed=proposal_seed,
                stage_status="stage_b_failed",
                failure_reason=str(exc),
            ),
            [],
        )

    aggregate_values = [
        aggregate.summary["overall_distance_median"],
        aggregate.summary["historical_core_distance_median"],
        aggregate.summary["intrinsic_baseline_distance_median"],
        aggregate.summary["historical_core_distance_iqr"],
    ]
    if not all(value is not None and math.isfinite(float(value)) for value in aggregate_values):
        return (
            _proposal_summary_row(
                proposal_id=proposal_id,
                family_id=family_id,
                family_label=family_label,
                proposal_index=proposal_index,
                proposal_seed=proposal_seed,
                stage_status="stage_b_failed",
                failure_reason="Non-finite stochastic aggregate distance",
            ),
            pd.concat(target_frames, ignore_index=True).to_dict(orient="records") if target_frames else [],
        )

    summary_row = _proposal_summary_row(
        proposal_id=proposal_id,
        family_id=family_id,
        family_label=family_label,
        proposal_index=proposal_index,
        proposal_seed=proposal_seed,
        stage_status="stage_b_scored",
    )
    summary_row.update(
        {
            "stochastic_overall_distance_median": float(aggregate.summary["overall_distance_median"]),
            "stochastic_historical_core_distance_median": float(aggregate.summary["historical_core_distance_median"]),
            "stochastic_intrinsic_baseline_distance_median": float(aggregate.summary["intrinsic_baseline_distance_median"]),
            "stochastic_historical_core_distance_iqr": float(aggregate.summary["historical_core_distance_iqr"]),
            "stochastic_full_ready_for_module3": bool(aggregate.summary["full_ready_for_module3"]),
            "failure_reason": "",
        }
    )
    return summary_row, pd.concat(target_frames, ignore_index=True).to_dict(orient="records")


def _execute_tasks(
    tasks: list[dict[str, Any]],
    worker,
    workers: int,
    batch_size: int,
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    results: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    if not tasks:
        return results

    for start in range(0, len(tasks), batch_size):
        batch = tasks[start : start + batch_size]
        if workers == 1:
            results.extend(worker(task) for task in batch)
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                results.extend(executor.map(worker, batch))
    return results


def _prepare_parameter_table(
    model_inputs: ModelInputs,
    family_id: str,
    config: Module3Config,
) -> pd.DataFrame:
    family_index = _family_index(family_id)
    tables: list[pd.DataFrame] = []
    for proposal_index in range(1, config.stage_a_draws_per_family + 1):
        proposal_seed = _derive_seed(config.master_seed, family_index, proposal_index, STAGE_A_CODE)
        sampled = sample_family_parameter_table(
            model_inputs,
            family_id,
            np.random.default_rng(proposal_seed),
            1,
        )
        sampled["proposal_index"] = proposal_index
        sampled["proposal_id"] = _proposal_id(family_id, proposal_index)
        sampled["proposal_seed"] = proposal_seed
        tables.append(sampled)
    parameter_values = pd.concat(tables, ignore_index=True)
    return parameter_values


def _rank_stage_a_proposals(summary: pd.DataFrame, keep_n: int) -> tuple[pd.DataFrame, tuple[str, ...]]:
    updated = summary.copy()
    eligible = updated.loc[
        updated["stage_status"] == "stage_a_scored",
        [
            "proposal_id",
            "deterministic_overall_distance",
            "deterministic_historical_core_distance",
            "deterministic_intrinsic_baseline_distance",
        ],
    ].copy()
    if eligible.empty:
        return updated, ()

    eligible = eligible.sort_values(
        [
            "deterministic_overall_distance",
            "deterministic_historical_core_distance",
            "deterministic_intrinsic_baseline_distance",
            "proposal_id",
        ]
    ).reset_index(drop=True)
    eligible["stage_a_rank"] = np.arange(1, len(eligible) + 1)
    retained_ids = tuple(eligible.head(min(keep_n, len(eligible)))["proposal_id"].tolist())

    rank_lookup = dict(zip(eligible["proposal_id"], eligible["stage_a_rank"], strict=True))
    updated.loc[updated["proposal_id"].isin(rank_lookup), "stage_a_rank"] = (
        updated.loc[updated["proposal_id"].isin(rank_lookup), "proposal_id"].map(rank_lookup).astype(float)
    )
    updated.loc[updated["proposal_id"].isin(retained_ids), "stage_status"] = "stage_a_retained"
    updated.loc[
        updated["proposal_id"].isin(set(eligible["proposal_id"]) - set(retained_ids)),
        "stage_status",
    ] = "stage_a_rejected"
    return updated, retained_ids


def _rank_stage_b_proposals(summary: pd.DataFrame) -> pd.DataFrame:
    updated = summary.copy()
    eligible = updated.loc[
        updated["stage_status"] == "stage_b_scored",
        [
            "proposal_id",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
        ],
    ].copy()
    if eligible.empty:
        return updated

    eligible = eligible.sort_values(
        [
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
            "proposal_id",
        ]
    ).reset_index(drop=True)
    eligible["stage_b_rank"] = np.arange(1, len(eligible) + 1)
    rank_lookup = dict(zip(eligible["proposal_id"], eligible["stage_b_rank"], strict=True))
    updated.loc[updated["proposal_id"].isin(rank_lookup), "stage_b_rank"] = (
        updated.loc[updated["proposal_id"].isin(rank_lookup), "proposal_id"].map(rank_lookup).astype(float)
    )
    return updated


def _family_label(summary: pd.DataFrame, family_id: str) -> str:
    family_rows = summary.loc[summary["family_id"] == family_id, "family_label"]
    return str(family_rows.iloc[0]) if not family_rows.empty else family_id


def run_stage_a_screen(
    model_inputs: ModelInputs,
    family_id: str,
    config: Module3Config,
) -> FamilyCalibrationResult:
    parameter_values = _prepare_parameter_table(model_inputs, family_id, config)
    family_label = str(parameter_values["family_label"].iloc[0])
    summary_rows: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []

    for proposal_id, subset in parameter_values.groupby("proposal_id", sort=True):
        proposal_index = int(subset["proposal_index"].iloc[0])
        proposal_seed = int(subset["proposal_seed"].iloc[0])
        if bool(subset["proposal_sampling_failed"].any()):
            failure_reason = str(subset.loc[subset["failure_reason"] != "", "failure_reason"].iloc[0])
            summary_rows.append(
                _proposal_summary_row(
                    proposal_id=proposal_id,
                    family_id=family_id,
                    family_label=family_label,
                    proposal_index=proposal_index,
                    proposal_seed=proposal_seed,
                    stage_status="sampling_failure",
                    failure_reason=failure_reason,
                )
            )
            continue

        tasks.append(
            {
                "data_dir": str(model_inputs.data_dir),
                "proposal_id": proposal_id,
                "family_id": family_id,
                "family_label": family_label,
                "proposal_index": proposal_index,
                "proposal_seed": proposal_seed,
                "parameter_rows": subset.to_dict(orient="records"),
            }
        )

    task_results = _execute_tasks(tasks, _stage_a_worker, workers=config.workers, batch_size=config.batch_size)
    target_frames: list[pd.DataFrame] = []
    for summary_row, target_rows in task_results:
        summary_rows.append(summary_row)
        if target_rows:
            target_frames.append(pd.DataFrame(target_rows))

    proposal_summary = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS).sort_values("proposal_id").reset_index(drop=True)
    proposal_summary, retained_ids = _rank_stage_a_proposals(proposal_summary, config.stage_a_keep_per_family)

    parameter_values = parameter_values.assign(
        family_id=family_id,
        parameter_status=parameter_values["parameter_status"],
    )
    parameter_values = parameter_values[
        [
            "proposal_id",
            "family_id",
            "parameter_id",
            "parameter_status",
            "value_natural",
            "value_sampling",
            "sampled_flag",
        ]
    ].copy()

    target_scores = (
        pd.concat(target_frames, ignore_index=True)[TARGET_SCORE_COLUMNS].copy()
        if target_frames
        else _empty_target_frame()
    )
    return FamilyCalibrationResult(
        family_id=family_id,
        proposal_summary_table=proposal_summary,
        parameter_values_table=parameter_values,
        target_scores_table=target_scores,
        retained_proposal_ids=retained_ids,
        accepted_proposal_ids=(),
    )


def run_stage_b_confirmation(
    stage_a_result: FamilyCalibrationResult,
    model_inputs: ModelInputs,
    config: Module3Config,
) -> FamilyCalibrationResult:
    family_id = stage_a_result.family_id
    family_label = _family_label(stage_a_result.proposal_summary_table, family_id)
    proposal_summary = stage_a_result.proposal_summary_table.copy()
    parameter_values = stage_a_result.parameter_values_table.copy()
    target_scores = stage_a_result.target_scores_table.copy()

    tasks: list[dict[str, Any]] = []
    for proposal_id in stage_a_result.retained_proposal_ids:
        summary_row = proposal_summary.loc[proposal_summary["proposal_id"] == proposal_id].iloc[0]
        proposal_index = int(summary_row["proposal_index"])
        proposal_seed = int(summary_row["proposal_seed"])
        replicate_seeds = [
            _derive_seed(config.master_seed, _family_index(family_id), proposal_index, replicate_index, STAGE_B_CODE)
            for replicate_index in range(1, config.stage_b_historical_replicates + 1)
        ]
        parameter_rows = parameter_values.loc[parameter_values["proposal_id"] == proposal_id].copy()
        tasks.append(
            {
                "data_dir": str(model_inputs.data_dir),
                "proposal_id": proposal_id,
                "family_id": family_id,
                "family_label": family_label,
                "proposal_index": proposal_index,
                "proposal_seed": proposal_seed,
                "replicate_seeds": replicate_seeds,
                "stochastic_baselines": config.stochastic_baselines,
                "parameter_rows": parameter_rows.to_dict(orient="records"),
            }
        )

    task_results = _execute_tasks(tasks, _stage_b_worker, workers=config.workers, batch_size=config.batch_size)
    stage_b_rows: list[dict[str, Any]] = []
    target_frames: list[pd.DataFrame] = []
    for summary_row, target_rows in task_results:
        stage_b_rows.append(summary_row)
        if target_rows:
            target_frames.append(pd.DataFrame(target_rows))

    stage_b_summary = pd.DataFrame(stage_b_rows)
    if not stage_b_summary.empty:
        proposal_summary = proposal_summary.merge(
            stage_b_summary[
                [
                    "proposal_id",
                    "stage_status",
                    "stochastic_overall_distance_median",
                    "stochastic_historical_core_distance_median",
                    "stochastic_intrinsic_baseline_distance_median",
                    "stochastic_historical_core_distance_iqr",
                    "stochastic_full_ready_for_module3",
                    "failure_reason",
                ]
            ],
            on="proposal_id",
            how="left",
            suffixes=("", "_stage_b"),
        )
        for column in [
            "stage_status",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
            "stochastic_full_ready_for_module3",
            "failure_reason",
        ]:
            stage_column = f"{column}_stage_b"
            proposal_summary[column] = proposal_summary[stage_column].combine_first(proposal_summary[column])
            proposal_summary = proposal_summary.drop(columns=[stage_column])

    proposal_summary = _rank_stage_b_proposals(proposal_summary)
    if target_frames:
        target_scores = pd.concat([target_scores, *target_frames], ignore_index=True)[TARGET_SCORE_COLUMNS].copy()

    return FamilyCalibrationResult(
        family_id=family_id,
        proposal_summary_table=proposal_summary.sort_values("proposal_id").reset_index(drop=True),
        parameter_values_table=parameter_values.sort_values(["proposal_id", "parameter_id"]).reset_index(drop=True),
        target_scores_table=target_scores.sort_values(["proposal_id", "stage", "replicate_index", "target_id"]).reset_index(drop=True),
        retained_proposal_ids=stage_a_result.retained_proposal_ids,
        accepted_proposal_ids=(),
    )


def _combine_family_results(family_results: dict[str, FamilyCalibrationResult]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = pd.concat(
        [result.proposal_summary_table for result in family_results.values()],
        ignore_index=True,
    ) if family_results else _empty_summary_frame()
    parameters = pd.concat(
        [result.parameter_values_table for result in family_results.values()],
        ignore_index=True,
    ) if family_results else _empty_parameter_frame()
    targets = pd.concat(
        [result.target_scores_table for result in family_results.values()],
        ignore_index=True,
    ) if family_results else _empty_target_frame()
    if not summary.empty:
        summary = summary[SUMMARY_COLUMNS].sort_values(["family_id", "proposal_index"]).reset_index(drop=True)
    if not parameters.empty:
        parameters = parameters[PARAMETER_COLUMNS].sort_values(["family_id", "proposal_id", "parameter_id"]).reset_index(drop=True)
    if not targets.empty:
        targets = targets[TARGET_SCORE_COLUMNS].sort_values(
            ["family_id", "proposal_id", "stage", "replicate_index", "target_id"]
        ).reset_index(drop=True)
    return summary, parameters, targets


def _apply_global_acceptance(proposal_summary: pd.DataFrame, config: Module3Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    updated = proposal_summary.copy()
    valid_stage_b = updated.loc[
        (updated["stage_status"] == "stage_b_scored")
        & updated["stochastic_full_ready_for_module3"].astype(bool)
        & np.isfinite(updated["stochastic_overall_distance_median"].astype(float)),
        [
            "proposal_id",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
        ],
    ].copy()
    if valid_stage_b.empty:
        return updated, updated.loc[updated["accepted_final"]].copy()

    valid_stage_b = valid_stage_b.sort_values(
        [
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
            "proposal_id",
        ]
    ).reset_index(drop=True)
    accept_n = min(
        int(config.final_acceptance_cap),
        int(math.ceil(config.final_acceptance_fraction * len(valid_stage_b))),
    )
    accepted_ids = set(valid_stage_b.head(accept_n)["proposal_id"].tolist())

    updated["accepted_final"] = updated["proposal_id"].isin(accepted_ids)
    updated.loc[(updated["stage_status"] == "stage_b_scored") & (~updated["accepted_final"]), "stage_status"] = "stage_b_rejected"
    updated.loc[updated["accepted_final"], "stage_status"] = "accepted"
    accepted = updated.loc[updated["accepted_final"]].copy().sort_values(
        [
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
            "proposal_id",
        ]
    ).reset_index(drop=True)
    return updated, accepted


def _build_family_summary(proposal_summary: pd.DataFrame, families: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family_id in families:
        subset = proposal_summary.loc[proposal_summary["family_id"] == family_id].copy()
        if subset.empty:
            continue
        stage_a_valid = subset["stage_status"].isin(SCORED_STAGE_A_STATUSES).sum()
        stage_a_retained = subset["stage_status"].isin({"stage_a_retained", "stage_b_failed", "stage_b_rejected", "accepted"}).sum()
        stage_b_evaluated = subset["stage_status"].isin({"stage_b_failed", "stage_b_rejected", "accepted"}).sum()
        stage_b_valid = subset["stage_status"].isin(STAGE_B_VALID_STATUSES).sum()
        final_accepted = subset["accepted_final"].sum()
        rows.append(
            {
                "family_id": family_id,
                "family_label": str(subset["family_label"].iloc[0]),
                "stage_a_draws": int(len(subset)),
                "stage_a_valid_scored": int(stage_a_valid),
                "stage_a_valid_rate": float(stage_a_valid / len(subset)),
                "stage_a_retained": int(stage_a_retained),
                "stage_b_evaluated": int(stage_b_evaluated),
                "stage_b_valid": int(stage_b_valid),
                "final_accepted": int(final_accepted),
                "final_acceptance_rate": float(final_accepted / len(subset)),
                "median_deterministic_distance_retained": (
                    float(subset.loc[subset["stage_status"].isin({"stage_a_retained", "stage_b_failed", "stage_b_rejected", "accepted"}), "deterministic_overall_distance"].median())
                    if stage_a_retained > 0
                    else float("nan")
                ),
                "median_stochastic_distance_valid": (
                    float(subset.loc[subset["stage_status"].isin(STAGE_B_VALID_STATUSES), "stochastic_overall_distance_median"].median())
                    if stage_b_valid > 0
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("family_id").reset_index(drop=True) if rows else pd.DataFrame(
        columns=[
            "family_id",
            "family_label",
            "stage_a_draws",
            "stage_a_valid_scored",
            "stage_a_valid_rate",
            "stage_a_retained",
            "stage_b_evaluated",
            "stage_b_valid",
            "final_accepted",
            "final_acceptance_rate",
            "median_deterministic_distance_retained",
            "median_stochastic_distance_valid",
        ]
    )


def _write_run_outputs(run_result: CalibrationRunResult) -> None:
    output_dir = _normalize_output_dir(run_result.config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run_manifest.json").write_text(
        json.dumps(run_result.run_manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    run_result.proposal_summary_table.to_csv(output_dir / "proposal_summary.csv.gz", index=False)
    run_result.parameter_values_table.to_csv(output_dir / "parameter_values.csv.gz", index=False)
    run_result.target_scores_table.to_csv(output_dir / "target_scores.csv.gz", index=False)
    run_result.family_summary_table.to_csv(output_dir / "family_summary.csv", index=False)
    run_result.accepted_proposals_table.to_csv(output_dir / "accepted_proposals.csv", index=False)


def _load_existing_outputs(output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any] | None]:
    manifest_path = output_dir / "run_manifest.json"
    proposal_path = output_dir / "proposal_summary.csv.gz"
    parameter_path = output_dir / "parameter_values.csv.gz"
    target_path = output_dir / "target_scores.csv.gz"
    family_path = output_dir / "family_summary.csv"
    accepted_path = output_dir / "accepted_proposals.csv"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    proposals = pd.read_csv(proposal_path) if proposal_path.exists() else _empty_summary_frame()
    parameters = pd.read_csv(parameter_path) if parameter_path.exists() else _empty_parameter_frame()
    targets = pd.read_csv(target_path) if target_path.exists() else _empty_target_frame()
    family_summary = pd.read_csv(family_path) if family_path.exists() else pd.DataFrame()
    accepted = pd.read_csv(accepted_path) if accepted_path.exists() else pd.DataFrame()
    return proposals, parameters, targets, family_summary, accepted, manifest


def _manifest_matches(existing_manifest: dict[str, Any] | None, expected_manifest: dict[str, Any]) -> bool:
    if existing_manifest is None:
        return False
    existing_config = dict(existing_manifest.get("config", {}))
    expected_config = dict(expected_manifest.get("config", {}))
    existing_config.pop("resume", None)
    expected_config.pop("resume", None)
    return existing_config == expected_config


def _family_stage_a_complete(existing_summary: pd.DataFrame, family_id: str, config: Module3Config) -> bool:
    expected_ids = {_proposal_id(family_id, index) for index in range(1, config.stage_a_draws_per_family + 1)}
    present_ids = set(existing_summary.loc[existing_summary["family_id"] == family_id, "proposal_id"].astype(str))
    return expected_ids.issubset(present_ids)


def _family_stage_b_complete(existing_summary: pd.DataFrame, family_id: str) -> bool:
    family_rows = existing_summary.loc[existing_summary["family_id"] == family_id].copy()
    if family_rows.empty:
        return False
    retained_rows = family_rows.loc[family_rows["stage_status"].isin({"stage_a_retained", *FINAL_STAGE_B_STATUSES})]
    if retained_rows.empty:
        return True
    return bool(retained_rows["stage_status"].isin(FINAL_STAGE_B_STATUSES).all())


def _rebuild_family_result(
    family_id: str,
    proposal_summary: pd.DataFrame,
    parameter_values: pd.DataFrame,
    target_scores: pd.DataFrame,
) -> FamilyCalibrationResult:
    family_summary = proposal_summary.loc[proposal_summary["family_id"] == family_id].copy()
    family_parameters = parameter_values.loc[parameter_values["family_id"] == family_id].copy()
    family_targets = target_scores.loc[target_scores["family_id"] == family_id].copy()
    retained = tuple(
        family_summary.loc[
            family_summary["stage_status"].isin({"stage_a_retained", *FINAL_STAGE_B_STATUSES}),
            "proposal_id",
        ].astype(str).tolist()
    )
    accepted = tuple(
        family_summary.loc[family_summary["accepted_final"].astype(bool), "proposal_id"].astype(str).tolist()
    )
    return FamilyCalibrationResult(
        family_id=family_id,
        proposal_summary_table=family_summary.sort_values("proposal_id").reset_index(drop=True),
        parameter_values_table=family_parameters.sort_values(["proposal_id", "parameter_id"]).reset_index(drop=True),
        target_scores_table=family_targets.sort_values(["proposal_id", "stage", "replicate_index", "target_id"]).reset_index(drop=True),
        retained_proposal_ids=retained,
        accepted_proposal_ids=accepted,
    )


def _run_module3_with_stage(
    model_inputs: ModelInputs,
    config: Module3Config,
    stage: str,
) -> CalibrationRunResult:
    _validate_module3_config(config)
    if stage not in {"all", "stage_a", "stage_b"}:
        raise ValueError(f"Unsupported stage: {stage}")

    output_dir = _normalize_output_dir(config.output_dir)
    manifest = _build_manifest(model_inputs, config)
    families = _selected_families(config)

    existing_summary = _empty_summary_frame()
    existing_parameters = _empty_parameter_frame()
    existing_targets = _empty_target_frame()
    if config.resume and output_dir.exists():
        loaded_summary, loaded_parameters, loaded_targets, _, _, loaded_manifest = _load_existing_outputs(output_dir)
        if _manifest_matches(loaded_manifest, manifest):
            existing_summary = loaded_summary
            existing_parameters = loaded_parameters
            existing_targets = loaded_targets

    family_results: dict[str, FamilyCalibrationResult] = {}
    for family_id in families:
        rerun_stage_a = not _family_stage_a_complete(existing_summary, family_id, config)
        if not rerun_stage_a:
            family_result = _rebuild_family_result(family_id, existing_summary, existing_parameters, existing_targets)
        else:
            family_result = run_stage_a_screen(model_inputs, family_id, config)

        if stage in {"all", "stage_b"}:
            rerun_stage_b = rerun_stage_a or (not _family_stage_b_complete(existing_summary, family_id))
            if rerun_stage_b:
                family_result = run_stage_b_confirmation(family_result, model_inputs, config)
            elif not rerun_stage_a:
                family_result = _rebuild_family_result(family_id, existing_summary, existing_parameters, existing_targets)

        family_results[family_id] = family_result

    proposal_summary, parameter_values, target_scores = _combine_family_results(family_results)
    accepted = pd.DataFrame(columns=SUMMARY_COLUMNS)
    if stage == "all":
        proposal_summary, accepted = _apply_global_acceptance(proposal_summary, config)
    family_summary = _build_family_summary(proposal_summary, families)

    refreshed_family_results: dict[str, FamilyCalibrationResult] = {}
    for family_id in families:
        refreshed_family_results[family_id] = _rebuild_family_result(family_id, proposal_summary, parameter_values, target_scores)

    accepted = proposal_summary.loc[proposal_summary["accepted_final"].astype(bool)].copy().sort_values(
        [
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
            "proposal_id",
        ]
    ).reset_index(drop=True)
    run_result = CalibrationRunResult(
        config=config,
        proposal_summary_table=proposal_summary,
        parameter_values_table=parameter_values,
        target_scores_table=target_scores,
        family_summary_table=family_summary,
        accepted_proposals_table=accepted,
        run_manifest=manifest,
        family_results=refreshed_family_results,
    )
    _write_run_outputs(run_result)
    return run_result


def run_module3_calibration(
    model_inputs: ModelInputs,
    config: Module3Config,
) -> CalibrationRunResult:
    return _run_module3_with_stage(model_inputs, config, stage="all")


def run_module3_calibration_stage(
    model_inputs: ModelInputs,
    config: Module3Config,
    stage: str,
) -> CalibrationRunResult:
    return _run_module3_with_stage(model_inputs, config, stage=stage)
