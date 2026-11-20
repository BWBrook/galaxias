#!/usr/bin/env python3
"""Qualify the singleton guard against a bounded slice of frozen histories.

This is a read-only replay check.  It runs the original common-model kernel
for one frozen source in each configuration/restriction group and the first
two archived validation seeds, then compares every archived history field
produced by the old history task.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from galaxias_model import common_model, mate_guard  # noqa: E402
from scripts.run_common_model_comparison import (  # noqa: E402
    IDENTITY,
    _flatten_history,
    _resolved,
    file_hash,
    require,
    require_runtime_match,
    verify_archive,
)


SEED_FIELDS = ("replicate_index", "simulation_seed", "environment_seed")
ARCHIVE_METADATA = (*IDENTITY, "source_id", "phase", *SEED_FIELDS)


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, float_precision="round_trip")


def _load_freeze(freeze_dir: Path) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    manifest_path = freeze_dir / "freeze_manifest.json"
    require(manifest_path.exists(), f"missing freeze manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("status") == "frozen", "freeze is not marked frozen")
    for name, expected in manifest.get("outputs", {}).items():
        path = freeze_dir / name
        require(path.exists() and file_hash(path) == expected, f"freeze output drift: {path}")
    sources = _read(freeze_dir / "sources.csv")
    parameters = _read(freeze_dir / "parameter_values.csv.gz")
    seeds = pd.read_csv(
        freeze_dir / "history_seeds.csv.gz",
        dtype={"simulation_seed": "uint64", "environment_seed": "uint64"},
    )
    selected_profiles = _read(freeze_dir / "selected_profiles.csv")
    require(len(sources) == int(manifest["source_count"]), "frozen source count mismatch")
    require(len(seeds) == int(manifest["history_count"]), "frozen history count mismatch")
    require(len(selected_profiles) == 1527, "frozen profile count mismatch")
    return manifest, sources, parameters, seeds


def _baseline_bound_files(freeze_manifest: Mapping[str, Any], baseline_dir: Path) -> dict[str, dict[str, Any]]:
    """Verify and return the frozen baseline bindings relative to ``validate``."""
    result: dict[str, dict[str, Any]] = {}
    for relative, expected in freeze_manifest["original_files"].items():
        if relative.startswith("validate/"):
            path = baseline_dir / relative.removeprefix("validate/")
        else:
            path = baseline_dir.parent / relative
        require(path.exists(), f"missing frozen baseline binding: {path}")
        observed = file_hash(path)
        require(observed == expected, f"baseline binding drift: {relative}")
        result[relative] = observed
    return result


def _select_sources(sources: pd.DataFrame) -> pd.DataFrame:
    required = {"source_ordinal", "source_id", "configuration", "restriction"}
    require(required.issubset(sources.columns), "frozen sources lack selection fields")
    ordered = sources.sort_values(["configuration", "restriction", "source_ordinal"], kind="mergesort")
    selected = ordered.groupby(["configuration", "restriction"], sort=True, observed=True).head(1)
    selected = selected.sort_values("source_ordinal", kind="mergesort").reset_index(drop=True)
    require(len(selected) == 24, f"expected one source per 6x4 group, found {len(selected)}")
    require(selected.source_id.is_unique, "selected source IDs are duplicated")
    return selected


def _read_archived_rows(raw_path: Path, source_ids: set[str]) -> pd.DataFrame:
    require(raw_path.exists(), f"missing baseline histories: {raw_path}")
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        raw_path,
        chunksize=100_000,
        float_precision="round_trip",
        dtype={"simulation_seed": "uint64", "environment_seed": "uint64"},
    ):
        keep = chunk.source_id.astype(str).isin(source_ids) & chunk.replicate_index.isin((1, 2))
        if keep.any():
            chunks.append(chunk.loc[keep].copy())
    require(chunks, "no selected archived histories found")
    rows = pd.concat(chunks, ignore_index=True)
    require(not rows.duplicated(["source_id", "replicate_index"]).any(), "selected archive rows are duplicated")
    return rows


def _same_value(left: Any, right: Any) -> bool:
    left_missing = pd.isna(left)
    right_missing = pd.isna(right)
    if bool(left_missing) or bool(right_missing):
        return bool(left_missing) and bool(right_missing)
    return bool(left == right)


def _history_row(
    source: Mapping[str, Any],
    parameters: pd.DataFrame,
    seed_row: Mapping[str, Any],
    data_dir: Path,
) -> dict[str, Any]:
    params = _resolved(parameters.to_dict("records"), str(data_dir))
    demographic_seed = int(seed_row["simulation_seed"])
    environment_seed = int(seed_row["environment_seed"])
    result = common_model.run_common_history(
        params,
        str(source["restriction"]),
        str(source["configuration"]),
        demographic_seed,
        environment_seed,
    )
    row = {key: source[key] for key in (*IDENTITY, "source_id")}
    row.update(
        phase="validate",
        replicate_index=int(seed_row["replicate_index"]),
        simulation_seed=demographic_seed,
        environment_seed=environment_seed,
    )
    row.update(_flatten_history(result))
    trajectory = result.trajectory_table
    for year in (1980, 1983):
        state = trajectory.loc[trajectory.year.eq(year)].iloc[0]
        row[f"ct005_N_L_{year}"] = float(state.N_L)
        row[f"ct005_C_L_{year}"] = float(state.C_L)
    row["ct005_cross_product_change"] = (
        row["ct005_C_L_1983"] * row["ct005_N_L_1980"]
        - row["ct005_C_L_1980"] * row["ct005_N_L_1983"]
    )
    row.update(
        {
            f"annual_N_R_{int(year)}": float(value)
            for year, value in trajectory[["year", "N_R"]].itertuples(index=False, name=None)
        }
    )
    return row


def _compare_history_rows(archived: pd.DataFrame, generated: list[dict[str, Any]]) -> dict[str, Any]:
    generated_by_key = {(str(row["source_id"]), int(row["replicate_index"])): row for row in generated}
    archived_fields = [field for field in archived.columns if field not in ARCHIVE_METADATA]
    generated_fields = sorted(set().union(*(row.keys() for row in generated)))
    missing_generated = sorted(set(archived_fields) - set(generated_fields))
    extra_generated = sorted(set(generated_fields) - set(archived.columns))
    mismatches: list[dict[str, Any]] = []
    mismatch_count = 0
    for archived_row in archived.to_dict("records"):
        key = (str(archived_row["source_id"]), int(archived_row["replicate_index"]))
        expected = generated_by_key.get(key)
        require(expected is not None, f"missing regenerated history for {key}")
        for field in archived.columns:
            if field not in expected:
                mismatch_count += 1
                if len(mismatches) < 20:
                    mismatches.append({"key": key, "field": field, "reason": "not_generated"})
                continue
            if not _same_value(archived_row[field], expected[field]):
                mismatch_count += 1
                if len(mismatches) < 20:
                    mismatches.append(
                        {
                            "key": key,
                            "field": field,
                            "archived": archived_row[field],
                            "regenerated": expected[field],
                        }
                    )
    return {
        "archived_common_field_count": len(archived_fields),
        "generated_field_count": len(generated_fields),
        "generated_extra_fields": extra_generated,
        "archived_fields_missing_from_generated": missing_generated,
        "mismatch_count": mismatch_count,
        "mismatch_examples": mismatches,
        "passed": mismatch_count == 0 and not missing_generated,
    }


def _compare_initial_tuples(
    selected: pd.DataFrame,
    parameters: pd.DataFrame,
    data_dir: Path,
) -> dict[str, Any]:
    forcing_mismatches = 0
    state_mismatches = 0
    rows = []
    for source in selected.to_dict("records"):
        source_parameters = parameters.loc[parameters.source_id.eq(source["source_id"])]
        params = _resolved(source_parameters.to_dict("records"), str(data_dir))
        key = common_model._parameter_key(params)
        original_forcing, original_state = common_model._prepared_source(key, False)
        guarded_forcing, guarded_state = mate_guard._prepared_source(key, False)
        forcing_equal = original_forcing.equals(guarded_forcing)
        state_equal = all(left == right for left, right in zip(original_state, guarded_state, strict=True))
        forcing_mismatches += int(not forcing_equal)
        state_mismatches += int(not state_equal)
        rows.append(
            {
                "source_id": source["source_id"],
                "configuration": source["configuration"],
                "restriction": source["restriction"],
                "forcing_equal": forcing_equal,
                "initial_state_equal": state_equal,
            }
        )
    return {
        "source_count": len(rows),
        "forcing_mismatch_count": forcing_mismatches,
        "initial_state_mismatch_count": state_mismatches,
        "per_source": rows,
    }


def qualify(freeze_dir: Path, baseline_dir: Path, output_file: Path) -> dict[str, Any]:
    require(not output_file.exists(), f"output already exists: {output_file}")
    freeze_manifest, sources, parameters, seeds = _load_freeze(freeze_dir)
    baseline_dir = baseline_dir.resolve()
    baseline_manifest_path = baseline_dir / "run_manifest.json"
    require(baseline_manifest_path.exists(), f"missing baseline manifest: {baseline_manifest_path}")
    baseline_manifest = json.loads(baseline_manifest_path.read_text(encoding="utf-8"))
    require_runtime_match(baseline_manifest)
    archive_manifest = verify_archive(baseline_dir, phase="validate")
    bound_files = _baseline_bound_files(freeze_manifest, baseline_dir)
    require(
        file_hash(baseline_manifest_path) == freeze_manifest["original_files"]["validate/run_manifest.json"],
        "baseline manifest differs from frozen ancestry",
    )

    selected = _select_sources(sources)
    selected_ids = set(selected.source_id.astype(str))
    source_seeds = seeds.loc[seeds.source_id.astype(str).isin(selected_ids) & seeds.replicate_index.isin((1, 2))].copy()
    require(len(source_seeds) == len(selected) * 2, "selected seed count mismatch")
    require(not source_seeds.duplicated(["source_id", "replicate_index"]).any(), "selected seeds duplicated")
    require(source_seeds.groupby("source_id").size().eq(2).all(), "selected seeds do not have two replicates")

    archived = _read_archived_rows(baseline_dir / "raw_histories.csv.gz", selected_ids)
    require(len(archived) == len(selected) * 2, "selected archive count mismatch")
    params_by_source = {source_id: group for source_id, group in parameters.groupby("source_id", sort=False)}
    generated = [
        _history_row(
            source,
            params_by_source[str(source["source_id"])],
            seed_row,
            ROOT / "data",
        )
        for source in selected.to_dict("records")
        for seed_row in source_seeds.loc[source_seeds.source_id.eq(source["source_id"])].sort_values("replicate_index").to_dict("records")
    ]
    parity = _compare_history_rows(archived, generated)
    initial_tuples = _compare_initial_tuples(selected, parameters, ROOT / "data")
    receipt = {
        "status": "qualified" if parity["passed"] and initial_tuples["forcing_mismatch_count"] == 0 else "failed",
        "scope": "common_model_mate_guard_replay_qualification",
        "runtime": baseline_manifest["runtime"],
        "runtime_match": True,
        "freeze_manifest": file_hash(freeze_dir / "freeze_manifest.json"),
        "baseline_manifest": file_hash(baseline_manifest_path),
        "baseline_archive_manifest": archive_manifest,
        "baseline_bindings": bound_files,
        "selected_source_count": len(selected),
        "selected_history_count": len(generated),
        "selected_source_ids": selected.source_id.astype(str).tolist(),
        "selected_seeds": [
            {
                "source_id": str(row.source_id),
                "replicate_index": int(row.replicate_index),
                "simulation_seed": int(row.simulation_seed),
                "environment_seed": int(row.environment_seed),
            }
            for row in source_seeds.sort_values(["source_id", "replicate_index"]).itertuples(index=False)
        ],
        "actual_original_historical_calls": len(generated),
        "conservative_initialization_executions": len(selected) * 2,
        "initial_tuple_comparison": initial_tuples,
        "parity": parity,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    require(parity["passed"], f"archived replay parity failed: {parity['mismatch_count']} mismatches")
    require(initial_tuples["forcing_mismatch_count"] == 0, "original and amended forcing differ")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-dir", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True, help="original validate archive directory")
    parser.add_argument("--output-file", type=Path, required=True)
    args = parser.parse_args()
    receipt = qualify(args.freeze_dir, args.baseline_dir, args.output_file)
    print(json.dumps({key: receipt[key] for key in ("status", "selected_source_count", "selected_history_count", "actual_original_historical_calls")}, sort_keys=True))


if __name__ == "__main__":
    main()
