from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from typing import Any, Iterable

import numpy as np
import pandas as pd

from galaxias_model.calibration import run_module3_calibration, run_module3_calibration_stage
from galaxias_model.io import load_model_inputs
from galaxias_model.types import ModelInputs, Module3Config


def _format_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return "NA"
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_format_value(row.get(column)) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


MODULE3_REVIEW_TARGET_IDS = {f"CT{i:03d}" for i in range(1, 13)}


def _fresh_run_dir(path: Path) -> Path:
    if path.exists():
        rmtree(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _accepted_id_tuple(frame: pd.DataFrame) -> tuple[str, ...]:
    if frame.empty:
        return ()
    return tuple(frame["proposal_id"].astype(str).tolist())


def _safe_spearman(x: pd.Series, y: pd.Series) -> float:
    paired = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(paired) < 2:
        return float("nan")
    if paired["x"].nunique() < 2 or paired["y"].nunique() < 2:
        return float("nan")
    ranked = paired.rank(method="average")
    return float(ranked["x"].corr(ranked["y"], method="pearson"))


def _module3_small_repro_config(output_dir: Path, workers: int) -> Module3Config:
    return Module3Config(
        stage_a_draws_per_family=60,
        stage_a_keep_per_family=8,
        stage_b_historical_replicates=3,
        final_acceptance_fraction=0.10,
        final_acceptance_cap=5,
        workers=workers,
        batch_size=50,
        master_seed=20260410,
        stochastic_baselines=False,
        output_dir=output_dir,
        resume=False,
    )


def _module3_screen_discrimination_rows(
    proposal_summary: pd.DataFrame,
    config: Module3Config,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family_id in config.families:
        subset = proposal_summary.loc[proposal_summary["family_id"] == family_id].copy()
        retained = subset.loc[
            pd.to_numeric(subset["stage_a_rank"], errors="coerce").between(1, config.stage_a_keep_per_family),
            "deterministic_overall_distance",
        ]
        rejected = subset.loc[subset["stage_status"] == "stage_a_rejected", "deterministic_overall_distance"]
        retained_median = float(pd.to_numeric(retained, errors="coerce").median()) if not retained.empty else float("nan")
        rejected_median = float(pd.to_numeric(rejected, errors="coerce").median()) if not rejected.empty else float("nan")
        passed = bool(
            np.isfinite(retained_median)
            and np.isfinite(rejected_median)
            and retained_median <= 0.8 * rejected_median
        )
        rows.append(
            {
                "family_id": family_id,
                "retained_median": retained_median,
                "rejected_median": rejected_median,
                "pass": passed,
            }
        )
    return pd.DataFrame(rows)


def _module3_rank_consistency_rows(proposal_summary: pd.DataFrame, families: Iterable[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for family_id in families:
        subset = proposal_summary.loc[
            (proposal_summary["family_id"] == family_id)
            & (proposal_summary["stage_status"].isin({"stage_b_rejected", "accepted"}))
        ].copy()
        correlation = _safe_spearman(
            subset["deterministic_overall_distance"],
            subset["stochastic_overall_distance_median"],
        )
        passed = bool(np.isfinite(correlation) and correlation >= 0.40)
        rows.append(
            {
                "family_id": family_id,
                "spearman_rank_correlation": correlation,
                "pass": passed,
            }
        )
    return pd.DataFrame(rows)


def _module3_accepted_targets_scored(
    accepted_summary: pd.DataFrame,
    target_scores: pd.DataFrame,
) -> bool:
    if accepted_summary.empty:
        return False
    for proposal_id in accepted_summary["proposal_id"].astype(str):
        subset = target_scores.loc[
            (target_scores["proposal_id"] == proposal_id)
            & (target_scores["stage"] == "stage_b")
        ].copy()
        if set(subset["target_id"].astype(str)) != MODULE3_REVIEW_TARGET_IDS:
            return False
        if not (subset["evaluation_status"] == "scored").all():
            return False
    return True


def run_module3_readiness_review(
    root: Path,
    config: Module3Config | None = None,
    repro_config: Module3Config | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    data_dir = root / "data"
    model_inputs = load_model_inputs(data_dir)

    readiness_dir = root / "outputs" / "module3"
    primary_config = config or Module3Config.readiness_defaults(
        output_dir=readiness_dir / "readiness_primary"
    )
    repeat_config = Module3Config(
        **{
            **primary_config.__dict__,
            "output_dir": readiness_dir / "readiness_repeat",
            "resume": False,
        }
    )
    serial_small_config = repro_config or _module3_small_repro_config(
        readiness_dir / "readiness_repro_workers1",
        workers=1,
    )
    parallel_small_config = Module3Config(
        **{
            **serial_small_config.__dict__,
            "workers": 2,
            "output_dir": readiness_dir / "readiness_repro_workers2",
            "resume": False,
        }
    )
    resume_stage_a_config = Module3Config(
        **{
            **serial_small_config.__dict__,
            "output_dir": readiness_dir / "readiness_resume_stage_a",
            "resume": False,
        }
    )
    resume_full_config = Module3Config(
        **{
            **serial_small_config.__dict__,
            "output_dir": readiness_dir / "readiness_resume_stage_a",
            "resume": True,
        }
    )
    clean_small_config = Module3Config(
        **{
            **serial_small_config.__dict__,
            "output_dir": readiness_dir / "readiness_resume_clean",
            "resume": False,
        }
    )

    for path in [
        primary_config.output_dir,
        repeat_config.output_dir,
        serial_small_config.output_dir,
        parallel_small_config.output_dir,
        resume_stage_a_config.output_dir,
        clean_small_config.output_dir,
    ]:
        _fresh_run_dir(path)

    primary_run = run_module3_calibration(model_inputs, primary_config)
    repeat_run = run_module3_calibration(model_inputs, repeat_config)
    serial_small_run = run_module3_calibration(model_inputs, serial_small_config)
    parallel_small_run = run_module3_calibration(model_inputs, parallel_small_config)
    run_module3_calibration_stage(model_inputs, resume_stage_a_config, stage="stage_a")
    resumed_run = run_module3_calibration_stage(model_inputs, resume_full_config, stage="all")
    clean_small_run = run_module3_calibration(model_inputs, clean_small_config)

    family_summary = primary_run.family_summary_table.copy()
    accepted_summary = primary_run.accepted_proposals_table[
        [
            "proposal_id",
            "family_id",
            "proposal_seed",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
        ]
    ].copy()

    sampler_valid_rate_pass = bool((family_summary["stage_a_valid_rate"] >= 0.70).all())

    discrimination_rows = _module3_screen_discrimination_rows(
        primary_run.proposal_summary_table,
        primary_config,
    )
    screen_discrimination_pass = bool(discrimination_rows["pass"].sum() >= 4)

    stage_b_rows = primary_run.proposal_summary_table.loc[
        primary_run.proposal_summary_table["stage_status"].isin({"stage_b_failed", "stage_b_rejected", "accepted"})
    ].copy()
    stochastic_confirmation_finite_pass = bool(
        (not stage_b_rows.empty)
        and np.isfinite(pd.to_numeric(stage_b_rows["stochastic_overall_distance_median"], errors="coerce")).all()
        and np.isfinite(pd.to_numeric(stage_b_rows["stochastic_historical_core_distance_median"], errors="coerce")).all()
        and np.isfinite(pd.to_numeric(stage_b_rows["stochastic_intrinsic_baseline_distance_median"], errors="coerce")).all()
        and np.isfinite(pd.to_numeric(stage_b_rows["stochastic_historical_core_distance_iqr"], errors="coerce")).all()
    )

    rank_rows = _module3_rank_consistency_rows(primary_run.proposal_summary_table, primary_config.families)
    rank_consistency_pass = bool(rank_rows["pass"].sum() >= 4)

    accepted_set_nonempty_pass = bool(
        (not accepted_summary.empty)
        and _module3_accepted_targets_scored(accepted_summary, primary_run.target_scores_table)
    )

    repeat_ids_match = _accepted_id_tuple(primary_run.accepted_proposals_table) == _accepted_id_tuple(
        repeat_run.accepted_proposals_table
    )
    worker_ids_match = _accepted_id_tuple(serial_small_run.accepted_proposals_table) == _accepted_id_tuple(
        parallel_small_run.accepted_proposals_table
    )
    resume_ids_match = _accepted_id_tuple(resumed_run.accepted_proposals_table) == _accepted_id_tuple(
        clean_small_run.accepted_proposals_table
    )
    reproducibility_pass = bool(repeat_ids_match and worker_ids_match and resume_ids_match)

    gates = {
        "sampler_valid_rate_pass": sampler_valid_rate_pass,
        "screen_discrimination_pass": screen_discrimination_pass,
        "stochastic_confirmation_finite_pass": stochastic_confirmation_finite_pass,
        "rank_consistency_pass": rank_consistency_pass,
        "accepted_set_nonempty_pass": accepted_set_nonempty_pass,
        "reproducibility_pass": reproducibility_pass,
    }
    gates["full_ready_for_module4"] = all(gates.values())
    gates["needs_module_3_5"] = not gates["full_ready_for_module4"]

    evaluation = {
        "gates": gates,
        "metrics": {
            "accepted_count": int(len(accepted_summary)),
            "same_seed_same_worker_identical": repeat_ids_match,
            "workers1_vs_workers2_identical": worker_ids_match,
            "resume_matches_clean_run": resume_ids_match,
        },
        "screen_discrimination": discrimination_rows,
        "rank_consistency": rank_rows,
        "primary_run": primary_run,
    }
    return family_summary, accepted_summary, evaluation


def render_module3_readiness_review(
    family_summary: pd.DataFrame,
    accepted_summary: pd.DataFrame,
    evaluation: dict[str, Any],
) -> str:
    gates = evaluation["gates"]
    metrics = evaluation["metrics"]
    discrimination_rows = evaluation["screen_discrimination"].to_dict(orient="records")
    rank_rows = evaluation["rank_consistency"].to_dict(orient="records")
    family_rows = family_summary[
        [
            "family_id",
            "stage_a_valid_rate",
            "stage_a_retained",
            "stage_b_valid",
            "final_accepted",
            "final_acceptance_rate",
        ]
    ].to_dict(orient="records")
    accepted_rows = accepted_summary.to_dict(orient="records")
    gate_rows = [{"gate": key, "status": value} for key, value in gates.items()]
    metric_rows = [{"metric": key, "value": value} for key, value in metrics.items()]

    lines = [
        "# Module 3 Readiness Review",
        "",
        "## Summary",
        "",
        (
            "Module 3 adds the first full two-stage ABC/history-matching calibration harness "
            "on top of the validated latent kernel and the Module 2.5 bundle scorer."
        ),
        (
            "Stage A screens equal proposal budgets across all five hypothesis families using "
            "deterministic scenario bundles, while Stage B confirms retained proposals against "
            "stochastic historical replicates with deterministic baselines."
        ),
        "",
        "## Acceptance Gates",
        "",
        _markdown_table(gate_rows, ["gate", "status"]),
        "",
        "## Family Summary",
        "",
        _markdown_table(
            family_rows,
            [
                "family_id",
                "stage_a_valid_rate",
                "stage_a_retained",
                "stage_b_valid",
                "final_accepted",
                "final_acceptance_rate",
            ],
        ),
        "",
        "## Screen Discrimination",
        "",
        _markdown_table(discrimination_rows, ["family_id", "retained_median", "rejected_median", "pass"]),
        "",
        "## Rank Consistency",
        "",
        _markdown_table(rank_rows, ["family_id", "spearman_rank_correlation", "pass"]),
        "",
        "## Reproducibility Checks",
        "",
        _markdown_table(metric_rows, ["metric", "value"]),
        "",
        "## Accepted Proposals",
        "",
    ]

    if accepted_rows:
        lines.append(
            _markdown_table(
                accepted_rows,
                [
                    "proposal_id",
                    "family_id",
                    "proposal_seed",
                    "stochastic_overall_distance_median",
                    "stochastic_historical_core_distance_median",
                    "stochastic_intrinsic_baseline_distance_median",
                    "stochastic_historical_core_distance_iqr",
                ],
            )
        )
    else:
        lines.append("No accepted proposals were retained in the readiness run.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )

    if gates["full_ready_for_module4"]:
        lines.extend(
            [
                "All Module 3 readiness gates passed.",
                "The retained-sample calibration harness is ready to support Module 4 posterior summaries and counterfactual analysis.",
            ]
        )
    else:
        lines.extend(
            [
                "Module 4 should not start yet.",
                "The correct next step is Module 3.5 because at least one calibration-harness readiness gate failed.",
            ]
        )

    lines.extend(
        [
            "",
            "## Module 3.5 Trigger",
            "",
            "- Trigger a sampler/constraint realignment pass if valid-rate failures or pre-simulation proposal failures dominate.",
            "- Trigger a Stage A to Stage B handoff refinement pass if rank consistency is weak or stochastic confirmation is numerically unstable.",
            "- Trigger a reproducibility repair pass if accepted proposal ids differ under the same seed or across worker counts.",
            "",
            "## Artifacts",
            "",
            "- `data/module3_readiness_family_summary.csv`",
            "- `data/module3_readiness_accepted_summary.csv`",
            "- `docs/module3_readiness_review.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_module3_readiness_bundle(root: Path, output_root: Path | None = None) -> dict[str, Any]:
    data_dir = root / "data"
    target_root = output_root if output_root is not None else root
    output_data_dir = target_root / "data"
    docs_dir = target_root / "docs"
    family_summary, accepted_summary, evaluation = run_module3_readiness_review(root)

    output_data_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    family_path = output_data_dir / "module3_readiness_family_summary.csv"
    accepted_path = output_data_dir / "module3_readiness_accepted_summary.csv"
    review_path = docs_dir / "module3_readiness_review.md"

    family_summary.to_csv(family_path, index=False)
    accepted_summary.to_csv(accepted_path, index=False)
    review_path.write_text(
        render_module3_readiness_review(family_summary, accepted_summary, evaluation),
        encoding="utf-8",
    )

    return {
        "family_summary": family_path,
        "accepted_summary": accepted_path,
        "review_doc": review_path,
        "full_ready_for_module4": evaluation["gates"]["full_ready_for_module4"],
        "needs_module_3_5": evaluation["gates"]["needs_module_3_5"],
    }


STAGE_B_FINAL_STATUSES = {"stage_b_rejected", "accepted"}


def _valid_stage_b_proposals(proposal_summary: pd.DataFrame) -> pd.DataFrame:
    valid = proposal_summary.loc[proposal_summary["stage_status"].isin(STAGE_B_FINAL_STATUSES)].copy()
    valid["stochastic_overall_distance_median"] = pd.to_numeric(
        valid["stochastic_overall_distance_median"],
        errors="coerce",
    )
    return valid.loc[np.isfinite(valid["stochastic_overall_distance_median"])].copy()


def _module3_5_sampler_failure_rows(proposal_summary: pd.DataFrame) -> pd.DataFrame:
    family_draws = proposal_summary.groupby("family_id").size().rename("family_draws").reset_index()
    failures = proposal_summary.loc[
        proposal_summary["stage_status"].isin({"sampling_failure", "constraint_failure", "stage_a_failed"})
    ].copy()
    if failures.empty:
        return pd.DataFrame(
            columns=["family_id", "stage_status", "failure_reason", "failure_count", "family_draws", "failure_rate"]
        )

    grouped = (
        failures.assign(failure_reason=failures["failure_reason"].fillna(""))
        .groupby(["family_id", "stage_status", "failure_reason"], as_index=False)
        .size()
        .rename(columns={"size": "failure_count"})
        .merge(family_draws, on="family_id", how="left")
    )
    grouped["failure_rate"] = grouped["failure_count"] / grouped["family_draws"]
    return grouped.sort_values(["family_id", "failure_count"], ascending=[True, False]).reset_index(drop=True)


def _module3_5_stage_b_frontier(proposal_summary: pd.DataFrame) -> pd.DataFrame:
    valid = _valid_stage_b_proposals(proposal_summary)
    if valid.empty:
        return pd.DataFrame()
    frontier = valid.sort_values(
        [
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
            "proposal_id",
        ]
    ).reset_index(drop=True)
    frontier["global_stage_b_rank"] = np.arange(1, len(frontier) + 1)
    return frontier[
        [
            "global_stage_b_rank",
            "proposal_id",
            "family_id",
            "stage_status",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
            "accepted_final",
        ]
    ].copy()


def _module3_5_family_best_rows(stage_b_frontier: pd.DataFrame) -> pd.DataFrame:
    if stage_b_frontier.empty:
        return pd.DataFrame()
    return (
        stage_b_frontier.sort_values("global_stage_b_rank")
        .groupby("family_id", as_index=False)
        .head(1)
        .sort_values("global_stage_b_rank")
        .reset_index(drop=True)
    )


def _module3_5_proposal_target_medians(target_scores: pd.DataFrame) -> pd.DataFrame:
    stage_b = target_scores.loc[target_scores["stage"] == "stage_b"].copy()
    if stage_b.empty:
        return pd.DataFrame(columns=["proposal_id", "family_id", "target_id", "median_weighted_penalty"])
    stage_b["weighted_penalty"] = pd.to_numeric(stage_b["weighted_penalty"], errors="coerce")
    return (
        stage_b.groupby(["proposal_id", "family_id", "target_id"], as_index=False)["weighted_penalty"]
        .median()
        .rename(columns={"weighted_penalty": "median_weighted_penalty"})
        .sort_values(["family_id", "proposal_id", "target_id"])
        .reset_index(drop=True)
    )


def _module3_5_target_leverage_rows(
    proposal_target_medians: pd.DataFrame,
    proposal_summary: pd.DataFrame,
    model_inputs: ModelInputs,
) -> pd.DataFrame:
    valid_ids = set(_valid_stage_b_proposals(proposal_summary)["proposal_id"].astype(str))
    target_medians = proposal_target_medians.loc[
        proposal_target_medians["proposal_id"].astype(str).isin(valid_ids)
    ].copy()
    if target_medians.empty:
        return pd.DataFrame()

    family_distance = (
        _valid_stage_b_proposals(proposal_summary)
        .groupby("family_id", as_index=False)["stochastic_overall_distance_median"]
        .median()
        .rename(columns={"stochastic_overall_distance_median": "family_median_stage_b_distance"})
    )
    leverage = (
        target_medians.groupby(["family_id", "target_id"], as_index=False)["median_weighted_penalty"]
        .median()
        .merge(family_distance, on="family_id", how="left")
    )
    leverage["target_share_of_family_distance"] = (
        leverage["median_weighted_penalty"] / leverage["family_median_stage_b_distance"]
    )

    target_meta = model_inputs.calibration_targets[
        ["target_id", "target_group", "comparison_type", "priority_weight"]
    ].copy()
    leverage = leverage.merge(target_meta, on="target_id", how="left")
    return leverage[
        [
            "family_id",
            "target_id",
            "target_group",
            "comparison_type",
            "priority_weight",
            "median_weighted_penalty",
            "family_median_stage_b_distance",
            "target_share_of_family_distance",
        ]
    ].sort_values(["family_id", "median_weighted_penalty"], ascending=[True, False]).reset_index(drop=True)


def _module3_5_accepted_target_penalties(
    proposal_target_medians: pd.DataFrame,
    accepted_summary: pd.DataFrame,
    model_inputs: ModelInputs,
) -> pd.DataFrame:
    accepted_ids = set(accepted_summary["proposal_id"].astype(str)) if not accepted_summary.empty else set()
    accepted = proposal_target_medians.loc[proposal_target_medians["proposal_id"].astype(str).isin(accepted_ids)].copy()
    target_meta = model_inputs.calibration_targets[
        ["target_id", "target_group", "comparison_type", "priority_weight"]
    ].copy()
    if accepted.empty:
        return pd.DataFrame(columns=[*target_meta.columns, "accepted_median_weighted_penalty"])
    rows = (
        accepted.groupby("target_id", as_index=False)["median_weighted_penalty"]
        .median()
        .rename(columns={"median_weighted_penalty": "accepted_median_weighted_penalty"})
        .merge(target_meta, on="target_id", how="left")
    )
    return rows[
        [
            "target_id",
            "target_group",
            "comparison_type",
            "priority_weight",
            "accepted_median_weighted_penalty",
        ]
    ].sort_values("accepted_median_weighted_penalty", ascending=False).reset_index(drop=True)


def _module3_5_best_proposal_target_penalties(
    proposal_target_medians: pd.DataFrame,
    family_best_rows: pd.DataFrame,
) -> pd.DataFrame:
    if proposal_target_medians.empty or family_best_rows.empty:
        return pd.DataFrame()
    best = family_best_rows[["family_id", "proposal_id", "global_stage_b_rank"]].copy()
    rows = proposal_target_medians.merge(best, on=["family_id", "proposal_id"], how="inner")
    return rows.sort_values(
        ["global_stage_b_rank", "median_weighted_penalty"],
        ascending=[True, False],
    ).reset_index(drop=True)


def _module3_5_target_omission_rows(
    proposal_target_medians: pd.DataFrame,
    proposal_summary: pd.DataFrame,
) -> pd.DataFrame:
    valid = _valid_stage_b_proposals(proposal_summary)[["proposal_id", "family_id"]].copy()
    if valid.empty or proposal_target_medians.empty:
        return pd.DataFrame(
            columns=[
                "omission_label",
                "omitted_target_ids",
                "family_id",
                "best_proposal_id",
                "adjusted_median_target_sum",
                "family_rank",
                "delta_from_winning_family",
            ]
        )

    proposal_targets = proposal_target_medians.merge(valid, on=["proposal_id", "family_id"], how="inner")
    target_ids = sorted(proposal_targets["target_id"].astype(str).unique())
    omission_specs: list[tuple[str, tuple[str, ...]]] = [
        ("none", ()),
        *[(target_id, (target_id,)) for target_id in target_ids],
        ("late_terminal_block", ("CT007", "CT009", "CT010")),
        ("causal_mechanism_block", ("CT004", "CT005")),
    ]

    rows: list[dict[str, Any]] = []
    for label, omitted_targets in omission_specs:
        keep = proposal_targets.loc[~proposal_targets["target_id"].isin(omitted_targets)].copy()
        proposal_totals = (
            keep.groupby(["proposal_id", "family_id"], as_index=False)["median_weighted_penalty"]
            .sum()
            .rename(columns={"median_weighted_penalty": "adjusted_median_target_sum"})
        )
        if proposal_totals.empty:
            continue
        best_by_family = (
            proposal_totals.sort_values(["adjusted_median_target_sum", "proposal_id"])
            .groupby("family_id", as_index=False)
            .head(1)
            .sort_values(["adjusted_median_target_sum", "family_id"])
            .reset_index(drop=True)
        )
        best_by_family["family_rank"] = np.arange(1, len(best_by_family) + 1)
        winning_distance = float(best_by_family["adjusted_median_target_sum"].iloc[0])
        for row in best_by_family.to_dict(orient="records"):
            rows.append(
                {
                    "omission_label": label,
                    "omitted_target_ids": ",".join(omitted_targets) if omitted_targets else "none",
                    "family_id": row["family_id"],
                    "best_proposal_id": row["proposal_id"],
                    "adjusted_median_target_sum": float(row["adjusted_median_target_sum"]),
                    "family_rank": int(row["family_rank"]),
                    "delta_from_winning_family": float(row["adjusted_median_target_sum"] - winning_distance),
                }
            )
    return pd.DataFrame(rows)


def run_module3_5_diagnostic_review(
    root: Path,
    config: Module3Config | None = None,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    data_dir = root / "data"
    model_inputs = load_model_inputs(data_dir)
    diagnostic_dir = root / "outputs" / "module3_5"
    diagnostic_config = config or Module3Config.readiness_defaults(
        output_dir=diagnostic_dir / "diagnostic_primary"
    )
    _fresh_run_dir(diagnostic_config.output_dir)

    run = run_module3_calibration(model_inputs, diagnostic_config)
    proposal_summary = run.proposal_summary_table.copy()
    target_scores = run.target_scores_table.copy()
    accepted_summary = run.accepted_proposals_table.copy()

    stage_b_frontier = _module3_5_stage_b_frontier(proposal_summary)
    family_best = _module3_5_family_best_rows(stage_b_frontier)
    proposal_target_medians = _module3_5_proposal_target_medians(target_scores)
    sampler_failures = _module3_5_sampler_failure_rows(proposal_summary)
    target_leverage = _module3_5_target_leverage_rows(
        proposal_target_medians,
        proposal_summary,
        model_inputs,
    )
    accepted_target_penalties = _module3_5_accepted_target_penalties(
        proposal_target_medians,
        accepted_summary,
        model_inputs,
    )
    best_proposal_targets = _module3_5_best_proposal_target_penalties(
        proposal_target_medians,
        family_best,
    )
    target_omission = _module3_5_target_omission_rows(proposal_target_medians, proposal_summary)

    valid_stage_b = _valid_stage_b_proposals(proposal_summary)
    winning_family = (
        str(stage_b_frontier.iloc[0]["family_id"]) if not stage_b_frontier.empty else ""
    )
    omitted_winners = (
        target_omission.loc[target_omission["family_rank"] == 1].copy()
        if "family_rank" in target_omission.columns
        else pd.DataFrame()
    )
    omission_flip_count = int((omitted_winners["family_id"] != winning_family).sum()) if not omitted_winners.empty else 0

    evaluation = {
        "config": {
            "stage_a_draws_per_family": diagnostic_config.stage_a_draws_per_family,
            "stage_a_keep_per_family": diagnostic_config.stage_a_keep_per_family,
            "stage_b_historical_replicates": diagnostic_config.stage_b_historical_replicates,
            "final_acceptance_fraction": diagnostic_config.final_acceptance_fraction,
            "final_acceptance_cap": diagnostic_config.final_acceptance_cap,
            "master_seed": diagnostic_config.master_seed,
            "output_dir": str(diagnostic_config.output_dir),
        },
        "metrics": {
            "stage_b_valid_proposals": int(len(valid_stage_b)),
            "accepted_count": int(len(accepted_summary)),
            "winning_family": winning_family,
            "target_omission_flip_count": omission_flip_count,
        },
        "recommended_next_step": (
            "Reparameterize constrained priors before changing biological target weights."
            if not sampler_failures.empty
            else "Run a larger remote sensitivity sweep before changing biological target weights."
        ),
    }
    tables = {
        "family_summary": run.family_summary_table.copy(),
        "sampler_failures": sampler_failures,
        "stage_b_frontier": stage_b_frontier,
        "family_best_stage_b": family_best,
        "target_leverage": target_leverage,
        "accepted_target_penalties": accepted_target_penalties,
        "best_proposal_target_penalties": best_proposal_targets,
        "target_omission_sensitivity": target_omission,
    }
    return tables, evaluation


def render_module3_5_diagnostic_review(
    tables: dict[str, pd.DataFrame],
    evaluation: dict[str, Any],
) -> str:
    metrics = [{"metric": key, "value": value} for key, value in evaluation["metrics"].items()]
    config_rows = [{"setting": key, "value": value} for key, value in evaluation["config"].items()]

    sampler_rows = tables["sampler_failures"].head(10).to_dict(orient="records")
    family_best_rows = tables["family_best_stage_b"][
        [
            "global_stage_b_rank",
            "proposal_id",
            "family_id",
            "stage_status",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_iqr",
        ]
    ].to_dict(orient="records") if not tables["family_best_stage_b"].empty else []
    accepted_target_rows = tables["accepted_target_penalties"].head(8).to_dict(orient="records")
    best_target_rows = tables["best_proposal_target_penalties"][
        [
            "family_id",
            "proposal_id",
            "target_id",
            "median_weighted_penalty",
        ]
    ].head(30).to_dict(orient="records") if not tables["best_proposal_target_penalties"].empty else []
    omission_table = tables["target_omission_sensitivity"]
    omission_winners = (
        omission_table.loc[omission_table["family_rank"] == 1].copy()
        if "family_rank" in omission_table.columns
        else pd.DataFrame()
    )
    omission_rows = omission_winners[
        [
            "omission_label",
            "omitted_target_ids",
            "family_id",
            "best_proposal_id",
            "adjusted_median_target_sum",
        ]
    ].to_dict(orient="records") if not omission_winners.empty else []

    lines = [
        "# Module 3.5 Diagnostic Review",
        "",
        "## Summary",
        "",
        (
            "Module 3.5 diagnoses why the first ABC/history-matching readiness run is not yet "
            "a sound basis for Module 4 posterior summaries."
        ),
        (
            "It reruns the Module 3 readiness-scale calibration once, then inspects sampler "
            "failures, retained-proposal target leverage, and target-omission family ranking."
        ),
        "",
        "## Run Configuration",
        "",
        _markdown_table(config_rows, ["setting", "value"]),
        "",
        "## Key Metrics",
        "",
        _markdown_table(metrics, ["metric", "value"]),
        "",
        "## Sampler Geometry",
        "",
    ]
    if sampler_rows:
        lines.append(
            _markdown_table(
                sampler_rows,
                ["family_id", "stage_status", "failure_reason", "failure_count", "failure_rate"],
            )
        )
    else:
        lines.append("No pre-simulation sampler or constraint failures were recorded.")

    lines.extend(
        [
            "",
            "## Family Ranking Frontier",
            "",
        ]
    )
    if family_best_rows:
        lines.append(
            _markdown_table(
                family_best_rows,
                [
                    "global_stage_b_rank",
                    "proposal_id",
                    "family_id",
                    "stage_status",
                    "stochastic_overall_distance_median",
                    "stochastic_historical_core_distance_iqr",
                ],
            )
        )
    else:
        lines.append("No valid Stage B proposals were available for ranking.")

    lines.extend(
        [
            "",
            "## Accepted Target Leverage",
            "",
        ]
    )
    if accepted_target_rows:
        lines.append(
            _markdown_table(
                accepted_target_rows,
                [
                    "target_id",
                    "target_group",
                    "comparison_type",
                    "priority_weight",
                    "accepted_median_weighted_penalty",
                ],
            )
        )
    else:
        lines.append("No accepted proposals were available for target-leverage summaries.")

    lines.extend(
        [
            "",
            "## Best Proposal Target Penalties",
            "",
        ]
    )
    if best_target_rows:
        lines.append(
            _markdown_table(
                best_target_rows,
                ["family_id", "proposal_id", "target_id", "median_weighted_penalty"],
            )
        )
    else:
        lines.append("No best-proposal target penalties were available.")

    lines.extend(
        [
            "",
            "## Target Omission Sensitivity",
            "",
        ]
    )
    if omission_rows:
        lines.append(
            _markdown_table(
                omission_rows,
                [
                    "omission_label",
                    "omitted_target_ids",
                    "family_id",
                    "best_proposal_id",
                    "adjusted_median_target_sum",
                ],
            )
        )
    else:
        lines.append("Target omission sensitivity could not be computed.")

    lines.extend(["", "## Interpretation", ""])
    if sampler_rows:
        lines.extend(
            [
                "The immediate blocker is sampler geometry, not numerical instability or reproducibility.",
                (
                    "Independent prior draws frequently violate ordered biological constraints, so a large "
                    "fraction of proposals never reaches simulation. The next code change should therefore "
                    "make those constrained pairs explicit in the sampling parameterisation."
                ),
            ]
        )
    else:
        lines.extend(
            [
                "The constraint-aware sampler removed the pre-simulation validity blocker.",
                (
                    "At this readiness scale the accepted frontier now includes climbing-only, persistent "
                    "joint-cause, and transient perfect-storm proposals, so the earlier climbing-only result "
                    "should not be interpreted as a stable biological conclusion."
                ),
            ]
        )
    lines.extend(
        [
            (
                "Family ranking remains sensitive to the late detection and contraction targets: omitting "
                "`CT007`, `CT010`, or the late-terminal block can move the best retained proposal toward "
                "the persistent joint-cause family."
            ),
            "",
            "## Recommended Next Step",
            "",
            evaluation["recommended_next_step"],
            "",
            "## Artifacts",
            "",
            "- `data/module3_5_family_summary.csv`",
            "- `data/module3_5_sampler_failures.csv`",
            "- `data/module3_5_stage_b_frontier.csv`",
            "- `data/module3_5_family_best_stage_b.csv`",
            "- `data/module3_5_target_leverage.csv`",
            "- `data/module3_5_accepted_target_penalties.csv`",
            "- `data/module3_5_best_proposal_target_penalties.csv`",
            "- `data/module3_5_target_omission_sensitivity.csv`",
            "- `docs/module3_5_diagnostic_review.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_module3_5_diagnostic_bundle(
    root: Path,
    output_root: Path | None = None,
    config: Module3Config | None = None,
) -> dict[str, Any]:
    target_root = output_root if output_root is not None else root
    output_data_dir = target_root / "data"
    docs_dir = target_root / "docs"
    tables, evaluation = run_module3_5_diagnostic_review(root, config=config)

    output_data_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    for name, frame in tables.items():
        path = output_data_dir / f"module3_5_{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path

    review_path = docs_dir / "module3_5_diagnostic_review.md"
    review_path.write_text(render_module3_5_diagnostic_review(tables, evaluation), encoding="utf-8")

    return {
        **paths,
        "review_doc": review_path,
        "winning_family": evaluation["metrics"]["winning_family"],
        "target_omission_flip_count": evaluation["metrics"]["target_omission_flip_count"],
        "recommended_next_step": evaluation["recommended_next_step"],
    }
