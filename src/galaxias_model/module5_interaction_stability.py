from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd


FACTORIAL_FAMILIES: tuple[str, ...] = (
    "persistent_joint_cause",
    "transient_perfect_storm",
)
ENDPOINTS: tuple[str, ...] = (
    "persistence_2002_contrast",
    "min_abundance_1992_2002_contrast",
    "lake_refuge_share_2002_contrast",
)
REMOVAL_AXES: tuple[str, ...] = (
    "no_trout_pressure",
    "no_climbing_pressure",
    "no_trout_or_climbing_pressure",
)
PREFIXES: tuple[int, ...] = (25, 50, 75, 100)
EFFECT_COLUMNS: dict[str, str] = {
    "trout_removal": "no_trout_pressure",
    "climbing_removal": "no_climbing_pressure",
    "joint_removal": "no_trout_or_climbing_pressure",
    "additive_interaction": "additive_interaction",
}
IDENTITY_COLUMNS: tuple[str, ...] = (
    "proposal_source_key",
    "module4_run_id",
    "variant_id",
    "seed",
    "run_dir_name",
    "family_id",
    "proposal_id",
    "proposal_seed",
)
INPUT_COLUMNS: tuple[str, ...] = (
    *IDENTITY_COLUMNS,
    "stochastic_replicate_id",
    "intervention_id",
    "intervention_axis",
    "baseline_stochastic_seed",
    "intervention_stochastic_seed",
    "min_abundance_1992_2002_baseline",
    *ENDPOINTS,
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(
    name: str,
    observed: object,
    expected: object,
    passed: bool,
    details: str = "",
) -> dict[str, object]:
    def encode(value: object) -> str:
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, sort_keys=True)
        return str(value)

    return {
        "check_name": name,
        "observed_value": encode(observed),
        "expected_value": encode(expected),
        "passed": bool(passed),
        "details": details,
    }


def _context_id(frame: pd.DataFrame) -> pd.Series:
    return frame["variant_id"].astype(str) + "|seed" + frame["seed"].astype(str)


def endpoint_tolerances(frame: pd.DataFrame) -> dict[tuple[str, str], float]:
    tolerances: dict[tuple[str, str], float] = {}
    for family_id in FACTORIAL_FAMILIES:
        family = frame.loc[frame["family_id"] == family_id]
        status_quo = family.loc[family["intervention_axis"] == "status_quo"]
        baseline = pd.to_numeric(
            status_quo["min_abundance_1992_2002_baseline"], errors="coerce"
        ).dropna()
        if baseline.empty:
            baseline = pd.to_numeric(
                family["min_abundance_1992_2002_baseline"], errors="coerce"
            ).dropna()
        if baseline.empty:
            raise ValueError(f"Missing baseline abundance values for {family_id}")
        abundance_tolerance = max(10.0, 0.02 * float(baseline.median()))
        tolerances[(family_id, "persistence_2002_contrast")] = 0.01
        tolerances[(family_id, "lake_refuge_share_2002_contrast")] = 0.01
        tolerances[(family_id, "min_abundance_1992_2002_contrast")] = (
            abundance_tolerance
        )
    return tolerances


def classify_effect(value: float, tolerance: float, effect: str) -> str:
    if effect == "additive_interaction":
        if value > tolerance:
            return "more_than_additive"
        if value < -tolerance:
            return "less_than_additive"
        return "near_additive_or_unresolved"
    if value > tolerance:
        return "positive"
    if value < -tolerance:
        return "negative"
    return "near_zero"


def build_qc_checks(
    frame: pd.DataFrame,
    *,
    expected_row_count: int,
    expected_replicates: int,
    expected_contexts: int,
) -> tuple[dict[str, object], ...]:
    checks: list[dict[str, object]] = []
    missing = [column for column in INPUT_COLUMNS if column not in frame.columns]
    checks.append(_check("required_columns", missing, [], not missing))
    checks.append(
        _check("raw_row_count", len(frame), expected_row_count, len(frame) == expected_row_count)
    )
    if missing:
        return tuple(checks)

    target = frame.loc[frame["family_id"].isin(FACTORIAL_FAMILIES)].copy()
    checks.append(
        _check(
            "factorial_families",
            sorted(target["family_id"].unique().tolist()),
            sorted(FACTORIAL_FAMILIES),
            set(target["family_id"].unique()) == set(FACTORIAL_FAMILIES),
        )
    )
    seed_match = target["baseline_stochastic_seed"].eq(
        target["intervention_stochastic_seed"]
    )
    checks.append(
        _check(
            "within_pair_seed_match",
            int((~seed_match).sum()),
            0,
            bool(seed_match.all()),
            "This does not imply cross-intervention four-arm pairing.",
        )
    )

    expected_ids = set(range(expected_replicates))
    for family_id in FACTORIAL_FAMILIES:
        family = target.loc[target["family_id"] == family_id]
        removal = family.loc[family["intervention_axis"].isin(REMOVAL_AXES)]
        source_sets = {
            axis: set(
                removal.loc[removal["intervention_axis"] == axis, "proposal_source_key"]
            )
            for axis in REMOVAL_AXES
        }
        same_sources = len({frozenset(values) for values in source_sets.values()}) == 1
        checks.append(
            _check(
                f"{family_id}_factorial_source_sets",
                {axis: len(values) for axis, values in source_sets.items()},
                "identical non-empty sets",
                same_sources and bool(next(iter(source_sets.values()), set())),
            )
        )

        failures = 0
        unit_count = 0
        for _, group in removal.groupby(
            ["proposal_source_key", "intervention_axis"], sort=False
        ):
            unit_count += 1
            ids = pd.to_numeric(
                group["stochastic_replicate_id"], errors="coerce"
            ).dropna().astype(int)
            if len(group) != expected_replicates or set(ids) != expected_ids or ids.duplicated().any():
                failures += 1
        checks.append(
            _check(
                f"{family_id}_replicate_coverage",
                {"units": unit_count, "failures": failures},
                {"failures": 0, "replicate_ids": f"0..{expected_replicates - 1}"},
                failures == 0,
            )
        )
        context_count = (
            family.assign(context_id=_context_id(family))["context_id"].nunique()
        )
        checks.append(
            _check(
                f"{family_id}_context_count",
                int(context_count),
                expected_contexts,
                int(context_count) == expected_contexts,
            )
        )

    finite_failures: dict[str, int] = {}
    for endpoint in ENDPOINTS:
        numeric = pd.to_numeric(target[endpoint], errors="coerce")
        finite_failures[endpoint] = int((~numeric.notna()).sum())
    checks.append(
        _check(
            "finite_endpoint_values",
            finite_failures,
            {endpoint: 0 for endpoint in ENDPOINTS},
            not any(finite_failures.values()),
        )
    )
    return tuple(checks)


def seed_collision_facts(frame: pd.DataFrame) -> dict[str, int]:
    key_columns = [
        "proposal_source_key",
        "intervention_id",
        "stochastic_replicate_id",
    ]
    keys = frame.loc[:, [*key_columns, "baseline_stochastic_seed"]].drop_duplicates(
        key_columns
    )
    group_sizes = keys.groupby("baseline_stochastic_seed", dropna=False).size()
    collisions = group_sizes.loc[group_sizes > 1]
    source_seed = keys.groupby(
        ["proposal_source_key", "baseline_stochastic_seed"], dropna=False
    )["intervention_id"].nunique()
    return {
        "all_seed_key_count": int(len(keys)),
        "distinct_seed_count": int(keys["baseline_stochastic_seed"].nunique()),
        "collision_group_count": int(len(collisions)),
        "collision_excess_key_count": int((collisions - 1).sum()),
        "same_source_cross_intervention_collision_group_count": int(
            (source_seed > 1).sum()
        ),
    }


def compute_source_effects(
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
    selected["context_id"] = _context_id(selected)
    group_columns = [
        "family_id",
        "proposal_source_key",
        "module4_run_id",
        "variant_id",
        "seed",
        "run_dir_name",
        "proposal_id",
        "proposal_seed",
        "context_id",
        "intervention_axis",
    ]
    records: list[dict[str, object]] = []
    for endpoint in ENDPOINTS:
        grouped = (
            selected.groupby(group_columns, sort=False)[endpoint]
            .agg(["mean", "var", "count"])
            .reset_index()
        )
        index_columns = group_columns[:-1]
        mean_wide = grouped.pivot(index=index_columns, columns="intervention_axis", values="mean")
        var_wide = grouped.pivot(index=index_columns, columns="intervention_axis", values="var")
        count_wide = grouped.pivot(index=index_columns, columns="intervention_axis", values="count")
        for index, means in mean_wide.iterrows():
            identity = dict(zip(index_columns, index, strict=True))
            family_id = str(identity["family_id"])
            tolerance = tolerances[(family_id, endpoint)]
            effects = {
                "trout_removal": float(means["no_trout_pressure"]),
                "climbing_removal": float(means["no_climbing_pressure"]),
                "joint_removal": float(means["no_trout_or_climbing_pressure"]),
            }
            effects["additive_interaction"] = (
                effects["joint_removal"]
                - effects["trout_removal"]
                - effects["climbing_removal"]
            )
            mean_variances = {
                "trout_removal": float(var_wide.loc[index, "no_trout_pressure"])
                / float(count_wide.loc[index, "no_trout_pressure"]),
                "climbing_removal": float(var_wide.loc[index, "no_climbing_pressure"])
                / float(count_wide.loc[index, "no_climbing_pressure"]),
                "joint_removal": float(var_wide.loc[index, "no_trout_or_climbing_pressure"])
                / float(count_wide.loc[index, "no_trout_or_climbing_pressure"]),
            }
            mean_variances["additive_interaction"] = sum(mean_variances.values())
            record: dict[str, object] = {
                **identity,
                "endpoint": endpoint,
                "window_label": window_label,
                "window_type": window_type,
                "replicate_start": replicate_start,
                "replicate_stop_exclusive": replicate_stop,
                "n_replicates_per_intervention": replicate_stop - replicate_start,
                "tolerance": tolerance,
            }
            for effect_name, value in effects.items():
                variance = mean_variances[effect_name]
                record[effect_name] = value
                record[f"{effect_name}_mc_variance"] = variance
                record[f"{effect_name}_classification"] = classify_effect(
                    value, tolerance, effect_name
                )
            records.append(record)
    return pd.DataFrame.from_records(records)


def compute_context_effects(source_effects: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    group_columns = [
        "family_id",
        "context_id",
        "variant_id",
        "seed",
        "endpoint",
        "window_label",
        "window_type",
        "replicate_start",
        "replicate_stop_exclusive",
        "n_replicates_per_intervention",
        "tolerance",
    ]
    for index, group in source_effects.groupby(group_columns, sort=False):
        record = dict(zip(group_columns, index, strict=True))
        record["source_count"] = int(len(group))
        for effect_name in EFFECT_COLUMNS:
            record[effect_name] = float(group[effect_name].mean())
            record[f"{effect_name}_mc_variance"] = float(
                group[f"{effect_name}_mc_variance"].sum() / (len(group) ** 2)
            )
        records.append(record)
    return pd.DataFrame.from_records(records)


def _class_proportions(values: pd.Series, tolerance: float) -> tuple[float, float, float]:
    numeric = pd.to_numeric(values, errors="coerce")
    return (
        float((numeric < -tolerance).mean()),
        float((numeric.abs() <= tolerance).mean()),
        float((numeric > tolerance).mean()),
    )


def build_prefix_summary(
    source_effects: pd.DataFrame,
    context_effects: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    group_columns = [
        "family_id",
        "endpoint",
        "window_label",
        "window_type",
        "replicate_start",
        "replicate_stop_exclusive",
        "n_replicates_per_intervention",
        "tolerance",
    ]
    for index, sources in source_effects.groupby(group_columns, sort=False):
        identity = dict(zip(group_columns, index, strict=True))
        contexts = context_effects
        for column, value in identity.items():
            contexts = contexts.loc[contexts[column] == value]
        tolerance = float(identity["tolerance"])
        for effect_name in EFFECT_COLUMNS:
            negative, near_zero, positive = _class_proportions(
                sources[effect_name], tolerance
            )
            for weighting, units in (
                ("context_equal", contexts),
                ("source_equal", sources),
            ):
                estimate = float(units[effect_name].mean())
                mc_variance = float(
                    units[f"{effect_name}_mc_variance"].sum() / (len(units) ** 2)
                )
                mc_se = math.sqrt(max(mc_variance, 0.0))
                half_width = 1.96 * mc_se
                records.append(
                    {
                        **identity,
                        "effect": effect_name,
                        "weighting": weighting,
                        "estimate": estimate,
                        "mc_se": mc_se,
                        "mc_95_half_width": half_width,
                        "mc_95_low": estimate - half_width,
                        "mc_95_high": estimate + half_width,
                        "classification": classify_effect(
                            estimate, tolerance, effect_name
                        ),
                        "source_negative_proportion": negative,
                        "source_near_zero_proportion": near_zero,
                        "source_positive_proportion": positive,
                        "source_count": int(len(sources)),
                        "context_count": int(len(contexts)),
                        "context_min": float(contexts[effect_name].min()),
                        "context_max": float(contexts[effect_name].max()),
                    }
                )
    return pd.DataFrame.from_records(records)


def _recommended_replicates(
    half_width: float,
    tolerance: float,
    *,
    adequate: bool,
) -> str:
    if adequate:
        return "100"
    required = max(250.0, 100.0 * (half_width / tolerance) ** 2)
    for candidate in (250, 500, 1000):
        if required <= candidate:
            return str(candidate)
    return ">1000_or_redesign"


def build_replication_decision(prefix_summary: pd.DataFrame) -> pd.DataFrame:
    prefix = prefix_summary.loc[
        (prefix_summary["window_type"] == "prefix")
        & (prefix_summary["weighting"] == "context_equal")
    ]
    sensitivity = prefix_summary.loc[
        (prefix_summary["window_type"] == "prefix")
        & (prefix_summary["weighting"] == "source_equal")
        & (prefix_summary["n_replicates_per_intervention"] == 100)
    ]
    records: list[dict[str, object]] = []
    for (family_id, endpoint), group in prefix.groupby(
        ["family_id", "endpoint"], sort=False
    ):
        tolerance = float(group["tolerance"].iloc[0])
        effects = sorted(group["effect"].unique().tolist())
        drift_pass = True
        half_width_pass = True
        proportion_pass = True
        max_drift = 0.0
        max_bound_drift = 0.0
        max_half_width = 0.0
        max_proportion_drift = 0.0
        for effect in effects:
            row75 = group.loc[
                (group["effect"] == effect)
                & (group["n_replicates_per_intervention"] == 75)
            ].iloc[0]
            row100 = group.loc[
                (group["effect"] == effect)
                & (group["n_replicates_per_intervention"] == 100)
            ].iloc[0]
            estimate_drift = abs(float(row100["estimate"]) - float(row75["estimate"]))
            bound_drift = max(
                abs(float(row100["mc_95_low"]) - float(row75["mc_95_low"])),
                abs(float(row100["mc_95_high"]) - float(row75["mc_95_high"])),
            )
            half_width = float(row100["mc_95_half_width"])
            proportion_drift = max(
                abs(
                    float(row100[column]) - float(row75[column])
                )
                for column in (
                    "source_negative_proportion",
                    "source_near_zero_proportion",
                    "source_positive_proportion",
                )
            )
            max_drift = max(max_drift, estimate_drift)
            max_bound_drift = max(max_bound_drift, bound_drift)
            max_half_width = max(max_half_width, half_width)
            max_proportion_drift = max(max_proportion_drift, proportion_drift)
            drift_pass &= estimate_drift <= tolerance and bound_drift <= tolerance
            half_width_pass &= half_width <= tolerance
            proportion_pass &= proportion_drift < 0.05

        interaction_classes = group.loc[
            group["effect"] == "additive_interaction"
        ].set_index("n_replicates_per_intervention")["classification"]
        classification_pass = len(
            {str(interaction_classes.loc[n]) for n in (50, 75, 100)}
        ) == 1
        adequate = bool(
            drift_pass and half_width_pass and proportion_pass and classification_pass
        )
        full100 = group.loc[group["n_replicates_per_intervention"] == 100]
        source100 = sensitivity.loc[
            (sensitivity["family_id"] == family_id)
            & (sensitivity["endpoint"] == endpoint)
        ]
        weighting_difference = float(
            (
                full100.set_index("effect")["estimate"]
                - source100.set_index("effect")["estimate"]
            ).abs().max()
        )
        interaction100 = full100.loc[
            full100["effect"] == "additive_interaction"
        ].iloc[0]
        if adequate:
            action = "no_rerun"
        elif drift_pass and half_width_pass and classification_pass:
            action = "targeted_extension"
        elif half_width_pass and weighting_difference > tolerance:
            action = "more_replicates_will_not_help"
        else:
            action = "full_factorial_rerun"
        records.append(
            {
                "family_id": family_id,
                "endpoint": endpoint,
                "endpoint_role": (
                    "lead" if endpoint == "persistence_2002_contrast" else "support"
                ),
                "tolerance": tolerance,
                "interaction_estimate_100": float(interaction100["estimate"]),
                "interaction_classification_100": interaction100["classification"],
                "max_estimate_drift_75_to_100": max_drift,
                "max_mc_bound_drift_75_to_100": max_bound_drift,
                "max_mc_95_half_width_100": max_half_width,
                "max_source_class_proportion_drift_75_to_100": max_proportion_drift,
                "interaction_classification_stable_50_75_100": classification_pass,
                "estimate_and_bound_drift_pass": drift_pass,
                "mc_half_width_pass": half_width_pass,
                "source_class_proportion_pass": proportion_pass,
                "context_vs_source_max_estimate_difference_100": weighting_difference,
                "replicates_100_adequate": adequate,
                "recommended_action": action,
                "suggested_next_replicates": _recommended_replicates(
                    max_half_width, tolerance, adequate=adequate
                ),
            }
        )
    return pd.DataFrame.from_records(records)


def run_interaction_stability_audit(
    frame: pd.DataFrame,
    *,
    expected_row_count: int,
    expected_replicates: int = 100,
    expected_contexts: int = 15,
) -> dict[str, object]:
    qc = build_qc_checks(
        frame,
        expected_row_count=expected_row_count,
        expected_replicates=expected_replicates,
        expected_contexts=expected_contexts,
    )
    if not all(bool(check["passed"]) for check in qc):
        failed = [str(check["check_name"]) for check in qc if not check["passed"]]
        raise ValueError(f"Interaction audit QC failed: {failed}")
    tolerances = endpoint_tolerances(frame)
    windows: list[tuple[int, int, str, str]] = [
        (0, prefix, f"prefix_{prefix}", "prefix") for prefix in PREFIXES
    ]
    windows.extend(
        (start, start + 25, f"batch_{start:02d}_{start + 24:02d}", "batch")
        for start in range(0, expected_replicates, 25)
    )
    sources = pd.concat(
        [
            compute_source_effects(
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
    decision = build_replication_decision(prefix_summary)
    return {
        "qc": pd.DataFrame(qc),
        "sources": sources,
        "contexts": contexts,
        "prefix_summary": prefix_summary,
        "decision": decision,
        "seed_collisions": seed_collision_facts(frame),
        "tolerances": tolerances,
    }


def write_interaction_stability_audit(
    *,
    matched_outcomes_path: Path,
    output_dir: Path,
    expected_sha256: str,
    source_artifact: Path,
    source_execution_sha: str,
    goal014_record_sha: str,
    run_id: str,
    command: str,
    expected_row_count: int = 279500,
    expected_replicates: int = 100,
    expected_contexts: int = 15,
) -> dict[str, Path]:
    actual_sha256 = file_sha256(matched_outcomes_path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Matched-outcomes SHA-256 mismatch: {actual_sha256} != {expected_sha256}"
        )
    try:
        under_artifact = matched_outcomes_path.resolve().is_relative_to(
            source_artifact.resolve()
        )
    except ValueError:
        under_artifact = False
    if not under_artifact:
        raise ValueError("Matched outcomes are outside the authorized source artifact")

    frame = pd.read_csv(matched_outcomes_path, usecols=list(INPUT_COLUMNS))
    result = run_interaction_stability_audit(
        frame,
        expected_row_count=expected_row_count,
        expected_replicates=expected_replicates,
        expected_contexts=expected_contexts,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "qc": output_dir / "qc_summary.csv",
        "sources": output_dir / "source_effect_summary.csv",
        "contexts": output_dir / "context_effect_summary.csv",
        "prefix": output_dir / "prefix_stability_summary.csv",
        "decision": output_dir / "replication_decision.csv",
        "metadata": output_dir / "audit_metadata.json",
    }
    result["qc"].to_csv(paths["qc"], index=False)
    full_sources = result["sources"].loc[
        result["sources"]["window_label"] == "prefix_100"
    ]
    full_contexts = result["contexts"].loc[
        result["contexts"]["window_label"] == "prefix_100"
    ]
    full_sources.to_csv(paths["sources"], index=False)
    full_contexts.to_csv(paths["contexts"], index=False)
    result["prefix_summary"].to_csv(paths["prefix"], index=False)
    result["decision"].to_csv(paths["decision"], index=False)

    decisions = result["decision"]
    actions = set(decisions["recommended_action"])
    if "full_factorial_rerun" in actions:
        overall_action = "full_factorial_rerun"
    elif "targeted_extension" in actions:
        overall_action = "targeted_extension"
    elif "more_replicates_will_not_help" in actions:
        overall_action = "more_replicates_will_not_help"
    else:
        overall_action = "no_rerun"
    metadata = {
        "label": "goal026-module5-factorial-interaction-monte-carlo-audit",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "source_artifact": source_artifact.as_posix(),
        "matched_outcomes_path": matched_outcomes_path.as_posix(),
        "matched_outcomes_size": matched_outcomes_path.stat().st_size,
        "matched_outcomes_sha256": actual_sha256,
        "source_execution_sha": source_execution_sha,
        "goal014_record_sha": goal014_record_sha,
        "analysis_command": command,
        "raw_matched_outcomes_copied_locally": False,
        "families": list(FACTORIAL_FAMILIES),
        "endpoints": list(ENDPOINTS),
        "prefixes": list(PREFIXES),
        "primary_weighting": "equal variant_id x Module4 calibration-seed contexts",
        "sensitivity_weighting": "equal proposal_source_key rows",
        "interaction_definition": "joint_removal - trout_removal - climbing_removal",
        "seed_pairing_boundary": (
            "Common random numbers apply within each baseline-counterfactual pair; "
            "intervention IDs use distinct seed streams."
        ),
        "tolerances": {
            f"{family}|{endpoint}": tolerance
            for (family, endpoint), tolerance in result["tolerances"].items()
        },
        "seed_collision_facts": result["seed_collisions"],
        "qc_all_passed": bool(result["qc"]["passed"].all()),
        "overall_recommended_action": overall_action,
        "output_row_counts": {
            "qc_summary.csv": len(result["qc"]),
            "source_effect_summary.csv": len(full_sources),
            "context_effect_summary.csv": len(full_contexts),
            "prefix_stability_summary.csv": len(result["prefix_summary"]),
            "replication_decision.csv": len(result["decision"]),
        },
        "interpretation_boundary": (
            "Conditional expectation-scale interaction and Monte Carlo adequacy "
            "only; not posterior inference, attributable fraction, or proof of "
            "ecological synergy."
        ),
    }
    paths["metadata"].write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return paths
