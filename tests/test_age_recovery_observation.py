import numpy as np

from galaxias_model.age_recovery_observation import decision_profiles, exposures, generate_observations


def feature():
    return dict(creek_early=[[3,20]]*20, creek_feb=[2,4], creek_late=[[0,1]]*60,
                lake=[[100,10]]*5+[[0,0]]*3, jan=[0,4], march=[0,2],
                ob_early=[[1,2,3]]*3, ob96=[1,2,3], ob97=[1,2,3], ob99=[1,2,3],
                ob12=[1,2,3], sg_early=[[0,0,3]]*5, sg08=[1,2,3], early_minimum=25)


def test_profile_panel_is_fixed_and_covers_every_agreed_level():
    profiles = decision_profiles()
    assert len(profiles) == len({p['profile_id'] for p in profiles}) == 540
    assert sum(p['panel']=='base' for p in profiles) == 36
    assert {p['creek_age0'] for p in profiles} == {0.,.25,1.}
    assert {p['lake_power'] for p in profiles} == {1/12,.25,1.}


def test_exposures_use_observed_cohorts_and_temporal_averaging_only():
    p = decision_profiles()[0]
    creek,lake,binary=exposures([feature()],p)
    np.testing.assert_allclose(creek[0],[860,8,p['K']*p['rho']])
    np.testing.assert_allclose(lake[0],[500,0])
    assert binary[0,0] == 4 and binary[0,2] == 6 and binary[0,9] == 0


def test_analysis_powers_do_not_redraw_synthetic_data():
    p = {**decision_profiles()[0], 'q':1.}
    a=generate_observations([feature()],[('fixture',1)],[False],p,generator='fixed_creek_total')
    b=generate_observations([feature()],[('fixture',1)],[False],
        {**p,'creek_power':.25,'lake_power':1.},generator='fixed_creek_total')
    assert a['creek_counts'].sum() == 69
    for key in ('creek_counts','lake_equivalents','binary_counts','coherent'):
        np.testing.assert_array_equal(a[key],b[key])


def test_intervention_conflicts_are_retained_without_observation_replacement():
    f=feature(); f['jan']=[0,0]
    p=decision_profiles()[0]
    a=generate_observations([f],[('fixture',2)],[True],p,generator='poisson')
    assert not a['coherent'][0]
    assert a['binary_counts'][0,0] == 0
    assert 'january_capture_minimum' in a['failure_reasons'][0]
def test_gamma_quality_is_shared_by_adult_and_juvenile_records_from_one_visit():
    import numpy as np
    from galaxias_model.age_recovery_observation import binary_visit_quality
    rng = np.random.default_rng(241)
    quality = np.stack([binary_visit_quality(rng) for _ in range(100)])
    np.testing.assert_array_equal(quality[:, 4], quality[:, 5])
    np.testing.assert_array_equal(quality[:, 7], quality[:, 8])
    assert not np.array_equal(quality[:, 4], quality[:, 7])
