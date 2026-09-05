from __future__ import annotations

import pandas as pd
import pytest

from galaxias_model.module5_counterfactual import _attach_uncertainty_summaries
from galaxias_model.module5_output_checks import (
    check_matched_pair_ids,
    check_ordered_schema,
    check_seed_pairing,
    check_source_identity,
)
from galaxias_model.module5_proposals import PROPOSAL_SOURCE_KEY_FIELDS


SOURCE_KEY = (
    "module4_run|baseline_current|20260410|baseline_current_seed20260410|"
    "persistent_joint_cause|persistent_joint_cause:p00001"
)


def _frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for replicate_id in (0, 1):
        matched_pair_id = (
            f"{SOURCE_KEY}|m5_persistent_joint_cause_status_quo|r{replicate_id}"
        )
        rows.append(
            {
                "proposal_source_key": SOURCE_KEY,
                "module4_run_id": "module4_run",
                "variant_id": "baseline_current",
                "seed": 20260410,
                "run_dir_name": "baseline_current_seed20260410",
                "family_id": "persistent_joint_cause",
                "proposal_id": "persistent_joint_cause:p00001",
                "intervention_id": "m5_persistent_joint_cause_status_quo",
                "stochastic_replicate_id": replicate_id,
                "matched_pair_id": matched_pair_id,
                "run_id_baseline": f"{matched_pair_id}|baseline",
                "run_id_counterfactual": f"{matched_pair_id}|counterfactual",
                "baseline_stochastic_seed": 100 + replicate_id,
                "intervention_stochastic_seed": 100 + replicate_id,
            }
        )
    return pd.DataFrame(rows)


def test_ordered_schema_check_rejects_reordered_columns() -> None:
    frame = _frame()
    expected = list(frame.columns)
    reordered = frame.loc[:, [expected[1], expected[0], *expected[2:]]]

    result = check_ordered_schema(reordered, expected)

    assert not result["passed"]
    assert "same_order=False" in str(result["details"])


def test_source_identity_check_rejects_source_key_collision() -> None:
    frame = _frame()
    frame.loc[1, "stochastic_replicate_id"] = 0
    provenance = {
        "selected_proposal_source_keys": [SOURCE_KEY],
        "source_identity_fields": list(PROPOSAL_SOURCE_KEY_FIELDS),
    }

    result = check_source_identity(frame, provenance)

    assert not result["passed"]
    assert "duplicate_source_intervention_replicates=1" in str(result["details"])


def test_matched_pair_check_rejects_run_id_mismatch() -> None:
    frame = _frame()
    frame.loc[0, "run_id_counterfactual"] = "wrong"

    result = check_matched_pair_ids(frame)

    assert not result["passed"]
    assert "counterfactual_id_mismatches=1" in str(result["details"])


def test_seed_pairing_check_rejects_unmatched_seed() -> None:
    frame = _frame()
    frame.loc[0, "intervention_stochastic_seed"] = 999

    result = check_seed_pairing(frame)

    assert not result.check["passed"]
    assert result.mismatch_count == 1
    assert "seed mismatches=1" in str(result.check["details"])


def test_uncertainty_summaries_require_and_preserve_source_identity() -> None:
    rows = []
    for source_key, contrast in (("source_a", 0.0), ("source_b", 10.0)):
        row = {column: 0.0 for column in (
            "uncertainty_n_replicates", "uncertainty_extirpation_median",
            "uncertainty_extirpation_ci_low", "uncertainty_extirpation_ci_high",
            "uncertainty_persistence_2002_delta_median",
            "uncertainty_persistence_2002_ci_low", "uncertainty_persistence_2002_ci_high",
        )}
        row.update(proposal_source_key=source_key, intervention_id="same_intervention",
                   extirpation_year_contrast=contrast, persistence_2002_contrast=0.0)
        rows.append(row)
    summary = pd.DataFrame(_attach_uncertainty_summaries(rows)).set_index("proposal_source_key")
    assert summary["uncertainty_extirpation_median"].to_dict() == {"source_a": 0.0, "source_b": 10.0}
    assert (summary["uncertainty_n_replicates"] == 1).all()
    for row in rows:
        del row["proposal_source_key"]
    with pytest.raises(ValueError, match="proposal_source_key"):
        _attach_uncertainty_summaries(rows)
