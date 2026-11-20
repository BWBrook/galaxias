# Terminal-history screening and confirmation

Date: 2026-09-08. State: approved tranche; design fixed before new simulations.

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

Pending. Add results only after freezing this specification and the relevant
phase selections.
