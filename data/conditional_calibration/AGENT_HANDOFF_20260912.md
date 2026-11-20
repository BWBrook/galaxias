# Galaxias Successor Handover

Updated: 2026-09-12

This is the compact starting point for a new Galaxias agent. It supersedes the
June 2026 handover that previously occupied this file. It records the current
scientific state and the live discussion boundary, not a chronology of all 27
goal packets.

## Start Here

1. Read `AGENTS.md` and this file.
2. Confirm `pwd`, `git status --short --branch`, `git rev-parse HEAD`, and the
   current remote relationship before changing anything.
3. Read the small current-state set under **Essential Reading** below.
4. Use `/Users/bwbrook/.codex/skills/twilight-laboratory/SKILL.md` as the
   primary collaboration workflow for substantial scientific work.
5. Use `/Users/bwbrook/.codex/skills/kill-your-darlings/SKILL.md` when auditing
   or simplifying the codebase. Do not recreate retired machinery merely to
   preserve history.

Successor orientation verified a clean `main`, matching the live `origin/main`,
at `f5595e14859a73b5fe3d17b5f29e3b7a997c8347` (the committed handover).
Subsequent code simplification is described under **Lean-Code State**; inspect
the live working tree before changing anything.

Barry intends to launch the successor directly in this repository. Derive the
authority for edits, compute, commits, and publication from his current request
and the applicable instructions. Do not assume the old `pedder`, Chief of Staff,
or one-numbered-goal-per-step workflow remains the operating model.

## Completed programme: conditional calibration

Barry approved proceeding autonomously from the completed terminal-history
screen to a larger conditional calibration. The frozen design is
`docs/conditional_calibration.md`: 7,500 fresh sources across all five families,
100 screening histories, 500 refinement histories, and 2,000 independent
validation histories at frozen final sources. Five profiles cover presence
only, two detection levels, and independent versus shared-window detection.
Conservation extraction remains explicitly unmodelled. Weight-one family
diagnostics accompany the primary weight-five score.

The programme launched on deep-server on 2026-09-12 under
`/data/codex/scratch/galaxias/conditional_calibration_20260912T034910Z/`, from
`/data/codex/repos/galaxias-conditional-20260912T034910Z/`, with 32 workers.
Inspect `current_step.txt`, exit receipts and phase manifests before interpreting
completion. The local mirror is the corresponding ignored `outputs/remote/`
directory. Local `make check` passed 137 tests; the target-host eight-test check
and two-worker smoke passed. The full conservative 19.5-million-seed domain
passed collision checks against earlier process and parameter-draw seeds.
All phases completed and their archives, summary calculations and membership
ancestry were verified. The realized programme used 750,000 screening, 318,000
refinement and 712,000 validation histories (1,780,000 total), plus 15,000
intrinsic runs. Read `docs/conditional_calibration_results.md` and the compact
`data/conditional_calibration/` evidence and figure. The fixed diagnostic
tranche is complete; historical adequacy and production-ensemble promotion
have not been established.

An independently checked interpretation issue is already decisive: these
families remove invasive-taxon states/forcing together with their demographic
effects. CT005 therefore imposes at least 64.76 weighted penalty units on
`trout_only` and `habitat_only_null` because climbing galaxias is absent. CT004
imposes fixed floors of 5 on trout-absent families and 5/3 on the persistent
joint formulation because it requires a later piscivory increase. Family
ranking is partly structural target compatibility, not a nested test of causal
effects. Preserve the frozen run; expose target contributions and consider a
future design that keeps known species/forcing while switching off their
demographic effects. Do not silently redesign the model during this tranche.

Observation sensitivity also depends on source selection. At the fixed union
of global sources, validation survival under independent 0.98 detection is
0.400–0.425 across search seeds, versus 0.544–0.548 under shared-window 0.98.
The near-zero estimate at the independent-0.98 profile's own selected sources
therefore combines parameter selection and history weighting. None of that
profile's 150 global sources passes the planned mean-compatibility precision
flag. These are conditional simulator summaries, not empirical extinction
probabilities. The next scientific decision is a nested demographic-effect
comparison with known invasive species retained; further calibration needs
that formulation settled first. Conservation removal forcing remains unresolved.

## Scientific Purpose

The project asks which mechanistic histories can plausibly reproduce the sparse
known history of Pedder galaxias (`Galaxias pedderensis`) and what conditional
counterfactuals say about habitat change, trout pressure, and climbing-galaxias
pressure.

The epistemic stance is essential:

- this is scenario analysis and pattern-oriented plausibility filtering;
- sparse, opportunistic observations are anchors, not precise calibration data;
- retained or "accepted" proposals are plausible parameterisations, not
  posterior samples or estimates of model probability;
- eliminating large regions of implausible model and parameter space is itself
  a useful result;
- counterfactual effects are conditional on retained model histories, not
  automatically real-world attributable fractions or proof of causation.

Barry wants an assertive senior-researcher collaborator: make reversible
technical decisions, challenge weak interpretations, and reserve his attention
for choices that can change the science, claims, direction, compute envelope,
or publication posture. Work to a coherent scientific gold stamp rather than
returning for approval after every internal stage.

## What The Modules Established

- **Module 1:** assembled the evidence, priors, mechanism families, scenarios,
  and explicit historical anchors.
- **Module 1.5:** checked the latent demographic kernel and historical
  chronology. Its old report generator has since been deleted; direct tests and
  its retained canonical regression checkpoints preserve the useful protection.
- **Module 2:** mapped latent trajectories to imperfect observations and scored
  targets. Treat this as a plausibility filter, not a likelihood analysis.
- **Module 2.5:** checked intrinsic population/scenario behaviour against the
  Lake Oberon and Strathgordon baseline scenarios.
- **Module 3:** implemented two-stage ABC/history matching to retain plausible
  parameterisations.
- **Module 3.5:** exposed target leverage and target-omission sensitivity.
  Family ranking is not independent of the late-history targets.
- **Module 3.75:** isolated three consequential observation-bridge judgements:
  1990-1991 occupancy versus capture counts (`CT007`), the 1996 last record
  (`CT009`), and 1998-2002 nondetections (`CT010`).
- **Module 4:** reran calibration over five observation formulations and three
  stochastic search seeds, giving 15 variant-by-seed contexts.
- **Module 4.5:** audited mechanism coherence and established the family
  hierarchy used in Module 5.
- **Module 5:** ran matched stochastic pressure-removal counterfactuals,
  inspected production outputs, built compact internal review evidence, audited
  Monte Carlo stability, and finally ran a fully shared four-arm 250-replicate
  interaction experiment.

## Family Interpretation Before The Observation Audit

The 2026-09-08 historical-fit audit qualifies the use of this hierarchy. It is
the result under the original scoring assumptions; historical adequacy remains
unestablished. Read the current audit below before extending ecological claims.

Module 4 results:

- `persistent_joint_cause` won 12 of 15 variant-by-seed searches, including all
  strict-baseline and combined-soft runs;
- `climbing_only` won 3 runs under single-axis observation relaxations;
- `transient_perfect_storm` remained well represented among retained plausible
  proposals without winning target-sum rank;
- `habitat_only_null` and `trout_only` had no accepted-frontier support.

The agreed hierarchy is therefore:

- **primary:** `persistent_joint_cause`;
- **sensitivity / narrower alternatives:** `transient_perfect_storm` and
  `climbing_only` where its intervention structure is relevant;
- **negative-reference or diagnostic only:** `habitat_only_null` and
  `trout_only`.

Do not turn winner counts or accepted-proposal counts into probabilities that a
family is true. The joint family is also the most flexible family, although its
ability to fit when restrictive alternatives fail remains scientifically
informative.

## Module 5 Evidence Now In Hand

Goal 014 executed the earlier 100-replicate production counterfactual. Goals
015-020 reduced its remote raw result to checked compact summaries and an
internal, non-display review packet. Goal 021 removed three mislabeled
`detection_summary_*` fields from the active contract: those immutable Goal 014
raw fields were only `N_total(2002) * 0.01`, not a genuine observation-model
projection.

Goal 026 found that 100 replicates were adequate for family means but that the
original intervention-specific random streams were not the cleanest basis for
factorial interaction. Goal 027 therefore ran one status-quo arm plus trout
removed, climbing removed, and both removed from a common starting seed for
every source-replicate block.

Goal 027 facts:

- 265 `persistent_joint_cause` and 250 `transient_perfect_storm` proposal
  sources across the 15 Module 4 contexts;
- 250 replicates, 128,750 source-replicate blocks, and 515,000 arm simulations;
- all 21 structural and scientific QC checks passed;
- 128,750 distinct block seeds with no collision;
- family-level estimates were stable by 250 replicates, so **do not run 500 or
  1,000 replicates without a new scientific reason**;
- equal starting seeds are a common-seed coupling, not guaranteed event-level
  common shocks after state-dependent trajectories diverge.

The robust family-level pattern is response-scale dependent:

- every pressure-removal contrast is favourable on all three current endpoint
  scales;
- persistence-to-2002 interaction is less than additive in all 15 contexts for
  both families, consistent with overlap or saturation on a bounded endpoint;
- minimum-abundance interaction is more than additive in all 15 contexts for
  both families;
- lake/refuge-share interaction is near additive or unresolved at family level
  and heterogeneous among contexts;
- the transient-family lake/refuge source-class proportions remain sensitive to
  an arbitrary near-zero threshold, although the continuous family estimate is
  stable. Avoid a categorical prevalence claim there.

Do not collapse these results into an unqualified claim that the pressures are
"synergistic". Name the response scale and keep model-conditional effects
separate from ecological causal claims.

## Endpoint Decisions From The Current Barry Review

Barry and the outgoing agent began a skeptical, supervisor-style review after
Goal 027. These points are agreed but not yet formalized in a new analysis:

- the broader course of population degradation and viability is the main
  scientific story;
- persistence to 2002 remains a lead historical guardrail, but cannot carry the
  mechanistic interpretation alone;
- minimum abundance and lake/refuge use remain supporting endpoints;
- extinction timing is a promising additional endpoint and should be treated as
  right-censored through 2002, not by pretending that a run alive in 2002 went
  extinct in 2003;
- quasi-extinction is a secondary robustness endpoint only;
- no defensible absolute abundance or minimum-viable-population threshold is
  known from the assembled evidence;
- if quasi-extinction is pursued, the agreed pragmatic design is to test 5%,
  10%, and 20% of each parameterisation's simulated 1965-1971 median reference
  abundance, requiring two consecutive years below threshold and using the
  same reference across its four matched arms;
- describe those as model-relative low-abundance thresholds, never as known
  fish counts or empirical viability thresholds.

Extinction timing can probably be audited from existing matched output.
Quasi-extinction requires replaying trajectories with the frozen sources and
seeds because annual abundance trajectories were not retained in the compact
Git evidence. No such replay has been authorized or run.

## Current Observation Audit And Next Decision

Barry approved a historical-fit and observation-model audit on 2026-09-08.
It is complete in `docs/historical_fit_observation_audit.md`, with reproducible
summaries under `data/historical_fit_observation_audit/` and an archive-only
analysis script. The audit used the existing local Module 4 artifacts, verified
60 raw file bindings and 1.8 million Stage B target rows, and reproduced all
original acceptance sets. Full project checks passed (108 tests).

The audit treats the 15 Module 4 contexts separately.
They are five observation formulations crossed with three stochastic search
seeds, not 15 equally distinct ecological beliefs:

| Role | Variant | Main assumption |
| --- | --- | --- |
| strict reference | `baseline_current` | 50:50 nominal CT007 occupancy/count weights; exact 1996 endpoint; original detection bridge |
| single-axis diagnostic | `ct007_occupancy_primary` | 75:25 nominal occupancy/count weights |
| single-axis diagnostic | `ct009_terminal_window_gap3` | 1992-1996 terminal window with softer late penalty |
| single-axis diagnostic | `ct010_detection_half` | half the expected detections for the nondetection window |
| combined-soft reference | `late_bridge_soft` | combines all three softer late-observation choices |

The three seeds test search repeatability within each formulation. They should
not be narrated as three additional ecological assumptions.

Baseline and combined-soft served as reference bookends; neither was privileged.
The audit recommendation is **REPAIR the observation bridge before extending
historical-adequacy claims or endpoint analyses**. Different survey exposures,
count-derived occupancy, last detection versus latent presence, and
proposal-specific PR037 downweighting require a scientific correction design.
Merely changing target coefficients does not resolve these issues.

Typical retained CT007 projections are about one site against the nominal 3–7
range; about 98–99% of baseline/combined-soft historical replicates persist
through 2002. Survival alone does not contradict nondetection, but the bridge
cannot quantify their compatibility. Omitting CT007's count component replaces
most selected sources. The published sum-of-target-medians winner tally (12
joint, 3 climbing) differs from the actual acceptance-distance winner tally
(8 joint, 6 climbing, 1 transient). Neither is a model probability.

Barry subsequently authorized the proposed repair and bounded pilot. That
tranche is complete in `docs/observation_repair_pilot.md`; its exact specification
before execution and compact results are under `data/observation_repair_pilot/`.
The experimental module requires dated positive-record compatibility and scores
nondetections under fixed 0.60/0.98 detection scenarios, with a presence-only
bracket. Unsupported count/site conversions and PR035–PR037 score influence
are absent from repaired scores. Production scoring, priors, latent equations,
historical ensembles and Module 5 results remain unchanged.

The pilot ran 15,480 scenario simulations on deep-server, using two new seeds,
100 prior proposals per family, 20 search replicates and 100 independent
validation replicates per selected source. Raw hashes, selections, score
decompositions and disjoint validation seeds were verified. Project checks
passed 121 tests before execution; the subsequent summary regression passed.
Independent methods review reproduced raw-history calculations.

The pilot decision was: **the semantic repair passes; the pilot ensembles remain
qualified and should not be promoted to the main analysis or endpoint work**.
All three repaired profiles selected zero of the ten original-control sources
in both seeds. At detection 0.98, compatibility-weighted validation survival to
end-2002 was 70.2% and 39.3%, but 3/10 and 7/10 sources had ESS below ten.
Some estimates were dominated by a single history. Detection 0.60 also had
precision warnings, especially in the second seed. These conditional process
summaries are not posterior probabilities or empirical extinction estimates.

The deterministic Stage A sets were identical across repaired profiles, limiting
what the small pilot could establish about available stochastic histories.
Barry then approved the terminal-history screening tranche and asked for larger,
coherent reporting horizons under Twilight Laboratory. That tranche is complete
in `docs/terminal_history_screen.md`, with compact evidence under
`data/terminal_history_screen/` and empirical follow-up in
`docs/terminal_history_evidence_followup.md`.

It screened all 1,000 existing parameter sets with 50 fresh histories each,
compared equal-size selections from the full pool and the original deterministic
Stage A set, independently confirmed 90 candidates with 500 histories each,
and extended all 30 flagged sources by another 2,000 histories. Total new
simulations: 155,000. The full project check passed 129 tests. All phase hashes,
source ancestry, frozen selections and independent seed namespaces were verified;
independent review reconstructed the central raw-history comparisons.

**Current decision: GO with stochastic screening for future calibration;
QUALIFY the ensembles and strong-detection precision.** Of 138 screened sources
that generated positive-compatible terminal loss, 121 were outside repaired
Stage A. Independent confirmation reproduced such events at 28 excluded sources.
Full-pool selections had better high-detection composite scores in both seeds;
the weaker-detection second seed was slightly worse overall despite better late
compatibility. Presence-only selections were unchanged. The extension preserved
those comparisons, but 17/30 extended sources still had ESS below ten under
detection 0.98. Near-zero compatibility-weighted survival under that scenario
is not an empirical extinction probability or a family probability.

New agency material gives a rough 50–200 fish estimate for 1992 and an 18/13
split of Oberon releases across 1991/1992; it does not supply measured exposure,
detection probability or a complete wild-removal schedule. Scientific inputs
remain unchanged. The next proposed programme should settle the observation
and removal assumptions, then carry that design through larger stochastic
calibration and mechanism comparison with independent evaluation. More generic
replication is not the priority. Production calibration and endpoint replay
remain outside the completed tranche. Preserve previous results as conditional
scenarios with their original provenance.

## Lean-Code State

Goals 021-025 applied a deliberate `kill-your-darlings` tranche:

- corrected the Module 5 semantic contract and removed the false detection
  proxy from active interpretation;
- consolidated duplicated Module 5 partition and output-check logic;
- deleted two caller-free Python builders whose seven CSV outputs are now
  canonical curated scientific inputs;
- audited `src/galaxias_model/review.py` and removed the superseded Module 1.5,
  2, and 2.5 report-generation machinery, thin wrappers, stale reports, and
  orphan outputs while retaining direct tests and four used checkpoints;
- retained the Module 3 and 3.5 review machinery because it still protects
  consequential calibration and target-sensitivity decisions.

Do not add compatibility layers, replacement generators, preservation ledgers,
or tests of file existence for the deleted paths. Git is the archive. The
Module 3 readiness report now performs one calibration and reports five
scientific gates. Serial/parallel and resume reproducibility remain in the
integration tests; the report does not claim to assess them. Neither the
Module 3 nor the Module 3.5 review deletes whole output directories.

The successor code sweep also retired the fixed Goal 006 real-proposal dry-run
runner and inspector. The general matched-pair runner, shared four-arm runner,
tiny default-parameter smoke and common output checks remain. A bounded
real-source execution test retains sampled-parameter, provenance, pairing and
disk-inspection coverage. Redundant test loops, unused parameter-input formats
and unused report reexports were removed. Source identity is mandatory for
uncertainty grouping. Model equations, scoring choices, production seed labels
and committed scientific evidence are unchanged.

Existing numbered goal packets are provenance, not a requirement to create a
new packet for every small step. Under the Twilight Laboratory workflow, align
on the next coherent scientific reporting horizon, execute routine internal
stages autonomously, and return at its gold stamp or a genuine consult trigger.

## Essential Reading

Read only what is needed to recover current reasoning:

Start with `docs/conditional_calibration_results.md` and its frozen protocol
`docs/conditional_calibration.md` for the current scientific decision, then
`docs/terminal_history_screen.md`, `docs/observation_repair_pilot.md` and
`docs/historical_fit_observation_audit.md` for the formulation and evidence basis.
Use the older module documents as provenance.

1. `README.md` for the biological question, module map and current commands.
2. `docs/module4_observation_sensitivity_plan.md`
3. `docs/module4_observation_sensitivity_review.md`
4. `docs/module4_5_mechanism_interpretation_review.md`
5. `docs/module5_shared_four_arm_250rep_extension.md`
6. `docs/module5_internal_results_review_packet.md`
7. `docs/review_pipeline_disposition_audit.md`
8. `docs/goals/027-module5-shared-four-arm-250rep-extension/Log.md` only when
   exact execution provenance is needed.

Useful compact data:

- `data/module5_factorial_250rep_extension/context_effect_summary.csv`
- `data/module5_factorial_250rep_extension/replication_decision.csv`
- `data/module5_factorial_250rep_extension/source_effect_summary.csv`
- `data/module5_internal_review_packet/review_packet_manifest.json`

Do not read all historical goal packets as an orientation ritual. Follow links
from the current documents only when a specific claim or implementation detail
needs verification.

## Raw Evidence And Reproducibility

The authoritative Goal 027 raw matched output remains remote-only under:

`/data/codex/artifacts/galaxias/module5_factorial_extension_20260809T053300Z-goal027-m5-shared-250rep`

Raw matched-output SHA-256:

`3ea4ad0a05ad928628fc3cd780cb94a3f4517d07a1827b16a527ea9000ce20c5`

The frozen execution source is commit
`4e2e786381595a4dcb9ca11f04b40df1d5606f2a`; the compact completion record is
commit `17d00931b97a757ef0d69ccf6de71f4be84c07ca`. The frozen source passed
`make fast-check` with 105 tests passed and 5 slow tests deselected before the
remote run. The all-source five-replicate smoke preceded the 250-replicate run.

Do not pull the large raw CSV into Git. Verify remote availability and checksums
before relying on it. Use `deep-server-ts` and the `/data/codex` layout for any
future meaningful compute, after reading the relevant Nectar control-plane
documents and running a narrow live probe.

## Current Non-Claims And Stop Boundary

- No posterior model probabilities or uniquely identified historical cause.
- No real-world attributable fraction.
- No unqualified synergy or antagonism claim across response scales.
- No empirical absolute quasi-extinction threshold.
- No manuscript prose, polished display figure, or publication-ready table has
  been authorized or produced from the current synthesis.

Barry explicitly wants the ecological evidence put under a collaborative
"blowtorch" before manuscript-facing artefacts are designed. Continue that
conversation one substantive issue at a time. The completed observation audit
now recommends bridge repair and a bounded calibration pilot before censored
extinction-time or relative low-abundance extensions. Agree the scientific
specification before recalibration; the audit itself did not authorize a new
production run or increase in replicate count.
