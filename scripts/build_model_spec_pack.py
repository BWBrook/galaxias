from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


TARGET_FIELDS = [
    "target_id",
    "target_group",
    "target_label",
    "evidence_ids",
    "time_start",
    "time_end",
    "location_scope",
    "taxon_scope",
    "model_output",
    "comparison_type",
    "target_value_numeric",
    "target_value_text",
    "tolerance_low",
    "tolerance_high",
    "priority_weight",
    "uncertainty_level",
    "notes",
]


CALIBRATION_TARGETS = [
    {
        "target_id": "CT001",
        "target_group": "historical_core",
        "target_label": "Pre-flood restricted range and habitat occupancy",
        "evidence_ids": "E001;E040",
        "time_start": 1965,
        "time_end": 1971,
        "location_scope": "original Lake Pedder plus immediate inflows and swampy pools",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "pedder_presence_lake_and_refuge_pre_flood",
        "comparison_type": "qualitative_state_constraint",
        "target_value_numeric": "",
        "target_value_text": "Before inundation, Pedder must be present in both lake and immediate refuge-stream habitat within the original range; Tier 1 does not represent any additional occupied basins.",
        "tolerance_low": "",
        "tolerance_high": "",
        "priority_weight": 4,
        "uncertainty_level": "low",
        "notes": "Use as an initial-state and burn-in constraint, not as a fitted abundance target.",
    },
    {
        "target_id": "CT002",
        "target_group": "historical_core",
        "target_label": "Post-flood boom phase in impoundment",
        "evidence_ids": "E005;E038;E042",
        "time_start": 1975,
        "time_end": 1980,
        "location_scope": "Lake Pedder impoundment and some tributaries",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "pedder_lake_abundance_index",
        "comparison_type": "window_relative_abundance_requirement",
        "target_value_numeric": "",
        "target_value_text": "Model must show a clear early post-inundation abundance phase in the lake compartment before the later decline.",
        "tolerance_low": "",
        "tolerance_high": "",
        "priority_weight": 5,
        "uncertainty_level": "medium",
        "notes": "Relative-pattern target only; not a hard numeric abundance constraint.",
    },
    {
        "target_id": "CT003",
        "target_group": "historical_core",
        "target_label": "Current candidate peak year is 1977",
        "evidence_ids": "E042;E043",
        "time_start": 1975,
        "time_end": 1979,
        "location_scope": "Lake Pedder impoundment littoral zone",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "year_of_peak_pedder_lake_abundance",
        "comparison_type": "target_year_match",
        "target_value_numeric": 1977,
        "target_value_text": "Peak-year target for the short-lived post-flood boom.",
        "tolerance_low": 1,
        "tolerance_high": 1,
        "priority_weight": 4,
        "uncertainty_level": "medium",
        "notes": "Supported well enough for calibration timing, but not yet as a hard numeric peak abundance target.",
    },
    {
        "target_id": "CT004",
        "target_group": "historical_core",
        "target_label": "Early trout predation and large-body phase",
        "evidence_ids": "E006;E007;E008",
        "time_start": 1972,
        "time_end": 1980,
        "location_scope": "Lake Pedder impoundment",
        "taxon_scope": "Salmo trutta acting on Pedder galaxias",
        "model_output": "trout_abundance_index_and_piscivory_modifier",
        "comparison_type": "event_and_window_presence",
        "target_value_numeric": 350000,
        "target_value_text": "The 1972 stocking pulse must be represented, and the model must allow a high-piscivory trout phase during the early impoundment years.",
        "tolerance_low": "",
        "tolerance_high": "",
        "priority_weight": 5,
        "uncertainty_level": "medium",
        "notes": "Use 350,000 fry as fixed forcing; do not treat it as a free calibration target.",
    },
    {
        "target_id": "CT005",
        "target_group": "historical_core",
        "target_label": "Lagged switch to climbing galaxias dominance",
        "evidence_ids": "E013;E014",
        "time_start": 1980,
        "time_end": 1983,
        "location_scope": "Lake Pedder lake samples",
        "taxon_scope": "Galaxias pedderensis and Galaxias brevipinnis",
        "model_output": "climbing_to_pedder_lake_ratio",
        "comparison_type": "windowed_dominance_switch",
        "target_value_numeric": 1.0,
        "target_value_text": "Pedder should dominate around 1980, with climbing galaxias becoming more abundant by about 1983.",
        "tolerance_low": "",
        "tolerance_high": "",
        "priority_weight": 5,
        "uncertainty_level": "medium",
        "notes": "This is the key lagged-mechanism pattern separating trout-first and climbing-first stories.",
    },
    {
        "target_id": "CT006",
        "target_group": "historical_core",
        "target_label": "Late-1980s stream-only persistence",
        "evidence_ids": "E009;E010;E044",
        "time_start": 1988,
        "time_end": 1989,
        "location_scope": "Four inflowing streams and remnant tributaries",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "pedder_refuge_presence_with_lake_absence",
        "comparison_type": "compartment_presence_constraint",
        "target_value_numeric": 11,
        "target_value_text": "By 1988-1989 the model should place Pedder in remnant tributary refugia, with effective disappearance from the impoundment and only very low total detected counts.",
        "tolerance_low": 5,
        "tolerance_high": 20,
        "priority_weight": 5,
        "uncertainty_level": "low",
        "notes": "Use as a strong transition constraint between lake decline and final refuge phase.",
    },
    {
        "target_id": "CT007",
        "target_group": "historical_core",
        "target_label": "Severe occupancy contraction in 1990-1991",
        "evidence_ids": "E011;E012",
        "time_start": 1990,
        "time_end": 1991,
        "location_scope": "Bonnet Bay creeks and wider surveyed catchment",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "occupied_refuge_sites_and_refuge_capture_index",
        "comparison_type": "joint_occupancy_and_count_constraint",
        "target_value_numeric": 5,
        "target_value_text": "Pedder should occur at only 5 of 117 sites, with 68 fish captured in 43 trips across the two Bonnet Bay streams.",
        "tolerance_low": 3,
        "tolerance_high": 7,
        "priority_weight": 5,
        "uncertainty_level": "low",
        "notes": "Use occupancy as the primary target and Bonnet Bay captures as the abundance-side anchor.",
    },
    {
        "target_id": "CT008",
        "target_group": "historical_core",
        "target_label": "Terminal decline in 1992-1996",
        "evidence_ids": "E037;E045",
        "time_start": 1992,
        "time_end": 1996,
        "location_scope": "Natural Lake Pedder system",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "terminal_natural_range_abundance",
        "comparison_type": "upper_bound_count_constraint",
        "target_value_numeric": 10,
        "target_value_text": "Further surveys in 1992-1996 yielded only 10 Pedder galaxias from the natural system, with total abundance thought to be fewer than 50 individuals.",
        "tolerance_low": "",
        "tolerance_high": 15,
        "priority_weight": 5,
        "uncertainty_level": "low",
        "notes": "Use the 10-fish count as the stronger direct constraint and the <50 estimate as corroborative context.",
    },
    {
        "target_id": "CT009",
        "target_group": "historical_core",
        "target_label": "Last natural-range record on 6 March 1996",
        "evidence_ids": "E046",
        "time_start": 1996,
        "time_end": 1996,
        "location_scope": "Natural Lake Pedder system",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "last_plausible_detection_year",
        "comparison_type": "last_occurrence_event",
        "target_value_numeric": 1996,
        "target_value_text": "The last plausible natural-range detection must occur in 1996, with the explicit dated record on 6 March 1996.",
        "tolerance_low": 0,
        "tolerance_high": 0,
        "priority_weight": 5,
        "uncertainty_level": "low",
        "notes": "This is the cleanest endpoint year and should be matched exactly in Tier 1.",
    },
    {
        "target_id": "CT010",
        "target_group": "historical_core",
        "target_label": "No detections through 2002",
        "evidence_ids": "E020;E046",
        "time_start": 1998,
        "time_end": 2002,
        "location_scope": "Natural Lake Pedder system",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "post_extirpation_detection_count",
        "comparison_type": "zero_detection_window",
        "target_value_numeric": 0,
        "target_value_text": "After the 1996 record, annual surveys through 2002 should yield zero detections in the natural range.",
        "tolerance_low": 0,
        "tolerance_high": 0,
        "priority_weight": 5,
        "uncertainty_level": "low",
        "notes": "Use alongside CT009 to pin the terminal state.",
    },
    {
        "target_id": "CT011",
        "target_group": "intrinsic_baseline",
        "target_label": "Lake Oberon predator-free establishment and growth",
        "evidence_ids": "E023;E050;E051",
        "time_start": 1991,
        "time_end": 2012,
        "location_scope": "Lake Oberon",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "predator_free_refuge_growth_trajectory",
        "comparison_type": "baseline_growth_constraint",
        "target_value_numeric": 500,
        "target_value_text": "A founder event of roughly 34 fish should plausibly establish, show juveniles by 1997, and reach a thriving population of at least ~500 adults by the early 2000s and several thousand fish by 2012.",
        "tolerance_low": 350,
        "tolerance_high": "",
        "priority_weight": 3,
        "uncertainty_level": "medium",
        "notes": "This constrains intrinsic Pedder dynamics away from the historical invasion setting.",
    },
    {
        "target_id": "CT012",
        "target_group": "intrinsic_baseline",
        "target_label": "Strathgordon delayed recruitment after habitat limitation",
        "evidence_ids": "E025;E052;E053;E054",
        "time_start": 2001,
        "time_end": 2012,
        "location_scope": "Strathgordon water supply dam",
        "taxon_scope": "Galaxias pedderensis",
        "model_output": "refuge_establishment_with_spawning_threshold",
        "comparison_type": "delayed_establishment_constraint",
        "target_value_numeric": 8,
        "target_value_text": "A larger serial-founder program should still permit delayed recruitment until habitat improvement, with juveniles first detected in 2008 and a well-established population by 2012.",
        "tolerance_low": "",
        "tolerance_high": "",
        "priority_weight": 3,
        "uncertainty_level": "low",
        "notes": "Use as a check on habitat-quality terms rather than as a historical-lake fit target.",
    },
]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_evidence_ids() -> set[str]:
    with (DATA_DIR / "evidence_ledger.csv").open(newline="", encoding="utf-8") as handle:
        return {row["evidence_id"] for row in csv.DictReader(handle)}


def split_ids(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def validate_targets(evidence_ids: set[str]) -> None:
    seen: set[str] = set()
    for row in CALIBRATION_TARGETS:
        target_id = row["target_id"]
        if target_id in seen:
            raise ValueError(f"Duplicate target_id: {target_id}")
        seen.add(target_id)
        missing = [eid for eid in split_ids(str(row["evidence_ids"])) if eid not in evidence_ids]
        if missing:
            raise ValueError(f"Unknown evidence_ids for {target_id}: {missing}")


def main() -> None:
    evidence_ids = load_evidence_ids()
    validate_targets(evidence_ids)
    write_csv(DATA_DIR / "calibration_targets.csv", CALIBRATION_TARGETS, TARGET_FIELDS)
    print("Wrote 12 calibration targets.")


if __name__ == "__main__":
    main()
