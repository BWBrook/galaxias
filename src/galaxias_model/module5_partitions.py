from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PartitionDefinition:
    label: str
    source_set: str
    family_id: str
    intervention_ids: tuple[str, ...]


PARTITION_DEFINITIONS: tuple[PartitionDefinition, ...] = (
    PartitionDefinition(
        label="headline/persistent_joint_cause",
        source_set="accepted",
        family_id="persistent_joint_cause",
        intervention_ids=(
            "m5_persistent_joint_cause_status_quo",
            "m5_persistent_joint_cause_no_trout_pressure",
            "m5_persistent_joint_cause_no_climbing_pressure",
            "m5_persistent_joint_cause_no_trout_or_climbing_pressure",
        ),
    ),
    PartitionDefinition(
        label="headline/climbing_only",
        source_set="accepted",
        family_id="climbing_only",
        intervention_ids=(
            "m5_climbing_only_status_quo",
            "m5_climbing_only_no_climbing_pressure",
        ),
    ),
    PartitionDefinition(
        label="headline/transient_perfect_storm",
        source_set="accepted",
        family_id="transient_perfect_storm",
        intervention_ids=(
            "m5_transient_perfect_storm_status_quo",
            "m5_transient_perfect_storm_no_trout_pressure",
            "m5_transient_perfect_storm_no_climbing_pressure",
            "m5_transient_perfect_storm_no_trout_or_climbing_pressure",
        ),
    ),
    PartitionDefinition(
        label="diagnostic_sidecar/climbing_only_no_trout_pressure",
        source_set="accepted",
        family_id="climbing_only",
        intervention_ids=("m5_climbing_only_no_trout_pressure",),
    ),
    PartitionDefinition(
        label="negative_reference/habitat_only_null",
        source_set="family_winners",
        family_id="habitat_only_null",
        intervention_ids=("m5_habitat_only_null_negative_reference",),
    ),
    PartitionDefinition(
        label="negative_reference/trout_only",
        source_set="family_winners",
        family_id="trout_only",
        intervention_ids=("m5_trout_only_negative_reference",),
    ),
)


def _build_intervention_to_partition() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for definition in PARTITION_DEFINITIONS:
        for intervention_id in definition.intervention_ids:
            if intervention_id in mapping:
                raise ValueError(
                    f"Intervention appears in multiple partitions: {intervention_id}"
                )
            mapping[intervention_id] = definition.label
    return mapping


INTERVENTION_TO_PARTITION = _build_intervention_to_partition()
