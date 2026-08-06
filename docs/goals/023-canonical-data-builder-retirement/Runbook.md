# Goal 023 Runbook

## Baseline

```bash
pwd
git branch --show-current
git rev-parse HEAD
git status --short --branch
```

Stop if the baseline is not clean `main` at
`1f46d8809761a1eae018e8683942befa941bf165` plus this untracked packet.

## Allowed Paths

- `scripts/build_evidence_ledger.py` (delete)
- `scripts/build_prior_pack.py` (delete)
- `data/README.md`
- `scripts/validate_prior_pack.py` only if a builder-only consequential
  invariant must be transferred
- one narrowly named prior-validator test only if the validator changes
- `docs/goals/023-canonical-data-builder-retirement/Log.md`

Do not edit any of the seven canonical CSVs.

## Required Evidence

Before deletion, record SHA-256 hashes for:

```text
data/source_register.csv
data/evidence_ledger.csv
data/proxy_evidence_leads.csv
data/priority_source_gaps.csv
data/parameter_priors.csv
data/model_family_parameter_map.csv
data/parameter_constraints.csv
```

Use repository searches to establish callers and references. Distinguish
active commands from historical prose; do not rewrite accepted historical
documents merely because they mention a former builder.

## Validation

```bash
uv run python scripts/validate_prior_pack.py
make fast-check
git diff --check
```

Also confirm:

- final hashes of all seven canonical CSVs exactly match the baseline receipt;
- neither deleted builder remains tracked;
- no active command or current data documentation instructs users to invoke a
  deleted builder;
- existing runtime consumers and validators still read the canonical CSVs.

Do not regenerate data tables to prove equivalence. The tracked inputs and
their hashes are the protected boundary.

## Stop Conditions

Stop and report rather than:

- deleting or modifying a canonical CSV;
- weakening a scientific invariant;
- introducing a replacement builder, archive, migration, manifest, tag, or
  compatibility path;
- extending cleanup into other builders or `review.py`;
- running remote work, simulations, or generated-output commands;
- staging, committing, or pushing.

After one focused review, make at most one material repair pass.

## Report

Report final branch, HEAD, status, exact paths, the caller/consumer finding,
baseline/final hash comparison, retained canonical flow, validation evidence,
deviations, and residual risks. Send a wake-up on completion or blockage.
