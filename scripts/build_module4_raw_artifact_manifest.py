from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "module4_observation_sensitivity_20260522T101942Z"
DEFAULT_MODULE4_ROOT = ROOT / "outputs" / "remote" / RUN_ID
DEFAULT_REMOTE_ARTIFACT_ROOT = Path("/data/codex/artifacts/galaxias") / RUN_ID
DEFAULT_OUTPUT = ROOT / "data" / "module4_raw_artifact_manifest.csv"
SUMMARY_PATH = ROOT / "data" / "module4_family_summary.csv"

CALIBRATION_SOURCE_GIT_COMMIT = "9ac8496204ad660c8f908511c981d057c4c5f371"
SUMMARY_PUBLISH_GIT_COMMIT = "eaac90ef0260946f2c2126b8bc0fc03bd1a05010"
CALIBRATION_COMMIT_BASIS = (
    "inferred_from_run_start_after_module4_runner_commit; exact_commit_absent_from_run_manifest"
)
PYTHON_VERSION_BASIS = "historical_repo_python_baseline_only; exact_patch_absent_from_run_manifest"
CALIBRATION_SOURCE_PYTHON_VERSION = "3.12.x"

EXPECTED_FILES = (
    ("proposal_summary", "proposal_summary.csv.gz"),
    ("parameter_values", "parameter_values.csv.gz"),
    ("target_scores", "target_scores.csv.gz"),
    ("accepted_proposals", "accepted_proposals.csv"),
    ("family_summary", "family_summary.csv"),
    ("run_manifest", "run_manifest.json"),
)

COMPLETED_RE = re.compile(r"^completed variant=(?P<variant>\S+) seed=(?P<seed>\d+) output=(?P<output>\S+)$")

FIELDNAMES = [
    "run_id",
    "variant_id",
    "seed",
    "run_dir_name",
    "file_role",
    "file_name",
    "required_file_present",
    "all_required_files_present",
    "local_path",
    "local_bytes",
    "local_sha256",
    "local_mtime_utc",
    "remote_scratch_path",
    "remote_artifact_path",
    "tracked_summary_run_dir",
    "run_log_completed_output",
    "run_start_utc",
    "run_end_utc",
    "source_command",
    "source_command_basis",
    "calibration_source_git_commit",
    "calibration_source_git_commit_basis",
    "summary_publish_git_commit",
    "source_python_version",
    "source_python_version_basis",
    "manifest_builder_git_commit",
    "manifest_builder_python_version",
    "stage_a_draws_per_family",
    "stage_a_keep_per_family",
    "stage_b_historical_replicates",
    "final_acceptance_fraction",
    "final_acceptance_cap",
    "workers",
    "batch_size",
    "families",
    "stochastic_baselines",
    "resume",
    "run_manifest_module",
    "parameter_count",
    "target_count",
    "scenario_ids",
    "tracked_summary_family_rows",
    "tracked_summary_final_accepted_total",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the tracked provenance manifest for the raw Module 4 artifact mirror."
    )
    parser.add_argument("--module4-root", type=Path, default=DEFAULT_MODULE4_ROOT)
    parser.add_argument("--remote-artifact-root", type=Path, default=DEFAULT_REMOTE_ARTIFACT_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--calibration-source-git-commit", default=CALIBRATION_SOURCE_GIT_COMMIT)
    parser.add_argument("--summary-publish-git-commit", default=SUMMARY_PUBLISH_GIT_COMMIT)
    parser.add_argument(
        "--source-python-version",
        default=None,
        help=(
            "Exact Python version used for the source run. Defaults to the historical "
            "Module 4 calibration baseline with an unknown patch."
        ),
    )
    return parser.parse_args()


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def utc_mtime(path: Path) -> str:
    stamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_summary_runs(path: Path) -> list[dict[str, Any]]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for row in read_csv(path):
        key = (row["variant_id"], row["seed"])
        if key not in records:
            records[key] = {
                "variant_id": row["variant_id"],
                "seed": row["seed"],
                "tracked_summary_run_dir": row["run_dir"],
                "tracked_summary_family_rows": 0,
                "tracked_summary_final_accepted_total": 0,
            }
        records[key]["tracked_summary_family_rows"] += 1
        records[key]["tracked_summary_final_accepted_total"] += int(row["final_accepted"])
    return list(records.values())


def read_run_log(path: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {"completed": {}}
    if not path.exists():
        return meta
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if line.startswith("START_UTC="):
                meta["run_start_utc"] = line.split("=", 1)[1]
            elif line.startswith("END_UTC="):
                meta["run_end_utc"] = line.split("=", 1)[1]
            elif line.startswith("RUN_ID="):
                meta["run_id"] = line.split("=", 1)[1]
            else:
                match = COMPLETED_RE.match(line)
                if match:
                    key = (match.group("variant"), match.group("seed"))
                    meta["completed"][key] = match.group("output")
    return meta


def git_head() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip()


def source_python_version(explicit_version: str | None) -> str:
    if explicit_version:
        return explicit_version
    return CALIBRATION_SOURCE_PYTHON_VERSION


def command_from_config(config: dict[str, Any], variant: str, seed: str, remote_output: str) -> str:
    remote_root = str(Path(remote_output).parent) if remote_output else str(Path(config["output_dir"]).parent)
    command = [
        "uv",
        "run",
        "python",
        "scripts/run_module4_observation_sensitivity.py",
        "--output-dir",
        remote_root,
        "--variants",
        variant,
        "--seeds",
        seed,
        "--stage-a-draws-per-family",
        str(config.get("stage_a_draws_per_family", "")),
        "--stage-a-keep-per-family",
        str(config.get("stage_a_keep_per_family", "")),
        "--stage-b-historical-replicates",
        str(config.get("stage_b_historical_replicates", "")),
        "--final-acceptance-fraction",
        str(config.get("final_acceptance_fraction", "")),
        "--final-acceptance-cap",
        str(config.get("final_acceptance_cap", "")),
        "--workers",
        str(config.get("workers", "")),
        "--batch-size",
        str(config.get("batch_size", "")),
    ]
    if config.get("resume"):
        command.append("--resume")
    return shlex.join(command)


def build_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[str]]:
    module4_root = args.module4_root
    if not module4_root.exists():
        raise FileNotFoundError(f"Module 4 root does not exist: {module4_root}")

    run_log = read_run_log(module4_root / "run.log")
    builder_git_commit = git_head()
    builder_python_version = platform.python_version()
    run_rows = read_summary_runs(args.summary)
    rows: list[dict[str, str]] = []
    missing: list[str] = []

    for run in run_rows:
        variant = str(run["variant_id"])
        seed = str(run["seed"])
        run_dir_name = Path(str(run["tracked_summary_run_dir"])).name
        run_dir = module4_root / run_dir_name
        manifest_path = run_dir / "run_manifest.json"
        manifest = load_json(manifest_path) if manifest_path.exists() else {}
        config = manifest.get("config", {}) if isinstance(manifest.get("config", {}), dict) else {}
        remote_scratch_run_dir = str(config.get("output_dir", run_log["completed"].get((variant, seed), "")))
        run_log_output = str(run_log["completed"].get((variant, seed), ""))
        required_paths = [run_dir / file_name for _, file_name in EXPECTED_FILES]
        all_present = all(path.exists() for path in required_paths)
        run_manifest_sha = sha256_file(manifest_path) if manifest_path.exists() else ""

        if not all_present:
            for path in required_paths:
                if not path.exists():
                    missing.append(repo_relative(path))

        for file_role, file_name in EXPECTED_FILES:
            path = run_dir / file_name
            present = path.exists()
            remote_scratch_path = str(Path(remote_scratch_run_dir) / file_name) if remote_scratch_run_dir else ""
            remote_artifact_path = str(args.remote_artifact_root / run_dir_name / file_name)
            local_sha = sha256_file(path) if present else ""
            local_bytes = str(path.stat().st_size) if present else ""
            local_mtime = utc_mtime(path) if present else ""
            rows.append(
                {
                    "run_id": str(run_log.get("run_id", RUN_ID)),
                    "variant_id": variant,
                    "seed": seed,
                    "run_dir_name": run_dir_name,
                    "file_role": file_role,
                    "file_name": file_name,
                    "required_file_present": bool_text(present),
                    "all_required_files_present": bool_text(all_present),
                    "local_path": repo_relative(path),
                    "local_bytes": local_bytes,
                    "local_sha256": local_sha,
                    "local_mtime_utc": local_mtime,
                    "remote_scratch_path": remote_scratch_path,
                    "remote_artifact_path": remote_artifact_path,
                    "tracked_summary_run_dir": str(run["tracked_summary_run_dir"]),
                    "run_log_completed_output": run_log_output,
                    "run_start_utc": str(run_log.get("run_start_utc", "")),
                    "run_end_utc": str(run_log.get("run_end_utc", "")),
                    "source_command": command_from_config(config, variant, seed, run_log_output),
                    "source_command_basis": "single_run_reproducer_reconstructed_from_run_manifest",
                    "calibration_source_git_commit": str(args.calibration_source_git_commit),
                    "calibration_source_git_commit_basis": CALIBRATION_COMMIT_BASIS,
                    "summary_publish_git_commit": str(args.summary_publish_git_commit),
                    "source_python_version": source_python_version(args.source_python_version),
                    "source_python_version_basis": PYTHON_VERSION_BASIS,
                    "manifest_builder_git_commit": builder_git_commit,
                    "manifest_builder_python_version": builder_python_version,
                    "stage_a_draws_per_family": str(config.get("stage_a_draws_per_family", "")),
                    "stage_a_keep_per_family": str(config.get("stage_a_keep_per_family", "")),
                    "stage_b_historical_replicates": str(config.get("stage_b_historical_replicates", "")),
                    "final_acceptance_fraction": str(config.get("final_acceptance_fraction", "")),
                    "final_acceptance_cap": str(config.get("final_acceptance_cap", "")),
                    "workers": str(config.get("workers", "")),
                    "batch_size": str(config.get("batch_size", "")),
                    "families": ";".join(str(item) for item in config.get("families", [])),
                    "stochastic_baselines": bool_text(bool(config.get("stochastic_baselines", False))),
                    "resume": bool_text(bool(config.get("resume", False))),
                    "run_manifest_module": str(manifest.get("module", "")),
                    "parameter_count": str(manifest.get("parameter_count", "")),
                    "target_count": str(manifest.get("target_count", "")),
                    "scenario_ids": ";".join(str(item) for item in manifest.get("scenario_ids", [])),
                    "tracked_summary_family_rows": str(run["tracked_summary_family_rows"]),
                    "tracked_summary_final_accepted_total": str(run["tracked_summary_final_accepted_total"]),
                }
            )
    return rows, missing


def write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    rows, missing = build_rows(args)
    write_manifest(args.output, rows)
    run_count = len({(row["variant_id"], row["seed"]) for row in rows})
    print(f"Wrote {len(rows)} file records across {run_count} Module 4 runs to {repo_relative(args.output)}")
    if missing:
        print("Missing required Module 4 files:", file=sys.stderr)
        for path in missing:
            print(f"- {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
