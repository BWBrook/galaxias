# Pedder galaxias MFR planning package

Prepared 4 October 2026 for Barry Brook and Chris Burridge, before the first
manuscript draft. Marine and Freshwater Research is the agreed first target.

**Status, 6 October 2026:** Barry has sent the brief to Chris, who is reviewing
it. Barry's cleaned 92-record bibliography has been imported from `wsl-laptop`
and verified locally. The bibliography handoff is complete; the first draft
awaits Chris's comments.

## Documents

- [Paper plan and paragraph-level skeleton](paper_plan_and_skeleton.md):
  argument, novelty relative to Chilcott and Horner, section contents, word
  budget, figures, tables, supplement and questions for Chris.
- [Chris's review brief](chris_review_brief.docx), with editable
  [Markdown source](chris_review_brief.md): a concise account of the complete
  proposed paper and the comments needed before drafting.
- [Literature review](literature_review.md): thematic synthesis across direct
  Pedder evidence, galaxiid ecology, historical reconstruction, detection,
  extinction inference, rescue decisions, model assessment, genetics and
  current monitoring.
- [DOI import list](dois.txt): **74 unique identifiers**, one per line, comprising
  73 journal articles and one explicitly labelled arXiv preprint.
- [Annotated reference register](reference_register.csv): the same 74 items
  with verified metadata, topic, reading priority, access depth, contribution,
  limits and publication-year notes.
- [Sources without verified DOIs](sources_without_doi.csv): **18 books, reports,
  chapters, official pages, newsletters and methodological sources** for manual
  Zotero checking. A blank DOI means no DOI was verified, not that one can
  never exist.
- [Historical evidence notes](evidence_notes.md): source locators, founder
  alternatives, survey-effort gaps and exact stopping results.
- [Search and verification record](search_log.md), with the detailed
  [ecology](search_log_ecology.md) and [methods](search_log_methods.md) queries.
- [Canonical bibliography](../../references/galaxias_bibliography.yaml):
  Barry's cleaned export, preserved byte-for-byte, with a
  [register-to-citation-key map](../../references/citation_key_map.csv) and
  [import verification receipt](../../references/import_receipt.json).

## Decisions carried into the plan

Lead with the fish, the record and the conservation response. The modelling
section reports four distinct failures to qualify an inferential procedure;
it supplies no historical causal ranking, terminal-loss probability or rescue
effect. The sequence does not prove intrinsic non-identifiability. Each
production protocol preceded its own run, with later designs responding to
earlier results; this was not formal public preregistration of the whole
programme.

Credit the recovery literature for the established breeding insurance
populations. Present founder disagreements as source-accounting questions,
Oberon's unsuccessful searches as a detection example with unmeasured exposure,
and creek spawning as an observed event with limited recruitment implications.
Include the conditional chronology argument for Chris's assessment: under a
six-year lifespan bound, the 1996 capture implies birth around 1990 or later,
approximately a decade after the last positive retained lake sweep. The dates
do not locate the nursery; fish could have used creeks, missed lake habitat
or both across life stages. Chris will also decide whether, and how, to include
the reintroduction idea he discussed informally with IFS. It remains a question
in the brief and plan, separate from the literature evidence.
Keep 2024–2026 management and genetics updates separate from the completed
historical modelling windows.

The package is a content plan and literature synthesis. Manuscript prose,
submission figures and the final consolidated event/effort table follow
Barry's and Chris's comments. The existing event registers and the evidence
notes supply the starting material. Rob Freeman's possible involvement remains
an optional discussion for Barry; no contact or authorship arrangement has
been made.

## Zotero and makedoc handoff

The DOI file is an acquisition/cross-check list, not a commitment to cite every
item. The register groups DOI items as 38 core, 22 supporting and 14 methods
references. Its `key` values are temporary review identifiers, not final
Zotero citation keys.

The follow-up adds Beven (2006), Gneiting and Raftery (2007), Cook, Gelman and
Rubin (2006), and Barry's specified thylacine paper, Brook et al. (2023), DOI
`10.1016/j.scitotenv.2023.162878`. The cleaned export also includes Caswell's
*Matrix Population Models*, second edition (2001), **ISBN 9780878930968**.
No DOI was verified for that book; do not substitute a DOI belonging to a book
review. Its details are in the sources-without-DOI register.

The canonical Better BibTeX YAML is now
`references/galaxias_bibliography.yaml` at the repository root. It contains
92 entries under a top-level `references` list: 74 DOI records and 18
additions. Every entry has matching, unique `id` and `citation-key` values.
All 92 titles and publication years match the checked registers; `issued`
dates contain only the year, with Horner retained as 2026. The Caswell edition
and ISBN and Vehtari's JMLR 25(72):1–58 details were also checked.

Use the exported citation keys for manuscript citations. The CSV key map
connects all 92 planning-register identifiers to those keys. Future manuscript
profiles should point to this one canonical bibliography through makedoc's
external-path mode. The import receipt records the source location, matching
remote/local SHA-256 hashes and validation results. The export was not edited.

Check the register's `publication_note` field during reconciliation. In
particular, Horner belongs to the 2026 volume despite online publication in
2025; Tingley is a 2021 issue paper first online in 2020; Haidvogl's source
typology is a 2014 issue paper first online in 2013. Bunnell's November 2026
issue assignment follows its September 2026 availability, which places it
within this review's cutoff. Talts is an arXiv preprint, first posted in 2018
and revised in 2020. Some publisher metadata also requires author-name or
title-markup cleanup; these are recorded in the verification notes.

The brief was built using makedoc's external-path mode. Its
`build/empty_refs.yaml` is deliberately empty and belongs only to this
uncited planning memo; it is not the manuscript bibliography.
`build/planning_style.csl` is a planning-build dependency, not approval of the
final journal reference style. The config uses paths relative to its own
directory. Rebuild from the makedoc checkout using `make docx CONFIG=` followed
by the absolute path to `manuscript/planning/build/build.yaml` in this repo.
Then, from this repository, run the following with the document workspace's
Python runtime (which supplies `python-docx`):

```sh
"$MEMO_PYTHON" manuscript/planning/build/repair_docx_layout.py \
  --input manuscript/planning/chris_review_brief.docx \
  --output manuscript/planning/chris_review_brief.docx
```

Set `MEMO_PYTHON` to the runtime returned by the workspace dependency loader.
This task-local finishing step sets explicit Letter pages, one-inch margins,
11-point body text and page numbers. It is required after a fresh makedoc
build. It changes layout only. Render the resulting DOCX again before sharing.

## Verification and limits

The DOI identities, titles and publication metadata were checked against
Crossref, DataCite and publisher records. The DOI list and CSVs were checked
for duplicates, matching membership and required fields. A separate scientific
review of the outline and brief prompted the final wording refinements. The
final three-page DOCX was rendered and every page inspected; its accessibility
audit reported no findings. PDF text-position checks confirmed one-inch top
margins on all three pages. All 33 files bound by the completed modelling
receipt retained their recorded hashes.

The 4 October follow-up received a focused independent scientific check of
the recruitment chronology. Its final wording retains the lifespan condition,
ties the decade-scale implication specifically to the 1996 fish, and allows
creek and lake habitat use within the same life history. The added reference
metadata and access depths were verified, and the revised Word brief was
rendered and inspected again. Config validation, manuscript lint and all 37
builder tests passed. The general reference audit stopped on the deliberately
empty planning bibliography. On 6 October the imported canonical bibliography
passed makedoc's reference audit with all 92 keys cited in a temporary check
document, followed by successful Pandoc citeproc processing. This verifies
bibliography compatibility; checking the eventual manuscript's citations
remains part of drafting.

The 4 October `verification.json` remains the dated package snapshot. This
README received the 6 October status and bibliography update; the brief,
paper plan and literature review retain their 4 October versions.

This is a broad narrative review with documented searches through
4 October 2026. Full text was not accessible for every item, and no exhaustive
Scopus or Web of Science search was performed. Access depth is explicit in the
register. Obtain the full article before using an abstract-only source for a
detailed claim. Original Hamr tables, late field logs and transfer ledgers
remain unresolved evidence needs.

No scientific source, frozen model result, or stopped analysis was changed for
this planning package. The first manuscript draft awaits comments.
