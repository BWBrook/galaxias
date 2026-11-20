from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "analyze_age_recovery.py"
SPEC = importlib.util.spec_from_file_location("age_recovery_analysis", SCRIPT)
analysis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(analysis)


def _feature(scale: float = 1.0) -> dict:
    return {
        "creek_early": [[3 * scale, 20 * scale]] * 20,
        "creek_feb": [2 * scale, 4 * scale],
        "creek_late": [[0.5 * scale, 2 * scale]] * 60,
        "lake": [[100 * scale, 10 * scale]] * 5 + [[0, 0]] * 3,
        "jan": [0, 8 * scale],
        "march": [0, 4 * scale],
        "ob_early": [[1 * scale, 2 * scale, 3 * scale]] * 3,
        "ob96": [1 * scale, 2 * scale, 3 * scale],
        "ob97": [1 * scale, 2 * scale, 3 * scale],
        "ob99": [1 * scale, 2 * scale, 3 * scale],
        "ob12": [1 * scale, 2 * scale, 3 * scale],
        "sg_early": [[0, 0, 3 * scale]] * 5,
        "sg08": [1 * scale, 2 * scale, 3 * scale],
        "early_minimum": 0,
    }


def _write_jsonl(path: Path, rows: list[dict]) -> bytes:
    payload = b"".join((json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n").encode() for row in rows)
    path.write_bytes(payload)
    return payload


def _write_fixture(root: Path, *, mismatch: bool = False) -> Path:
    root.mkdir()
    cell = "A6_narrow_primary_R_H"
    source_rows = []
    history_rows = []
    # Pooled support meets the class thresholds (16 truth and 8 bank sources
    # per class), while each index stratum contains only one terminal class.
    for role, count in (("truth", 32), ("bank", 16)):
        for index in range(count):
            source_id = f"smoke:{role}:source-{index:02d}"
            source_rows.append({
                "cell_id": cell,
                "source_id": source_id,
                "namespace": f"smoke:{role}",
                "role": role,
            })
            history_rows.append({
                "cell_id": cell,
                "namespace": role,
                "source_id": source_id if not (mismatch and role == "truth" and index == 0) else "missing-source",
                "replicate": 0,
                "process_seed": 1000 + index,
                "status": "complete",
                "failure": "",
                "terminal_alive": bool(index >= 16),
                "refuge_2002": float(10 + index),
                "lake_2002": float(20 + index),
                "refuge_index": 0.8 + index / 100,
                "index_stratum": "above_one" if index >= 16 else "below_one",
                "march_retention": bool(index % 2),
                "features": _feature(1.0 + index / 100),
            })
    source_payload = _write_jsonl(root / "source_banks.jsonl", source_rows)
    compact_payload = _write_jsonl(root / "histories.jsonl", history_rows)
    with gzip.open(root / "histories.jsonl.gz", "wb") as stream:
        stream.write(compact_payload)
    with gzip.open(root / "full_histories.jsonl.gz", "wb") as stream:
        stream.write(compact_payload)

    def binding(path: Path) -> dict:
        return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}

    manifest = {
        "status": "complete",
        "run_namespace": "smoke",
        "full_design": False,
        "source_rows": len(source_rows),
        "replicates_per_source": 1,
        "outputs": {
            name: binding(root / name)
            for name in ("source_banks.jsonl", "histories.jsonl.gz", "full_histories.jsonl.gz")
        },
        "content_sha256": {
            "histories.jsonl": hashlib.sha256(compact_payload).hexdigest(),
            "full_histories.jsonl": hashlib.sha256(compact_payload).hexdigest(),
        },
        # The fixture emulates the generation driver's source snapshot.  The
        # analyzer itself is bound in its own analysis receipt.
        "source_bindings": {
            relative: analysis._binding(analysis.ROOT / relative)
            for relative in analysis.ANALYSIS_BINDING_PATHS
            if relative != "scripts/analyze_age_recovery.py"
        },
    }
    (root / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


def test_smoke_analysis_preserves_a_failures_and_marks_qualification(tmp_path: Path):
    input_dir = _write_fixture(tmp_path / "input")
    output_dir = tmp_path / "analysis"
    receipt = analysis._run_analysis(
        input_dir,
        output_dir,
        workers=1,
        bootstrap_replicates=8,
        profiles=[analysis.decision_profiles()[0]],
    )

    assert receipt["status"] == "complete"
    assert receipt["analysis_bindings"] == analysis._analysis_bindings()
    assert receipt["generation_source_bindings"] == json.loads(
        (input_dir / "run_manifest.json").read_text()
    )["source_bindings"]
    summary = json.loads((output_dir / "summary.json").read_text())
    assert summary["status"] == "QUALIFICATION_SMOKE_ONLY"
    assert summary["production_launch"] is False
    assert summary["score_controls_passed"] is True
    controls = json.loads((output_dir / "score_controls.json").read_text())
    assert controls["all_passed"] is True
    assert controls["informative_high_near_zero"]["predictions"] == [0, 1]
    assert controls["identical_exposure_opposite_labels"]["predictions"] == [-1, -1]
    assert (output_dir / "analysis_receipt.json").is_file()
    assert (output_dir / "gate_by_profile.csv").is_file()
    with (output_dir / "gate_by_profile.csv").open(newline="") as stream:
        gate_rows = list(csv.DictReader(stream))
    assert {item["index_stratum"] for item in gate_rows} == {"above_one", "below_one"}
    assert all(item["full_gate_passed"] == "0" for item in gate_rows)
    row = gate_rows[0]
    assert int(row["complete_truth_histories"]) == 16
    assert row["index_stratum"] in {"above_one", "below_one"}
    assert int(row["full_bank_sources_loss"]) == 0 or int(row["full_bank_sources_persist"]) == 0
    assert row["full_gate_passed"] == "0"
    assert "coverage_weighted_abstentions" in row

    arrays = np.load(output_dir / "cell_arrays" / "A6_narrow_primary_R_H__stratum_below_one.npz")
    assert arrays["index_stratum"].tolist() == ["below_one"]
    assert arrays["coherent"].shape[:2] == (3, 1)
    assert arrays["creek_counts"].shape[:3] == (3, 1, 16)
    assert arrays["prediction_full"].shape == (3, 1, 16)
    np.testing.assert_array_equal(arrays["coherent"][0, 0], arrays["coherent"][1, 0])


def test_analysis_rejects_source_mismatch_and_existing_output(tmp_path: Path):
    bad_input = _write_fixture(tmp_path / "bad", mismatch=True)
    with pytest.raises(ValueError, match="source identity"):
        analysis._run_analysis(bad_input, tmp_path / "bad-output", profiles=[analysis.decision_profiles()[0]], bootstrap_replicates=2)

    good_input = _write_fixture(tmp_path / "good")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        analysis._run_analysis(good_input, existing, profiles=[analysis.decision_profiles()[0]], bootstrap_replicates=2)


def test_analysis_rejects_tampered_generation_source_binding(tmp_path: Path):
    input_dir = _write_fixture(tmp_path / "tampered")
    manifest_path = input_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    first = next(iter(manifest["source_bindings"]))
    manifest["source_bindings"][first]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="generation source bindings mismatch"):
        analysis._run_analysis(
            input_dir,
            tmp_path / "tampered-output",
            profiles=[analysis.decision_profiles()[0]],
            bootstrap_replicates=2,
        )
    assert not (tmp_path / "tampered-output").exists()


def test_source_macro_fixture_is_not_row_weighted():
    truth_rows = [
        {"source_id": "a", "terminal_alive": False},
        {"source_id": "a", "terminal_alive": False},
        {"source_id": "a", "terminal_alive": False},
        {"source_id": "b", "terminal_alive": False},
        {"source_id": "c", "terminal_alive": True},
        {"source_id": "d", "terminal_alive": True},
    ]
    classification = {"prediction": np.array([0, 0, 0, 1, 1, 0], dtype=np.int8)}
    metrics = analysis._recovery(
        classification,
        truth_rows,
        np.ones(6, dtype=bool),
        bootstrap_replicates=20,
    )
    np.testing.assert_allclose(metrics["source_macro_sensitivity"], [0.5, 0.5])
    assert metrics["balanced_accuracy"] == pytest.approx(0.5)
