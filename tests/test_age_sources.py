import json
import math

from galaxias_model.age_sources import DESIGN, cell_id, make_source, runner_arguments


def test_recovery_worlds_are_paired_across_restrictions_and_separated_across_roles():
    design = json.loads(DESIGN.read_text())
    cell = design['process_cells'][0]
    other = {**cell, 'restriction': 'R_J'}
    a = make_source(cell, 3, namespace='test-truth')
    b = make_source(other, 3, namespace='test-truth')
    c = make_source(cell, 3, namespace='test-bank')
    assert a['demography'] == b['demography']
    assert a['forcing_values'] == b['forcing_values']
    assert a['source_id'] != c['source_id'] and a['source_seed'] != c['source_seed']
    assert a['demography'] != c['demography']
    assert cell_id(cell) != cell_id(other)
    assert runner_arguments(a, 0, run_namespace='test')['seed'] != runner_arguments(a, 1, run_namespace='test')['seed']


def test_boundary_strata_are_explicit_and_neutral_failure_is_retained():
    design = json.loads(DESIGN.read_text())
    records = [make_source(design['process_cells'][0], i, namespace='test-strata') for i in range(16)]
    assert all((x['refuge_index'] > 1) == bool(x['index'] % 2) for x in records)
    assert len({x['source_id'] for x in records}) == 16
    assert any(not x['feasible'] for x in records)
    for x in records:
        assert math.isfinite(x['demography']['recruits_per_female'])
        assert (x['failure_reason'] == '') == x['feasible']
