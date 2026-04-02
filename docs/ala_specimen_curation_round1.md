# ALA Specimen Curation Round 1

## Scope

This pass used `galah-python` against the Atlas of Living Australia to download preserved-specimen records for:

- `Galaxias pedderensis` across all available ALA records
- `Galaxias brevipinnis` restricted to Tasmania
- `Galaxias parvus` restricted to Tasmania

The workflow is scripted in `scripts/curate_ala_specimens.py` and writes outputs to `data/ala/`.

## Outputs

- `data/ala/specimens_raw.csv`: 524 preserved-specimen rows
- `data/ala/specimens_curated.csv`: 524 curated rows after specimen-key checks
- `data/ala/specimens_project_relevant.csv`: Pedder-linked or unresolved rows retained for project use
- `data/ala/summary_by_taxon.csv`
- `data/ala/summary_by_institution.csv`

No duplicate specimen keys were detected in this first pass.

## Key Findings

### Pedder galaxias

- `75` preserved-specimen rows were returned for `Galaxias pedderensis`, spanning `1965` to `2022` across `6` institutions.
- `NMV` and `QVMAG` provide the clearest dated chronology for the natural range and early impoundment period.
- The `1977` boom signal is visible directly in museum lots, including `NMV A7748` from the flooded Serpentine Impoundment with an `individualCount` of `152`.
- `CSIRO ANFC` contributes modern `2022` vouchers from the `Strathgordon water supply dam`, giving independent specimen support for the insurance population.
- `TMAG` contributes many useful Pedder and Bonnet Bay lots, but a large fraction are undated in ALA and still need museum-side export or curator confirmation.

### Climbing galaxias

- `368` Tasmanian preserved-specimen rows were returned for `Galaxias brevipinnis`.
- `26` rows were classified as Pedder-linked or unresolved by locality heuristics.
- The Pedder-linked subset is dominated by `TMAG` and includes `Bonnet Bay`, `Maria Creek`, `McPartland` localities, `Sprent Basin`, `Serpentine Basin`, `Scotts Peak Dam`, `Timber Creek`, and `Strathgordon`.
- This is enough to support a museum-backed chronology for climbing-galaxias presence in the Pedder system, but not yet enough to infer abundance change on its own.

### Swamp galaxias

- `81` Tasmanian preserved-specimen rows were returned for `Galaxias parvus`.
- `71` of these were classified as Pedder-linked.
- The specimen spread is broad across the original Lake Pedder system and adjacent inflows / impoundment localities, which strengthens the case for keeping `G. parvus` in the conceptual community background.

## Important Caveats

- `TMAG` records are especially valuable but often missing `year` and `eventDate` in ALA.
- Locality-based Pedder flags are heuristic. They are useful for triage, not a substitute for direct museum-lot export.
- A small set of `G. pedderensis` records occur at `Stillwater Rivulet`, `Salmon Ponds`, and `Trappes Hill`. These are project-relevant but need curator follow-up before they are interpreted.
- One `G. brevipinnis` record from `NHMUK` has no locality in the ALA export and should remain unresolved for now.

## Next Actions

1. Add the strongest dated specimen milestones to the evidence ledger, especially the `1977` NMV lots and the `2022` Strathgordon vouchers.
2. Request direct lot-level exports from `TMAG`, `QVMAG`, `Museums Victoria`, and `ANFC`.
3. Use the curated specimen table to define a first specimen chronology figure or appendix table for the paper.
