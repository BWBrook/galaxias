from __future__ import annotations

from dataclasses import dataclass, field
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
class SimulationConfig:
    start_year: int = 1965
    end_year: int = 2002
    burn_in_years: int = 100
    stochastic: bool = True
    scenario_id: str = "historical_lake"
    record_forcing: bool = True


@dataclass
class SimulationResult:
    trajectory_table: pd.DataFrame
    resolved_parameters: ResolvedParameters
    forcing_table: pd.DataFrame
    summary: dict[str, Any] = field(default_factory=dict)
