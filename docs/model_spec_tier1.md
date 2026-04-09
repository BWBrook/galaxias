# Tier 1 Model Specification

## Summary

Tier 1 is an annual, explicit-but-simple simulator for asking two linked questions:

1. which mechanism set best explains the historical extirpation of `Galaxias pedderensis` from the natural Lake Pedder system, and
2. whether that extirpation implies persistent non-coexistence or instead reflects a transient `perfect storm` created by inundation, trophic upsurge, trout overshoot, and later climbing-galaxias dominance.

The historical core runs from `1965` to `2002`. The same structure can later be extended into present-day counterfactual coexistence runs, but historical fit comes first.

Tier 1 is intentionally asymmetric:

- `Pedder galaxias` gets real biological structure: juvenile/adult stages plus lake/refuge compartments.
- `Brown trout` and `climbing galaxias` remain explicit state variables, but only as simple annual abundance / pressure states.
- the early `trophy trout` story is represented by a transient piscivory modifier, not by a full trout age model.
- `Galaxias parvus` stays in community background only.
- genetics and introgression are excluded from the core demographic dynamics.

## Time Axis And Units

- Simulation window: `1965-2002`
- Time step: `1 year`
- Annual state is interpreted as the end-of-year post-recruitment state.
- Pedder states are latent counts linked to the index-scale carrying terms through `PR039`.
- Trout and climbing states are standardized abundance-pressure indices, not absolute fish counts.
- Trophic upsurge is a standardized productivity index.
- Historical forcing constants are fixed, not estimated:
  - inundation / system-connection onset begins in `1972`
  - brown trout stocking event is fixed at `350,000` fry in `1972`
  - trophic upsurge is forced to peak in `1977`, then decay
- the inundation-linked habitat penalty begins in `1972`, but ramps in gradually through `H[t]` and reaches full strength only after `PR040` years

Pre-flood initialization is not fitted directly. Instead, the historical run should begin from a Pedder-only burn-in that reaches a stable age structure under pre-inundation conditions, with trout and climbing states set to zero in the connected lake system before `1972`.

The latent-count scaling matters explicitly in implementation:

- `PR008` and `PR009` remain relative carrying-capacity indices
- `PR039` converts those indices into model-internal count-scale capacities used in burn-in, density dependence, and abundance-index calculations

## State Variables

| Symbol | State | Unit | Notes |
| --- | --- | --- | --- |
| `J_L[t]` | Pedder juveniles in lake | latent count | Juveniles exposed to lake threats and lake density dependence |
| `A_L[t]` | Pedder adults in lake | latent count | Adults contributing to lake-linked recruitment |
| `J_R[t]` | Pedder juveniles in refuge streams | latent count | Juveniles in tributary refuge habitat |
| `A_R[t]` | Pedder adults in refuge streams | latent count | Adults in remnant tributary habitat |
| `T[t]` | Brown trout abundance | index | Annual trout state in the connected system |
| `P[t]` | Brown trout piscivory / large-body modifier | index | Transient early overshoot / trophy-trout signal |
| `C_L[t]` | Climbing galaxias abundance in lake | index | Lake pressure state for `G. brevipinnis` |
| `C_R[t]` | Climbing galaxias abundance in refuge streams | index | Refuge-stream pressure state |
| `U[t]` | Trophic upsurge state | index | Early productivity pulse after inundation |

## Core Process Structure

### 1. Trophic upsurge

Tier 1 uses a deterministic pulse shape, not a free-running ecological submodel.

- `U[t] = 0` before `1972`
- `U[t]` rises linearly from the onset of inundation to a fixed peak year in `1977`
- after `1977`, `U[t]` decays exponentially at `PR030`
- `PR029` controls peak amplitude
- `PR031` controls how strongly `U[t]` boosts Pedder productivity, implemented as stronger recruitment plus temporary relief of lake density pressure during the boom window
- `PR016` and `PR018` let `U[t]` also amplify trout abundance and piscivory

This choice preserves the now well-supported `1977` target while keeping Tier 1 minimal.

### 2. Brown trout

Brown trout are modeled as a single annual abundance state plus a separate piscivory modifier.

- `T[t]` starts near zero in the connected lake system before `1972`
- the fixed `1972` stocking event adds `350,000 * PR013` to the trout state
- annual trout update uses simple density-regulated growth with background capacity `PR015`
- effective trout capacity is temporarily inflated by trophic upsurge via `PR016`
- `P[t]` is baseline piscivory `PR017` plus an upsurge-linked overshoot term controlled by `PR018`
- the overshoot term decays after the `1977` peak at `PR019`

Tier 1 therefore represents the large-bodied trout phase explicitly, but without adding trout age or size classes.

### 2b. Delayed habitat transition

The loss of the original Lake Pedder habitat is treated as real, but not as an instantaneous step-function penalty.

- `connected[t]` still switches on in `1972` for trout and climbing-galaxias access
- `H[t]` is a separate inundation-transition forcing used only for Pedder habitat-penalty terms
- `H[t] = 0` before `1972`
- after `1972`, `H[t]` rises linearly to `1.0` over `PR040` years
- this keeps the documented early post-flood boom compatible with a later habitat-penalty contribution

### 3. Climbing galaxias

Climbing galaxias are represented by separate lake and refuge abundance indices.

- `C_L[t]` and `C_R[t]` begin from low initial states `PR022` and `PR023`
- visible expansion is delayed by `PR024`
- after the lag, `C_L[t]` and `C_R[t]` grow at `PR025` and `PR026`
- Pedder performance is reduced by climbing pressure through `PR027` in lake habitat and `PR028` in refuge habitat

Tier 1 treats climbing effects as a combined competition / predation pressure term rather than splitting those mechanisms.

### 4. Pedder recruitment, maturation, survival, and redistribution

Pedder dynamics are the biological core of Tier 1.

Annual update order:

1. compute total spawning adults from `A_L[t]` and `A_R[t]`
2. split spawning effort between lake-linked and refuge-linked recruitment using `PR005`
3. apply fecundity `PR004` and trophic-upsurge boost `PR031`
4. split new recruits between lake and refuge settlement using `PR006`
5. apply baseline juvenile and adult survival `PR001` and `PR002`
6. apply maturation from juvenile to adult using `PR003`
7. apply density dependence using `PR008`-`PR011`
   - implementation uses count-scale capacities derived from `PR008`, `PR009`, and `PR039`
   - the lake density term is temporarily relaxed by `U[t]` through `PR031` to let the model express a genuine post-flood boom rather than an instantaneous density-capped response
8. apply habitat penalty and threat effects:
   - lake habitat penalty `PR033`, scaled by the delayed habitat-transition forcing `H[t]`
   - trout effects `PR020` and `PR021`, scaled by `T[t] * P[t]`
   - climbing effects `PR027` and `PR028`, scaled by `C_L[t]` or `C_R[t]`
9. allow threat-driven redistribution from lake to refuge streams using `PR007`

Implementation note:

- `U[t]` and `H[t]` act in the current update year
- explicit trout and climbing states are treated as end-of-year states, so their effects on Pedder are applied with a one-year lag in the annual update
- this keeps the annual accounting consistent while avoiding an implausibly instantaneous post-stocking collapse in `1972`

### 5. Refuge habitat quality

Refuge-stream quality is an explicit Tier 1 modifier.

- `PR032` controls baseline refuge quality
- `PR034` buffers trout and climbing effects in refuge streams
- refuge quality must be high enough to support the observed final tributary persistence and the translocation baseline constraints

## Hypothesis Families

Tier 1 must support these five model families without adding new processes later.

### Habitat-only null

- Pedder responds only to inundation-driven habitat penalty and trophic upsurge
- trout and climbing effect coefficients are fixed to zero
- trout and climbing states may be omitted entirely or tracked passively without affecting Pedder

### Trout-only

- trout abundance and piscivory are active
- climbing effect coefficients are fixed to zero
- used to test whether trout alone can reproduce both early decline and terminal chronology

### Climbing-only

- climbing abundance states are active
- trout effect coefficients and piscivory modifier are fixed to zero
- used mainly as a falsification case against the anti-trout narrative

### Trout + climbing persistent joint-cause

- trout and climbing are both active
- trout piscivory is allowed only at baseline `PR017`
- the transient overshoot multiplier `PR018` is fixed to `1.0`

### Trout + climbing + transient perfect-storm overshoot

- trout and climbing are both active
- the upsurge-linked trout overshoot is active
- this is the only family that can express the full inundation → trophic upsurge → trophy trout → later climbing-dominance sequence

## Calibration Design

Tier 1 calibration is split into two layers.

### Historical-lake targets

These are the primary fit targets:

- `CT001`: pre-flood restricted range
- `CT002`: early post-flood boom
- `CT003`: `1977` peak-year target
- `CT004`: trout stocking plus early large-trout phase
- `CT005`: lagged climbing-galaxias dominance switch
- `CT006`: late-1980s stream-only persistence
- `CT007`: severe occupancy contraction in `1990-1991`
- `CT008`: terminal decline in `1992-1996`
- `CT009`: last natural-range record in `1996`
- `CT010`: zero detections through `2002`

### Intrinsic-baseline constraints

These are screening constraints rather than historical-lake fit targets:

- `CT011`: Lake Oberon establishment and predator-free growth
- `CT012`: Strathgordon delayed recruitment followed by establishment

The intended workflow is:

1. fit or filter candidate parameter sets against the historical-lake targets
2. reject parameter sets that imply implausible intrinsic Pedder dynamics when checked against Lake Oberon and Strathgordon

## Parameter Mapping

### State and process coverage

| Component | Parameter IDs |
| --- | --- |
| Pedder survival, maturation, fecundity | `PR001`-`PR004` |
| Pedder spawning allocation and redistribution | `PR005`-`PR007` |
| Pedder density dependence / carrying terms | `PR008`-`PR011`, `PR039` |
| Trout abundance trajectory | `PR012`-`PR016` |
| Trout piscivory and Pedder vulnerability to trout | `PR017`-`PR021` |
| Climbing expansion and Pedder vulnerability to climbing | `PR022`-`PR028` |
| Trophic upsurge pulse | `PR029`-`PR031` |
| Refuge and habitat-quality modifiers | `PR032`-`PR034` |
| Habitat transition timing | `PR040` |
| Observation and calibration nuisance terms | `PR035`-`PR038` |

### Standardized quantities

These remain in index units in Tier 1:

- `Brown trout abundance`
- `Brown trout piscivory modifier`
- `Climbing galaxias abundance in lake`
- `Climbing galaxias abundance in refuge streams`
- `Trophic upsurge`
- lake and refuge carrying terms

Pedder states are latent counts, but they should be interpreted as model-internal counts tied to sparse observations through nuisance terms, not as trusted historical census totals. `PR039` exists specifically to bridge the standardized carrying indices and those latent counts without pretending the model knows literal historical census sizes.

## Explicitly Deferred

These are out of scope for Tier 1 and must not be back-filled implicitly during implementation:

- no genetics or introgression in the core dynamics
- `Galaxias parvus` as a modeled driver
- no seasonal or monthly simulator
- no detailed trout size or age structure beyond `P[t]`
- no detailed climbing-galaxias stage structure
- no absolute fish-per-hectare thresholds for trout or climbing
- no direct present-day reintroduction decision model yet

## Implementation Defaults

- Use pattern-oriented stochastic simulation as the first calibration method.
- Treat hypothesis comparison as relative support across model families, not as courtroom-style single-cause attribution.
- Prefer rejection / filtering / synthetic-likelihood style fitting against the target table before attempting a heavier Bayesian wrapper.
- Counterfactual present-day coexistence runs should reuse the same parameterized structure, with `U[t] = 0` and no new stocking pulse after the historical period.
