import numpy as np
import pytest

from galaxias_model.age_scenarios import conditions_from_forcing, reference_demography, strathgordon_spawn_multiplier
from galaxias_model.age_scenarios import complete_event_calendar
from galaxias_model.age_demography import CountEvent


class Parameters:
    def value(self, key):
        return {"PR005": .5, "PR007": .2, "PR020": .4, "PR021": .3,
                "PR027": .7, "PR028": .6, "PR031": 2., "PR032": .8,
                "PR033": .5, "PR034": .25}[key]


def condition(restriction="R_J", h=.5, connected=1):
    return conditions_from_forcing(
        reference_demography(), Parameters(),
        {"H": h, "U": .4, "spawn_habitat_multiplier": 1.},
        {"connected": connected, "T": .8, "P": .9, "C_L": .5, "C_R": .2},
        restriction, post_habitat_refuge_fraction=.2, recruitment_sigma=.4,
    )


def test_climbing_is_nursery_only_and_does_not_drive_adult_movement():
    joint, trout = condition(), condition("R_T")
    assert joint.old_hazard_lake[0] - trout.old_hazard_lake[0] == pytest.approx(.35)
    np.testing.assert_array_equal(joint.old_hazard_lake[1:], trout.old_hazard_lake[1:])
    np.testing.assert_array_equal(joint.late_hazard_lake, trout.late_hazard_lake)
    assert joint.newborn_hazard_lake - trout.newborn_hazard_lake == pytest.approx(.35)
    assert joint.movement_probability == trout.movement_probability


def test_connectivity_not_habitat_gates_invaders():
    assert condition(h=0).old_hazard_lake[1] > 0
    assert condition(h=0, connected=0).old_hazard_lake[1] == 0


def test_habitat_restriction_retains_refuge_recruitment_loss():
    c = condition("R_H", h=1)
    assert c.refuge_limit_multiplier == pytest.approx(.2)
    assert c.old_hazard_refuge[0] == 0
    assert c.recruitment_multiplier < c.lake_limit_multiplier


def test_insurance_timing_is_birth_year_not_detection_year():
    assert strathgordon_spawn_multiplier(2006, pre_2007=.02) == .02
    assert strathgordon_spawn_multiplier(2007, pre_2007=.02) == 1
    with pytest.raises(ValueError):
        strathgordon_spawn_multiplier(2006, pre_2007=-.1)


def test_common_calendar_keeps_zero_effect_placeholders():
    calendar = (CountEvent(1, .1, 0), CountEvent(2, .5, 1))
    empty = complete_event_calendar(calendar, {})
    removal = complete_event_calendar(calendar, {2: CountEvent(2, .5, 1, remove_count=4)})
    assert [e.time for e in empty] == [e.time for e in removal]
    assert empty[1].remove_count == 0 and removal[1].remove_count == 4
    with pytest.raises(ValueError):
        complete_event_calendar(calendar, {2: CountEvent(2, .6, 1)})
