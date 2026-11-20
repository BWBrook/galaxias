#!/usr/bin/env python3
"""Bounded synthetic qualification; never loads or scores historical evidence."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
from pathlib import Path

import numpy as np

from galaxias_model.age_demography import AgeConditions, CountEvent, advance, neutral_equilibrium_from_abundance
from galaxias_model.age_scenarios import complete_event_calendar, reference_demography


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("src/galaxias_model/age_demography.py", "src/galaxias_model/age_scenarios.py",
           "src/galaxias_model/age_observation.py", "src/galaxias_model/recruitment_demography.py",
           "scripts/qualify_age_demography.py", "data/age_structured_design_20260927/scenarios.json")
CALENDAR = ((1, .1, 0), (2, .5, 1), (3, .9, 0))


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def trajectory(spec: tuple[int, int, int]) -> dict:
    max_age, scale, seed = spec
    demo = reference_demography(max_age)
    equilibrium = neutral_equilibrium_from_abundance(demo, 100 * scale, 5 * scale)
    state = np.floor(equilibrium["state"] + .5)
    checkpoints = tuple(CountEvent(*point) for point in CALENDAR)
    calendar = complete_event_calendar(checkpoints, {})
    conditions = AgeConditions(
        old_hazard_lake=(.6,) + (.2,) * (max_age - 1),
        late_hazard_lake=(.2,) * max_age,
        old_hazard_refuge=(.1,) + (0.,) * (max_age - 1),
        late_hazard_refuge=(0.,) * max_age,
        newborn_hazard_lake=.6, newborn_hazard_refuge=.1,
        recruitment_sigma=.4, recruitment_multiplier=.8,
        refuge_limit_multiplier=.5, movement_probability=.02,
    )
    records = []
    for year in range(20):
        state, diagnostics = advance(state, demo, equilibrium["limits"], conditions=conditions,
                                     seed=seed, year=year, site_id="synthetic", stochastic=True,
                                     events=calendar)
        if np.any(state < 0) or np.any(state != np.floor(state)):
            raise AssertionError("integer/nonnegative invariant failed")
        records.append({"year": year, "state": state.tolist(),
                        "Z": diagnostics["environment_multiplier"],
                        "breeders_F": diagnostics["pre_spawn_females"],
                        "breeders_M": diagnostics["pre_spawn_males"]})
    return {"max_age": max_age, "scale": scale, "seed": seed, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=False)
    source_hashes = {name: digest((ROOT / name).read_bytes()) for name in SOURCES}
    for name in SOURCES:
        target = output / "source_snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    calendar_json = json.dumps(CALENDAR, separators=(",", ":"))
    (output / "calendar.json").write_text(calendar_json + "\n")
    receipt = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
               "synthetic_only": True, "ceiling_site_path_executions": 128,
               "planned_stochastic_executions": 48, "planned_deterministic_executions": 6,
               "scientific_comparison_histories": 0, "source_hashes": source_hashes,
               "calendar_sha256": digest((output / "calendar.json").read_bytes()),
               "local_workers": 2, "stochastic_years_per_path": 20}
    def save() -> None:
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    save()
    try:
        errors = []
        for age in (6, 8):
            for scale in (1, 10, 100):
                demo = reference_demography(age)
                eq = neutral_equilibrium_from_abundance(demo, 100 * scale, 5 * scale)
                after, _ = advance(eq["state"], demo, eq["limits"])
                error = float(np.max(np.abs(after - eq["state"])))
                np.testing.assert_allclose(after, eq["state"], rtol=1e-12, atol=1e-12)
                errors.append(error)
        specs = [(age, scale, seed) for age in (6, 8) for scale in (1, 10)
                 for seed in range(2026092700, 2026092706)]
        serial = [trajectory(spec) for spec in specs]
        (output / "serial.json").write_text(json.dumps(serial, separators=(",", ":")) + "\n")
        with ProcessPoolExecutor(max_workers=2, mp_context=multiprocessing.get_context("spawn")) as pool:
            parallel = list(pool.map(trajectory, specs))
        (output / "parallel.json").write_text(json.dumps(parallel, separators=(",", ":")) + "\n")
        if serial != parallel:
            raise AssertionError("serial/parallel replay differs")
        if source_hashes != {name: digest((ROOT / name).read_bytes()) for name in SOURCES}:
            raise AssertionError("source changed during qualification")
        receipt.update(status="complete", actual_stochastic_executions=48,
                       actual_deterministic_executions=6, serial_parallel_exact=True,
                       maximum_absolute_fixed_point_error=max(errors),
                       completed_utc=datetime.now(timezone.utc).isoformat(),
                       output_sha256={name: digest((output / name).read_bytes())
                                      for name in ("serial.json", "parallel.json", "calendar.json")})
    except Exception as exc:
        receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}",
                       completed_utc=datetime.now(timezone.utc).isoformat())
        save()
        raise
    save()
    print(json.dumps({key: value for key, value in receipt.items() if key not in ("source_hashes", "output_sha256")}, indent=2))


if __name__ == "__main__":
    main()
