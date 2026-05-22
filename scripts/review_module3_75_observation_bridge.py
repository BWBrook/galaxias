from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galaxias_model.scoring import count_penalty, range_penalty


ROOT = Path(__file__).resolve().parents[1]
VALID_STAGE_B_STATUSES = {"stage_b_rejected", "accepted"}
DETECTION_MULTIPLIERS = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5)


def _format_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return "NA"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows available._"
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_format_value(row.get(column)) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write Module 3.75 observation-bridge diagnostics.")
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=ROOT / "outputs" / "remote",
        help="Root containing Module 3.5 sensitivity run directories.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        action="append",
        default=None,
        help="Specific raw_run or parent artifact directory. May be supplied multiple times.",
    )
    return parser.parse_args()


def _as_raw_run_dir(path: Path) -> Path:
    return path if path.name == "raw_run" else path / "raw_run"


def discover_raw_run_dirs(artifact_root: Path, explicit_dirs: list[Path] | None) -> list[Path]:
    candidates = [_as_raw_run_dir(path) for path in explicit_dirs] if explicit_dirs else []
    if not candidates:
        candidates = sorted(artifact_root.glob("*/raw_run"))
    raw_dirs = [
        path
        for path in candidates
        if (path / "proposal_summary.csv.gz").exists()
        and (path / "target_scores.csv.gz").exists()
        and (path / "parameter_values.csv.gz").exists()
    ]
    if not raw_dirs:
        raise FileNotFoundError(
            "No Module 3.5 raw run artifacts found. Expected raw_run directories with "
            "proposal_summary.csv.gz, target_scores.csv.gz, and parameter_values.csv.gz."
        )
    return raw_dirs


def load_target_metadata(root: Path) -> tuple[dict[str, Any], pd.DataFrame]:
    details = json.loads((root / "data" / "calibration_target_details.json").read_text(encoding="utf-8"))
    targets = pd.read_csv(root / "data" / "calibration_targets.csv")
    return details, targets


def _read_manifest(raw_dir: Path) -> dict[str, Any]:
    manifest_path = raw_dir / "run_manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}


def _run_label(raw_dir: Path) -> str:
    return raw_dir.parent.name if raw_dir.name == "raw_run" else raw_dir.name


def _run_seed(manifest: dict[str, Any]) -> int | None:
    seed = manifest.get("config", {}).get("master_seed")
    return int(seed) if seed is not None else None


def _normalise_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def load_raw_run(raw_dir: Path) -> dict[str, pd.DataFrame | dict[str, Any] | str | int | None]:
    manifest = _read_manifest(raw_dir)
    run_label = _run_label(raw_dir)
    seed = _run_seed(manifest)

    proposal_summary = pd.read_csv(raw_dir / "proposal_summary.csv.gz")
    target_scores = pd.read_csv(raw_dir / "target_scores.csv.gz")
    parameter_values = pd.read_csv(raw_dir / "parameter_values.csv.gz")

    for frame in (proposal_summary, target_scores, parameter_values):
        frame["run_label"] = run_label
        frame["seed"] = seed

    proposal_summary["accepted_final"] = _normalise_bool(proposal_summary["accepted_final"])
    for column in [
        "proposal_index",
        "proposal_seed",
        "deterministic_overall_distance",
        "stochastic_overall_distance_median",
        "stochastic_historical_core_distance_median",
        "stochastic_intrinsic_baseline_distance_median",
        "stochastic_historical_core_distance_iqr",
        "stage_a_rank",
        "stage_b_rank",
    ]:
        if column in proposal_summary:
            proposal_summary[column] = pd.to_numeric(proposal_summary[column], errors="coerce")

    for column in ["replicate_index", "raw_penalty", "weighted_penalty", "projected_primary", "projected_secondary"]:
        if column in target_scores:
            target_scores[column] = pd.to_numeric(target_scores[column], errors="coerce")

    parameter_values["value_natural"] = pd.to_numeric(parameter_values["value_natural"], errors="coerce")

    return {
        "run_label": run_label,
        "seed": seed,
        "manifest": manifest,
        "proposal_summary": proposal_summary,
        "target_scores": target_scores,
        "parameter_values": parameter_values,
    }


def _valid_stage_b(proposal_summary: pd.DataFrame) -> pd.DataFrame:
    valid = proposal_summary.loc[proposal_summary["stage_status"].isin(VALID_STAGE_B_STATUSES)].copy()
    valid["stochastic_overall_distance_median"] = pd.to_numeric(
        valid["stochastic_overall_distance_median"],
        errors="coerce",
    )
    return valid.loc[np.isfinite(valid["stochastic_overall_distance_median"])].copy()


def _proposal_metadata(proposal_summary: pd.DataFrame) -> pd.DataFrame:
    valid = _valid_stage_b(proposal_summary)
    return valid[
        [
            "run_label",
            "seed",
            "proposal_id",
            "family_id",
            "stage_status",
            "accepted_final",
            "stage_b_rank",
            "stochastic_overall_distance_median",
            "stochastic_historical_core_distance_median",
            "stochastic_intrinsic_baseline_distance_median",
            "stochastic_historical_core_distance_iqr",
        ]
    ].copy()


def _parameter_lookup(parameter_values: pd.DataFrame, parameter_id: str) -> pd.DataFrame:
    params = parameter_values.loc[parameter_values["parameter_id"] == parameter_id].copy()
    return params[
        ["run_label", "seed", "proposal_id", "family_id", "value_natural"]
    ].rename(columns={"value_natural": parameter_id.lower()})


def _stage_b_target_scores(
    target_scores: pd.DataFrame,
    proposal_meta: pd.DataFrame,
    target_ids: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    scores = target_scores.loc[target_scores["stage"] == "stage_b"].copy()
    if target_ids is not None:
        scores = scores.loc[scores["target_id"].isin(target_ids)].copy()
    scores = scores.merge(
        proposal_meta[["run_label", "proposal_id", "family_id", "accepted_final"]],
        on=["run_label", "proposal_id", "family_id"],
        how="inner",
    )
    return scores.loc[scores["evaluation_status"] == "scored"].copy()


def proposal_target_medians(target_scores: pd.DataFrame, proposal_meta: pd.DataFrame) -> pd.DataFrame:
    scores = _stage_b_target_scores(target_scores, proposal_meta)
    return (
        scores.groupby(["run_label", "seed", "proposal_id", "family_id", "target_id"], as_index=False)
        .agg(
            median_weighted_penalty=("weighted_penalty", "median"),
            median_raw_penalty=("raw_penalty", "median"),
            median_projected_primary=("projected_primary", "median"),
            median_projected_secondary=("projected_secondary", "median"),
            replicate_count=("weighted_penalty", "size"),
        )
        .sort_values(["seed", "family_id", "proposal_id", "target_id"])
        .reset_index(drop=True)
    )


def build_ct007_decomposition(
    target_scores: pd.DataFrame,
    proposal_meta: pd.DataFrame,
    parameter_values: pd.DataFrame,
    target_details: dict[str, Any],
    priority_weight: float,
) -> pd.DataFrame:
    details = target_details["CT007"]
    site_range = details["occupied_site_range"]
    pr037 = _parameter_lookup(parameter_values, "PR037")
    scores = _stage_b_target_scores(target_scores, proposal_meta, ("CT007",)).merge(
        pr037,
        on=["run_label", "seed", "proposal_id", "family_id"],
        how="left",
    )
    scores["expected_occupied_sites"] = scores["projected_primary"]
    scores["expected_refuge_capture_mean"] = scores["projected_secondary"]
    scores["ct007_occupancy_component_raw"] = scores["expected_occupied_sites"].map(
        lambda value: range_penalty(value, site_range["low"], site_range["high"])
    )
    scores["ct007_count_component_raw"] = scores.apply(
        lambda row: count_penalty(
            obs=details["observed_capture_count"],
            exp=row["expected_refuge_capture_mean"],
            overdispersion=row["pr037"],
        ),
        axis=1,
    )
    scores["ct007_recomputed_raw_penalty"] = 0.5 * (
        scores["ct007_occupancy_component_raw"] + scores["ct007_count_component_raw"]
    )
    scores["ct007_recomputed_weighted_penalty"] = priority_weight * scores["ct007_recomputed_raw_penalty"]
    scores["ct007_occupancy_primary_weighted_penalty"] = priority_weight * (
        0.75 * scores["ct007_occupancy_component_raw"] + 0.25 * scores["ct007_count_component_raw"]
    )
    scores["ct007_count_primary_weighted_penalty"] = priority_weight * (
        0.25 * scores["ct007_occupancy_component_raw"] + 0.75 * scores["ct007_count_component_raw"]
    )
    scores["ct007_occupancy_only_weighted_penalty"] = priority_weight * scores["ct007_occupancy_component_raw"]
    scores["ct007_count_only_weighted_penalty"] = priority_weight * scores["ct007_count_component_raw"]

    summary = (
        scores.groupby(["run_label", "seed", "proposal_id", "family_id"], as_index=False)
        .agg(
            accepted_final=("accepted_final", "first"),
            replicate_count=("weighted_penalty", "size"),
            expected_occupied_sites_median=("expected_occupied_sites", "median"),
            expected_refuge_capture_mean_median=("expected_refuge_capture_mean", "median"),
            pr037_median=("pr037", "median"),
            ct007_current_weighted_penalty_median=("weighted_penalty", "median"),
            ct007_recomputed_weighted_penalty_median=("ct007_recomputed_weighted_penalty", "median"),
            ct007_occupancy_component_raw_median=("ct007_occupancy_component_raw", "median"),
            ct007_count_component_raw_median=("ct007_count_component_raw", "median"),
            ct007_occupancy_primary_weighted_penalty_median=("ct007_occupancy_primary_weighted_penalty", "median"),
            ct007_count_primary_weighted_penalty_median=("ct007_count_primary_weighted_penalty", "median"),
            ct007_occupancy_only_weighted_penalty_median=("ct007_occupancy_only_weighted_penalty", "median"),
            ct007_count_only_weighted_penalty_median=("ct007_count_only_weighted_penalty", "median"),
        )
        .sort_values(["seed", "family_id", "proposal_id"])
        .reset_index(drop=True)
    )
    denominator = (
        summary["ct007_occupancy_component_raw_median"] + summary["ct007_count_component_raw_median"]
    ).replace(0.0, np.nan)
    summary["ct007_occupancy_component_share"] = summary["ct007_occupancy_component_raw_median"] / denominator
    summary["ct007_count_component_share"] = summary["ct007_count_component_raw_median"] / denominator
    return summary


def _terminal_window_penalty(
    value: float,
    low: int = 1992,
    high: int = 1996,
    early_gap: float = 4.0,
    late_gap: float = 3.0,
) -> float:
    if value is None or pd.isna(value):
        return 10.0
    year = float(value)
    if low <= year <= high:
        return 0.0
    if year < low:
        return (low - year) / max(float(early_gap), 1e-9)
    return (year - high) / max(float(late_gap), 1e-9)


def build_ct009_soft_window(
    target_scores: pd.DataFrame,
    proposal_meta: pd.DataFrame,
    priority_weight: float,
) -> pd.DataFrame:
    scores = _stage_b_target_scores(target_scores, proposal_meta, ("CT009",)).copy()
    scores["last_year_total_present"] = scores["projected_primary"]
    scores["first_year_total_absent"] = scores["projected_secondary"]
    for gap in (2.0, 3.0, 4.0):
        raw_col = f"ct009_terminal_window_1992_1996_gap{int(gap)}_raw"
        weighted_col = f"ct009_terminal_window_1992_1996_gap{int(gap)}_weighted"
        scores[raw_col] = scores["last_year_total_present"].map(lambda value: _terminal_window_penalty(value, late_gap=gap))
        scores[weighted_col] = priority_weight * scores[raw_col]

    return (
        scores.groupby(["run_label", "seed", "proposal_id", "family_id"], as_index=False)
        .agg(
            accepted_final=("accepted_final", "first"),
            replicate_count=("weighted_penalty", "size"),
            last_year_total_present_median=("last_year_total_present", "median"),
            first_year_total_absent_median=("first_year_total_absent", "median"),
            ct009_current_exact_weighted_penalty_median=("weighted_penalty", "median"),
            ct009_terminal_window_gap2_weighted_penalty_median=(
                "ct009_terminal_window_1992_1996_gap2_weighted",
                "median",
            ),
            ct009_terminal_window_gap3_weighted_penalty_median=(
                "ct009_terminal_window_1992_1996_gap3_weighted",
                "median",
            ),
            ct009_terminal_window_gap4_weighted_penalty_median=(
                "ct009_terminal_window_1992_1996_gap4_weighted",
                "median",
            ),
        )
        .sort_values(["seed", "family_id", "proposal_id"])
        .reset_index(drop=True)
    )


def build_ct010_detection_sensitivity(
    target_scores: pd.DataFrame,
    proposal_meta: pd.DataFrame,
    parameter_values: pd.DataFrame,
    priority_weight: float,
) -> pd.DataFrame:
    pr037 = _parameter_lookup(parameter_values, "PR037")
    scores = _stage_b_target_scores(target_scores, proposal_meta, ("CT010",)).merge(
        pr037,
        on=["run_label", "seed", "proposal_id", "family_id"],
        how="left",
    )
    scores["mean_expected_detected_count"] = scores["projected_primary"]
    scores["max_expected_detected_count"] = scores["projected_secondary"]

    rows: list[dict[str, Any]] = []
    grouping = ["run_label", "seed", "proposal_id", "family_id"]
    for keys, group in scores.groupby(grouping):
        base_raw = 2.0 * group["mean_expected_detected_count"] / group["pr037"].clip(lower=1e-9)
        current_weighted = float(group["weighted_penalty"].median())
        for multiplier in DETECTION_MULTIPLIERS:
            weighted = float((priority_weight * base_raw * multiplier).median())
            rows.append(
                {
                    "run_label": keys[0],
                    "seed": keys[1],
                    "proposal_id": keys[2],
                    "family_id": keys[3],
                    "accepted_final": bool(group["accepted_final"].iloc[0]),
                    "detection_multiplier": float(multiplier),
                    "replicate_count": int(len(group)),
                    "mean_expected_detected_count_median": float(group["mean_expected_detected_count"].median()),
                    "max_expected_detected_count_median": float(group["max_expected_detected_count"].median()),
                    "pr037_median": float(group["pr037"].median()),
                    "ct010_current_weighted_penalty_median": current_weighted,
                    "ct010_scenario_weighted_penalty_median": weighted,
                    "delta_from_current_weighted_penalty": weighted - current_weighted,
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["seed", "family_id", "proposal_id", "detection_multiplier"]
    ).reset_index(drop=True)


def build_family_bridge_summary(
    proposal_meta: pd.DataFrame,
    ct007: pd.DataFrame,
    ct009: pd.DataFrame,
    ct010: pd.DataFrame,
) -> pd.DataFrame:
    ct010_half = ct010.loc[ct010["detection_multiplier"] == 0.5][
        [
            "run_label",
            "seed",
            "proposal_id",
            "family_id",
            "ct010_current_weighted_penalty_median",
            "ct010_scenario_weighted_penalty_median",
            "mean_expected_detected_count_median",
            "max_expected_detected_count_median",
        ]
    ].rename(columns={"ct010_scenario_weighted_penalty_median": "ct010_detection_half_weighted_penalty_median"})

    bridge = (
        proposal_meta.merge(ct007, on=["run_label", "seed", "proposal_id", "family_id", "accepted_final"], how="left")
        .merge(ct009, on=["run_label", "seed", "proposal_id", "family_id", "accepted_final"], how="left")
        .merge(ct010_half, on=["run_label", "seed", "proposal_id", "family_id"], how="left")
    )

    rows: list[pd.DataFrame] = []
    for label, subset in [
        ("all_stage_b_valid", bridge),
        ("accepted_final", bridge.loc[bridge["accepted_final"]].copy()),
    ]:
        if subset.empty:
            continue
        grouped = (
            subset.groupby(["run_label", "seed", "family_id"], as_index=False)
            .agg(
                proposal_group=("family_id", lambda _: label),
                proposal_count=("proposal_id", "nunique"),
                stage_b_rank_min=("stage_b_rank", "min"),
                stochastic_overall_distance_median=("stochastic_overall_distance_median", "median"),
                expected_occupied_sites_median=("expected_occupied_sites_median", "median"),
                expected_refuge_capture_mean_median=("expected_refuge_capture_mean_median", "median"),
                ct007_current_weighted_penalty_median=("ct007_current_weighted_penalty_median", "median"),
                ct007_occupancy_component_raw_median=("ct007_occupancy_component_raw_median", "median"),
                ct007_count_component_raw_median=("ct007_count_component_raw_median", "median"),
                ct007_count_component_share_median=("ct007_count_component_share", "median"),
                last_year_total_present_median=("last_year_total_present_median", "median"),
                ct009_current_exact_weighted_penalty_median=(
                    "ct009_current_exact_weighted_penalty_median",
                    "median",
                ),
                ct009_terminal_window_gap3_weighted_penalty_median=(
                    "ct009_terminal_window_gap3_weighted_penalty_median",
                    "median",
                ),
                mean_expected_detected_count_median=("mean_expected_detected_count_median", "median"),
                max_expected_detected_count_median=("max_expected_detected_count_median", "median"),
                ct010_current_weighted_penalty_median=("ct010_current_weighted_penalty_median", "median"),
                ct010_detection_half_weighted_penalty_median=(
                    "ct010_detection_half_weighted_penalty_median",
                    "median",
                ),
            )
            .reset_index(drop=True)
        )
        rows.append(grouped)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True).sort_values(
        ["proposal_group", "seed", "family_id"]
    ).reset_index(drop=True)


def _target_pivot(target_medians: pd.DataFrame) -> pd.DataFrame:
    pivot = target_medians.pivot_table(
        index=["run_label", "seed", "proposal_id", "family_id"],
        columns="target_id",
        values="median_weighted_penalty",
        aggfunc="first",
    ).reset_index()
    pivot.columns.name = None
    return pivot


def build_ranking_scenarios(
    proposal_meta: pd.DataFrame,
    target_medians: pd.DataFrame,
    ct007: pd.DataFrame,
    ct009: pd.DataFrame,
    ct010: pd.DataFrame,
) -> pd.DataFrame:
    target_totals = (
        target_medians.groupby(["run_label", "seed", "proposal_id", "family_id"], as_index=False)[
            "median_weighted_penalty"
        ]
        .sum()
        .rename(columns={"median_weighted_penalty": "baseline_target_sum"})
    )
    target_components = _target_pivot(target_medians)
    ct010_half = ct010.loc[ct010["detection_multiplier"] == 0.5][
        ["run_label", "seed", "proposal_id", "family_id", "ct010_scenario_weighted_penalty_median"]
    ].rename(columns={"ct010_scenario_weighted_penalty_median": "ct010_detection_half_weighted_penalty_median"})

    components = (
        proposal_meta[["run_label", "seed", "proposal_id", "family_id", "accepted_final", "stage_b_rank"]]
        .merge(target_totals, on=["run_label", "seed", "proposal_id", "family_id"], how="inner")
        .merge(target_components, on=["run_label", "seed", "proposal_id", "family_id"], how="left")
        .merge(
            ct007[
                [
                    "run_label",
                    "seed",
                    "proposal_id",
                    "family_id",
                    "ct007_occupancy_primary_weighted_penalty_median",
                    "ct007_count_primary_weighted_penalty_median",
                    "ct007_occupancy_only_weighted_penalty_median",
                ]
            ],
            on=["run_label", "seed", "proposal_id", "family_id"],
            how="left",
        )
        .merge(
            ct009[
                [
                    "run_label",
                    "seed",
                    "proposal_id",
                    "family_id",
                    "ct009_terminal_window_gap3_weighted_penalty_median",
                ]
            ],
            on=["run_label", "seed", "proposal_id", "family_id"],
            how="left",
        )
        .merge(ct010_half, on=["run_label", "seed", "proposal_id", "family_id"], how="left")
    )

    scenario_rows: list[dict[str, Any]] = []
    for row in components.to_dict(orient="records"):
        current_ct007 = float(row.get("CT007", 0.0))
        current_ct009 = float(row.get("CT009", 0.0))
        current_ct010 = float(row.get("CT010", 0.0))
        baseline = float(row["baseline_target_sum"])
        scenario_specs = {
            "baseline_current": baseline,
            "ct007_occupancy_primary": (
                baseline - current_ct007 + float(row["ct007_occupancy_primary_weighted_penalty_median"])
            ),
            "ct007_count_primary": (
                baseline - current_ct007 + float(row["ct007_count_primary_weighted_penalty_median"])
            ),
            "ct009_terminal_window_gap3": (
                baseline - current_ct009 + float(row["ct009_terminal_window_gap3_weighted_penalty_median"])
            ),
            "ct010_detection_half": (
                baseline - current_ct010 + float(row["ct010_detection_half_weighted_penalty_median"])
            ),
            "late_bridge_soft": (
                baseline
                - current_ct007
                - current_ct009
                - current_ct010
                + float(row["ct007_occupancy_primary_weighted_penalty_median"])
                + float(row["ct009_terminal_window_gap3_weighted_penalty_median"])
                + float(row["ct010_detection_half_weighted_penalty_median"])
            ),
        }
        for scenario_id, adjusted in scenario_specs.items():
            scenario_rows.append(
                {
                    "run_label": row["run_label"],
                    "seed": row["seed"],
                    "scenario_id": scenario_id,
                    "proposal_id": row["proposal_id"],
                    "family_id": row["family_id"],
                    "accepted_final": row["accepted_final"],
                    "stage_b_rank": row["stage_b_rank"],
                    "baseline_target_sum": baseline,
                    "adjusted_target_sum": adjusted,
                }
            )

    scenarios = pd.DataFrame(scenario_rows)
    best = (
        scenarios.sort_values(["adjusted_target_sum", "proposal_id"])
        .groupby(["run_label", "seed", "scenario_id", "family_id"], as_index=False)
        .head(1)
        .sort_values(["seed", "scenario_id", "adjusted_target_sum", "family_id"])
        .reset_index(drop=True)
    )
    best["family_rank"] = best.groupby(["run_label", "seed", "scenario_id"]).cumcount() + 1
    winning = best.groupby(["run_label", "seed", "scenario_id"])["adjusted_target_sum"].transform("min")
    best["delta_from_winning_family"] = best["adjusted_target_sum"] - winning
    return best[
        [
            "run_label",
            "seed",
            "scenario_id",
            "family_rank",
            "family_id",
            "proposal_id",
            "accepted_final",
            "stage_b_rank",
            "baseline_target_sum",
            "adjusted_target_sum",
            "delta_from_winning_family",
        ]
    ].sort_values(["seed", "scenario_id", "family_rank"]).reset_index(drop=True)


def _accepted_summary_rows(family_summary: pd.DataFrame) -> list[dict[str, Any]]:
    accepted = family_summary.loc[family_summary["proposal_group"] == "accepted_final"].copy()
    if accepted.empty:
        return []
    rows = (
        accepted.groupby("family_id", as_index=False)
        .agg(
            accepted_proposals=("proposal_count", "sum"),
            ct007_current=("ct007_current_weighted_penalty_median", "median"),
            ct007_count_share=("ct007_count_component_share_median", "median"),
            ct009_current=("ct009_current_exact_weighted_penalty_median", "median"),
            ct009_soft_gap3=("ct009_terminal_window_gap3_weighted_penalty_median", "median"),
            ct010_current=("ct010_current_weighted_penalty_median", "median"),
            ct010_half=("ct010_detection_half_weighted_penalty_median", "median"),
        )
        .sort_values("family_id")
    )
    return rows.to_dict(orient="records")


def _scenario_winner_rows(ranking: pd.DataFrame) -> list[dict[str, Any]]:
    winners = ranking.loc[ranking["family_rank"] == 1].copy()
    if winners.empty:
        return []
    return winners[
        ["seed", "scenario_id", "family_id", "proposal_id", "adjusted_target_sum"]
    ].sort_values(["scenario_id", "seed"]).to_dict(orient="records")


def _ct007_component_rows(ct007: pd.DataFrame) -> list[dict[str, Any]]:
    accepted = ct007.loc[ct007["accepted_final"]].copy()
    if accepted.empty:
        return []
    rows = (
        accepted.groupby("family_id", as_index=False)
        .agg(
            expected_sites=("expected_occupied_sites_median", "median"),
            expected_capture=("expected_refuge_capture_mean_median", "median"),
            occupancy_raw=("ct007_occupancy_component_raw_median", "median"),
            count_raw=("ct007_count_component_raw_median", "median"),
            count_share=("ct007_count_component_share", "median"),
            current_weighted=("ct007_current_weighted_penalty_median", "median"),
        )
        .sort_values("family_id")
    )
    return rows.to_dict(orient="records")


def _input_rows(raw_dirs: list[Path], loaded: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for raw_dir, run in zip(raw_dirs, loaded, strict=True):
        manifest = run["manifest"]
        config = manifest.get("config", {}) if isinstance(manifest, dict) else {}
        rows.append(
            {
                "seed": run["seed"],
                "run_label": run["run_label"],
                "stage_a_draws_per_family": config.get("stage_a_draws_per_family"),
                "stage_a_keep_per_family": config.get("stage_a_keep_per_family"),
                "stage_b_replicates": config.get("stage_b_historical_replicates"),
                "artifact_dir": str(raw_dir),
            }
        )
    return rows


def render_review(
    raw_dirs: list[Path],
    loaded: list[dict[str, Any]],
    family_summary: pd.DataFrame,
    ct007: pd.DataFrame,
    ranking: pd.DataFrame,
) -> str:
    input_rows = _input_rows(raw_dirs, loaded)
    component_rows = _ct007_component_rows(ct007)
    accepted_rows = _accepted_summary_rows(family_summary)
    winner_rows = _scenario_winner_rows(ranking)

    baseline_winners = [
        row
        for row in winner_rows
        if row["scenario_id"] == "baseline_current"
    ]
    soft_winners = [
        row
        for row in winner_rows
        if row["scenario_id"] == "late_bridge_soft"
    ]
    baseline_family_count = (
        pd.DataFrame(baseline_winners)["family_id"].value_counts().to_dict() if baseline_winners else {}
    )
    soft_family_count = pd.DataFrame(soft_winners)["family_id"].value_counts().to_dict() if soft_winners else {}

    lines = [
        "# Module 3.75 Observation-Bridge Review",
        "",
        "## Summary",
        "",
        (
            "Module 3.75 reuses the three remote Module 3.5 sensitivity sweeps and asks whether "
            "the late-history targets are carrying biological signal or observation-bridge artefacts."
        ),
        (
            "The pass decomposes `CT007`, softens the exact-year treatment in `CT009`, and rescales "
            "`CT010` expected detections without rerunning the simulator."
        ),
        "",
        "## Inputs",
        "",
        _markdown_table(
            input_rows,
            [
                "seed",
                "run_label",
                "stage_a_draws_per_family",
                "stage_a_keep_per_family",
                "stage_b_replicates",
            ],
        ),
        "",
        "## CT007 Occupancy And Count Split",
        "",
        _markdown_table(
            component_rows,
            [
                "family_id",
                "expected_sites",
                "expected_capture",
                "occupancy_raw",
                "count_raw",
                "count_share",
                "current_weighted",
            ],
        ),
        "",
        "## Accepted Late-Target Summary",
        "",
        _markdown_table(
            accepted_rows,
            [
                "family_id",
                "accepted_proposals",
                "ct007_current",
                "ct007_count_share",
                "ct009_current",
                "ct009_soft_gap3",
                "ct010_current",
                "ct010_half",
            ],
        ),
        "",
        "## Scenario Winners",
        "",
        _markdown_table(
            winner_rows,
            ["seed", "scenario_id", "family_id", "proposal_id", "adjusted_target_sum"],
        ),
        "",
        "## Interpretation",
        "",
        (
            f"Under the current target-sum scoring, the baseline winners across seeds are "
            f"{baseline_family_count or 'unavailable'}."
        ),
        (
            f"Under the deliberately softer late observation bridge, the winners are "
            f"{soft_family_count or 'unavailable'}."
        ),
        (
            "`CT007` is not a pure occupancy target in practice: the Bonnet Bay capture anchor often "
            "contributes most of its raw penalty, so changing that split is a scientific choice rather "
            "than a cosmetic scoring tweak."
        ),
        (
            "`CT009` is structurally harsh because any proposal retaining natural-range presence to "
            "2002 receives a fixed 30 weighted-penalty hit. A terminal-window version reduces that hit "
            "to about 10 for 2002 persistence, which is enough to check robustness but not enough to "
            "make the endpoint irrelevant."
        ),
        (
            "`CT010` behaves exactly like an observation-effort scale for zero detections: halving the "
            "expected detection bridge halves the weighted penalty. This is useful for sensitivity "
            "analysis, but it should be justified from survey/capture effort rather than tuned to favor "
            "a family."
        ),
        "",
        "## Recommended Next Step",
        "",
        (
            "Keep the current biological family set, but promote the late observation bridge to an "
            "explicit Module 4 sensitivity axis: baseline, occupancy-primary `CT007`, soft `CT009`, "
            "and low-detection `CT010`. The key research question is no longer whether transient, "
            "persistent, and climbing-only mechanisms can all enter the frontier; they can. It is "
            "which conclusion survives transparent observation-model assumptions."
        ),
        "",
        "## Artifacts",
        "",
        "- `data/module3_75_ct007_decomposition.csv`",
        "- `data/module3_75_ct009_soft_window.csv`",
        "- `data/module3_75_ct010_detection_sensitivity.csv`",
        "- `data/module3_75_family_bridge_summary.csv`",
        "- `data/module3_75_ranking_scenarios.csv`",
        "- `docs/module3_75_observation_bridge_review.md`",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(root: Path, output_root: Path, raw_dirs: list[Path]) -> dict[str, Path]:
    target_details, targets = load_target_metadata(root)
    priority_lookup = dict(zip(targets["target_id"], targets["priority_weight"], strict=False))
    loaded = [load_raw_run(raw_dir) for raw_dir in raw_dirs]

    proposal_summary = pd.concat(
        [run["proposal_summary"] for run in loaded],
        ignore_index=True,
    )
    target_scores = pd.concat(
        [run["target_scores"] for run in loaded],
        ignore_index=True,
    )
    parameter_values = pd.concat(
        [run["parameter_values"] for run in loaded],
        ignore_index=True,
    )

    proposal_meta = _proposal_metadata(proposal_summary)
    target_medians = proposal_target_medians(target_scores, proposal_meta)
    ct007 = build_ct007_decomposition(
        target_scores,
        proposal_meta,
        parameter_values,
        target_details,
        float(priority_lookup["CT007"]),
    )
    ct009 = build_ct009_soft_window(
        target_scores,
        proposal_meta,
        float(priority_lookup["CT009"]),
    )
    ct010 = build_ct010_detection_sensitivity(
        target_scores,
        proposal_meta,
        parameter_values,
        float(priority_lookup["CT010"]),
    )
    family_summary = build_family_bridge_summary(proposal_meta, ct007, ct009, ct010)
    ranking = build_ranking_scenarios(proposal_meta, target_medians, ct007, ct009, ct010)

    data_dir = output_root / "data"
    docs_dir = output_root / "docs"
    data_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "ct007_decomposition": data_dir / "module3_75_ct007_decomposition.csv",
        "ct009_soft_window": data_dir / "module3_75_ct009_soft_window.csv",
        "ct010_detection_sensitivity": data_dir / "module3_75_ct010_detection_sensitivity.csv",
        "family_bridge_summary": data_dir / "module3_75_family_bridge_summary.csv",
        "ranking_scenarios": data_dir / "module3_75_ranking_scenarios.csv",
        "review_doc": docs_dir / "module3_75_observation_bridge_review.md",
    }
    ct007.to_csv(paths["ct007_decomposition"], index=False)
    ct009.to_csv(paths["ct009_soft_window"], index=False)
    ct010.to_csv(paths["ct010_detection_sensitivity"], index=False)
    family_summary.to_csv(paths["family_bridge_summary"], index=False)
    ranking.to_csv(paths["ranking_scenarios"], index=False)
    paths["review_doc"].write_text(
        render_review(raw_dirs, loaded, family_summary, ct007, ranking),
        encoding="utf-8",
    )
    return paths


def main() -> None:
    args = parse_args()
    raw_dirs = discover_raw_run_dirs(args.artifact_root, args.artifact_dir)
    paths = write_outputs(ROOT, args.output_root, raw_dirs)
    print("Wrote Module 3.75 observation-bridge diagnostics:")
    for name, path in paths.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
