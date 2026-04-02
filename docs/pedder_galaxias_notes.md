# Pedder galaxias research notes

I could use a hybrid model combining age/size-structured state-space and individual-based simulations. It’s important to think about data, feasibility, and minimal viable scope.

I’m thinking it could be valuable to search for primary sources on Pedder galaxias and other relevant topics like the impacts of invasive fish. Some technical sources like the Chilcott 2013 paper and recovery plans for species might strengthen the ideas.

I’m considering the modeling approach for determining whether brown trout or climbing galaxias caused the extinction of Pedder galaxias. A simulation model seems preferable, something like agent-based or Bayesian state-space modeling. For a more traditional approach, a deterministic mathematical model with population dynamics might work too, but it’s data-limited for precise estimations.

Maybe a hybrid approach: a mechanistic, stochastic simulation embedded in a Bayesian framework? The core could still rely on differential equations, but using Bayesian evidence synthesis. Alternatively, a Bayesian state-space model could track population dynamics, incorporating sparse observations with priors from related species.

I’m thinking of testing different scenarios—whether brevipinnis, trout, both, or neither caused extinction—using counterfactual simulations. The idea is to estimate when extinction happens under various conditions and to use threshold surfaces to analyze extinction probability based on factors like trout density. Since data is sparse, the model should focus on exclusion rather than definitive conclusions, providing more comparative, probabilistic insights. The workflow could run through hypothesis generation, data collection, modeling, and sensitivity analysis.

I’m considering state variables for the species: juvenile and adult pedderensis, brevipinnis and trout in different growth stages (fry, juvenile, etc.). I’m thinking of using equations to predict survival and reproduction, incorporating fecundity, habitat conditions, and predation, with stochastic elements. There’s also the option to model only Pedder galaxias using external data for trout and brevipinnis

To make things manageable, I’m considering a two-tier modelling system. In Tier 1, the model would be a simple heuristic model for attributing causes to Pedderensis’ extinction. It would use basic terms for competition and mortality from external threats like trout or brevipinnis. The Tier 2 model could be a full eco-evolutionary model, but that might not be necessary. This way, we can get quickly assessable answers while still keeping it flexible.

I need to consider various data: historical fish surveys, unpublished reports, museum collections for relative abundance, angler catch records, stocking info, diet data, and presence records from resources like the Atlas of Living Australia. Hydro papers are useful for post-flood productivity. I could also look at literature on trout predation and life-history proxies for related species, drawing on other systems for better validations. This will help refine the model.

I’m considering whether Python or R is more suitable for the task. Python offers more robust testing and modular frameworks for simulations like ABC/SMC, so it’s useful for building custom simulations. R, however, excels in ecological stats and Bayesian models. Given that the task involves simulations, Python might be preferable, though R is also a strong choice for statistical models. I’ll recommend both while leaning slightly toward Python for flexibility. Of course, the model itself should be evidence-calibrated, not a simple theoretical exercise!

Given the sparse and qualitative data, it seems best to lean on a simulation model, especially to handle uncertainty and explore different scenarios. I can model phases like pre-flood, post-flood productivity pulse, and long-term decline. This will allow for extinction probabilities and testing competing hypotheses about the cause of the boom-and-bust cycle, including various ecological drivers. From habitat change alone, to the effects of trout and brevipinnis, all will be considered.

Each piece of evidence becomes an observation with uncertainty (error bars or bounds) regarding the timeline of the species' abundance, like the pre-1972 abundance, stocking events, and decline trends. I'll use this to lay out constraints like time-to-extirpation, incorporating data from official sources. For parameter priors, I'll probably need to rely on informative priors and broad ranges, considering established data for life history, trout growth, and ecological interactions.

I should consider building meta-analytic priors using ecological data from other systems (like trout impact on galaxiid survival

Some species only survived in two streams by the early 1990s. I might model this by allowing a fraction of juveniles to spawn in streams before moving to the lake. For trout, size classes could help describe predation pressure, though I could simplify to just annual predation pressure. For brevipinnis, I’ll use an abundance index influenced by the flood, with growth modeled via logistic growth or as a single pressure index.

The basic model could be:
- Pedderensis population in the lake (N_ped,L) and streams (N_ped,S) grow or decline based on a combination of factors like abundance, predation, and flooding effects.
- Flood impacts (q_flood) could decay over time, and I might represent trout predation as a function of their abundance and size.

For data, I’ll model counts with Poisson, occupancy with Bernoulli, and sample composition with multinomial. I’m considering implementing this in a Bayesian framework, either using Stan/NIMBLE or a Python alternative like PyMC.

For sparse, mixed data, ABC (Approximate Bayesian Computation) seems like a solid choice. It allows comparing hypotheses based on summary statistics like decline onset, switch to brevipinnis dominance, and stream refugia persistence. I’d need to carefully choose summary stats and priors, though. Alternatively, synthetic likelihood or Bayesian history matching might work too. Another option is pattern-oriented modeling (POM), often used in ecology when data is scarce, to calibrate models with multiple relevant patterns.

Instead of formal inference, I’m thinking about using "pattern-oriented stochastic simulation." This could provide a more achievable and transparent approach. The idea is to replicate key patterns, like the initial boom, shift to brevipinnis dominance, and near-extinction by the 1990s, by searching the parameter space. This method would focus on testing mechanisms, not exact parameter estimates. I could use Latin hypercube or rejection sampling for simulation, with three tiers of analysis: 1. Pattern-oriented simulation to test mechanisms, 2. Bayesian synthesis for priors, 3. Further analysis.

The most plausible outcome might be a "joint-cause model," where trout initiated the decline, and brevipinnis prevented recovery. This fits the chronology in Sanger and recovery documents, but I should stress that the value of the model is in quantitatively confirming this, not just supporting it narratively. I'll also note that limited observations suggest Pedder may have been declining before galaxias abundance increased, supporting the idea that galaxias hastened, rather than initiated, the decline. Predation and competition likely played crucial roles.

For a narrower management study, Clarence Lagoon might be easier to model, as the data is more defined and focused on brook trout stocking vs. Clarence galaxias persistence. The question is simpler and involves optimizing fishery satisfaction with extinction constraints. However, if broader interest and a compelling story are desired, Pedder provides a better narrative. This could be useful for Barry, and we might consider novelty for publication – perhaps a conservation biology paper on causal attribution, or a methodology piece on simulation-based evidence synthesis. A paired approach with Pedder and Clarence could be interesting too.

I'll start by focusing on key factors like levels, inundation maps, tributary connectivity, and habitat proxies. The comparative priors could involve Tasmanian, NZ, and even Clarence Lagoon systems. There’s missing data to acknowledge, especially from the 1970s and '80s, and issues with species misidentification. This misidentification, though a challenge, also presents an opportunity with museum collections for reconstructing species composition. Re-analyzing these archived specimens could offer stronger evidence for the timing of brevipinnis expansion—this could become an important task, especially if specimens are available for DNA analysis.

For a broad strategy, I'd focus on ideas like squeezing more out of museum collections and archive data before starting the modeling. It might be overkill to include otoliths, genetic data, or stable isotopes, but I’ll mention them just in case. For modeling, I’m thinking of a hybrid process model with stochastic steps (1965–1996). The species to focus on would be Pedder, trout, and brevipinnis. I'd need to account for unknown coefficients like growth rates and predation. We could calibrate with methods like Latin hypercube or particle filtering. Scenario comparison could involve Bayes

I’m thinking about using a discrete-time mechanistic simulator rather than aiming for a neat closed-form solution. With sparse data, an annual time step makes sense, adding seasonal structure only if necessary — focusing on spawning and annual flood productivity patterns. Maybe "annual with life-stage substeps" or "seasonal," depending on needs. Keeping the model broad to begin with seems like the best approach.

For Clarence Lagoon, I could propose a simpler stochastic model focusing on brook trout stocking. The decision variable would be "number of brook trout stocked" with the goal of maximizing angler satisfaction while ensuring galaxias persistence. It can be validated using past data. Also, I might tie this back to Pedder as the main focus, adding a potential research question like: "Can we reproduce Pedder galaxias decline with trout or galaxias alone, or must both factors contribute?"

Regarding Pedder Galaxias: their life history traits, like 2-4 years maturity and low fecundity, could guide model structure, particularly a stage-structured annual model. Climbing Galaxias' life traits from Sanger, like its ability to exceed 250 mm, autumn spawning, and predation on other galaxiids. This supports incorporating both competition and predation from brevipinnis. I'll focus on relevant threat lines for model design and current population data.

I’m thinking of using information about Clarence Lagoon stocking from current fact sheets. I might not need to search too much, since it’s easier to reference official documents like the recovery plan. Since the user provided files, I'll prioritize file-based citations, ensuring all factual claims are appropriately supported.

The model should consider the interactions between both species, not just "trout vs. brevipinnis." Instead, it should explore different possibilities like trout only, brevipinnis only, both, or both with additional changes in habitat or spawning. I’ll build a stage-structured model with components for the species and habitat. I'll include important details from the file, like the species' timeline and characteristics, such as Pedder galaxias' maturity and fecundity.

To accurately represent the species' persistence and challenges, the lake needs at least two compartments: the main lake and refuge tributaries. This reflects observed behaviors, like species disappearing from the impoundment but persisting in smaller streams. I'll cite the relevant life history and persistence information from sources. Key processes include flood pulse, trout stocking impacts, brevipinnis competition, and detection processes. I'll keep pressures from both species partially explicit and partly scenario-based to create a more flexible model.

There were ~350,000 brown trout fry in late 1972. For calibration, could use pattern-oriented calibration/ABC-SMC due to sparse data. The model must reproduce multiple key patterns, tossing parameter sets that fail to match.

Possibly "simulation-based Bayesian calibration" as an example, and then discuss sources for priors and proxies. For Pedder demography, I’ll refer to Hamr or listing statements, trout info from Tasmanian fisheries, and brevipinnis from studies in Tasmania or NZ. The ALA may help, but agency archives and museum collections might be more useful. Also, I’ll bring in comparative galaxiid systems and use Clarence Lagoon as a validation case.

Some results, like the timing of extinction risk, are more reasoning-based than factual. We'd need to present it as a likely outcome rather than a certain one and mention that empirical work should happen before heavy modeling, like creating an evidence ledger, compiling dated observations, and standardizing data. For specifics: digitize catch records and note uncertainty/ taxonomic confidence.

For implementing in Codex, I'd suggest parsing the data into a CSV with specific columns like date, location, taxon, and more. For coding, my instinct is Python, as it keeps everything — simulation, calibration, plotting — in one codebase. R could be suitable for hierarchical stats or paper-type analysis, though.

The current populations of Pedder in predator-free systems like Lake Oberon and Strathgordon can inform baseline demographic data for the species. These translocated populations provide useful insight for modeling Pedder's growth without trout and brev impacts. While including the species' status might help, the model validation with these populations is more central.

We know that translocated populations do exist. Regarding the model, I think it's important to note that a decline in prey base is likely the main driver, not food collapse. Sanger's work supports this. Including a habitat-only model could be useful as a null case, but unlikely to be the winner.

Clarify that instead of using absolute fish-per-hectare thresholds, I'd focus on standardized pressure indices or CPUE equivalents unless stocking and survey data are unusually comprehensive. Also, I'll emphasize that blame attribution is probabilistic, not absolute. For Clarence, a dynamic state model could work well since brook trout are stocked and don't breed, with stocking density being the main management lever. The recovery doc mentions that brook trout have been stocked since 1963, with galaxias still abundant.

I think it's doable and interesting. Pedder is scientifically better than Clarence, but I view Pedder as retrospective causal attribution. Sanger and current listings point to a combined-effects chronology. The real question in modeling is how trout and brevipinnis interact.

Rather than a closed-form model, a stochastic mechanistic simulation would work better, employing Bayesian calibration. This isn’t about math vs. simulation, but analytical vs. data-assimilative approaches.

Include elements like flood pulse decay and trout stocking impact, considering the roles of brevipinnis colonization and trout predation on Pedder. Need to consider competition and habitat loss, but keep habitat change secondary based on Sanger’s perspective.

Given limited mixed data, I think the best approach is to create a dated evidence ledger.

Note various observations as constraints: Pedder's abundance before the flood, the boom afterward, and anglers reporting trout predating galaxias in the 1970s. These, along with museum specimens, will guide the model.

Set parameters for species and trout populations, using available studies and data. The key output will be probability statements and threshold surfaces, exploring prior data and patterns, alongside simulation calibration using methods like ABC-SMC.

The Galaxias population since 1963 seems more like a forward optimization problem rather than a historical attribution issue. This could even serve as a pilot or second paper.

I’d lean towards using Python for custom simulation and testing, with R for stats. I’ll ensure the setup allows for reproducible, modular workflows. The final pitch would place Pedder as the main focus, with Clarence as a secondary consideration. I'd emphasize the method's novelty and its application in sparse historical contexts.

A pure mathematical model like Lotka-Volterra wouldn’t work, and go for a simpler mechanistic discrete-time simulation instead. I can mention the initial boom, the role of trout/brev, and historical thoughts on Pedder, citing Sanger and current official listings for clarity.

117 sites, 5 occupied, and the last record from 1996, with surveys until 2002. Translocated populations at Lake Oberon and Strathgordon from official source. Strathgordon breeding uncertainty. Issues with Lake Pedder—trout and brevipinnis are problematic for reintroduction

I think the Pedder idea stands out scientifically, and simulation seems like the appropriate approach. Instead of focusing on a single culprit, I'd present it as a causal-attribution problem: which mechanisms can explain the observed timeline using biologically realistic parameters? Sanger’s overview already hints at a model-friendly chronology: the post-inundation boom, trout predation, galaxias dominance, and Pedder galaxias disappearing.

The species' eventual restriction to a few shaded tributary streams shows the importance of stage structure. Pedder galaxias, a low-fecundity, non-diadromous fish, matures around two years, breeds mainly at three to four, and lives up to about six. A one-line logistic model would neglect essential biological details.

Trout pressure increases through both colonization and stocking, with a review noting the release of 350,000 brown trout fry in late 1972. The official listing mentions a rapid increase in trout numbers during the first decade after flooding. Climbing galaxias later dominant in many streams. Factors contributing to Pedder decline could include trout predation, galaxias competition, and possible direct predation. I’ll also include a habitat-only null model as a foil but treat it as secondary, since Sanger discounted food or water quality collapse as the sole cause.

The museum-based shift around 1980-83 marked a transition from Pedder galaxias dominance to climbing galaxias dominance, evident in the 1988-91 surveys where Pedder was found at only 5 of 117 sites. The last capture occurred in 1996, followed by unsuccessful surveys. A simulator calibration based on these patterns would rely on simulation-based Bayesian calibration or approximate Bayesian computation. The goal is to identify which hypotheses consistently reproduce the observed data.

For calibration, I plan to use baseline data on Pedder demography from translocated populations and captive-breeding work, trout demography from Tasmanian fishery data, and climbing-galaxias data from Tasmanian and possibly New Zealand studies. I suspect that Inland Fisheries archives, stocking records, museum specimens, and old catch data will be more valuable, especially since the translocated Pedder populations at Lake Oberon and Strathgordon can give insights into intrinsic Pedder dynamics beyond the original invasion setting.

I suspect that historical density data might be too uncertain for a solid 'fish per hectare' threshold, so I would recommend using standardized pressure or CPUE-equivalent units, unless archival data surprises me with strong support. If the combined model can reproduce both the early decline and later replacement pattern, that would be a publishable result. It would also back the view that Lake Pedder remains unsuitable for reintroduction since brown trout and climbing galaxias are well established there. Best to make sure to credit the official reference here.

For the next idea, the Clarence Lagoon situation seems like a cleaner management optimization problem. Here, the control lever—brook trout stocking density—is explicit, and the biological question centers around coexistence, not retrospective extirpation.

The official recovery material mentions that Clarence Lagoon has been stocked with brook trout since 1963, while Clarence galaxias have stayed relatively abundant. Brook trout were deliberately maintained as a less disruptive alternative to brown trout, making it perfect for a model maximizing angler benefits while preserving galaxias. This could serve as a pilot for the Pedder code base, though Pedder remains the stronger main focus here.

For simulations, I’d probably go with Python due to its support for custom simulators, calibration wrappers, and scenario sweeps. R, however, would still work well for a more stats-oriented approach.

The brook trout since 1963 and the translocated populations at Lake Oberon and Strathgordon are official. 

New additions from the "A fish and a lake" draft:

- Use "trophic upsurge" as the explicit term for the post-inundation boom mechanism.
- Treat the apparent Pedder peak around 1977 as a candidate calibration target if the underlying source can be pinned down.
- Keep the possibility open that extinction reflected a transient overshoot regime of unusually large, piscivorous trout rather than a timeless impossibility of coexistence.
- Retain *Galaxias parvus* in the conceptual community background even if it is not a modeled state variable.
- Add a sidecar genetics question: mito mixing among brev and pedder, allozymes suggesting they remain distinct, possible follow-up via DArT/RAD. This matters for conservation framing and maybe for interpretation of modern refuge populations, but is probably not part of phase-1 demographic modelling.

Literature-ingestion additions from the new markdown bundle:

- `1977` is now better supported than before as the main candidate peak year for the post-flood Pedder boom.
- Use the wording `trophic upsurge` consistently rather than switching between subsidy, boost, enrichment pulse, and boom.
- Keep the exact statement conservative:
- strong support for a 1977 peak signal
- still worth chasing the original fish series or figure before treating it as a hard numeric target

- The best extinction narrative is still `joint cause, ordered in time`:
- trout likely initiated the crash during the high-productivity early impoundment phase
- climbing galaxias likely accelerated replacement and blocked recovery later

- The `perfect storm` framing is looking increasingly viable:
- inundation changed habitat
- trophic upsurge created an unusually productive early lake
- trout overshot into a large-bodied, highly piscivorous phase
- climbing galaxias then became dominant in the altered system

- `Galaxias parvus` remains background, not a default state variable.

- Genetics is now a clearer sidecar issue than before:
- current insurance populations retain similar heterozygosity and low differentiation
- introgression with `G. brevipinnis` is real
- best-supported timing may pre-date anthropogenic contact
- therefore do not build hybridisation into phase-1 collapse dynamics unless new evidence forces it

- The `johnstoni` genetics paper is useful as a warning case:
- present-day trout allopatry does not automatically imply trout caused fragmentation
- helpful for Introduction nuance and for avoiding overclaiming from spatial pattern alone

Current Tier 1 design freeze (April 2026):

- Annual time step, historical core `1965-2002`.
- Pedder gets the real demographic structure: juveniles and adults in both `lake` and `refuge-stream` compartments.
- Trout and climbing galaxias stay explicit, but as annual pressure / abundance states rather than full age-structured populations.
- Represent the `large trophy trout` idea with a transient piscivory multiplier tied to the early `trophic upsurge`, not with a detailed trout size model.
- Treat the apparent `1977` Pedder peak as a timing target, not yet a hard numeric abundance target.
- Use Lake Oberon and Strathgordon as `intrinsic-baseline` constraints for Pedder demography, not as direct analogues of the historical Lake Pedder invasion dynamics.
- Keep `Galaxias parvus` in conceptual background only.
- Keep genetics / introgression as a sidecar interpretation issue, not a phase-1 collapse process.
- Defer seasonal detail, full trout size structure, full climbing stage structure, and absolute density thresholds.
- The Tier 1 machine-readable artifacts are now `data/calibration_targets.csv` and `data/parameter_priors.csv`, with the design narrative in `docs/model_spec_tier1.md`.
