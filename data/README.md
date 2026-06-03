# Evidence Ledger

This directory contains the first structured evidence pass for the Pedder galaxias project.

Files:

- `source_register.csv`: metadata for sources actually used in this pass.
- `evidence_ledger.csv`: direct Pedder-system evidence rows for chronology, life history, threats, translocations, monitoring, and data-service leads.
- `proxy_evidence_leads.csv`: comparative or proxy evidence that may help parameter priors or later companion analyses.
- `priority_source_gaps.csv`: missing or not-yet-retrieved sources that would materially improve the ledger.
- `calibration_targets.csv`: machine-readable historical and baseline constraints for Tier 1 model calibration.
- `parameter_priors.csv`: ABC-ready prior table for the Tier 1 simulator, with explicit source strategies, sampling transforms, and evidence links.
- `model_family_parameter_map.csv`: family-by-parameter activation table for the five Tier 1 hypothesis families.
- `parameter_constraints.csv`: biologically important joint rules and family-definition constraints that later sampling must respect.
- `module1_5_example_summary.csv`: deterministic default-run review bundle across all five Tier 1 families.
- `module1_5_stochastic_summary.csv`: twenty-seed stochastic review bundle for the `transient_perfect_storm` family.
- `module3_readiness_family_summary.csv`: tracked family-level summary from the reduced Module 3 calibration readiness run.
- `module3_readiness_accepted_summary.csv`: tracked retained-sample summary from the reduced Module 3 readiness run.
- `module4_raw_artifact_manifest.csv`: Gate 1A provenance manifest for the ignored raw Module 4 variant/seed artifacts used by Module 4.5.
- `module4_5_proposal_set_membership.csv`: proposal-level Module 4.5 membership flags for accepted, near-frontier, family-winner, and global-winner sets.
- `module4_5_distance_audit.csv`: target-sum versus stochastic-distance family-rank audit for Module 4.5.
- `module4_5_parameter_summary.csv`: parameter summaries by variant, seed, family, proposal set, and parameter.
- `module4_5_parameter_contrasts.csv`: robust effect-size contrasts among mechanism-rich families and accepted versus rejected Stage B proposals.
- `module4_5_nuisance_audit.csv`: prior-bound and fit-correlation diagnostics for `PR035`-`PR039`.
- `module4_5_target_family_summary.csv`: target-level weighted-penalty summaries by family and proposal set.
- `module4_5_pressure_landmarks.csv`: derived trout/climbing pressure summaries for biological time windows.
- `module4_5_trajectory_landmarks.csv`: deterministic landmark trajectory summaries for selected Module 4.5 proposal sets.
- `module4_5_family_decision_table.csv`: compact Module 5 ensemble decision table from the Module 4.5 audit.
- `module5_counterfactual_interventions.csv`: provisional intervention contract for Module 5 axes and role-aligned family-level designs.
- `module5_counterfactual_outcome_schema.csv`: planned output schema for matched stochastic counterfactual endpoints and contrast fields.
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
- `project_relevant_occurrence_enrichment.csv`: per-record ALA API enrichment for the project-relevant subset, including raw/processed event fields and quality flags.
- `project_relevant_metadata_gap_summary.csv`: grouped summary of what metadata remains absent online after the enrichment pass.
- `tmag_pedderensis_request_list.csv`: generated request list for the core undated TMAG `G. pedderensis` lots.

Design notes:

- I kept conflicting source claims rather than prematurely resolving them.
- `uncertainty_level` is qualitative and is meant to help triage rows for calibration use.
- `source_priority` distinguishes `primary`, `official`, `review`, `secondary`, and `data_service`.
- The ALA rows are deliberately tagged as `data_service`; they are leads for curated specimen extraction, not ready-made abundance evidence.
- The current ledger is strongest on chronology and management history, and weaker on direct quantitative demography and trout/climbing abundance time series.
- `calibration_targets.csv` is generated by `scripts/build_model_spec_pack.py`.
- `parameter_priors.csv`, `model_family_parameter_map.csv`, and `parameter_constraints.csv` are generated by `scripts/build_prior_pack.py`.
- `scripts/validate_prior_pack.py` is the authoritative schema and consistency check for the prior pack.
- `module1_5_example_summary.csv`, `module1_5_stochastic_summary.csv`, and `docs/module1_5_review.md` are generated by `scripts/review_module1_5_examples.py`.
- `data/module3_readiness_family_summary.csv`, `data/module3_readiness_accepted_summary.csv`, and `docs/module3_readiness_review.md` are generated by `scripts/review_module3_readiness.py`.
- Large Module 3 calibration outputs are written under `outputs/module3/` and are intentionally ignored by git.
- `data/module4_raw_artifact_manifest.csv` is generated by `scripts/build_module4_raw_artifact_manifest.py` from the ignored Module 4 mirror under `outputs/remote/`.
- `data/module4_5_*.csv` and `docs/module4_5_mechanism_interpretation_review.md` are generated by `scripts/run_module4_5_mechanism_interpretation.py` from the raw Module 4 artifacts indexed by `data/module4_raw_artifact_manifest.csv`.
- `data/module5_counterfactual_interventions.csv` and `data/module5_counterfactual_outcome_schema.csv` are designed as the Module 5 planning contract.
- `scripts/validate_module5_counterfactual_contract.py` validates this contract against `data/module4_5_family_decision_table.csv`.
- In the normalized pedder plate tables, blank numeric cells from the raw sheet have been interpreted as zero counts. The `G. fontanus` row is treated as a species-total row because it appears inline rather than under a separate location block.
- In the ALA curation outputs, `specimens_curated.csv` is one row per inferred specimen key, and `specimens_project_relevant.csv` keeps rows that are either directly Pedder-linked or unresolved enough to warrant follow-up rather than immediate exclusion.
- In the ALA enrichment outputs, `MISSING_COLLECTION_DATE` is taken from the ALA per-record quality flags and is a useful indicator that the date is not merely absent from the bulk download.

Immediate next steps:

1. Use `docs/module3_readiness_review.md` to decide whether the calibration harness is stable enough to support Module 4 posterior summaries and counterfactual analysis.
2. If the Module 3 readiness gate fails, route into Module 3.5 and treat the failure mode as diagnostic rather than pushing ahead.
3. Keep the TMAG metadata request alive, but do not treat the remaining museum gaps as blockers for the calibration workflow.
