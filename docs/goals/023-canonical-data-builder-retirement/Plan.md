# Goal 023 Plan

## 1. Prove The Active Path

- Inventory both builders, their seven outputs, all references, and every
  runtime or validation consumer of those outputs.
- Hash the seven tracked CSVs and preserve the baseline receipt in `Log.md`.
- Compare builder-only checks with `scripts/validate_prior_pack.py` closely
  enough to identify any consequential invariant that would otherwise vanish.

## 2. Retire Duplicate Sources Of Truth

- Delete the builders if the required audit supports the Goal decision.
- Make only the minimum documentation or validator change needed to leave one
  coherent canonical-data path.
- Do not replace deleted machinery with new preservation machinery.

## 3. Verify Once

- Confirm no active builder reference remains.
- Confirm canonical CSV hashes are unchanged.
- Run the independent prior validator and `make fast-check` once.
- Review the diff for accidental data, scientific-contract, or scope changes.

## 4. Stop

Report the retained flow, deletions, protected invariants, validation, and
material residual risk. Do not continue into other cleanup candidates.
