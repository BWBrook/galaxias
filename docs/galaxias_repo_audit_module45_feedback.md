# Pedder galaxias repo audit, Module 4.5 critique, and later-module roadmap

Prepared: 23 May 2026  
Repository inspected: `galaxias-main.zip` unpacked to `/mnt/data/galaxias-main`  
Scope: repository structure, documentation, tests, calibration artefacts, Module 4.5 plan, and likely Modules 5+.

## Executive judgement

This is already a unusually disciplined small-science repo. It has the right intellectual architecture for the problem: a transparent mechanistic simulator; explicit model families rather than a single favoured story; calibration targets separated from priors; a recognisable ABC/history-matching workflow; documented module gates; and a live plain-language bridge for Chris. The main scientific strength is that the repo does not merely ask whether brown trout, climbing galaxias, or habitat change are individually plausible. It asks which causal stories can reproduce a historical sequence: pre-flood persistence, post-flood boom, lagged trophic and community change, contraction to tributary refugia, last natural-range detection, and later non-detection.

The main risk is not that the repo is under-developed. It is that it is now mature enough for the next module to create a false sense of causal precision. Module 4 has already shown a strong pattern: `persistent_joint_cause` wins 12 of 15 variant-by-seed runs, wins all baseline runs and all combined soft late-observation runs, while `habitat_only_null` and `trout_only` have zero accepted proposals across the grid. That is a powerful result. It is not yet a causal conclusion in the strong sense. Before counterfactual attribution, Module 4.5 must show that the winning families are being carried by interpretable biological pressure trajectories rather than by late-observation nuisance parameters, arbitrary target-weighting leverage, or the difference between two distance summaries.

My highest-priority recommendation is to make Module 4.5 a mechanism audit, not a posterior-summary exercise. It should predefine the proposal sets being compared; reconstruct derived threat-pressure histories; test whether nuisance terms are near bounds; distinguish family prevalence from family rank; and decide explicitly whether Module 5 carries only `persistent_joint_cause`, all three mechanism-rich families, or a weighted sensitivity ensemble. If Module 4.5 does that well, the repo will be ready for counterfactual analysis. If it does not, Module 5 will convert a calibration ranking into a causal story too early.

One correction to a provisional note from the live inspection: an initially suspected duplicate stochastic draw in the Pedder update kernel did not survive line-level checking of the archive. In the inspected file there is a single density-dependence draw for each stage-compartment state. I therefore do not treat that as a code defect below.

## What I inspected and ran

I inspected the root configuration files, `AGENTS.md`, `Makefile`, `pyproject.toml`, `.gitignore`, `.gitattributes`, the `data/` and `docs/` manifests, the model core under `src/galaxias_model/`, the scripts under `scripts/`, and the tests under `tests/`. I read the Module 4.5 plan, the Module 4 review, the Tier 1 model specification, the notes for Chris, the target tables, the model-family parameter map, the parameter-prior and constraint tables, and the tracked Module 3.5, 3.75, and 4 summary outputs.

I ran the following checks in the audit environment. Because the archive specifies Python 3.12 and the local sandbox had no network access for `uv` to download CPython 3.12, I used the available Python 3.13 environment for most executable checks.

| Check | Result | Interpretation |
| --- | --- | --- |
| `make check` | Failed before repo code executed, because `uv` attempted to download CPython 3.12.12 and DNS was unavailable. | Environmental, not a model failure. It does reveal that the default command is brittle on offline machines or locked-down clusters. |
| `uv run --python 3.13 python scripts/validate_prior_pack.py` | Passed: 40 priors, 200 family-map rows, 10 constraints. | The prior/family/constraint pack is internally coherent. |
| `uv run --python 3.13 python -m compileall -q src scripts tests` | Passed. | No syntax-level failures in the inspected Python files. |
| `uv run --python 3.13 pytest tests/test_latent_kernel.py tests/test_module2_5_scenario_bundle.py tests/test_observation_scoring.py -q` | Passed: 48 tests. | The latent kernel, scenario bundle, and observation scoring layers pass the existing unit checks. |
| Full `pytest -q` | Timed out after many tests had passed. | The suite is too slow or stalls in this audit environment. See the parallel-worker note below. |
| `pytest tests/test_module3_calibration.py -vv` | Passed the first eight tests, then stalled at `test_parallel_workers_match_serial_accepted_ids` when run in sequence. | This looks like a multiprocessing/test-isolation problem rather than a biological-model error. The parallel reproducibility test should be hardened or marked as a slower integration test. |
| Module 4 smoke command with two variants, one seed, three Stage A draws per family, one retained proposal per family, one Stage B replicate | Passed and produced summary CSVs and review markdown. | The Module 4 runner/summariser can execute in a reduced configuration. |

## General repo audit

### Overall architecture

The conceptual architecture is sound. The repo has a clear progression: evidence ingestion; model specification; latent kernel; observation bridge; intrinsic baseline scenarios; ABC/history-matching; sensitivity to late-observation assumptions; and now mechanism interpretation. The separation between `data/calibration_targets.csv`, `data/parameter_priors.csv`, `data/model_family_parameter_map.csv`, and `data/parameter_constraints.csv` is particularly valuable. It makes the model auditable because the causal stories are not hidden in code alone.

The five-family design is also defensible. `habitat_only_null`, `trout_only`, `climbing_only`, `persistent_joint_cause`, and `transient_perfect_storm` are the right coarse hypotheses for Tier 1. The family map correctly disables omitted mechanisms: for example, `climbing_only` disables trout effects and leaves climbing parameters active, while `persistent_joint_cause` fixes `PR018 = 1` to remove the transient overshoot multiplier. This is much better than relying on informal interpretation of a single unconstrained model.

The main architectural weakness is that some generated summaries are tracked, while the raw artefacts needed to reproduce the next interpretive layer are not in the zip. The Module 4.5 plan points to `outputs/remote/module4_observation_sensitivity_20260522T101942Z/*`, but the archive contains only the compact tracked summaries in `data/`. Those summaries are enough to know which families won. They are not enough to compute parameter posterior-like summaries, nuisance-bound diagnostics, trajectory reconstruction, or near-frontier comparisons. Module 4.5 therefore depends on private remote state unless a compact raw artefact bundle is added.

The root also lacks a `README.md`. At this stage that is a real cost. A reader can infer the workflow from `AGENTS.md`, `data/README.md`, and the module docs, but a new collaborator or reviewer should not have to reconstruct the project by reading the whole repo. The README should state the biological question, the module sequence, the current evidentiary status, a quick-start command set, which files are source inputs versus generated artefacts, and what claims are not yet licensed by the current analysis.

### Reproducibility and portability

The `uv` workflow is a good choice, and the locked environment is appropriate. The failure of `make check` in the audit environment is still worth addressing. The issue was not a code error: `uv` tried to fetch the Python 3.12 standalone build because `.python-version` pins `3.12`, and the sandbox could not resolve GitHub. On a networked machine this will usually be invisible. On a cluster, a university-managed machine, or a remote VM behind strict egress rules, it may be annoying. Add a short note to `README.md` or `docs/compute_workflow.md` showing the offline-safe pattern, for example using a pre-installed interpreter with `uv run --python /path/to/python ...` or setting `UV_PYTHON_DOWNLOADS=never` when downloads are undesirable.

`scripts/check_portability.py` is useful but assumes a Git working tree because it calls `git ls-files`. That is fine inside the repo; it is less robust for a zip-based audit, an exported archive, or a collaborator who has unpacked the project without `.git`. Add either a fallback that walks the tree while excluding `.venv`, `outputs`, `.git`, and caches, or emit a clearer message: “This check must be run from a Git checkout.” The current script passed after I initialised a local Git index, but the out-of-the-box zip archive did not contain `.git`.

The `.gitignore` is minimal but mostly correct: `.venv`, Python caches, `.DS_Store`, and `outputs/` are ignored. I would add common transient files such as `.mypy_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `*.log`, and perhaps `.ipynb_checkpoints/` if notebooks are ever used. The `.gitattributes` file is sensible and helps with LF line endings and binary files.

The repo would benefit from an explicit artefact manifest. At minimum, add `data/artifact_manifest.csv` or `data/artifact_manifest.json` with one row per tracked generated artefact: producing script, source run directory, command, date, Git commit, Python version, random seed, input table hashes, and a short description. This matters because the tracked Module 4 summaries already represent multi-run remote computations. Without provenance metadata, a future reader cannot easily tell whether a summary table corresponds exactly to a given plan, seed grid, or prior pack.

### Test suite and CI

The existing unit tests cover the right layers: latent kernel, observation scoring, scenario bundles, and calibration. The 48-test subset I ran passed cleanly. The full suite did not complete within the audit timeout, and `tests/test_module3_calibration.py` stalled at `test_parallel_workers_match_serial_accepted_ids` when run after the earlier small-run test. That same class of failure often arises when a multiprocessing test forks from a parent process that has already performed substantial NumPy/Pandas work, or when process-pool workers inherit state in an order-dependent way. It may not reproduce on Barry’s Mac, the Mac mini, or `deep-server`, but it is not something to ignore.

I would separate tests into three classes: fast unit tests, smoke/integration tests, and slow reproducibility tests. The parallel-worker equality check is scientifically important, but it need not run as part of every fast `pytest`. Mark it as slow or integration, and add a standard command such as `pytest -m "not slow"` for routine development. If the parallel test remains order-dependent, try using an explicit multiprocessing context, reducing the amount of parent-state created before the pool is launched, or moving the worker-equality check to a subprocess-level script where each run starts from a fresh interpreter. The current `_execute_tasks()` also opens a new `ProcessPoolExecutor` for every batch; that is simple but may be slow and creates repeated process-pool churn. A single executor per stage would probably be cleaner for larger runs.

Add GitHub Actions or another CI gate even for the private repo. A minimal CI matrix running `uv sync --locked`, prior validation, compile, and the fast test subset would catch many accidental breakages. The slower Module 3/4 smoke checks can be manual or scheduled.

### Code organisation

The code is readable, but two files have become monoliths: `src/galaxias_model/review.py` is about 2,023 lines, and `scripts/build_evidence_ledger.py` is about 2,024 lines. That is not yet catastrophic, but it is the point at which adding Module 4.5 directly to the same review module would make maintenance worse. Split review code by module, for example `galaxias_model/review/module3.py`, `module3_75.py`, `module4.py`, and `module4_5.py`, while keeping a stable public import surface in `__init__.py` if needed.

The calibration code is more cohesive but still large. The core concepts are separable: sampling, Stage A, Stage B, acceptance, artefact writing, and summarisation. A future refactor could move task execution and output writing into smaller helpers, but I would not prioritise that before Module 4.5 unless it blocks work.

The simulator is deliberately simple and auditable. One design choice deserves more explicit documentation in code comments and tests: trout and climbing states are recorded for the current year, but their effects on Pedder are applied with a one-year lag via `threat_row`. This is described in the model specification and is biologically reasonable, because it avoids an instantaneous 1972 collapse after stocking. It should also be covered by a small regression test that confirms a 1972 stocking input affects Pedder from the intended update year, not accidentally one year earlier or later.

One small future-facing issue is that `_build_historical_lake_forcing_impl()` hard-codes `spawn_habitat_multiplier` to `1.0` even though `ScenarioDefinition` carries `spawn_habitat_by_year`. That is harmless for the current historical scenario, where the schedule is all ones, but it will be limiting if Module 5 wants historical-lake counterfactuals that alter spawning habitat through a scenario definition. The historical forcing builder should probably honour `scenario_definition.spawn_habitat_by_year` just as the baseline-refuge builder does.

`SimulationConfig.record_forcing` appears in the type definition but is not used in the simulation result pathway. Either implement it or remove it. Leaving unused configuration switches around is a small reproducibility hazard because readers may think they are controlling output volume when they are not.

### Observation bridge and scoring

The observation bridge is the project’s most sensitive layer, and the repo appropriately treats it as such. Module 4’s explicit late-observation variants are a major improvement over post-hoc spreadsheet interpretation. The current target table is also transparent: CT007, CT009, and CT010 are rightly marked as late-history constraints, and Module 4 shows that they dominate leverage among accepted proposals. Across Module 4, mean accepted median weighted penalties were highest for CT007, CT010, and CT009, far above most other targets. That is not wrong; those are precisely the data that anchor terminal decline. But it means family ranking is only as defensible as the late-observation bridge.

CT009 is the target I would scrutinise hardest before counterfactuals. In the current observation projection, CT009 maps the “last natural-range record in 1996” to `summary["last_year_total_present"]`. That is a latent-presence endpoint, not a detection endpoint. If the true statement is “last detected in 1996 under imperfect surveys,” then a tiny latent population persisting after 1996 should be penalised mainly through CT010’s zero-detection likelihood, not automatically treated as a wrong last-presence year. Module 4’s terminal-window softening helps, but the structural mapping still matters. A future Module 4.75 could recast CT009 as a last-detection event with detection probability, or down-weight it relative to CT010 if the survey-effort model remains coarse.

CT010 is closer to a detection model because it penalises expected detected counts over 1998–2002, but it does not currently vary survey effort by year. If the historical survey effort can be reconstructed, even coarsely, the natural form would be

$$
Y_t \sim \operatorname{NegBin}\left(q e_t N_t,\, \phi\right),
$$

where $Y_t$ is detected count, $q$ is a detectability/count-scale term, $e_t$ is effort, $N_t$ is latent abundance, and $\phi$ is overdispersion. The existing nuisance terms already approximate pieces of this, but formalising effort would reduce the temptation to use `PR036` and `PR037` as all-purpose escape valves.

CT004 is also worth a short wording adjustment. The target table includes the 350,000 fry stocking event, but the scoring logic treats it as an event/window presence condition rather than a quantitative match to 350,000. That is defensible because `PR013` converts stocked fry to the model’s trout index and should not be calibrated as literal abundance. Still, any manuscript or review document should say clearly that CT004 checks representation of the stocking and early piscivory phase, not numeric trout abundance.

CT005 uses the climbing-to-Pedder lake ratio in 1980 and 1983. This is a good discriminating target, but because the denominator is the model’s Pedder lake index, the ratio can become extreme as Pedder lake abundance approaches zero. For accepted proposals this may be exactly the intended signal. Module 4.5 should nevertheless inspect whether CT005 rewards numerical denominator collapse rather than a biologically sensible dominance transition.

### Data and evidence layer

The evidence layer is stronger than a typical modelling repo at this stage. `source_register.csv`, `evidence_ledger.csv`, `proxy_evidence_leads.csv`, and `priority_source_gaps.csv` make the chain from literature to target/prior design inspectable. The register already includes official listing material, recovery plans, local markdown conversions of key sources, ALA curation outputs, proxy trout-galaxiid studies, and recent genetics-side sources. That is excellent.

The remaining empirical weak points are also correctly identified in the repo: direct quantitative Pedder abundance through the late 1970s and early 1980s, exact survey effort for terminal non-detection, specimen-level museum chronology, and stronger priors for interaction strengths. These are not fatal. They should, however, control the language of the eventual paper. This analysis can credibly support statements such as “within the current model-family and target framework, single-factor habitat-only and trout-only explanations are not competitive, and joint trout-plus-climbing explanations are most stable.” It should avoid statements like “we proved that persistent joint predation caused extinction” unless the later counterfactual and robustness modules are much stronger than the present evidence can probably support.

The repo’s inclusion of genetics as a sidecar rather than a core demographic mechanism is the right choice. Recent conservation-genetic work on *G. pedderensis* is highly relevant to insurance-population management and taxonomic interpretation, but it should not be forced into the historical demographic collapse model unless specific evidence links introgression or identity uncertainty to the 1972–2002 decline process.

## Specific high-priority fixes before or during Module 4.5

### 1. Add a compact raw Module 4 publish bundle

The current tracked Module 4 tables are not enough for Module 4.5. Add a reproducible bundle, either under an ignored `outputs/` directory with a manifest or as compressed tracked artefacts if size permits, containing at least:

- `proposal_summary.csv.gz` for every variant/seed run;
- `parameter_values.csv.gz` for every variant/seed run;
- `target_scores.csv.gz` for every variant/seed run;
- `accepted_proposals.csv` for every variant/seed run;
- each `run_manifest.json`;
- a top-level manifest with hashes and source command.

If the files are too large for Git, put them in a documented external artefact location and track a manifest that gives paths, hashes, and commands. Module 4.5 should not depend on a human remembering that the real inputs live on `deep-server` under a dated path.

### 2. Make the full test suite predictable

At minimum, mark the parallel-worker check and larger Module 3 review tests as slow/integration. The fast development gate should complete reliably. A good split would be:

```bash
uv run pytest -m "not slow"
uv run pytest -m slow
uv run python scripts/run_module4_observation_sensitivity.py --...small smoke...
```

Then add `pytest.ini` or equivalent configuration under `pyproject.toml` defining the `slow` marker. This will prevent “tests hang sometimes” from becoming normalised.

### 3. Add a root README

A good README should be short but explicit. Suggested headings: biological question; current status; repo layout; quick start; module map; source versus generated files; current headline result; current non-claims; how to reproduce Module 4 summaries; how Module 4.5 will be run; and where raw artefacts live.

### 4. Split Module 4.5 code into its own module

Do not add a large Module 4.5 implementation into `review.py`. Create something like `src/galaxias_model/mechanism_interpretation.py` or `src/galaxias_model/review/module4_5.py`, plus `scripts/run_module4_5_mechanism_interpretation.py`. The script should accept explicit inputs rather than relying on hard-coded paths:

```bash
uv run python scripts/run_module4_5_mechanism_interpretation.py \
  --module4-root outputs/remote/module4_observation_sensitivity_20260522T101942Z \
  --publish-root . \
  --near-frontier-delta 10 \
  --trajectory-sample 100 \
  --seed 20260523
```

Add a `--summarize-only` mode for re-rendering outputs from already-derived tables.

### 5. Add a formal target-weight and distance audit

Module 4 currently uses both `stochastic_overall_distance_median` and post-hoc median target sums for family ranking. This is not inherently wrong, but Module 4.5 must make it explicit. Define a proposal-level distance such as

$$
d_p = \sum_{j \in \mathcal{T}} w_j\, \tilde{\ell}_{p,j},
$$

where $\tilde{\ell}_{p,j}$ is the replicate-median penalty for target $j$ and $w_j$ is the target priority weight already embedded in the weighted penalty. Then show whether family conclusions change under the distance columns already produced by Stage B versus this target-sum reconstruction. If they differ, report the difference rather than hiding it.

## Critical pass over the Module 4.5 plan

The current Module 4.5 plan is conceptually right. Its purpose statement is exactly what the project needs: “what biological mechanism, parameter pattern, and historical trajectory make the accepted families work?” It correctly focuses on `climbing_only`, `persistent_joint_cause`, and `transient_perfect_storm`, while keeping `habitat_only_null` and `trout_only` as negative references. It correctly identifies CT007, CT009, and CT010 as late-history targets with high leverage. It also correctly recognises nuisance terms as a possible threat to interpretation.

The main improvements I recommend are not changes of direction. They are sharpenings that will prevent Module 4.5 from becoming descriptive rather than diagnostic.

### Define proposal sets before looking at the results

The plan defines four nested sets: `accepted`, `near_frontier`, `family_winners`, and `global_winners`. That is good, but `near_frontier` is currently vague. Define it operationally before running the analysis. For example, within each variant/seed,

$$
\mathcal{F}_{v,s}(\Delta) = \{p : d_{p,v,s} \le d^{\star}_{v,s} + \Delta\},
$$

where $d^{\star}_{v,s}$ is the best valid Stage B distance in that variant/seed and $\Delta$ is a pre-specified margin. Report at least one absolute margin and one relative margin, for example $\Delta = 10$ weighted-penalty units and $d_p \le 1.05 d^{\star}$. If the biological conclusion is sensitive to this definition, that is a result.

Also distinguish “accepted because globally in the top 10% or cap” from “family plausible because its own best run is near the global frontier.” The accepted set is useful as an ensemble, but it is not a posterior sample in the strict sense. If one family has many mediocre accepted proposals and another has fewer but closer-to-frontier proposals, prevalence and plausibility diverge.

### Use derived mechanism metrics, not just raw parameters

Parameter summaries are necessary but insufficient. The same biological pressure can be produced by different combinations of trout abundance, piscivory, climbing abundance, habitat transition, and refuge buffering. Module 4.5 should therefore reconstruct derived annual pressure terms directly from the simulator logic. The core quantities should be approximately:

$$
\Lambda_{L,t} = H_t\left(\theta_{20}T_tP_t + \theta_{27}C_{L,t}\right),
$$

$$
\Lambda_{R,t} = H_t(1-\theta_{34})\left(\theta_{21}T_tP_t + \theta_{28}C_{R,t}\right),
$$

where $\Lambda_{L,t}$ and $\Lambda_{R,t}$ are lake and refuge biotic-pressure indices, $H_t$ is habitat-transition forcing, $T_t$ is trout abundance, $P_t$ is piscivory, $C_{L,t}$ and $C_{R,t}$ are climbing-galaxias pressure states, and $\theta_i$ denotes the corresponding `PR` parameter. Then derive cumulative pressures over biologically meaningful windows:

$$
A_L(W) = \sum_{t \in W} \Lambda_{L,t}, \qquad
A_R(W) = \sum_{t \in W} \Lambda_{R,t}.
$$

Useful windows are 1972–1977, 1978–1983, 1984–1991, 1992–1996, and 1998–2002. These windows map cleanly onto the post-flood boom, climbing transition, refuge contraction, final natural-range record, and non-detection endpoint.

For mechanism decomposition, calculate trout shares and climbing shares, with a small $\epsilon$ to avoid division by zero:

$$
s^{\text{trout}}_{L,t} =
\frac{\theta_{20}T_tP_t}{\theta_{20}T_tP_t + \theta_{27}C_{L,t} + \epsilon},
$$

and the analogous refuge term. These summaries will be much more interpretable to Chris than raw `PR020` or `PR027` medians alone.

### Make nuisance dependence a formal diagnostic

The plan says to check whether nuisance terms cluster near bounds. Turn that into a quantitative table. For each proposal $p$ and nuisance parameter $i$, rescale to prior position:

$$
z_{p,i} = \frac{\theta_{p,i} - L_i}{U_i - L_i},
$$

where $L_i$ and $U_i$ are the prior lower and upper bounds. Then for each family and variant report:

$$
b_{f,i} = \frac{1}{n_f}\sum_{p \in f} I(z_{p,i} < 0.05 \;\lor\; z_{p,i} > 0.95),
$$

as the fraction of accepted or near-frontier proposals near a prior boundary. Also report rank correlations between each nuisance term and fit distance:

$$
\rho_i = \operatorname{cor}_{\text{Spearman}}(z_{p,i}, d_p).
$$

If `climbing_only` wins occur only when `PR036` is very low, `PR037` is very high, or `PR039` pushes latent counts into a narrow scale regime, then they should be treated as observation-model wins rather than biological wins.

### Add posterior-predictive checks by target block

Do not only summarise target penalties. For each family and variant, report the empirical success rate for each target under the accepted and near-frontier sets. For example, report the fraction of proposals for which CT007 lies in the occupied-site range, CT009 falls inside the exact or terminal window, and CT010’s expected detections are below a specified small threshold. Also report block-level leave-one-out ranking stability for at least four blocks: early boom/trophic targets, trout/climbing mechanism targets, refuge-contraction targets, and terminal non-detection targets.

A compact way to present this is a target-by-family heatmap or table with median penalty, 10th–90th percentile penalty, and pass fraction. The key question is whether `persistent_joint_cause` wins because it is moderately good across all target blocks, or because it is merely less bad on the late block than other families.

### Test persistent-versus-transient degeneracy

The current plan asks whether `transient_perfect_storm` is biologically distinct. That is essential. Do it in trajectory space, not only parameter space. For selected proposal trajectories, calculate a distance such as

$$
\delta(p,q) = \left[\sum_t \sum_s a_s\left(x_{p,s,t}-x_{q,s,t}\right)^2\right]^{1/2},
$$

where $s$ indexes standardised state or pressure summaries and $a_s$ are scaling weights. Then ask whether accepted transient proposals occupy a genuinely different trajectory region from persistent proposals. If the transient family simply emulates persistent joint-cause by using extra flexibility without producing a distinct early overshoot signature, it should not be given a separate causal interpretation in Module 5. It can be folded into a broader joint-cause ensemble.

The discriminating signature for transient should be explicit: high `PR018`, non-trivial `PR019` decay, elevated 1972–1977 trout piscivory pressure, and a later shift to climbing/refuge pressure. If those are absent, the family label is not doing biological work.

### Add minimum biological requirements for each surviving family

Before looking at the Module 4.5 summaries, write short “minimum requirements” for each family. For example, a credible `climbing_only` explanation should show climbing activation and growth early enough to create the observed 1980–1983 switch, without requiring extreme detection/overdispersion, and while still satisfying early boom and refuge-baseline constraints. A credible `persistent_joint_cause` explanation should show non-negligible trout pressure after the early boom plus sustained climbing pressure in lake or refuge compartments. A credible `transient_perfect_storm` explanation should show a temporary trout-overshoot component that materially changes the trajectory relative to persistent joint-cause.

This will make the interpretation falsifiable. If a family wins statistically but fails its own biological minimum requirements, the right conclusion is not “the family wins”; it is “the score can be satisfied by a biologically degenerate member of that family.”

### Add landmark-year summaries, not only trajectory plots

The plan already proposes landmark years. Make them table-first. For each family/variant/proposal set, summarise at least 1972, 1977, 1980, 1983, 1988–1991, 1996, and 2002. The table should include `N_L`, `N_R`, `N_total`, `T`, `P`, `C_L`, `C_R`, `U`, $\Lambda_L$, $\Lambda_R$, trout share, climbing share, and lake/refuge occupancy. Plots can then illustrate the table rather than replace it.

### Decide the Module 5 ensemble with a written rule

The plan ends with possible ensemble choices. Add a written decision rule. For example:

- If `persistent_joint_cause` is the only family with stable rank, non-bound nuisance values, and coherent derived pressure histories, Module 5 uses persistent joint-cause as the primary ensemble and treats the other mechanism-rich families as sensitivity cases.
- If `persistent_joint_cause` and `transient_perfect_storm` differ in parameters but not derived trajectories, combine them as a joint-cause ensemble rather than over-interpreting the family distinction.
- If `climbing_only` remains competitive under the combined soft late-observation variant and does not require nuisance extremes, it must be carried as a serious alternative in Module 5.
- If family ranking is dominated by `PR035`–`PR039`, run Module 4.75 before Module 5.

This will stop Module 5 from inheriting ambiguity by inertia.

## What should come in Modules 5+

### Module 5: matched counterfactual attribution

Module 5 should be a matched counterfactual analysis using the calibrated Module 4.5 ensemble. It should not be another broad fishing expedition. For each retained proposal, run the historical baseline and a standard set of interventions with common random numbers, so stochastic noise cancels as much as possible within proposal. The basic causal contrast can be written as

$$
\Delta_m = P(\tau > 2002 \mid \operatorname{do}(m)) - P(\tau > 2002 \mid \text{historical}),
$$

where $\tau$ is the extirpation time from the natural Lake Pedder system and $m$ is an intervention. Other useful outcomes are expected extirpation year, probability of persistence past 1996, minimum abundance over 1992–2002, lake versus refuge persistence, and expected detections under the survey bridge.

The intervention set should separate state removal from effect removal. Suggested scenarios are:

| Intervention | Interpretation |
| --- | --- |
| Historical baseline | Reproduce the fitted 1965–2002 history. |
| No trout stocking | Set 1972 stocking input to zero and allow trout state to remain absent unless another explicit source exists. |
| Trout effects removed | Keep the historical trout state but set `PR020 = PR021 = 0`; isolates direct trout impact. |
| No climbing-galaxias effect | Keep climbing state but set `PR027 = PR028 = 0`; isolates direct climbing pressure. |
| No trout or climbing effects | Joint removal of biotic interactions; tests combined biotic pressure. |
| No transient trout overshoot | Set `PR018 = 1` while leaving baseline trout abundance/effects otherwise intact; tests the perfect-storm component. |
| No habitat-transition penalty | Set the Pedder habitat penalty contribution to zero or hold $H_t=0$; a diagnostic counterfactual, not a realistic management scenario. |
| Strong refuge buffering | Increase refuge quality or buffering terms within plausible limits; tests whether refuge-mediated persistence was the key missing condition. |

The central interaction term should be explicit. If $T$ denotes trout-effect removal and $C$ denotes climbing-effect removal, then a simple synergy contrast is

$$
I_{T,C} = \Delta_{T+C} - \Delta_T - \Delta_C.
$$

A large positive $I_{T,C}$ would support a joint-cause interpretation in which neither single removal captures the combined release from pressure. A near-zero or negative interaction would imply more additive or substitutable mechanisms.

Module 5 should report results by family and by the Module 4.5 chosen ensemble. Do not collapse immediately to a single overall number. The key outputs should be a counterfactual effect table, an extirpation-year distribution plot, and a compact “attribution fingerprint” for each family.

### Module 5.5: present-day coexistence envelope

Chris’s most interesting framing is not only “what caused the historical extirpation?” It is also “are the conditions that caused extirpation still present?” That deserves a separate module after historical counterfactuals. Module 5.5 should hold transient post-flood upsurge terms off and explore persistence under present-day or standardised trout and climbing pressure. The natural axes are cumulative trout pressure and climbing pressure, perhaps expressed through the same derived terms used in Module 4.5:

$$
\lambda_T = \theta_{20}TP, \qquad
\lambda_C = \theta_{27}C_L,
$$

with analogous refuge terms. The output should be a coexistence surface:

$$
P(\tau > T_{\mathrm{future}} \mid \lambda_T, \lambda_C, \text{refuge state}),
$$

where $T_{\mathrm{future}}$ might be 25 or 50 years. This would convert the retrospective model into a management-relevant claim without pretending to know literal fish-per-hectare thresholds. The most defensible thresholds will probably be in standardised pressure units or CPUE-equivalent units, unless the archival data become much stronger.

### Module 6: robustness, prior sensitivity, and target sensitivity

Module 6 should be the formal robustness layer. It should perturb weak priors, target weights, CT007/CT009/CT010 bridge variants, and proposal-set definitions. It should also run a larger calibration grid if Module 4.5 suggests that sample size rather than biology is driving ambiguity. This is where an SMC-ABC or history-matching refinement could be considered. The aim would be not to make the model fancier, but to test whether the headline causal conclusion survives reasonable alternatives.

Useful analyses include prior expansion for weak interaction parameters; target-block omission; target-weight jitter; alternative CT009 last-detection formulations; alternative CT010 effort/detection assumptions; larger Stage A sampling for families that sit near the frontier; and global sensitivity or PRCC/Sobol-style summaries of derived outcomes. If the causal conclusion changes only under implausible target weights or nuisance extremes, that strengthens the paper. If it changes under modest changes, that is the correct result to report.

### Module 7: manuscript and communication package

Module 7 should convert the modelling workflow into paper-ready artefacts. I would plan the paper around a small number of figures:

1. A historical timeline of Lake Pedder flooding, trout stocking, trophic upsurge, climbing-galaxias shift, refuge contraction, final record, and non-detection.
2. A model schematic showing Pedder lake/refuge compartments and forcing states.
3. A calibration-family ranking figure across Modules 3.5, 3.75, and 4.
4. A Module 4.5 mechanism figure showing derived trout and climbing pressure trajectories for the surviving families.
5. A Module 5 counterfactual attribution figure.
6. If included, a present-day coexistence-envelope figure.

The manuscript language should emphasise historical causal attribution under sparse evidence and model-family comparison. The strongest likely claim is not “we estimated the true cause.” It is: “a transparent mechanistic history-matching analysis rejects simple habitat-only and trout-only explanations under the current target/prior framework, and points to sustained or sequential joint pressure from trout and climbing galaxias as the most stable explanation of the observed chronology.” That is a strong and defensible scientific statement.

### Module 8 or appendix: genetics and identity sidecar

A short genetics sidecar should be planned, either as a module or a manuscript appendix. It should cover insurance-population diversity, serial translocation history, possible introgression from *G. brevipinnis*, and the interpretive caution that present-day distributions or genetic patterns need not map simply onto 1972–2002 demographic causation. This sidecar should inform conservation implications and taxonomic confidence, but it should remain separate from the Tier 1 demographic mechanism unless new evidence justifies coupling it directly.

### Possible companion module: Clarence Lagoon

Clarence Lagoon is a cleaner forward-management optimisation problem than Lake Pedder because the control lever is explicit and the question is coexistence under a stocked salmonid regime rather than retrospective extirpation. It should probably remain a companion project rather than a later Pedder module. The current Pedder codebase could seed it, but the paper logic is different enough that folding it into this repo too early would dilute the main story.

## Suggested Module 4.5 output tables

The current plan lists useful outputs. I would make the following tables mandatory:

| Output | Purpose |
| --- | --- |
| `data/module4_5_proposal_set_membership.csv` | Records accepted, near-frontier, family-winner, and global-winner membership for every proposal. |
| `data/module4_5_parameter_summary.csv` | Family/variant/proposal-set summaries for all priority parameters. |
| `data/module4_5_parameter_contrasts.csv` | Effect sizes and rank contrasts between mechanism-rich families. |
| `data/module4_5_nuisance_audit.csv` | Boundary fractions, nuisance-fit correlations, and family-rank associations for `PR035`–`PR039`. |
| `data/module4_5_target_family_summary.csv` | Median penalties, pass fractions, and quantiles for every target by family and variant. |
| `data/module4_5_pressure_landmarks.csv` | Derived pressure terms and trout/climbing shares at landmark years/windows. |
| `data/module4_5_trajectory_landmarks.csv` | Pedder abundance, state, and occupancy summaries at landmark years/windows. |
| `data/module4_5_family_decision_table.csv` | A compact yes/no/uncertain table against minimum biological requirements and nuisance checks. |
| `docs/module4_5_mechanism_interpretation_review.md` | The human-readable interpretation and decision for Module 5. |

The decision table is especially important. It should state, for each family, whether it is biologically coherent, whether it relies on nuisance extremes, whether it is stable across variants, whether it is distinct in trajectory space, and whether it is carried forward to Module 5.

## Suggested Module 4.5 figures

Keep figures few and diagnostic. A mechanism interpretation module can easily drown in plots. I would use:

| Figure | Content |
| --- | --- |
| Parameter contrast strip plot | Priority mechanism and nuisance parameters, faceted by family, with prior bounds visible. |
| Derived pressure trajectories | Median and 50/90% bands for $\Lambda_L$ and $\Lambda_R$ by family. |
| Trout-versus-climbing pressure share | Time series or windowed stacked summaries showing whether pressure is trout-led, climbing-led, or joint. |
| Target penalty heatmap | Families by targets, perhaps separated by observation variant. |
| Nuisance diagnostic plot | Fit distance versus `PR036`, `PR037`, and `PR039`, coloured by family. |
| Persistent-transient trajectory-distance plot | Demonstrates whether transient proposals form a separate mechanism cloud. |

## External context checked during this audit

The current official listing material still frames the species as originally restricted to Lake Pedder and nearby inflows/swampy pools, increasing after inundation before disappearing from the impoundment and remaining natural stream habitat, with introduced brown trout and native climbing galaxias thought to have contributed to extinction. It also identifies the two extant translocated populations as Lake Oberon and the Strathgordon water supply dam. See the Tasmanian NRE 2023 listing statement: <https://nre.tas.gov.au/Documents/Galaxias%20pedderensis_LS_APPROVED%20BY%20GM_15062023.pdf>.

The Australian Government’s EPBC assessment similarly states that decline was probably due to a combination of predation or competition by brown trout and climbing galaxias, and that surveys from 1998 to 2002 failed to locate the species in its natural range. See: <https://www.dcceew.gov.au/environment/biodiversity/threatened/assessments/galaxias-pedderensis-2005>.

A recent genetics paper directly relevant to the insurance populations is Horner et al., “Evaluating genetic diversity, population structure, and introgression in insurance populations of one of Australia’s most threatened species: the freshwater fish *Galaxias pedderensis*”, *Conservation Genetics* 27, article 9 (2026), DOI `10.1007/s10592-025-01731-0`. Its relevance is mainly to genetic management, serial translocation interpretation, and introgression caution, not to the first-order demographic mechanism of the historical collapse.

A recent comparative cautionary paper in *Diversity and Distributions* is Jense et al., “Historical Impacts of Invasive Species May Not Always Be What They Seem: A Genetic Perspective From an Endangered Native Species”, DOI `10.1111/ddi.70072`. It is relevant to framing because it warns against over-inferring historical impact from present-day distributions alone.

## Bottom line

The repo is ready for Module 4.5, provided Module 4.5 is treated as a strict diagnostic gate rather than a narrative polishing exercise. The strongest current result is the repeated failure of habitat-only and trout-only explanations and the stability of `persistent_joint_cause` under the combined late-observation variant. The biggest remaining threat to inference is that late-history observation assumptions and nuisance terms may be doing more work than the biological mechanism labels imply. The next module should therefore quantify mechanism, nuisance dependence, and family distinctness in derived trajectory space. Only then should the project move to counterfactual attribution.
