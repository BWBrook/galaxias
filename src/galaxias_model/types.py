from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ModelInputs:
    data_dir: Path
    parameter_priors: pd.DataFrame
    family_map: pd.DataFrame
    constraints: pd.DataFrame
    calibration_targets: pd.DataFrame | None = None
    calibration_target_details: dict[str, dict[str, Any]] | None = None
    scenario_definitions: dict[str, "ScenarioDefinition"] | None = None


@dataclass(frozen=True)
class ResolvedParameters:
    family_id: str
    family_label: str
    manifest: pd.DataFrame
    values: dict[str, float]
    statuses: dict[str, str]

    def value(self, parameter_id: str) -> float:
        return self.values[parameter_id]

    def status(self, parameter_id: str) -> str:
        return self.statuses[parameter_id]

    @property
    def trout_active(self) -> bool:
        trout_ids = {"PR012", "PR013", "PR014", "PR015", "PR016", "PR017", "PR018", "PR019"}
        return any(self.status(pid) != "unused" for pid in trout_ids) or any(
            self.value(pid) > 0 for pid in ("PR020", "PR021")
        )

    @property
    def climbing_active(self) -> bool:
        climbing_ids = {"PR022", "PR023", "PR024", "PR025", "PR026"}
        return any(self.status(pid) != "unused" for pid in climbing_ids) or any(
            self.value(pid) > 0 for pid in ("PR027", "PR028")
        )

    def as_jsonable(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "family_label": self.family_label,
            "parameters": self.manifest.to_dict(orient="records"),
        }


@dataclass(frozen=True)
class ForcingSchedule:
    years: list[int]
    table: pd.DataFrame


@dataclass(frozen=True)
class FounderEvent:
    year: int
    adult_lake_addition: float


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    start_year: int
    end_year: int
    initialization_mode: str
    forcing_mode: str
    founder_events: tuple[FounderEvent, ...] = ()
    spawn_habitat_by_year: dict[int, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulationConfig:
    start_year: int = 1965
    end_year: int = 2002
    burn_in_years: int = 100
    stochastic: bool = True
    scenario_id: str = "historical_lake"
    record_forcing: bool = True
    scenario_definition: ScenarioDefinition | None = None


@dataclass
class SimulationResult:
    scenario_id: str
    trajectory_table: pd.DataFrame
    resolved_parameters: ResolvedParameters
    forcing_table: pd.DataFrame
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScoringConfig:
    include_historical_core: bool = True
    include_intrinsic_baseline: bool = True
    require_all_targets: bool = True
    replicate_aggregation: str = "median"


@dataclass(frozen=True)
class ProjectionResult:
    projection_table: pd.DataFrame


@dataclass(frozen=True)
class ScoringResult:
    projection_table: pd.DataFrame
    target_score_table: pd.DataFrame
    summary: dict[str, Any]


@dataclass(frozen=True)
class AggregateScoringResult:
    replicate_score_table: pd.DataFrame
    aggregate_target_score_table: pd.DataFrame
    summary: dict[str, Any]


@dataclass(frozen=True)
class ScenarioBundleResult:
    scenario_results: dict[str, ScoringResult]
    bundle_target_score_table: pd.DataFrame
    summary: dict[str, Any]


@dataclass(frozen=True)
class AggregateScenarioBundleResult:
    replicate_bundle_score_table: pd.DataFrame
    aggregate_target_score_table: pd.DataFrame
    summary: dict[str, Any]


def _default_module3_output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    return Path("outputs") / "module3" / stamp


@dataclass(frozen=True)
class Module3Config:
    families: tuple[str, ...] = (
        "habitat_only_null",
        "trout_only",
        "climbing_only",
        "persistent_joint_cause",
        "transient_perfect_storm",
    )
    stage_a_draws_per_family: int = 2000
    stage_a_keep_per_family: int = 100
    stage_b_historical_replicates: int = 20
    final_acceptance_fraction: float = 0.10
    final_acceptance_cap: int = 50
    workers: int = 1
    batch_size: int = 100
    master_seed: int = 20260410
    stochastic_baselines: bool = False
    output_dir: Path = field(default_factory=_default_module3_output_dir)
    resume: bool = False

    @classmethod
    def readiness_defaults(cls, output_dir: Path | None = None) -> "Module3Config":
        return cls(
            stage_a_draws_per_family=250,
            stage_a_keep_per_family=20,
            stage_b_historical_replicates=5,
            final_acceptance_fraction=0.10,
            final_acceptance_cap=10,
            workers=1,
            output_dir=output_dir if output_dir is not None else cls().output_dir,
            resume=False,
        )


@dataclass(frozen=True)
class ProposalResult:
    summary_row: dict[str, Any]
    parameter_values_table: pd.DataFrame
    target_scores_table: pd.DataFrame


@dataclass(frozen=True)
class FamilyCalibrationResult:
    family_id: str
    proposal_summary_table: pd.DataFrame
    parameter_values_table: pd.DataFrame
    target_scores_table: pd.DataFrame
    retained_proposal_ids: tuple[str, ...] = ()
    accepted_proposal_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CalibrationRunResult:
    config: Module3Config
    proposal_summary_table: pd.DataFrame
    parameter_values_table: pd.DataFrame
    target_scores_table: pd.DataFrame
    family_summary_table: pd.DataFrame
    accepted_proposals_table: pd.DataFrame
    run_manifest: dict[str, Any]
    family_results: dict[str, FamilyCalibrationResult]
