import math
import json

import numpy as np
import pandas as pd
import pytest

from galaxias_model.abundance_detection import (
    BLOCKS, EPISODE_FIELDS, history_log_likelihood, summarize_log_likelihood,
)


def frame(values):
    return pd.DataFrame([values], columns=EPISODE_FIELDS)


def test_binary_observation_law_and_zero_support():
    q = .02
    x = frame([10.] * 6 + [0.] * 7)
    assert history_log_likelihood(x, q)[0] == pytest.approx(6 * math.log(1 - (1 - q)**10))
    x.iloc[0, 0] = 0
    assert history_log_likelihood(x, q)[0] == -math.inf
    x.iloc[0, 0] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        history_log_likelihood(x, q)


def test_shared_quality_integrates_joint_mixed_sign_blocks():
    q = .2
    counts = np.arange(1, 14, dtype=float)
    products = []
    for factor in (.5, 1.5):
        miss = (1 - factor*q)**counts
        products.append(np.concatenate([1-miss[:6], miss[6:]]))
    expected = math.prod(.5*np.prod(products[0][list(b)]) + .5*np.prod(products[1][list(b)]) for b in BLOCKS)
    actual = history_log_likelihood(frame(counts), q, "shared_quality")[0]
    assert actual == pytest.approx(math.log(expected))
    independent = math.prod(.5*products[0] + .5*products[1])
    assert history_log_likelihood(frame(counts), q, "independent_quality")[0] == pytest.approx(math.log(independent))
    assert not np.isclose(actual, math.log(independent))


def test_homogeneous_scale_alias_and_underflow_preserve_log_support():
    q, scale = .02, 10
    counts = np.arange(1, 14, dtype=float)
    transformed_q = -math.expm1(math.log1p(-q)/scale)
    assert history_log_likelihood(frame(counts), q)[0] == pytest.approx(
        history_log_likelihood(frame(scale*counts), transformed_q)[0])
    r = summarize_log_likelihood(np.array([-2000., -2000.]), {"survival": np.array([0., 1.])})
    assert r["log_mean_compatibility"] == -2000
    assert r["positive_supported_count"] == 2
    assert r["weighted_survival"] == .5
    assert r["weighted_survival_mc_se"] == .5
    assert r["mean_compatibility"] == 0  # Representation underflow, not unsupported.


def test_endpoint_ratios_and_unsupported_sources():
    r = summarize_log_likelihood(np.log([.25, .75]), {"survival": np.array([0., 1.])})
    assert r["weighted_survival"] == pytest.approx(.75)
    assert r["weight_ess"] == pytest.approx(1.6)
    assert r["weighted_survival_mc_se"] == pytest.approx(.375)
    r = summarize_log_likelihood(np.array([-math.inf, -math.inf]), {"survival": np.array([0., 1.])})
    assert r["positive_supported_count"] == 0
    assert math.isnan(r["weighted_survival"])


def test_common_model_two_1996_events_share_quality_and_preserve_extraction_order():
    from galaxias_model.abundance_detection import COMMON_EPISODE_FIELDS, common_history_log_likelihood
    q = .2
    values = [10.]*5 + [5., 1.] + [0.]*7
    data = pd.DataFrame([values], columns=COMMON_EPISODE_FIELDS)
    detect = lambda n, probability: 1 - (1-probability)**n
    expected = detect(10, q)**5 * detect(5, q) * detect(1, q)
    assert common_history_log_likelihood(data, q)[0] == pytest.approx(math.log(expected))
    early = sum(.5*detect(10, m*q)**5 for m in (.5, 1.5))
    both_1996 = sum(.5*detect(5, m*q)*detect(1, m*q) for m in (.5, 1.5))
    assert common_history_log_likelihood(data, q, "shared_quality")[0] == pytest.approx(math.log(early*both_1996))
    data.loc[0, "pos_N_R_1996_march"] = 0
    assert common_history_log_likelihood(data, q)[0] == -math.inf


def test_constant_refuge_reference_full_likelihood_and_optimum():
    from galaxias_model.abundance_detection import COMMON_EPISODE_FIELDS, Q_SCENARIOS, common_history_log_likelihood
    for q in Q_SCENARIOS:
        optimum = math.log(5/12)/math.log1p(-q)
        counts = np.array([.99, 1., 1.01])*optimum
        data = pd.DataFrame([[n]*7 + [0.]*2 + [n]*5 for n in counts], columns=COMMON_EPISODE_FIELDS)
        observed = common_history_log_likelihood(data, q)
        expected = 7*np.log(-np.expm1(counts*math.log1p(-q))) + 5*counts*math.log1p(-q)
        assert observed == pytest.approx(expected)
        assert observed[1] > max(observed[0], observed[2])


def test_fixed_cohort_analysis_and_tamper_rejection(tmp_path):
    from scripts.analyze_detection_replay import analyze, file_hash, old_profile_logs

    replay = tmp_path / "replay"
    replay.mkdir()
    rows, members = [], []
    for proposal, survival in (("p1", 0), ("p2", 1)):
        identity = dict(search_seed=11, family_id="fixture", proposal_id=proposal)
        for _ in range(2):
            rows.append({**identity, **dict(zip(EPISODE_FIELDS, [10]*6 + [1]*7)),
                         "surviving_2002": survival, "n_total_2002": survival*5})
        members.append({**identity, "profile": "repair_presence_only", "cohort": "global"})
    # Reuse in a second cohort/profile must not duplicate a source in the union.
    members.extend([{**members[0], "cohort": "family"},
                    {**members[0], "profile": "another_profile"}])
    membership = tmp_path / "membership.csv"
    pd.DataFrame(members).to_csv(membership, index=False)
    compact = replay / "compact_abundance_replay.csv.gz"
    data = pd.DataFrame(rows)
    data.to_csv(compact, index=False)
    from galaxias_model.conditional_observation import CONDITIONAL_PROFILES
    for profile, (p, dependence) in CONDITIONAL_PROFILES.items():
        occupied = 2 if dependence == "shared_window" else 7
        assert old_profile_logs(data, profile) == pytest.approx(np.full(4, occupied*math.log1p(-p)))
    manifest = {"status": "complete", "scope": "conditional_detection_replay_preparation",
                "replicates": 2, "source_count": 2,
                "outputs": {compact.name: file_hash(compact)},
                "inputs": {"membership": file_hash(membership)}}
    (replay / "replay_manifest.json").write_text(json.dumps(manifest))
    output = tmp_path / "analysis"
    analyze(replay, membership, output)
    cohorts = pd.read_csv(output / "fixed_cohort_comparison.csv")
    assert cohorts.n_sources.eq(2).all()
    assert cohorts.weighted_surviving_2002.to_numpy() == pytest.approx(np.full(len(cohorts), .5))
    assert len(pd.read_csv(output / "source_observation_comparison.csv")) == 34
    membership.write_text(membership.read_text() + "\n")
    with pytest.raises(ValueError, match="membership changed"):
        analyze(replay, membership, tmp_path / "tampered")
    assert not (tmp_path / "tampered").exists()
