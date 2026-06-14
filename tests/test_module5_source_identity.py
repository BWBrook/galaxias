from __future__ import annotations

import csv
from pathlib import Path

from galaxias_model import module5_proposals as proposals_module
from galaxias_model.module5_proposals import derive_module5_seed


ROOT = Path(__file__).resolve().parents[1]
MEMBERSHIP = ROOT / "data" / "module4_5_proposal_set_membership.csv"
SOURCE_KEY_FIELDS = (
    "module4_run_id",
    "variant_id",
    "seed",
    "run_dir_name",
    "family_id",
    "proposal_id",
)


def _accepted_frontier_rows() -> list[dict[str, str]]:
    rows = list(csv.DictReader(MEMBERSHIP.open(newline="", encoding="utf-8")))
    return [
        row
        for row in rows
        if row["in_accepted"].strip().lower() == "true"
        and row["family_id"]
        in {
            "persistent_joint_cause",
            "climbing_only",
            "transient_perfect_storm",
        }
    ]


def _expected_source_key(row: dict[str, str]) -> str:
    return "|".join(row[field] for field in SOURCE_KEY_FIELDS)


def test_source_key_helper_uses_required_context_fields() -> None:
    assert hasattr(proposals_module, "build_proposal_source_key")

    row = _accepted_frontier_rows()[0]
    assert proposals_module.build_proposal_source_key(
        module4_run_id=row["module4_run_id"],
        variant_id=row["variant_id"],
        seed=row["seed"],
        run_dir_name=row["run_dir_name"],
        family_id=row["family_id"],
        proposal_id=row["proposal_id"],
    ) == _expected_source_key(row)


def test_repeated_bare_proposal_ids_get_distinct_source_keys_and_seeds() -> None:
    assert hasattr(proposals_module, "build_proposal_source_key")

    duplicate_rows = [
        row for row in _accepted_frontier_rows() if row["proposal_id"] == "climbing_only:p00005"
    ]
    assert len(duplicate_rows) == 2
    assert len({row["proposal_id"] for row in duplicate_rows}) == 1

    source_keys = [
        proposals_module.build_proposal_source_key(
            module4_run_id=row["module4_run_id"],
            variant_id=row["variant_id"],
            seed=row["seed"],
            run_dir_name=row["run_dir_name"],
            family_id=row["family_id"],
            proposal_id=row["proposal_id"],
        )
        for row in duplicate_rows
    ]
    seeds = [
        derive_module5_seed(source_key, "m5_climbing_only_status_quo", 0)
        for source_key in source_keys
    ]

    assert source_keys == [_expected_source_key(row) for row in duplicate_rows]
    assert len(set(source_keys)) == 2
    assert len(set(seeds)) == 2
