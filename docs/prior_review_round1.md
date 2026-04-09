# Prior Review Round 1

## Summary

This pass converts the original `parameter_priors.csv` from a useful first draft into an ABC-ready prior pack. The major change is not just narrower numbers. It is a cleaner distinction between:

- priors that are genuinely anchored by direct Pedder evidence
- priors that are defensible only through insurance-population or comparative proxies
- priors that remain structural because the system still lacks direct effect-size data

The output of this round is therefore a more explicit and honest prior architecture, not a claim that all important uncertainty has been removed.

## How this pass was tightened

- The evidence ladder was applied consistently: `direct_pedder` first, then `insurance_population_proxy`, then `tasmanian_proxy`, then `comparative_proxy`, with `structural_assumption` retained only where no better empirical anchor exists.
- All 38 rows were revisited and given an explicit `sampling_transform` so the next calibration phase can sample on the intended scale without hard-coding transform decisions in the simulator.
- The new `model_family_parameter_map.csv` captures parameter activation and fixed settings for all five Tier 1 hypothesis families.
- The new `parameter_constraints.csv` captures only the biologically important joint rules that are easy to violate in code or sampling if left implicit.

## Parameter-group rationale

### Pedder life history

- These priors are now in relatively good shape.
- `PR003` and `PR004` are among the strongest in the whole pack because maturation timing and fecundity are directly described in Hamr (1995) and the official summaries.
- `PR001` and `PR002` are still partly proxy-based, but the Lake Oberon and Strathgordon growth trajectories now provide much better lower and upper plausibility bounds than we had in the first pass.

### Pedder movement and allocation

- `PR005` and `PR006` are still broad because the lake-versus-stream spawning and settlement split is not directly quantified.
- The defaults now lean more strongly toward stream-linked spawning and lake-linked juvenile settlement, which better fits the adfluvial life-history descriptions.
- `PR007` remains weak. The chronology clearly implies threat-driven concentration in refuge streams, but it does not tell us the annual redistribution rate.

### Density dependence and habitat capacity

- `PR008` and `PR009` remain index-scale priors because absolute Pedder densities are still too uncertain.
- `PR010` and `PR011` remain structural controls rather than empirical demography estimates. They are necessary to stop the model from confusing the `trophic upsurge` with unlimited growth.
- The important improvement here is not sharpness; it is clearer linkage to the historical boom and final refuge persistence.

### Trout abundance and piscivory

- This block improved materially because the current literature bundle is stronger than the first web-only pass.
- The one-off `350,000` fry release is now secure enough to anchor `PR013`, but the conversion from fry to model index is still one of the weakest priors in the pack.
- `PR016`, `PR018`, and `PR019` are now among the best-supported mechanism priors because Lake (2001), Chilcott et al. (2013), and Horner et al. (2025) all reinforce the same short-lived productivity-plus-trophy-trout sequence.
- `PR020` and `PR021` remain weak because the Pedder record shows predation and decline, but not a directly measured interaction coefficient.

### Climbing galaxias expansion and effect size

- The chronology for delayed `brevipinnis` rise is now much stronger than the first pass, so `PR024` is comparatively well grounded.
- The initial state priors `PR022` and `PR023` are better than before, but still weak because absence from early sweep-net samples is not the same as a clean abundance estimate.
- The growth and effect-size priors `PR025` to `PR028` remain among the least certain in the whole model. The evidence strongly supports later contribution and blocked recovery, but not precise rates or coefficients.

### Trophic upsurge

- This is now one of the strongest blocks in the model architecture.
- `PR029`, `PR030`, and `PR031` are all directly supported by the literature synthesis around the 1975-1977 littoral-fauna boom and the explicit `1977` peak signal for endemic galaxiids.
- The exact ecological mechanism is still simplified, but the existence and timing of the pulse are much firmer than in the first pass.

### Refuge habitat quality

- `PR032` improved substantially because the Bonnet Bay habitat description, Lake Oberon site logic, and Strathgordon spawning-lag story all point in the same direction: structured, slow-flowing littoral and inflow habitat is critical.
- `PR033` remains broad because habitat loss clearly mattered, but the size of the post-inundation lake penalty is still poorly separable from trout and climbing effects.
- `PR034` is still comparative-proxy dependent, but the final refuge habitat descriptions make the existence of a buffering effect hard to deny.

### Observation and nuisance terms

- These remain structural, but are now less arbitrary than in the first pass.
- `PR035` is moderately defensible because the late surveys were repeated and intensive enough that the model should not assume very poor detectability.
- `PR036` and `PR037` remain weak, and they will absorb a lot of mismatch between latent abundance and sparse historical counts.
- `PR038` is acceptable because the museum dominance-switch signal is real, but it still needs an observation-noise term around it.

## Strongest and weakest priors

### Strongest

- `PR003` maturation probability
- `PR004` effective fecundity
- `PR016` trout upsurge response strength
- `PR018` trout piscivory upsurge multiplier
- `PR019` trout piscivory decay
- `PR024` climbing colonisation lag
- `PR029` trophic-upsurge peak amplitude
- `PR030` trophic-upsurge decay
- `PR031` trophic-upsurge effect on Pedder recruitment

### Weakest

- `PR007` threat-driven refuge redistribution
- `PR013` stocking-to-index conversion
- `PR015` long-run trout background capacity
- `PR020` and `PR021` Pedder vulnerability to trout
- `PR025` to `PR028` climbing growth and effect-size terms
- `PR036` and `PR037` count-scaling and overdispersion nuisance terms

## Readiness assessment

### Ready for ABC sampling

- `PR001`
- `PR002`
- `PR003`
- `PR004`
- `PR016`
- `PR018`
- `PR019`
- `PR024`
- `PR029`
- `PR030`
- `PR031`
- `PR032`
- `PR035`
- `PR038`

### Acceptable but intentionally broad

- `PR005`
- `PR006`
- `PR008`
- `PR009`
- `PR010`
- `PR011`
- `PR012`
- `PR014`
- `PR017`
- `PR022`
- `PR023`
- `PR033`
- `PR034`

### Still weak and likely to dominate uncertainty

- `PR007`
- `PR013`
- `PR015`
- `PR020`
- `PR021`
- `PR025`
- `PR026`
- `PR027`
- `PR028`
- `PR036`
- `PR037`

## Residual source gaps that still matter

- `Historical IFC stocking records` remain the highest-value unresolved source for improving the trout-abundance and trout-piscivory block, especially `PR013` to `PR016`.
- `Original fish-series material behind the 1977 peak` still matters because it would tighten the `trophic upsurge` and early-boom priors, especially `PR029` to `PR031`, and would strengthen the calibration side at the same time.
- `Gaffney et al. 1992` still matters, but mainly for founder-history interpretation and recovery targets rather than for the main collapse-mechanism priors.
- `TMAG missing dates` are not a blocker for this phase. They may still improve chronology and appendix-grade forensic reconstruction later, but they do not presently limit any single high-leverage prior more than the gaps above do.

## Bottom line

The prior pack is now good enough to support an ABC-ready implementation phase. The next coding step should read this pack directly rather than reinterpreting it in code. The main uncertainty burden has shifted away from basic Pedder life history and toward interaction-strength terms, indexed trout build-up, and the observation bridge between latent model states and sparse historical counts.
