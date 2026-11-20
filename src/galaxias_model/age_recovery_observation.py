"""Frozen observation profiles and synthetic data for endpoint qualification.

Features contain only declared observation checkpoints. Terminal labels are
kept separately and are never inputs to observation generation or scoring.
"""
from __future__ import annotations

from itertools import product
import math

import numpy as np

from galaxias_model.age_sources import keyed_seed


BINARY_RECORDS = (
    "pedder_january_1996", "pedder_march_1996", "oberon_1993_1995",
    "oberon_february_1996_adult", "oberon_march_1997_adult",
    "oberon_march_1997_juvenile", "oberon_1999", "oberon_2012_adult",
    "oberon_2012_juvenile", "strath_2001_2005_juvenile", "strath_2008_juvenile",
)
LAKE_YEARS = (1976, 1977, 1978, 1979, 1980, 1983, 1986, 1989)
# Adult/juvenile outcomes from one visit share its latent survey quality.
BINARY_VISIT_GROUPS = np.asarray((0, 1, 2, 3, 4, 4, 5, 6, 6, 7, 8))


def binary_visit_quality(rng):
    return rng.gamma(1., 1., 9)[BINARY_VISIT_GROUPS]


def _array(value):
    return np.asarray(value, dtype=float)


def _age_pair(state, compartment=None):
    x = _array(state)
    ages = x.sum(axis=(0, 1)) if compartment is None else x[compartment].sum(axis=0)
    return [float(ages[0]), float(ages[1:].sum())]


def extract_features(history: dict) -> dict:
    """Compress a valid linked history without exposing terminal state to scores."""
    if not history['valid']:
        raise ValueError('cannot extract observation features from an invalid history')
    checkpoints = history['checkpoint_states']
    def one(site, label):
        matches = [x['state'] for x in checkpoints[site] if x['label'] == label]
        if len(matches) != 1:
            raise ValueError(f'expected exactly one {site}:{label}, got {len(matches)}')
        return _array(matches[0])
    def window(site, prefix):
        matches = [x for x in checkpoints[site] if x['label'].startswith(prefix)]
        return [x['state'] for x in sorted(matches, key=lambda x:(x['year'], x['time']))]
    early = window('pedder', 'early_refuge_')
    late = window('pedder', 'late_refuge_')
    if len(early) != 20 or len(late) != 60:
        raise ValueError('the complete early and late monthly calendar is required')
    jan = one('pedder', 'january_1996_pre_removal')
    march = one('pedder', 'march_1996_record')
    ob96 = one('oberon', 'oberon_february_1996_adult')
    ob97 = one('oberon', 'oberon_march_1997_adult_juvenile')
    ob99 = one('oberon', 'oberon_1999_positive')
    ob12 = one('oberon', 'oberon_march_2012_adult_juvenile')
    ob_early = [one('oberon', f'oberon_survey_{y}') for y in (1993, 1994, 1995)]
    sg_early = [one('strathgordon', f'strath_survey_{y}') for y in range(2001, 2006)]
    sg08 = one('strathgordon', 'strath_april_2008_juvenile')
    def bins(state):
        a = _array(state).sum(axis=(0, 1))
        return [float(a[0]), float(a[1]), float(a[2:].sum())]
    lake = []
    for y in LAKE_YEARS:
        state = history['annual_states']['pedder'][y]
        a = _array(state)[0].sum(axis=0)
        lake.append([float(a[0]), float(a[1])])
    # Only the fraction of known removals assigned to the survey window forms
    # the lower bound. It is not an independently fitted capture observation.
    early_minimum = 0
    for r in history['removal_ledger']:
        if r['site'] != 'pedder':
            continue
        y, t = int(r['year']), float(r['time'])
        in_window = (y == 1990 and t >= 31/365) or (y == 1991 and t < 273/365)
        if in_window:
            early_minimum += int(round(_array(r['actual_by_sex_age']).sum()))
    return {
        'creek_early': [_age_pair(x, 1) for x in early],
        'creek_feb': _age_pair(one('pedder', 'february_1992_capture'), 1),
        'creek_late': [_age_pair(x, 1) for x in late],
        'lake': lake, 'jan': _age_pair(jan, 1), 'march': _age_pair(march, 1),
        'ob_early': [bins(x) for x in ob_early], 'ob96': bins(ob96),
        'ob97': bins(ob97), 'ob99': bins(ob99), 'ob12': bins(ob12),
        'sg_early': [bins(x) for x in sg_early], 'sg08': bins(sg08),
        'early_minimum': early_minimum,
    }


def decision_profiles() -> list[dict]:
    """Fixed primary panel, one-factor changes and two declared joint corners."""
    profiles = []
    changes = [('base', {})]
    changes += [(name, change) for name, change in (
        ('feb4', {'feb_effort':4.}), ('creek_power_quarter', {'creek_power':.25}),
        ('creek_age0_quarter', {'creek_age0':.25}), ('creek_age0_all', {'creek_age0':1.}),
        ('lake_power_quarter', {'lake_power':.25}), ('lake_power_full', {'lake_power':1.}),
        ('lake_rho_quarter', {'lake_rho':.25}), ('lake_rho_four', {'lake_rho':4.}),
        ('lake_age01', {'lake_age1':1.}), ('reading_low', {'reading_shift':-1.}),
        ('reading_high', {'reading_shift':1.}), ('juvenile_age0', {'juvenile_age1':0.}),
        ('low_information_corner', {'feb_effort':2., 'creek_power':.25, 'creek_age0':0.,
            'lake_power':1/12, 'lake_rho':.25, 'lake_age1':0., 'reading_shift':-1., 'juvenile_age1':0.}),
        ('high_information_corner', {'feb_effort':4., 'creek_power':1., 'creek_age0':1.,
            'lake_power':1., 'lake_rho':4., 'lake_age1':1., 'reading_shift':1., 'juvenile_age1':1.}),
    )]
    for k, rho, q in product((2.5, 5., 10., 20.), (.25, 1., 4.), (.01, .1, 1.)):
        for name, change in changes:
            p = dict(K=k, rho=rho, q=q, feb_effort=2., creek_power=1., creek_age0=0.,
                     lake_power=1/12, lake_rho=1., lake_age1=0., reading_shift=0., juvenile_age1=1.)
            p.update(change)
            p.update(profile_id=f'K{k:g}_rho{rho:g}_q{q:g}_{name}', panel=name)
            profiles.append(p)
    return profiles


def exposures(features: list[dict], profile: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return unnormalised candidate exposures; no fitted source or class inputs."""
    creek, lake, binary = [], [], []
    p = profile
    for f in features:
        def accessible(v):
            x = _array(v)
            return x[..., 1] + p['creek_age0']*x[..., 0]
        def adult(key):
            return float(f[key][2])
        def juvenile(key):
            return float(f[key][0] + p['juvenile_age1']*f[key][1])
        c = [43*accessible(f['creek_early']).mean(), p['feb_effort']*accessible(f['creek_feb']),
             p['K']*p['rho']*accessible(f['creek_late']).mean()]
        lx = _array(f['lake']) @ np.array([1., p['lake_age1']])
        l = [lx[:5].sum(), p['lake_rho']*lx[5:].sum()]
        sg = _array(f['sg_early'])
        b = [accessible(f['jan']), accessible(f['march']), _array(f['ob_early']).sum(axis=1).mean(),
             adult('ob96'), adult('ob97'), juvenile('ob97'), sum(f['ob99']),
             adult('ob12'), juvenile('ob12'), (sg[:,0]+p['juvenile_age1']*sg[:,1]).mean(),
             juvenile('sg08')]
        creek.append(c); lake.append(l); binary.append(b)
    return _array(creek).reshape(-1,3), _array(lake).reshape(-1,2), _array(binary).reshape(-1,len(BINARY_RECORDS))


def generate_observations(features: list[dict], identities: list[tuple[str,int]],
                          march_retention: list[bool], profile: dict, *, generator: str) -> dict:
    """Draw once, then flag intervention contradictions without replacement.

    The creek generator's common nuisance rate gives expected total 69; Lake's
    gives expected total 173. They are generator-only information normalizers,
    not empirical catchability estimates used in the candidate scores.
    """
    if generator not in ('poisson', 'gamma_quality', 'fixed_creek_total'):
        raise ValueError('unknown observation generator')
    if not (len(features) == len(identities) == len(march_retention)):
        raise ValueError('one identity and retention value are needed per history')
    p = profile
    nominal_creek, nominal_lake, binary_x = exposures(features, p)
    # Powers and reading endpoints are analysis rules. They must not change the
    # generated observations; common random streams couple related profiles.
    generator_profile = {k:p[k] for k in ('K','rho','q','feb_effort','creek_age0','lake_rho','lake_age1','juvenile_age1')}
    creek_counts, lake_values, binary_counts, coherent, reasons = [], [], [], [], []
    for i, (f, identity, retain_march) in enumerate(zip(features, identities, march_retention)):
        rng = np.random.default_rng(keyed_seed('age-observations-20261001', identity, generator, generator_profile, bits=128))
        total = float(nominal_creek[i].sum())
        cx = nominal_creek[i].copy()
        if generator == 'gamma_quality':
            e = _array(f['creek_early']); e = e[:,1]+p['creek_age0']*e[:,0]
            l = _array(f['creek_late']); l = l[:,1]+p['creek_age0']*l[:,0]
            fx = f['creek_feb'][1]+p['creek_age0']*f['creek_feb'][0]
            cx = np.array([np.dot(e,rng.gamma(43/len(e),1,len(e))),
                           fx*rng.gamma(p['feb_effort'],1),
                           p['rho']*np.dot(l,rng.gamma(p['K']/len(l),1,len(l)))])
        if total == 0:
            cc = np.zeros(3, dtype=int)
        elif generator == 'fixed_creek_total':
            cc = rng.multinomial(69, cx/cx.sum())
        else:
            cc = rng.poisson(69*cx/total)
        lx = _array(f['lake']) @ np.array([1.,p['lake_age1']])
        lx[5:] *= p['lake_rho']
        rate = 173/lx.sum() if lx.sum() else 0.
        means = np.repeat((rate*lx/12)[:,None], 12, axis=1)
        if generator == 'gamma_quality':
            means *= rng.gamma(1.,1.,means.shape)
        raw = rng.poisson(means).sum(axis=1)/12
        nonzero = raw > 0
        perturbed = np.where(nonzero, np.maximum(0,raw+rng.uniform(-.08,.08,8)),0.)
        perturbed = np.where(nonzero, np.maximum(0,perturbed+p['reading_shift']*.08),0.)
        lv = np.array([12*perturbed[:5].sum(),12*perturbed[5:].sum()])
        bx = p['q']*binary_x[i]
        if generator == 'gamma_quality':
            bx = bx*binary_visit_quality(rng)
        bc = rng.poisson(bx)
        failures = []
        if cc[0] < f['early_minimum']: failures.append('early_capture_minimum')
        if cc[1] < 1: failures.append('february_capture_minimum')
        if bc[0] < 4: failures.append('january_capture_minimum')
        if retain_march and bc[1] < 1: failures.append('march_capture_minimum')
        creek_counts.append(cc); lake_values.append(lv); binary_counts.append(bc)
        coherent.append(not failures); reasons.append(';'.join(failures))
    return dict(creek_counts=np.asarray(creek_counts,dtype=np.int64).reshape(-1,3),
                lake_equivalents=_array(lake_values).reshape(-1,2),
                binary_counts=np.asarray(binary_counts,dtype=np.int64).reshape(-1,len(BINARY_RECORDS)),
                binary_observed=np.asarray(binary_counts,dtype=np.int64).reshape(-1,len(BINARY_RECORDS)) > 0,
                coherent=np.asarray(coherent,dtype=bool), failure_reasons=reasons)
