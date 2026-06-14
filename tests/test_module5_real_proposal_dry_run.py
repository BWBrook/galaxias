from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from galaxias_model.io import load_model_inputs
from galaxias_model.module5_counterfactual import run_module5_real_proposal_dry_run
from galaxias_model import module5_proposals as proposals_module
from galaxias_model.module5_proposals import (
    APPROVED_DRY_RUN_PROPOSAL_IDS,
    DEFAULT_DRY_RUN_SEED,
    DEFAULT_DRY_RUN_VARIANT,
    DEFAULT_PARAMETER_VALUES_SHA256,
    derive_module5_seed,
    load_parameter_values_table,
    load_selected_dry_run_proposals,
    resolve_proposal_parameters,
    verify_parameter_values_artifact,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MEMBERSHIP = DATA_DIR / "module4_5_proposal_set_membership.csv"
MANIFEST = DATA_DIR / "module4_raw_artifact_manifest.csv"
INTERVENTIONS = DATA_DIR / "module5_counterfactual_interventions.csv"
OUTCOME_SCHEMA = DATA_DIR / "module5_counterfactual_outcome_schema.csv"
PARAMETER_VALUES = (
    ROOT
    / "outputs/remote/module4_observation_sensitivity_20260522T101942Z/"
    / "baseline_current_seed20260410/parameter_values.csv.gz"
)
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


def _expected_source_key(row: dict[str, object]) -> str:
    return "|".join(str(row[field]) for field in SOURCE_KEY_FIELDS)


def test_accepted_frontier_source_keys_are_unique_while_bare_proposal_ids_repeat() -> None:
    accepted = _accepted_frontier_rows()
    proposal_counts = Counter(row["proposal_id"] for row in accepted)
    source_keys = [_expected_source_key(row) for row in accepted]

    duplicate_bare_ids = {proposal_id: count for proposal_id, count in proposal_counts.items() if count > 1}

    assert len(accepted) == 750
    assert len(proposal_counts) == 246
    assert len(duplicate_bare_ids) == 158
    assert max(duplicate_bare_ids.values()) == 7
    assert len(set(source_keys)) == len(accepted)


def test_source_key_helper_distinguishes_repeated_bare_proposal_ids() -> None:
    assert hasattr(proposals_module, "build_proposal_source_key")

    duplicate_rows = [
        row for row in _accepted_frontier_rows() if row["proposal_id"] == "climbing_only:p00005"
    ]
    assert len(duplicate_rows) == 2

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
    assert source_keys == [_expected_source_key(row) for row in duplicate_rows]
    assert len(set(source_keys)) == 2

    seeds = [
        derive_module5_seed(source_key, "m5_climbing_only_status_quo", 0)
        for source_key in source_keys
    ]
    assert len(set(seeds)) == 2


def test_selected_dry_run_proposals_and_parameter_values_are_manifest_backed() -> None:
    proposals = load_selected_dry_run_proposals(MEMBERSHIP)

    assert tuple(proposal.proposal_id for proposal in proposals) == APPROVED_DRY_RUN_PROPOSAL_IDS
    assert all(proposal.proposal_source_key for proposal in proposals)
    assert all(proposal.module4_run_id for proposal in proposals)
    assert len({proposal.proposal_source_key for proposal in proposals}) == len(proposals)
    assert {proposal.variant_id for proposal in proposals} == {DEFAULT_DRY_RUN_VARIANT}
    assert {proposal.seed for proposal in proposals} == {DEFAULT_DRY_RUN_SEED}
    assert all(proposal.in_family_winners for proposal in proposals)

    artifact = verify_parameter_values_artifact(MANIFEST, PARAMETER_VALUES)
    assert artifact.sha256 == DEFAULT_PARAMETER_VALUES_SHA256

    values = load_parameter_values_table(PARAMETER_VALUES)
    counts = values[values["proposal_id"].isin(APPROVED_DRY_RUN_PROPOSAL_IDS)].groupby("proposal_id")[
        "parameter_id"
    ].nunique()
    assert set(counts.index) == set(APPROVED_DRY_RUN_PROPOSAL_IDS)
    assert (counts == 40).all()


def test_resolve_real_proposal_parameters_uses_sampled_values_and_valid_constraints() -> None:
    model_inputs = load_model_inputs(DATA_DIR)
    proposals = load_selected_dry_run_proposals(MEMBERSHIP)
    values = load_parameter_values_table(PARAMETER_VALUES)
    proposal = next(item for item in proposals if item.proposal_id == "persistent_joint_cause:p00162")

    resolved = resolve_proposal_parameters(model_inputs, proposal, values)
    sampled = values.loc[values["proposal_id"] == proposal.proposal_id].set_index("parameter_id")

    assert resolved.family_id == "persistent_joint_cause"
    assert resolved.family_label == proposal.family_label
    assert len(resolved.values) == 40
    assert resolved.value("PR020") == sampled.loc["PR020", "value_natural"]
    assert resolved.status("PR020") == sampled.loc["PR020", "parameter_status"]
    assert set(
        [
            "proposal_id",
            "variant_id",
            "seed",
            "proposal_seed",
            "sampled_flag",
            "value_sampling",
            "effective_value",
        ]
    ).issubset(resolved.manifest.columns)


def test_real_proposal_dry_run_writes_schema_conforming_matched_rows(tmp_path: Path) -> None:
    output_dir = tmp_path / "module5_real_dry_run"
    output_file = run_module5_real_proposal_dry_run(
        data_dir=DATA_DIR,
        proposal_membership_path=MEMBERSHIP,
        module4_manifest_path=MANIFEST,
        parameter_values_path=PARAMETER_VALUES,
        interventions_path=INTERVENTIONS,
        outcome_schema_path=OUTCOME_SCHEMA,
        output_dir=output_dir,
        replicates=1,
        stochastic=True,
    )

    assert output_file == output_dir / "matched_outcomes.csv"
    assert (output_dir / "provenance.json").exists()

    rows = list(csv.DictReader(output_file.open(newline="", encoding="utf-8")))
    assert len(rows) == 13
    assert {row["proposal_id"] for row in rows} == set(APPROVED_DRY_RUN_PROPOSAL_IDS)
    assert {row["variant_id"] for row in rows} == {DEFAULT_DRY_RUN_VARIANT}
    assert {int(row["seed"]) for row in rows} == {DEFAULT_DRY_RUN_SEED}
    assert {"proposal_source_key", "module4_run_id", "run_dir_name"}.issubset(rows[0])

    schema_columns = list(pd.read_csv(OUTCOME_SCHEMA)["column_name"])
    assert list(rows[0].keys()) == schema_columns

    membership = pd.read_csv(MEMBERSHIP, dtype={"seed": "Int64"}, keep_default_na=False)
    selected_source_keys = {
        str(row["proposal_id"]): _expected_source_key(row)
        for row in membership.loc[
            membership["proposal_id"].isin(APPROVED_DRY_RUN_PROPOSAL_IDS)
            & (membership["variant_id"] == DEFAULT_DRY_RUN_VARIANT)
            & (membership["seed"].astype(int) == DEFAULT_DRY_RUN_SEED)
        ].to_dict(orient="records")
    }

    for row in rows:
        assert not row["proposal_id"].startswith("smoke_default:")
        assert row["proposal_source_key"] == selected_source_keys[row["proposal_id"]]
        assert row["module4_run_id"] == "module4_observation_sensitivity_20260522T101942Z"
        assert row["run_dir_name"] == "baseline_current_seed20260410"
        assert row["baseline_stochastic_seed"] == row["intervention_stochastic_seed"]
        assert row["baseline_stochastic_seed"] == str(
            derive_module5_seed(
                row["proposal_source_key"],
                row["intervention_id"],
                int(row["stochastic_replicate_id"]),
            )
        )
        assert row["matched_pair_id"] == (
            f"{row['proposal_source_key']}|{row['intervention_id']}|r{row['stochastic_replicate_id']}"
        )
        assert row["run_id_baseline"] == f"{row['matched_pair_id']}|baseline"
        assert row["run_id_counterfactual"] == f"{row['matched_pair_id']}|counterfactual"

    provenance = json.loads((output_dir / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["status"] == "real_proposal_local_dry_run"
    assert provenance["production_attribution"] is False
    assert provenance["parameter_values_sha256"] == DEFAULT_PARAMETER_VALUES_SHA256
    assert set(provenance["selected_proposal_ids"]) == set(APPROVED_DRY_RUN_PROPOSAL_IDS)
    assert set(provenance["selected_proposal_source_keys"]) == set(selected_source_keys.values())
    assert provenance["source_identity_fields"] == list(SOURCE_KEY_FIELDS)
    assert "proposal_source_key" in provenance["seed_derivation"]
