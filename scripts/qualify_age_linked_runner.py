#!/usr/bin/env python3
"""Bounded engineering qualification of linked identities and exact replay."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from run_age_recovery import binding, encoded
from galaxias_model.age_demography import AgeDemography
from galaxias_model.age_runner import run_linked_history, _forcing_rows, _Parameters
from galaxias_model.age_sources import DESIGN, make_source
from galaxias_model.common_model import _common_historical_forcing, _ParameterValues

SOURCE_PATHS = (
    "src/galaxias_model/age_demography.py", "src/galaxias_model/age_runner.py",
    "src/galaxias_model/age_scenarios.py", "src/galaxias_model/common_model.py",
    "src/galaxias_model/age_sources.py", "src/galaxias_model/age_recovery_observation.py",
    "scripts/run_age_recovery.py", "scripts/qualify_age_linked_runner.py",
    "docs/age_linked_recovery_protocol.md", "data/scenario_definitions.json",
    "data/age_structured_design_20260929/scenarios.json",
    "data/age_linked_recovery_20261001/retained_forcing_parameters.csv", "uv.lock", "pyproject.toml",
)


def fixture(spec):
    age, timing, sanger, stochastic, seed, no_wild = spec
    params = {f"PR{i:03d}": 0. for i in range(12, 35)}
    params.update(PR005=0., PR007=0., PR032=1., PR040=10.)
    demography = AgeDemography((1.,)*age, (0., 0.)+(1.,)*(age-1), 100., lake_settlement=.95)
    result = run_linked_history(
        demography, params, {"pedder_lake":100000., "pedder_refuge":1000., "oberon":100000., "strathgordon":100000.},
        restriction="R_J", eta_refuge=.5, recruitment_sigma=0., strath_pre2007=.02,
        seed=seed, ledger_timing=timing, march_retention=timing == "late",
        removal_account="sanger_42_early_releases_held_before_1992" if sanger else "primary_plan_31_early_releases",
        stochastic=stochastic, no_wild_removals=no_wild,
    )
    return {"spec": spec, "history": result}


def check_identity(record):
    age, timing, sanger, stochastic, seed, no_wild = record["spec"]
    history = record["history"]
    if not history["valid"]:
        return False
    assert history["advance_calls"] == 48*3
    if no_wild:
        assert not history["removal_ledger"] and not history["addition_ledger"] and not history["holding_ledger"] and not history["transfer_ledger"]
        for site in ("oberon", "strathgordon"):
            assert all(np.asarray(state).sum() == 0 for state in history["annual_states"][site].values())
        return True
    expected_early = 42 if sanger else 31
    assert np.isclose(sum(x["count"] for x in history["addition_ledger"] if x["year"] <= 1992), expected_early)
    assert np.isclose(sum(x["count"] for x in history["addition_ledger"]), expected_early+3)
    assert np.isclose(sum(x["actual_by_sex_age"].sum() for x in history["removal_ledger"] if x["year"] <= 1992), 36 if sanger else 25)
    captures = {x["label"]: x for x in history["removal_ledger"]}
    for label in {x["capture_label"] for x in history["holding_ledger"]}:
        represented = np.zeros((2, age+1))
        for outcome in (x for x in history["holding_ledger"] if x["capture_label"] == label):
            if outcome["status"] == "released":
                assert (outcome["capture_year"], outcome["capture_time"]) < (outcome["release_year"], outcome["release_time"])
                captured = np.asarray(outcome["released_capture_cohorts"])
                delta = outcome["release_year"]-outcome["capture_year"]
                shifted = np.zeros_like(captured)
                shifted[:, delta:] = captured[:, :age+1-delta]
                np.testing.assert_allclose(shifted, outcome["vector"], atol=1e-10)
                assert np.asarray(outcome["vector"])[:, -1].sum() == 0
                represented += captured
            else:
                represented += outcome["vector"]
        np.testing.assert_allclose(represented[:, :-1], captures[label]["actual_by_sex_age"], atol=1e-10)
    if sanger:
        captured = captures[f"sanger_extra_capture_{timing}"]
        ceiling = age-1-(1992-captured["year"])
        assert captured["actual_by_sex_age"][:, ceiling+1:].sum() == 0
    november = next(x for x in history["addition_ledger"] if x["label"] == "november_1991_release")
    np.testing.assert_allclose(november["vector"][:, 1:].sum(axis=1), [8, 9])
    assert np.isclose(november["vector"][:, 0].sum(), 1)
    feb = next(t for y, t, label in history["calendar"] if label == "february_1992_release")
    assert np.isclose(sum(x["count"] for x in history["addition_ledger"] if x["year"] == 1992 and abs(x["time"]-feb) < 1e-10), 12)
    assert sum(x["count"] for x in history["transfer_ledger"]) == 353
    for transfer in history["transfer_ledger"]:
        np.testing.assert_allclose(transfer["donor_by_compartment_sex_age"].sum(axis=0), transfer["vector"][:, :-1])
        assert transfer["conserved"] and 0 < transfer["fraction_removed"] <= 1
    return True


def check_forcing():
    cell = json.loads(DESIGN.read_text())["process_cells"][0]
    fields = ("connected", "U", "O", "H", "spawn_habitat_multiplier", "T", "P", "C_L", "C_R")
    comparisons = 0
    for index in range(3):
        params = _ParameterValues(make_source(cell, index, namespace="forcing-qualification")["forcing_values"])
        for removed in (False, True):
            extended = _forcing_rows(_Parameters(params), 1964, 2012, overshoot_removed=removed)
            for row in _common_historical_forcing(params, overshoot_removed=removed).to_dict(orient="records"):
                np.testing.assert_array_equal([extended[int(row["year"])][x] for x in fields], [row[x] for x in fields])
                comparisons += len(fields)
    return comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.workers <= 4:
        raise ValueError("qualification workers must be in 1..4")
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=False)
    frozen = {p: binding(ROOT/p) for p in SOURCE_PATHS}
    receipt = {"status":"running", "started_utc":datetime.now(timezone.utc).isoformat(),
               "source_bindings": frozen, "engineering_fixtures_not_prior_or_historical_evidence": True,
               "planned_joint_histories":21, "nominal_site_histories":63, "workers":args.workers}
    start = time.monotonic()
    def save():
        (out/"receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    save()
    try:
        det_specs = [(6, t, s, False, 19, False) for t in ("early", "late") for s in (False, True)]
        specs = [(a, t, s, True, 99117+i, False) for i, (a,t,s) in enumerate(
            (a,t,s) for a in (6,8) for t in ("early","late") for s in (False,True))]
        deterministic = [fixture(x) for x in det_specs]
        assert all(check_identity(x) for x in deterministic)
        serial = [fixture(x) for x in specs]
        for x in serial:
            check_identity(x)
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn")) as pool:
            parallel = list(pool.map(fixture, specs))
        assert encoded(serial) == encoded(parallel), "serial/parallel history mismatch"
        counter = fixture((*specs[0][:-1], True))
        assert check_identity(counter)
        for year in range(1965, 1990):
            np.testing.assert_array_equal(serial[0]["history"]["annual_states"]["pedder"][year],
                                          counter["history"]["annual_states"]["pedder"][year])
        calendars = {x["history"]["calendar_hash"] for x in deterministic+serial+[counter]}
        assert len(calendars) == 1
        forcing_comparisons = check_forcing()
        for name, records in (("deterministic.jsonl.gz", deterministic), ("serial.jsonl.gz", serial),
                              ("parallel.jsonl.gz", parallel), ("counterfactual.jsonl.gz", [counter])):
            with gzip.open(out/name, "wt") as handle:
                for record in records:
                    handle.write(encoded(record)+"\n")
        assert frozen == {p: binding(ROOT/p) for p in SOURCE_PATHS}, "source changed during qualification"
        receipt.update(status="complete", completed_utc=datetime.now(timezone.utc).isoformat(),
                       elapsed_seconds=time.monotonic()-start, actual_joint_histories=21,
                       deterministic_complete=4, stochastic_complete=sum(x["history"]["valid"] for x in serial),
                       stochastic_attempted=8, serial_parallel_exact=True, forcing_parity=True,
                       forcing_scalar_comparisons=forcing_comparisons, holding_conservation=True,
                       transfer_conservation=True, no_wild_empty=True, pre_removal_pairing_exact=True,
                       calendar_hash=next(iter(calendars)),
                       outputs={p.name:binding(p) for p in sorted(out.glob("*.gz"))})
    except BaseException as exc:
        receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}", elapsed_seconds=time.monotonic()-start)
        save()
        raise
    save()
    print(json.dumps({k:v for k,v in receipt.items() if k not in ("source_bindings","outputs")}, indent=2))


if __name__ == "__main__":
    main()
