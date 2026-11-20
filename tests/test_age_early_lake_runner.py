from __future__ import annotations

import gzip
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from galaxias_model.age_early_lake import make_early_lake_source
import scripts.run_age_early_lake as runner


def _args(tmp_path: Path, *, preflight_only: bool = False, workers: int = 1):
    return SimpleNamespace(mode="smoke", output=tmp_path / "run",
                           workers=workers, preflight_only=preflight_only)


def _read_gzip_jsonl(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def test_smoke_preflight_has_fixed_allocation_and_no_biology(tmp_path):
    manifest = runner.run(_args(tmp_path, preflight_only=True))

    assert manifest["status"] == "preflight_complete"
    assert manifest["mode"] == "smoke"
    assert manifest["configuration"]["namespace"] == runner.SMOKE_NAMESPACE
    assert manifest["source_rows"] == 48
    assert manifest["planned_history_attempts"] == 192
    assert manifest["configuration"]["bank_replicates"] == 1
    assert manifest["biological_simulation_started"] is False
    assert (tmp_path / "run" / "sources.jsonl.gz").is_file()
    assert not (tmp_path / "run" / "features.jsonl.gz").exists()
    assert not (tmp_path / "run" / "histories.jsonl.gz").exists()
    assert len(_read_gzip_jsonl(tmp_path / "run" / "sources.jsonl.gz")) == 48


def test_source_pairing_and_seed_preflight_are_explicit():
    sources = runner.build_sources(runner.SMOKE_NAMESPACE, 4, bank_replicates=1)
    pairing = runner.validate_source_pairing(sources)
    seeds = runner.seed_preflight(sources, bank_replicates=1)

    assert pairing == {"source_rows": 48, "distinct_source_ids": 24,
                       "paired_quality_rows": 24}
    assert seeds["process_seed_excludes_quality_and_restriction"] is True
    assert seeds["checked_cross_namespace_collisions"] is True
    by_id = {source["source_id"]: source for source in sources
             if source["quality_regime"] == "neutral"}
    for source in sources:
        paired = by_id[source["source_id"]]
        assert source["source_seed"] == paired["source_seed"]
        assert source["demography"] == paired["demography"]
        assert source["forcing_values"]["PR032"] == 1.0 or 0.7 <= source["forcing_values"]["PR032"] <= 1.8
        assert runner.process_seed(source, 0) == runner.process_seed(paired, 0)


def test_bindings_are_source_and_protocol_inputs_only():
    bindings = runner.source_bindings()
    assert "scripts/run_age_early_lake.py" in bindings
    assert "docs/early_lake_mechanism_protocol.md" in bindings
    assert "data/age_structured_design_20260929/scenarios.json" in bindings
    assert "data/age_linked_recovery_20261001/retained_forcing_parameters.csv" in bindings
    assert "uv.lock" in bindings and "pyproject.toml" in bindings
    assert not any("lake_figure6" in name or "lake_observation" in name for name in bindings)


def test_execute_source_task_retains_fixed_rows_and_full_history():
    source = make_early_lake_source(
        6, 3, role="test", namespace="prefix",
        quality_regime="neutral",
    )
    features, raw = runner.execute_source_task(
        (source, "early-lake-test-fixture", 1)
    )

    assert len(features) == len(raw) == 4
    assert {row["restriction"] for row in features} == set(runner.RESTRICTIONS)
    assert all(set(("source_id", "index", "role", "maximum_age",
                    "quality_regime", "restriction", "replicate", "seed",
                    "status", "valid", "lake_exposures")) <= set(row)
               for row in features)
    assert all(row["source_id"] == source["source_id"] for row in raw)
    valid = [row for row in raw if row["status"] == "valid"]
    assert len(valid) == 4
    for row in valid:
        history = row["history"]
        assert len(history["annual_states"]) == 25
        assert len(history["process_diagnostics"]) == 25
        assert "initial_rounding_vector" in history


def test_mock_driver_is_ordered_and_hashes_are_reproducible(tmp_path, monkeypatch):
    source = make_early_lake_source(
        6, 0, role="calibration", namespace="early-lake-mock",
        quality_regime="neutral",
    )
    paired_source = make_early_lake_source(
        6, 0, role="calibration", namespace="early-lake-mock",
        quality_regime="engineering",
    )
    sources = [source, paired_source]

    def fake_build(namespace, source_count, **kwargs):
        del namespace, source_count
        return sources

    def fake_execute(task):
        source, _namespace, _bank_replicates = task
        features, raw = [], []
        for restriction in runner.RESTRICTIONS:
            features.append({
                "source_id": source["source_id"], "index": 0, "role": "calibration",
                "maximum_age": 6, "quality_regime": source["quality_regime"], "restriction": restriction,
                "replicate": 0, "seed": 11, "status": "valid", "valid": True,
                "lake_exposures": [[0.0, 0.0]] * 8,
            })
            raw.append({"source": source, "history": {"annual_states": {}, "process_diagnostics": {}},
                        "demographic": {"annual_states": {}, "process_diagnostics": {}},
                        "source_id": source["source_id"], "index": 0, "role": "calibration",
                        "maximum_age": 6, "quality_regime": source["quality_regime"], "restriction": restriction,
                        "replicate": 0, "seed": 11, "status": "valid"})
        return features, raw

    monkeypatch.setattr(runner, "build_sources", fake_build)
    monkeypatch.setattr(runner, "execute_source_task", fake_execute)
    monkeypatch.setattr(runner, "source_bindings", lambda **kwargs: {})
    first = runner.run(_args(tmp_path / "one"))
    second = runner.run(_args(tmp_path / "two"))
    assert first["logical_sha256"] == second["logical_sha256"]
    assert first["accounting"]["history_rows"] == 8
    assert first["accounting"]["runtime_failures"] == 0


def test_existing_output_is_never_overwritten(tmp_path):
    output = tmp_path / "run"
    output.mkdir()
    with pytest.raises(FileExistsError, match="overwrite"):
        runner.run(_args(tmp_path))
