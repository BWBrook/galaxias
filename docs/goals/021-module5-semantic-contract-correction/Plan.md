# Goal 021 Plan

1. Confirm the clean baseline and capture the exact active references to the
   detection fields and rehearsal status.
2. Add focused failing assertions for the 50-column schema, absence of the
   misleading fields, and replicate-neutral provenance.
3. Delete the detection endpoint from the active code and contract surfaces.
4. Filter only the invalid detection endpoint rows from the three compact
   summary tables; update summary metadata and direct current consumers.
5. Make execution provenance replicate-neutral without renaming the broader
   rehearsal implementation.
6. Add a concise erratum to the current internal review surface. Preserve all
   Goal 001-020 packets and frozen Goal 014 evidence.
7. Run the focused validation slice, contract validator, `make fast-check`, and
   diff/whitespace checks. Perform at most one material repair pass.
8. Leave all changes unstaged and uncommitted for Galaxias review.

## Allowed Paths

- `src/galaxias_model/module5_counterfactual.py`
- `src/galaxias_model/module5_rehearsal.py`
- `src/galaxias_model/module5_production_summary.py`
- `scripts/validate_module5_counterfactual_contract.py`
- `data/module5_counterfactual_outcome_schema.csv`
- `data/module5_production_summaries/summary_metadata.json`
- `data/module5_production_summaries/partition_endpoint_summary.csv`
- `data/module5_production_summaries/source_intervention_endpoint_summary.csv`
- `data/module5_production_summaries/direction_summary.csv`
- `data/module5_interpretation_audits/endpoint_priority_matrix.csv`
- `data/module5_results_review_design/data_dependency_matrix.csv`
- `docs/module5_production_summary_review.md`
- `docs/module5_interpretation_gate_review.md`
- `docs/module5_internal_results_review_packet.md`
- `tests/test_module5_counterfactual_contract.py`
- `tests/test_module5_production_rehearsal.py`
- `tests/test_module5_production_summary.py`
- `docs/goals/021-module5-semantic-contract-correction/Log.md`

The Goal 021 `Goal.md`, `Plan.md`, and `Runbook.md` are part of the authorised
packet but should not be edited by the action agent.
