from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from galaxias_model.io import load_model_inputs
from galaxias_model.sampling import build_resolved_parameters_from_sample
from galaxias_model.simulation import run_historical_simulation
from galaxias_model.types import SimulationConfig

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_MODULE4_ARTIFACTS: dict[str, str] = {
    "proposal_summary": "proposal_summary.csv.gz",
    "parameter_values": "parameter_values.csv.gz",
    "target_scores": "target_scores.csv.gz",
    "accepted_proposals": "accepted_proposals.csv",
    "family_summary": "family_summary.csv",
    "run_manifest": "run_manifest.json",
}

MODULE4_5_MANDATORY_OUTPUTS: tuple[str, ...] = (
    "data/module4_5_proposal_set_membership.csv",
    "data/module4_5_distance_audit.csv",
    "data/module4_5_parameter_summary.csv",
    "data/module4_5_parameter_contrasts.csv",
    "data/module4_5_nuisance_audit.csv",
    "data/module4_5_target_family_summary.csv",
    "data/module4_5_pressure_landmarks.csv",
    "data/module4_5_trajectory_landmarks.csv",
    "data/module4_5_family_decision_table.csv",
    "docs/module4_5_mechanism_interpretation_review.md",
)

PROPOSAL_SET_COLUMNS: dict[str, str] = {
    "accepted": "in_accepted",
    "near_frontier_absolute": "in_near_frontier_absolute",
    "near_frontier_relative": "in_near_frontier_relative",
    "family_winners": "in_family_winners",
    "global_winners": "in_global_winners",
}

MECHANISM_RICH_FAMILIES: tuple[str, ...] = (
    "climbing_only",
    "persistent_joint_cause",
    "transient_perfect_storm",
)

NUISANCE_PARAMETERS: tuple[str, ...] = ("PR035", "PR036", "PR037", "PR038", "PR039")

LANDMARK_YEARS: tuple[int, ...] = (1972, 1977, 1980, 1983, 1988, 1991, 1996, 2002)

PRESSURE_WINDOWS: tuple[tuple[str, int, int], ...] = (
    ("post_flood_boom_1972_1977", 1972, 1977),
    ("climbing_transition_1978_1983", 1978, 1983),
    ("refuge_contraction_1984_1991", 1984, 1991),
    ("final_record_window_1992_1996", 1992, 1996),
    ("non_detection_endpoint_1998_2002", 1998, 2002),
)

PROPOSAL_KEY_COLUMNS: list[str] = ["variant_id", "seed", "proposal_id", "family_id"]


@dataclass(frozen=True)
class Module4ArtifactValidation:
    manifest_path: Path
    module4_root: Path
    record_count: int
    run_count: int
    missing_files: tuple[str, ...]
    missing_roles: tuple[str, ...]
    hash_mismatches: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not (self.missing_files or self.missing_roles or self.hash_mismatches)


@dataclass(frozen=True)
class Module45GenerationResult:
    validation: Module4ArtifactValidation
    output_paths: dict[str, Path]
    row_counts: dict[str, int]


def module4_5_output_paths(publish_root: Path) -> dict[str, Path]:
    return {output: publish_root / output for output in MODULE4_5_MANDATORY_OUTPUTS}


def read_raw_artifact_manifest(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_path(row: dict[str, str], module4_root: Path) -> Path:
    if module4_root:
        return module4_root / row["run_dir_name"] / row["file_name"]
    return ROOT / row["local_path"]


def validate_module4_raw_artifact_manifest(
    manifest_path: Path,
    module4_root: Path,
    *,
    verify_hashes: bool = False,
) -> Module4ArtifactValidation:
    rows = read_raw_artifact_manifest(manifest_path)
    runs = sorted({(row["variant_id"], row["seed"], row["run_dir_name"]) for row in rows})
    expected_roles = set(REQUIRED_MODULE4_ARTIFACTS)
    roles_by_run: dict[tuple[str, str, str], set[str]] = {run: set() for run in runs}
    missing_files: list[str] = []
    hash_mismatches: list[str] = []

    for row in rows:
        run = (row["variant_id"], row["seed"], row["run_dir_name"])
        roles_by_run.setdefault(run, set()).add(row["file_role"])
        path = _artifact_path(row, module4_root)
        if not path.exists():
            missing_files.append(path.as_posix())
            continue
        if verify_hashes:
            expected_hash = row.get("local_sha256", "")
            if expected_hash and sha256_file(path) != expected_hash:
                hash_mismatches.append(path.as_posix())

    missing_roles = []
    for variant, seed, run_dir_name in runs:
        missing = sorted(expected_roles - roles_by_run[(variant, seed, run_dir_name)])
        for role in missing:
            missing_roles.append(f"{variant}:{seed}:{run_dir_name}:{role}")

    return Module4ArtifactValidation(
        manifest_path=manifest_path,
        module4_root=module4_root,
        record_count=len(rows),
        run_count=len(runs),
        missing_files=tuple(sorted(missing_files)),
        missing_roles=tuple(sorted(missing_roles)),
        hash_mismatches=tuple(sorted(hash_mismatches)),
    )


def _normalise_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, compression="infer")


def _run_key(row: dict[str, str]) -> tuple[str, int, str]:
    return str(row["variant_id"]), int(row["seed"]), str(row["run_dir_name"])


def _rows_by_run(rows: list[dict[str, str]]) -> dict[tuple[str, int, str], dict[str, dict[str, str]]]:
    grouped: dict[tuple[str, int, str], dict[str, dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(_run_key(row), {})[str(row["file_role"])] = row
    return grouped


def _load_module4_tables(
    manifest_rows: list[dict[str, str]],
    module4_root: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    proposal_frames: list[pd.DataFrame] = []
    parameter_frames: list[pd.DataFrame] = []
    target_frames: list[pd.DataFrame] = []
    family_frames: list[pd.DataFrame] = []
    accepted_frames: list[pd.DataFrame] = []
    run_records: list[dict[str, Any]] = []

    for (variant_id, seed, run_dir_name), role_rows in sorted(_rows_by_run(manifest_rows).items()):
        missing_roles = sorted(set(REQUIRED_MODULE4_ARTIFACTS) - set(role_rows))
        if missing_roles:
            raise ValueError(f"{run_dir_name} is missing manifest roles: {missing_roles}")

        run_manifest_path = _artifact_path(role_rows["run_manifest"], module4_root)
        run_manifest = _read_json(run_manifest_path)
        config = run_manifest.get("config", {})
        run_id = role_rows["run_manifest"].get("run_id", "")
        run_meta = {
            "module4_run_id": run_id,
            "variant_id": variant_id,
            "seed": seed,
            "run_dir_name": run_dir_name,
            "stage_a_draws_per_family": config.get("stage_a_draws_per_family"),
            "stage_a_keep_per_family": config.get("stage_a_keep_per_family"),
            "stage_b_historical_replicates": config.get("stage_b_historical_replicates"),
            "final_acceptance_fraction": config.get("final_acceptance_fraction"),
            "final_acceptance_cap": config.get("final_acceptance_cap"),
        }
        run_records.append(run_meta)

        for role, frames in [
            ("proposal_summary", proposal_frames),
            ("parameter_values", parameter_frames),
            ("target_scores", target_frames),
            ("family_summary", family_frames),
            ("accepted_proposals", accepted_frames),
        ]:
            frame = _read_csv(_artifact_path(role_rows[role], module4_root))
            frame["module4_run_id"] = run_id
            frame["variant_id"] = variant_id
            frame["seed"] = seed
            frame["run_dir_name"] = run_dir_name
            frames.append(frame)

    proposals = pd.concat(proposal_frames, ignore_index=True)
    parameters = pd.concat(parameter_frames, ignore_index=True)
    targets = pd.concat(target_frames, ignore_index=True)
    family_summary = pd.concat(family_frames, ignore_index=True)
    accepted = pd.concat(accepted_frames, ignore_index=True)

    proposals["accepted_final"] = _normalise_bool(proposals["accepted_final"])
    if "accepted_final" in accepted:
        accepted["accepted_final"] = _normalise_bool(accepted["accepted_final"])

    for frame in (proposals, parameters, targets, family_summary, accepted):
        frame["seed"] = pd.to_numeric(frame["seed"], errors="raise").astype(int)

    return proposals, parameters, targets, family_summary, accepted, run_records


def _proposal_target_sums(targets: pd.DataFrame, proposals: pd.DataFrame) -> pd.DataFrame:
    stage_b = targets.loc[targets["stage"] == "stage_b"].copy()
    stage_b["weighted_penalty"] = pd.to_numeric(stage_b["weighted_penalty"], errors="coerce")
    stage_b = stage_b.loc[stage_b["weighted_penalty"].notna()].copy()
    medians = (
        stage_b.groupby(["variant_id", "seed", "proposal_id", "family_id", "target_id"], as_index=False)
        .agg(
            median_weighted_penalty=("weighted_penalty", "median"),
            replicate_count=("replicate_index", "nunique"),
        )
    )
    sums = (
        medians.groupby(["variant_id", "seed", "proposal_id", "family_id"], as_index=False)
        .agg(
            target_sum=("median_weighted_penalty", "sum"),
            target_count=("target_id", "nunique"),
            min_replicate_count=("replicate_count", "min"),
        )
    )
    meta_cols = [
        "variant_id",
        "seed",
        "run_dir_name",
        "proposal_id",
        "family_id",
        "family_label",
        "proposal_index",
        "proposal_seed",
        "stage_status",
        "accepted_final",
        "stage_b_rank",
        "stochastic_overall_distance_median",
        "stochastic_historical_core_distance_median",
        "stochastic_intrinsic_baseline_distance_median",
        "stochastic_historical_core_distance_iqr",
    ]
    return sums.merge(
        proposals[[column for column in meta_cols if column in proposals.columns]],
        on=["variant_id", "seed", "proposal_id", "family_id"],
        how="left",
    )


def build_proposal_set_membership(
    proposals: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    near_frontier_delta: float = 10.0,
    near_frontier_relative: float = 1.05,
) -> pd.DataFrame:
    target_sums = _proposal_target_sums(targets, proposals)
    proposal_cols = [
        "module4_run_id",
        "variant_id",
        "seed",
        "run_dir_name",
        "proposal_id",
        "family_id",
        "family_label",
        "proposal_index",
        "proposal_seed",
        "stage_status",
        "accepted_final",
        "stage_b_rank",
        "deterministic_overall_distance",
        "stochastic_overall_distance_median",
        "stochastic_historical_core_distance_median",
        "stochastic_intrinsic_baseline_distance_median",
        "stochastic_historical_core_distance_iqr",
    ]
    membership = proposals[[column for column in proposal_cols if column in proposals.columns]].drop_duplicates(
        subset=PROPOSAL_KEY_COLUMNS
    )
    membership = membership.merge(
        target_sums[
            [
                "variant_id",
                "seed",
                "proposal_id",
                "family_id",
                "target_sum",
                "target_count",
                "min_replicate_count",
            ]
        ],
        on=PROPOSAL_KEY_COLUMNS,
        how="left",
    )

    membership["has_stage_b_scores"] = membership["target_sum"].notna()
    best = membership.groupby(["variant_id", "seed"])["target_sum"].transform("min")
    family_best = membership.groupby(["variant_id", "seed", "family_id"])["target_sum"].transform("min")
    membership["best_target_sum"] = best
    membership["family_best_target_sum"] = family_best
    membership["delta_from_best_target_sum"] = membership["target_sum"] - membership["best_target_sum"]
    membership["target_sum_rank"] = membership.groupby(["variant_id", "seed"])["target_sum"].rank(
        method="min",
        na_option="bottom",
    )
    membership["stochastic_distance_rank"] = membership.groupby(["variant_id", "seed"])[
        "stochastic_overall_distance_median"
    ].rank(method="min", na_option="bottom")
    membership["in_accepted"] = membership["accepted_final"].fillna(False).astype(bool)
    membership["in_near_frontier_absolute"] = membership["has_stage_b_scores"] & (
        membership["target_sum"] <= membership["best_target_sum"] + near_frontier_delta
    )
    membership["in_near_frontier_relative"] = membership["has_stage_b_scores"] & (
        membership["target_sum"] <= membership["best_target_sum"] * near_frontier_relative
    )
    membership["in_family_winners"] = membership["has_stage_b_scores"] & (
        membership["target_sum"] == membership["family_best_target_sum"]
    )
    membership["in_global_winners"] = membership["has_stage_b_scores"] & (
        membership["target_sum"] == membership["best_target_sum"]
    )
    membership["near_frontier_delta"] = near_frontier_delta
    membership["near_frontier_relative"] = near_frontier_relative
    return membership.sort_values(["variant_id", "seed", "family_id", "target_sum", "proposal_id"]).reset_index(
        drop=True
    )


def _expand_proposal_sets(membership: pd.DataFrame, sets: tuple[str, ...] | None = None) -> pd.DataFrame:
    selected_sets = sets if sets is not None else tuple(PROPOSAL_SET_COLUMNS)
    frames = []
    for set_name in selected_sets:
        flag = PROPOSAL_SET_COLUMNS[set_name]
        subset = membership.loc[membership[flag]].copy()
        subset["proposal_set"] = set_name
        frames.append(subset)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _spearman(x: pd.Series, y: pd.Series) -> float:
    frame = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(frame) < 3 or frame["x"].nunique() < 2 or frame["y"].nunique() < 2:
        return np.nan
    x_rank = frame["x"].rank(method="average")
    y_rank = frame["y"].rank(method="average")
    return float(x_rank.corr(y_rank))


def _quantile(series: pd.Series, q: float) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    return float(numeric.quantile(q)) if not numeric.empty else np.nan


def _with_prior_positions(parameters: pd.DataFrame, priors: pd.DataFrame) -> pd.DataFrame:
    prior_cols = [
        "parameter_id",
        "parameter_group",
        "parameter_name",
        "lower_bound",
        "upper_bound",
        "default_value",
        "sampling_transform",
    ]
    merged = parameters.merge(priors[prior_cols], on="parameter_id", how="left")
    for column in ["value_natural", "lower_bound", "upper_bound", "default_value"]:
        merged[column] = pd.to_numeric(merged[column], errors="coerce")
    span = merged["upper_bound"] - merged["lower_bound"]
    merged["prior_position"] = np.where(
        span > 0,
        (merged["value_natural"] - merged["lower_bound"]) / span,
        np.nan,
    )
    merged["near_lower_prior_bound"] = merged["prior_position"] <= 0.05
    merged["near_upper_prior_bound"] = merged["prior_position"] >= 0.95
    merged["near_either_prior_bound"] = merged["near_lower_prior_bound"] | merged["near_upper_prior_bound"]
    return merged


def _parameter_set_frame(
    parameters: pd.DataFrame,
    membership: pd.DataFrame,
    priors: pd.DataFrame,
    *,
    sets: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    assignments = _expand_proposal_sets(membership, sets=sets)
    if assignments.empty:
        return pd.DataFrame()
    keep_cols = [
        *PROPOSAL_KEY_COLUMNS,
        "proposal_set",
        "family_label",
        "target_sum",
        "stochastic_overall_distance_median",
        "target_sum_rank",
        "stochastic_distance_rank",
    ]
    merged = parameters.merge(assignments[keep_cols], on=PROPOSAL_KEY_COLUMNS, how="inner")
    return _with_prior_positions(merged, priors)


def _summarize_parameter_groups(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(group_cols, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        record = dict(zip(group_cols, key_values, strict=False))
        values = pd.to_numeric(group["value_natural"], errors="coerce")
        record.update(
            {
                "n_proposals": int(group["proposal_id"].nunique()),
                "parameter_group": group["parameter_group"].iloc[0],
                "parameter_name": group["parameter_name"].iloc[0],
                "parameter_status": group["parameter_status"].iloc[0],
                "lower_bound": float(group["lower_bound"].iloc[0]),
                "upper_bound": float(group["upper_bound"].iloc[0]),
                "default_value": float(group["default_value"].iloc[0]),
                "median_value": _quantile(values, 0.50),
                "q05_value": _quantile(values, 0.05),
                "q25_value": _quantile(values, 0.25),
                "q75_value": _quantile(values, 0.75),
                "q95_value": _quantile(values, 0.95),
                "median_prior_position": _quantile(group["prior_position"], 0.50),
                "near_lower_bound_fraction": float(group["near_lower_prior_bound"].mean()),
                "near_upper_bound_fraction": float(group["near_upper_prior_bound"].mean()),
                "near_either_bound_fraction": float(group["near_either_prior_bound"].mean()),
                "spearman_value_vs_target_sum": _spearman(group["value_natural"], group["target_sum"]),
                "spearman_value_vs_stochastic_distance": _spearman(
                    group["value_natural"],
                    group["stochastic_overall_distance_median"],
                ),
            }
        )
        rows.append(record)
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True) if rows else pd.DataFrame()


def build_parameter_summary(parameters: pd.DataFrame, membership: pd.DataFrame, priors: pd.DataFrame) -> pd.DataFrame:
    frame = _parameter_set_frame(parameters, membership, priors)
    if frame.empty:
        return pd.DataFrame()
    return _summarize_parameter_groups(
        frame,
        ["variant_id", "seed", "family_id", "family_label", "proposal_set", "parameter_id"],
    )


def build_nuisance_audit(parameters: pd.DataFrame, membership: pd.DataFrame, priors: pd.DataFrame) -> pd.DataFrame:
    frame = _parameter_set_frame(parameters, membership, priors)
    if frame.empty:
        return pd.DataFrame()
    frame = frame.loc[frame["parameter_id"].isin(NUISANCE_PARAMETERS)].copy()
    summary = _summarize_parameter_groups(
        frame,
        ["variant_id", "family_id", "family_label", "proposal_set", "parameter_id"],
    )
    if summary.empty:
        return summary
    summary["boundary_status"] = np.select(
        [
            summary["near_either_bound_fraction"] >= 0.50,
            summary["near_either_bound_fraction"] >= 0.25,
        ],
        ["high_boundary_dependence", "moderate_boundary_dependence"],
        default="low_boundary_dependence",
    )
    return summary


def _robust_effect(median_a: float, q25_a: float, q75_a: float, median_b: float, q25_b: float, q75_b: float) -> float:
    pooled_iqr = float(np.sqrt(((q75_a - q25_a) ** 2 + (q75_b - q25_b) ** 2) / 2))
    if not np.isfinite(pooled_iqr) or pooled_iqr <= 0:
        return np.nan
    return (median_a - median_b) / pooled_iqr


def _contrast_row(
    contrast_type: str,
    variant_id: str,
    proposal_set: str,
    parameter_id: str,
    label_a: str,
    values_a: pd.Series,
    label_b: str,
    values_b: pd.Series,
) -> dict[str, Any]:
    median_a = _quantile(values_a, 0.50)
    q25_a = _quantile(values_a, 0.25)
    q75_a = _quantile(values_a, 0.75)
    median_b = _quantile(values_b, 0.50)
    q25_b = _quantile(values_b, 0.25)
    q75_b = _quantile(values_b, 0.75)
    return {
        "contrast_type": contrast_type,
        "variant_id": variant_id,
        "proposal_set": proposal_set,
        "parameter_id": parameter_id,
        "group_a": label_a,
        "group_b": label_b,
        "n_a": int(values_a.notna().sum()),
        "n_b": int(values_b.notna().sum()),
        "median_a": median_a,
        "median_b": median_b,
        "median_difference_a_minus_b": median_a - median_b,
        "robust_effect_size": _robust_effect(median_a, q25_a, q75_a, median_b, q25_b, q75_b),
    }


def build_parameter_contrasts(parameters: pd.DataFrame, membership: pd.DataFrame, priors: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    set_frame = _parameter_set_frame(
        parameters,
        membership,
        priors,
        sets=("accepted", "near_frontier_absolute", "near_frontier_relative"),
    )
    family_pairs = (
        ("persistent_joint_cause", "transient_perfect_storm"),
        ("persistent_joint_cause", "climbing_only"),
        ("transient_perfect_storm", "climbing_only"),
    )
    for (variant_id, proposal_set, parameter_id), group in set_frame.groupby(
        ["variant_id", "proposal_set", "parameter_id"],
        dropna=False,
    ):
        for family_a, family_b in family_pairs:
            values_a = group.loc[group["family_id"] == family_a, "value_natural"]
            values_b = group.loc[group["family_id"] == family_b, "value_natural"]
            if values_a.empty or values_b.empty:
                continue
            rows.append(
                _contrast_row(
                    "family_pair",
                    str(variant_id),
                    str(proposal_set),
                    str(parameter_id),
                    family_a,
                    values_a,
                    family_b,
                    values_b,
                )
            )

    stage_b = membership.loc[membership["has_stage_b_scores"]].copy()
    stage_b["proposal_set"] = np.where(stage_b["in_accepted"], "accepted", "stage_b_rejected")
    stage_frame = _with_prior_positions(
        parameters.merge(
            stage_b[[*PROPOSAL_KEY_COLUMNS, "proposal_set"]],
            on=PROPOSAL_KEY_COLUMNS,
            how="inner",
        ),
        priors,
    )
    for (variant_id, family_id, parameter_id), group in stage_frame.groupby(
        ["variant_id", "family_id", "parameter_id"],
        dropna=False,
    ):
        accepted_values = group.loc[group["proposal_set"] == "accepted", "value_natural"]
        rejected_values = group.loc[group["proposal_set"] == "stage_b_rejected", "value_natural"]
        if accepted_values.empty or rejected_values.empty:
            continue
        rows.append(
            _contrast_row(
                "accepted_vs_stage_b_rejected",
                str(variant_id),
                "accepted_vs_stage_b_rejected",
                str(parameter_id),
                f"{family_id}:accepted",
                accepted_values,
                f"{family_id}:stage_b_rejected",
                rejected_values,
            )
        )

    return pd.DataFrame(rows).sort_values(["contrast_type", "variant_id", "proposal_set", "parameter_id"]).reset_index(
        drop=True
    ) if rows else pd.DataFrame()


def build_distance_audit(membership: pd.DataFrame) -> pd.DataFrame:
    stage_b = membership.loc[membership["has_stage_b_scores"]].copy()
    if stage_b.empty:
        return pd.DataFrame()
    target_best = (
        stage_b.sort_values(["variant_id", "seed", "family_id", "target_sum", "proposal_id"])
        .groupby(["variant_id", "seed", "family_id"], as_index=False)
        .head(1)
        .copy()
    )
    target_best["target_sum_family_rank"] = target_best.groupby(["variant_id", "seed"])["target_sum"].rank(
        method="min"
    )
    stochastic_best = (
        stage_b.sort_values(
            ["variant_id", "seed", "family_id", "stochastic_overall_distance_median", "proposal_id"]
        )
        .groupby(["variant_id", "seed", "family_id"], as_index=False)
        .head(1)
        .copy()
    )
    stochastic_best["stochastic_distance_family_rank"] = stochastic_best.groupby(["variant_id", "seed"])[
        "stochastic_overall_distance_median"
    ].rank(method="min")
    counts = (
        membership.groupby(["variant_id", "seed", "family_id"], as_index=False)
        .agg(
            stage_b_valid_count=("has_stage_b_scores", "sum"),
            accepted_count=("in_accepted", "sum"),
            near_frontier_absolute_count=("in_near_frontier_absolute", "sum"),
            near_frontier_relative_count=("in_near_frontier_relative", "sum"),
        )
    )
    target_cols = [
        "variant_id",
        "seed",
        "family_id",
        "family_label",
        "proposal_id",
        "target_sum",
        "target_sum_family_rank",
        "stochastic_overall_distance_median",
    ]
    stochastic_cols = [
        "variant_id",
        "seed",
        "family_id",
        "proposal_id",
        "stochastic_overall_distance_median",
        "stochastic_distance_family_rank",
        "target_sum",
    ]
    audit = target_best[target_cols].rename(
        columns={
            "proposal_id": "best_target_sum_proposal_id",
            "target_sum": "best_target_sum",
            "stochastic_overall_distance_median": "stochastic_distance_for_best_target_sum",
        }
    )
    audit = audit.merge(
        stochastic_best[stochastic_cols].rename(
            columns={
                "proposal_id": "best_stochastic_distance_proposal_id",
                "stochastic_overall_distance_median": "best_stochastic_distance",
                "target_sum": "target_sum_for_best_stochastic_distance",
            }
        ),
        on=["variant_id", "seed", "family_id"],
        how="left",
    )
    audit = audit.merge(counts, on=["variant_id", "seed", "family_id"], how="left")
    audit["same_best_proposal_under_both_distances"] = (
        audit["best_target_sum_proposal_id"] == audit["best_stochastic_distance_proposal_id"]
    )
    audit["rank_delta_stochastic_minus_target"] = (
        audit["stochastic_distance_family_rank"] - audit["target_sum_family_rank"]
    )
    audit["global_winner_by_target_sum"] = audit["target_sum_family_rank"] == 1
    return audit.sort_values(["variant_id", "seed", "target_sum_family_rank", "family_id"]).reset_index(drop=True)


def build_target_family_summary(targets: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    assignments = _expand_proposal_sets(membership)
    if assignments.empty:
        return pd.DataFrame()
    stage_b = targets.loc[targets["stage"] == "stage_b"].copy()
    stage_b["weighted_penalty"] = pd.to_numeric(stage_b["weighted_penalty"], errors="coerce")
    stage_b["raw_penalty"] = pd.to_numeric(stage_b["raw_penalty"], errors="coerce")
    proposal_targets = (
        stage_b.groupby(["variant_id", "seed", "proposal_id", "family_id", "scenario_id", "target_id"], as_index=False)
        .agg(
            median_weighted_penalty=("weighted_penalty", "median"),
            median_raw_penalty=("raw_penalty", "median"),
            replicate_count=("replicate_index", "nunique"),
        )
    )
    proposal_targets = proposal_targets.merge(
        assignments[[*PROPOSAL_KEY_COLUMNS, "family_label", "proposal_set"]],
        on=PROPOSAL_KEY_COLUMNS,
        how="inner",
    )
    rows: list[dict[str, Any]] = []
    group_cols = ["variant_id", "seed", "family_id", "family_label", "proposal_set", "scenario_id", "target_id"]
    for key, group in proposal_targets.groupby(group_cols, dropna=False):
        values = group["median_weighted_penalty"]
        rows.append(
            {
                **dict(zip(group_cols, key, strict=False)),
                "n_proposals": int(group["proposal_id"].nunique()),
                "median_weighted_penalty": _quantile(values, 0.50),
                "q10_weighted_penalty": _quantile(values, 0.10),
                "q90_weighted_penalty": _quantile(values, 0.90),
                "median_raw_penalty": _quantile(group["median_raw_penalty"], 0.50),
                "pass_fraction_zero_weighted_penalty": float((values <= 0).mean()),
                "min_replicate_count": int(group["replicate_count"].min()),
            }
        )
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True) if rows else pd.DataFrame()


def _selected_for_trajectory(membership: pd.DataFrame, *, trajectory_sample: int, seed: int) -> pd.DataFrame:
    winner_mask = membership["in_family_winners"] | membership["in_global_winners"]
    selected = [membership.loc[winner_mask].copy()]
    if trajectory_sample > 0:
        accepted = membership.loc[membership["in_accepted"]].copy()
        sampled = []
        for _, group in accepted.groupby(["variant_id", "seed"], dropna=False):
            if len(group) <= trajectory_sample:
                sampled.append(group)
            else:
                sampled.append(group.sample(n=trajectory_sample, random_state=seed))
        if sampled:
            selected.append(pd.concat(sampled, ignore_index=True))
    combined = pd.concat(selected, ignore_index=True) if selected else pd.DataFrame()
    return combined.drop_duplicates(subset=PROPOSAL_KEY_COLUMNS).reset_index(drop=True)


def _derive_pressure_columns(frame: pd.DataFrame, params: Any) -> pd.DataFrame:
    out = frame.copy()
    h = pd.to_numeric(out["H"], errors="coerce")
    trout_component_lake = params.value("PR020") * out["T"] * out["P"]
    climbing_component_lake = params.value("PR027") * out["C_L"]
    trout_component_refuge = params.value("PR021") * out["T"] * out["P"] * (1 - params.value("PR034"))
    climbing_component_refuge = params.value("PR028") * out["C_R"] * (1 - params.value("PR034"))
    out["lake_trout_pressure"] = h * trout_component_lake
    out["lake_climbing_pressure"] = h * climbing_component_lake
    out["refuge_trout_pressure"] = h * trout_component_refuge
    out["refuge_climbing_pressure"] = h * climbing_component_refuge
    out["lake_biotic_pressure"] = out["lake_trout_pressure"] + out["lake_climbing_pressure"]
    out["refuge_biotic_pressure"] = out["refuge_trout_pressure"] + out["refuge_climbing_pressure"]
    out["lake_habitat_exposure"] = params.value("PR033") * h
    out["lake_total_exposure"] = out["lake_habitat_exposure"] + out["lake_biotic_pressure"]
    out["refuge_total_exposure"] = out["refuge_biotic_pressure"]
    out["lake_trout_share"] = trout_component_lake / (trout_component_lake + climbing_component_lake + 1e-12)
    out["lake_climbing_share"] = climbing_component_lake / (trout_component_lake + climbing_component_lake + 1e-12)
    out["refuge_trout_share"] = trout_component_refuge / (trout_component_refuge + climbing_component_refuge + 1e-12)
    out["refuge_climbing_share"] = climbing_component_refuge / (
        trout_component_refuge + climbing_component_refuge + 1e-12
    )
    return out


def _build_selected_trajectories(
    membership: pd.DataFrame,
    parameters: pd.DataFrame,
    *,
    trajectory_sample: int,
    seed: int,
) -> pd.DataFrame:
    selected = _selected_for_trajectory(membership, trajectory_sample=trajectory_sample, seed=seed)
    if selected.empty:
        return pd.DataFrame()
    model_inputs = load_model_inputs(ROOT / "data")
    frames: list[pd.DataFrame] = []
    config = SimulationConfig(stochastic=False, record_forcing=True)
    for row in selected.to_dict(orient="records"):
        proposal_params = parameters.loc[
            (parameters["variant_id"] == row["variant_id"])
            & (parameters["seed"] == row["seed"])
            & (parameters["proposal_id"] == row["proposal_id"])
            & (parameters["family_id"] == row["family_id"])
        ].copy()
        if proposal_params.empty:
            continue
        resolved = build_resolved_parameters_from_sample(model_inputs, str(row["family_id"]), proposal_params)
        simulation_seed = int(row["proposal_seed"]) if pd.notna(row.get("proposal_seed")) else int(row["seed"])
        result = run_historical_simulation(resolved, str(row["family_id"]), config, seed=simulation_seed)
        trajectory = result.trajectory_table.merge(
            result.forcing_table[["year", "H", "spawn_habitat_multiplier"]],
            on="year",
            how="left",
        )
        trajectory = _derive_pressure_columns(trajectory, resolved)
        trajectory["simulation_seed"] = simulation_seed
        trajectory["seed"] = int(row["seed"])
        for column in [
            "module4_run_id",
            "variant_id",
            "run_dir_name",
            "proposal_id",
            "proposal_index",
            "proposal_seed",
            "family_id",
            "family_label",
            "target_sum",
            "stochastic_overall_distance_median",
        ]:
            trajectory[column] = row.get(column)
        frames.append(trajectory)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _expand_trajectory_sets(trajectories: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    assignments = _expand_proposal_sets(membership)
    if assignments.empty or trajectories.empty:
        return pd.DataFrame()
    return trajectories.merge(
        assignments[[*PROPOSAL_KEY_COLUMNS, "proposal_set"]],
        on=PROPOSAL_KEY_COLUMNS,
        how="inner",
    )


def build_pressure_landmarks(trajectories_by_set: pd.DataFrame) -> pd.DataFrame:
    if trajectories_by_set.empty:
        return pd.DataFrame()
    proposal_window_rows: list[dict[str, Any]] = []
    pressure_cols = [
        "lake_trout_pressure",
        "lake_climbing_pressure",
        "refuge_trout_pressure",
        "refuge_climbing_pressure",
        "lake_biotic_pressure",
        "refuge_biotic_pressure",
        "lake_total_exposure",
        "refuge_total_exposure",
    ]
    share_cols = ["lake_trout_share", "lake_climbing_share", "refuge_trout_share", "refuge_climbing_share"]
    for window_label, start_year, end_year in PRESSURE_WINDOWS:
        window = trajectories_by_set.loc[trajectories_by_set["year"].between(start_year, end_year)].copy()
        if window.empty:
            continue
        for key, group in window.groupby(
            ["variant_id", "seed", "family_id", "family_label", "proposal_set", "proposal_id"],
            dropna=False,
        ):
            record = dict(
                zip(
                    ["variant_id", "seed", "family_id", "family_label", "proposal_set", "proposal_id"],
                    key,
                    strict=False,
                )
            )
            record.update({"window_label": window_label, "start_year": start_year, "end_year": end_year})
            for column in pressure_cols:
                record[f"cumulative_{column}"] = float(pd.to_numeric(group[column], errors="coerce").sum())
            for column in share_cols:
                record[f"mean_{column}"] = float(pd.to_numeric(group[column], errors="coerce").mean())
            proposal_window_rows.append(record)
    proposal_windows = pd.DataFrame(proposal_window_rows)
    if proposal_windows.empty:
        return proposal_windows
    rows: list[dict[str, Any]] = []
    group_cols = ["variant_id", "seed", "family_id", "family_label", "proposal_set", "window_label", "start_year", "end_year"]
    metric_cols = [column for column in proposal_windows.columns if column.startswith(("cumulative_", "mean_"))]
    for key, group in proposal_windows.groupby(group_cols, dropna=False):
        record = dict(zip(group_cols, key, strict=False))
        record["n_proposals"] = int(group["proposal_id"].nunique())
        for column in metric_cols:
            record[f"median_{column}"] = _quantile(group[column], 0.50)
            record[f"q10_{column}"] = _quantile(group[column], 0.10)
            record[f"q90_{column}"] = _quantile(group[column], 0.90)
        rows.append(record)
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True)


def build_trajectory_landmarks(trajectories_by_set: pd.DataFrame) -> pd.DataFrame:
    if trajectories_by_set.empty:
        return pd.DataFrame()
    landmark = trajectories_by_set.loc[trajectories_by_set["year"].isin(LANDMARK_YEARS)].copy()
    rows: list[dict[str, Any]] = []
    group_cols = ["variant_id", "seed", "family_id", "family_label", "proposal_set", "year"]
    value_cols = [
        "N_L",
        "N_R",
        "N_total",
        "pedder_lake_index",
        "pedder_refuge_index",
        "T",
        "P",
        "C_L",
        "C_R",
        "U",
        "H",
        "lake_biotic_pressure",
        "refuge_biotic_pressure",
    ]
    for key, group in landmark.groupby(group_cols, dropna=False):
        record = dict(zip(group_cols, key, strict=False))
        record["n_proposals"] = int(group["proposal_id"].nunique())
        for column in value_cols:
            record[f"median_{column}"] = _quantile(group[column], 0.50)
            record[f"q10_{column}"] = _quantile(group[column], 0.10)
            record[f"q90_{column}"] = _quantile(group[column], 0.90)
        for column in ["lake_present", "refuge_present", "total_present"]:
            record[f"{column}_fraction"] = float(pd.to_numeric(group[column], errors="coerce").mean())
        rows.append(record)
    return pd.DataFrame(rows).sort_values(group_cols).reset_index(drop=True) if rows else pd.DataFrame()


def build_family_decision_table(
    membership: pd.DataFrame,
    nuisance_audit: pd.DataFrame,
    pressure_landmarks: pd.DataFrame,
    parameter_summary: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    winners = membership.loc[membership["in_global_winners"]].copy()
    for family_id in sorted(membership["family_id"].unique()):
        accepted_count = int(membership.loc[(membership["family_id"] == family_id) & membership["in_accepted"]].shape[0])
        global_wins = int(winners.loc[winners["family_id"] == family_id].shape[0])
        baseline_wins = int(
            winners.loc[(winners["family_id"] == family_id) & (winners["variant_id"] == "baseline_current")].shape[0]
        )
        soft_wins = int(
            winners.loc[(winners["family_id"] == family_id) & (winners["variant_id"] == "late_bridge_soft")].shape[0]
        )
        stable_rank = "yes" if baseline_wins >= 3 and soft_wins >= 3 else "partial" if global_wins > 0 else "no"
        accepted_frontier = "yes" if accepted_count > 0 else "no"

        family_nuisance = nuisance_audit.loc[
            (nuisance_audit["family_id"] == family_id) & (nuisance_audit["proposal_set"] == "accepted")
        ]
        max_boundary = (
            float(family_nuisance["near_either_bound_fraction"].max()) if not family_nuisance.empty else np.nan
        )
        nuisance_status = (
            "uncertain_no_accepted_set"
            if np.isnan(max_boundary)
            else "high_boundary_risk"
            if max_boundary >= 0.50
            else "moderate_boundary_risk"
            if max_boundary >= 0.25
            else "low_boundary_risk"
        )

        family_pressure = pressure_landmarks.loc[
            (pressure_landmarks["family_id"] == family_id) & (pressure_landmarks["proposal_set"] == "accepted")
        ]
        pressure_status = "not_applicable_negative_reference" if accepted_count == 0 else "uncertain"
        if not family_pressure.empty:
            lake_trout = family_pressure.filter(like="median_cumulative_lake_trout_pressure").max(axis=1).max()
            lake_climbing = family_pressure.filter(like="median_cumulative_lake_climbing_pressure").max(axis=1).max()
            refuge_climbing = family_pressure.filter(like="median_cumulative_refuge_climbing_pressure").max(axis=1).max()
            if family_id == "persistent_joint_cause":
                pressure_status = "yes" if lake_trout > 0 and (lake_climbing > 0 or refuge_climbing > 0) else "no"
            elif family_id == "climbing_only":
                pressure_status = "yes" if lake_climbing > 0 or refuge_climbing > 0 else "no"
            elif family_id == "transient_perfect_storm":
                pressure_status = "yes" if lake_trout > 0 and (lake_climbing > 0 or refuge_climbing > 0) else "uncertain"
            else:
                pressure_status = "not_applicable_negative_reference"

        pr018 = parameter_summary.loc[
            (parameter_summary["family_id"] == family_id)
            & (parameter_summary["proposal_set"] == "accepted")
            & (parameter_summary["parameter_id"] == "PR018")
        ]
        transient_signature = "not_applicable"
        if family_id == "transient_perfect_storm":
            median_pr018 = float(pr018["median_value"].median()) if not pr018.empty else np.nan
            transient_signature = "yes" if np.isfinite(median_pr018) and median_pr018 > 1.5 else "uncertain"

        if family_id == "persistent_joint_cause" and stable_rank == "yes" and accepted_frontier == "yes":
            module5_role = "primary"
        elif family_id in MECHANISM_RICH_FAMILIES and accepted_frontier == "yes":
            module5_role = "sensitivity"
        else:
            module5_role = "negative_reference"

        rows.append(
            {
                "family_id": family_id,
                "accepted_proposal_count": accepted_count,
                "global_winner_count": global_wins,
                "baseline_current_winner_count": baseline_wins,
                "late_bridge_soft_winner_count": soft_wins,
                "stable_rank": stable_rank,
                "accepted_frontier": accepted_frontier,
                "nuisance_boundary_status": nuisance_status,
                "max_accepted_nuisance_boundary_fraction": max_boundary,
                "coherent_pressure_history": pressure_status,
                "transient_overshoot_signature": transient_signature,
                "module5_role": module5_role,
                "decision_note": _decision_note(family_id, module5_role, stable_rank, nuisance_status, pressure_status),
            }
        )
    return pd.DataFrame(rows).sort_values(["module5_role", "family_id"]).reset_index(drop=True)


def _decision_note(
    family_id: str,
    module5_role: str,
    stable_rank: str,
    nuisance_status: str,
    pressure_status: str,
) -> str:
    if module5_role == "primary":
        return "Stable baseline and combined-late winner; carry as the primary Module 5 ensemble unless later checks overturn nuisance or pressure diagnostics."
    if module5_role == "sensitivity" and family_id == "climbing_only":
        return "Accepted and locally competitive, but carry as a sensitivity case unless combined-late ranking and nuisance checks strengthen."
    if module5_role == "sensitivity" and family_id == "transient_perfect_storm":
        return "Accepted frontier member; carry as a joint-cause sensitivity case and test whether its transient signature is biologically distinct."
    if module5_role == "negative_reference":
        return "No accepted Module 4 frontier support under the current target/prior framework; keep only as a negative reference."
    return f"Rank={stable_rank}; nuisance={nuisance_status}; pressure={pressure_status}."


def _format_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return "NA"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.3f}"
    if isinstance(value, (bool, np.bool_)):
        return "yes" if bool(value) else "no"
    return str(value)


def _markdown_table(frame: pd.DataFrame, columns: list[str], *, max_rows: int = 20) -> str:
    if frame.empty:
        return "_No rows available._"
    rows = frame.head(max_rows).to_dict(orient="records")
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(_format_value(row.get(column)) for column in columns) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def render_module4_5_review(
    *,
    validation: Module4ArtifactValidation,
    membership: pd.DataFrame,
    distance_audit: pd.DataFrame,
    nuisance_audit: pd.DataFrame,
    target_family_summary: pd.DataFrame,
    pressure_landmarks: pd.DataFrame,
    trajectory_landmarks: pd.DataFrame,
    family_decision_table: pd.DataFrame,
    near_frontier_delta: float,
    near_frontier_relative: float,
    trajectory_sample: int,
    seed: int,
) -> str:
    set_counts = (
        _expand_proposal_sets(membership)
        .groupby(["proposal_set", "family_id"], as_index=False)
        .agg(proposal_count=("proposal_id", "size"))
        .sort_values(["proposal_set", "family_id"])
    )
    winners = distance_audit.loc[distance_audit["target_sum_family_rank"] == 1].copy()
    late_targets = target_family_summary.loc[
        target_family_summary["target_id"].isin(["CT007", "CT009", "CT010"])
        & target_family_summary["proposal_set"].isin(["accepted", "near_frontier_absolute"])
    ].copy()
    late_targets = late_targets.sort_values(
        ["variant_id", "seed", "proposal_set", "target_id", "median_weighted_penalty"]
    )
    accepted_nuisance = nuisance_audit.loc[nuisance_audit["proposal_set"] == "accepted"].copy()
    accepted_nuisance = accepted_nuisance.sort_values(
        ["near_either_bound_fraction", "variant_id", "family_id"],
        ascending=[False, True, True],
    )
    pressure_snapshot = pressure_landmarks.loc[
        pressure_landmarks["proposal_set"].isin(["accepted", "family_winners"])
    ].copy()
    pressure_snapshot = pressure_snapshot.sort_values(["variant_id", "seed", "family_id", "window_label"])
    trajectory_snapshot = trajectory_landmarks.loc[
        trajectory_landmarks["proposal_set"].isin(["accepted", "family_winners"])
        & trajectory_landmarks["year"].isin([1977, 1991, 1996, 2002])
    ].copy()
    trajectory_snapshot = trajectory_snapshot.sort_values(["variant_id", "seed", "family_id", "year"])
    decision = family_decision_table.copy()
    primary = decision.loc[decision["module5_role"] == "primary", "family_id"].tolist()
    sensitivities = decision.loc[decision["module5_role"] == "sensitivity", "family_id"].tolist()

    lines = [
        "# Module 4.5 Mechanism Interpretation Review",
        "",
        "## Provenance And Run Contract",
        "",
        (
            f"Validated `{validation.record_count}` raw Module 4 artifact records across "
            f"`{validation.run_count}` variant/seed runs before interpretation."
        ),
        "",
        f"- Raw manifest: `{validation.manifest_path}`",
        f"- Module 4 root: `{validation.module4_root}`",
        f"- Near-frontier absolute margin: `{near_frontier_delta:g}` target-sum units",
        f"- Near-frontier relative margin: `{near_frontier_relative:g}` times the best target sum",
        f"- Accepted trajectory sample cap per variant/seed: `{trajectory_sample}`",
        f"- Deterministic landmark regeneration seed: `{seed}`",
        "",
        "## Proposal Sets",
        "",
        (
            "Target-sum distance is reconstructed as the sum across targets of Stage B "
            "replicate-median weighted penalties. The accepted set remains the main "
            "biological ensemble; near-frontier and winner sets are diagnostics."
        ),
        "",
        _markdown_table(set_counts, ["proposal_set", "family_id", "proposal_count"], max_rows=50),
        "",
        "## Distance Audit",
        "",
        (
            "`best_target_sum` and `best_stochastic_distance` are deliberately reported "
            "side by side because Module 4 family ranking used target-sum reconstruction."
        ),
        "",
        _markdown_table(
            winners,
            [
                "variant_id",
                "seed",
                "family_id",
                "best_target_sum_proposal_id",
                "best_target_sum",
                "best_stochastic_distance_proposal_id",
                "best_stochastic_distance",
                "same_best_proposal_under_both_distances",
            ],
            max_rows=20,
        ),
        "",
        "## Late-Target Summary",
        "",
        _markdown_table(
            late_targets,
            [
                "variant_id",
                "seed",
                "family_id",
                "proposal_set",
                "target_id",
                "n_proposals",
                "median_weighted_penalty",
                "pass_fraction_zero_weighted_penalty",
            ],
            max_rows=30,
        ),
        "",
        "## Nuisance Diagnostic",
        "",
        _markdown_table(
            accepted_nuisance,
            [
                "variant_id",
                "family_id",
                "parameter_id",
                "n_proposals",
                "median_value",
                "near_either_bound_fraction",
                "boundary_status",
                "spearman_value_vs_target_sum",
            ],
            max_rows=30,
        ),
        "",
        "## Derived Pressure Landmarks",
        "",
        _markdown_table(
            pressure_snapshot,
            [
                "variant_id",
                "seed",
                "family_id",
                "proposal_set",
                "window_label",
                "n_proposals",
                "median_cumulative_lake_trout_pressure",
                "median_cumulative_lake_climbing_pressure",
                "median_cumulative_refuge_climbing_pressure",
            ],
            max_rows=30,
        ),
        "",
        "## Trajectory Landmarks",
        "",
        _markdown_table(
            trajectory_snapshot,
            [
                "variant_id",
                "seed",
                "family_id",
                "proposal_set",
                "year",
                "n_proposals",
                "median_N_total",
                "median_N_L",
                "median_N_R",
                "total_present_fraction",
            ],
            max_rows=30,
        ),
        "",
        "## Module 5 Decision Table",
        "",
        _markdown_table(
            family_decision_table,
            [
                "family_id",
                "accepted_proposal_count",
                "global_winner_count",
                "stable_rank",
                "nuisance_boundary_status",
                "coherent_pressure_history",
                "module5_role",
            ],
            max_rows=20,
        ),
        "",
        "## Interpretation",
        "",
        (
            f"Primary Module 5 ensemble under this diagnostic rule: `{primary}`. "
            f"Families retained as sensitivity cases: `{sensitivities}`."
        ),
        (
            "This is still a mechanism audit, not a posterior claim. The strongest current "
            "claim is whether a family survives target-sum, nuisance, and derived-pressure "
            "checks well enough to seed counterfactual analysis."
        ),
        (
            "`habitat_only_null` and `trout_only` remain useful negative references when "
            "their accepted-frontier support is absent under the current target/prior framework."
        ),
        "",
        "## Generated Artifacts",
        "",
        *[f"- `{output}`" for output in MODULE4_5_MANDATORY_OUTPUTS],
        "",
    ]
    return "\n".join(lines)


def render_module4_5_review_from_outputs(publish_root: Path) -> Path:
    paths = module4_5_output_paths(publish_root)
    required_csvs = {
        "membership": paths["data/module4_5_proposal_set_membership.csv"],
        "distance": paths["data/module4_5_distance_audit.csv"],
        "nuisance": paths["data/module4_5_nuisance_audit.csv"],
        "target": paths["data/module4_5_target_family_summary.csv"],
        "pressure": paths["data/module4_5_pressure_landmarks.csv"],
        "trajectory": paths["data/module4_5_trajectory_landmarks.csv"],
        "decision": paths["data/module4_5_family_decision_table.csv"],
    }
    missing = [path for path in required_csvs.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Cannot re-render Module 4.5 review; missing derived tables: {missing}")
    membership = pd.read_csv(required_csvs["membership"])
    distance = pd.read_csv(required_csvs["distance"])
    nuisance = pd.read_csv(required_csvs["nuisance"])
    target = pd.read_csv(required_csvs["target"])
    pressure = pd.read_csv(required_csvs["pressure"])
    trajectory = pd.read_csv(required_csvs["trajectory"])
    decision = pd.read_csv(required_csvs["decision"])
    manifest_path = publish_root / "data" / "module4_raw_artifact_manifest.csv"
    if not manifest_path.exists():
        manifest_path = ROOT / "data" / "module4_raw_artifact_manifest.csv"
    module4_root = Path("outputs") / "remote" / "module4_observation_sensitivity_20260522T101942Z"
    if not module4_root.exists():
        module4_root = ROOT / "outputs" / "remote" / "module4_observation_sensitivity_20260522T101942Z"
    validation = validate_module4_raw_artifact_manifest(
        manifest_path,
        module4_root,
        verify_hashes=False,
    )
    review = render_module4_5_review(
        validation=validation,
        membership=membership,
        distance_audit=distance,
        nuisance_audit=nuisance,
        target_family_summary=target,
        pressure_landmarks=pressure,
        trajectory_landmarks=trajectory,
        family_decision_table=decision,
        near_frontier_delta=float(membership["near_frontier_delta"].dropna().iloc[0]),
        near_frontier_relative=float(membership["near_frontier_relative"].dropna().iloc[0]),
        trajectory_sample=100,
        seed=20260523,
    )
    paths["docs/module4_5_mechanism_interpretation_review.md"].parent.mkdir(parents=True, exist_ok=True)
    paths["docs/module4_5_mechanism_interpretation_review.md"].write_text(review, encoding="utf-8")
    return paths["docs/module4_5_mechanism_interpretation_review.md"]


def generate_module4_5_outputs(
    *,
    module4_root: Path,
    manifest_path: Path,
    publish_root: Path,
    near_frontier_delta: float = 10.0,
    near_frontier_relative: float = 1.05,
    trajectory_sample: int = 100,
    seed: int = 20260523,
    verify_hashes: bool = False,
) -> Module45GenerationResult:
    validation = validate_module4_raw_artifact_manifest(
        manifest_path,
        module4_root,
        verify_hashes=verify_hashes,
    )
    if not validation.passed:
        problems = {
            "missing_files": validation.missing_files,
            "missing_roles": validation.missing_roles,
            "hash_mismatches": validation.hash_mismatches,
        }
        raise ValueError(f"Module 4 raw artifact validation failed: {problems}")

    manifest_rows = read_raw_artifact_manifest(manifest_path)
    proposals, parameters, targets, family_summary, accepted, run_records = _load_module4_tables(
        manifest_rows,
        module4_root,
    )
    model_inputs = load_model_inputs(ROOT / "data")
    membership = build_proposal_set_membership(
        proposals,
        targets,
        near_frontier_delta=near_frontier_delta,
        near_frontier_relative=near_frontier_relative,
    )
    distance_audit = build_distance_audit(membership)
    parameter_summary = build_parameter_summary(parameters, membership, model_inputs.parameter_priors)
    parameter_contrasts = build_parameter_contrasts(parameters, membership, model_inputs.parameter_priors)
    nuisance_audit = build_nuisance_audit(parameters, membership, model_inputs.parameter_priors)
    target_family_summary = build_target_family_summary(targets, membership)
    selected_trajectories = _build_selected_trajectories(
        membership,
        parameters,
        trajectory_sample=trajectory_sample,
        seed=seed,
    )
    trajectories_by_set = _expand_trajectory_sets(selected_trajectories, membership)
    pressure_landmarks = build_pressure_landmarks(trajectories_by_set)
    trajectory_landmarks = build_trajectory_landmarks(trajectories_by_set)
    family_decision_table = build_family_decision_table(
        membership,
        nuisance_audit,
        pressure_landmarks,
        parameter_summary,
    )

    paths = module4_5_output_paths(publish_root)
    tables: dict[str, pd.DataFrame] = {
        "data/module4_5_proposal_set_membership.csv": membership,
        "data/module4_5_distance_audit.csv": distance_audit,
        "data/module4_5_parameter_summary.csv": parameter_summary,
        "data/module4_5_parameter_contrasts.csv": parameter_contrasts,
        "data/module4_5_nuisance_audit.csv": nuisance_audit,
        "data/module4_5_target_family_summary.csv": target_family_summary,
        "data/module4_5_pressure_landmarks.csv": pressure_landmarks,
        "data/module4_5_trajectory_landmarks.csv": trajectory_landmarks,
        "data/module4_5_family_decision_table.csv": family_decision_table,
    }
    row_counts: dict[str, int] = {
        "module4_family_summary_rows": int(len(family_summary)),
        "module4_accepted_rows": int(len(accepted)),
        "module4_run_records": int(len(run_records)),
    }
    for output, table in tables.items():
        path = paths[output]
        path.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(path, index=False)
        row_counts[output] = int(len(table))

    review = render_module4_5_review(
        validation=validation,
        membership=membership,
        distance_audit=distance_audit,
        nuisance_audit=nuisance_audit,
        target_family_summary=target_family_summary,
        pressure_landmarks=pressure_landmarks,
        trajectory_landmarks=trajectory_landmarks,
        family_decision_table=family_decision_table,
        near_frontier_delta=near_frontier_delta,
        near_frontier_relative=near_frontier_relative,
        trajectory_sample=trajectory_sample,
        seed=seed,
    )
    review_path = paths["docs/module4_5_mechanism_interpretation_review.md"]
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(review, encoding="utf-8")
    row_counts["docs/module4_5_mechanism_interpretation_review.md"] = len(review.splitlines())

    return Module45GenerationResult(validation=validation, output_paths=paths, row_counts=row_counts)
