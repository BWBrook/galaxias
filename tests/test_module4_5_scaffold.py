from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from galaxias_model import load_model_inputs, resolve_family_parameters
from galaxias_model.mechanism_interpretation import (
    MODULE4_5_MANDATORY_OUTPUTS,
    REQUIRED_MODULE4_ARTIFACTS,
    module4_5_output_paths,
    validate_module4_raw_artifact_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


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


def _proposal_row(
    proposal_id: str,
    family_id: str,
    family_label: str,
    proposal_index: int,
    proposal_seed: int,
    accepted: bool,
    distance: float,
) -> dict[str, object]:
    return {
        "proposal_id": proposal_id,
        "family_id": family_id,
        "family_label": family_label,
        "proposal_index": proposal_index,
        "stage_status": "accepted" if accepted else "stage_b_rejected",
        "proposal_seed": proposal_seed,
        "deterministic_overall_distance": distance,
        "deterministic_historical_core_distance": distance - 1,
        "deterministic_intrinsic_baseline_distance": 1.0,
        "stochastic_overall_distance_median": distance + 0.5,
        "stochastic_historical_core_distance_median": distance - 0.5,
        "stochastic_intrinsic_baseline_distance_median": 1.0,
        "stochastic_historical_core_distance_iqr": 0.5,
        "accepted_final": accepted,
        "failure_reason": "",
        "deterministic_full_ready_for_module3": True,
        "stochastic_full_ready_for_module3": True,
        "stage_a_rank": proposal_index,
        "stage_b_rank": proposal_index,
    }


def _write_generation_manifest(tmp_path: Path) -> tuple[Path, Path]:
    module4_root = tmp_path / "module4"
    run_dir_name = "baseline_current_seed20260410"
    run_dir = module4_root / run_dir_name
    run_dir.mkdir(parents=True)

    proposals = pd.DataFrame(
        [
            _proposal_row(
                "persistent_joint_cause:p00001",
                "persistent_joint_cause",
                "Trout + climbing persistent joint-cause",
                1,
                101,
                True,
                10.0,
            ),
            _proposal_row(
                "transient_perfect_storm:p00001",
                "transient_perfect_storm",
                "Trout + climbing + transient perfect-storm overshoot",
                1,
                102,
                True,
                13.0,
            ),
            _proposal_row(
                "climbing_only:p00001",
                "climbing_only",
                "Climbing-only",
                1,
                103,
                False,
                21.0,
            ),
        ]
    )
    proposals.to_csv(run_dir / "proposal_summary.csv.gz", index=False)
    proposals.loc[proposals["accepted_final"]].to_csv(run_dir / "accepted_proposals.csv", index=False)

    model_inputs = load_model_inputs(DATA_DIR)
    parameter_rows = []
    for proposal in proposals.to_dict(orient="records"):
        resolved = resolve_family_parameters(model_inputs, str(proposal["family_id"]))
        for row in resolved.manifest.to_dict(orient="records"):
            value = float(row["effective_value"])
            parameter_rows.append(
                {
                    "proposal_id": proposal["proposal_id"],
                    "family_id": proposal["family_id"],
                    "parameter_id": row["parameter_id"],
                    "parameter_status": row["status"],
                    "value_natural": value,
                    "value_sampling": value,
                    "sampled_flag": row["status"] == "estimate",
                }
            )
    pd.DataFrame(parameter_rows).to_csv(run_dir / "parameter_values.csv.gz", index=False)

    target_rows = []
    penalties = {
        "persistent_joint_cause:p00001": {"CT001": 0.0, "CT007": 2.0, "CT009": 3.0, "CT010": 5.0},
        "transient_perfect_storm:p00001": {"CT001": 0.0, "CT007": 3.0, "CT009": 4.0, "CT010": 6.0},
        "climbing_only:p00001": {"CT001": 1.0, "CT007": 6.0, "CT009": 7.0, "CT010": 7.0},
    }
    for proposal in proposals.to_dict(orient="records"):
        for replicate_index in range(2):
            for target_id, penalty in penalties[str(proposal["proposal_id"])].items():
                target_rows.append(
                    {
                        "proposal_id": proposal["proposal_id"],
                        "family_id": proposal["family_id"],
                        "stage": "stage_b",
                        "replicate_index": replicate_index,
                        "target_id": target_id,
                        "scenario_id": "historical_lake",
                        "evaluation_status": "scored",
                        "raw_penalty": penalty,
                        "weighted_penalty": penalty,
                        "projected_primary": 1.0,
                        "projected_secondary": 1.0,
                    }
                )
    pd.DataFrame(target_rows).to_csv(run_dir / "target_scores.csv.gz", index=False)

    pd.DataFrame(
        [
            {
                "family_id": row["family_id"],
                "family_label": row["family_label"],
                "stage_a_draws": 1,
                "stage_a_valid_scored": 1,
                "stage_a_valid_rate": 1.0,
                "stage_a_retained": 1,
                "stage_b_evaluated": 1,
                "stage_b_valid": 1,
                "final_accepted": int(row["accepted_final"]),
                "final_acceptance_rate": float(row["accepted_final"]),
                "median_deterministic_distance_retained": row["deterministic_overall_distance"],
                "median_stochastic_distance_valid": row["stochastic_overall_distance_median"],
            }
            for row in proposals.to_dict(orient="records")
        ]
    ).to_csv(run_dir / "family_summary.csv", index=False)

    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "config": {
                    "observation_bridge_variant": "baseline_current",
                    "master_seed": 20260410,
                    "stage_a_draws_per_family": 1,
                    "stage_a_keep_per_family": 1,
                    "stage_b_historical_replicates": 2,
                    "final_acceptance_fraction": 0.5,
                    "final_acceptance_cap": 2,
                }
            }
        ),
        encoding="utf-8",
    )

    rows = []
    for role, file_name in REQUIRED_MODULE4_ARTIFACTS.items():
        path = run_dir / file_name
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


def test_module4_5_generation_cli_writes_mandatory_outputs(tmp_path: Path) -> None:
    manifest, module4_root = _write_generation_manifest(tmp_path)
    publish_root = tmp_path / "publish"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_module4_5_mechanism_interpretation.py"),
            "--module4-root",
            str(module4_root),
            "--manifest",
            str(manifest),
            "--publish-root",
            str(publish_root),
            "--trajectory-sample",
            "10",
            "--verify-hashes",
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )

    assert "Module 4.5 outputs generated" in result.stdout
    for output in MODULE4_5_MANDATORY_OUTPUTS:
        assert (publish_root / output).exists()
    decision_table = pd.read_csv(publish_root / "data" / "module4_5_family_decision_table.csv")
    assert set(decision_table["family_id"]).issuperset({"persistent_joint_cause", "transient_perfect_storm"})
