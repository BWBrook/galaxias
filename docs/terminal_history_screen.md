# Terminal-history screening and confirmation

Date: 2026-09-08. State: complete; use stochastic screening for further
calibration, with observation and precision qualifications retained.

Barry approved the next screening tranche and requested a larger, coherent
reporting horizon under the Twilight Laboratory workflow. This tranche includes
screening, independent confirmation, bounded targeted replication, empirical
follow-up and a scientific decision. The preceding
[observation-repair pilot](observation_repair_pilot.md) remains an immutable
comparison with its own source and result bindings.

## Question and scientific boundary

Does the existing parameter pool contain late histories missed by deterministic
screening, and do the resulting observation-compatibility estimates support a
stable interpretation after independent process replication?

The pool is exactly the preceding pilot's 1,000 sources: 100 proposals in each
of five families under search seeds 20260908 and 20260909. No new parameter
draws, changed priors, demographic equations, removal forcing, observation
assumptions, detection choices or block weights enter this comparison.
The three repair profiles remain presence only, detection 0.60 and detection
0.98. The original scoring is computed as a diagnostic, without promoting a
new production ensemble or running intervention endpoints.

The closing criterion is a verified, independently evaluated comparison of the
screening routes and a clear statement of what terminal-history support exists
within this pool. A preferred family, lower survival or a particular historical
fit is not an acceptance criterion. Neither nonselection nor zero observed
events proves that a mechanism or the wider prior cannot produce such histories.

## Fixed staged design

1. **Stochastic screen:** run 50 new stochastic histories at all 1,000 original
   parameter sources. Reuse their deterministic intrinsic scores. All repair
   profiles receive the same histories and original parameter values.
2. **Paired screening-route comparison:** within each seed/profile, select the
   best ten finite sources from (a) the full 500-source pool and (b) the original
   profile-specific deterministic Stage A set of 100 sources. Both routes use
   the same new 50-history score. Ten is a fixed comparison size; applying 10%
   separately to unequal pools would confound screening with ensemble size.
   Preserve the existing overall/historical/intrinsic/historical-IQR/proposal-ID
   ordering. A route with fewer than ten finite sources retains all available
   sources and discloses that denominator.
3. **Family diagnostics:** select the best one finite source per family under
   each route, seed and repair profile using the same score ordering. These
   candidates support family-level comparison even when global selection omits
   a family. They are diagnostic representatives, not family probabilities.
   Also retain the source with the largest screening frequency of positive-
   compatible extinction by end-2002 in each seed/family where any such event
   occurred. Break ties by proposal ID. These at most ten representatives test
   terminal-event support even if composite-score selection omits it.
4. **Independent confirmation:** freeze the union of those candidates and all
   55 distinct sources selected in the preceding pilot. Run 500 new histories
   at each, without reselection. At most 245 distinct sources require this
   phase: 120 global-route slots, 60 family-route slots, ten terminal-event
   representatives and 55 prior sources;
   overlaps reduce the actual number.
5. **Targeted precision extension:** from the confirmation results, flag a
   source if any repaired-profile calculation has ESS below ten, largest
   compatibility contribution above 20%, or no positive-compatible history.
   Extend at most 40 distinct sources by exactly 2,000 fresh histories each.
   Prioritise no sampled positive support first, then the largest Monte Carlo
   relative standard error across repaired profiles, with ascending search seed,
   family ID and proposal ID breaking ties. Freeze the extension list before
   generating its histories. There is one extension batch, no sequential
   stopping within it and no change to selection.
6. **Synthesis and evidence follow-up:** assess screening omissions, independent
   score changes, terminal-event support and remaining precision limits, and
   reconcile newly accessible survey/removal evidence without silently changing
   the model. Independent review checks central calculations and interpretation.

New seed namespaces are 601 (screen), 701 (confirmation) and 809 (extension),
passed through the existing source/replicate seed derivation. They are checked
for collisions with each other and the original pilot's 202/409 namespaces.
Independence is between stochastic realizations at the same selected parameter
points. This is not independent field evidence or validation at unseen parameters.

The maximum new compute is 252,500 historical simulations: 50,000 screen,
122,500 confirmation and 80,000 extension. Use at most 16 workers on deep-server
with numerical-library threads fixed to one. Preflight found about 112 GiB
available RAM and load around 12 on 64 logical CPUs. Barry also authorized a
separate Nectar 3XL instance if competing work constrains deep-server; an
existing unrelated job is not to be displaced. Small local tests and a remote
smoke precede the full screen. Source and raw payloads stay under the existing
Nectar control-plane placement conventions.

## Measurements and interpretation

Repaired scores retain the earlier source-level calculation:

```text
L_r = I(all dated positive records compatible) * (1-p)^K_r
D_total = median(early-target + intrinsic penalties) - 5*log(mean L_r)
```

The primary comparisons use the uniformly sampled 500-history confirmation
phase. Report source-equal context means, source-level distributions, family
composition, route overlap, and how many newly selected sources were outside
the original deterministic screen. Preserve each seed and detection profile.
For the same source, paired routes share exactly the same confirmation histories.
Source overlap reduces independence; do not count repeated selections as new
parameter sources or average detection profiles into one scientific ensemble.

Report both unconditional physical summaries and within-source compatibility-
weighted histories. The latter condition simulated processes on the stated
observation assumptions and then weight parameter sources equally. They are
not posterior model or parameter probabilities. Zero sampled support produces
missing conditional summaries with denominators disclosed; no numerical floor
creates support. Original-control compatibility diagnostics remain presence-only
diagnostics rather than an asserted original observation likelihood.

Terminal-event diagnostics include (a) all dated positive records compatible
and extinction by the end of 2002 and (b) all positive records compatible and
all five natural-domain nondetection episodes empty. Also report positive
compatibility with all seven nondetection proxies empty. These distinguish known
presence followed by loss from death before the last record. Neither event is
required by nondetection: continued presence with missed detection remains
permitted. Report first zero only when observed, and right-censor histories
still present at the simulation endpoint. Do not invent extinction in 2003.

For fixed-source event frequencies, report counts and pointwise 95% binomial
intervals; a zero count has a one-sided 95% upper bound
`1 - 0.05^(1/n)`. This is about process Monte Carlo resolution, not biological
plausibility or a multiple-comparison discovery threshold. In particular,
zero events among 500 histories only bounds that event's probability at about
0.006 for that parameter source under the current simulator.

ESS, largest contribution and relative standard error diagnose observed weight
concentration. High ESS cannot certify convergence when a rarer, much more
compatible low-K history has not yet appeared. This matters especially at
detection 0.98, where successive occupied-episode counts differ in weight by
a factor of 50. The extension addresses observed instability, not unseen-tail
certification. Report initial confirmation, extension-only and pooled estimates
separately. Pooled estimates use a budget chosen after initial confirmation
and are sensitivity estimates; they do not replace the uniform confirmation
comparison or provide an unbiased adaptive-stopping guarantee.

## Reproducibility and review surfaces

Preserve the exact pre-run specification, parameter/input/source bindings,
phase manifests, frozen selection memberships, raw replicate summaries and a
compact analysis receipt. Existing pilot files are read-only. Use the existing
scoring, observation projection and analysis functions where their contracts
fit; avoid a parallel calibration framework.

The deliverables are one scientific report, compact source and context tables,
a diagnostic plot if useful, the empirical follow-up, and an updated current
handover. Complete central independent review and meaningful tests. Commit,
push, publication, production calibration, new assumptions and endpoint replay
are outside this authorized tranche.

## Execution and findings

**Decision: GO with stochastic screening for further calibration.** The
deterministic screen discarded parameter sets that independently reproduce
dated presence followed by terminal loss. This is a demonstrated screening
limitation within the existing pool. It does not establish historical adequacy,
a preferred detection probability or a new mechanism-family hierarchy.

The exact [pre-run specification](../data/terminal_history_screen/specification_before_run.md)
has SHA-256
`38e3d95735b09551d3126a3b8ff0c4cdc34e41bdbaa26f5b775e759c3fb33da5`.
The sections above preserve the design; the findings below were added after
execution. The confirmation and extension source lists were frozen before their
respective simulations and were not changed after inspecting those results.

### Screening loss and independent confirmation

The all-pool screen contained 637 histories that satisfied every positive
record and subsequently went extinct by end-2002. These occurred at 138 of the
1,000 parameter sets; **121 of those sets lay outside the repaired deterministic
Stage A set**. Ninety-four sources generated 206 histories satisfying the
positive records with all five natural-range nondetection episodes empty.
No screened history satisfied the positives with all seven nondetection
episodes empty. These counts are conditional simulator results, not estimates
of historical extinction frequency.

Ninety distinct sources entered independent confirmation. Among their 45,000
new histories, 2,261 satisfied the positives and went extinct by end-2002,
distributed across 48 parameter sets. Twenty-eight of those parameter sets
were outside the repaired deterministic screen. All nine representatives
selected for their terminal-event frequency reproduced that event during
confirmation. The upper-stage screen therefore missed more than isolated
single-history accidents.

The route comparison below uses exactly ten selected sources per seed/profile
and 500 independent histories per source. Lower composite discrepancy is better
under the stated scoring formulation; values across detection profiles are not
absolute-fit comparisons. The last column is the full-route fraction of all
histories that both satisfy the positives and end extinct, averaged equally
over parameter sources.

| Seed | Detection | Full-route sources outside Stage A | Full / restricted composite discrepancy | Full / restricted late discrepancy | Full-route positive-compatible terminal loss |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20260908 | 0.60 | 4/10 | 36.12 / 37.56 | 5.40 / 6.18 | 8.60% |
| 20260909 | 0.60 | 1/10 | 34.13 / 33.98 | 5.15 / 5.38 | 8.42% |
| 20260908 | 0.98 | 8/10 | 65.76 / 100.53 | 9.72 / 17.90 | 13.38% |
| 20260909 | 0.98 | 6/10 | 58.95 / 59.98 | 8.35 / 10.11 | 14.80% |

Presence-only selections were identical between routes in both seeds. Their
confirmation composite discrepancies were 5.23 and 5.01. The full route improved
late compatibility in all four nonzero-detection comparisons, but improvement
in the full composite was not uniform: the weaker-detection second seed was
slightly worse. The broader search can find better late histories while trading
away early fit or positive-record probability.

That trade-off is substantial under detection 0.98. Mean positive-compatible
fractions were 59.44% and 46.14% for the full route, versus 87.06% and 73.52%
for the restricted route. Mean early-target discrepancies rose from 6.04 to
11.77 and from 4.83 to 11.74. These are reasons to retain the score decomposition,
not to describe selection alone as historical adequacy.

### Terminal histories across mechanism families

The event representatives were chosen on the screening results and then tested
on new process histories. Their confirmation counts were:

| Family | Seed 20260908: positive-compatible terminal losses /500 | Seed 20260909: positive-compatible terminal losses /500 |
| --- | ---: | ---: |
| Climbing only | 85 (17.0%) | 205 (41.0%) |
| Persistent joint cause | 156 (31.2%) | 177 (35.4%) |
| Transient perfect storm | 106 (21.2%) | 75 (15.0%) |
| Habitat only | 2 (0.4%) | No terminal-event representative selected |
| Trout only | 11 (2.2%) | 8 (1.6%) |

For example, the fixed-source 95% Wilson interval for the 31.2% persistent-joint
event frequency is 27.3–35.4%; for the 41.0% climbing-only frequency it is
36.8–45.4%. The small habitat/trout counts demonstrate sampled event support,
not an adequate fit to the full history. Their best screened composite-score
representatives under detection 0.98 had confirmation discrepancies about
214–238, compared with about 44–64 for the other families. Those representatives
are neither exhaustive family optima nor model probabilities.

Full-route global family counts also changed with observation assumptions. In
climbing / persistent-joint / transient order, the counts were 0/6/4 and 3/4/3
under detection 0.60, and 2/4/4 and 5/3/2 under detection 0.98. Neither habitat-only
nor trout-only entered these global top tens. This supports retaining competing
mechanisms in subsequent calibration; it does not reinstate the previous
production hierarchy or identify a new universal winner.

### Conditional survival and the precision extension

At detection 0.98, the full-route unconditional survival fractions were 49.7%
and 34.4%. After weighting histories by observation compatibility within each
source, survival was only `1.62 × 10⁻⁶` and `5.58 × 10⁻⁸`. These very small
conditional values describe the declared observation scenario. A history
surviving all five later survey proxies incurs a nondetection factor
`0.02^5 = 3.2 × 10⁻⁹` before the lake episodes. Histories losing fish after the
positive records consequently receive vastly greater relative weight.
This is not independent evidence of almost-certain real-world extinction.

In particular, only 13.38% and 14.80% of all full-route histories both met the
positive conditions and went extinct by end-2002; many other deaths occurred
too early. Normalized conditional survival must be read beside that event
frequency, the positive-compatible fraction and the absolute joint compatibility.

Thirty of the 90 confirmed sources triggered the extension rule; none had zero
positive support. All thirty received the extra 2,000 histories, so the cap did
not exclude a flagged source. The extension produced 60,000 fresh histories.
The uniformly sampled 500-history comparison remains primary. The sensitivity
table below substitutes pooled 2,500-history estimates at extended sources
and retains the original 500 at the others, with all selections unchanged.

| Seed | Detection | Full / restricted composite after pooled substitution | Full / restricted sources with ESS <10: initial → pooled substitution |
| --- | ---: | ---: | ---: |
| 20260908 | 0.60 | 36.04 / 37.13 | 0/0 → 0/0 |
| 20260909 | 0.60 | 34.23 / 34.08 | 1/1 → 0/0 |
| 20260908 | 0.98 | 63.75 / 95.08 | 5/6 → 1/4 |
| 20260909 | 0.98 | 57.82 / 59.87 | 5/8 → 2/4 |

The direction of every route comparison survived the extension. The weaker
second-seed full route remained slightly worse overall. Full-route conditional
survival under detection 0.60 was about 54.6% and 32.2% after substitution;
under 0.98 it remained extremely small (`2.33 × 10⁻⁷`, `5.11 × 10⁻⁸`). These
mixed-budget summaries have the prespecified adaptive-budget qualification.
Extension-only substitution is separately recorded and supports the same
qualitative comparison.

Across all thirty extended sources, 17 still had ESS below ten under detection
0.98 after pooling, and 13 still assigned over 20% of weight to one history.
The corresponding detection-0.60 warnings were zero. Thus more replication
improved observed precision without making every strongly conditioned source
stable. High ESS remains insufficient to exclude unseen rare histories.

The previously unseen all-seven-empty event illustrates the issue. It appeared
once in the initial confirmation at seed 20260908,
`transient_perfect_storm:p00074`, and once more in its extension. Two other sources
each produced it once during extension. For `p00074`, the high-detection ESS
increased from 2.44 to 11.49 after pooling, but the largest contribution was
still 20.6%. Its pooled positive-compatible terminal-loss frequency was
540/2,500, while only two histories explained every nondetection through empty
domains. Sampling these different events has very different precision demands.

### Empirical update and scientific disposition

The [evidence follow-up](terminal_history_evidence_followup.md) recovered a
contemporaneous agency account reporting a rough **50–200 fish estimate for
1992**, 18 releases into Oberon in 1991 and 13 in 1992, and continuing searches.
The estimate has no supplied derivation or clearly defined population scope;
release dates do not reconstruct wild removal dates.
[Source: May 1997 IFC newsletter, p. 3](https://www.ifs.tas.gov.au/media/publications/IFS_Newsletter_VOL26-_NO1-_MAY1997.pdf#page=3).
Neither comparable survey exposure, detection probability nor a complete
natural-range removal schedule was recovered. No scientific inputs were changed.

The defensible conclusion is that **deterministic screening was excluding useful
stochastic terminal histories**. The current model/pool can reproduce positive
records followed by loss, and that support is not confined to one mechanism
family. Which of those histories is favoured remains strongly dependent on
observation assumptions and on the trade-off against earlier patterns.

The recommended next programme is a larger **conditional calibration and
mechanism comparison**, beginning with a scientific decision on the defensible
observation and removal assumptions, then carrying that design through stochastic
calibration and independent process evaluation across all five families. Keep
the two current detection scenarios as comparators and preserve explicit
rare-history diagnostics. Evaluate the full historical pattern before promoting
ensembles to matched counterfactual analysis. Detection 0.98 should remain a
sensitivity scenario, not become the main formulation because it produces
terminal extinction. More generic replication is not the next priority. The
retrieved records do not settle the empirical assumptions, and new production
calibration or endpoint replay is outside this completed tranche.

### Execution, verification and reproduction

All three phases completed on deep-server with 16 workers and exit code zero:
50,000 screen, 45,000 confirmation and 60,000 extension histories, **155,000 in
total**. Phase runtimes were 158.625, 145.063 and 198.671 seconds (about 8.4 minutes
of execution in total). No deterministic reruns or new parameter draws were
needed. Deep-server retained capacity; no additional Nectar instance was created.

The source snapshot comprises commit
`81e37202f6322e37ac7f1b0070402b76b7967a82` plus the hashed working overlay.
The locked remote runtime used Python 3.14.5, NumPy 2.4.6 and pandas 2.3.3.
The full local project check passed 129 tests; seven focused tests and the
two-worker smoke passed remotely. All phase output hashes, source/input ancestry,
exact parameter identities, planned seed namespaces and frozen selection files
were verified. Independent raw-history review checked the central event counts,
route comparisons and precision interpretation. The production observation
bridge, priors, demographic kernel and previous Module 4/5 results are unchanged.

Compact review surfaces under `data/terminal_history_screen/` are:

- [route_summary.csv](../data/terminal_history_screen/route_summary.csv): primary
  screen/confirmation comparisons and explicitly labelled extension-only and
  pooled substitution sensitivities, with source and replicate denominators;
- [source_metrics.csv](../data/terminal_history_screen/source_metrics.csv):
  scores, physical summaries, event counts, fixed-phase binomial intervals and
  weight diagnostics, keeping pooled adaptive results distinct;
- [screen_family_support.csv](../data/terminal_history_screen/screen_family_support.csv)
  and [route_overlap.csv](../data/terminal_history_screen/route_overlap.csv):
  prior-pool event support and screening omissions;
- [selection_membership.csv](../data/terminal_history_screen/selection_membership.csv),
  [confirmation_candidates.csv](../data/terminal_history_screen/confirmation_candidates.csv),
  [extension_priority.csv](../data/terminal_history_screen/extension_priority.csv)
  and [extension_candidates.csv](../data/terminal_history_screen/extension_candidates.csv):
  the frozen phase selections;
- [receipt.json](../data/terminal_history_screen/receipt.json): analysis and
  output bindings, with phase manifests linking back to the original pilot.

The local ignored raw archive is
`outputs/remote/terminal_history_screen_20260908T012648Z/`.
Remote payloads and launch receipts remain under
`/data/codex/scratch/galaxias/terminal_history_screen_20260908T012648Z/` and the
isolated source under
`/data/codex/repos/galaxias-terminal-history-20260908T012648Z/`.

```sh
uv run --locked python scripts/analyze_terminal_history_screen.py \
  --screen-dir outputs/remote/terminal_history_screen_20260908T012648Z/screen \
  --pilot-dir outputs/remote/observation_repair_pilot_20260908T004649Z/pilot \
  --output-dir data/terminal_history_screen \
  --confirm-dir outputs/remote/terminal_history_screen_20260908T012648Z/confirm \
  --extend-dir outputs/remote/terminal_history_screen_20260908T012648Z/extend
```
