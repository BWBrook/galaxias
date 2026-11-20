"""Offline contracts for compact conditional-detection replay preparation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("detection_replay", ROOT / "scripts" / "replay_conditional_detection.py")
replay = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(replay)


def _write_archive(directory: Path, phase: str, files: dict[str, pd.DataFrame | str], *, prior_binding: dict | None = None, previous: list[dict] | None = None) -> dict:
    directory.mkdir(parents=True)
    for name, value in files.items():
        path = directory / name
        if isinstance(value, pd.DataFrame):
            value.to_csv(path, index=False, compression="gzip" if name.endswith(".gz") else None)
        else:
            path.write_text(value, encoding="utf-8")
    manifest = {
        "status": "complete", "scope": "conditional_calibration", "phase": phase,
        "source_id_namespace": replay.SOURCE_NAMESPACE, "source_identity": replay.IDENTITY,
        "data_dir": str(directory), "runtime": replay._runtime(),
        "outputs": {name: replay.file_hash(directory / name) for name in files},
        "source_files": [], "input_files": [], "spec_documents": [],
    }
    if prior_binding is not None:
        manifest["prior_input_binding"] = {"run_manifest.json": prior_binding}
    if previous is not None:
        manifest["previous_phase_bindings"] = previous
    (directory / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path, Path, list[int]]:
    prior = tmp_path / "prior"
    validation = tmp_path / "validate"
    screen = tmp_path / "screen"
    refine = tmp_path / "refine"
    data_dir = tmp_path / "inputs"
    data_dir.mkdir()
    identities = [(11, "fixture_family", "fixture_family:p00001"), (12, "fixture_family", "fixture_family:p00002")]
    sources = pd.DataFrame([
        {**dict(zip(replay.IDENTITY, identity)), "proposal_index": i, "proposal_seed": 1000 + i,
         "source_id": replay.calibration.source_id(identity)}
        for i, identity in enumerate(identities, 1)
    ])
    parameter_rows = []
    for source in sources.to_dict("records"):
        for i in range(40):
            parameter_rows.append({**{key: source[key] for key in replay.IDENTITY}, "parameter_id": f"PR{i + 1:03d}", "proposal_index": source["proposal_index"], "proposal_seed": source["proposal_seed"], "value_sampling": float(i)})
    parameters = pd.DataFrame(parameter_rows)
    intrinsic_rows = []
    for source in sources.to_dict("records"):
        intrinsic_rows.append({**{key: source[key] for key in replay.IDENTITY}, "source_id": source["source_id"], **{f"CT{target}_{field}": 0.1 * int(target) for target in ("011", "012") for field in ("raw_penalty", "weighted_penalty", "projected_primary", "projected_secondary")}})
    intrinsic = pd.DataFrame(intrinsic_rows)
    prior_raw = pd.DataFrame({"placeholder": []})
    prior_manifest = _write_archive(prior, "prior", {"parameter_values.csv.gz": parameters, "sources.csv": sources, "source_summary.csv": intrinsic, "raw_replicates.csv.gz": prior_raw})

    def history(seed: int) -> SimpleNamespace:
        years = np.arange(1987, 2003)
        base = float(seed % 100)
        trajectory = pd.DataFrame({"year": years, "N_R": base + years - 1987, "N_L": base + 2 * (years - 1987), "N_total": 2 * base + 3 * (years - 1987)})
        return SimpleNamespace(trajectory_table=trajectory)

    def fake_features(value: SimpleNamespace) -> dict:
        total = float(value.trajectory_table.loc[value.trajectory_table.year == 2002, "N_total"].iloc[0])
        return {"diagnostic": total, "surviving_2002": total > 0, "n_total_2002": total}

    def fake_scores(value: SimpleNamespace, inputs: object) -> dict:
        total = float(value.trajectory_table.loc[value.trajectory_table.year == 2002, "N_total"].iloc[0])
        return {"CT001_raw_penalty": total / 10, "CT001_weighted_penalty": total / 5, "CT001_projected_primary": total, "CT001_projected_secondary": total + 1}

    monkeypatch.setattr(replay.calibration, "_load_inputs_cached", lambda _: object())
    monkeypatch.setattr(replay.calibration, "build_resolved_parameters_from_sample", lambda *args: object())
    monkeypatch.setattr(replay.calibration, "_scenario_config", lambda *args: object())
    monkeypatch.setattr(replay.calibration, "run_historical_simulation", lambda params, family, config, seed: history(int(seed)))
    monkeypatch.setattr(replay.terminal_screen, "terminal_features", fake_features)
    monkeypatch.setattr(replay.pilot, "scored_fields", fake_scores)

    raw_rows = []
    seeds: list[int] = []
    for source in sources.sort_values(replay.IDENTITY).to_dict("records"):
        for replicate in range(1, 4):
            seed = 900000 + source["proposal_index"] * 100 + replicate
            seeds.append(seed)
            result = history(seed)
            row = {key: source[key] for key in replay.IDENTITY}
            row.update(source_id=source["source_id"], stage="validate", replicate_index=replicate, simulation_seed=seed)
            row.update(fake_features(result))
            row.update(fake_scores(result, None))
            row.update({field: value for field, value in intrinsic.loc[intrinsic.source_id == source["source_id"]].iloc[0].items() if field.startswith("CT011_") or field.startswith("CT012_")})
            raw_rows.append(row)
    raw = pd.DataFrame(raw_rows)
    validation_manifest = {
        "status": "complete", "scope": "conditional_calibration", "phase": "validate",
        "source_id_namespace": replay.SOURCE_NAMESPACE, "source_identity": replay.IDENTITY,
        "data_dir": str(data_dir), "runtime": replay._runtime(), "replicates": 3, "source_count": 2,
        "config": {"replicates": 3}, "source_files": [], "input_files": [], "spec_documents": [],
    }
    # Screen/refine are tiny ancestry fixtures; their bindings are included in
    # the validation manifest exactly as the production runner records them.
    screen_manifest = _write_archive(screen, "screen", {"marker.txt": "screen"}, prior_binding=replay.file_hash(prior / "run_manifest.json"), previous=[])
    refine_manifest = _write_archive(refine, "refine", {"marker.txt": "refine"}, prior_binding=replay.file_hash(prior / "run_manifest.json"), previous=[])
    screen_bindings = {"run_manifest.json": replay.file_hash(screen / "run_manifest.json"), "marker.txt": replay.file_hash(screen / "marker.txt")}
    refine_bindings = {"run_manifest.json": replay.file_hash(refine / "run_manifest.json"), "marker.txt": replay.file_hash(refine / "marker.txt")}
    validation_manifest["prior_input_binding"] = {"run_manifest.json": replay.file_hash(prior / "run_manifest.json")}
    validation_manifest["previous_phase_bindings"] = [{"phase": "screen", "bindings": screen_bindings}, {"phase": "refine", "bindings": refine_bindings}]
    validation.mkdir()
    raw.to_csv(validation / "raw_replicates.csv.gz", index=False, compression="gzip")
    sources.to_csv(validation / "sources.csv", index=False)
    pd.DataFrame().to_csv(validation / "source_summary.csv", index=False)
    validation_manifest["outputs"] = {name: replay.file_hash(validation / name) for name in ("raw_replicates.csv.gz", "sources.csv", "source_summary.csv")}
    (validation / "run_manifest.json").write_text(json.dumps(validation_manifest, indent=2) + "\n", encoding="utf-8")
    membership_dir = tmp_path / "refine_analysis"
    membership_dir.mkdir()
    membership = membership_dir / "selection_membership.csv"
    membership_table = sources.assign(profile="fixture", cohort="family")
    membership_table = pd.concat([membership_table, membership_table.iloc[[0]].assign(cohort="global")], ignore_index=True)
    membership_table.to_csv(membership, index=False)
    analysis_manifest = {"status": "complete", "outputs": {"selection_membership.csv": replay.file_hash(membership)}}
    (membership_dir / "analysis_manifest.json").write_text(json.dumps(analysis_manifest, indent=2) + "\n")
    return prior, validation, screen, refine, membership, seeds


def test_replay_uses_archived_seeds_and_emits_compact_abundance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prior, validation, screen, refine, membership, seeds = _fixture(tmp_path, monkeypatch)
    observed: list[int] = []
    original = replay.calibration.run_historical_simulation

    def record(*args, **kwargs):
        observed.append(int(kwargs["seed"]))
        return original(*args, **kwargs)

    monkeypatch.setattr(replay.calibration, "run_historical_simulation", record)
    output = tmp_path / "replay"
    manifest = replay.replay_validation(prior, validation, output, membership, screen_dir=screen, refine_dir=refine, workers=1)
    assert manifest["status"] == "complete"
    assert observed == seeds
    compact = pd.read_csv(output / "compact_abundance_replay.csv.gz", float_precision="round_trip")
    assert list(compact.columns) == replay.OUTPUT_COLUMNS
    assert len(compact) == 6
    assert compact.loc[0, "pos_N_R_1988"] == pytest.approx((seeds[0] % 100) + 0)
    assert compact.loc[0, "neg_N_total_2002"] == pytest.approx(2 * (seeds[0] % 100) + 3 * 14)
    assert json.loads((output / "replay_manifest.json").read_text())["counts"]["historical_runs"] == 6


def test_preflight_is_read_only_and_accepts_cross_cohort_membership_reuse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prior, validation, screen, refine, membership, _ = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(replay.calibration, "run_historical_simulation", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("preflight must not simulate")))
    result = replay.preflight_validation(prior, validation, membership, screen_dir=screen, refine_dir=refine)
    assert result["status"] == "preflight_complete"
    assert result["source_count"] == 2 and result["historical_runs"] == 6
    assert result["inputs"]["membership"]["rows"] == 3


def test_replay_fails_closed_on_archived_diagnostic_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prior, validation, screen, refine, membership, _ = _fixture(tmp_path, monkeypatch)
    raw_path = validation / "raw_replicates.csv.gz"
    raw = pd.read_csv(raw_path)
    raw.loc[0, "diagnostic"] += 1
    raw.to_csv(raw_path, index=False, compression="gzip")
    manifest = json.loads((validation / "run_manifest.json").read_text())
    manifest["outputs"]["raw_replicates.csv.gz"] = replay.file_hash(raw_path)
    (validation / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with pytest.raises(ValueError, match="Replay mismatch"):
        replay.replay_validation(prior, validation, tmp_path / "bad-replay", membership, screen_dir=screen, refine_dir=refine, workers=1)
    assert not (tmp_path / "bad-replay" / "replay_manifest.json").exists()


def test_replay_refuses_existing_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prior, validation, screen, refine, membership, _ = _fixture(tmp_path, monkeypatch)
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        replay.replay_validation(prior, validation, output, membership, screen_dir=screen, refine_dir=refine)


def test_replay_rejects_decimal_archived_seed_before_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prior, validation, screen, refine, membership, _ = _fixture(tmp_path, monkeypatch)
    raw_path = validation / "raw_replicates.csv.gz"
    raw = pd.read_csv(raw_path)
    raw["simulation_seed"] = raw["simulation_seed"].astype(float)
    raw.loc[0, "simulation_seed"] = 900010.5
    raw.to_csv(raw_path, index=False, compression="gzip")
    manifest = json.loads((validation / "run_manifest.json").read_text())
    manifest["outputs"]["raw_replicates.csv.gz"] = replay.file_hash(raw_path)
    (validation / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with pytest.raises(ValueError, match="Malformed simulation seed"):
        replay.replay_validation(prior, validation, tmp_path / "decimal-seed", membership, screen_dir=screen, refine_dir=refine)


def test_replay_rejects_membership_hash_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prior, validation, screen, refine, membership, _ = _fixture(tmp_path, monkeypatch)
    membership.write_text(membership.read_text().replace("fixture_family:p00001", "fixture_family:p00099"))
    with pytest.raises(ValueError, match="membership hash"):
        replay.replay_validation(prior, validation, tmp_path / "membership-drift", membership, screen_dir=screen, refine_dir=refine)
