#!/usr/bin/env python3
"""Diagnose encoded target penalties at frozen sources without reselection."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_conditional_calibration import IDENTITY, file_hash, verify_archive
from galaxias_model.scoring import EPS


def summarize(phase_dirs, membership, output_dir):
    members = pd.read_csv(membership)
    wanted = set(members[IDENTITY].itertuples(index=False, name=None))
    target_fields = [f'CT{i:03d}_weighted_penalty' for i in range(1, 6)]
    source_rows, manifests = [], {}
    for directory in phase_dirs:
        manifest, _ = verify_archive(directory)
        phase, n = manifest['phase'], manifest['replicates']
        manifests[phase] = file_hash(directory / 'run_manifest.json')
        for chunk in pd.read_csv(directory / 'raw_replicates.csv.gz', usecols=IDENTITY + target_fields, chunksize=max(n, (20000 // n)*n)):
            for identity, group in chunk.groupby(IDENTITY, sort=False):
                if identity not in wanted:
                    continue
                if len(group) != n:
                    raise ValueError('Incomplete source in target decomposition')
                row = {**dict(zip(IDENTITY, identity)), 'phase': phase}
                row.update({f'{c}_mean': group[c].mean() for c in target_fields})
                row['early_total_median'] = group[target_fields].sum(axis=1).median()
                row['early_without_CT004_CT005_median'] = group[target_fields[:3]].sum(axis=1).median()
                source_rows.append(row)
    source = pd.DataFrame(source_rows)
    for phase in manifests:
        part = source.loc[source.phase.eq(phase)]
        if part.duplicated(IDENTITY).any() or set(part[IDENTITY].itertuples(index=False, name=None)) != wanted:
            raise ValueError('Incomplete or duplicated source coverage in target decomposition')
    values = [c for c in source if c not in IDENTITY + ['phase']]
    selected = members.merge(source, on=IDENTITY, how='left', validate='many_to_many')
    if selected.phase.isna().any():
        raise ValueError('Missing selected source in target decomposition')
    contexts = selected.groupby(['phase', 'search_seed', 'profile', 'cohort', 'family_id'], sort=True)[values].mean().reset_index()
    total_mean = contexts[[f'{c}_mean' for c in target_fields]].sum(axis=1)
    contexts['CT005_fraction_of_mean_early_penalty'] = contexts.CT005_weighted_penalty_mean / total_mean.where(total_mean.gt(0))
    priors = pd.read_csv(ROOT / 'data/parameter_priors.csv').set_index('parameter_id')
    targets = pd.read_csv(ROOT / 'data/calibration_targets.csv').set_index('target_id')
    wt4, wt5 = targets.loc['CT004', 'priority_weight'], targets.loc['CT005', 'priority_weight']
    no_climbing_floor = .5 * wt5 * math.log(1 / EPS) / priors.loc['PR038', 'upper_bound']
    floors = pd.DataFrame([
        ('habitat_only_null', wt4, no_climbing_floor),
        ('trout_only', 0., no_climbing_floor),
        ('climbing_only', wt4, 0.),
        ('persistent_joint_cause', wt4 / 3, 0.),
        ('transient_perfect_storm', 0., 0.),
    ], columns=['family_id', 'CT004_structural_floor', 'CT005_structural_floor'])
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {'target_leverage_sources.csv': source, 'target_leverage_contexts.csv': contexts, 'structural_score_floors.csv': floors}
    for name, table in files.items():
        table.to_csv(output_dir / name, index=False)
    receipt = {'status': 'complete', 'diagnostic_only': 'Frozen sources; no score replacement or reselection.',
               'source': file_hash(Path(__file__)), 'membership': file_hash(membership), 'phases': manifests,
               'outputs': {name: file_hash(output_dir / name) for name in files}}
    (output_dir / 'target_leverage_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(floors.to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase-dir', type=Path, action='append', required=True, dest='phase_dirs')
    parser.add_argument('--membership', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    summarize(**vars(parser.parse_args()))
