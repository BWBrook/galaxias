from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from galaxias_model.module5_counterfactual import read_outcome_schema_columns
from galaxias_model.module5_factorial_extension import (
    FACTORIAL_EXTENSION_SOURCE_COUNTS,
    FACTORIAL_EXTENSION_STATUS,
)
from galaxias_model.module5_interaction_stability import (
    EFFECT_COLUMNS,
    ENDPOINTS,
    FACTORIAL_FAMILIES,
    IDENTITY_COLUMNS,
    INPUT_COLUMNS,
    REMOVAL_AXES,
    build_prefix_summary,
    build_qc_checks,
    classify_effect,
    compute_context_effects,
    endpoint_tolerances,
    file_sha256,
)
from galaxias_model.module5_output_checks import (
    check_matched_pair_ids,
    check_ordered_schema,
    check_seed_pairing,
    check_source_identity,
)


DEFAULT_PREFIXES = (100, 175, 250)
DEFAULT_BATCH_SIZE = 50
BASELINE_COLUMNS = (
    "persistence_2002_baseline",
    "persistence_1996_baseline",
    "min_abundance_1992_2002_baseline",
    "lake_refuge_share_2002_baseline",
)


def _check(name: str, passed: bool, details: str) -> dict[str, object]:
    return {"check_name": name, "passed": bool(passed), "details": details}


def build_shared_block_qc(
    frame: pd.DataFrame,
    provenance: dict[str, object],
    *,
    schema_columns: list[str],
    expected_row_count: int,
    expected_replicates: int,
    expected_contexts: int = 15,
    expected_source_counts: dict[str, int] | None = None,
) -> pd.DataFrame:
    source_counts = expected_source_counts or FACTORIAL_EXTENSION_SOURCE_COUNTS
    checks = list(
        build_qc_checks(
            frame,
            expected_row_count=expected_row_count,
            expected_replicates=expected_replicates,
            expected_contexts=expected_contexts,
        )
    )
    checks.extend(
        [
            check_ordered_schema(frame, schema_columns),
            check_source_identity(frame, provenance),
            check_matched_pair_ids(frame),
            check_seed_pairing(frame).check,
        ]
    )
    if any(column not in frame.columns for column in (*INPUT_COLUMNS, *BASELINE_COLUMNS)):
        return pd.DataFrame(checks)

    actual_source_counts = {
        str(key): int(value)
        for key, value in frame.groupby("family_id")[
            "proposal_source_key"
        ].nunique().to_dict().items()
    }
    checks.append(
        _check(
            "factorial_source_counts",
            actual_source_counts == source_counts,
            f"actual={actual_source_counts} expected={source_counts}",
        )
    )

    block_columns = ["proposal_source_key", "stochastic_replicate_id"]
    axis_counts = (
        frame.groupby([*block_columns, "intervention_axis"], sort=False)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=list(REMOVAL_AXES), fill_value=0)
    )
    exact_axes = bool((axis_counts == 1).all(axis=1).all())
    expected_blocks = sum(source_counts.values()) * expected_replicates
    checks.append(
        _check(
            "three_contrasts_per_source_replicate_block",
            len(axis_counts) == expected_blocks and exact_axes,
            f"blocks={len(axis_counts)} expected={expected_blocks} exact_axes={exact_axes}",
        )
    )

    seed_uniqueness = frame.groupby(block_columns, sort=False)[
        ["baseline_stochastic_seed", "intervention_stochastic_seed"]
    ].nunique(dropna=False)
    one_seed_per_block = bool((seed_uniqueness == 1).all(axis=1).all())
    checks.append(
        _check(
            "one_seed_across_stored_arms",
            one_seed_per_block,
            f"blocks_with_multiple_seeds={int((seed_uniqueness > 1).any(axis=1).sum())}",
        )
    )

    block_seeds = frame.groupby(block_columns, sort=False)[
        "baseline_stochastic_seed"
    ].first()
    seed_counts = block_seeds.value_counts(dropna=False)
    collision_groups = int((seed_counts > 1).sum())
    collision_excess = int((seed_counts.loc[seed_counts > 1] - 1).sum())
    checks.append(
        _check(
            "zero_cross_block_seed_collisions",
            collision_groups == 0 and len(block_seeds) == expected_blocks,
            (
                f"block_seeds={len(block_seeds)} distinct={block_seeds.nunique()} "
                f"collision_groups={collision_groups} collision_excess={collision_excess}"
            ),
        )
    )

    baseline_uniqueness = frame.groupby(block_columns, sort=False)[
        list(BASELINE_COLUMNS)
    ].nunique(dropna=False)
    baseline_failures = int((baseline_uniqueness > 1).any(axis=1).sum())
    checks.append(
        _check(
            "shared_status_quo_baseline_values",
            baseline_failures == 0,
            f"blocks_with_baseline_disagreement={baseline_failures}",
        )
    )

    provenance_ok = (
        provenance.get("status") == FACTORIAL_EXTENSION_STATUS
        and provenance.get("production_attribution") is False
        and provenance.get("status_quo_executed_once_per_block") is True
        and int(provenance.get("expected_replicates", -1)) == expected_replicates
        and int(provenance.get("expected_row_count", -1)) == expected_row_count
        and list(provenance.get("stored_contrast_axes", [])) == list(REMOVAL_AXES)
    )
    checks.append(
        _check(
            "factorial_extension_provenance",
            provenance_ok,
            (
                f"status={provenance.get('status')} "
                f"production_attribution={provenance.get('production_attribution')} "
                "status_quo_once="
                f"{provenance.get('status_quo_executed_once_per_block')}"
            ),
        )
    )
    return pd.DataFrame(checks)


def compute_shared_block_source_effects(
    frame: pd.DataFrame,
    *,
    replicate_start: int,
    replicate_stop: int,
    window_label: str,
    window_type: str,
    tolerances: dict[tuple[str, str], float],
) -> pd.DataFrame:
    selected = frame.loc[
        frame["family_id"].isin(FACTORIAL_FAMILIES)
        & frame["intervention_axis"].isin(REMOVAL_AXES)
        & frame["stochastic_replicate_id"].between(
            replicate_start, replicate_stop - 1
        )
    ].copy()
    selected["context_id"] = (
        selected["variant_id"].astype(str)
        + "|seed"
        + selected["seed"].astype(str)
    )
    identity_columns = [*IDENTITY_COLUMNS, "context_id"]
    records: list[dict[str, object]] = []
    for endpoint in ENDPOINTS:
        replicate_wide = selected.pivot(
            index=[*identity_columns, "stochastic_replicate_id"],
            columns="intervention_axis",
            values=endpoint,
        )
        missing_axes = sorted(set(REMOVAL_AXES) - set(replicate_wide.columns))
        if missing_axes or replicate_wide[list(REMOVAL_AXES)].isna().any().any():
            raise ValueError(
                f"Incomplete shared-block axes for {endpoint}: {missing_axes}"
            )
        replicate_wide = replicate_wide.reset_index()
        replicate_wide["trout_removal"] = replicate_wide["no_trout_pressure"]
        replicate_wide["climbing_removal"] = replicate_wide[
            "no_climbing_pressure"
        ]
        replicate_wide["joint_removal"] = replicate_wide[
            "no_trout_or_climbing_pressure"
        ]
        replicate_wide["additive_interaction"] = (
            replicate_wide["joint_removal"]
            - replicate_wide["trout_removal"]
            - replicate_wide["climbing_removal"]
        )
        for identity, group in replicate_wide.groupby(identity_columns, sort=False):
            record = dict(zip(identity_columns, identity, strict=True))
            family_id = str(record["family_id"])
            tolerance = tolerances[(family_id, endpoint)]
            record.update(
                {
                    "endpoint": endpoint,
                    "window_label": window_label,
                    "window_type": window_type,
                    "replicate_start": replicate_start,
                    "replicate_stop_exclusive": replicate_stop,
                    "n_replicates_per_intervention": len(group),
                    "tolerance": tolerance,
                }
            )
            for effect_name in EFFECT_COLUMNS:
                values = pd.to_numeric(group[effect_name], errors="raise")
                estimate = float(values.mean())
                mc_variance = float(values.var(ddof=1) / len(values))
                record[effect_name] = estimate
                record[f"{effect_name}_mc_variance"] = mc_variance
                record[f"{effect_name}_classification"] = classify_effect(
                    estimate,
                    tolerance,
                    effect_name,
                )
            records.append(record)
    return pd.DataFrame.from_records(records)


def build_250_replication_decision(prefix_summary: pd.DataFrame) -> pd.DataFrame:
    primary = prefix_summary.loc[
        (prefix_summary["window_type"] == "prefix")
        & (prefix_summary["weighting"] == "context_equal")
    ]
    sensitivity = prefix_summary.loc[
        (prefix_summary["window_type"] == "prefix")
        & (prefix_summary["weighting"] == "source_equal")
        & (prefix_summary["n_replicates_per_intervention"] == 250)
    ]
    records: list[dict[str, object]] = []
    for (family_id, endpoint), group in primary.groupby(
        ["family_id", "endpoint"], sort=False
    ):
        tolerance = float(group["tolerance"].iloc[0])
        drift_pass = True
        half_width_pass = True
        source_proportion_pass = True
        max_estimate_drift = 0.0
        max_bound_drift = 0.0
        max_half_width = 0.0
        max_proportion_drift = 0.0
        for effect in EFFECT_COLUMNS:
            row175 = group.loc[
                (group["effect"] == effect)
                & (group["n_replicates_per_intervention"] == 175)
            ].iloc[0]
            row250 = group.loc[
                (group["effect"] == effect)
                & (group["n_replicates_per_intervention"] == 250)
            ].iloc[0]
            estimate_drift = abs(float(row250["estimate"]) - float(row175["estimate"]))
            bound_drift = max(
                abs(float(row250["mc_95_low"]) - float(row175["mc_95_low"])),
                abs(float(row250["mc_95_high"]) - float(row175["mc_95_high"])),
            )
            half_width = float(row250["mc_95_half_width"])
            proportion_drift = max(
                abs(float(row250[column]) - float(row175[column]))
                for column in (
                    "source_negative_proportion",
                    "source_near_zero_proportion",
                    "source_positive_proportion",
                )
            )
            max_estimate_drift = max(max_estimate_drift, estimate_drift)
            max_bound_drift = max(max_bound_drift, bound_drift)
            max_half_width = max(max_half_width, half_width)
            max_proportion_drift = max(max_proportion_drift, proportion_drift)
            drift_pass &= estimate_drift <= tolerance and bound_drift <= tolerance
            half_width_pass &= half_width <= tolerance
            source_proportion_pass &= proportion_drift < 0.05

        interaction_classes = group.loc[
            group["effect"] == "additive_interaction"
        ].set_index("n_replicates_per_intervention")["classification"]
        interaction_stable = len(
            {str(interaction_classes.loc[value]) for value in DEFAULT_PREFIXES}
        ) == 1
        full250 = group.loc[group["n_replicates_per_intervention"] == 250]
        source250 = sensitivity.loc[
            (sensitivity["family_id"] == family_id)
            & (sensitivity["endpoint"] == endpoint)
        ]
        primary_classes = full250.set_index("effect")["classification"]
        sensitivity_classes = source250.set_index("effect")["classification"]
        weighting_agreement = primary_classes.equals(
            sensitivity_classes.reindex(primary_classes.index)
        )
        weighting_difference = float(
            (
                full250.set_index("effect")["estimate"]
                - source250.set_index("effect")["estimate"]
            ).abs().max()
        )
        family_level_stable = bool(
            drift_pass and half_width_pass and interaction_stable
        )
        if family_level_stable and source_proportion_pass and weighting_agreement:
            decision = "stable_at_250"
        elif family_level_stable and not source_proportion_pass:
            decision = "family_level_stable_source_distribution_unstable"
        elif family_level_stable and not weighting_agreement:
            decision = "heterogeneity_not_monte_carlo_limited"
        else:
            decision = "unstable_at_250"
        interaction250 = full250.loc[
            full250["effect"] == "additive_interaction"
        ].iloc[0]
        records.append(
            {
                "family_id": family_id,
                "endpoint": endpoint,
                "endpoint_role": (
                    "lead" if endpoint == "persistence_2002_contrast" else "support"
                ),
                "tolerance": tolerance,
                "interaction_estimate_250": float(interaction250["estimate"]),
                "interaction_classification_250": interaction250["classification"],
                "max_estimate_drift_175_to_250": max_estimate_drift,
                "max_mc_bound_drift_175_to_250": max_bound_drift,
                "max_mc_95_half_width_250": max_half_width,
                "max_source_class_proportion_drift_175_to_250": max_proportion_drift,
                "interaction_classification_stable_100_175_250": interaction_stable,
                "estimate_and_bound_drift_pass": drift_pass,
                "mc_half_width_pass": half_width_pass,
                "source_class_proportion_pass": source_proportion_pass,
                "context_source_classification_agreement_250": weighting_agreement,
                "context_vs_source_max_estimate_difference_250": weighting_difference,
                "family_level_stable_at_250": family_level_stable,
                "decision": decision,
                "stop_replicates": 250,
            }
        )
    return pd.DataFrame.from_records(records)


def build_goal026_continuity_check(
    prefix_summary: pd.DataFrame,
    goal026_prefix_summary: pd.DataFrame,
) -> pd.DataFrame:
    keys = ["family_id", "endpoint", "effect", "weighting"]
    current = prefix_summary.loc[
        (prefix_summary["window_type"] == "prefix")
        & (prefix_summary["n_replicates_per_intervention"] == 100)
        & (prefix_summary["weighting"] == "context_equal"),
        [*keys, "tolerance", "estimate", "mc_se", "classification"],
    ]
    previous = goal026_prefix_summary.loc[
        (goal026_prefix_summary["window_type"] == "prefix")
        & (goal026_prefix_summary["n_replicates_per_intervention"] == 100)
        & (goal026_prefix_summary["weighting"] == "context_equal"),
        [*keys, "estimate", "mc_se", "classification"],
    ]
    comparison = current.merge(
        previous,
        on=keys,
        suffixes=("_goal027", "_goal026"),
        validate="one_to_one",
    )
    expected_rows = len(FACTORIAL_FAMILIES) * len(ENDPOINTS) * len(EFFECT_COLUMNS)
    if len(comparison) != expected_rows:
        raise ValueError(
            f"Goal 026 continuity comparison has {len(comparison)} rows, "
            f"expected {expected_rows}"
        )
    comparison["absolute_estimate_difference"] = (
        comparison["estimate_goal027"] - comparison["estimate_goal026"]
    ).abs()
    comparison["combined_mc_se"] = (
        comparison["mc_se_goal027"] ** 2 + comparison["mc_se_goal026"] ** 2
    ).pow(0.5)
    comparison["review_threshold"] = comparison[
        ["tolerance", "combined_mc_se"]
    ].apply(lambda row: max(float(row["tolerance"]), 3.0 * float(row["combined_mc_se"])), axis=1)
    comparison["implementation_review_flag"] = (
        comparison["absolute_estimate_difference"] > comparison["review_threshold"]
    )
    return comparison


def run_factorial_extension_audit(
    frame: pd.DataFrame,
    provenance: dict[str, object],
    *,
    schema_columns: list[str],
    expected_row_count: int,
    expected_replicates: int,
    expected_contexts: int = 15,
    expected_source_counts: dict[str, int] | None = None,
    qc_only: bool = False,
    prefixes: tuple[int, ...] = DEFAULT_PREFIXES,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, object]:
    qc = build_shared_block_qc(
        frame,
        provenance,
        schema_columns=schema_columns,
        expected_row_count=expected_row_count,
        expected_replicates=expected_replicates,
        expected_contexts=expected_contexts,
        expected_source_counts=expected_source_counts,
    )
    if not bool(qc["passed"].all()):
        failed = qc.loc[~qc["passed"].astype(bool), "check_name"].tolist()
        raise ValueError(f"Shared-block audit QC failed: {failed}")
    result: dict[str, object] = {"qc": qc}
    if qc_only:
        return result
    if prefixes != DEFAULT_PREFIXES or expected_replicates != 250:
        raise ValueError("Full Goal 027 audit requires prefixes 100,175,250 and 250 replicates")

    tolerances = endpoint_tolerances(frame)
    windows = [(0, prefix, f"prefix_{prefix}", "prefix") for prefix in prefixes]
    windows.extend(
        (
            start,
            min(start + batch_size, expected_replicates),
            f"batch_{start:03d}_{min(start + batch_size, expected_replicates) - 1:03d}",
            "batch",
        )
        for start in range(0, expected_replicates, batch_size)
    )
    sources = pd.concat(
        [
            compute_shared_block_source_effects(
                frame,
                replicate_start=start,
                replicate_stop=stop,
                window_label=label,
                window_type=window_type,
                tolerances=tolerances,
            )
            for start, stop, label, window_type in windows
        ],
        ignore_index=True,
    )
    contexts = compute_context_effects(sources)
    prefix_summary = build_prefix_summary(sources, contexts)
    result.update(
        {
            "sources": sources,
            "contexts": contexts,
            "prefix_summary": prefix_summary,
            "decision": build_250_replication_decision(prefix_summary),
            "tolerances": tolerances,
        }
    )
    return result


def write_factorial_extension_audit(
    *,
    matched_outcomes_path: Path,
    provenance_path: Path,
    outcome_schema_path: Path,
    output_dir: Path,
    expected_sha256: str,
    source_artifact: Path,
    source_execution_sha: str,
    run_id: str,
    command: str,
    expected_row_count: int,
    expected_replicates: int,
    qc_only: bool = False,
    goal026_prefix_summary_path: Path | None = None,
) -> dict[str, Path]:
    actual_sha256 = file_sha256(matched_outcomes_path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Matched-outcomes SHA-256 mismatch: {actual_sha256} != {expected_sha256}"
        )
    if not matched_outcomes_path.resolve().is_relative_to(source_artifact.resolve()):
        raise ValueError("Matched outcomes are outside the authorized source artifact")
    if not provenance_path.resolve().is_relative_to(source_artifact.resolve()):
        raise ValueError("Provenance is outside the authorized source artifact")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if provenance.get("matched_outcomes_sha256") != actual_sha256:
        raise ValueError("Provenance matched-outcomes SHA-256 does not match the raw file")
    if provenance.get("git_sha") != source_execution_sha:
        raise ValueError(
            f"Provenance execution SHA {provenance.get('git_sha')} != "
            f"{source_execution_sha}"
        )
    if provenance.get("run_id") != run_id:
        raise ValueError(
            f"Provenance run ID {provenance.get('run_id')} != {run_id}"
        )
    frame = pd.read_csv(matched_outcomes_path, keep_default_na=False)
    schema_columns = read_outcome_schema_columns(outcome_schema_path)
    result = run_factorial_extension_audit(
        frame,
        provenance,
        schema_columns=schema_columns,
        expected_row_count=expected_row_count,
        expected_replicates=expected_replicates,
        qc_only=qc_only,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "qc": output_dir / "qc_summary.csv",
        "metadata": output_dir / "audit_metadata.json",
    }
    result["qc"].to_csv(paths["qc"], index=False)
    continuity: pd.DataFrame | None = None
    if not qc_only:
        paths.update(
            {
                "sources": output_dir / "source_effect_summary.csv",
                "contexts": output_dir / "context_effect_summary.csv",
                "prefix": output_dir / "prefix_stability_summary.csv",
                "decision": output_dir / "replication_decision.csv",
            }
        )
        full_sources = result["sources"].loc[
            result["sources"]["window_label"] == "prefix_250"
        ]
        full_contexts = result["contexts"].loc[
            result["contexts"]["window_label"] == "prefix_250"
        ]
        full_sources.to_csv(paths["sources"], index=False)
        full_contexts.to_csv(paths["contexts"], index=False)
        result["prefix_summary"].to_csv(paths["prefix"], index=False)
        result["decision"].to_csv(paths["decision"], index=False)
        if goal026_prefix_summary_path is not None:
            continuity = build_goal026_continuity_check(
                result["prefix_summary"],
                pd.read_csv(goal026_prefix_summary_path),
            )
            paths["continuity"] = output_dir / "goal026_continuity_check.csv"
            continuity.to_csv(paths["continuity"], index=False)

    decisions = result.get("decision")
    metadata = {
        "label": "goal027-module5-shared-four-arm-250rep-extension",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "source_artifact": source_artifact.as_posix(),
        "matched_outcomes_path": matched_outcomes_path.as_posix(),
        "matched_outcomes_size": matched_outcomes_path.stat().st_size,
        "matched_outcomes_sha256": actual_sha256,
        "source_execution_sha": source_execution_sha,
        "analysis_command": command,
        "raw_matched_outcomes_copied_locally": False,
        "qc_only": qc_only,
        "qc_all_passed": bool(result["qc"]["passed"].all()),
        "expected_replicates": expected_replicates,
        "expected_row_count": expected_row_count,
        "families": list(FACTORIAL_FAMILIES),
        "endpoints": list(ENDPOINTS),
        "interaction_definition": (
            "replicate-level joint_removal - trout_removal - climbing_removal"
        ),
        "common_seed_boundary": (
            "Equal starting seeds across four arms, not guaranteed identical "
            "event-level ecological shocks after trajectories diverge."
        ),
        "primary_weighting": "equal variant_id x Module4 calibration-seed contexts",
        "sensitivity_weighting": "equal proposal_source_key rows",
        "prefixes": [] if qc_only else list(DEFAULT_PREFIXES),
        "batch_size": None if qc_only else DEFAULT_BATCH_SIZE,
        "stop_replicates": expected_replicates,
        "output_row_counts": {
            path.name: int(sum(1 for _ in path.open(encoding="utf-8")) - 1)
            for key, path in paths.items()
            if key not in {"metadata"} and path.suffix == ".csv"
        },
        "decision_counts": (
            {}
            if decisions is None
            else {
                str(key): int(value)
                for key, value in decisions["decision"].value_counts().to_dict().items()
            }
        ),
        "goal026_continuity_review_flags": (
            None
            if continuity is None
            else int(continuity["implementation_review_flag"].sum())
        ),
        "interpretation_boundary": (
            "Conditional endpoint-scale interaction and Monte Carlo stability "
            "only; not proof of ecological synergy or a final causal claim."
        ),
    }
    paths["metadata"].write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return paths
