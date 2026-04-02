from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
ALA_DIR = ROOT / "data" / "ala"
CURATED_PATH = ALA_DIR / "specimens_curated.csv"
API_BASE = "https://biocache.ala.org.au/ws/occurrence"


def get_nested(data: dict[str, Any], *path: str) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if current is None:
            return None
    return current


def to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, list):
        parts = [to_text(item) for item in value]
        parts = [item for item in parts if item]
        return "; ".join(parts) if parts else None
    text = str(value).strip()
    return text or None


def fetch_occurrence(session: requests.Session, record_id: str) -> dict[str, Any]:
    response = session.get(f"{API_BASE}/{record_id}", timeout=60)
    response.raise_for_status()
    return response.json()


def enrich_rows(curated: pd.DataFrame) -> pd.DataFrame:
    target = curated.loc[curated["project_relevance"] != "context_only"].copy()
    session = requests.Session()

    records: list[dict[str, Any]] = []
    for row in target.itertuples(index=False):
        payload = fetch_occurrence(session, row.recordID)
        raw = payload.get("raw", {})
        processed = payload.get("processed", {})

        raw_issues = (
            get_nested(raw, "classification", "taxonomicIssues")
            or get_nested(processed, "classification", "taxonomicIssues")
            or []
        )
        raw_locality = get_nested(raw, "location", "locality")
        raw_verbatim_locality = get_nested(raw, "location", "verbatimLocality")
        raw_water_body = get_nested(raw, "location", "waterBody")
        raw_recorded_by = get_nested(raw, "occurrence", "recordedBy")
        processed_occurrence_status = get_nested(processed, "occurrence", "occurrenceStatus")

        record = {
            "recordID": row.recordID,
            "query_taxon": row.query_taxon,
            "project_taxon_role": row.project_taxon_role,
            "project_relevance": row.project_relevance,
            "site_bucket": row.site_bucket,
            "institutionCode": row.institutionCode,
            "collectionCode": row.collectionCode,
            "catalogNumber": row.catalogNumber,
            "occurrence_api_url": f"{API_BASE}/{row.recordID}",
            "locality_text_curated": row.locality_text,
            "raw_locality": to_text(raw_locality),
            "raw_verbatim_locality": to_text(raw_verbatim_locality),
            "raw_water_body": to_text(raw_water_body),
            "raw_recorded_by": to_text(raw_recorded_by),
            "raw_identified_by": to_text(get_nested(raw, "identification", "identifiedBy")),
            "raw_event_year": to_text(get_nested(raw, "event", "year")),
            "raw_event_month": to_text(get_nested(raw, "event", "month")),
            "raw_event_day": to_text(get_nested(raw, "event", "day")),
            "processed_event_year": to_text(get_nested(processed, "event", "year")),
            "processed_event_month": to_text(get_nested(processed, "event", "month")),
            "processed_event_day": to_text(get_nested(processed, "event", "day")),
            "processed_event_date_precision": to_text(get_nested(processed, "event", "datePrecision")),
            "processed_occurrence_status": to_text(processed_occurrence_status),
            "raw_individual_count": to_text(get_nested(raw, "occurrence", "individualCount")),
            "processed_individual_count": to_text(get_nested(processed, "occurrence", "individualCount")),
            "raw_preparations": to_text(get_nested(raw, "occurrence", "preparations")),
            "raw_sampling_protocol": to_text(get_nested(raw, "occurrence", "samplingProtocol")),
            "raw_georeference_protocol": to_text(get_nested(raw, "location", "georeferenceProtocol")),
            "raw_georeference_sources": to_text(get_nested(raw, "location", "georeferenceSources")),
            "processed_rights_holder": to_text(get_nested(processed, "occurrence", "rightsHolder")),
            "raw_occurrence_modified": to_text(get_nested(raw, "occurrence", "modified")),
            "processed_occurrence_modified": to_text(get_nested(processed, "occurrence", "modified")),
            "raw_taxonomic_issues": to_text(raw_issues),
            "missing_collection_date_issue": "MISSING_COLLECTION_DATE" in raw_issues,
            "missing_locality_after_enrichment": to_text(raw_locality) is None and to_text(raw_verbatim_locality) is None,
            "has_any_public_date_component": any(
                to_text(value)
                for value in (
                    get_nested(raw, "event", "year"),
                    get_nested(raw, "event", "month"),
                    get_nested(raw, "event", "day"),
                    get_nested(processed, "event", "year"),
                    get_nested(processed, "event", "month"),
                    get_nested(processed, "event", "day"),
                )
            ),
        }
        records.append(record)
        time.sleep(0.05)

    return pd.DataFrame.from_records(records)


def build_gap_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    summary = (
        enriched.groupby(["query_taxon", "institutionCode"], dropna=False)
        .agg(
            records=("recordID", "count"),
            missing_collection_date_issue=("missing_collection_date_issue", "sum"),
            missing_locality_after_enrichment=("missing_locality_after_enrichment", "sum"),
            has_any_public_date_component=("has_any_public_date_component", "sum"),
        )
        .reset_index()
        .sort_values(["query_taxon", "institutionCode"])
    )
    return summary


def build_tmag_request_list(enriched: pd.DataFrame) -> pd.DataFrame:
    request = enriched.loc[
        (enriched["query_taxon"] == "Galaxias pedderensis")
        & (enriched["institutionCode"] == "TMAG")
    ].copy()
    request["request_priority"] = "high"
    request["requested_fields"] = (
        "collection_date; collector; locality; waterbody; event remarks; individual count; identification history; label scan"
    )
    request["request_reason"] = request.apply(
        lambda row: (
            "Core Pedder galaxias lot missing collection date in public ALA feed"
            if row["missing_collection_date_issue"]
            else "Core Pedder galaxias lot for chronology verification"
        ),
        axis=1,
    )
    columns = [
        "catalogNumber",
        "institutionCode",
        "query_taxon",
        "site_bucket",
        "locality_text_curated",
        "raw_recorded_by",
        "raw_identified_by",
        "raw_taxonomic_issues",
        "occurrence_api_url",
        "request_priority",
        "requested_fields",
        "request_reason",
    ]
    return request[columns].sort_values(["catalogNumber"])


def main() -> None:
    curated = pd.read_csv(CURATED_PATH)
    enriched = enrich_rows(curated)
    gap_summary = build_gap_summary(enriched)
    tmag_request = build_tmag_request_list(enriched)

    enriched.to_csv(ALA_DIR / "project_relevant_occurrence_enrichment.csv", index=False)
    gap_summary.to_csv(ALA_DIR / "project_relevant_metadata_gap_summary.csv", index=False)
    tmag_request.to_csv(ALA_DIR / "tmag_pedderensis_request_list.csv", index=False)

    print(f"Enriched {len(enriched)} project-relevant records")
    print(gap_summary.to_string(index=False))


if __name__ == "__main__":
    main()
