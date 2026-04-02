# Evidence Ledger

This directory contains the first structured evidence pass for the Pedder galaxias project.

Files:

- `source_register.csv`: metadata for sources actually used in this pass.
- `evidence_ledger.csv`: direct Pedder-system evidence rows for chronology, life history, threats, translocations, monitoring, and data-service leads.
- `proxy_evidence_leads.csv`: comparative or proxy evidence that may help parameter priors or later companion analyses.
- `priority_source_gaps.csv`: missing or not-yet-retrieved sources that would materially improve the ledger.
- `ala/`: ALA preserved-specimen curation outputs produced via `galah-python`.
- `pedder_plate.csv`: raw plate-planning table as dropped into the repo.
- `pedder_plate_tidy.csv`: normalized version of `pedder_plate.csv`, one row per species-location record.
- `pedder_plate_g_brevipinnis.csv`, `pedder_plate_g_pedderensis.csv`, `pedder_plate_g_fontanus.csv`: species-specific extracts from the tidy table.
- `pedder_plate_totals_check.csv`: reconciliation of the tidy rows against the reported `SUM` row in the raw file.

In `data/ala/`:

- `taxon_matches.csv`: ALA taxon-resolution results for the queried names.
- `specimens_raw.csv`: raw preserved-specimen download rows from the ALA for the configured taxa.
- `specimens_curated.csv`: curated specimen table with normalized dates, locality text, specimen keys, and Pedder-relevance flags.
- `specimens_project_relevant.csv`: subset of curated rows that are directly relevant or potentially relevant to the Pedder project.
- `summary_by_taxon.csv`: counts and year ranges by queried taxon.
- `summary_by_institution.csv`: counts and year ranges by institution / collection / taxon.

Design notes:

- I kept conflicting source claims rather than prematurely resolving them.
- `uncertainty_level` is qualitative and is meant to help triage rows for calibration use.
- `source_priority` distinguishes `primary`, `official`, `review`, `secondary`, and `data_service`.
- The ALA rows are deliberately tagged as `data_service`; they are leads for curated specimen extraction, not ready-made abundance evidence.
- The current ledger is strongest on chronology and management history, and weaker on direct quantitative demography and trout/climbing abundance time series.
- In the normalized pedder plate tables, blank numeric cells from the raw sheet have been interpreted as zero counts. The `G. fontanus` row is treated as a species-total row because it appears inline rather than under a separate location block.
- In the ALA curation outputs, `specimens_curated.csv` is one row per inferred specimen key, and `specimens_project_relevant.csv` keeps rows that are either directly Pedder-linked or unresolved enough to warrant follow-up rather than immediate exclusion.

Immediate next steps:

1. Fold the strongest dated museum-specimen milestones from `data/ala/` back into `evidence_ledger.csv`.
2. Request direct museum-lot exports to fill missing TMAG dates and verify ambiguous off-system Pedder galaxias records.
3. Add a `parameter_priors.csv` file once the direct evidence base is a little less dependent on secondary synthesis.
