from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from galaxias_model.module5_proposals import (
    PROPOSAL_SOURCE_KEY_FIELDS,
    build_proposal_source_key,
)


@dataclass(frozen=True)
class SeedPairingResult:
    check: dict[str, object]
    mismatch_count: int | None


def check_ordered_schema(
    outcomes: pd.DataFrame,
    expected_columns: Sequence[str],
) -> dict[str, object]:
    expected = list(expected_columns)
    actual = list(outcomes.columns)
    missing = [column for column in expected if column not in actual]
    extra = [column for column in actual if column not in expected]
    same_order = actual == expected
    return {
        "check_name": "schema_columns",
        "passed": not missing and not extra and same_order,
        "details": (
            f"rows={len(outcomes)} columns={len(actual)} missing={missing} "
            f"extra={extra} same_order={same_order}"
        ),
    }


def check_source_identity(
    outcomes: pd.DataFrame,
    provenance: dict[str, object] | None = None,
) -> dict[str, object]:
    required = [
        "proposal_source_key",
        *PROPOSAL_SOURCE_KEY_FIELDS,
        "intervention_id",
        "stochastic_replicate_id",
    ]
    missing = [column for column in required if column not in outcomes.columns]
    if missing:
        return {
            "check_name": "source_identity",
            "passed": False,
            "details": f"missing required columns={missing}",
        }

    source_keys = outcomes["proposal_source_key"].astype(str)
    blank_source_keys = int((source_keys.str.strip() == "").sum())
    expected_keys: list[str] = []
    key_errors: list[str] = []
    for index, row in outcomes.iterrows():
        try:
            expected_keys.append(
                build_proposal_source_key(
                    module4_run_id=row["module4_run_id"],
                    variant_id=row["variant_id"],
                    seed=row["seed"],
                    run_dir_name=row["run_dir_name"],
                    family_id=row["family_id"],
                    proposal_id=row["proposal_id"],
                )
            )
        except ValueError as exc:
            expected_keys.append("")
            key_errors.append(f"row={index}: {exc}")
    expected_series = pd.Series(expected_keys, index=outcomes.index).astype(str)
    key_mismatches = int((source_keys != expected_series).sum())
    duplicate_grain_count = int(
        (
            outcomes.groupby(
                [
                    "proposal_source_key",
                    "intervention_id",
                    "stochastic_replicate_id",
                ],
                dropna=False,
            ).size()
            > 1
        ).sum()
    )
    observed_keys = set(source_keys)
    provenance_keys_match = True
    provenance_fields_match = True
    if provenance is not None:
        if "selected_proposal_source_keys" in provenance:
            provenance_keys = {
                str(item) for item in provenance["selected_proposal_source_keys"]  # type: ignore[union-attr]
            }
            provenance_keys_match = provenance_keys == observed_keys
        provenance_fields_match = list(
            provenance.get("source_identity_fields", [])
        ) == list(PROPOSAL_SOURCE_KEY_FIELDS)

    passed = (
        blank_source_keys == 0
        and key_mismatches == 0
        and duplicate_grain_count == 0
        and not key_errors
        and provenance_keys_match
        and provenance_fields_match
    )
    return {
        "check_name": "source_identity",
        "passed": passed,
        "details": (
            f"source_keys={len(observed_keys)} blank_source_keys={blank_source_keys} "
            f"key_mismatches={key_mismatches} "
            "duplicate_source_intervention_replicates="
            f"{duplicate_grain_count} provenance_keys_match={provenance_keys_match} "
            f"provenance_fields_match={provenance_fields_match} "
            f"key_errors={key_errors[:3]}"
        ),
    }


def check_matched_pair_ids(outcomes: pd.DataFrame) -> dict[str, object]:
    required = [
        "proposal_source_key",
        "intervention_id",
        "stochastic_replicate_id",
        "matched_pair_id",
        "run_id_baseline",
        "run_id_counterfactual",
    ]
    missing = [column for column in required if column not in outcomes.columns]
    if missing:
        return {
            "check_name": "matched_pair_ids",
            "passed": False,
            "details": f"missing required columns={missing}",
        }

    expected = (
        outcomes["proposal_source_key"].astype(str)
        + "|"
        + outcomes["intervention_id"].astype(str)
        + "|r"
        + outcomes["stochastic_replicate_id"].astype(str)
    )
    matched_pair_ids = outcomes["matched_pair_id"].astype(str)
    baseline_ids = outcomes["run_id_baseline"].astype(str)
    counterfactual_ids = outcomes["run_id_counterfactual"].astype(str)
    blank_pairs = int((matched_pair_ids.str.strip() == "").sum())
    pair_mismatches = int((matched_pair_ids != expected).sum())
    baseline_mismatches = int((baseline_ids != expected + "|baseline").sum())
    counterfactual_mismatches = int(
        (counterfactual_ids != expected + "|counterfactual").sum()
    )
    same_run_ids = int((baseline_ids == counterfactual_ids).sum())
    duplicate_pairs = int(matched_pair_ids.duplicated().sum())
    duplicate_baseline_ids = int(baseline_ids.duplicated().sum())
    duplicate_counterfactual_ids = int(counterfactual_ids.duplicated().sum())
    passed = (
        blank_pairs == 0
        and pair_mismatches == 0
        and baseline_mismatches == 0
        and counterfactual_mismatches == 0
        and same_run_ids == 0
        and duplicate_pairs == 0
        and duplicate_baseline_ids == 0
        and duplicate_counterfactual_ids == 0
    )
    return {
        "check_name": "matched_pair_ids",
        "passed": passed,
        "details": (
            f"unique_pairs={matched_pair_ids.nunique()} duplicate_pairs={duplicate_pairs} "
            f"blank_pairs={blank_pairs} same_run_ids={same_run_ids} "
            f"duplicate_baseline_ids={duplicate_baseline_ids} "
            f"duplicate_counterfactual_ids={duplicate_counterfactual_ids} "
            f"source_context_mismatches={pair_mismatches} "
            f"pair_mismatches={pair_mismatches} baseline_id_mismatches={baseline_mismatches} "
            f"counterfactual_id_mismatches={counterfactual_mismatches}"
        ),
    }


def check_seed_pairing(outcomes: pd.DataFrame) -> SeedPairingResult:
    required = ["baseline_stochastic_seed", "intervention_stochastic_seed"]
    missing = [column for column in required if column not in outcomes.columns]
    if missing:
        return SeedPairingResult(
            check={
                "check_name": "common_random_seed_pairing",
                "passed": False,
                "details": f"missing required columns={missing}",
            },
            mismatch_count=None,
        )

    baseline = outcomes["baseline_stochastic_seed"].astype(str)
    intervention = outcomes["intervention_stochastic_seed"].astype(str)
    mismatch_count = int((baseline != intervention).sum())
    return SeedPairingResult(
        check={
            "check_name": "common_random_seed_pairing",
            "passed": mismatch_count == 0,
            "details": f"seed mismatches={mismatch_count}",
        },
        mismatch_count=mismatch_count,
    )
