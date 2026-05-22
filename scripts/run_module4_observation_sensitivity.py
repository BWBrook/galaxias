from __future__ import annotations

import argparse
import json
from pathlib import Path
from shutil import rmtree
from typing import Any

import numpy as np
import pandas as pd

from galaxias_model import Module3Config, load_model_inputs, observation_bridge_variant_ids, run_module3_calibration


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VARIANTS = observation_bridge_variant_ids()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or summarize Module 4 observation-bridge sensitivity calibrations.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "module4" / "observation_sensitivity")
    parser.add_argument("--publish-root", type=Path, default=None)
    parser.add_argument("--variants", nargs="*", default=list(DEFAULT_VARIANTS))
    parser.add_argument("--seeds", nargs="*", type=int, default=[20260410])
    parser.add_argument("--families", nargs="*", default=None)
    parser.add_argument("--stage-a-draws-per-family", type=int, default=1000)
    parser.add_argument("--stage-a-keep-per-family", type=int, default=100)
    parser.add_argument("--stage-b-historical-replicates", type=int, default=20)
    parser.add_argument("--final-acceptance-fraction", type=float, default=0.10)
    parser.add_argument("--final-acceptance-cap", type=int, default=50)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--summarize-only", action="store_true")
    parser.add_argument("--clean", action="store_true", help="Remove an existing variant/seed output before rerunning it.")
    return parser.parse_args()


def _validate_variants(variants: list[str]) -> list[str]:
    known = set(observation_bridge_variant_ids())
    unknown = [variant for variant in variants if variant not in known]
    if unknown:
        raise ValueError(f"Unknown Module 4 variants: {unknown}. Expected one of {sorted(known)}")
    return variants


def _run_dir(output_dir: Path, variant: str, seed: int) -> Path:
    return output_dir / f"{variant}_seed{seed}"


def _run_one(args: argparse.Namespace, variant: str, seed: int) -> Path:
    run_dir = _run_dir(args.output_dir, variant, seed)
    if args.clean and run_dir.exists():
        rmtree(run_dir)
    data_dir = ROOT / "data"
    model_inputs = load_model_inputs(data_dir)
    config = Module3Config(
        families=tuple(args.families) if args.families else Module3Config().families,
        stage_a_draws_per_family=args.stage_a_draws_per_family,
        stage_a_keep_per_family=args.stage_a_keep_per_family,
        stage_b_historical_replicates=args.stage_b_historical_replicates,
        final_acceptance_fraction=args.final_acceptance_fraction,
        final_acceptance_cap=args.final_acceptance_cap,
        workers=args.workers,
        batch_size=args.batch_size,
        master_seed=seed,
        stochastic_baselines=False,
        observation_bridge_variant=variant,
        output_dir=run_dir,
        resume=args.resume,
    )
    run_module3_calibration(model_inputs, config)
    return run_dir


def _load_manifest(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "run_manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}


def _run_dirs(output_dir: Path, variants: list[str], seeds: list[int]) -> list[Path]:
    return [_run_dir(output_dir, variant, seed) for variant in variants for seed in seeds]


def _normalise_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def _load_run_tables(run_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    manifest = _load_manifest(run_dir)
    config = manifest.get("config", {})
    variant = str(config.get("observation_bridge_variant", run_dir.name.split("_seed")[0]))
    seed = int(config.get("master_seed", run_dir.name.rsplit("seed", 1)[-1]))

    family = pd.read_csv(run_dir / "family_summary.csv")
    proposals = pd.read_csv(run_dir / "proposal_summary.csv.gz")
    targets = pd.read_csv(run_dir / "target_scores.csv.gz")
    accepted = pd.read_csv(run_dir / "accepted_proposals.csv")
    for frame in (family, proposals, targets, accepted):
        frame["variant_id"] = variant
        frame["seed"] = seed
        frame["run_dir"] = str(run_dir)
    proposals["accepted_final"] = _normalise_bool(proposals["accepted_final"])
    if "accepted_final" in accepted:
        accepted["accepted_final"] = _normalise_bool(accepted["accepted_final"])
    return family, proposals, targets, accepted, manifest


def _proposal_target_sums(targets: pd.DataFrame, proposals: pd.DataFrame) -> pd.DataFrame:
    stage_b = targets.loc[targets["stage"] == "stage_b"].copy()
    stage_b["weighted_penalty"] = pd.to_numeric(stage_b["weighted_penalty"], errors="coerce")
    medians = (
        stage_b.groupby(["variant_id", "seed", "proposal_id", "family_id", "target_id"], as_index=False)[
            "weighted_penalty"
        ]
        .median()
        .rename(columns={"weighted_penalty": "median_weighted_penalty"})
    )
    sums = (
        medians.groupby(["variant_id", "seed", "proposal_id", "family_id"], as_index=False)[
            "median_weighted_penalty"
        ]
        .sum()
        .rename(columns={"median_weighted_penalty": "median_target_sum"})
    )
    meta_cols = [
        "variant_id",
        "seed",
        "proposal_id",
        "family_id",
        "accepted_final",
        "stage_status",
        "stage_b_rank",
        "stochastic_overall_distance_median",
        "stochastic_historical_core_distance_median",
        "stochastic_intrinsic_baseline_distance_median",
        "stochastic_historical_core_distance_iqr",
    ]
    return sums.merge(proposals[meta_cols], on=["variant_id", "seed", "proposal_id", "family_id"], how="left")


def _family_winners(target_sums: pd.DataFrame) -> pd.DataFrame:
    if target_sums.empty:
        return pd.DataFrame()
    best = (
        target_sums.sort_values(["median_target_sum", "proposal_id"])
        .groupby(["variant_id", "seed", "family_id"], as_index=False)
        .head(1)
        .sort_values(["variant_id", "seed", "median_target_sum", "family_id"])
        .reset_index(drop=True)
    )
    best["family_rank"] = best.groupby(["variant_id", "seed"]).cumcount() + 1
    winning = best.groupby(["variant_id", "seed"])["median_target_sum"].transform("min")
    best["delta_from_winning_family"] = best["median_target_sum"] - winning
    return best[
        [
            "variant_id",
            "seed",
            "family_rank",
            "family_id",
            "proposal_id",
            "accepted_final",
            "stage_status",
            "stage_b_rank",
            "stochastic_overall_distance_median",
            "median_target_sum",
            "delta_from_winning_family",
        ]
    ].sort_values(["variant_id", "seed", "family_rank"]).reset_index(drop=True)


def _accepted_mix(accepted: pd.DataFrame) -> pd.DataFrame:
    if accepted.empty:
        return pd.DataFrame(
            columns=["variant_id", "seed", "family_id", "accepted_count", "median_stochastic_distance"]
        )
    accepted["stochastic_overall_distance_median"] = pd.to_numeric(
        accepted["stochastic_overall_distance_median"],
        errors="coerce",
    )
    return (
        accepted.groupby(["variant_id", "seed", "family_id"], as_index=False)
        .agg(
            accepted_count=("proposal_id", "nunique"),
            median_stochastic_distance=("stochastic_overall_distance_median", "median"),
        )
        .sort_values(["variant_id", "seed", "family_id"])
        .reset_index(drop=True)
    )


def _target_leverage(targets: pd.DataFrame, accepted: pd.DataFrame) -> pd.DataFrame:
    accepted_ids = set(zip(accepted["variant_id"], accepted["seed"], accepted["proposal_id"], strict=False))
    stage_b = targets.loc[targets["stage"] == "stage_b"].copy()
    stage_b = stage_b.loc[
        stage_b[["variant_id", "seed", "proposal_id"]].apply(tuple, axis=1).isin(accepted_ids)
    ].copy()
    if stage_b.empty:
        return pd.DataFrame()
    stage_b["weighted_penalty"] = pd.to_numeric(stage_b["weighted_penalty"], errors="coerce")
    proposal_medians = (
        stage_b.groupby(["variant_id", "seed", "proposal_id", "target_id"], as_index=False)["weighted_penalty"]
        .median()
        .rename(columns={"weighted_penalty": "median_weighted_penalty"})
    )
    return (
        proposal_medians.groupby(["variant_id", "seed", "target_id"], as_index=False)[
            "median_weighted_penalty"
        ]
        .median()
        .rename(columns={"median_weighted_penalty": "accepted_median_weighted_penalty"})
        .sort_values(["variant_id", "seed", "accepted_median_weighted_penalty"], ascending=[True, True, False])
        .reset_index(drop=True)
    )


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


def _render_review(
    run_dirs: list[Path],
    family_summary: pd.DataFrame,
    accepted_mix: pd.DataFrame,
    winners: pd.DataFrame,
    target_leverage: pd.DataFrame,
) -> str:
    input_rows = []
    for run_dir in run_dirs:
        manifest = _load_manifest(run_dir)
        config = manifest.get("config", {})
        input_rows.append(
            {
                "variant_id": config.get("observation_bridge_variant", run_dir.name),
                "seed": config.get("master_seed"),
                "stage_a_draws": config.get("stage_a_draws_per_family"),
                "stage_a_keep": config.get("stage_a_keep_per_family"),
                "stage_b_replicates": config.get("stage_b_historical_replicates"),
            }
        )

    winner_rows = (
        winners.loc[winners["family_rank"] == 1][
            ["variant_id", "seed", "family_id", "proposal_id", "median_target_sum"]
        ].to_dict(orient="records")
        if not winners.empty
        else []
    )
    mix_rows = accepted_mix.to_dict(orient="records") if not accepted_mix.empty else []
    leverage_rows = (
        target_leverage.loc[target_leverage["target_id"].isin(["CT007", "CT009", "CT010"])]
        .to_dict(orient="records")
        if not target_leverage.empty
        else []
    )
    winning_families = winners.loc[winners["family_rank"] == 1].copy() if not winners.empty else pd.DataFrame()
    winner_counts = (
        winning_families.groupby("family_id").size().sort_values(ascending=False).to_dict()
        if not winning_families.empty
        else {}
    )
    variant_winner_counts = (
        winning_families.groupby(["variant_id", "family_id"]).size().unstack(fill_value=0).to_dict(orient="index")
        if not winning_families.empty
        else {}
    )
    accepted_totals = (
        accepted_mix.groupby("family_id")["accepted_count"].sum().sort_values(ascending=False).to_dict()
        if not accepted_mix.empty
        else {}
    )
    late_soft_winners = (
        winning_families.loc[winning_families["variant_id"] == "late_bridge_soft", "family_id"]
        .value_counts()
        .to_dict()
        if not winning_families.empty
        else {}
    )
    family_rows = (
        family_summary[
            [
                "variant_id",
                "seed",
                "family_id",
                "stage_a_valid_rate",
                "stage_b_valid",
                "final_accepted",
                "median_stochastic_distance_valid",
            ]
        ].to_dict(orient="records")
        if not family_summary.empty
        else []
    )

    lines = [
        "# Module 4 Observation-Bridge Sensitivity Review",
        "",
        "## Summary",
        "",
        (
            "Module 4 reruns the calibration with late-observation assumptions as explicit "
            "scoring variants rather than post-hoc spreadsheet adjustments."
        ),
        "",
        "## Inputs",
        "",
        _markdown_table(
            input_rows,
            ["variant_id", "seed", "stage_a_draws", "stage_a_keep", "stage_b_replicates"],
        ),
        "",
        "## Family Summary",
        "",
        _markdown_table(
            family_rows,
            [
                "variant_id",
                "seed",
                "family_id",
                "stage_a_valid_rate",
                "stage_b_valid",
                "final_accepted",
                "median_stochastic_distance_valid",
            ],
        ),
        "",
        "## Accepted Family Mix",
        "",
        _markdown_table(mix_rows, ["variant_id", "seed", "family_id", "accepted_count", "median_stochastic_distance"]),
        "",
        "## Target-Sum Winners",
        "",
        _markdown_table(winner_rows, ["variant_id", "seed", "family_id", "proposal_id", "median_target_sum"]),
        "",
        "## Late-Target Leverage Among Accepted Proposals",
        "",
        _markdown_table(
            leverage_rows,
            ["variant_id", "seed", "target_id", "accepted_median_weighted_penalty"],
        ),
        "",
        "## Interpretation",
        "",
        f"Winner counts across all variant/seed runs: `{winner_counts}`.",
        f"Winner counts by variant: `{variant_winner_counts}`.",
        f"Accepted proposal totals across all runs: `{accepted_totals}`.",
        f"Combined soft late-observation winners: `{late_soft_winners}`.",
        (
            "Habitat-only and trout-only should be treated as outside the accepted frontier "
            "when their accepted totals remain zero across the sensitivity grid."
        ),
        (
            "The central biological test is whether `persistent_joint_cause` remains stable "
            "under the combined late-observation variant, because that variant softens the "
            "three late targets simultaneously rather than giving a single scoring assumption "
            "all the leverage."
        ),
        (
            "Single-axis flips toward `climbing_only` are still informative. They identify "
            "which observation assumptions control local rank order, but they do not by "
            "themselves overturn the joint-cause signal unless the combined variant also flips."
        ),
        "",
        "## Artifacts",
        "",
        "- `module4_family_summary.csv`",
        "- `module4_accepted_mix.csv`",
        "- `module4_family_winners.csv`",
        "- `module4_target_leverage.csv`",
        "- `module4_observation_sensitivity_review.md`",
    ]
    return "\n".join(lines) + "\n"


def summarize_runs(output_dir: Path, variants: list[str], seeds: list[int], publish_root: Path | None = None) -> dict[str, Path]:
    run_dirs = [path for path in _run_dirs(output_dir, variants, seeds) if (path / "run_manifest.json").exists()]
    if not run_dirs:
        raise FileNotFoundError(f"No Module 4 run outputs found under {output_dir}")

    family_frames: list[pd.DataFrame] = []
    proposal_frames: list[pd.DataFrame] = []
    target_frames: list[pd.DataFrame] = []
    accepted_frames: list[pd.DataFrame] = []
    for run_dir in run_dirs:
        family, proposals, targets, accepted, _ = _load_run_tables(run_dir)
        family_frames.append(family)
        proposal_frames.append(proposals)
        target_frames.append(targets)
        accepted_frames.append(accepted)

    family_summary = pd.concat(family_frames, ignore_index=True)
    proposals = pd.concat(proposal_frames, ignore_index=True)
    targets = pd.concat(target_frames, ignore_index=True)
    accepted = pd.concat(accepted_frames, ignore_index=True) if accepted_frames else pd.DataFrame()

    target_sums = _proposal_target_sums(targets, proposals)
    winners = _family_winners(target_sums)
    mix = _accepted_mix(accepted)
    leverage = _target_leverage(targets, accepted)

    summary_dir = output_dir / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "family_summary": summary_dir / "module4_family_summary.csv",
        "accepted_mix": summary_dir / "module4_accepted_mix.csv",
        "family_winners": summary_dir / "module4_family_winners.csv",
        "target_leverage": summary_dir / "module4_target_leverage.csv",
        "review_doc": summary_dir / "module4_observation_sensitivity_review.md",
    }
    family_summary.to_csv(paths["family_summary"], index=False)
    mix.to_csv(paths["accepted_mix"], index=False)
    winners.to_csv(paths["family_winners"], index=False)
    leverage.to_csv(paths["target_leverage"], index=False)
    paths["review_doc"].write_text(
        _render_review(run_dirs, family_summary, mix, winners, leverage),
        encoding="utf-8",
    )

    if publish_root is not None:
        data_dir = publish_root / "data"
        docs_dir = publish_root / "docs"
        data_dir.mkdir(parents=True, exist_ok=True)
        docs_dir.mkdir(parents=True, exist_ok=True)
        publish_paths = {
            "family_summary": data_dir / "module4_family_summary.csv",
            "accepted_mix": data_dir / "module4_accepted_mix.csv",
            "family_winners": data_dir / "module4_family_winners.csv",
            "target_leverage": data_dir / "module4_target_leverage.csv",
            "review_doc": docs_dir / "module4_observation_sensitivity_review.md",
        }
        family_summary.to_csv(publish_paths["family_summary"], index=False)
        mix.to_csv(publish_paths["accepted_mix"], index=False)
        winners.to_csv(publish_paths["family_winners"], index=False)
        leverage.to_csv(publish_paths["target_leverage"], index=False)
        publish_paths["review_doc"].write_text(
            _render_review(run_dirs, family_summary, mix, winners, leverage),
            encoding="utf-8",
        )
        paths.update({f"published_{key}": value for key, value in publish_paths.items()})
    return paths


def main() -> None:
    args = parse_args()
    variants = _validate_variants([str(variant) for variant in args.variants])
    if not args.seeds:
        raise ValueError("At least one seed is required")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.summarize_only:
        for variant in variants:
            for seed in args.seeds:
                run_dir = _run_one(args, variant, seed)
                print(f"completed variant={variant} seed={seed} output={run_dir}")

    paths = summarize_runs(args.output_dir, variants, args.seeds, publish_root=args.publish_root)
    print("Wrote Module 4 observation sensitivity summary:")
    for name, path in paths.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
