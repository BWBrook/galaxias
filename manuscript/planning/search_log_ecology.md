# Search log: Pedder galaxias ecology, decline, genetics and conservation

## Scope and date

Searches were run on **4 October 2026** with a literature cutoff of that date. The approach was a broad, targeted review with backward reference chasing from the local Pedder corpus and forward/current searching through publisher pages, Crossref, government repositories and general web search. It was not a registered systematic review, and database subscription indexes were not queried exhaustively. Search results were screened for direct relevance to Pedder galaxias, Australian/New Zealand galaxiid responses to trout or other galaxiids, habitat alteration, isolation management, conservation translocation and genetics.

## Local evidence inspected

- `AGENT_HANDOFF.md`, `literature/README.md`, `docs/literature_review_round1.md`, and `docs/hamr_spawning_erratum_20261004.md`.
- Every markdown transcription in `literature/pedder/` and `literature/comparative/`, with targeted full reads of the Pedder genetics paper, Chilcott et al., Hamr, Sanger, Lake, the recovery plan, Ault and White, Townsend and Crowl, Glova and Sagar, Hardie, McDowall, Waters et al. and Jense et al.
- The round-one review was used as a discovery map only. Its causal assertions were rechecked against primary/local sources and the current official listing statement; stronger claims were not inherited.

## Exact web queries

General and Pedder-specific:

- `"Galaxias pedderensis" 2026`
- `"Galaxias pedderensis" conservation genetics Horner Jense Burridge`
- `"Extinct habitat, extant species" citing`
- `site:doi.org Galaxias galaxiid trout translocation threatened freshwater fish`
- `site:nre.tas.gov.au "Listing Statement for Galaxias pedderensis" 2023`
- `site:nre.tas.gov.au Pedder Galaxias management plan 2023`
- `site:ifs.tas.gov.au Pedder galaxias Lake Oberon Strathgordon monitoring`
- `"Galaxias pedderensis" 2024 OR 2025 OR 2026 -Horner`

Australian freshwater-fish recovery and translocation:

- `site:publish.csiro.au "A review of on-ground recovery actions for threatened freshwater fish in Australia" DOI`
- `Australian threatened freshwater fish translocation conservation review DOI`
- `galaxiid conservation translocation trout barrier eradication Australia New Zealand DOI`
- `Galaxias trout predation competition Australia Tasmania DOI`
- `"Key considerations for decision makers and stakeholders" fish conservation translocations DOI`
- `site:sciencedirect.com "Key considerations for decision makers" source populations conservation translocations fishes`
- `S2351989426003732 DOI`
- `2026 fish conservation translocation source populations genetics habitat life history DOI`
- `Weeks Sgro Young Frankham 2011 assessing benefits risks translocations DOI`
- `"Assessing the benefits and risks of translocations in changing environments"`
- `freshwater fish translocation guidelines genetics conservation DOI Australia`
- `barred galaxias translocation Ayres 2012 DOI`

Trout, galaxiids, refuges and barriers:

- `site:onlinelibrary.wiley.com galaxiid trout barrier removal translocation conservation New Zealand`
- `site:publish.csiro.au galaxiid translocation threatened fish recovery Australia`
- `site:link.springer.com Galaxias brown trout predation competition conservation`
- `introduced trout galaxiid density experimental removal waterfall barrier DOI`
- `"Managing Isolation: Implementing In-Stream Barriers" DOI`
- `"Effects of introduced trout predation on non-diadromous galaxiid" DOI`
- `"Evidence of source-sink metapopulations" galaxiid trout DOI`
- `"Size-related impacts of introduced brown trout" DOI`
- `"Effects of Habitat Structure and the Presence of Brown Trout" DOI`
- `"Fragmented population structure in a native New Zealand fish" DOI`
- `"Dietary and Spatial Overlap between Stream Populations" DOI`
- `"A further assessment of trophic and spatial inter-relations" DOI`

## Source avenues and verification

- **Publisher pages:** CSIRO/ConnectSci, Wiley, Springer, Oxford Academic, Taylor & Francis and ScienceDirect were used for titles, abstracts, article details and accessible full text.
- **Government and institutional sources:** Tasmanian NRE listing statement; Inland Fisheries Service monitoring/news; Australian DCCEEW recovery plan and listing advice; New Zealand Department of Conservation Science for Conservation report; USGS publication record for the 2026 fish-source framework.
- **Crossref REST metadata:** every nonblank DOI in `references.csv` was resolved or queried against Crossref and matched to title and year. Where legacy DOI punctuation includes angle brackets, the URL is percent encoded but the DOI identity is unchanged.
- **Backward chaining:** reference lists in Chilcott (2013), Horner (2026), Jense (2025), Hardie et al. (2006), McDowall (2006) and Jolly et al. (2024/2025) were used to locate foundational and recent sources.
- **Forward/current searching:** direct searches located the 2023 Tasmanian listing statement, 2024 IFS monitoring report, 2025 Australian refuge paper, 2025 barrier and trait-risk papers, 2026 Pedder genetics paper, 2026 Australian trout community paper, 2026 fish-source framework, and the April 2026 Pedder augmentation report.

## Inclusion decisions

Included sources had at least one of these roles:

1. direct Pedder taxonomy, biology, survey chronology, recovery action, monitoring or genetics;
2. primary Australian or New Zealand evidence on trout effects, climbing galaxias interactions, habitat-dependent coexistence or demographic sinks;
3. recent synthesis or empirical evidence on barrier refuges, isolation management or threatened freshwater-fish risk; or
4. fish-specific translocation/genetic guidance needed to interpret the Oberon–Strathgordon programme.

Recent sources were not included merely because they cited Pedder. The 2026 acid-mine remediation study of *G. brevipinnis*, for example, was screened but excluded from the core set because it concerns restoration of migratory access through a chemical barrier rather than trout, Pedder decline or insurance-population management. General invasive-species, global freshwater-biodiversity and terrestrial translocation papers were excluded when a closer fish or galaxiid source was available. Methods papers on simulation, detection, extinction inference and multiple-stressor statistics were left to the parent manuscript-methods review.

## Access and evidence limits

- `local full-text transcription read` means the retained markdown/OCR surrogate was inspected; it does not guarantee fidelity to the original page. Hamr's original PDF is unavailable locally.
- `publisher full text read` means the accessible article or report was inspected beyond the abstract, at least in the sections relevant to this review.
- `abstract` means no claim was taken beyond title, abstract and bibliographic metadata.
- `metadata` means the source was used only for bibliographic or high-level contextual placement.
- Search-engine snippets were discovery aids, not final evidence. Claims in `review.md` trace to local full text, publisher content or government documents.
- No Web of Science or Scopus forward-citation export was available, so citation chasing may have missed papers whose titles/abstracts omit the searched terms.
- Grey-literature coverage is strongest for documents already staged in the repository and current official web publications; older internal IFC transfer logs and unpublished survey records remain a material gap.

## Reproducibility checks performed

- Parsed both CSV files with Python's standard `csv` module.
- Checked that keys are unique across the two files.
- Checked that each nonblank DOI resolves to the same DOI expressed in its URL after URL decoding and case normalisation.
- Verified founder-count statements against the separate Hamr, Sanger, Chilcott and Horner texts rather than treating one as canonical.
- Rechecked the Creek 2 spawning statement against the local Hamr transcription and the project erratum.
- Kept the four failed synthetic qualification gates outside the ecological evidence hierarchy: they constrain manuscript claims but do not supply a historical mechanism or probability.

