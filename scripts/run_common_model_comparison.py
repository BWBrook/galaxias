#!/usr/bin/env python3
"""Run the frozen common-model search, refinement, validation and counterfactual.

The production plan is deliberately fixed by ``docs/common_model_protocol.md``.
Reduced runs require the explicit ``smoke`` mode and are labelled as such in
their manifests.  Each phase writes to a fresh directory and leaves a failed
manifest if execution stops, so a partial archive cannot be mistaken for a
completed scientific phase.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import gzip
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from galaxias_model.abundance_detection import (
    COMMON_EPISODE_FIELDS,
    OBSERVATION_MODELS,
    Q_SCENARIOS,
    common_history_log_likelihood,
    summarize_log_likelihood,
)
from galaxias_model.calibration import _load_inputs_cached, _prepare_parameter_table
from galaxias_model.common_model import (
    CONFIGURATIONS,
    RESTRICTIONS,
    intrinsic_viability,
    run_common_history,
    source_exposure_table,
)
from galaxias_model.io import _validate_resolved_constraints
from galaxias_model.sampling import inverse_transform_parameter_value, transform_parameter_value
from galaxias_model.types import Module3Config, ResolvedParameters


SCOPE = "common_model_comparison"
FAMILY = "transient_perfect_storm"
IDENTITY = ["search_seed", "configuration", "restriction", "wave", "source_index"]
PRIMARY_MODELS = ("homogeneous", "shared_quality")
DIAGNOSTIC_MODELS = ("independent_quality",)
SEARCH_SEEDS = (20260918, 20260919)
PHASE_CODES = {"search": 2101, "refine": 2203, "validate": 2309,
               "counterfactual": 2411, "paired_toggle": 2459, "parity": 2503}
EFFECT_PARAMETERS = ("PR020", "PR021", "PR027", "PR028", "PR033")
FIXED_STORAGE_PARAMETERS = ("PR035", "PR036", "PR037", "PR038")
RESTRICTION_ZEROES = {
    "R_H": ("PR020", "PR021", "PR027", "PR028"),
    "R_T": ("PR027", "PR028"),
    "R_C": ("PR020", "PR021"),
    "R_J": (),
}
PROTOCOL = ROOT / "docs" / "common_model_protocol.md"
MAX_WORKERS = 32
MAX_REPLICATES = 2048


@dataclass(frozen=True)
class RunPlan:
    mode: str
    search_sources: int
    search_replicates: int
    refine_keep_per_profile: int
    refine_replicates: int
    validate_keep_per_profile: int
    validate_replicates: int
    waves: int = 3
    global_after_first: int = 80
    local_after_first: int = 120
    local_parent_keep: int = 20

    @classmethod
    def production(cls) -> "RunPlan":
        return cls("production", 200, 64, 20, 256, 5, 1024)

    @classmethod
    def smoke(cls) -> "RunPlan":
        return cls("smoke", 3, 2, 2, 3, 1, 4, waves=2,
                   global_after_first=1, local_after_first=2, local_parent_keep=1)

    def validate(self) -> None:
        require(self.mode in {"production", "smoke"}, "mode must be production or smoke")
        fields = (self.search_sources, self.search_replicates, self.refine_keep_per_profile,
                  self.refine_replicates, self.validate_keep_per_profile,
                  self.validate_replicates, self.waves, self.local_parent_keep)
        require(all(type(value) is int and value > 0 for value in fields), "plan counts must be positive integers")
        require(self.search_replicates <= MAX_REPLICATES and self.validate_replicates <= MAX_REPLICATES,
                "replicate count exceeds seed-plan bound")
        require(self.global_after_first + self.local_after_first == self.search_sources,
                "later-wave source split must equal search_sources")
        if self.mode == "production":
            require(self == RunPlan.production(), "production mode cannot use reduced or expanded counts")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def file_hash(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": Path(path).stat().st_size, "sha256": digest.hexdigest()}


def _json_seed(parts: Sequence[Any]) -> int:
    """Stable high uint64 seed; uniqueness is checked over every planned run."""
    payload = json.dumps([SCOPE, *parts], separators=(",", ":"), ensure_ascii=True).encode()
    low_span = (1 << 63) - 1000
    return (1 << 63) + 1000 + int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % low_span


def history_seed(source_id: str, phase: str, replicate_index: int, stream: str) -> int:
    require(phase in PHASE_CODES, f"unknown phase {phase}")
    require(stream in {"demographic", "environment"}, f"unknown stream {stream}")
    require(type(replicate_index) is int and 1 <= replicate_index <= MAX_REPLICATES,
            "replicate index outside seed-plan bound")
    phase_index = list(PHASE_CODES).index(phase)
    stream_index = ("demographic", "environment").index(stream)
    payload = json.dumps([SCOPE, source_id, replicate_index], separators=(",", ":")).encode()
    low = 1000 + int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % ((1 << 59) - 1000)
    # High-bit uint64 domains are disjoint by phase and stream. Hash collisions
    # within a domain are then exhaustively checked for each complete plan.
    return (1 << 63) | (phase_index << 60) | (stream_index << 59) | low


def preflight_history_seeds(sources: pd.DataFrame, phase: str, replicates: int) -> dict[str, Any]:
    require("source_id" in sources, "source table lacks source_id")
    require(not sources.source_id.duplicated().any(), "duplicate source IDs")
    keys: list[tuple[str, int, str]] = []
    values: list[int] = []
    for source_id in sources.source_id.astype(str):
        for replicate in range(1, replicates + 1):
            for stream in ("demographic", "environment"):
                keys.append((source_id, replicate, stream))
                values.append(history_seed(source_id, phase, replicate, stream))
    require(len(values) == len(set(values)), "derived seed collision in complete phase plan")
    return {"phase": phase, "source_count": len(sources), "replicates": replicates,
            "stream_count": 2, "unique_seed_count": len(values),
            "key_count": len(keys),
            "derivation": "sha256 tuple to uint64 above 2^63+999; exhaustive collision check"}


def source_id(row: Mapping[str, Any]) -> str:
    mode = str(row.get("run_mode", "production"))
    return (f"common-{mode}|{int(row['search_seed'])}|{row['configuration']}|{row['restriction']}|"
            f"w{int(row['wave'])}|s{int(row['source_index']):04d}")


def _git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _bindings(data_dir: Path) -> dict[str, list[dict[str, Any]]]:
    sources = sorted((ROOT / "src" / "galaxias_model").glob("*.py"))
    sources += [Path(__file__), ROOT / "scripts" / "analyze_common_model_comparison.py",
                ROOT / "scripts" / "tabulate_detection_reference.py",
                ROOT / "pyproject.toml", ROOT / "uv.lock"]
    inputs = [data_dir / name for name in (
        "parameter_priors.csv", "model_family_parameter_map.csv", "parameter_constraints.csv",
        "evidence_ledger.csv", "calibration_targets.csv", "calibration_target_details.json",
        "scenario_definitions.json")]
    clarification = ROOT / "docs" / "common_model_implementation_notes.md"
    reference = ROOT / "data" / "common_model" / "constant_refuge_observation_reference.csv"
    require(PROTOCOL.exists(), "approved protocol is missing")
    require(all(path.exists() for path in sources), "one or more declared source files are missing")
    require(all(path.exists() for path in inputs), "one or more required model inputs are missing")
    def bind(paths: Iterable[Path]) -> list[dict[str, Any]]:
        return [{"path": str(path.relative_to(ROOT)), **file_hash(path)} for path in paths if path.exists()]
    freeze = ROOT / "data" / "common_model" / "protocol_freeze.json"
    require(freeze.exists() and clarification.exists() and reference.exists(),
            "protocol freeze receipt, implementation note, or analytic reference is missing")
    freeze_record = json.loads(freeze.read_text(encoding="utf-8"))
    require(freeze_record.get("status") == "frozen", "protocol freeze is not final")
    require(file_hash(PROTOCOL) == {"bytes": freeze_record.get("bytes"), "sha256": freeze_record.get("sha256")},
            "protocol no longer matches its signed freeze receipt")
    return {"source_files": bind(sources), "input_files": bind(inputs),
            "spec_documents": bind([PROTOCOL, freeze, clarification, reference])}


def verify_archive(directory: Path, *, phase: str | None = None) -> dict[str, Any]:
    directory = Path(directory)
    manifest_path = directory / "run_manifest.json"
    require(manifest_path.exists(), f"missing manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("status") == "complete" and manifest.get("scope") == SCOPE,
            f"archive is incomplete or has wrong scope: {directory}")
    if phase is not None:
        require(manifest.get("phase") == phase, f"expected {phase}, found {manifest.get('phase')}")
    for name, expected in manifest.get("outputs", {}).items():
        require(Path(name).name == name, "archive outputs must be direct filenames")
        path = directory / name
        require(path.exists() and file_hash(path) == expected, f"archive output drift: {path}")
    for group in ("source_files", "input_files", "spec_documents"):
        for binding in manifest.get(group, []):
            path = ROOT / binding["path"]
            require(path.exists() and file_hash(path) == {k: binding[k] for k in ("bytes", "sha256")},
                    f"bound file drift: {binding['path']}")
    # Input-archive paths are provenance hints and may change when an archive
    # moves between remote scratch and local artifacts. Callers verify ancestry
    # by supplying the actual archive to require_archive_input_binding().
    return manifest


def require_archive_input_binding(manifest: Mapping[str, Any], input_archive: Path) -> None:
    input_archive = Path(input_archive).resolve()
    expected = file_hash(input_archive / "run_manifest.json")
    matches = [binding for binding in manifest.get("input_archives", [])
               if binding.get("run_manifest") == expected]
    require(len(matches) == 1,
            f"archive does not bind supplied input: {input_archive}")


def require_runtime_match(*manifests: Mapping[str, Any]) -> None:
    current = {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__,
               "platform": platform.platform()}
    for manifest in manifests:
        expected = manifest.get("runtime", {})
        for key, value in current.items():
            require(expected.get(key) == value,
                    f"runtime drift for {key}: expected {expected.get(key)!r}, found {value!r}")


def _base_parameter_draws(data_dir: Path, search_seed: int, count: int, *, offset: int = 0) -> pd.DataFrame:
    inputs = _load_inputs_cached(str(data_dir.resolve()))
    config = Module3Config(families=(FAMILY,), master_seed=int(search_seed) + int(offset),
                           stage_a_draws_per_family=count, stage_a_keep_per_family=count,
                           stage_b_historical_replicates=1, workers=1, batch_size=1,
                           output_dir=Path("."))
    table = _prepare_parameter_table(inputs, FAMILY, config).copy()
    priors = inputs.parameter_priors.set_index("parameter_id")
    for proposal_index, indices in table.groupby("proposal_index", sort=True).groups.items():
        rng = np.random.default_rng(_json_seed(("effect-uniform", search_seed, offset, int(proposal_index))))
        # Draw the ordered trout pair jointly by rejection; other effects independently.
        while True:
            p20 = float(rng.uniform(0.0, float(priors.loc["PR020", "upper_bound"])))
            p21 = float(rng.uniform(0.0, float(priors.loc["PR021", "upper_bound"])))
            if p20 >= p21:
                break
        replacements = {"PR020": p20, "PR021": p21}
        for parameter in ("PR027", "PR028", "PR033"):
            replacements[parameter] = float(rng.uniform(0.0, float(priors.loc[parameter, "upper_bound"])))
        for parameter in FIXED_STORAGE_PARAMETERS:
            replacements[parameter] = float(priors.loc[parameter, "default_value"])
        for parameter, value in replacements.items():
            mask = (table.index.isin(indices)) & table.parameter_id.eq(parameter)
            table.loc[mask, "value_natural"] = value
            table.loc[mask, "value_sampling"] = value if parameter in EFFECT_PARAMETERS else np.nan
            if parameter in EFFECT_PARAMETERS:
                table.loc[mask, "sampling_transform"] = "identity"
            if parameter in FIXED_STORAGE_PARAMETERS:
                table.loc[mask, "sampled_flag"] = False
                table.loc[mask, "parameter_status"] = "unused"
    return table


def _resolved(parameter_rows: Sequence[Mapping[str, Any]], data_dir: str):
    inputs = _load_inputs_cached(str(Path(data_dir).resolve()))
    table = pd.DataFrame(parameter_rows)
    require(set(("parameter_id", "value_natural", "parameter_status")).issubset(table.columns),
            "parameter rows lack resolver fields")
    require(len(table) == 40 and not table.parameter_id.duplicated().any(),
            "common source must contain exactly 40 unique parameters")
    values = dict(zip(table.parameter_id.astype(str), table.value_natural.astype(float), strict=True))
    statuses = dict(zip(table.parameter_id.astype(str), table.parameter_status.astype(str), strict=True))
    require(all(math.isfinite(value) for value in values.values()), "parameter values must be finite")
    _validate_resolved_constraints(inputs.constraints, values, FAMILY, statuses)
    manifest = table.copy()
    manifest["effective_value"] = manifest["value_natural"]
    manifest["status"] = manifest["parameter_status"]
    manifest["active"] = ~manifest["parameter_status"].eq("unused")
    # Candidate 2 deliberately changes these search transforms and bounds.
    manifest.loc[manifest.parameter_id.isin(EFFECT_PARAMETERS), "sampling_transform"] = "identity"
    manifest.loc[manifest.parameter_id.isin(EFFECT_PARAMETERS), "declared_lower_bound"] = 0.0
    priors = inputs.parameter_priors.set_index("parameter_id")
    manifest["declared_upper_bound"] = manifest.parameter_id.map(priors.upper_bound)
    return ResolvedParameters(family_id=FAMILY, family_label="Common forcing model",
                              manifest=manifest, values=values, statuses=statuses)


def _parameter_values(table: pd.DataFrame) -> dict[str, float]:
    return dict(zip(table.parameter_id.astype(str), table.value_natural.astype(float), strict=True))


def _apply_restriction(parameters: pd.DataFrame, restriction: str) -> pd.DataFrame:
    require(restriction in RESTRICTION_ZEROES, f"unknown restriction {restriction}")
    table = parameters.copy()
    for parameter in RESTRICTION_ZEROES[restriction]:
        mask = table.parameter_id.eq(parameter)
        require(mask.sum() == 1, f"restriction parameter missing: {parameter}")
        table.loc[mask, "value_natural"] = 0.0
        table.loc[mask, "value_sampling"] = np.nan
        table.loc[mask, "sampled_flag"] = False
        table.loc[mask, "parameter_status"] = "fixed_zero"
        table.loc[mask, "sampling_transform"] = "identity"
    return table


def _local_draw(parent: pd.DataFrame, priors: pd.DataFrame, rng: np.random.Generator, scale: float,
                data_dir: Path) -> pd.DataFrame:
    inputs = _load_inputs_cached(str(data_dir.resolve()))
    base = parent.copy()
    for _ in range(1000):
        trial = base.copy()
        for index, row in trial.iterrows():
            parameter = str(row.parameter_id)
            if parameter in FIXED_STORAGE_PARAMETERS or not bool(row.sampled_flag):
                continue
            prior = priors.loc[parameter]
            lower = 0.0 if parameter in EFFECT_PARAMETERS else float(prior.lower_bound)
            upper = float(prior.upper_bound)
            transform = "identity" if parameter in EFFECT_PARAMETERS else str(prior.sampling_transform)
            low_t = transform_parameter_value(lower, transform)
            high_t = transform_parameter_value(upper, transform)
            centre = transform_parameter_value(float(row.value_natural), transform)
            for _coordinate_attempt in range(1000):
                if str(prior.distribution_family) == "discrete_uniform":
                    value = float(round(rng.normal(centre, scale * (upper - lower))))
                else:
                    value = inverse_transform_parameter_value(
                        float(rng.normal(centre, scale * (high_t - low_t))), transform)
                if lower <= value <= upper:
                    break
            else:
                raise RuntimeError(f"bounded local perturbation failed for {parameter}")
            trial.at[index, "value_natural"] = value
            trial.at[index, "value_sampling"] = value if transform == "identity" else transform_parameter_value(value, transform)
            trial.at[index, "sampling_transform"] = transform
        values = _parameter_values(trial)
        if values["PR020"] < values["PR021"]:
            continue
        try:
            _resolved(trial.to_dict("records"), str(data_dir))
        except ValueError:
            continue
        return trial
    raise RuntimeError("local perturbation failed after 1000 rejected proposals")


def _decorate_source_parameters(parameter_rows: pd.DataFrame, metadata: Mapping[str, Any]) -> pd.DataFrame:
    table = parameter_rows.copy()
    for key, value in reversed(list(metadata.items())):
        table.insert(0, key, value)
    return table


def _source_row(metadata: Mapping[str, Any], parameters: pd.DataFrame, parent_id: str | None,
                proposal_kind: str) -> dict[str, Any]:
    values = _parameter_values(parameters)
    return {**metadata, "source_id": source_id(metadata), "parent_source_id": parent_id or "",
            "proposal_kind": proposal_kind, "K_L": values["PR008"] * values["PR039"],
            "K_R": values["PR009"] * values["PR039"], "PR011": values["PR011"],
            "PR033": values["PR033"], "K_R_over_PR011": values["PR009"] * values["PR039"] / values["PR011"]}


def _viability_for_source(parameters: pd.DataFrame, data_dir: Path) -> dict[str, Any]:
    result = intrinsic_viability(_resolved(parameters.to_dict("records"), str(data_dir)))
    require("viable" in result, "intrinsic viability result lacks viable")
    output = {}
    for key, value in result.items():
        name = f"viability_{key}" if key != "viable" else "viable"
        if isinstance(value, Mapping):
            # Preserve every annual state in a stable, lossless source-level
            # cache without expanding the main source table to dozens of cols.
            output[f"{name}_json"] = json.dumps(value, sort_keys=True, separators=(",", ":"))
        else:
            require(np.isscalar(value) or value is None, f"unsupported viability diagnostic: {key}")
            output[name] = value
    return output


def _flatten_history(result: Any) -> dict[str, Any]:
    require(set(COMMON_EPISODE_FIELDS).issubset(result.observation_features),
            "common history lacks one or more observation records")
    row = {field: result.observation_features[field] for field in COMMON_EPISODE_FIELDS}
    row["removals_valid"] = bool(result.removals_valid)
    for key, value in result.early_patterns.items():
        require(np.isscalar(value), f"early pattern {key} is not scalar")
        row[f"early_{key}"] = value
    for key, value in getattr(result, "summary", {}).items():
        if np.isscalar(value) or value is None:
            row[f"endpoint_{key}"] = value
    return row


def _history_task(task: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    require(source_id(task) == task["source_id"], "task source ID disagrees with its archived identity")
    params = _resolved(task["parameter_rows"], task["data_dir"])
    rows = []
    refuge_by_year = []
    for replicate_index in range(1, int(task["replicates"]) + 1):
        seed_phase = task.get("seed_phase", task["phase"])
        demographic_seed = history_seed(task["source_id"], seed_phase, replicate_index, "demographic")
        environment_seed = history_seed(task["source_id"], seed_phase, replicate_index, "environment")
        evaluated_restriction = task.get("evaluated_restriction", task["restriction"])
        result = run_common_history(params, evaluated_restriction, task["configuration"],
                                    demographic_seed, environment_seed,
                                    overshoot_removed=bool(task.get("overshoot_removed", False)))
        row = {key: task[key] for key in (*IDENTITY, "source_id")}
        row.update(phase=task["phase"], replicate_index=replicate_index,
                   simulation_seed=demographic_seed, environment_seed=environment_seed)
        if "evaluated_restriction" in task:
            row["evaluated_restriction"] = evaluated_restriction
        row.update(_flatten_history(result))
        trajectory = result.trajectory_table
        for year in (1980, 1983):
            state = trajectory.loc[trajectory.year.eq(year)].iloc[0]
            row[f"ct005_N_L_{year}"] = float(state.N_L)
            row[f"ct005_C_L_{year}"] = float(state.C_L)
        row["ct005_cross_product_change"] = (row["ct005_C_L_1983"] * row["ct005_N_L_1980"]
                                               - row["ct005_C_L_1980"] * row["ct005_N_L_1983"])
        row.update({f"annual_N_R_{int(year)}": float(value)
                    for year, value in trajectory[["year", "N_R"]].itertuples(index=False, name=None)})
        rows.append(row)
        refuge_by_year.append(trajectory["N_R"].to_numpy(float))
    matrix = np.vstack(refuge_by_year)
    years = result.trajectory_table["year"].to_numpy(int)
    annual = []
    identity = {key: task[key] for key in (*IDENTITY, "source_id")}
    for column, year in enumerate(years):
        values = matrix[:, column]
        annual.append({**identity, "phase": task["phase"], "year": int(year),
                       "replicate_count": len(values), "N_R_mean": float(values.mean()),
                       "N_R_sd": float(values.std(ddof=1)) if len(values) > 1 else math.nan,
                       "N_R_min": float(values.min()), "N_R_q05": float(np.quantile(values, .05)),
                       "N_R_median": float(np.median(values)), "N_R_q95": float(np.quantile(values, .95)),
                       "N_R_max": float(values.max())})
    return {"histories": rows, "annual_refuge": annual}


def _source_exposure_rows(source: Mapping[str, Any], parameters: pd.DataFrame, data_dir: Path) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    params = _resolved(parameters.to_dict("records"), str(data_dir))
    table = source_exposure_table(params, source["restriction"], source["configuration"])
    identity = {key: source[key] for key in (*IDENTITY, "source_id")}
    for key, value in reversed(list(identity.items())):
        if key in table:
            require(table[key].astype(str).eq(str(value)).all(), f"exposure table identity drift: {key}")
        else:
            table.insert(0, key, value)
    descriptors = []
    post = table.loc[table.year.ge(1972)]
    for pathway in ("habitat", "trout", "climbing"):
        columns = [column for column in table if column.startswith(f"{pathway}_") and column.endswith("_mortality")]
        require(len(columns) == 4, f"exposure table lacks four {pathway} mortality paths")
        peak = float(post[columns].to_numpy(float).max())
        descriptors.append({**identity, "pathway": pathway, "peak_isolated_annual_mortality": peak,
                            "below_5_percent_all_stages_compartments_years": bool(peak < .05),
                            "year_start": 1972, "year_end": 2002})
    return table, descriptors


def _execute(tasks: Sequence[dict[str, Any]], workers: int, buffer_size: int) -> Iterable[dict[str, list[dict[str, Any]]]]:
    if workers == 1:
        return map(_history_task, tasks)
    pool = ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn"))
    mapped = pool.map(_history_task, tasks, chunksize=1, buffersize=buffer_size)
    def close_after():
        try:
            yield from mapped
        finally:
            pool.shutdown(cancel_futures=True)
    return close_after()


def _early_indicator(raw: pd.DataFrame) -> np.ndarray:
    require("early_early_patterns_pass" in raw, "history rows lack aggregate early-pattern indicator")
    values = raw["early_early_patterns_pass"]
    require(values.notna().all() and values.isin([True, False, 0, 1]).all(),
            "aggregate early-pattern indicator is not boolean")
    return values.astype(bool).to_numpy()


def _log_mean_and_se(log_values: np.ndarray) -> tuple[float, float, float, float]:
    logs = np.asarray(log_values, dtype=float)
    finite = np.isfinite(logs)
    if not finite.any():
        return -math.inf, 0.0, 0.0, 0.0
    maximum = float(logs[finite].max())
    scaled = np.zeros(len(logs), dtype=float)
    scaled[finite] = np.exp(logs[finite] - maximum)
    mean_scaled = float(scaled.mean())
    se_scaled = float(scaled.std(ddof=1) / math.sqrt(len(scaled))) if len(scaled) > 1 else math.nan
    log_mean = maximum + math.log(mean_scaled)
    factor = math.exp(maximum)
    mean = factor * mean_scaled
    se = factor * se_scaled
    return log_mean, mean, se, max(0.0, mean - 1.96 * se)


def _wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    require(0 <= successes <= trials and trials > 0, "invalid binomial counts")
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    radius = z / denominator * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials))
    return max(0.0, centre - radius), min(1.0, centre + radius)


def summarize_source(raw: pd.DataFrame, viable: bool) -> pd.DataFrame:
    early = _early_indicator(raw) if viable else np.zeros(len(raw), dtype=bool)
    early_mean = float(early.mean())
    early_se = math.sqrt(early_mean * (1 - early_mean) / len(early))
    early_lower, early_upper = _wilson_interval(int(early.sum()), len(early))
    endpoint_columns = [column for column in raw if column.startswith(("endpoint_", "annual_N_R_"))]
    endpoints = {column.removeprefix("endpoint_").removeprefix("annual_"):
                 pd.to_numeric(raw[column], errors="coerce").fillna(0).to_numpy(float)
                 for column in endpoint_columns if pd.to_numeric(raw[column], errors="coerce").notna().all()}
    for column in [name for name in endpoint_columns if name.startswith("annual_N_R_")]:
        year = column.removeprefix("annual_N_R_")
        endpoints[f"N_R_presence_{year}"] = (pd.to_numeric(raw[column], errors="raise").to_numpy(float) > 0).astype(float)
    features = raw.loc[:, COMMON_EPISODE_FIELDS]
    output = []
    for q in Q_SCENARIOS:
        for model in OBSERVATION_MODELS:
            binary_logs = common_history_log_likelihood(features, q, model)
            joint_logs = np.where(early & raw.removals_valid.astype(bool).to_numpy(), binary_logs, -math.inf)
            binary = summarize_log_likelihood(binary_logs, endpoints)
            joint = summarize_log_likelihood(joint_logs, endpoints)
            log_joint, joint_mean, joint_se, joint_lower = _log_mean_and_se(joint_logs)
            _, _, _, binary_lower = _log_mean_and_se(binary_logs)
            zero_support_upper = 1 - .05 ** (1 / len(raw)) if not np.isfinite(joint_logs).any() else math.nan
            row = {key: raw.iloc[0][key] for key in (*IDENTITY, "source_id")}
            row.update(q=q, observation_model=model, primary_profile=model in PRIMARY_MODELS,
                       viable=bool(viable), replicate_count=len(raw),
                       early_pattern_probability=early_mean,
                       early_pattern_mc_se=early_se,
                       early_pattern_lower95=early_lower,
                       early_pattern_upper95=((1 - .05 ** (1 / len(raw))) if not early.any() else early_upper),
                       early_pattern_zero_one_sided_upper95=(1 - .05 ** (1 / len(raw))
                                                             if not early.any() else math.nan),
                       log_binary_mean=binary["log_mean_compatibility"],
                       binary_mean=binary["mean_compatibility"], binary_lower95=binary_lower,
                       binary_positive_supported_count=binary["positive_supported_count"],
                       binary_mean_underflow=(math.isfinite(binary["log_mean_compatibility"])
                                              and binary["mean_compatibility"] == 0),
                       log_joint_mean=log_joint, joint_mean=joint_mean,
                       joint_positive_supported_count=joint["positive_supported_count"],
                       joint_mean_underflow=(math.isfinite(log_joint) and joint_mean == 0),
                       joint_mc_se=joint_se, joint_lower95=joint_lower,
                       joint_upper95=(zero_support_upper if math.isfinite(zero_support_upper)
                                      else min(1.0, joint_mean + 1.96 * joint_se)),
                       joint_positive_support_upper95=zero_support_upper,
                       joint_weight_ess=joint["weight_ess"],
                       joint_mc_relative_se=joint["mc_relative_se"],
                       joint_largest_weight_share=joint["largest_weight_share"],
                       joint_mc_qualified=joint["mc_qualified"])
            for key, value in joint.items():
                if key.startswith(("unconditional_", "weighted_")):
                    row[key] = value
            output.append(row)
    return pd.DataFrame(output)


def zero_source_summary(source: Mapping[str, Any]) -> pd.DataFrame:
    """Explicit zero-support rows for V failures, which consume no histories."""
    rows = []
    for q in Q_SCENARIOS:
        for model in OBSERVATION_MODELS:
            row = {key: source[key] for key in (*IDENTITY, "source_id")}
            row.update(q=q, observation_model=model, primary_profile=model in PRIMARY_MODELS,
                       viable=False, replicate_count=0, early_pattern_probability=0.0,
                       early_pattern_mc_se=math.nan, early_pattern_lower95=0.0,
                       early_pattern_upper95=math.nan, log_binary_mean=-math.inf,
                       early_pattern_zero_one_sided_upper95=math.nan,
                       binary_mean=0.0, binary_lower95=0.0,
                       binary_positive_supported_count=0, binary_mean_underflow=False,
                       log_joint_mean=-math.inf, joint_positive_supported_count=0,
                       joint_mean_underflow=False,
                       joint_mean=0.0, joint_mc_se=math.nan, joint_lower95=0.0,
                       joint_upper95=math.nan, joint_weight_ess=0.0,
                       joint_positive_support_upper95=math.nan,
                       joint_mc_relative_se=math.nan, joint_largest_weight_share=math.nan,
                       joint_mc_qualified=False)
            rows.append(row)
    return pd.DataFrame(rows)


def rank_membership(summary: pd.DataFrame, keep: int, *, wave_only: int | None = None) -> pd.DataFrame:
    frame = summary.loc[summary.primary_profile.astype(bool) & summary.viable.astype(bool)].copy()
    if wave_only is not None:
        frame = frame.loc[frame.wave.eq(wave_only)]
    retained = []
    group = ["search_seed", "configuration", "restriction", "q", "observation_model"]
    for key, part in frame.groupby(group, sort=True):
        part = part.sort_values(["log_joint_mean", "early_pattern_probability", "log_binary_mean", "source_id"],
                                ascending=[False, False, False, True])
        chosen = part.head(keep).copy()
        chosen["selection_rank"] = np.arange(1, len(chosen) + 1)
        retained.append(chosen[[*group, "selection_rank", "source_id", "wave"]])
    return pd.concat(retained, ignore_index=True) if retained else pd.DataFrame(
        columns=[*group, "selection_rank", "source_id", "wave"])


def _rank_union(summary: pd.DataFrame, keep: int, *, wave_only: int | None = None) -> pd.DataFrame:
    membership = rank_membership(summary, keep, wave_only=wave_only)
    return pd.DataFrame({"source_id": sorted(set(membership.source_id))})


def _make_tasks(sources: pd.DataFrame, parameters: pd.DataFrame, data_dir: Path,
                phase: str, replicates: int, *, overshoot_removed: bool = False) -> list[dict[str, Any]]:
    grouped = parameters.groupby("source_id", sort=False)
    tasks = []
    for row in sources.sort_values("source_id").to_dict("records"):
        require(row["source_id"] in grouped.groups, f"parameters missing for {row['source_id']}")
        tasks.append({**row, "parameter_rows": grouped.get_group(row["source_id"]).to_dict("records"),
                      "data_dir": str(data_dir.resolve()), "phase": phase,
                      "replicates": replicates, "overshoot_removed": overshoot_removed})
    return tasks


def _write_phase_histories(tasks: Sequence[dict[str, Any]], output_dir: Path, workers: int,
                           buffer_size: int, viable_lookup: Mapping[str, bool]) -> pd.DataFrame:
    summaries = []
    with (gzip.open(output_dir / "raw_histories.csv.gz", "wt", encoding="utf-8", newline="") as stream,
          gzip.open(output_dir / "annual_refuge_summary.csv.gz", "wt", encoding="utf-8", newline="") as refuge_stream):
        wrote_header = False
        wrote_refuge = False
        for completed, batch in enumerate(_execute(tasks, workers, buffer_size), start=1):
            raw = pd.DataFrame(batch["histories"])
            expected = int(tasks[completed - 1]["replicates"])
            require(len(raw) == expected and not raw.duplicated(["source_id", "replicate_index"]).any(),
                    "worker returned incomplete or duplicate histories")
            summaries.append(summarize_source(raw, bool(viable_lookup[raw.source_id.iloc[0]])))
            raw.drop(columns=[column for column in raw if column.startswith("annual_N_R_")]).to_csv(
                stream, index=False, header=not wrote_header, float_format="%.17g")
            wrote_header = True
            pd.DataFrame(batch["annual_refuge"]).to_csv(refuge_stream, index=False, header=not wrote_refuge,
                                                         float_format="%.17g")
            wrote_refuge = True
    return pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()


def empty_history_frame(*extra_columns: str) -> pd.DataFrame:
    raw_columns = [*IDENTITY, "source_id", "phase", "replicate_index", "simulation_seed",
                   "environment_seed", *COMMON_EPISODE_FIELDS, "removals_valid",
                   "early_early_patterns_pass", "early_ct005_directional_contrast",
                   "ct005_N_L_1980", "ct005_C_L_1980", "ct005_N_L_1983", "ct005_C_L_1983",
                   "ct005_cross_product_change", "endpoint_terminal_survival",
                   "endpoint_min_total_over_preflood_mean", "endpoint_extinction_time_censored"]
    return pd.DataFrame(columns=[*raw_columns, *extra_columns])


def _write_empty_history_files(output_dir: Path) -> None:
    empty_history_frame().to_csv(output_dir / "raw_histories.csv.gz", index=False, compression="gzip")
    annual_columns = [*IDENTITY, "source_id", "phase", "year", "replicate_count", "N_R_mean",
                      "N_R_sd", "N_R_min", "N_R_q05", "N_R_median", "N_R_q95", "N_R_max"]
    pd.DataFrame(columns=annual_columns).to_csv(output_dir / "annual_refuge_summary.csv.gz", index=False,
                                                compression="gzip")


def _start_archive(output_dir: Path, phase: str, plan: RunPlan, bindings: Mapping[str, Any],
                   input_archives: Sequence[Path]) -> dict[str, Any]:
    require(not output_dir.exists(), "output directory already exists")
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "running", "scope": SCOPE, "phase": phase, "mode": plan.mode,
                "plan": plan.__dict__, "started_unix": time.time(), "git_commit": _git_commit(),
                "runtime": {"python": sys.version, "numpy": np.__version__, "pandas": pd.__version__,
                            "platform": platform.platform()},
                "scientific_definitions": {
                    "boom_metric": "pedder_lake_index=N_L/(N_L+K_L)",
                    "ct005_metric": "raw latent counts via directional cross-product",
                    "minimum_dated_removals": "does not test the broader removal hypothesis",
                },
                "input_archives": [{"path": str(path.resolve()), "run_manifest": file_hash(path / "run_manifest.json")}
                                   for path in input_archives], **bindings, "outputs": {}}
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _finish_archive(output_dir: Path, manifest: dict[str, Any], **updates: Any) -> dict[str, Any]:
    manifest.update(updates)
    manifest["status"] = "complete"
    manifest["elapsed_seconds"] = round(time.time() - manifest["started_unix"], 3)
    manifest["outputs"] = {path.name: file_hash(path) for path in sorted(output_dir.iterdir())
                           if path.is_file() and path.name != "run_manifest.json"}
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _fail_archive(output_dir: Path, manifest: dict[str, Any], exc: BaseException) -> None:
    manifest.update(status="failed", failure_type=type(exc).__name__, failure_message=str(exc),
                    elapsed_seconds=round(time.time() - manifest["started_unix"], 3))
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def run_search(output_dir: Path, *, data_dir: Path = ROOT / "data", plan: RunPlan | None = None,
               workers: int = 1, buffer_size: int = 16) -> dict[str, Any]:
    plan = plan or RunPlan.production(); plan.validate()
    require(1 <= workers <= MAX_WORKERS and 1 <= buffer_size <= 256, "invalid worker settings")
    bindings = _bindings(data_dir)
    manifest = _start_archive(Path(output_dir), "search", plan, bindings, [])
    output_dir = Path(output_dir)
    try:
        all_sources: list[pd.DataFrame] = []
        all_parameters: list[pd.DataFrame] = []
        all_summaries: list[pd.DataFrame] = []
        all_exposure_descriptors: list[pd.DataFrame] = []
        viability_cache: dict[tuple[int, int, int], dict[str, Any]] = {}
        priors = _load_inputs_cached(str(data_dir.resolve())).parameter_priors.set_index("parameter_id")
        for wave in range(1, plan.waves + 1):
            wave_sources = []
            wave_parameters = []
            for search_seed in SEARCH_SEEDS:
                paired_global_groups = None
                if wave == 1:
                    paired = _base_parameter_draws(data_dir, search_seed, plan.search_sources)
                    paired_global_groups = [group.copy() for _, group in paired.groupby("proposal_index", sort=True)]
                for configuration in CONFIGURATIONS:
                    for restriction in RESTRICTIONS:
                        if wave == 1:
                            global_groups = paired_global_groups
                        else:
                            cell_offset = (wave * 10000 + 1000 * list(CONFIGURATIONS).index(configuration)
                                           + 100 * list(RESTRICTIONS).index(restriction))
                            fresh = _base_parameter_draws(data_dir, search_seed, plan.global_after_first,
                                                          offset=cell_offset)
                            global_groups = [group.copy() for _, group in fresh.groupby("proposal_index", sort=True)]
                        candidates: list[tuple[pd.DataFrame, str, str | None, str]] = [
                            (group.copy(), "global", None,
                             f"global|{search_seed}|w{wave}|{configuration if wave > 1 else 'paired'}|"
                             f"{restriction if wave > 1 else 'paired'}|d{draw_index:04d}")
                            for draw_index, group in enumerate(global_groups, start=1)]
                        if wave > 1:
                            prior_summary = pd.concat(all_summaries, ignore_index=True)
                            parent_ids = _rank_union(prior_summary, plan.local_parent_keep, wave_only=wave - 1)
                            eligible = parent_ids.merge(pd.concat(all_sources, ignore_index=True), on="source_id", how="left")
                            eligible = eligible.loc[(eligible.search_seed == search_seed) &
                                                    (eligible.configuration == configuration) &
                                                    (eligible.restriction == restriction)]
                            if len(eligible):
                                parameter_archive = pd.concat(all_parameters, ignore_index=True)
                                for local_index in range(plan.local_after_first):
                                    rng = np.random.default_rng(_json_seed(("local", search_seed, configuration,
                                                                           restriction, wave, local_index)))
                                    parent_id = str(eligible.iloc[int(rng.integers(len(eligible)))].source_id)
                                    parent = parameter_archive.loc[parameter_archive.source_id.eq(parent_id)].copy()
                                    parent = parent.drop(columns=[*IDENTITY, "source_id", "run_mode"], errors="ignore")
                                    candidates.append((_local_draw(parent, priors, rng, .20 if wave == 2 else .10, data_dir),
                                                       "local", parent_id,
                                                       f"local|{parent_id}|w{wave}|d{local_index + 1:04d}"))
                            else:
                                fallback_offset = (100000 + wave * 10000
                                                   + 1000 * list(CONFIGURATIONS).index(configuration)
                                                   + 100 * list(RESTRICTIONS).index(restriction))
                                fallback = _base_parameter_draws(data_dir, search_seed,
                                                                 plan.local_after_first,
                                                                 offset=fallback_offset)
                                candidates.extend((group.copy(), "global_no_viable_parent", None,
                                                   f"fallback|{search_seed}|{configuration}|{restriction}|w{wave}|d{draw_index:04d}")
                                                  for draw_index, (_, group) in enumerate(
                                                      fallback.groupby("proposal_index", sort=True), start=1))
                        require(len(candidates) == plan.search_sources, "wave source allocation drift")
                        for index, (raw_parameters, kind, parent_id, common_draw_id) in enumerate(candidates, start=1):
                            raw_effects = {f"raw_{key}": value for key, value in _parameter_values(raw_parameters).items()
                                           if key in EFFECT_PARAMETERS}
                            parameters = _apply_restriction(raw_parameters, restriction)
                            metadata = {"run_mode": plan.mode, "search_seed": search_seed, "configuration": configuration,
                                        "restriction": restriction, "wave": wave, "source_index": index}
                            row = _source_row(metadata, parameters, parent_id, kind)
                            row.update(common_draw_id=common_draw_id, **raw_effects)
                            # Wave-one paired draws share exact viability checks across all cells.
                            cache_key = ((search_seed, wave, index) if wave == 1 else
                                         (search_seed, wave, _json_seed((configuration, restriction, index))))
                            if cache_key not in viability_cache:
                                viability_cache[cache_key] = _viability_for_source(parameters, data_dir)
                            row.update(viability_cache[cache_key])
                            wave_sources.append(row)
                            wave_parameters.append(_decorate_source_parameters(parameters, {**metadata,
                                                                                             "source_id": row["source_id"]}))
            sources = pd.DataFrame(wave_sources)
            parameters = pd.concat(wave_parameters, ignore_index=True)
            require(not sources.source_id.duplicated().any(), "duplicate search source ID")
            if wave == 1:
                nuisance = parameters.loc[~parameters.parameter_id.isin(("PR020", "PR021", "PR027", "PR028"))]
                paired_check = nuisance.groupby(["search_seed", "source_index", "parameter_id"]).value_natural.nunique()
                require(paired_check.le(1).all(), "wave-one non-effect nuisance draws are not paired across cells")
                raw_columns = [f"raw_{parameter}" for parameter in EFFECT_PARAMETERS]
                raw_pairing = sources.groupby(["search_seed", "source_index"])[raw_columns].nunique()
                require(raw_pairing.le(1).all(axis=None), "wave-one raw effect draws are not paired across cells")
            all_sources.append(sources); all_parameters.append(parameters)
            viable_sources = sources.loc[sources.viable.astype(bool)].copy()
            preflight_history_seeds(viable_sources, "search", plan.search_replicates)
            tasks = _make_tasks(viable_sources, parameters, data_dir, "search", plan.search_replicates)
            summaries = []
            raw_path = output_dir / f"raw_histories_wave_{wave}.csv.gz"
            refuge_path = output_dir / f"annual_refuge_summary_wave_{wave}.csv.gz"
            exposure_path = output_dir / f"source_exposures_wave_{wave}.csv.gz"
            with (gzip.open(raw_path, "wt", encoding="utf-8", newline="") as stream,
                  gzip.open(refuge_path, "wt", encoding="utf-8", newline="") as refuge_stream,
                  gzip.open(exposure_path, "wt", encoding="utf-8", newline="") as exposure_stream):
                wrote = wrote_refuge = wrote_exposure = False
                for batch in _execute(tasks, workers, buffer_size):
                    raw = pd.DataFrame(batch["histories"])
                    summaries.append(summarize_source(raw, True))
                    raw.drop(columns=[column for column in raw if column.startswith("annual_N_R_")]).to_csv(
                        stream, index=False, header=not wrote, float_format="%.17g")
                    wrote = True
                    pd.DataFrame(batch["annual_refuge"]).to_csv(
                        refuge_stream, index=False, header=not wrote_refuge, float_format="%.17g")
                    wrote_refuge = True
                parameter_groups = parameters.groupby("source_id", sort=False)
                descriptors = []
                for source in sources.sort_values("source_id").to_dict("records"):
                    exposure, source_descriptors = _source_exposure_rows(
                        source, parameter_groups.get_group(source["source_id"]), data_dir)
                    exposure.to_csv(exposure_stream, index=False, header=not wrote_exposure, float_format="%.17g")
                    wrote_exposure = True
                    descriptors.extend(source_descriptors)
                all_exposure_descriptors.append(pd.DataFrame(descriptors))
            if not tasks:
                raw_path.unlink(); refuge_path.unlink()
            all_summaries.extend(summaries)
            # Viability failures still appear under every profile with zero support.
            for row in sources.loc[~sources.viable.astype(bool)].to_dict("records"):
                all_summaries.append(zero_source_summary(row))
        sources = pd.concat(all_sources, ignore_index=True)
        parameters = pd.concat(all_parameters, ignore_index=True)
        summary = pd.concat(all_summaries, ignore_index=True)
        sources.to_csv(output_dir / "sources.csv", index=False, float_format="%.17g")
        parameters.to_csv(output_dir / "parameter_values.csv.gz", index=False, compression="gzip", float_format="%.17g")
        summary.to_csv(output_dir / "source_summary.csv", index=False, float_format="%.17g")
        pd.concat(all_exposure_descriptors, ignore_index=True).to_csv(
            output_dir / "source_exposure_descriptors.csv", index=False, float_format="%.17g")
        refine_membership = rank_membership(summary, plan.refine_keep_per_profile)
        selected = pd.DataFrame({"source_id": sorted(set(refine_membership.source_id))})
        refine_membership.to_csv(output_dir / "refine_selection_membership.csv", index=False)
        selected.to_csv(output_dir / "refine_source_ids.csv", index=False)
        # Recompute immediate-wave eligibility and prove every local parent was
        # selected from the correct cell's immediately preceding top union.
        ancestry_rows = []
        eligible_by_cell: dict[tuple[int, int, str, str], pd.DataFrame] = {}
        for prior_wave in range(1, plan.waves):
            membership = rank_membership(summary, plan.local_parent_keep, wave_only=prior_wave)
            for cell, part in membership.groupby(["search_seed", "configuration", "restriction"], sort=False):
                eligible_by_cell[(prior_wave, *cell)] = part
        for child in sources.loc[sources.proposal_kind.eq("local")].to_dict("records"):
            key = (int(child["wave"]) - 1, int(child["search_seed"]),
                   child["configuration"], child["restriction"])
            eligible = eligible_by_cell.get(key, pd.DataFrame(columns=["source_id"]))
            require(child["parent_source_id"] in set(eligible.source_id),
                    f"local parent is outside immediate prior-wave top union: {child['source_id']}")
            ancestry_rows.append({"child_source_id": child["source_id"],
                                  "parent_source_id": child["parent_source_id"],
                                  "child_wave": child["wave"],
                                  "eligible_profile_memberships": int(eligible.source_id.eq(child["parent_source_id"]).sum())})
        pd.DataFrame(ancestry_rows, columns=["child_source_id", "parent_source_id", "child_wave",
                                             "eligible_profile_memberships"]).to_csv(
                                                 output_dir / "local_parent_ancestry.csv", index=False)
        expected_max = len(CONFIGURATIONS) * len(RESTRICTIONS) * len(SEARCH_SEEDS) * 8 * plan.refine_keep_per_profile
        require(len(selected) <= expected_max, "refinement source union exceeds protocol cap")
        executed = int(sources.viable.astype(bool).sum()) * plan.search_replicates
        complete_seed_preflight = preflight_history_seeds(
            sources.loc[sources.viable.astype(bool)], "search", plan.search_replicates)
        return _finish_archive(output_dir, manifest, source_count=len(sources), viable_source_count=int(sources.viable.sum()),
                               history_count=executed, refinement_source_count=len(selected),
                               seed_preflight=complete_seed_preflight,
                               seed_policy="separate phase/source/replicate demographic and environmental streams")
    except BaseException as exc:
        _fail_archive(output_dir, manifest, exc); raise


def _load_source_archive(directory: Path, phase: str) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    manifest = verify_archive(directory, phase=phase)
    sources = pd.read_csv(directory / "sources.csv", float_precision="round_trip")
    parameters = pd.read_csv(directory / "parameter_values.csv.gz", float_precision="round_trip")
    summary = pd.read_csv(directory / "source_summary.csv", float_precision="round_trip")
    require(not sources.source_id.duplicated().any(), "source archive has duplicate identities")
    require(all(source_id(row) == row["source_id"] for row in sources.to_dict("records")),
            "source archive contains an identity/ID mismatch")
    require(not parameters.duplicated(["source_id", "parameter_id"]).any(), "parameter archive has duplicates")
    return manifest, sources, parameters, summary


def verify_reused_validation_seeds(validate_dir: Path, sources: pd.DataFrame, replicates: int) -> dict[str, Any]:
    """Bind reused seed pairs to the actual frozen validation rows."""
    wanted = set(sources.source_id.astype(str))
    seen: set[tuple[str, int]] = set()
    path = Path(validate_dir) / "raw_histories.csv.gz"
    for chunk in pd.read_csv(path, usecols=["source_id", "replicate_index", "simulation_seed", "environment_seed"],
                             chunksize=100_000):
        chunk = chunk.loc[chunk.source_id.astype(str).isin(wanted) & chunk.replicate_index.le(replicates)]
        for row in chunk.itertuples(index=False):
            key = (str(row.source_id), int(row.replicate_index))
            require(key not in seen, "duplicate frozen validation seed key")
            require(int(row.simulation_seed) == history_seed(key[0], "validate", key[1], "demographic"),
                    "frozen demographic seed disagrees with derivation")
            require(int(row.environment_seed) == history_seed(key[0], "validate", key[1], "environment"),
                    "frozen environmental seed disagrees with derivation")
            seen.add(key)
    require(len(seen) == len(wanted) * replicates, "frozen validation seeds do not cover paired diagnostic")
    return {"source_count": len(wanted), "replicates": replicates, "verified_seed_pairs": len(seen),
            "validation_raw_histories": file_hash(path)}


def run_selected_phase(search_dir: Path, output_dir: Path, phase: str, *,
                       input_phase_dir: Path | None = None, data_dir: Path = ROOT / "data",
                       plan: RunPlan | None = None, workers: int = 1, buffer_size: int = 16) -> dict[str, Any]:
    require(phase in {"refine", "validate"}, "selected phase must be refine or validate")
    plan = plan or RunPlan.production(); plan.validate()
    search_manifest, search_sources, search_parameters, search_summary = _load_source_archive(Path(search_dir), "search")
    require_runtime_match(search_manifest)
    if phase == "refine":
        selected = pd.read_csv(Path(search_dir) / "refine_source_ids.csv")
        replicates = plan.refine_replicates
        inputs = [Path(search_dir)]
    else:
        require(input_phase_dir is not None, "validate requires the completed refinement archive")
        refine_manifest = verify_archive(Path(input_phase_dir), phase="refine")
        require_runtime_match(refine_manifest)
        require_archive_input_binding(refine_manifest, Path(search_dir))
        selected = pd.read_csv(Path(input_phase_dir) / "validate_source_ids.csv")
        replicates = plan.validate_replicates
        inputs = [Path(search_dir), Path(input_phase_dir)]
    sources = selected.merge(search_sources, on="source_id", how="left", validate="one_to_one")
    require(sources.viable.fillna(False).astype(bool).all(), "selected list contains unknown or viability-failing source")
    parameters = search_parameters.loc[search_parameters.source_id.isin(sources.source_id)].copy()
    preflight = preflight_history_seeds(sources, phase, replicates)
    manifest = _start_archive(Path(output_dir), phase, plan, _bindings(data_dir), inputs)
    output_dir = Path(output_dir)
    try:
        sources.to_csv(output_dir / "sources.csv", index=False, float_format="%.17g")
        parameters.to_csv(output_dir / "parameter_values.csv.gz", index=False, compression="gzip", float_format="%.17g")
        if sources.empty:
            search_summary.iloc[0:0].to_csv(output_dir / "source_summary.csv", index=False)
            _write_empty_history_files(output_dir)
            if phase == "refine":
                rank_membership(search_summary.iloc[0:0], plan.validate_keep_per_profile).to_csv(
                    output_dir / "validate_selection_membership.csv", index=False)
                pd.DataFrame(columns=["source_id"]).to_csv(output_dir / "validate_source_ids.csv", index=False)
            return _finish_archive(output_dir, manifest, source_count=0, history_count=0,
                                   next_phase_source_count=0 if phase == "refine" else None,
                                   seed_preflight={"source_count": 0, "replicates": replicates,
                                                   "unique_seed_count": 0},
                                   validation_reselection=False,
                                   scientific_status="complete_no_viable_or_retained_candidates")
        tasks = _make_tasks(sources, parameters, data_dir, phase, replicates)
        summary = _write_phase_histories(tasks, output_dir, workers, buffer_size,
                                         dict(zip(sources.source_id, sources.viable)))
        summary.to_csv(output_dir / "source_summary.csv", index=False, float_format="%.17g")
        if phase == "refine":
            validate_membership = rank_membership(summary, plan.validate_keep_per_profile)
            selected_validate = pd.DataFrame({"source_id": sorted(set(validate_membership.source_id))})
            validate_membership.to_csv(output_dir / "validate_selection_membership.csv", index=False)
            selected_validate.to_csv(output_dir / "validate_source_ids.csv", index=False)
            expected_max = len(CONFIGURATIONS) * len(RESTRICTIONS) * len(SEARCH_SEEDS) * 8 * plan.validate_keep_per_profile
            require(len(selected_validate) <= expected_max, "validation source union exceeds protocol cap")
            selection_count = len(selected_validate)
        else:
            selection_count = None
        return _finish_archive(output_dir, manifest, source_count=len(sources), history_count=len(sources) * replicates,
                               next_phase_source_count=selection_count, seed_preflight=preflight,
                               validation_reselection=False)
    except BaseException as exc:
        _fail_archive(output_dir, manifest, exc); raise


def run_counterfactual(search_dir: Path, validate_dir: Path, output_dir: Path, *,
                       data_dir: Path = ROOT / "data", plan: RunPlan | None = None,
                       workers: int = 1, buffer_size: int = 16) -> dict[str, Any]:
    plan = plan or RunPlan.production(); plan.validate()
    search_manifest, search_sources, search_parameters, _ = _load_source_archive(Path(search_dir), "search")
    validate_manifest = verify_archive(Path(validate_dir), phase="validate")
    require_runtime_match(search_manifest, validate_manifest)
    validate_sources = pd.read_csv(Path(validate_dir) / "sources.csv")
    sources = validate_sources.loc[validate_sources.restriction.eq("R_J")].copy()
    require(len(sources) <= len(CONFIGURATIONS) * len(SEARCH_SEEDS) * 8 * plan.validate_keep_per_profile,
            "R_J counterfactual source cap exceeded")
    require(int(validate_manifest["plan"]["validate_replicates"]) == plan.validate_replicates,
            "counterfactual plan differs from validation")
    parameters = search_parameters.loc[search_parameters.source_id.isin(sources.source_id)].copy()
    seed_preflight = preflight_history_seeds(sources, "validate", plan.validate_replicates)
    seed_binding = verify_reused_validation_seeds(Path(validate_dir), sources, plan.validate_replicates)
    # Paired streams intentionally reuse validation seeds; counterfactual phase
    # code is retained only as archive identity and is not used for its histories.
    tasks = _make_tasks(sources, parameters, data_dir, "validate", plan.validate_replicates,
                        overshoot_removed=True)
    for task in tasks:
        task["phase"] = "counterfactual"
        task["seed_phase"] = "validate"
    manifest = _start_archive(Path(output_dir), "counterfactual", plan, _bindings(data_dir),
                              [Path(search_dir), Path(validate_dir)])
    output_dir = Path(output_dir)
    try:
        sources.to_csv(output_dir / "sources.csv", index=False, float_format="%.17g")
        parameters.to_csv(output_dir / "parameter_values.csv.gz", index=False, compression="gzip", float_format="%.17g")
        if sources.empty:
            empty_history_frame().to_csv(output_dir / "counterfactual_histories.csv.gz", index=False,
                                         compression="gzip")
            return _finish_archive(output_dir, manifest, source_count=0, history_count=0,
                                   weighting="factual validation observation weights; no counterfactual reweighting",
                                   paired_seed_phase="validate", seed_preflight=seed_preflight,
                                   factual_seed_binding=seed_binding,
                                   scientific_status="complete_no_final_R_J_sources")
        with gzip.open(output_dir / "counterfactual_histories.csv.gz", "wt", encoding="utf-8", newline="") as stream:
            wrote = False; count = 0
            for batch in _execute(tasks, workers, buffer_size):
                raw = pd.DataFrame(batch["histories"])
                raw.to_csv(stream, index=False, header=not wrote, float_format="%.17g")
                wrote = True; count += len(raw)
        require(count == len(sources) * plan.validate_replicates, "counterfactual history count drift")
        return _finish_archive(output_dir, manifest, source_count=len(sources), history_count=count,
                               weighting="factual validation observation weights; no counterfactual reweighting",
                               paired_seed_phase="validate", seed_preflight=seed_preflight,
                               factual_seed_binding=seed_binding)
    except BaseException as exc:
        _fail_archive(output_dir, manifest, exc); raise


def run_paired_toggles(search_dir: Path, validate_dir: Path, output_dir: Path, *,
                       data_dir: Path = ROOT / "data", plan: RunPlan | None = None,
                       workers: int = 1, buffer_size: int = 16) -> dict[str, Any]:
    """Evaluate R_H/R_T/R_C at every final R_J source using 64 paired streams.

    This fixed-parameter diagnostic is separate from the independently refitted
    compatibility map. With at most 64 histories it cannot satisfy the primary
    ESS>=100 rule and is never admitted as a compatibility witness.
    """
    plan = plan or RunPlan.production(); plan.validate()
    search_manifest, _, search_parameters, _ = _load_source_archive(Path(search_dir), "search")
    validate_manifest = verify_archive(Path(validate_dir), phase="validate")
    require_runtime_match(search_manifest, validate_manifest)
    validate_sources = pd.read_csv(Path(validate_dir) / "sources.csv")
    factual_sources = validate_sources.loc[validate_sources.restriction.eq("R_J")].copy()
    replicates = min(64, plan.validate_replicates)
    require(int(validate_manifest["plan"]["validate_replicates"]) == plan.validate_replicates,
            "paired-toggle plan differs from validation")
    parameters = search_parameters.loc[search_parameters.source_id.isin(factual_sources.source_id)].copy()
    tasks = []
    grouped = parameters.groupby("source_id", sort=False)
    for factual in factual_sources.sort_values("source_id").to_dict("records"):
        for toggle in ("R_H", "R_T", "R_C"):
            task = {**factual, "factual_source_id": factual["source_id"],
                    "factual_restriction": "R_J", "evaluated_restriction": toggle,
                    "parameter_rows": grouped.get_group(factual["source_id"]).to_dict("records"),
                    "data_dir": str(data_dir.resolve()), "phase": "paired_toggle",
                    "seed_phase": "validate", "replicates": replicates,
                    "overshoot_removed": False}
            tasks.append(task)
    manifest = _start_archive(Path(output_dir), "paired_toggle", plan, _bindings(data_dir),
                              [Path(search_dir), Path(validate_dir)])
    output_dir = Path(output_dir)
    try:
        seed_preflight = preflight_history_seeds(factual_sources, "validate", replicates)
        seed_binding = verify_reused_validation_seeds(Path(validate_dir), factual_sources, replicates)
        factual_sources.to_csv(output_dir / "factual_R_J_sources.csv", index=False, float_format="%.17g")
        parameters.to_csv(output_dir / "parameter_values.csv.gz", index=False, compression="gzip", float_format="%.17g")
        if factual_sources.empty:
            empty_history_frame("factual_source_id", "factual_restriction", "evaluated_restriction").to_csv(
                output_dir / "paired_toggle_histories.csv.gz", index=False, compression="gzip")
            return _finish_archive(output_dir, manifest, factual_source_count=0,
                                   evaluated_restrictions=["R_H", "R_T", "R_C"],
                                   replicates_per_toggle=replicates, history_count=0,
                                   paired_seed_phase="validate", seed_preflight=seed_preflight,
                                   factual_seed_binding=seed_binding,
                                   interpretation="fixed-R_J-parameter diagnostic; excluded from compatibility witness map",
                                   scientific_status="complete_no_final_R_J_sources")
        count = 0
        with gzip.open(output_dir / "paired_toggle_histories.csv.gz", "wt", encoding="utf-8", newline="") as stream:
            wrote = False
            for task, batch in zip(tasks, _execute(tasks, workers, buffer_size), strict=True):
                raw = pd.DataFrame(batch["histories"])
                raw["factual_source_id"] = task["factual_source_id"]
                raw["factual_restriction"] = "R_J"
                raw["evaluated_restriction"] = task["evaluated_restriction"]
                raw.to_csv(stream, index=False, header=not wrote, float_format="%.17g")
                wrote = True; count += len(raw)
        expected = len(factual_sources) * 3 * replicates
        require(count == expected, "paired-toggle history count drift")
        return _finish_archive(output_dir, manifest, factual_source_count=len(factual_sources),
                               evaluated_restrictions=["R_H", "R_T", "R_C"],
                               replicates_per_toggle=replicates, history_count=count,
                               paired_seed_phase="validate",
                               seed_preflight=seed_preflight, factual_seed_binding=seed_binding,
                               interpretation="fixed-R_J-parameter diagnostic; excluded from compatibility witness map")
    except BaseException as exc:
        _fail_archive(output_dir, manifest, exc); raise


def serial_parallel_check(task: Mapping[str, Any], *, workers: int = 2) -> pd.DataFrame:
    """Run one identical source task serially and under spawn, requiring exact rows."""
    require(workers >= 2, "parallel check needs at least two workers")
    serial = pd.DataFrame(_history_task(task)["histories"]).sort_values("replicate_index").reset_index(drop=True)
    parallel_batches = list(_execute([dict(task)], workers, 2))
    require(len(parallel_batches) == 1, "parallel check returned wrong task count")
    parallel = pd.DataFrame(parallel_batches[0]["histories"]).sort_values("replicate_index").reset_index(drop=True)
    pd.testing.assert_frame_equal(serial, parallel, check_exact=True)
    return serial


def run_parity_matrix(output_dir: Path, *, data_dir: Path = ROOT / "data", workers: int = 2) -> dict[str, Any]:
    """Exact target-host check over all 24 cells, two histories per cell.

    The single nuisance draw is prespecified by the protocol search seed and is
    never selected using model output. These 48 histories are preflight only.
    """
    require(workers >= 2, "parity matrix needs at least two parallel workers")
    plan = RunPlan.smoke()
    manifest = _start_archive(Path(output_dir), "parity", plan, _bindings(data_dir), [])
    output_dir = Path(output_dir)
    try:
        draw = next(iter(_base_parameter_draws(data_dir, SEARCH_SEEDS[0], 1).groupby("proposal_index")))[1]
        tasks = []
        for configuration in CONFIGURATIONS:
            for restriction in RESTRICTIONS:
                metadata = {"run_mode": "parity", "search_seed": SEARCH_SEEDS[0], "configuration": configuration,
                            "restriction": restriction, "wave": 0, "source_index": 1}
                sid = source_id(metadata)
                effective = _apply_restriction(draw, restriction)
                tasks.append({**metadata, "source_id": sid, "parameter_rows": effective.to_dict("records"),
                              "data_dir": str(data_dir.resolve()), "phase": "parity", "replicates": 2,
                              "overshoot_removed": False})
        preflight = preflight_history_seeds(pd.DataFrame([{"source_id": task["source_id"]} for task in tasks]),
                                            "parity", 2)
        serial = pd.concat([pd.DataFrame(batch["histories"]) for batch in _execute(tasks, 1, 2)], ignore_index=True)
        parallel = pd.concat([pd.DataFrame(batch["histories"]) for batch in _execute(tasks, workers, 2)], ignore_index=True)
        order = ["configuration", "restriction", "replicate_index"]
        serial = serial.sort_values(order).reset_index(drop=True)
        parallel = parallel.sort_values(order).reset_index(drop=True)
        pd.testing.assert_frame_equal(serial, parallel, check_exact=True)
        serial.to_csv(output_dir / "parity_histories.csv", index=False, float_format="%.17g")
        comparison = {"cells": len(CONFIGURATIONS) * len(RESTRICTIONS),
                      "distinct_histories": len(serial), "histories_executed": 2 * len(serial),
                      "serial_workers": 1, "parallel_workers": workers,
                      "exact_row_and_float_equality": True, "minimum_seed": int(serial.simulation_seed.min()),
                      "maximum_seed": int(serial.environment_seed.max()), "seed_preflight": preflight}
        (output_dir / "parity_result.json").write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
        return _finish_archive(output_dir, manifest, **comparison)
    except BaseException as exc:
        _fail_archive(output_dir, manifest, exc); raise


def production_budget() -> dict[str, int]:
    plan = RunPlan.production()
    search = len(CONFIGURATIONS) * len(RESTRICTIONS) * len(SEARCH_SEEDS) * plan.waves * plan.search_sources * plan.search_replicates
    refine = len(CONFIGURATIONS) * len(RESTRICTIONS) * len(SEARCH_SEEDS) * 8 * plan.refine_keep_per_profile * plan.refine_replicates
    validate = len(CONFIGURATIONS) * len(RESTRICTIONS) * len(SEARCH_SEEDS) * 8 * plan.validate_keep_per_profile * plan.validate_replicates
    counter = len(CONFIGURATIONS) * len(SEARCH_SEEDS) * 8 * plan.validate_keep_per_profile * plan.validate_replicates
    toggles = len(CONFIGURATIONS) * len(SEARCH_SEEDS) * 8 * plan.validate_keep_per_profile * 3 * 64
    total = 712000 + search + refine + validate + counter + toggles
    require(total == 7_071_040 and total <= 7_100_000, "production budget no longer matches approved envelope")
    return {"archived_replay": 712000, "search": search, "refine_max": refine,
            "validate_max": validate, "counterfactual_max": counter, "total_max": total,
            "paired_toggle_max": toggles, "hard_ceiling": 7_100_000,
            "remaining_for_prescribed_checks": 7_100_000 - total}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("search", "refine", "validate", "counterfactual", "paired_toggle", "parity", "budget"), required=True)
    parser.add_argument("--mode", choices=("production", "smoke"), required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--search-dir", type=Path)
    parser.add_argument("--refine-dir", type=Path)
    parser.add_argument("--validate-dir", type=Path)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--buffer-size", type=int, default=16)
    args = parser.parse_args()
    plan = RunPlan.production() if args.mode == "production" else RunPlan.smoke()
    if args.phase == "budget":
        print(json.dumps(production_budget(), indent=2))
    elif args.phase == "parity":
        require(args.output_dir is not None, "parity needs --output-dir")
        run_parity_matrix(args.output_dir, data_dir=args.data_dir, workers=max(2, args.workers))
    elif args.phase == "search":
        require(args.output_dir is not None, "search needs --output-dir")
        run_search(args.output_dir, data_dir=args.data_dir, plan=plan, workers=args.workers, buffer_size=args.buffer_size)
    elif args.phase in {"refine", "validate"}:
        require(args.search_dir is not None and args.output_dir is not None, "phase needs --search-dir and --output-dir")
        run_selected_phase(args.search_dir, args.output_dir, args.phase, input_phase_dir=args.refine_dir,
                           data_dir=args.data_dir, plan=plan, workers=args.workers, buffer_size=args.buffer_size)
    elif args.phase == "counterfactual":
        require(args.search_dir is not None and args.validate_dir is not None and args.output_dir is not None,
                "counterfactual needs --search-dir, --validate-dir and --output-dir")
        run_counterfactual(args.search_dir, args.validate_dir, args.output_dir, data_dir=args.data_dir,
                           plan=plan, workers=args.workers, buffer_size=args.buffer_size)
    else:
        require(args.search_dir is not None and args.validate_dir is not None and args.output_dir is not None,
                "paired_toggle needs --search-dir, --validate-dir and --output-dir")
        run_paired_toggles(args.search_dir, args.validate_dir, args.output_dir, data_dir=args.data_dir,
                           plan=plan, workers=args.workers, buffer_size=args.buffer_size)
