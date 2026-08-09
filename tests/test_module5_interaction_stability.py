from __future__ import annotations

import pandas as pd
import pytest

from galaxias_model.module5_interaction_stability import (
    ENDPOINTS,
    build_replication_decision,
    compute_context_effects,
    compute_source_effects,
    endpoint_tolerances,
    run_interaction_stability_audit,
)


def _source_key(family: str, variant: str, seed: int, proposal: str) -> str:
    return f"m4|{variant}|{seed}|{variant}_seed{seed}|{family}|{proposal}"


def _synthetic_frame(*, varying: bool = False) -> pd.DataFrame:
    sources = {
        "persistent_joint_cause": [
            ("v1", 1, "p1", (1.0, 2.0, 5.0)),
            ("v1", 1, "p2", (1.0, 2.0, 5.0)),
            ("v2", 2, "p3", (10.0, 10.0, 10.0)),
        ],
        "transient_perfect_storm": [
            ("v1", 1, "p1", (1.0, 1.0, 2.0)),
            ("v2", 2, "p2", (2.0, 2.0, 4.0)),
        ],
    }
    axes = (
        "status_quo",
        "no_trout_pressure",
        "no_climbing_pressure",
        "no_trout_or_climbing_pressure",
    )
    rows: list[dict[str, object]] = []
    unique_seed = 1000
    for family, definitions in sources.items():
        for proposal_seed, (variant, calibration_seed, proposal, effects) in enumerate(
            definitions, start=1
        ):
            source_key = _source_key(family, variant, calibration_seed, proposal)
            effect_by_axis = dict(zip(axes[1:], effects, strict=True))
            for axis in axes:
                for replicate in range(100):
                    base = 0.0 if axis == "status_quo" else effect_by_axis[axis]
                    noise = 0.0
                    if varying and axis != "status_quo":
                        noise = -0.1 if replicate % 2 == 0 else 0.1
                    stochastic_seed = unique_seed
                    unique_seed += 1
                    row = {
                        "proposal_source_key": source_key,
                        "module4_run_id": "m4",
                        "variant_id": variant,
                        "seed": calibration_seed,
                        "run_dir_name": f"{variant}_seed{calibration_seed}",
                        "family_id": family,
                        "proposal_id": proposal,
                        "proposal_seed": proposal_seed,
                        "stochastic_replicate_id": replicate,
                        "intervention_id": f"m5_{family}_{axis}",
                        "intervention_axis": axis,
                        "baseline_stochastic_seed": stochastic_seed,
                        "intervention_stochastic_seed": stochastic_seed,
                        "min_abundance_1992_2002_baseline": 100.0,
                    }
                    row.update({endpoint: base + noise for endpoint in ENDPOINTS})
                    rows.append(row)
    return pd.DataFrame(rows)


def test_source_interaction_and_context_equal_weighting() -> None:
    frame = _synthetic_frame()
    tolerances = endpoint_tolerances(frame)
    sources = compute_source_effects(
        frame,
        replicate_start=0,
        replicate_stop=100,
        window_label="prefix_100",
        window_type="prefix",
        tolerances=tolerances,
    )
    persistence = sources.loc[
        (sources["family_id"] == "persistent_joint_cause")
        & (sources["endpoint"] == "persistence_2002_contrast")
    ]
    assert sorted(persistence["additive_interaction"].tolist()) == [-10.0, 2.0, 2.0]

    contexts = compute_context_effects(sources)
    context_values = contexts.loc[
        (contexts["family_id"] == "persistent_joint_cause")
        & (contexts["endpoint"] == "persistence_2002_contrast")
    ]["additive_interaction"]
    assert sorted(context_values.tolist()) == [-10.0, 2.0]
    assert context_values.mean() == pytest.approx(-4.0)
    assert persistence["additive_interaction"].mean() == pytest.approx(-2.0)


def test_interaction_mc_variance_adds_independent_intervention_variances() -> None:
    frame = _synthetic_frame(varying=True)
    tolerances = endpoint_tolerances(frame)
    sources = compute_source_effects(
        frame,
        replicate_start=0,
        replicate_stop=100,
        window_label="prefix_100",
        window_type="prefix",
        tolerances=tolerances,
    )
    row = sources.loc[
        (sources["family_id"] == "persistent_joint_cause")
        & (sources["proposal_id"] == "p1")
        & (sources["endpoint"] == "persistence_2002_contrast")
    ].iloc[0]
    component_sum = sum(
        row[f"{effect}_mc_variance"]
        for effect in ("trout_removal", "climbing_removal", "joint_removal")
    )
    assert row["additive_interaction_mc_variance"] == pytest.approx(component_sum)
    assert component_sum > 0


def test_full_audit_builds_prefixes_batches_and_pass_decisions() -> None:
    frame = _synthetic_frame()
    result = run_interaction_stability_audit(
        frame,
        expected_row_count=len(frame),
        expected_replicates=100,
        expected_contexts=2,
    )
    assert result["qc"]["passed"].all()
    assert set(result["prefix_summary"]["window_label"]) == {
        "prefix_25",
        "prefix_50",
        "prefix_75",
        "prefix_100",
        "batch_00_24",
        "batch_25_49",
        "batch_50_74",
        "batch_75_99",
    }
    assert len(result["decision"]) == 6
    assert result["decision"]["replicates_100_adequate"].all()
    assert set(result["decision"]["recommended_action"]) == {"no_rerun"}
    assert result["seed_collisions"]["all_seed_key_count"] == len(frame)


def test_decision_fails_when_interaction_classification_changes() -> None:
    rows: list[dict[str, object]] = []
    for effect in (
        "trout_removal",
        "climbing_removal",
        "joint_removal",
        "additive_interaction",
    ):
        for n in (25, 50, 75, 100):
            estimate = 0.0
            if effect == "additive_interaction" and n == 100:
                estimate = 0.1
            rows.append(
                {
                    "family_id": "persistent_joint_cause",
                    "endpoint": "persistence_2002_contrast",
                    "window_label": f"prefix_{n}",
                    "window_type": "prefix",
                    "replicate_start": 0,
                    "replicate_stop_exclusive": n,
                    "n_replicates_per_intervention": n,
                    "tolerance": 0.01,
                    "effect": effect,
                    "weighting": "context_equal",
                    "estimate": estimate,
                    "mc_se": 0.0001,
                    "mc_95_half_width": 0.000196,
                    "mc_95_low": estimate - 0.000196,
                    "mc_95_high": estimate + 0.000196,
                    "classification": (
                        "more_than_additive"
                        if effect == "additive_interaction" and n == 100
                        else (
                            "near_additive_or_unresolved"
                            if effect == "additive_interaction"
                            else "near_zero"
                        )
                    ),
                    "source_negative_proportion": 0.0,
                    "source_near_zero_proportion": 1.0,
                    "source_positive_proportion": 0.0,
                    "source_count": 2,
                    "context_count": 2,
                    "context_min": estimate,
                    "context_max": estimate,
                }
            )
        rows.append({**rows[-1], "weighting": "source_equal"})
    decision = build_replication_decision(pd.DataFrame(rows))
    assert len(decision) == 1
    assert not bool(decision.iloc[0]["replicates_100_adequate"])
    assert decision.iloc[0]["recommended_action"] == "full_factorial_rerun"
    assert decision.iloc[0]["suggested_next_replicates"] == "250"


def test_decision_targets_extension_when_only_source_proportions_drift() -> None:
    rows: list[dict[str, object]] = []
    for effect in (
        "trout_removal",
        "climbing_removal",
        "joint_removal",
        "additive_interaction",
    ):
        for n in (25, 50, 75, 100):
            near_zero = 0.8 if n < 100 else 0.7
            rows.append(
                {
                    "family_id": "persistent_joint_cause",
                    "endpoint": "persistence_2002_contrast",
                    "window_label": f"prefix_{n}",
                    "window_type": "prefix",
                    "replicate_start": 0,
                    "replicate_stop_exclusive": n,
                    "n_replicates_per_intervention": n,
                    "tolerance": 0.01,
                    "effect": effect,
                    "weighting": "context_equal",
                    "estimate": -0.02 if effect == "additive_interaction" else 0.03,
                    "mc_se": 0.001,
                    "mc_95_half_width": 0.00196,
                    "mc_95_low": -0.02196 if effect == "additive_interaction" else 0.02804,
                    "mc_95_high": -0.01804 if effect == "additive_interaction" else 0.03196,
                    "classification": (
                        "less_than_additive"
                        if effect == "additive_interaction"
                        else "positive"
                    ),
                    "source_negative_proportion": 0.2,
                    "source_near_zero_proportion": near_zero,
                    "source_positive_proportion": 1.0 - 0.2 - near_zero,
                    "source_count": 10,
                    "context_count": 2,
                    "context_min": -0.03,
                    "context_max": 0.04,
                }
            )
        rows.append({**rows[-1], "weighting": "source_equal"})
    decision = build_replication_decision(pd.DataFrame(rows)).iloc[0]
    assert not bool(decision["replicates_100_adequate"])
    assert decision["recommended_action"] == "targeted_extension"
    assert decision["suggested_next_replicates"] == "250"
