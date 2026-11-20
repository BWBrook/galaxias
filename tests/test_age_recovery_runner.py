"""Preserve failed worlds and disjoint source identities without demographic runs."""
import importlib.util
import json
from pathlib import Path

import pytest

from galaxias_model.age_sources import DESIGN, cell_id, make_source

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("run_age_recovery", ROOT / "scripts/run_age_recovery.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def source_record(index=0):
    cell = json.loads(DESIGN.read_text())["process_cells"][0]
    source = make_source(cell, index, namespace="qualification:truth")
    return {**source, "cell_id": cell_id(cell), "role": "truth"}


def test_algebraic_failure_is_retained_without_a_hidden_runner_call(monkeypatch):
    source = {**source_record(), "feasible": False, "failure_reason": "neutral allocation impossible"}
    def forbidden(**kwargs):
        raise AssertionError("infeasible worlds must not run or redraw")
    monkeypatch.setattr(runner, "run_linked_history", forbidden)
    rows, raw = runner.execute_source((source, 4, "qualification"))
    assert len(rows) == len(raw) == 4
    assert {x["status"] for x in rows} == {"algebraically_infeasible"}
    assert len({x["process_seed"] for x in rows}) == 4
    assert all("terminal_alive" not in x for x in rows)
    assert all(x["history"] is None for x in raw)
    assert sum(x["nominal_site_histories"] for x in rows) == 12


def test_process_failure_retains_trace_without_inventing_an_endpoint(monkeypatch):
    source = {**source_record(), "feasible": True}
    failed = {"valid": False, "failure": "not enough donor fish", "advance_calls": 93,
              "calendar_hash": "calendar", "partial_removals": [4]}
    monkeypatch.setattr(runner, "run_linked_history", lambda **kwargs: failed)
    rows, raw = runner.execute_source((source, 1, "qualification"))
    assert rows[0]["status"] == "process_infeasible"
    assert rows[0]["advance_calls"] == 93
    assert "terminal_alive" not in rows[0]
    assert raw[0]["history"] == failed


def test_seed_preflight_distinguishes_intended_pairing_from_collision():
    source = source_record()
    paired = {**source, "cell_id": source["cell_id"] + "_paired"}
    assert runner.seed_preflight([source, paired], 4, "qualification")["unique_parameter_and_process_seeds"] == 5
    collision = {**source_record(1), "source_seed": source["source_seed"]}
    with pytest.raises(RuntimeError, match="seed collision"):
        runner.seed_preflight([source, collision], 4, "qualification")
