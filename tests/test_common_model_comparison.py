from __future__ import annotations

import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

TEST_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEST_ROOT))

from scripts.analyze_common_model_comparison import (
    _factual_weights,
    add_q_specific_reference,
    analyze,
    annual_refuge_profiles,
    compatibility_map,
)
from scripts.run_common_model_comparison import (
    EFFECT_PARAMETERS,
    IDENTITY,
    ROOT,
    RunPlan,
    _apply_restriction,
    _base_parameter_draws,
    _history_task,
    history_seed,
    preflight_history_seeds,
    production_budget,
    rank_membership,
    require_archive_input_binding,
    source_id,
    summarize_source,
    zero_source_summary,
)
from galaxias_model.abundance_detection import COMMON_EPISODE_FIELDS


def test_budget_seed_domains_and_uint64_roundtrip(tmp_path: Path) -> None:
    assert production_budget() == {
        "archived_replay": 712_000,
        "search": 1_843_200,
        "refine_max": 1_966_080,
        "validate_max": 1_966_080,
        "counterfactual_max": 491_520,
        "total_max": 7_071_040,
        "paired_toggle_max": 92_160,
        "hard_ceiling": 7_100_000,
        "remaining_for_prescribed_checks": 28_960,
    }
    ids = pd.DataFrame({"source_id": ["common-production|a", "common-production|b"]})
    check = preflight_history_seeds(ids, "search", 3)
    assert check["unique_seed_count"] == 12
    search = history_seed(ids.source_id[0], "search", 1, "demographic")
    refine = history_seed(ids.source_id[0], "refine", 1, "demographic")
    environment = history_seed(ids.source_id[0], "search", 1, "environment")
    assert len({search, refine, environment}) == 3
    assert min(search, refine, environment) >= 2**63 + 1000
    path = tmp_path / "seeds.csv"
    pd.DataFrame({"seed": [search, refine, environment]}).to_csv(path, index=False)
    assert pd.read_csv(path, dtype={"seed": "uint64"}).seed.astype(object).tolist() == [search, refine, environment]


def test_zero_inclusive_effect_draws_and_restriction_effective_rows() -> None:
    draws = _base_parameter_draws(ROOT / "data", 17, 4)
    priors = pd.read_csv(ROOT / "data" / "parameter_priors.csv").set_index("parameter_id")
    for _, draw in draws.groupby("proposal_index"):
        values = draw.set_index("parameter_id").value_natural
        for parameter in EFFECT_PARAMETERS:
            assert 0 <= values[parameter] <= float(priors.loc[parameter, "upper_bound"])
            assert draw.loc[draw.parameter_id.eq(parameter), "sampling_transform"].iloc[0] == "identity"
        assert values["PR020"] >= values["PR021"]
        habitat = _apply_restriction(draw, "R_H").set_index("parameter_id")
        assert (habitat.loc[["PR020", "PR021", "PR027", "PR028"], "value_natural"] == 0).all()
        assert (habitat.loc[["PR020", "PR021", "PR027", "PR028"], "parameter_status"] == "fixed_zero").all()
        assert habitat.loc["PR033", "sampled_flag"]


def _raw_histories(n: int, *, early: bool) -> pd.DataFrame:
    identity = {"search_seed": 1, "configuration": "base", "restriction": "R_J",
                "wave": 1, "source_index": 1, "source_id": "source"}
    rows = []
    for index in range(n):
        row = {**identity, "replicate_index": index + 1, "removals_valid": True,
               "early_early_patterns_pass": early,
               "endpoint_terminal_survival": float(index % 2),
               "annual_N_R_1965": float(index + 1)}
        row.update({field: 10.0 for field in COMMON_EPISODE_FIELDS})
        rows.append(row)
    return pd.DataFrame(rows)


def test_source_summary_preserves_zero_event_uncertainty_and_annual_profiles() -> None:
    summary = summarize_source(_raw_histories(64, early=False), True)
    expected = 1 - .05 ** (1 / 64)
    assert summary.early_pattern_zero_one_sided_upper95.eq(expected).all()
    assert summary.early_pattern_upper95.eq(expected).all()
    assert summary.joint_positive_support_upper95.eq(expected).all()
    assert summary.joint_upper95.eq(expected).all()
    assert summary.joint_positive_supported_count.eq(0).all()
    assert {"unconditional_N_R_1965", "weighted_N_R_1965", "unconditional_N_R_presence_1965"}.issubset(summary)
    annual = annual_refuge_profiles(summary)
    assert annual.year.unique().tolist() == [1965]
    assert len(annual) == 12


def test_rank_membership_keeps_profile_ancestry_and_underflow_support() -> None:
    rows = []
    for source_index, score in enumerate((-10.0, -20.0, -math.inf), start=1):
        for q in (0.005, 0.02):
            rows.append({"search_seed": 1, "configuration": "base", "restriction": "R_J",
                         "wave": 1, "source_index": source_index, "source_id": f"s{source_index}",
                         "q": q, "observation_model": "homogeneous", "primary_profile": True,
                         "viable": True, "log_joint_mean": score,
                         "early_pattern_probability": .5, "log_binary_mean": -1.0})
    membership = rank_membership(pd.DataFrame(rows), 2)
    assert len(membership) == 4
    assert set(membership.source_id) == {"s1", "s2"}
    assert all(ranks == [1, 2] for ranks in
               membership.groupby(["q", "observation_model"]).selection_rank.apply(list))


def test_q_specific_reference_and_empty_cell_are_not_cross_ranked() -> None:
    summary = pd.DataFrame([
        {"configuration": "base", "restriction": "R_H", "search_seed": 1, "wave": 1,
         "source_index": 1, "source_id": "a", "q": .005, "observation_model": "homogeneous",
         "log_joint_mean": -2.0, "joint_mc_se": .01, "joint_mc_relative_se": .01,
         "early_pattern_lower95": .9, "early_pattern_upper95": 1.0,
         "joint_lower95": .1, "joint_upper95": .2, "joint_mc_qualified": True,
         "early_pattern_probability": .95, "joint_mean": .12, "viable": True, "K_R": 10},
        {"configuration": "base", "restriction": "R_J", "search_seed": 1, "wave": 1,
         "source_index": 2, "source_id": "b", "q": .02, "observation_model": "homogeneous",
         "log_joint_mean": -1.0, "joint_mc_se": .01, "joint_mc_relative_se": .01,
         "early_pattern_lower95": .9, "early_pattern_upper95": 1.0,
         "joint_lower95": .1, "joint_upper95": .2, "joint_mc_qualified": True,
         "early_pattern_probability": .95, "joint_mean": .2, "viable": True, "K_R": 30},
    ])
    referenced = add_q_specific_reference(summary)
    assert referenced.delta_log_W.eq(0).all()
    ledger = pd.DataFrame([
        {"configuration": "base", "restriction": "R_T", "q": .005,
         "observation_model": "homogeneous", "validate_source_count": 0}
    ])
    result = compatibility_map(referenced, ledger)
    empty = result.loc[result.restriction.eq("R_T")]
    assert len(empty) == 9
    assert empty.status.eq("not_found_at_cap").all()


def test_one_real_task_retains_compact_annual_evidence() -> None:
    draw = _apply_restriction(_base_parameter_draws(ROOT / "data", 31, 1), "R_J")
    metadata = {"run_mode": "smoke", "search_seed": 31, "configuration": "base",
                "restriction": "R_J", "wave": 1, "source_index": 1}
    task = {**metadata, "source_id": source_id(metadata), "parameter_rows": draw.to_dict("records"),
            "data_dir": str(ROOT / "data"), "phase": "search", "replicates": 2,
            "overshoot_removed": False}
    result = _history_task(task)
    assert len(result["histories"]) == 2
    assert len(result["annual_refuge"]) == 38
    assert all(f"annual_N_R_{year}" in result["histories"][0] for year in range(1965, 2003))
    summary = summarize_source(pd.DataFrame(result["histories"]), True)
    assert len(summary) == 12
    assert "weighted_N_R_2002" in summary


def test_viability_failure_has_no_fake_replicates() -> None:
    source = {"search_seed": 1, "configuration": "base", "restriction": "R_H",
              "wave": 1, "source_index": 1, "source_id": "vfail"}
    summary = zero_source_summary(source)
    assert len(summary) == 12
    assert summary.replicate_count.eq(0).all()
    assert summary.joint_positive_support_upper95.isna().all()


def test_archive_input_binding_rejects_same_coordinates_from_another_search(tmp_path: Path) -> None:
    search_a = tmp_path / "search-a"
    search_b = tmp_path / "search-b"
    search_a.mkdir(); search_b.mkdir()
    (search_a / "run_manifest.json").write_text('{"archive":"a"}\n', encoding="utf-8")
    (search_b / "run_manifest.json").write_text('{"archive":"b"}\n', encoding="utf-8")
    from scripts.run_common_model_comparison import file_hash
    refine_manifest = {
        "input_archives": [{
            "path": str(search_a.resolve()),
            "run_manifest": file_hash(search_a / "run_manifest.json"),
        }]
    }
    require_archive_input_binding(refine_manifest, search_a)
    with pytest.raises(ValueError, match="does not bind supplied input"):
        require_archive_input_binding(refine_manifest, search_b)


def test_no_retained_sources_flow_to_explicit_empty_compatibility_map(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.analyze_common_model_comparison as analysis_module
    from scripts.run_common_model_comparison import empty_history_frame, file_hash, rank_membership

    search = tmp_path / "search"; refine = tmp_path / "refine"; validate = tmp_path / "validate"
    for phase, path in (("search", search), ("refine", refine), ("validate", validate)):
        path.mkdir()
        (path / "run_manifest.json").write_text(f'{{"phase":"{phase}"}}\n', encoding="utf-8")
    refine_manifest = {"phase": "refine", "input_archives": [
        {"path": str(search.resolve()), "run_manifest": file_hash(search / "run_manifest.json")}]}
    validate_manifest = {"phase": "validate", "input_archives": [
        {"path": str(search.resolve()), "run_manifest": file_hash(search / "run_manifest.json")},
        {"path": str(refine.resolve()), "run_manifest": file_hash(refine / "run_manifest.json")} ]}
    manifests = {"search": {"phase": "search"}, "refine": refine_manifest, "validate": validate_manifest}
    monkeypatch.setattr(analysis_module, "verify_archive", lambda path, phase=None: manifests[phase])
    monkeypatch.setattr(analysis_module, "require_runtime_match", lambda *manifests: None)

    source = {"search_seed": 1, "configuration": "base", "restriction": "R_H",
              "wave": 1, "source_index": 1, "source_id": "vfail", "proposal_kind": "global",
              "K_L": 10.0, "K_R": 4.0, "PR011": 1.0, "K_R_over_PR011": 4.0, "PR033": .2}
    pd.DataFrame([source]).to_csv(search / "sources.csv", index=False)
    search_summary = zero_source_summary(source)
    search_summary.to_csv(search / "source_summary.csv", index=False)
    rank_membership(search_summary, 1).to_csv(search / "refine_selection_membership.csv", index=False)
    empty_sources = pd.DataFrame(columns=list(source))
    empty_summary = search_summary.iloc[0:0]
    for directory in (refine, validate):
        empty_sources.to_csv(directory / "sources.csv", index=False)
        empty_summary.to_csv(directory / "source_summary.csv", index=False)
    rank_membership(empty_summary, 1).to_csv(refine / "validate_selection_membership.csv", index=False)
    empty_history_frame().to_csv(validate / "raw_histories.csv.gz", index=False, compression="gzip")

    output = tmp_path / "analysis"
    analyze(search, refine, validate, output)
    compatibility = pd.read_csv(output / "compatibility_map.csv")
    assert len(compatibility) == 6 * 4 * 4 * 3 * 3 * 3
    assert compatibility.status.eq("not_found_at_cap").all()
    assert pd.read_csv(output / "annual_refuge_by_profile.csv.gz").empty


def test_finite_factual_support_is_retained_when_numeric_weight_underflows() -> None:
    rows = []
    for index in range(2):
        row = {"early_early_patterns_pass_factual": True, "removals_valid_factual": True}
        for field_index, field in enumerate(COMMON_EPISODE_FIELDS):
            is_positive = field_index < 7
            row[f"{field}_factual"] = 10.0 if is_positive else (0.0 if index == 0 else 1_000_000.0)
        rows.append(row)
    weights, finite = _factual_weights(pd.DataFrame(rows), .2, "homogeneous")
    assert finite.tolist() == [True, True]
    assert weights[0] == pytest.approx(1.0)
    assert weights[1] == 0.0
