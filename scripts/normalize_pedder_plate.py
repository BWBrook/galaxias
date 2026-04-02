from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_PATH = DATA_DIR / "pedder_plate.csv"


RAW_TO_CLEAN = {
    "On pedder plate and passed QC": "on_pedder_plate_passed_qc",
    "Already genotyped on johnstoni plate": "already_genotyped_on_johnstoni_plate",
    "Available to extract": "available_to_extract",
    "Number to extract": "number_to_extract",
    "All possible samples": "all_possible_samples",
    "Samples to genotype on pedder plate": "samples_to_genotype_on_pedder_plate",
    "Final sample size": "final_sample_size",
}


def read_raw_rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.reader(handle))


def normalize_rows(rows: list[list[str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    header = rows[0][1:]
    clean_header = [RAW_TO_CLEAN[h] for h in header]

    current_species = None
    normalized: list[dict[str, object]] = []
    reported_total_row: list[int] | None = None

    for row in rows[1:]:
        first = row[0].strip()
        metrics = row[1:]

        if not first and not any(cell.strip() for cell in metrics):
            continue

        # Species section headers usually have a taxon in the first column and no metric values.
        # Some species may instead appear as a single inline total row with counts.
        if first.startswith("G."):
            if not any(cell.strip() for cell in metrics):
                current_species = first
                continue
            if current_species != first:
                current_species = first

        if first == "SUM":
            reported_total_row = [int(cell or 0) for cell in metrics]
            continue

        if current_species is None:
            raise ValueError(f"Found data row without an active species block: {row}")

        location = first
        row_scope = "location"
        if first == current_species:
            location = "species_total_only"
            row_scope = "species_total"

        record: dict[str, object] = {
            "species": current_species,
            "row_scope": row_scope,
            "location": location,
        }
        for column_name, raw_value in zip(clean_header, metrics):
            record[column_name] = int(raw_value or 0)
        normalized.append(record)

    if reported_total_row is None:
        raise ValueError("Did not find SUM row in raw pedder plate CSV.")

    totals_check: list[dict[str, object]] = []
    for index, column_name in enumerate(clean_header):
        computed_total = sum(int(row[column_name]) for row in normalized)
        reported_total = reported_total_row[index]
        totals_check.append(
            {
                "metric": column_name,
                "reported_sum": reported_total,
                "computed_sum_from_tidy_rows": computed_total,
                "matches_reported_sum": computed_total == reported_total,
            }
        )

    return normalized, totals_check


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> None:
    rows = read_raw_rows(RAW_PATH)
    normalized, totals_check = normalize_rows(rows)

    tidy_fields = [
        "species",
        "row_scope",
        "location",
        "on_pedder_plate_passed_qc",
        "already_genotyped_on_johnstoni_plate",
        "available_to_extract",
        "number_to_extract",
        "all_possible_samples",
        "samples_to_genotype_on_pedder_plate",
        "final_sample_size",
    ]
    total_fields = [
        "metric",
        "reported_sum",
        "computed_sum_from_tidy_rows",
        "matches_reported_sum",
    ]

    write_csv(DATA_DIR / "pedder_plate_tidy.csv", normalized, tidy_fields)
    write_csv(DATA_DIR / "pedder_plate_totals_check.csv", totals_check, total_fields)

    species_to_filename = {
        "G. brevipinnis": "pedder_plate_g_brevipinnis.csv",
        "G. pedderensis": "pedder_plate_g_pedderensis.csv",
        "G. fontanus": "pedder_plate_g_fontanus.csv",
    }

    for species, filename in species_to_filename.items():
        species_rows = [row for row in normalized if row["species"] == species]
        write_csv(DATA_DIR / filename, species_rows, tidy_fields)


if __name__ == "__main__":
    main()
