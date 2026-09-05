# Galaxias Successor Handover

Updated: 2026-09-05

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

Immediately before this note was updated, `/Users/bwbrook/papers/galaxias` was
clean on `main`, synced with `origin/main`, at commit
`17d00931b97a757ef0d69ccf6de71f4be84c07ca`. The expected handover-time
working-tree change is this file only unless Barry commits it before relaunch.

Barry intends to launch the successor directly in this repository. Derive the
authority for edits, compute, commits, and publication from his current request
and the applicable instructions. Do not assume the old `pedder`, Chief of Staff,
or one-numbered-goal-per-step workflow remains the operating model.

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

## Current Family Interpretation

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

## The Live Unresolved Question

The supervisor-style review paused on how to treat the 15 Module 4 contexts.
They are five observation formulations crossed with three stochastic search
seeds, not 15 equally distinct ecological beliefs:

| Role | Variant | Main assumption |
| --- | --- | --- |
| strict reference | `baseline_current` | 50:50 nominal CT007 occupancy/count weights; exact 1996 endpoint; original detection bridge |
| single-axis diagnostic | `ct007_occupancy_primary` | 75:25 nominal occupancy/count weights |
| single-axis diagnostic | `ct009_terminal_window_gap3` | 1992-1996 terminal window with softer late penalty |
| single-axis diagnostic | `ct010_detection_half` | half the expected detections for the nondetection window |
| combined cautious formulation | `late_bridge_soft` | combines all three softer late-observation choices |

The three seeds test search repeatability within each formulation. They should
not be narrated as three additional ecological assumptions.

The outgoing agent's recommendation, still awaiting Barry's answer, was:

- use `baseline_current` and `late_bridge_soft` as strict and cautious
  evidentiary bookends, summarized across their three seeds;
- use the three single-axis variants diagnostically;
- recognize that the combined cautious formulation better matches Barry's
  stated view that occupancy is stronger than sparse counts, 1996 is a last
  detection rather than an extinction date, and nondetections are informative
  but imperfect;
- do not yet claim that its exact 75:25 and 0.5 settings are uniquely correct.

One important problem deserves explicit pressure: CT007's capture-count
deviance is numerically much larger than its occupancy penalty. The earlier
decomposition found roughly 98.6% of the baseline CT007 penalty arising from
the count component. Merely changing nominal weights from 50:50 to 75:25 does
not necessarily make occupancy dominate the realized score. Before treating an
"occupancy-primary" formulation as publication-primary, decide whether this is
acceptable sensitivity design or whether component scaling itself needs a
scientific correction.

Resume the meeting here. Ask Barry whether he prefers strict-versus-cautious
bookends or wants the cautious formulation explicitly privileged, while making
the CT007 scaling caveat visible.

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
remaining Module 3 readiness orchestrator may merit a separate simplification
later, but it is not an urgent obstacle to the scientific review.

Existing numbered goal packets are provenance, not a requirement to create a
new packet for every small step. Under the Twilight Laboratory workflow, align
on the next coherent scientific reporting horizon, execute routine internal
stages autonomously, and return at its gold stamp or a genuine consult trigger.

## Essential Reading

Read only what is needed to recover current reasoning:

1. `README.md` for the biological question and module map. Its **Current
   Status** section predates the completed Module 5 work; this handover is newer.
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
conversation one substantive issue at a time. The likely next analytical work,
after the context decision, is a bounded censored extinction-time audit and,
only if it adds information beyond minimum abundance, the agreed relative
low-abundance sensitivity. Do not rerun calibration or increase replicate count
without evidence that it could change the scientific decision.
