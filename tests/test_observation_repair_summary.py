"""Regression for cancellation at constant Monte Carlo compatibility weights."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def test_constant_compatibility_has_zero_monte_carlo_variance():
    spec = importlib.util.spec_from_file_location(
        "repair_summary", Path(__file__).resolve().parents[1] / "scripts/summarize_observation_repair_pilot.py"
    )
    summary = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(summary)
    histories = pd.DataFrame({
        "positive_records_compatible": [True] * 20,
        "nondetection_occupied_episodes": [7] * 20,
        **{field: [1.0] * 20 for field in summary.PHYSICS},
    })
    for p in (0.0, 0.60, 0.98):
        result = summary.conditioned_physics(histories, p)
        assert result["mc_relative_se"] == 0.0
        assert result["weight_ess"] == 20.0
        assert result["largest_weight_share"] == pytest.approx(0.05)
