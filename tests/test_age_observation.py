import math
import numpy as np
import pytest

from galaxias_model.age_observation import accessible_abundance, at_least_one_log_probability, conditional_late_zero_log_probability
from galaxias_model.age_observation import conditional_capture_log_probability, lake_capture_log_score


def test_conditioning_cancels_shared_abundance_scale():
    score = conditional_late_zero_log_probability(430., 10.)
    assert score == pytest.approx(68 * math.log(430 / 440))
    assert score == pytest.approx(conditional_late_zero_log_probability(4300., 100.))


def test_bridge_is_monotone_in_late_exposure_and_zero_effort_is_uninformative():
    assert conditional_late_zero_log_probability(43., 0.) == 0
    assert conditional_late_zero_log_probability(43., 5.) > conditional_late_zero_log_probability(43., 20.)
    assert conditional_late_zero_log_probability(0., 0.) == -math.inf
    assert conditional_late_zero_log_probability(0., 0., total_captures=0) == 0


def test_accessibility_does_not_count_unobserved_compartment_or_ages():
    state = np.ones((2, 2, 7))
    state[0] *= 100
    assert accessible_abundance(state, 1, np.array([0.] + [1.] * 6)) == 12
    assert at_least_one_log_probability(0., .1) == -math.inf
    assert at_least_one_log_probability(12., .1) == pytest.approx(math.log1p(-math.exp(-1.2)))


@pytest.mark.parametrize("early,late", [(-1, 0), (1, float("nan")), (float("inf"), 0)])
def test_invalid_exposures_rejected(early, late):
    with pytest.raises(ValueError):
        conditional_late_zero_log_probability(early, late)


def test_three_block_score_matches_multinomial_and_cancels_scale():
    exposures = np.array([43., .5, 1.])
    expected = math.log(69) + 68 * math.log(43 / 44.5) + math.log(.5 / 44.5)
    assert conditional_capture_log_probability([68, 1, 0], exposures) == pytest.approx(expected)
    assert conditional_capture_log_probability([68, 1, 0], 1000 * exposures) == pytest.approx(expected)
    assert conditional_capture_log_probability([68, 0], [43., 1.]) == pytest.approx(
        conditional_late_zero_log_probability(43., 1.))


def test_conditional_multinomial_normalizes_and_respects_impossible_positive():
    scores = [conditional_capture_log_probability([a, b, 3-a-b], [1., 2., 3.])
              for a in range(4) for b in range(4-a)]
    assert sum(math.exp(x) for x in scores) == pytest.approx(1.)
    assert conditional_capture_log_probability([68, 1, 0], [43., 0., 1.]) == -math.inf
    with pytest.raises(ValueError):
        conditional_capture_log_probability([68., 1., 0.], [43., 2., 1.])


def test_lake_score_is_explicitly_tempered_not_a_rounded_count_likelihood():
    raw = lake_capture_log_score(5., 3., early_catch_equivalent=173.2, power=1.)
    tempered = lake_capture_log_score(5., 3., early_catch_equivalent=173.2, power=1/12)
    assert tempered == pytest.approx(raw / 12)
    assert lake_capture_log_score(5., 0., early_catch_equivalent=173.2, power=1/12) == 0


def test_synthetic_lake_positive_catches_are_not_forced_to_historical_zeros():
    score = lake_capture_log_score(5., 3., early_catch_equivalent=20.5,
                                   late_catch_equivalent=3.5, power=.25)
    assert score == pytest.approx(.25*(20.5*math.log(5/8)+3.5*math.log(3/8)))
    assert lake_capture_log_score(5., 0., early_catch_equivalent=20.5,
                                  late_catch_equivalent=3.5, power=.25) == -math.inf
