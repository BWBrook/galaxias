from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path

from galaxias_model.mechanism_interpretation import (
    MODULE4_5_MANDATORY_OUTPUTS,
    REQUIRED_MODULE4_ARTIFACTS,
    module4_5_output_paths,
    validate_module4_raw_artifact_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_manifest(tmp_path: Path, include_all_roles: bool = True) -> tuple[Path, Path]:
    module4_root = tmp_path / "module4"
    run_dir_name = "baseline_current_seed20260410"
    run_dir = module4_root / run_dir_name
    run_dir.mkdir(parents=True)

    rows = []
    artifact_items = list(REQUIRED_MODULE4_ARTIFACTS.items())
    if not include_all_roles:
        artifact_items = artifact_items[:-1]
    for role, file_name in artifact_items:
        path = run_dir / file_name
        path.write_text(f"{role}\n", encoding="utf-8")
        rows.append(
            {
                "run_id": "test_run",
                "variant_id": "baseline_current",
                "seed": "20260410",
                "run_dir_name": run_dir_name,
                "file_role": role,
                "file_name": file_name,
                "local_path": path.as_posix(),
                "local_sha256": _sha256(path),
            }
        )

    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return manifest, module4_root


def test_module4_5_output_contract_is_explicit() -> None:
    outputs = module4_5_output_paths(Path("/publish"))
    assert set(outputs) == set(MODULE4_5_MANDATORY_OUTPUTS)
    assert "data/module4_5_proposal_set_membership.csv" in outputs
    assert "data/module4_5_distance_audit.csv" in outputs
    assert "docs/module4_5_mechanism_interpretation_review.md" in outputs


def test_module4_artifact_manifest_validation_passes_for_complete_run(tmp_path: Path) -> None:
    manifest, module4_root = _write_manifest(tmp_path)
    validation = validate_module4_raw_artifact_manifest(manifest, module4_root, verify_hashes=True)

    assert validation.passed
    assert validation.record_count == len(REQUIRED_MODULE4_ARTIFACTS)
    assert validation.run_count == 1


def test_module4_artifact_manifest_validation_reports_missing_role(tmp_path: Path) -> None:
    manifest, module4_root = _write_manifest(tmp_path, include_all_roles=False)
    validation = validate_module4_raw_artifact_manifest(manifest, module4_root)

    assert not validation.passed
    assert validation.missing_roles == ("baseline_current:20260410:baseline_current_seed20260410:run_manifest",)


def test_module4_5_smoke_cli_accepts_explicit_inputs(tmp_path: Path) -> None:
    manifest, module4_root = _write_manifest(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_module4_5_mechanism_interpretation.py"),
            "--module4-root",
            str(module4_root),
            "--manifest",
            str(manifest),
            "--publish-root",
            str(tmp_path / "publish"),
            "--smoke-only",
            "--verify-hashes",
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert "Module 4.5 input validation passed" in result.stdout
    assert "module4_5_family_decision_table.csv" in result.stdout
