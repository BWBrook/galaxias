from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_MODULE4_ARTIFACTS: dict[str, str] = {
    "proposal_summary": "proposal_summary.csv.gz",
    "parameter_values": "parameter_values.csv.gz",
    "target_scores": "target_scores.csv.gz",
    "accepted_proposals": "accepted_proposals.csv",
    "family_summary": "family_summary.csv",
    "run_manifest": "run_manifest.json",
}

MODULE4_5_MANDATORY_OUTPUTS: tuple[str, ...] = (
    "data/module4_5_proposal_set_membership.csv",
    "data/module4_5_distance_audit.csv",
    "data/module4_5_parameter_summary.csv",
    "data/module4_5_parameter_contrasts.csv",
    "data/module4_5_nuisance_audit.csv",
    "data/module4_5_target_family_summary.csv",
    "data/module4_5_pressure_landmarks.csv",
    "data/module4_5_trajectory_landmarks.csv",
    "data/module4_5_family_decision_table.csv",
    "docs/module4_5_mechanism_interpretation_review.md",
)


@dataclass(frozen=True)
class Module4ArtifactValidation:
    manifest_path: Path
    module4_root: Path
    record_count: int
    run_count: int
    missing_files: tuple[str, ...]
    missing_roles: tuple[str, ...]
    hash_mismatches: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not (self.missing_files or self.missing_roles or self.hash_mismatches)


def module4_5_output_paths(publish_root: Path) -> dict[str, Path]:
    return {output: publish_root / output for output in MODULE4_5_MANDATORY_OUTPUTS}


def read_raw_artifact_manifest(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_path(row: dict[str, str], module4_root: Path) -> Path:
    if module4_root:
        return module4_root / row["run_dir_name"] / row["file_name"]
    return ROOT / row["local_path"]


def validate_module4_raw_artifact_manifest(
    manifest_path: Path,
    module4_root: Path,
    *,
    verify_hashes: bool = False,
) -> Module4ArtifactValidation:
    rows = read_raw_artifact_manifest(manifest_path)
    runs = sorted({(row["variant_id"], row["seed"], row["run_dir_name"]) for row in rows})
    expected_roles = set(REQUIRED_MODULE4_ARTIFACTS)
    roles_by_run: dict[tuple[str, str, str], set[str]] = {run: set() for run in runs}
    missing_files: list[str] = []
    hash_mismatches: list[str] = []

    for row in rows:
        run = (row["variant_id"], row["seed"], row["run_dir_name"])
        roles_by_run.setdefault(run, set()).add(row["file_role"])
        path = _artifact_path(row, module4_root)
        if not path.exists():
            missing_files.append(path.as_posix())
            continue
        if verify_hashes:
            expected_hash = row.get("local_sha256", "")
            if expected_hash and sha256_file(path) != expected_hash:
                hash_mismatches.append(path.as_posix())

    missing_roles = []
    for variant, seed, run_dir_name in runs:
        missing = sorted(expected_roles - roles_by_run[(variant, seed, run_dir_name)])
        for role in missing:
            missing_roles.append(f"{variant}:{seed}:{run_dir_name}:{role}")

    return Module4ArtifactValidation(
        manifest_path=manifest_path,
        module4_root=module4_root,
        record_count=len(rows),
        run_count=len(runs),
        missing_files=tuple(sorted(missing_files)),
        missing_roles=tuple(sorted(missing_roles)),
        hash_mismatches=tuple(sorted(hash_mismatches)),
    )
