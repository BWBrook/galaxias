# Exact replay and fixed-cohort detection sensitivity

Completed 18 September 2026. All **712,000 histories at 356 frozen sources**
(2,000 histories each) were reproduced on the original Linux runtime. Every
archived field passed reconciliation; maximum absolute and relative differences
were **zero across all 61 numeric diagnostic fields**. Counts, flags, seeds and
source identities matched exactly. Source, input, membership and output hashes
were verified at closure. The analysis contains 6,052 source/profile rows.

No source was reselected. The three reference sets contain 356 sources (all
validated), 323 (union of old global cohorts), and 150 (old presence-only global
cohort), across the three original search seeds. All 153 cohort-summary rows
were checked independently for source counts, precision-qualified counts and
survival means against source summaries and frozen memberships.

## Observation sensitivity on the fixed global union

Entries below are ranges across the three search seeds of the **mean within-source
observation-weighted simulator survival through 2002**. They are not empirical
survival probabilities, source posterior weights, or a new common-model fit.
The precision column counts sources passing the prespecified likelihood-weight
MC criteria (ESS>=100, relative MC error<=.10, largest weight<=.05). Values from
poorly resolved weights remain descriptive and must not be treated as precise.

| q per model count unit | Homogeneous survival range | MC-qualified sources | Shared-quality survival range | MC-qualified sources |
|---|---:|---:|---:|---:|
| 0.005 | 0.761–0.790 | 241/323 | 0.765–0.795 | 253/323 |
| 0.02 | 0.612–0.630 | 100/323 | 0.672–0.688 | 195/323 |
| 0.05 | 0.433–0.454 | 5/323 | 0.509–0.538 | 62/323 |
| 0.2 | 0.400–0.425 | 0/323 | 0.401–0.426 | 0/323 |

Unconditional survival means on that same global union ranged from 0.682 to
0.724 across seeds. The legacy occupancy-based independent-0.98 representation
on exactly this union gave 0.400–0.425; its shared-window-0.98 representation
gave 0.544–0.548. These are observation-sensitivity comparisons on fixed
parameters and histories, not rankings of q by empirical plausibility.

Parameter selection remains consequential. In the fixed presence-only global
cohort, unconditional survival was 0.994–0.998; homogeneous q=0.005 gave
0.991–0.997 (143/150 likelihood-weight precision-qualified), while q=0.20 gave
0.880–0.900 (0/150 qualified). Reweighting that cohort does not reproduce the
near-empty histories selected by the older strong-nondetection search.

The replay shows that abundance-dependent detection changes both weighting and
Monte Carlo concentration. High q still produces severe concentration on this
old pool. It does not identify field catchability, validate historical adequacy,
or establish a necessary mechanism. The declared common-model comparison
remains unchanged. Its 14-record observation scheme includes both 1996 records;
this legacy replay has 13 records, so their absolute likelihoods are not a model
contest. Independent-quality diagnostics and every legacy profile are retained
in the full source and cohort tables; none was used to select a preferred q.

## Evidence

- `data/common_model/detection_replay_completion.json`: verified completion and
  immutable manifest hashes.
- `data/common_model/fixed_cohort_detection_comparison.csv`: all 153 cohort rows.
- `outputs/remote/detection_replay_20260918T1026/`: full compact replay, source
  comparisons, manifests and receipts, outside Git.
- Same run on deep-server under `/data/codex/scratch/galaxias/`.

The pre-dispatch kernel, serial/parallel and complete smoke evidence is recorded
in `docs/common_model_preflight.md`. This completed reconciliation satisfies
its final computational gate.
