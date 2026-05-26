# Notes for Chris

Last updated: 2026-05-18

This is a living plain-language note for Assoc. Prof. Chris Burridge as the
Pedder galaxias modelling work proceeds. The aim is to keep Chris in the loop
on what we are doing, why we are doing it, what we are finding, and where we
need biological judgement or extra context from him.

The intended reader is a trained biologist familiar with Pedder galaxias and
the conservation context, but not necessarily with population ecology
simulation, coding, or approximate Bayesian calibration.

This note reconstructs the work from Module 1 through Module 3.75 as faithfully
as possible from the repo documents and generated review artifacts.

## Current Message In One Page

We are building a transparent historical simulation model for Pedder galaxias
from the pre-flood period through the apparent loss of the natural Lake Pedder
population. The model does not assume one culprit. It compares several
plausible causal stories against the same biological and historical evidence.

The simple single-cause explanations are not doing well. Habitat change alone
and trout alone are currently outside the accepted frontier. Climbing galaxias
alone can sometimes fit important parts of the history, but the strongest
current signal is that multi-cause explanations remain important.

At present, the most robust family is `persistent_joint_cause`: a sustained
combination of climbing galaxias pressure and trout-related pressure. This is
not a final claim about causation. It is the current best-supported model
family under the evidence-scoring system we have built so far.

The main uncertainty now is the late observation bridge: how we translate
1990-1991 contraction, the 1996 final record, and 1998-2002 non-detection into
model penalties. Module 3.75 showed that these late targets are doing real
work, and that the persistent joint-cause signal survives a deliberately softer
combined late-observation check.

The most useful next modelling step is therefore not to invent a new biological
story. It is to carry a small set of transparent observation-bridge variants
into Module 4 and ask which causal conclusions survive them.

## The Causal Stories Being Compared

The current Tier 1 calibration compares five families:

- `habitat_only_null`: habitat change does the work by itself;
- `trout_only`: trout pressure does the work by itself;
- `climbing_only`: climbing galaxias pressure does the work by itself;
- `persistent_joint_cause`: trout and climbing galaxias both matter through a
  sustained period;
- `transient_perfect_storm`: the loss is driven by a sharper temporary
  combination of inundation, trophic upsurge, trout overshoot, and later
  climbing-galaxias dominance.

These are structured tests, not final narratives. The question is which kinds
of explanation can reproduce the main observed patterns without being tuned by
hand after the fact.

## Module 1: Tier 1 Model Design

Module 1 established the first formal model architecture.

The historical core runs from 1965 to 2002 with an annual time step. Pedder
galaxias gets the detailed biological structure: juveniles and adults in both
lake and refuge-stream compartments. Brown trout and climbing galaxias are
kept explicit, but as annual abundance or pressure indices rather than full
age-structured populations.

Important design choices:

- represent the post-inundation productivity boom as a `trophic upsurge`;
- allow that upsurge to peak around 1977 and then decay;
- represent the early large-trout period with a transient piscivory modifier,
  not a full trout size model;
- treat inundation as a delayed habitat transition rather than an instantaneous
  1972 step collapse;
- keep `Galaxias parvus` in the conceptual community background, but not as a
  core Tier 1 state variable;
- keep genetics and introgression as sidecar interpretation issues, not as
  phase-1 collapse dynamics.

The point of Module 1 was restraint. A very complicated model would be hard to
interpret with sparse historical data. A one-line population model would miss
the biology. Tier 1 is the middle ground: enough structure to compare causal
stories, but not more detail than the evidence can support.

Module 1 also created the target and prior architecture:

- `CT001` to `CT010` describe the historical Lake Pedder trajectory;
- `CT011` and `CT012` describe intrinsic Pedder performance in Lake Oberon and
  Strathgordon-style baseline scenarios;
- `PR001` onward define biological, threat, habitat, and observation
  parameters;
- the weakest priors are mostly interaction strengths and observation-bridge
  terms, not basic Pedder life history.

Plain-language meaning for Chris: the model is designed to ask whether habitat
change, trout, climbing galaxias, or combinations of them can reproduce the
chronology. It is not designed to estimate every ecological process in fine
detail.

## Module 1.5: Latent Kernel Check

Module 1.5 checked whether the basic simulator behaved sensibly before any
formal observation scoring was added.

This pass added two important details:

- `PR039`, which turns relative Pedder carrying terms into count-scale model
  capacities;
- `PR040`, which lets the inundation habitat penalty ramp in gradually rather
  than instantly.

It also made trout and climbing pressures act with an annual lag. That avoids
an unrealistic immediate collapse in 1972 and allows the model to represent
the documented early post-flood boom.

All Module 1.5 gates passed. In deterministic default runs, all five families
showed a peak around 1975-1977, and stochastic transient runs did not produce
pre-1972 extinctions. The transient family remained present in 1980 in all 20
test runs.

Plain-language meaning for Chris: before fitting to the evidence, the
simulation engine could already express the broad story we need it to express:
pre-flood persistence, post-flood boom, delayed decline, and later pressure
from climbing galaxias.

## Module 2: Observation Bridge

Module 2 added the scoring system that compares model runs against the
evidence targets.

This is the step where model outputs become things like:

- does the model show the early boom?
- does it peak around 1977?
- does trout pressure appear when trout were stocked and became important?
- does climbing galaxias dominance arrive in the right broad window?
- does Pedder contract into stream refuges by the right time?
- does the natural-range record end around 1996?
- do later surveys produce no detections?

The historical-core scoring layer passed. The target formulas behaved
monotonically: better biological matches received better scores, and worse
matches received worse scores. The scorer also correctly discriminated between
families where trout or climbing effects were active and families where they
were not.

Module 2 was not yet ready for full calibration because `CT011` and `CT012`
were still deferred. Those targets require explicit Lake Oberon and
Strathgordon baseline scenarios rather than the historical Lake Pedder
scenario.

Plain-language meaning for Chris: the historical evidence could now be turned
into reproducible model scores, but the insurance-population constraints still
needed their own scenario machinery.

## Module 2.5: Lake Oberon And Strathgordon Baselines

Module 2.5 added explicit `lake_oberon` and `strathgordon` scenarios. These
are not treated as direct analogues of the historical Lake Pedder invasion
setting. They are used as checks on intrinsic Pedder biology under
predator-free or threat-reduced conditions.

This activated:

- `CT011`: Lake Oberon establishment and growth;
- `CT012`: Strathgordon delayed recruitment followed by establishment.

All twelve calibration targets could then be scored through a scenario bundle.
No targets were missing or deferred, and the historical Module 2 results still
matched the earlier checkpoint.

Plain-language meaning for Chris: the model must now satisfy both the collapse
history and the basic fact that Pedder galaxias can establish and grow in
suitable refuge systems. This guards against fitting Lake Pedder decline with a
parameter set that would make the species intrinsically non-viable.

## Module 3: First ABC / History-Matching Calibration

Module 3 added the first full calibration harness.

The workflow has two stages:

- Stage A screens equal numbers of candidate parameter sets for each family
  using deterministic scenario bundles;
- Stage B takes the retained candidates and tests them against stochastic
  historical replicates.

This is similar in spirit to approximate Bayesian computation or
history-matching. We are not saying "this exact parameter set is true." We are
asking which families can repeatedly generate histories close to the observed
patterns under plausible parameter values.

The current Module 3 readiness run passed its gates:

- the sampler produced valid proposals;
- retained proposals were better than rejected ones;
- stochastic confirmation produced finite scores;
- same-seed runs were reproducible;
- the final accepted set was non-empty.

The accepted proposals were:

- 3 climbing-only;
- 5 persistent joint-cause;
- 2 transient perfect-storm;
- 0 trout-only;
- 0 habitat-only.

Plain-language meaning for Chris: after the first full calibration layer, the
single-factor habitat and trout stories were not competitive. Climbing-only,
persistent joint-cause, and transient perfect-storm stories remained alive.

## Module 3.5: Diagnostic Review

Module 3.5 asked why family ranking was sensitive and what should be checked
before moving to posterior summaries or counterfactual analysis.

The diagnostic run confirmed that the sampler geometry had been repaired: no
pre-simulation sampler or constraint failures were recorded. It also showed
that, at readiness scale, the top-ranked single proposal could be
`climbing_only`, while persistent joint-cause and transient perfect-storm
proposals were close behind.

The crucial finding was target leverage. The accepted proposals were dominated
by late-history targets:

- `CT007`: severe occupancy/capture contraction in 1990-1991;
- `CT009`: final natural-range record in 1996;
- `CT010`: no detections through 2002.

When these late targets were omitted or altered, family ranking could move.
This did not mean the late evidence was wrong. It meant the late evidence was
important enough to deserve a dedicated sensitivity pass.

Plain-language meaning for Chris: the model was not simply choosing a causal
story because of trout stocking or climbing galaxias presence. Much of the
ranking came from how well each family handled the last phase of decline and
non-detection.

## Module 3.5 Remote Sensitivity Sweep

We then ran a larger Module 3.5 sensitivity sweep remotely on Nectar. The
MacBook is being used as a control plane for light checks; heavier simulation
runs are offloaded.

The remote sweep used:

- three seeds: 20260410, 20260411, and 20260412;
- 1000 Stage A draws per family;
- 100 retained proposals per family;
- 20 stochastic historical replicates in Stage B;
- 50 accepted proposals per seed.

Accepted proposals were consistently split among the three mechanism-rich
families:

- climbing-only: 47 accepted across the three seeds;
- persistent joint-cause: 52 accepted;
- transient perfect-storm: 51 accepted;
- trout-only: 0 accepted;
- habitat-only: 0 accepted.

The best single stochastic proposal varied by seed, but the target-sum winner
was `persistent_joint_cause` in all three seeds.

Plain-language meaning for Chris: the larger sweep did not support a simple
"climbing only" conclusion. It supported a frontier of plausible
climbing-only, persistent joint-cause, and transient perfect-storm histories,
with the persistent joint-cause family currently most robust by target-sum
scoring.

## Module 3.75: Late Observation-Bridge Diagnostic

Module 3.75 focused on the late-history targets because they were doing so much
work.

### CT007: 1990-1991 contraction

`CT007` represents the 1990-1991 contraction evidence: about 5 occupied sites
out of 117, with 68 fish captured in the Bonnet Bay streams.

On paper this target mixes occupancy and capture abundance. In practice, the
capture-count side dominates the current score. Across accepted proposals,
about 98.6-98.8% of the raw `CT007` penalty comes from the count component,
not the occupied-site component.

Plain-language meaning: `CT007` is currently functioning mostly as an
abundance/detection bridge anchored by the Bonnet Bay capture count, not mostly
as an occupancy target. That is a biological and evidentiary choice we should
make explicit.

### CT009: 1996 final record

`CT009` currently treats the 1996 final natural-range record as a hard target.
If a modelled natural-range population persists through 2002, it receives a
weighted penalty of 30 for missing the exact endpoint.

Module 3.75 tested a softer terminal-window version. Persistence to 2002 is
still penalised, but less severely.

Plain-language meaning: the 1996 record is powerful evidence, but we should
decide whether it is best treated as an exact endpoint or as the centre of a
terminal window with detection uncertainty.

### CT010: 1998-2002 no detections

`CT010` is the zero-detection target for the post-1996 survey period. It
behaves exactly as expected: if the expected detection bridge is halved, the
penalty roughly halves.

Plain-language meaning: this is a useful sensitivity axis, but it should be
tied to real survey effort and capture probability, not tuned to help one
model family.

### Combined Module 3.75 result

The reassuring result is that the combined softer late-observation scenario
still selected `persistent_joint_cause` in all three seeds. Some single changes
can flip the winner toward `climbing_only`, especially changing the CT010
detection bridge, but the combined observation-bridge check did not erase the
joint-cause signal.

Plain-language meaning for Chris: the current joint-cause signal is not just a
fragile artefact of one harsh late-target setting. It still needs sensitivity
testing in Module 4, but it has survived the first targeted observation-bridge
stress test.

## Module 4: Observation-Bridge Sensitivity Calibration

Chris was away while this step was run, so we did not wait for answers to the
specific late-evidence questions above. Instead, we used the literature and the
existing repo notes to define a small, transparent sensitivity grid.

Module 4 reran the calibration with five explicit observation-bridge variants:

- baseline current scoring;
- `CT007` occupancy-primary scoring;
- `CT009` soft terminal-window scoring;
- `CT010` lower-detection scoring;
- a combined soft late-observation setting.

This was run on `deep-server`, not on the MacBook. The grid used three seeds,
1000 Stage A draws per family, 100 retained proposals per family, and 20 Stage
B stochastic historical replicates. In total this was 15 calibration runs.

The main result was stronger than expected:

- `persistent_joint_cause` won 12 of 15 variant/seed runs;
- `climbing_only` won 3 of 15 runs;
- `persistent_joint_cause` won all 3 baseline runs;
- `persistent_joint_cause` won all 3 combined soft late-observation runs;
- habitat-only and trout-only had zero accepted proposals across the whole
  Module 4 grid.

The single-axis changes are still informative. If we only halve the
zero-detection bridge in `CT010`, climbing-only wins two of three seeds. If we
make `CT007` occupancy-primary, climbing-only wins one of three seeds. But when
the late observation bridge is softened in a combined, transparent way, the
joint-cause signal remains stable.

Plain-language meaning for Chris: the current sustained joint-pressure
interpretation is no longer just the product of one exact late-evidence scoring
recipe. Climbing galaxias remains central and sometimes locally wins, but the
overall sensitivity grid still supports a combined trout-plus-climbing
explanation over a single-cause story.

## Module 4.5: Mechanism Interpretation Audit

Module 4.5 has now converted the Module 4 calibration grid into a mechanism
audit. It did not run a new broad calibration. Instead, it compared predefined
proposal sets from the raw Module 4 artifacts:

- accepted proposals;
- near-frontier proposals by absolute target-sum distance;
- near-frontier proposals by relative target-sum distance;
- family winners;
- global winners.

The audit also reconstructed deterministic landmark trajectories and derived
trout/climbing pressure summaries for the historical windows we care about:
1972-1977, 1978-1983, 1984-1991, 1992-1996, and 1998-2002.

The Module 4.5 decision table currently says:

- `persistent_joint_cause` is the primary Module 5 ensemble;
- `climbing_only` remains a sensitivity case;
- `transient_perfect_storm` remains a joint-cause sensitivity case;
- habitat-only and trout-only remain negative references.

The accepted mechanism-rich families did not show high nuisance-bound risk in
the current audit. That does not prove the observation model is perfect, but it
means Module 5 can proceed without an immediate Module 4.75 nuisance
refinement.

Plain-language meaning for Chris: the current best explanation is not simply
"climbing galaxias did it" or "trout did it". The most stable model family is a
sustained joint-pressure story. Climbing-only and transient perfect-storm
histories are still biologically useful uncertainty cases and should be kept in
counterfactual sensitivity analysis.

## Current Working Interpretation

At this point, the most defensible interpretation is:

- habitat-only is not credible on the present evidence;
- trout-only is not credible on the present evidence;
- climbing galaxias pressure is clearly important and can explain some
  histories;
- the strongest current explanation is sustained joint pressure involving
  climbing galaxias plus trout-related pressure;
- a transient perfect-storm explanation remains plausible and should not be
  discarded;
- late survey and capture evidence is central enough that it must be carried
  forward as an explicit sensitivity axis.

This is not yet a final causal conclusion. It is a well-structured interim
result.

## Next Step: Module 5 Counterfactual Attribution

The next step is matched counterfactual analysis. In plain terms, Module 5
should ask what happens to the fitted historical trajectories if we remove or
alter one mechanism at a time: trout effects, climbing-galaxias effects,
combined biotic effects, transient trout overshoot, habitat-transition penalty,
and refuge buffering.

The key discipline is to keep the Module 4.5 ensemble decision visible:
`persistent_joint_cause` is primary, while `climbing_only` and
`transient_perfect_storm` are sensitivity ensembles.

## Decisions Made So Far

We are not changing biological target weights simply to force a preferred
story.

We are keeping the five family set for now because it still does useful
discrimination.

We are carrying several observation-bridge variants into the next stage:

- baseline scoring;
- occupancy-primary treatment of `CT007`;
- softer terminal-window treatment of `CT009`;
- lower-detection treatment of `CT010`;
- the combined soft late-observation setting.

We are keeping the explicit mechanism targets active. Removing the trout and
climbing mechanism targets can let biologically misleading families become
competitive.

## Questions For Chris

1. For the 1990-1991 surveys, should the Bonnet Bay capture total be treated as
   a strong abundance anchor, or mainly as evidence that a refuge population
   persisted locally?

2. Is the "5 of 117 sites" framing the right way to represent contraction, or
   are there survey-design details that make some sites much more or less
   informative than others?

3. For the 1996 record, do you regard this as a hard last-natural-range
   endpoint, or would a softer terminal window be more biologically defensible?

4. For the 1998-2002 no-detection period, do we have enough information on
   survey effort, method, season, and expected capture probability to justify a
   strong zero-detection penalty?

5. Are there genetic or biogeographic clues that should constrain whether a
   small natural-range remnant could plausibly have persisted undetected after
   1996?

6. Does the current split between a persistent joint-cause family and a
   transient perfect-storm family match how you would distinguish the
   biological hypotheses?

7. Are there specific museum specimens, field notes, survey ledgers, or
   unpublished records that could strengthen the timing of climbing galaxias
   dominance?

8. Are the Lake Oberon and Strathgordon constraints being used in the right
   way: as intrinsic Pedder performance checks rather than as direct analogues
   of the historical Lake Pedder system?

## Running Log

### 2026-05-18

- Ported the project from its original WSL Ubuntu context to this macOS control
  plane while preserving Linux compatibility for Nectar and Kunanyi.
- Fixed portability issues around paths, line endings, GNU/BSD tool
  differences, and output locations.
- Reconstructed the project arc from Module 1 through Module 3.75 in this
  living note for Chris.
- Repaired the Module 3 sampler so biological ordering constraints are handled
  before simulation rather than causing wasted invalid draws.
- Ran the Module 3.5 sensitivity sweep remotely on Nectar after resizing the
  VM, then parked the VM again afterward.
- Found that accepted histories come from climbing-only, persistent
  joint-cause, and transient perfect-storm families, but not habitat-only or
  trout-only families.
- Ran Module 3.75 to decompose the late-history observation bridge. The
  persistent joint-cause family remained the most robust current winner, even
  under a combined softer late-observation scenario.
- Implemented and ran Module 4 on `deep-server`, with late-observation
  assumptions as first-class calibration variants. The full grid completed in
  about 42.5 minutes, and `persistent_joint_cause` won 12 of 15 variant/seed
  runs, including all combined soft late-observation runs.
