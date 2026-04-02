# Digital Museum Enrichment Round 1

## What was attempted

This pass focused on digital-only enrichment of the project-relevant museum subset, without relying on curator intervention or physical access.

The workflow:

- started from `data/ala/specimens_curated.csv`
- retained the project-relevant subset
- queried the ALA per-record occurrence API for each retained row
- extracted raw and processed event fields, locality fields, quality flags, preparation / protocol metadata, and modification timestamps

The workflow is scripted in `scripts/enrich_ala_project_records.py`.

## Outputs

- `data/ala/project_relevant_occurrence_enrichment.csv`
- `data/ala/project_relevant_metadata_gap_summary.csv`
- `data/ala/tmag_pedderensis_request_list.csv`

## Main result

The digital-only pass improved traceability, but it did not solve the main completeness problem.

The strongest result is negative but informative:

- all `30` TMAG `Galaxias pedderensis` rows in the project-relevant subset carry the ALA issue flag `MISSING_COLLECTION_DATE`
- all `25` Pedder-linked TMAG `G. brevipinnis` rows also carry `MISSING_COLLECTION_DATE`
- all `41` Pedder-linked TMAG `G. parvus` rows also carry `MISSING_COLLECTION_DATE`

This strongly suggests the missing dates are absent from the public ALA-backed feed itself, not just omitted from the earlier bulk download.

## What did improve digitally

- `NMV`, `QVMAG`, `CSIRO`, and `AM` records are already much more complete online and can be used directly for chronology work.
- The ALA per-record API exposes useful extra fields such as `datePrecision`, `preparations`, `samplingProtocol`, `georeferenceProtocol`, modification timestamps, and explicit quality flags.
- For `NMV`, the public Museums Victoria specimen pages are richer again than the ALA export and show that some additional fields are recoverable from online sources when a specimen page is already known.

## Current online bottlenecks

- `TMAG`: the public digital route appears to stop at the ALA-backed data feed for many vertebrate records, leaving the core date gap unresolved.
- `QVMAG`: the institution's own online collections page is currently down for maintenance, so ALA is the practical public route for now.
- `Museums Victoria`: public specimen pages are rich, but a clean scripted search-to-page crosswalk was not established in this pass.

## Interpretation

The limiting factor is no longer "can we script the public data better?" so much as "does the institution expose the missing fields online at all?".

For the Pedder project, that means:

- digital tooling can still keep improving provenance, quality-flag triage, and public-field extraction
- but the missing TMAG collection dates are now best treated as a curator-database problem rather than a scraping problem

## Recommendation

The highest-yield next contact is a narrow TMAG request for the `30` core `G. pedderensis` lots in `data/ala/tmag_pedderensis_request_list.csv`.
