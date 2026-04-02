from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

import galah
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "data" / "ala"
DEFAULT_EMAIL = "barry.brook@utas.edu.au"

COMMON_FILTERS = ["basisOfRecord=PRESERVED_SPECIMEN"]
DEFAULT_FIELDS = [
    "scientificName",
    "acceptedNameUsage",
    "basisOfRecord",
    "eventDate",
    "year",
    "month",
    "day",
    "locality",
    "verbatimLocality",
    "waterBody",
    "stateProvince",
    "decimalLatitude",
    "decimalLongitude",
    "coordinateUncertaintyInMeters",
    "individualCount",
    "sex",
    "lifeStage",
    "occurrenceRemarks",
    "catalogNumber",
    "recordID",
    "occurrenceID",
    "institutionCode",
    "collectionCode",
    "institutionUid",
    "collectionUid",
    "dataResourceName",
    "datasetName",
    "recordedBy",
    "identifiedBy",
    "identificationQualifier",
]


@dataclass(frozen=True)
class TaxonQuery:
    query_taxon: str
    project_taxon_role: str
    extra_filters: tuple[str, ...] = ()

    @property
    def filters(self) -> list[str]:
        return [*COMMON_FILTERS, *self.extra_filters]


TAXON_QUERIES = [
    TaxonQuery("Galaxias pedderensis", "core_endemic"),
    TaxonQuery("Galaxias brevipinnis", "co_occurring_galaxiid", ("stateProvince=Tasmania",)),
    TaxonQuery("Galaxias parvus", "co_occurring_galaxiid", ("stateProvince=Tasmania",)),
]


SITE_PATTERNS: list[tuple[str, list[str]]] = [
    ("lake_oberon_insurance", [r"\boberon\b"]),
    ("strathgordon_insurance", [r"\bstrathgordon\b"]),
    ("bonnet_bay_refuge", [r"\bbonnet\b"]),
    (
        "pedder_system_or_refuge",
        [
            r"\bpedder\b",
            r"\bserpentine\b",
            r"\bhuon inlet\b",
            r"\bgordon canal\b",
            r"\bscotts peak\b",
            r"\bedgar\b",
            r"\bsolitary\b",
            r"\bwilmot bay\b",
            r"\bsprent basin\b",
            r"\bmaria\b",
            r"\bfrankland\b",
            r"\bswallow\b",
            r"\bcurrie\b",
            r"\bpebbly creek\b",
            r"\bswampy creek\b",
            r"\bforest creek\b",
            r"\btimber creek\b",
            r"\bred tape creek\b",
            r"\bmcpartl?and\b",
            r"\bmcpartl?an\b",
            r"\bfranklin\b",
        ],
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and curate ALA preserved-specimen records for Pedder galaxias project taxa."
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("ALA_EMAIL", DEFAULT_EMAIL),
        help="ALA-registered email address used by galah-python.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where curated ALA tables will be written.",
    )
    return parser.parse_args()


def clean_text(value: object) -> str | None:
    if value is None:
        return None
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    return re.sub(r"\s+", " ", text)


def choose_first_nonempty(*values: object) -> str | None:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return None


def build_locality_text(row: pd.Series) -> str | None:
    parts: list[str] = []
    seen: set[str] = set()
    for key in ("locality", "verbatimLocality", "waterBody"):
        text = clean_text(row.get(key))
        if text and text.lower() not in seen:
            parts.append(text)
            seen.add(text.lower())
    if not parts:
        return None
    return " | ".join(parts)


def classify_site_bucket(locality_text: str | None) -> str:
    if not locality_text:
        return "unknown"
    lowered = locality_text.lower()
    for bucket, patterns in SITE_PATTERNS:
        if any(re.search(pattern, lowered) for pattern in patterns):
            return bucket
    return "other_tasmania"


def classify_project_relevance(project_taxon_role: str, site_bucket: str) -> str:
    if project_taxon_role == "core_endemic":
        if site_bucket == "unknown":
            return "core_taxon_unknown_site"
        return "core_taxon"
    if site_bucket in {"lake_oberon_insurance", "strathgordon_insurance", "bonnet_bay_refuge", "pedder_system_or_refuge"}:
        return "pedder_linked_context"
    if site_bucket == "unknown":
        return "unknown_site_context"
    return "context_only"


def build_specimen_key(row: pd.Series) -> str:
    primary = [
        clean_text(row.get("institutionCode")),
        clean_text(row.get("collectionCode")),
        clean_text(row.get("catalogNumber")),
    ]
    if all(primary):
        return "|".join(primary)
    fallback = choose_first_nonempty(row.get("occurrenceID"), row.get("recordID"))
    if fallback:
        return fallback
    query_taxon = clean_text(row.get("query_taxon")) or "unknown_taxon"
    return f"{query_taxon}|row_without_identifier"


def add_temporal_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["event_date"] = pd.to_datetime(result["eventDate"], utc=True, errors="coerce")
    result["event_date_iso"] = result["event_date"].dt.strftime("%Y-%m-%d")
    for column in ("year", "month", "day"):
        result[column] = pd.to_numeric(result[column], errors="coerce").astype("Int64")
    result["year_inferred"] = result["year"]
    missing_year = result["year_inferred"].isna() & result["event_date"].notna()
    result.loc[missing_year, "year_inferred"] = result.loc[missing_year, "event_date"].dt.year.astype("Int64")
    result["year_inferred"] = result["year_inferred"].astype("Int64")
    return result


def download_taxon_matches() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for query in TAXON_QUERIES:
        frame = galah.search_taxa(taxa=query.query_taxon).copy()
        frame.insert(0, "query_taxon", query.query_taxon)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def download_occurrences(query: TaxonQuery) -> pd.DataFrame:
    frame = galah.atlas_occurrences(
        taxa=query.query_taxon,
        filters=query.filters,
        fields=DEFAULT_FIELDS,
    ).copy()
    frame.insert(0, "query_taxon", query.query_taxon)
    frame.insert(1, "project_taxon_role", query.project_taxon_role)
    frame.insert(2, "query_filters", "; ".join(query.filters))
    return frame


def curate_occurrences(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = raw.copy()
    frame = add_temporal_columns(frame)
    frame["locality_text"] = frame.apply(build_locality_text, axis=1)
    frame["site_bucket"] = frame["locality_text"].apply(classify_site_bucket)
    frame["project_relevance"] = frame.apply(
        lambda row: classify_project_relevance(row["project_taxon_role"], row["site_bucket"]),
        axis=1,
    )
    frame["specimen_key"] = frame.apply(build_specimen_key, axis=1)
    frame["catalog_backed"] = frame["catalogNumber"].map(lambda value: clean_text(value) is not None)
    frame["has_coordinates"] = frame["decimalLatitude"].notna() & frame["decimalLongitude"].notna()
    frame["has_event_date"] = frame["event_date"].notna() | frame["year_inferred"].notna()

    frame["locality_text_length"] = frame["locality_text"].fillna("").str.len()
    frame["duplicate_rank"] = (
        frame["has_event_date"].astype(int) * 100
        + frame["catalog_backed"].astype(int) * 10
        + frame["locality_text_length"].clip(upper=9)
    )
    frame = frame.sort_values(
        by=["specimen_key", "duplicate_rank", "event_date", "year_inferred"],
        ascending=[True, False, True, True],
        na_position="last",
    )
    frame["is_duplicate_specimen_key"] = frame.duplicated(subset=["specimen_key"], keep="first")
    curated = frame.loc[~frame["is_duplicate_specimen_key"]].copy()

    curated = curated.drop(columns=["event_date", "locality_text_length", "duplicate_rank"])
    raw_out = frame.drop(columns=["event_date", "locality_text_length", "duplicate_rank"])
    return raw_out, curated


def summarize_by_taxon(curated: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        curated.groupby(["query_taxon", "project_taxon_role"], dropna=False)
        .agg(
            curated_records=("specimen_key", "count"),
            pedder_linked_records=("project_relevance", lambda s: int((s != "context_only").sum())),
            institutions=("institutionCode", "nunique"),
            collections=("collectionCode", "nunique"),
            earliest_year=("year_inferred", "min"),
            latest_year=("year_inferred", "max"),
        )
        .reset_index()
    )
    return grouped


def summarize_by_institution(curated: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        curated.groupby(["query_taxon", "institutionCode", "collectionCode", "dataResourceName"], dropna=False)
        .agg(
            curated_records=("specimen_key", "count"),
            earliest_year=("year_inferred", "min"),
            latest_year=("year_inferred", "max"),
            pedder_linked_records=("project_relevance", lambda s: int((s != "context_only").sum())),
        )
        .reset_index()
        .sort_values(["query_taxon", "curated_records", "institutionCode"], ascending=[True, False, True])
    )
    return grouped


def write_outputs(
    output_dir: Path,
    taxon_matches: pd.DataFrame,
    raw: pd.DataFrame,
    curated: pd.DataFrame,
    summary_by_taxon: pd.DataFrame,
    summary_by_institution: pd.DataFrame,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    relevant = curated.loc[curated["project_relevance"] != "context_only"].copy()
    outputs = {
        "taxon_matches.csv": taxon_matches,
        "specimens_raw.csv": raw,
        "specimens_curated.csv": curated,
        "specimens_project_relevant.csv": relevant,
        "summary_by_taxon.csv": summary_by_taxon,
        "summary_by_institution.csv": summary_by_institution,
    }

    for filename, frame in outputs.items():
        frame.to_csv(output_dir / filename, index=False)


def main() -> None:
    args = parse_args()
    galah.galah_config(email=args.email, atlas="Australia", reason=4)

    taxon_matches = download_taxon_matches()
    raw_frames = [download_occurrences(query) for query in TAXON_QUERIES]
    raw = pd.concat(raw_frames, ignore_index=True)
    raw_out, curated = curate_occurrences(raw)

    summary_by_taxon = summarize_by_taxon(curated)
    summary_by_institution = summarize_by_institution(curated)
    write_outputs(args.output_dir, taxon_matches, raw_out, curated, summary_by_taxon, summary_by_institution)

    print(f"Wrote {len(raw_out)} raw rows and {len(curated)} curated rows to {args.output_dir}")
    print(summary_by_taxon.to_string(index=False))


if __name__ == "__main__":
    main()
