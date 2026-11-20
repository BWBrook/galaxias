#!/usr/bin/env python3
"""Bounded, reproducible diagnostics for the frozen age-linked archive.

This script only reads the already generated archive.  It does not call the
demographic runner or generate biological simulations.  Its historical Lake
scores are exploratory relative-composition diagnostics; they are not a
historical fit, posterior, or causal analysis.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Iterator

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.run_age_historical_refocus import reconstruct_compartment_breeders
from galaxias_model.age_demography import AgeDemography, _keyed_rng, _survive


SCRIPT_RELATIVE = "scripts/diagnose_age_lake_archive.py"
ARCHIVE_RELATIVE = "outputs/remote/age_linked_recovery_20261001/gate"
LAKE_DATA_RELATIVE = "data/age_structured_design_20260929/lake_figure6_digitised.csv"
SELECTED_YEARS = (1976, 1977, 1978, 1979, 1980, 1983, 1986, 1989)
ANNUAL_YEARS = tuple(range(1976, 1992))
EXCLUDED_BIOLOGICAL_FIELDS = {
    "cell_id", "source_id", "namespace", "role", "source_seed", "index",
    "index_stratum", "ledger_timing", "march_retention", "cell",
}


def _binding(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def _decompressed_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _jsonl(path: Path, *, compressed: bool) -> Iterator[dict[str, Any]]:
    opener = gzip.open if compressed else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row is not an object: {path}:{line_number}")
            yield value


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> None:
    names = list(fields)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in names})


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _key(row: dict[str, Any]) -> tuple[str, str, str, int]:
    return (str(row.get("cell_id", "")), str(row.get("namespace", "")),
            str(row.get("source_id", "")), int(row.get("replicate", -1)))


def _verify_archive(archive: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest_path = archive / "run_manifest.json"
    manifest = _read_json(manifest_path)
    if manifest.get("status") != "complete":
        raise ValueError(f"archive manifest is not complete: {manifest.get('status')!r}")
    outputs = manifest.get("outputs")
    required = {"full_histories.jsonl.gz", "histories.jsonl.gz", "source_banks.jsonl", "source_support.csv"}
    if not isinstance(outputs, dict) or not required.issubset(outputs):
        raise ValueError("archive manifest does not bind all required archive outputs")
    used: dict[str, dict[str, Any]] = {str(manifest_path.relative_to(ROOT)): _binding(manifest_path)}
    for name, expected in outputs.items():
        path = archive / str(name)
        if not path.is_file() or not isinstance(expected, dict):
            raise ValueError(f"missing or invalid archive output binding: {name}")
        actual = _binding(path)
        if actual != {"sha256": expected.get("sha256"), "bytes": expected.get("bytes")}:
            raise ValueError(f"archive output hash/size mismatch: {name}")
        used[str(path.relative_to(ROOT))] = actual
    content_hashes = manifest.get("content_sha256", {})
    for name, expected_name in (("full_histories.jsonl.gz", "full_histories.jsonl"),
                                ("histories.jsonl.gz", "histories.jsonl")):
        expected = content_hashes.get(expected_name)
        if expected is not None and _decompressed_hash(archive / name) != expected:
            raise ValueError(f"archive decompressed content hash mismatch: {name}")
    source_bindings = manifest.get("source_bindings", {})
    if not isinstance(source_bindings, dict):
        raise ValueError("archive manifest lacks source bindings")
    for relative, expected in source_bindings.items():
        path = ROOT / str(relative)
        if not path.is_file() or not isinstance(expected, dict):
            raise ValueError(f"missing manifest source binding: {relative}")
        actual = _binding(path)
        if actual != {"sha256": expected.get("sha256"), "bytes": expected.get("bytes")}:
            raise ValueError(f"manifest source hash/size mismatch: {relative}")
        used[str(relative)] = actual
    return manifest, used


def _source_vector(row: dict[str, Any]) -> str:
    vector = {key: row[key] for key in sorted(row) if key not in EXCLUDED_BIOLOGICAL_FIELDS}
    return json.dumps(vector, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _source_grouping(source_rows: list[dict[str, Any]], history_rows: list[dict[str, Any]], complete_rows: list[dict[str, Any]],
                     manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    history_counts: Counter[tuple[str, str]] = Counter(
        (str(row.get("namespace", "")), str(row.get("source_id", ""))) for row in history_rows
    )
    complete_counts: Counter[tuple[str, str]] = Counter(
        (str(row["namespace"]), str(row["source_id"])) for row in complete_rows
    )
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        groups[(str(row["role"]), str(row["source_id"]))].append(row)
    rows = []
    vector_hashes: set[tuple[str, str]] = set()
    for (role, source_id), members in sorted(groups.items()):
        vectors = {_source_vector(member) for member in members}
        if len(vectors) != 1:
            raise ValueError(f"biological vector changes within source group: {role}/{source_id}")
        vector_hash = hashlib.sha256(next(iter(vectors)).encode()).hexdigest()
        vector_hashes.add((role, vector_hash))
        cells = {str(member["cell_id"]) for member in members}
        family = members[0]["cell"]
        # The frozen design has eight cells for A6/near_obligate (both
        # removal accounts) and four cells for every other source family.
        expected_cells = 8 if family["maximum_age"] == 6 and family["nursery"] == "near_obligate" else 4
        total_history_rows = int(history_counts[("truth" if role == "truth" else "bank", source_id)])
        complete_history_rows = int(complete_counts[("truth" if role == "truth" else "bank", source_id)])
        expected_history_rows = len(members) * int(manifest.get("replicates_per_source", 4))
        rows.append({
            "role": role,
            "source_id": source_id,
            "bank_rows": len(members),
            "distinct_cells": len(cells),
            "expected_paired_cells": expected_cells,
            "pair_count_mismatch": len(cells) != expected_cells,
            "history_rows_total": total_history_rows,
            "complete_history_rows": complete_history_rows,
            "expected_history_rows": expected_history_rows,
            "history_row_count_mismatch": total_history_rows != expected_history_rows,
            "complete_source_id_rows_are_not_independent": True,
            "biological_vector_hash": vector_hash,
        })
    return rows, {role: len({vector for group_role, vector in vector_hashes if group_role == role}) for role in ("truth", "bank")}


def _event_labels() -> dict[tuple[str, int], str]:
    """Recreate the runner's event-id labels for failure accounting only."""
    src = ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from galaxias_model.age_runner import _calendar, _event_id  # type: ignore

    dates = _calendar(1965, 2012)
    labels: dict[tuple[str, int], str] = {}
    for date in dates:
        ordinal = sum(1 for item in dates if item.year == date.year and (item.time, item.label) < (date.time, date.label))
        for site in ("pedder", "oberon", "strathgordon"):
            labels[(site, _event_id(site, date, ordinal))] = date.label
    for date in dates:
        if date.label.startswith("transfer_"):
            for site in ("oberon", "strathgordon"):
                labels[(site, _event_id(site, date, 20 + date.year))] = date.label
    return labels


_FAILURE_EVENT_RE = re.compile(r"^(pedder|oberon|strathgordon)\s+(\d{4}): event (\d+)")
_HOLDING_RE = re.compile(r"^linked history year (\d+): holding (\d+)")
_RELEASE_RE = re.compile(r"^linked history year (\d+): insufficient held fish")


def _failure_row(row: dict[str, Any], labels: dict[tuple[str, int], str]) -> dict[str, Any]:
    failure = str(row.get("failure") or "")
    timing = str(row.get("ledger_timing") or "")
    match = _FAILURE_EVENT_RE.match(failure)
    if match:
        site, year, event_id = match.group(1), int(match.group(2)), int(match.group(3))
        label = labels.get((site, event_id), f"unresolved_event_{event_id}")
        return {"failure_year": year, "site": site, "label": label, "failure_kind": "event_availability",
                "failure_text": failure, "namespace": row.get("namespace", ""), "cell_id": row.get("cell_id", "")}
    match = _HOLDING_RE.match(failure)
    if match:
        year, event_id = int(match.group(1)), int(match.group(2))
        label = labels.get(("pedder", event_id), f"unresolved_holding_{event_id}")
        return {"failure_year": year, "site": "linked", "label": f"holding:{label}", "failure_kind": "holding_availability",
                "failure_text": failure, "namespace": row.get("namespace", ""), "cell_id": row.get("cell_id", "")}
    match = _RELEASE_RE.match(failure)
    if match:
        year = int(match.group(1))
        label = f"may_1997_release_{timing}" if year == 1997 else f"release_{timing}"
        return {"failure_year": year, "site": "linked", "label": label, "failure_kind": "release_availability",
                "failure_text": failure, "namespace": row.get("namespace", ""), "cell_id": row.get("cell_id", "")}
    if failure == "requested neutral allocation is unachievable":
        return {"failure_year": "", "site": "", "label": "neutral_allocation", "failure_kind": "algebraic_feasibility",
                "failure_text": failure, "namespace": row.get("namespace", ""), "cell_id": row.get("cell_id", "")}
    return {"failure_year": "", "site": "", "label": "unresolved_failure", "failure_kind": "unresolved",
            "failure_text": failure, "namespace": row.get("namespace", ""), "cell_id": row.get("cell_id", "")}


def _state_metrics(state: Any) -> dict[str, float]:
    array = np.asarray(state, dtype=float)
    if array.ndim != 3 or array.shape[:2] != (2, 2):
        raise ValueError(f"unexpected state shape: {array.shape}")
    lake = float(array[0].sum())
    refuge = float(array[1].sum())
    total = lake + refuge
    age1plus = float(array[:, :, 1:].sum())
    return {"total": total, "lake": lake, "refuge": refuge, "age0": float(array[:, :, 0].sum()),
            "age1plus": age1plus, "lake_age0": float(array[0, :, 0].sum()),
            "lake_age1plus": float(array[0, :, 1:].sum())}


def _independent_compartment_replay(history: dict[str, Any], source: dict[str, Any], process_seed: int) -> np.ndarray:
    """Independently replay only the kernel's retained 2002 breeder draws."""
    demo = AgeDemography(**source["demography"])
    matches = [row for row in history["checkpoint_states"]["pedder"]
               if int(row["year"]) == 2002 and row["label"] == "transfer_2002_late"]
    if len(matches) != 1 or not math.isclose(float(matches[0]["time"]), demo.spawn_fraction, abs_tol=1e-12):
        raise ValueError("exact 2002 prespawning checkpoint is required for independent replay")
    current = np.asarray(matches[0]["state"], dtype=float)
    if (current.shape != (2, 2, demo.max_age + 1) or not np.isfinite(current).all()
            or np.any(current < 0) or np.any(current != np.floor(current))
            or np.any(current[:, :, demo.max_age] != 0)):
        raise ValueError("independent replay requires the stochastic pre-breeding eligible state")
    result = np.zeros((2, 2), dtype=float)
    for compartment in range(2):
        for sex in range(2):
            for age in range(demo.max_age):
                rng = _keyed_rng(int(process_seed), 2002, "pedder", 30000, compartment, sex, age)
                result[compartment, sex] += _survive(
                    current[compartment, sex, age], demo.breeding_probability[age + 1],
                    stochastic=True, rng=rng,
                )
    return result


def _diagnose_complete(row: dict[str, Any], terminal_alive: bool, process_seed: int,
                       source_meta: dict[tuple[str, str, str], dict[str, Any]]) -> dict[str, Any]:
    history = row.get("history")
    if not isinstance(history, dict) or not history.get("valid"):
        raise ValueError("complete archive row lacks a valid full history")
    namespace = str(row["namespace"])
    role = "truth" if namespace == "truth" or namespace.endswith(":truth") else "bank"
    key = (str(row["cell_id"]), role, str(row["source_id"]))
    meta = source_meta[key]
    annual = history["annual_states"]["pedder"]
    end = _state_metrics(annual["2002"])
    diag = (history.get("per_year_diagnostics") or {}).get("pedder", {}).get("2002", {}) or {}
    helper_breeders = np.asarray(reconstruct_compartment_breeders(history, meta, int(process_seed)), dtype=float)
    independent_breeders = _independent_compartment_replay(history, meta, int(process_seed))
    if helper_breeders.shape != (2, 2) or not np.array_equal(helper_breeders, independent_breeders):
        raise ValueError(f"helper/independent 2002 breeder replay mismatch: {row['cell_id']}/{row['source_id']}/{row['replicate']}")
    recorded_pooled = np.asarray([float(diag["pre_spawn_females"]), float(diag["pre_spawn_males"])])
    if not np.array_equal(helper_breeders.sum(axis=0), recorded_pooled):
        raise ValueError(f"reconstructed 2002 breeder pools differ from recorded pools: {row['cell_id']}/{row['source_id']}/{row['replicate']}")
    female_by_comp = helper_breeders[:, 0].tolist()
    male_by_comp = helper_breeders[:, 1].tolist()
    compartments_available = True
    pooled_pair = float(diag.get("pre_spawn_females", 0.0)) >= 1.0 and float(diag.get("pre_spawn_males", 0.0)) >= 1.0
    same_compartment_pair = any(float(female_by_comp[index]) >= 1.0 and float(male_by_comp[index]) >= 1.0 for index in range(2)) if compartments_available else ""
    result: dict[str, Any] = {
        "cell_id": row["cell_id"], "namespace": row["namespace"], "source_id": row["source_id"], "replicate": row["replicate"],
        "restriction": meta["cell"]["restriction"], "removal_account": meta["cell"]["removal_account"],
        "maximum_age": meta["cell"]["maximum_age"], "nursery": meta["cell"]["nursery"], "index_stratum": row.get("index_stratum", meta.get("index_stratum", "")),
        "refuge_index": row.get("refuge_index", meta.get("refuge_index", "")), "terminal_class": "persist" if terminal_alive else "loss",
        "total_2002": end["total"], "lake_2002": end["lake"], "refuge_2002": end["refuge"], "age1plus_2002": end["age1plus"],
        "pre_spawn_females_2002": diag.get("pre_spawn_females", ""), "pre_spawn_males_2002": diag.get("pre_spawn_males", ""),
        "pre_spawn_female_lake_2002": female_by_comp[0] if isinstance(female_by_comp, list) and len(female_by_comp) == 2 else "",
        "pre_spawn_female_refuge_2002": female_by_comp[1] if isinstance(female_by_comp, list) and len(female_by_comp) == 2 else "",
        "pre_spawn_male_lake_2002": male_by_comp[0] if isinstance(male_by_comp, list) and len(male_by_comp) == 2 else "",
        "pre_spawn_male_refuge_2002": male_by_comp[1] if isinstance(male_by_comp, list) and len(male_by_comp) == 2 else "",
        "pre_spawn_compartment_fields_available": compartments_available,
        "pre_spawn_compartment_reconstruction": "verified_keyed_2002_replay",
        "pre_spawn_reconstruction_independent_match": True,
        "pooled_pair_2002": pooled_pair,
        "same_compartment_pair_2002": same_compartment_pair,
        "calendar_hash": history.get("calendar_hash", ""),
    }
    for year in ANNUAL_YEARS:
        metrics = _state_metrics(annual[str(year)])
        result[f"lake_allage_{year}"] = metrics["lake"]
        result[f"lake_age0_{year}"] = metrics["lake_age0"]
        result[f"lake_age1plus_{year}"] = metrics["lake_age1plus"]
    early_all = [result[f"lake_allage_{year}"] for year in SELECTED_YEARS[:5]]
    early_age0 = [result[f"lake_age0_{year}"] for year in SELECTED_YEARS[:5]]
    early_age1 = [result[f"lake_age1plus_{year}"] for year in SELECTED_YEARS[:5]]
    for metric, values in (("allage", early_all), ("age0", early_age0), ("age1plus", early_age1)):
        result[f"lake_{metric}_1976_1980_min"] = min(values)
        result[f"lake_{metric}_1976_1980_peak"] = max(values)
        result[f"lake_{metric}_1976_1980_peakyear"] = SELECTED_YEARS[:5][values.index(max(values))]
    return result


def _relative_score(exposure: np.ndarray, counts: np.ndarray, tau: float) -> float:
    positive = counts > 0
    if not positive.any():
        return 0.0
    total_counts = float(counts.sum())
    total_exposure = float(exposure.sum())
    if total_exposure <= 0:
        return -math.inf
    probabilities = exposure / total_exposure
    observed = counts / total_counts
    if np.any((probabilities <= 0) & positive):
        return -math.inf
    return float(tau * np.sum(counts[positive] * np.log(probabilities[positive] / observed[positive])))


def _lake_data(path: Path) -> np.ndarray:
    rows = []
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if str(row.get("primary_count_block", "")).lower() == "true":
                rows.append(row)
    if len(rows) != 8:
        raise ValueError(f"expected eight primary Lake digitisation rows, got {len(rows)}")
    means = np.asarray([float(row["mean_per_site_trip"]) for row in rows], dtype=float)
    if np.any(means < 0):
        raise ValueError("digitised Lake means must be nonnegative")
    return means


def _historical_scores(complete: list[dict[str, Any]], lake_data: np.ndarray) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    profiles = [
        ("base", 1 / 12, 1.0, "age0", 0.0), ("tau_quarter", 1 / 4, 1.0, "age0", 0.0),
        ("tau_full", 1.0, 1.0, "age0", 0.0), ("rho_quarter", 1 / 12, .25, "age0", 0.0),
        ("rho_four", 1 / 12, 4.0, "age0", 0.0), ("age01", 1 / 12, 1.0, "age01", 0.0),
        ("reading_low", 1 / 12, 1.0, "age0", -.08), ("reading_high", 1 / 12, 1.0, "age0", .08),
    ]
    score_rows: list[dict[str, Any]] = []
    score_lookup: list[dict[str, Any]] = []
    base_means = lake_data.copy()
    for profile_id, tau, rho, age_basis, reading_shift in profiles:
        means = base_means.copy()
        if reading_shift:
            means = np.where(means > 0, np.maximum(0.0, means + reading_shift), 0.0)
        counts = 12.0 * means
        for index, item in enumerate(complete):
            # ``lake_allage`` is already age0 + age1plus.  The age01 profile
            # therefore uses it directly; age0 uses only the recorded age-0
            # component.
            values = np.asarray(
                [item[f"lake_age0_{year}"] if age_basis == "age0" else item[f"lake_allage_{year}"]
                 for year in SELECTED_YEARS], dtype=float
            )
            early = values[:5]
            late = values[5:] * rho
            exposure = np.concatenate((early, late))
            two_score = _relative_score(np.asarray([early.sum(), late.sum()]),
                                        np.asarray([counts[:5].sum(), counts[5:].sum()]), tau)
            eight_score = _relative_score(exposure, counts, tau)
            row = {"cell_id": item["cell_id"], "namespace": item["namespace"], "source_id": item["source_id"], "replicate": item["replicate"],
                   "index_stratum": item["index_stratum"], "restriction": item["restriction"], "terminal_class": item["terminal_class"],
                   "profile_id": profile_id, "tau": tau, "rho": rho, "age_basis": age_basis, "reading_shift": reading_shift,
                   "observed_count_early": counts[:5].sum(), "observed_count_late": counts[5:].sum(),
                   "exposure_early": early.sum(), "exposure_late": late.sum(),
                   "score_two_bin_relative": two_score, "score_eight_trip_saturated_relative": eight_score}
            score_rows.append(row)
            score_lookup.append({"item_index": index, "profile_id": profile_id, "two": two_score, "eight": eight_score})
    return score_rows, score_lookup


def _weighted_composition(complete: list[dict[str, Any]], score_lookup: list[dict[str, Any]], cell_ids: list[str]) -> list[dict[str, Any]]:
    profiles = [("base", "two_bin_relative"), ("base", "eight_trip_saturated_relative"),
                ("tau_quarter", "two_bin_relative"), ("tau_quarter", "eight_trip_saturated_relative"),
                ("tau_full", "two_bin_relative"), ("tau_full", "eight_trip_saturated_relative"),
                ("rho_quarter", "two_bin_relative"), ("rho_quarter", "eight_trip_saturated_relative"),
                ("rho_four", "two_bin_relative"), ("rho_four", "eight_trip_saturated_relative"),
                ("age01", "two_bin_relative"), ("age01", "eight_trip_saturated_relative"),
                ("reading_low", "two_bin_relative"), ("reading_low", "eight_trip_saturated_relative"),
                ("reading_high", "two_bin_relative"), ("reading_high", "eight_trip_saturated_relative")]
    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for i, item in enumerate(complete):
        groups[(str(item["cell_id"]), str(item["index_stratum"]))].append(i)
    lookup = {(x["item_index"], x["profile_id"]): x for x in score_lookup}
    rows = []
    for cell_id in sorted(cell_ids):
        for stratum in ("below_one", "above_one"):
            indices = groups.get((cell_id, stratum), [])
            for profile_id, variant in profiles:
                field = "two" if variant == "two_bin_relative" else "eight"
                raw_scores = np.asarray([lookup[(i, profile_id)][field] for i in indices], dtype=float)
                finite = np.isfinite(raw_scores)
                weights = np.zeros(len(indices), dtype=float)
                if finite.any():
                    shifted = raw_scores[finite] - float(np.max(raw_scores[finite]))
                    weights[finite] = np.exp(shifted)
                    weights /= weights.sum()
                cluster_weights: dict[str, float] = defaultdict(float)
                for local, history_index in enumerate(indices):
                    cluster_weights[str(complete[history_index]["source_id"])] += float(weights[local])
                cluster_values = np.asarray(list(cluster_weights.values()), dtype=float)
                ess = float(1 / np.square(cluster_values).sum()) if cluster_values.size else 0.0
                max_weight = float(cluster_values.max()) if cluster_values.size else math.nan
                weighted = lambda field_name: float(np.sum(weights * np.asarray([complete[i][field_name] for i in indices], dtype=float))) if weights.sum() else math.nan
                rows.append({
                    "cell_id": cell_id, "index_stratum": stratum, "profile_id": profile_id, "score_variant": variant,
                    "complete_histories": len(indices), "finite_score_histories": int(finite.sum()),
                    "distinct_source_clusters": len(cluster_weights), "source_cluster_ess": ess,
                    "max_source_cluster_weight": max_weight, "weighted_persist_fraction": (float(np.sum(weights * np.asarray([complete[i]["terminal_class"] == "persist" for i in indices], dtype=float))) if weights.sum() else math.nan),
                    "weighted_loss_fraction": (float(np.sum(weights * np.asarray([complete[i]["terminal_class"] == "loss" for i in indices], dtype=float))) if weights.sum() else math.nan),
                    "weighted_total_2002": weighted("total_2002"), "weighted_lake_2002": weighted("lake_2002"),
                    "weighted_refuge_2002": weighted("refuge_2002"), "weighted_age1plus_2002": weighted("age1plus_2002"),
                    "weight_status": "weighted" if weights.sum() else ("empty" if not indices else "no_finite_score"),
                })
    return rows


def _endpoint_summary(complete: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in complete:
        grouped[(str(row["restriction"]), str(row["terminal_class"]))].append(row)
    rows = []
    for restriction in ("R_H", "R_T", "R_C", "R_J"):
        for label in ("loss", "persist"):
            part = grouped[(restriction, label)]
            lakes = np.asarray([float(row["lake_2002"]) for row in part], dtype=float)
            rows.append({"restriction": restriction, "terminal_class": label, "histories": len(part),
                         "empty_lake_2002": int(np.sum(lakes == 0)) if lakes.size else 0,
                         "empty_lake_2002_fraction": float(np.mean(lakes == 0)) if lakes.size else math.nan,
                         "persist_lake_positive": int(np.sum(lakes > 0)) if label == "persist" else "",
                         "pooled_pair_count": int(sum(bool(row["pooled_pair_2002"]) for row in part)),
                         "same_compartment_pair_count": int(sum(bool(row["same_compartment_pair_2002"]) for row in part)),
                         "median_lake_2002": float(np.median(lakes)) if lakes.size else math.nan,
                         "p95_lake_2002": float(np.percentile(lakes, 95)) if lakes.size else math.nan})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, default=ROOT / ARCHIVE_RELATIVE)
    parser.add_argument("--lake-data", type=Path, default=ROOT / LAKE_DATA_RELATIVE)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/age_lake_repair_20261002/archive_diagnostic")
    args = parser.parse_args()
    archive = args.archive_dir.resolve()
    lake_data_path = args.lake_data.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    started = datetime.now(timezone.utc).isoformat()
    manifest, used_hashes = _verify_archive(archive)
    used_hashes[str(lake_data_path.relative_to(ROOT))] = _binding(lake_data_path)
    source_rows = list(_jsonl(archive / "source_banks.jsonl", compressed=False))
    source_meta = {(str(row["cell_id"]), str(row["role"]), str(row["source_id"])): row for row in source_rows}
    compact = {_key(row): row for row in _jsonl(archive / "histories.jsonl.gz", compressed=True)}
    if len(compact) != sum(1 for _ in _jsonl(archive / "histories.jsonl.gz", compressed=True)):
        raise ValueError("duplicate compact history identity")
    labels = _event_labels()
    failure_rows = []
    failure_counts: Counter[tuple[Any, ...]] = Counter()
    complete: list[dict[str, Any]] = []
    full_count = 0
    for row in _jsonl(archive / "full_histories.jsonl.gz", compressed=True):
        full_count += 1
        identity = _key(row)
        compact_row = compact.get(identity)
        if compact_row is None:
            raise ValueError(f"full history identity absent from compact archive: {identity}")
        if row.get("status") != compact_row.get("status"):
            raise ValueError(f"full/compact status mismatch: {identity}")
        if row.get("status") == "complete":
            item = _diagnose_complete(row, bool(compact_row.get("terminal_alive")), int(compact_row["process_seed"]), source_meta)
            if abs(float(item["lake_2002"]) - float(compact_row["lake_2002"])) > 1e-9 or abs(float(item["refuge_2002"]) - float(compact_row["refuge_2002"])) > 1e-9:
                raise ValueError(f"compact/full endpoint mismatch: {identity}")
            complete.append(item)
        else:
            item = _failure_row(compact_row, labels)
            failure_counts[(item["failure_year"], item["site"], item["label"], item["failure_kind"])] += 1
            failure_rows.append(item)
    if full_count != len(compact) or len(complete) != int(manifest["history_status_counts"]["complete"]):
        raise ValueError("archive row counts do not match manifest")

    complete.sort(key=lambda row: (str(row["cell_id"]), str(row["namespace"]), str(row["source_id"]), int(row["replicate"])))
    lake_data = _lake_data(lake_data_path)
    scores, lookup = _historical_scores(complete, lake_data)
    cells = sorted({str(row["cell_id"]) for row in source_rows})
    weighted = _weighted_composition(complete, lookup, cells)
    grouping, distinct_vectors = _source_grouping(source_rows, list(compact.values()), complete, manifest)
    failure_summary = [{"failure_year": key[0], "site": key[1], "label": key[2], "failure_kind": key[3], "histories": count}
                       for key, count in sorted(failure_counts.items(), key=lambda item: tuple(str(x) for x in item[0]))]
    annual_rows = []
    for item in complete:
        for year in ANNUAL_YEARS:
            annual_rows.append({"cell_id": item["cell_id"], "namespace": item["namespace"], "source_id": item["source_id"],
                                "replicate": item["replicate"], "restriction": item["restriction"], "index_stratum": item["index_stratum"],
                                "terminal_class": item["terminal_class"], "year": year,
                                "lake_allage": item[f"lake_allage_{year}"], "lake_age0": item[f"lake_age0_{year}"],
                                "lake_age1plus": item[f"lake_age1plus_{year}"]})

    complete_fields = ["cell_id", "namespace", "source_id", "replicate", "restriction", "removal_account", "maximum_age", "nursery", "index_stratum", "refuge_index", "terminal_class", "total_2002", "lake_2002", "refuge_2002", "age1plus_2002", "pre_spawn_females_2002", "pre_spawn_males_2002", "pre_spawn_female_lake_2002", "pre_spawn_female_refuge_2002", "pre_spawn_male_lake_2002", "pre_spawn_male_refuge_2002", "pre_spawn_compartment_fields_available", "pre_spawn_compartment_reconstruction", "pre_spawn_reconstruction_independent_match", "pooled_pair_2002", "same_compartment_pair_2002", "calendar_hash"]
    for year in ANNUAL_YEARS:
        complete_fields += [f"lake_allage_{year}", f"lake_age0_{year}", f"lake_age1plus_{year}"]
    for metric in ("allage", "age0", "age1plus"):
        complete_fields += [f"lake_{metric}_1976_1980_min", f"lake_{metric}_1976_1980_peak", f"lake_{metric}_1976_1980_peakyear"]
    _write_csv(output / "complete_histories.csv", complete, complete_fields)
    _write_csv(output / "lake_annual_selected.csv", annual_rows, ["cell_id", "namespace", "source_id", "replicate", "restriction", "index_stratum", "terminal_class", "year", "lake_allage", "lake_age0", "lake_age1plus"])
    _write_csv(output / "endpoint_summary.csv", _endpoint_summary(complete), ["restriction", "terminal_class", "histories", "empty_lake_2002", "empty_lake_2002_fraction", "persist_lake_positive", "pooled_pair_count", "same_compartment_pair_count", "median_lake_2002", "p95_lake_2002"])
    _write_csv(output / "capture_failure_breakdown.csv", failure_summary, ["failure_year", "site", "label", "failure_kind", "histories"])
    _write_csv(output / "source_grouping.csv", grouping, ["role", "source_id", "bank_rows", "distinct_cells", "expected_paired_cells", "pair_count_mismatch", "history_rows_total", "complete_history_rows", "expected_history_rows", "history_row_count_mismatch", "complete_source_id_rows_are_not_independent", "biological_vector_hash"])
    _write_csv(output / "historical_lake_scores.csv", scores, ["cell_id", "namespace", "source_id", "replicate", "index_stratum", "restriction", "terminal_class", "profile_id", "tau", "rho", "age_basis", "reading_shift", "observed_count_early", "observed_count_late", "exposure_early", "exposure_late", "score_two_bin_relative", "score_eight_trip_saturated_relative"])
    _write_csv(output / "weighted_endpoint_composition.csv", weighted, ["cell_id", "index_stratum", "profile_id", "score_variant", "complete_histories", "finite_score_histories", "distinct_source_clusters", "source_cluster_ess", "max_source_cluster_weight", "weighted_persist_fraction", "weighted_loss_fraction", "weighted_total_2002", "weighted_lake_2002", "weighted_refuge_2002", "weighted_age1plus_2002", "weight_status"])

    used_hashes[SCRIPT_RELATIVE] = _binding(Path(__file__).resolve())
    used_hashes["scripts/run_age_historical_refocus.py"] = _binding(ROOT / "scripts/run_age_historical_refocus.py")
    used_hashes["src/galaxias_model/age_demography.py"] = _binding(ROOT / "src/galaxias_model/age_demography.py")
    provenance = {
        "status": "complete",
        "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "input_manifest": str((archive / "run_manifest.json").relative_to(ROOT)),
        "input_manifest_sha256": used_hashes[str((archive / "run_manifest.json").relative_to(ROOT))]["sha256"],
        "all_used_hashes": used_hashes,
        "archive_rows": {"full_rows": full_count, "compact_rows": len(compact), "complete_rows": len(complete), "failed_rows": len(failure_rows), "reconstruction_verified_rows": sum(bool(row["pre_spawn_reconstruction_independent_match"]) for row in complete)},
        "source_grouping": {"source_bank_rows": len(source_rows), "distinct_source_ids": len({(r['role'], r['source_id']) for r in source_rows}), "distinct_cell_source_rows": len({(r['role'], r['cell_id'], r['source_id']) for r in source_rows}), "distinct_biological_vectors": distinct_vectors, "pairing_key": "source_id is the shared nuisance source; cell_id,source_id is the cell-specific row; repeated cells are paired and not independent"},
        "historical_data": {"path": str(lake_data_path.relative_to(ROOT)), "count_definition": "c_i = 12 * digitised mean per site trip", "zero_handling": "zero means remain exactly zero; reading shifts apply only to positive means", "annual_years": list(ANNUAL_YEARS), "lake_score_years": list(SELECTED_YEARS)},
        "diagnostic_qualification": {
            "scope": "bounded existing archive diagnostic only; no new biological simulations",
            "interpretation": "exploratory archive diagnostics, not historical fit, posterior, causal effect, or empirical endpoint claim",
            "score_exposure_labels": "exposures and historical scores use lake trajectories only; terminal labels are applied only after scoring for endpoint composition",
            "score_variants": "two-bin relative score and eight-trip saturated-relative score are parallel diagnostics; the eight-trip score replaces aggregate two-bin evidence and is not added to it",
            "weighted_endpoint_year": 2002,
            "pre_spawn_compartments": "exactly reconstructed for every complete history from the 2002 transfer_2002_late checkpoint and keyed breeding draws; the helper result and independent kernel-style replay match exactly and both pooled sexes match the recorded summary",
            "biological_vector_definition": "source-bank fields remaining after removing IDs, role/namespace, cell design factors (restriction, nursery, maximum age, removal account, tier), timing, index labels, and source seed; hash is a grouping aid, not an independent-set claim",
            "failure_definition": "failure text is grouped by parsed year/site/event label; event labels are resolved with the hash-bound age_runner calendar, with neutral and linked-release failures retained",
        },
    }
    _write_json(output / "provenance.json", provenance)
    print(json.dumps({"output_dir": str(output), "complete_histories": len(complete), "failed_histories": len(failure_rows), "distinct_source_ids": len({(r['role'], r['source_id']) for r in source_rows}), "distinct_biological_vectors": distinct_vectors}, sort_keys=True))


if __name__ == "__main__":
    main()
