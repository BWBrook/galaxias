from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from galaxias_model.module5_counterfactual import run_module5_counterfactual_smoke
from galaxias_model.module5_smoke_inspect import inspect_module5_counterfactual_smoke


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTCOME_SCHEMA = DATA_DIR / "module5_counterfactual_outcome_schema.csv"


def _write_smoke_output(output_dir: Path) -> None:
    run_module5_counterfactual_smoke(
        data_dir=DATA_DIR,
        interventions_path=DATA_DIR / "module5_counterfactual_interventions.csv",
        outcome_schema_path=OUTCOME_SCHEMA,
        output_dir=output_dir,
        intervention_ids=("m5_persistent_joint_cause_no_trout_pressure",),
        replicates=2,
        proposal_seed=20260605,
        stochastic=True,
    )


def test_inspect_module5_smoke_writes_review_bundle_from_disk(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "module5_runner_smoke"
    _write_smoke_output(smoke_dir)

    result = inspect_module5_counterfactual_smoke(
        smoke_dir=smoke_dir,
        outcome_schema_path=OUTCOME_SCHEMA,
    )

    assert result.all_checks_passed
    assert result.inspection_dir == smoke_dir / "inspection"
    assert result.summary_path.exists()
    assert result.checks_path.exists()
    assert result.report_path.exists()

    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert summary["all_checks_passed"] is True
    assert summary["row_count"] == 2
    assert summary["smoke_only_boundary"] is True

    checks = pd.read_csv(result.checks_path)
    assert set(checks["check_name"]) == {
        "schema_columns",
        "matched_pair_ids",
        "common_random_seed_pairing",
        "provenance_labels",
        "smoke_only_boundary",
    }
    assert checks["passed"].all()
    assert "not production attribution" in result.report_path.read_text(encoding="utf-8")


def test_inspect_module5_smoke_detects_broken_seed_pairing(tmp_path: Path) -> None:
    smoke_dir = tmp_path / "module5_runner_smoke"
    _write_smoke_output(smoke_dir)
    outcomes_path = smoke_dir / "matched_outcomes.csv"
    frame = pd.read_csv(outcomes_path)
    frame.loc[0, "intervention_stochastic_seed"] = frame.loc[0, "baseline_stochastic_seed"] + 100
    frame.to_csv(outcomes_path, index=False)

    result = inspect_module5_counterfactual_smoke(
        smoke_dir=smoke_dir,
        outcome_schema_path=OUTCOME_SCHEMA,
    )

    assert not result.all_checks_passed
    checks = pd.read_csv(result.checks_path).set_index("check_name")
    assert not bool(checks.loc["common_random_seed_pairing", "passed"])
    assert "seed mismatches=1" in checks.loc["common_random_seed_pairing", "details"]
