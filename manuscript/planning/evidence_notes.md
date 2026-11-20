# Historical record and repaired-gate evidence scout

4 October 2026. Input to manuscript planning and the Chris Burridge content brief. Mechanical extraction only; no historical inference, simulations, contact or source changes. The complete local Chilcott (2013) transcription was read, including its references.

## Locator key and source status

Locators below are **current local line numbers**, or CSV physical rows including the header. They are not printed page numbers. Source IDs retain `data/source_register.csv` identity.

| Key | Local source | Original locator and access qualification |
|---|---|---|
| H92 / SRC017 | `literature/pedder/hamr_1992_pedderensis_report.md` | Hamr (1992), IFC Occasional Report 92-01, 66 pp. (length also cited by Chilcott, line 271). Original PDF and exact printed pages are unavailable in the retained corpus. Line 7 explicitly says tables, figure pages and appendix data were mostly omitted from the narrative OCR. Table 1, Table 2 and Appendix 1 numeric cells cannot be reconstructed from this text. |
| S01 / SRC001 | `literature/pedder/Sanger_2001_CES_UTAS.md` | Sanger (2001), “Prospects and problems for the restoration of the Pedder galaxias”, proceedings pp. 125–130; exact printed page for each passage not verified from an original local PDF. The text reports a 1995 status and has an April 2001 editorial postscript. |
| C13 / SRC005 | `literature/pedder/chilcott_2013_lessons_learned_pedderensis.md` | Chilcott et al. (2013), *Marine and Freshwater Research* 64, 864–873, DOI [10.1071/MF12257](https://doi.org/10.1071/MF12257). Local transcription has no reliable printed-page breaks; section and figure locators below are usable but individual printed pages need the original article. |
| R06 / SRC003 | `literature/pedder/tasmanian_galaxiidae_recovery_plan_2006_2010.md` | Recovery Plan: Tasmanian Galaxiidae 2006–2010; Pedder section 1.1, especially 1.1.2, 1.1.4 and 1.1.7. Exact printed pages not verified locally. Current Pedder text is at lines 216–294; several older ledger locators no longer match. |
| G25 / SRC020 | `literature/pedder/2026_galaxias_pedderensis_genetics.md` | Horner et al., received/accepted in 2025 (line 5); file and removal register use 2026, source register uses 2025. Publication-year formatting needs bibliographic verification. Exact PDF pages unavailable here. |
| R97 / SRC015 | Official recovery plan, 1997 revised 1999 | [Archived DCCEEW HTML](https://www.dcceew.gov.au/environment/biodiversity/threatened/recovery-plans/pedder-swan-clarence-swamp-saddled-galaxias), section **1.1.6**, directly checked on 4 October 2026. HTML has no printed-page equivalent. |
| FUP | `docs/terminal_history_evidence_followup.md` | Retained record of an earlier bounded search and visual checks of agency newsletter scans; the current scout did not repeat those image checks. |

Within the inspected `literature/pedder` and `outputs/literature` trees, the retained original PDF is Lake (2001), at `outputs/literature/lake_2001/h-lake-inverts-11_01.pdf`. Its Figure 6 is printed p. 94 / PDF p. 8; methods are printed p. 89 / PDF p. 3. See `literature/pedder/lake_2001_retrieval_notes.md:29–58`. Absence from these local trees is not a claim that an original is unavailable elsewhere.

## Founding, removal and detection chronology

| Record | Verified content | Local support | Original locator / qualification |
|---|---|---|---|
| Captive adults, 1990–91 | Twelve adults (seven males, five females) collected for captive breeding; five died, seven survivors later released at Oberon. Artificial fertilisation separately produced eleven surviving juveniles. These groups must not be treated as twelve plus seven independent wild removals. | C13:114; `data/age_structured_design_20260929/removal_evidence.csv:2` (RM01) | C13 “Captive breeding and artificial fertilisation”; exact page unverified. |
| First dated release | **1 November 1991: 18 fish** at Oberon. The report calls them adults, then specifies nine mature males, eight mature females and one immature unsexed fish. | H92:115; removal register row 3 (RM02; its old line-113 pointer now lands on the section heading) | H92 “Recovery Actions To Date”, “Translocation”; original page unavailable. |
| February collection and release | **4 February 1992:** both Bonnet creeks intensively electrofished by two teams; one adult caught. **5 February:** twelve fish released at Oberon: this adult plus eleven captive juveniles. | H92:119,123; removal rows 4–5 (RM03–04) | H92 “Translocation” and “Monitoring”; date order is explicit. The survey is before removal of this adult, but after earlier collections. |
| Early releases, official account | **31 in 1991–92: 20 wild fish and 11 captive juveniles.** | R97 section 1.1.6, directly checked; removal row 6 (RM05) | Archived official HTML linked above. |
| Early releases, agency newsletter | **18 in late 1991 plus 13 in 1992**; first group associated with captive-program survivors. | FUP:26–44 | *On the Rise* 26(1), May 1997, printed/PDF p. 3, [“Promising news on most-endangered fish”](https://www.ifs.tas.gov.au/media/publications/IFS_Newsletter_VOL26-_NO1-_MAY1997.pdf#page=3); prior visual verification recorded in FUP. |
| Alternative early total | **42 released between November 1991 and November 1992**; composition not supplied in this passage. | S01:125; removal row 7 (RM06); `data/evidence_ledger.csv:25` (E024) | S01 recovery discussion; exact printed page unverified. |
| Later collection and release | **January 1996: four collected**, held at Strathgordon; **May 1997: three survivors released at Oberon**. Collection and release are separate events. | R97 section 1.1.6, directly checked; removal rows 8,10 (RM07,09) | Archived official HTML. No new 1997 wild collection follows from this account. |
| Later founding synthesis | **34 total, comprising 31 in 1991–92 and three in 1997.** Its opening wording describes all as collected by electrofishing, although its captive section records eleven offspring. R06 also reports 34 and inclusion of the eleven captive juveniles. | C13:114,128; R06:230,274–278; ledger row 49 (E048) | C13 “Lake Oberon”; R06 sections 1.1.2, 1.1.7. Preserve the composition inconsistency. |
| Genetics synthesis | Approximately **45 during 1991–97**, including **seven captive descendants**, citing Sanger and Chilcott. | G25:9,33; removal row 17 (RM16); ledger row 50 (E049) | Introduction; exact PDF page unverified. Seven captive descendants conflicts with H92/C13 eleven; arithmetic resemblance to 42 + 3 does not establish how the total arose. |
| First Oberon nondetection | **January 1992 visual search:** released fish not seen. | H92:127 | H92 monitoring subsection “Fish population”. Associated three-pass sampling refers to invertebrates, not three fish-detection trials. |
| Subsequent Oberon nondetections | **1993–95 backpack electrofishing** in the shallow embayment, **<10% of lake area**, detected no fish. Sanger says several revisits and no sign as at 1995. | C13:130; S01:127–129 | C13 “Lake Oberon”; S01 status is explicitly as at 1995. These are reported visits and restricted coverage, not proof of three complete years without fish. |
| Annual visit wording | Oberon had been surveyed **at least once each year since release**. This does not supply visit dates, durations or comparable detection probabilities. | R97 section 1.1.6, directly checked | Official HTML. |
| First dated post-release detection in C13 | **February 1996: one adult** in the embayment; founder versus locally recruited fish unresolved. | C13:130; ledger row 51 (E050); `data/age_structured_design_20260929/observation_register.csv:5` (OB04) | C13 “Lake Oberon”. Detection does not establish first recruitment date. |
| Recruitment confirmation | **March 1997:** ROV filmed two adults and one juvenile; diver observed a small postlarva. The May 1997 newsletter places breeding evidence in **February**, with video announced in March. | C13:130; R06:230; FUP:36–40 | C13 cites IFS unpublished data; newsletter p. 3. Month-level accounts should remain distinct until survey/video records are available. |
| Subsequent Oberon evidence | **1999:** 26 seen at night; **March 2012:** 158 in ten fyke nets over one night (48 juveniles), plus 27 electrofished in the inflow. Several-thousand population size was an inference; no quantitative abundance estimate had been conducted. | C13:130,134,136 | C13 “Lake Oberon”. Catch is not census size; fish from mixed gears should retain their separate effort. |

**Unresolved release accounting:** the two explicitly dated H92 releases total **30 = 18 + 12** through February 1992. Later accounts of 31 may include another release, but no date for that fish is established here. This is separate from the larger **31 versus 42** conflict and the **eleven versus seven captive offspring** conflict. Preserve source-specific accounts; do not silently average, sum or choose a reconciled history.

## Pedder, Bonnet Bay and the spawning correction

| Record | Verified content and limit | Local support | Original locator / missing item |
|---|---|---|---|
| Broad 1990–91 surveys | Intensive survey 12 February–1 May 1990, with additional work September 1990–May 1991; last additional site 12 March 1991. Two-person team worked upstream then downstream with Smith-Root Model 12 backpack gear (600–900 V; 60–120 Hz). | H92:27 | Methods; Table 1 and Appendix 1 should contain the missing site detail. Reported gear settings do not restore search duration or area. |
| 117-site summary | Hamr reports 117 locations; C13 dates them to 1990–91, while Sanger summarizes 117 sites across 1988–91. Only five sites produced Pedder galaxias across the broader surveys. | H92:55; C13:104; S01:70; ledger row 12 (E011) | Do not silently treat the different summary windows as identical effort. |
| Bonnet repeated visits | Creek 1 visited 21 times, Creek 2 22 times; captured fish usually returned unless retained for captive trials. Sanger reports **68 captures in 43 trips, February 1990–September 1991**. | H92:31,59; S01:72; ledger row 13 (E012); observation row 2 (OB01) | H92 Table 2 numeric cells absent. Sixty-eight captures are not documented as 68 unique individuals, and 43 visits are not equal measured exposure. |
| Stillwater repeated failures | One large adult male at the newly found Stillwater site; five subsequent electrofishing/trapping occasions produced no further Pedder galaxias. | H92:55 | Table 1 / Appendix 1; individual dates and effort absent. |
| February 1992 effort | Two teams intensively searched both creeks on 4 February and caught one adult; that fish was released at Oberon the following day. | H92:119,123; observation row 11 (OB10) | Measured duration, length, area and pass allocation absent. Two or four creek-trip equivalents in modelling are scenarios, not recovered field measurements. |
| Late aggregate catches | C13 reports only **ten individuals collected during 1992–96**. R06 reports ten Bonnet individuals under the previous plans. | C13:104; R06:228; ledger row 46 (E045); removal row 16 (RM15) | Aggregate membership, individual identities and recaptures not documented here; do not rescore dated components and aggregate as independent observations. |
| Last natural-range record | **6 March 1996**, followed by no sightings/collections despite annual electrofishing of impoundment and tributaries in good low-flow conditions until 2002. | R06:228; C13:104; ledger row 47 (E046) | R06 section 1.1.2, cites IFS unpublished data. A positive capture record does not by itself establish permanent removal of that fish. |
| Later search notices | October 1996 newsletter describes continued search; May 1997 newsletter describes surveys to obtain broodstock. Neither supplies visit dates, effort or quantitative catch records. | FUP:34–35,47–63 | [October 1996 *On the Rise* 25(2), p. 7](https://www.ifs.tas.gov.au/media/publications/IFS_Newsletter_VOL25-_NO2-_OCT1996.pdf#page=7); May 1997 26(1), p. 3. Publication dates are not new detection/nondetection events. |
| Wild spawning correction | **14 October 1991, Bonnet Creek 2: a mating pair and freshly spawned female.** The paragraph context supplies the year. | H92:67; `docs/hamr_spawning_erratum_20261004.md:3–20` | H92 references Table 2. This is a wild observation, separate from captive spawning. Verification is against the transcription, not an original page image. |
| Young fish and larvae | Small, presumed one-year-old fish found in summers 1989–90 and 1990–91; Hamr considered possible return from a lake nursery. Bi-weekly searches November 1990–January 1991 and November 1991 found no larvae/spawning sites; no larvae found in adjacent lake edges. | H92:67 | H92 life-history section, Tables 2–3 and Figure 5; no individually assigned natal habitats or two identified creek-born generations. |
| Limit of the correction | Creek spawning is supported. Natal habitat of adults, survival of this spawn, continuous lake-nursery absence after 1983 and two creek-born generations are **not established**. The correction changes no numerical output/stop rule. | Erratum:16–34 | Frozen terminal probability documents retain their original bytes; the erratum supersedes their mistaken “no wild mating pair” statement. |
| Early lake observation series | Lake Figure 6 gives a standardized sweep index with observed late zeros at plotted years corresponding to 1983, 1986 and 1989. The methods describe twelve sites/four three-minute sweeps, with a separate three-site November 1975 pilot. | `literature/pedder/lake_2001_retrieval_notes.md:39–58`; `data/age_structured_design_20260929/lake_figure6_digitised.csv:2–11` | Lake (2001) Fig. 6 printed p. 94; methods p. 89. SE label versus SD caption and time 0/0.5 mapping are unresolved. Digitized means are not raw counts, and these zeros do not establish continuous lake absence. |

## Scope of the evidence registers

- `data/source_register.csv`: **29 sources** (SRC001–SRC029; rows 2–30), mixing primary papers/reports, official summaries, comparative work and an occurrence-service snapshot. `data/evidence_ledger.csv`: **56 entries** (E001–E056; rows 2–57). These are a synthesis registry and claim ledger, not a complete trip-level dataset.
- `data/age_structured_design_20260929/removal_evidence.csv`: **16 records** (RM01–RM16; rows 2–17). `observation_register.csv`: **10 records** (OB01–OB10; rows 2–11), with explicit aggregation, effort and double-counting cautions. Neither is the original field log.
- Missing quantitative information is stated in FUP:55–63: Hamr Tables 1–2/Appendix 1, trip-level lengths/areas/durations/passes, complete late captures and removal dates, population-estimate derivations and independence of repeat visits. IFS field logbooks, especially 1992–2002, remain a named retrieval lead.
- The historical **50–200 estimate in 1992** (newsletter p. 3; FUP:30–44) has no defined wild/captive/translocated scope or estimator. The later fewer-than-50 statement (ledger E037, row 38) also lacks derivation. Different dates and unknown scope preclude a direct numerical contradiction test.
- Ledger usage text is inherited analysis framing, not independent validation. Examples: E050 calls the Oberon sequence “delayed establishment”, although the records establish delayed **detection/confirmation**; E051 infers rapid growth from a partial catch; E053 associates recruitment with habitat works. A manuscript should return to the actual observations and their limits.

## Four repaired synthetic gates: exact stops

These are the repaired age/sex programme results. Earlier invalid-kernel ranks are outside this table. Engineering qualification does not imply synthetic inferential qualification.

| Gate | Run accounting | Exact stopping result | Verified source |
|---|---|---|---|
| Linked recovery | 7,680 joint proposals / 23,040 nominal site histories; 2,055 complete, 848 algebraically infeasible, 4,777 process failures. | `STOP_BEFORE_HISTORICAL_SEARCH`. All 40 cell/index strata had at most two distinct completed extinction sources in either role; required 16 truth and eight bank sources **per terminal class**. All 4,212 base rows lacked both truth and bank coverage; classifier abstained. Endpoint discrimination unassessed; no historical fate or removal effect estimated. | `docs/age_linked_recovery_results.md:8–25,29–52,88–101`; `data/age_linked_recovery_20261001/gate_decision.json:10`; receipt line 29. |
| Lake-history-conditioned refocus | 30,720 joint / 92,160 nominal site histories; 9,740 complete, 3,544 algebraic and 17,436 process/intervention failures; 3,072 independent nuisance IDs. | `STOP_BEFORE_HISTORICAL_COMPARISON`. All 4,320 base rows unassessed. Loss-class support maxima 14 truth / seven bank before conditioning, against 16/eight required; maximum coherent support 12/seven and ESS 3.72/2.45, against 16/four. All 259,200 endpoint/profile rows unassessed. Bounded representation failure, not measured discrimination failure. | `docs/age_historical_refocus_results.md:3–40`. Its lines 105–121 also preserve uncalibrated early-survey effort and conditioning on the full later intervention chronology. |
| Final terminal probability | 1,152 assessment rows: 576 per age truncation. | `STOP_FINAL_BOUNDED_ATTEMPT`. Age six: 564 computationally unassessable, twelve computational passes with calibration too uncertain, zero qualified. Age eight: 469/107/zero. No `CALIBRATION_FAILED` row: calibration was neither established nor decisively rejected. Required precision coverage combined interval width ≤0.20, half-bank difference ≤0.05 and ≥95% target weight; twelve primary passes still had calibration upper limits 0.682–0.723 against 0.05. | `docs/age_probability_gate_results.md:3–52`. Its mistaken wild-pair statement is superseded by the erratum, not silently edited. |
| Separate early-lake mechanism recovery | 49,152 Pedder attempts, 37,992 complete, 11,160 algebraic exclusions, no runtime/process failures; 3,072 independent nuisance identities. | `STOP_EARLY_RECOVERY_UNASSESSED`. Zero of sixteen primary groups qualified: **all sixteen failed bank stability**, thirteen also lacked coverage precision. Minimum within-group set agreement 52.5–81.8% versus 90% required. Coverage point estimates 91.4–98.6%, exact lower bounds 84.5–95.5%; no decisive coverage failure. Age-eight sensitivity also failed. Actual Lake record was not scored. | `docs/early_lake_mechanism_results.md:3–14,58–96`. |

The first two stops concern insufficient independent terminal-class representation, the third computational/calibration uncertainty, and the fourth unstable restriction sets. None establishes historical causal identity, loss probability, a rescue-removal effect, or impossibility of inference in principle. The early-lake unqualified power diagnostics (R_T against R_H; R_J against R_H, lower bounds 0.510/0.532) are explicitly barred from historical interpretation in its results lines 89–96.

## Material already covered by Chilcott et al. (2013)

The existing article is a recovery-program account with substantial ecological and management synthesis. This inventory identifies overlap; it does not claim that any other proposed topic has never been studied.

| Covered material | Current local lines / original section |
|---|---|
| Original range, impoundment, environmental change, trout and climbing-galaxias arrival, trophic pulse, 1977 peak and subsequent decline; predation/competition evidence and uncertainty | C13:35–92; “The Pedder galaxias” / “Decline of the Pedder galaxias”. Figures 1–2 provide species/system context. |
| Sparse baseline knowledge, late field-survey chronology, natural-range disappearance, recovery plans and changing criteria | C13:100–110; “Field surveys”, “Recovery plans”. |
| Captive adults, deaths, artificial fertilisation and eleven offspring; limited benefits and competing demands on resources | C13:112–114; “Captive breeding and artificial fertilisation”. |
| Site-selection criteria, urgent translocation decision, Oberon founding counts, years of nondetection, adult/juvenile confirmation, monitoring methods and 2012 partial catch | C13:116–136; “Translocation”, “Lake Oberon”; Figure 3 is Oberon. |
| Serial transfers of 353 fish in five events; missing age/sex records; Strathgordon recruitment delay, 2005 and 2007 habitat works, eight juveniles in April 2008, 2012 catch, and climbing-galaxias incursions | C13:138–150; “Strathgordon water supply dam”; Figure 4 is the dam. |
| Receiving-ecosystem risks, Lake Cygnus control sampling, unanalysed samples and anecdotal shrimp/tadpole declines; incomplete quantification of impacts | C13:152–156,184–188; “Impacts of the translocations” and Discussion. |
| Redfin risk and lake-level management; ongoing monitoring and obstacles to natural-range reintroduction | C13:158–170; “Lake level management and the risk of redfin perch”, “Present conservation management”. |
| Urgency and early warning; surveillance and missing biological knowledge; acting with limited evidence; empowered recovery teams and adaptive plans; genetic bottleneck concern; restoration costs, prioritisation, proposed further population/PVA; single- versus multispecies recovery planning | C13:174–208; Discussion. Its then-unresolved genetics questions must be distinguished from subsequent Horner work. |

The article explicitly makes the recovery-success/averted-extinction argument (C13:15,178,208). A new manuscript cannot present that narrative, the translocation chronology, or the value of decisive recovery action as newly discovered by this modelling programme. Whether the current repaired-gate evidence supports a distinct scientific contribution is a manuscript-level decision for the parent and Barry.

## Conditional recruitment chronology added after review

4 October 2026 follow-up: the following is an explicit argument from the
record and a lifespan assumption, separate from the mechanical extraction
above. Barry requested its inclusion for Chris's biological assessment.

Lake Figure 6 (printed p. 94; digitised register row 8) has its last positive
retained sweep in **1980**. The retained later visits are **1983, 1986 and
1989**, each zero (rows 9–11). The 2006 recovery plan, section 1.1.2, reports
the final natural-range capture on **6 March 1996**. Those records do not
represent uninterrupted annual lake sampling or establish continuous absence.

Conditional on an upper lifespan of six years, birth must be no earlier than
approximately capture year minus six. Thus fish caught from 1990 onwards
postdate the 1980 positive sweep, and the 1996 fish implies birth around
1990 or later. Under that bound, the 1996 fish supports recruitment
approximately a decade after the last positive retained sweep. It does not identify the
natal habitat, demonstrate continuous annual breeding, or prove successful
recruitment from the particular 1991 spawning event. Fish could have developed
in creeks, lake habitat missed by the surveys, or used both across life stages;
creek spawning and lake nursery use need not be mutually exclusive.

The lifespan bound is an assumption requiring review, not a precisely
established maximum. Hamr's retained life-history section (H92:67) describes
limited otolith observations and proposes maximum size at five to six years;
the report also records small presumed one-year-old fish in 1989–90 and
1990–91 and considers their possible return from a lake nursery. The model's
age-six primary and age-eight sensitivity settings do not independently
validate the six-year bound. Even an eight-year bound would put a 1996 fish's
birth around 1988 or later, still after the last positive sweep, but it would
weaken the decade-length statement. No new simulation or historical fit is
needed for this arithmetic implication.
