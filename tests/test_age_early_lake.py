from __future__ import annotations

import copy
import inspect
import math

import numpy as np

from galaxias_model.age_demography import AgeDemography
from galaxias_model.age_early_lake import (
    LAKE_EXPECTED_TOTAL,
    LAKE_YEARS,
    generate_lake_observation,
    make_early_lake_source,
    run_early_lake_history,
)
from galaxias_model.age_runner import run_linked_history
import galaxias_model.age_early_lake as early_lake


# Explicit qualification budget: these tests execute at most eight histories.
QUALIFYING_HISTORY_COUNT = 8


def _source(age=6, index=0, quality="neutral", namespace="test-early-lake"):
    return make_early_lake_source(
        age, index, role="test", namespace=namespace, quality_regime=quality,
    )


def test_direct_sources_pair_quality_and_leave_restrictions_and_insurance_out():
    neutral = _source(index=2, quality="neutral")
    engineering = _source(index=2, quality="engineering")
    assert neutral["source_id"] == engineering["source_id"]
    assert neutral["source_seed"] == engineering["source_seed"]
    assert neutral["demography"] == engineering["demography"]
    assert neutral["scales"] == engineering["scales"]
    assert neutral["eta_refuge"] == engineering["eta_refuge"]
    assert neutral["recruitment_sigma"] == engineering["recruitment_sigma"]
    assert neutral["forcing_values"] != engineering["forcing_values"]
    assert neutral["forcing_values"]["PR032"] == 1.0
    assert 0.7 <= engineering["forcing_values"]["PR032"] <= 1.8
    assert not any(name in neutral for name in ("restriction", "ledger_timing", "removal_account"))
    assert set(neutral["scales"]) == {"pedder_lake", "pedder_refuge"}
    assert neutral["source_id"].count("R_") == 0


def test_source_strata_are_balanced_and_bounded_without_redraw():
    sources = [_source(index=i) for i in range(QUALIFYING_HISTORY_COUNT)]
    assert [source["index_stratum"] for source in sources] == ["below_one", "above_one"] * 4
    assert any(source["feasible"] for source in sources)
    assert any(not source["feasible"] and source["failure_reason"] for source in sources)
    assert all(source["demography"]["recruits_per_female"] <= 1200 for source in sources)
    assert all(math.isfinite(source["refuge_index"]) for source in sources)
    assert all(0.35 <= source["demography"]["lake_settlement"] <= 0.90 for source in sources)


def test_early_prefix_matches_old_linked_pedder_when_insurance_inputs_are_added_manually():
    source = _source(age=6, index=3, namespace="prefix")
    early = run_early_lake_history(source, restriction="R_C", seed=123)
    old_scales = {**source["scales"], "oberon": 30.0, "strathgordon": 20.0}
    old = run_linked_history(
        AgeDemography(**source["demography"]), source["forcing_values"], old_scales,
        restriction="R_C", eta_refuge=source["eta_refuge"], recruitment_sigma=source["recruitment_sigma"],
        strath_pre2007=1.0, seed=123, no_wild_removals=True,
        start_year=1965, end_year=1989, stochastic=True,
    )
    assert early["status"] == "valid"
    assert old["valid"]
    assert early["advance_calls"] == 25
    for year in range(1965, 1990):
        np.testing.assert_array_equal(early["annual_states"][year], old["annual_states"]["pedder"][year])


def test_history_has_exact_calendar_and_eight_age_lake_exposures():
    result = run_early_lake_history(_source(index=0), restriction="R_H", seed=456)
    assert result["status"] == "valid"
    assert result["advance_calls"] == 25
    assert tuple(result["annual_states"]) == tuple(range(1965, 1990))
    assert tuple(result["lake_exposures"].shape) == (8, 2)
    assert result["metadata"]["no_events"] is True
    assert result["metadata"]["site_id"] == "pedder"
    assert tuple(LAKE_YEARS) == (1976, 1977, 1978, 1979, 1980, 1983, 1986, 1989)


def test_infeasible_source_is_retained_without_redraw_or_rescue():
    source = _source(index=5)
    failed = copy.deepcopy(source)
    failed["feasible"] = False
    failed["failure_reason"] = "declared qualification failure"
    result = run_early_lake_history(failed, restriction="R_J", seed=7)
    assert result["status"] == "algebraically_infeasible"
    assert result["advance_calls"] == 0
    assert result["failure_reason"] == failed["failure_reason"]
    assert result["source"] == failed
    assert np.all(result["lake_exposures"] == 0)


def test_lake_generators_retain_means_raw_counts_and_digitisation_behaviour():
    exposures = np.column_stack((np.arange(1, 9, dtype=float), np.zeros(8)))
    poisson = generate_lake_observation(exposures, seed=10, generator="poisson")
    gamma = generate_lake_observation(exposures, seed=10, generator="gamma1")
    assert poisson["raw_site_counts"].shape == (8, 12)
    assert gamma["raw_site_counts"].shape == (8, 12)
    assert poisson["expected_total"] == LAKE_EXPECTED_TOTAL == 173.0
    assert np.all((poisson["visit_means"] == 0) | (np.abs(poisson["visit_means"] - poisson["raw_visit_means"]) <= 0.08 + 1e-12))
    assert np.all((gamma["visit_means"] == 0) | (np.abs(gamma["visit_means"] - gamma["raw_visit_means"]) <= 0.08 + 1e-12))
    assert not np.array_equal(poisson["raw_site_counts"], gamma["raw_site_counts"])


def test_all_zero_exposure_is_valid_all_zero_observation_and_profiles_can_pair():
    exposures = np.zeros((8, 2))
    first = generate_lake_observation(exposures, seed=88, profile="base")
    paired = generate_lake_observation(exposures, seed=88, profile="tau-quarter")
    assert first["status"] == "valid"
    assert first["all_zero_exposure"] is True
    assert np.all(first["raw_site_counts"] == 0)
    assert np.all(first["visit_means"] == 0)
    np.testing.assert_array_equal(first["raw_site_counts"], paired["raw_site_counts"])


def test_seed_and_api_validation_are_explicit_and_old_kernel_is_not_called():
    source = _source(index=6)
    assert source["source_seed"] >= 2**64
    assert "run_linked_history" not in inspect.getsource(early_lake)
    result = run_early_lake_history(source, restriction="R_T", seed=999)
    assert result["seed"] == 999
    assert set(result["process_diagnostics"]) == set(range(1965, 1990))
