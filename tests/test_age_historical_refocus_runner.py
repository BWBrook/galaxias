"""Failure modes specific to the additive refocus driver, without simulations."""
import math
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_age_historical_refocus import endpoint_and_campaign_features, logmeanexp, reconstruct_compartment_breeders


def test_training_utility_is_arithmetic_with_failed_attempts():
    assert logmeanexp([0., -math.inf]) == pytest.approx(-math.log(2))
    assert math.exp(logmeanexp([math.log(.2), math.log(.8), -math.inf, -math.inf])) == pytest.approx(.25)
    assert logmeanexp([-math.inf, -math.inf]) == -math.inf
    with pytest.raises(ValueError):
        logmeanexp([])


def test_endpoint_times_and_campaign_boundaries_are_distinct():
    states = {}
    for year, number in ((1987, 2), (1988, 4), (1989, 10), (1990, 20), (1991, 30), (2002, 0)):
        state = np.zeros((2, 2, 7))
        state[0, 0, 1] = number
        if year in (1990, 1991):
            state[0, 0, 0] = number
        states[str(year)] = state
    diagnostics = {"2002": {"pre_spawn_females": 1, "pre_spawn_males": 1,
                            "pre_spawn_by_compartment_sex": [[1, 0], [0, 1]]}}
    value = endpoint_and_campaign_features({"annual_states": {"pedder": states},
                                           "per_year_diagnostics": {"pedder": diagnostics}})
    assert value["terminal_pair"]  # breeding before a zero end-year state
    assert not value["terminal_same_compartment_pair"]
    assert not value["terminal_age1plus10"]
    assert value["campaign_exposures"] == {
        "electro_start": 3., "electro_end": 7., "electro_mid": 5., "larvae": 25.,
    }


def test_missing_compartment_diagnostics_cannot_be_reported_as_no_pair():
    state = np.zeros((2, 2, 7))
    history = {"annual_states": {"pedder": {2002: state}},
               "per_year_diagnostics": {"pedder": {2002: {"pre_spawn_females": 1, "pre_spawn_males": 1}}}}
    with pytest.raises(ValueError, match="compartment endpoint"):
        endpoint_and_campaign_features(history)


def test_compartment_reconstruction_preserves_the_empty_terminal_slot():
    source = {"demography": {"annual_survival": [.4]*6, "breeding_probability": [0, 0, .2, 1, 1, 1, 1],
                            "recruits_per_female": 5.}}
    state = np.zeros((2, 2, 7))
    state[0, 0, 2], state[1, 1, 2] = 2, 3
    history = {"checkpoint_states": {"pedder": [{"year": 2002, "time": .75, "label": "transfer_2002_late", "state": state}]},
               "per_year_diagnostics": {"pedder": {2002: {"pre_spawn_females": 2, "pre_spawn_males": 3}}}}
    assert reconstruct_compartment_breeders(history, source, 19).tolist() == [[2., 0.], [0., 3.]]
    state[0, 0, 6] = 1
    with pytest.raises(ValueError, match="eligible state"):
        reconstruct_compartment_breeders(history, source, 19)
