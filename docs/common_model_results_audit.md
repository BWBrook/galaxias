# Independent audit of the common-model central results

Date: 19 September 2026  
Archive: `/data/codex/scratch/galaxias/common_model_20260918/production`  
Frozen protocol SHA256: `c165e25bfa223cbb79ba00fce75f099c13979746b2d516ae06e93af5243879d8`

## Verdict and audited claim

**Conditionally supported.** The archived calculations support the operational
claim that none of the four restrictions has a stable exclusion or necessity
result across the declared q, observation-law, structural-arm and cutoff grid.
They also support the narrower claim that direct trout mortality is not needed
to produce sampled compatible histories under several declared scenarios. They
do not identify the historical mechanism, estimate field detection, or yield an
empirical extinction probability.

I independently recomputed the central results from raw archived histories. I
did not run simulations, call the project analysis functions, change source
code, or inspect the search/provenance chain already assigned to the production
closure audit.

## Independent checks

I implemented the 14-record observation likelihood, its homogeneous,
shared-quality and episodewise-independent variants, Wilson intervals, stable
log-mean calculations, ESS and MC qualification, grid classification, capacity
strata and fixed factual-weight paired estimands independently. Input CSVs were
read with round-trip floating-point parsing.

- All **1,025,024** validation histories were read: 1,001 sources with exactly
  1,024 histories each. The resulting **12,012** source/q/observation profiles
  matched the archive in every early-pattern bound, log joint mean, ordinary
  mean and MC error, support count, ESS, relative error, largest weight and
  qualification flag. The largest numerical discrepancy was
  `5.68e-14` in a binary log mean; no comparison failed tolerance.
- All **2,592** compatibility-map cells were independently classified. Status,
  witness counts, best-source identity, capacity label and reported best values
  had zero mismatches.
- All **12,012** q-specific reference assignments and delta-log-weight values,
  and all **576** capacity-stratum rows, matched exactly.
- Fixed factual weights were independently rebuilt for all **3,048** overshoot
  source profiles and all **9,144** endpoint contrasts. Feasibility, precision,
  contrast, MC-error and invalid-support fields had zero mismatches.
- The same check covered all **9,144** paired-toggle profiles and all **27,432**
  endpoint contrasts. No paired diagnostic met the primary ESS requirement, as
  specified. All invalid-removal cases remained undefined without
  renormalisation. There were no cases where positive invalid support was hidden
  by an underflowed displayed mass.

The detailed machine-readable comparison is
[`results_audit.json`](../data/common_model/results_audit.json).

## Findings that survive scrutiny

The primary map contains 465 compatible, 284 unresolved and 979 not-found cells.
These are repeated sensitivity cells, not independent observations or model
probabilities.

At the permissive cutoffs (early lower bound 0.50 and joint lower bound
10^-6), q = 0.005 has qualified witnesses for all 48 combinations of six
configurations, four restrictions and two primary observation laws. Every
combination is represented by both search seeds and by at least one witness
with `K_R >= 20`. This directly undermines any claim that the finite comparison
establishes a necessary direct trout effect, climbing effect, or joint biotic
effect.

The result is highly detection-dependent. Across the 1,001 sources, primary MC
qualification declines from 593 homogeneous and 619 shared-quality profiles at
q = 0.005 to zero homogeneous and two shared-quality profiles at q = 0.20. The
two high-q witnesses are both R_C (climbing but no direct trout effect) under
minimum dated adult-first removals. Their `K_R` values are 75.28 and 91.44 and
their ESS values are 131.98 and 119.55. Their unconditional terminal-survival
fractions are 0.236 and 0.471, but factual joint weighting (early-pattern,
removal-validity and observation terms) reduces
survival to 0.000018 and 0.000096 and concentrates extinction time near 1996.
Thus high-q compatibility is an example of detection-conditioned near-extinction,
not general support for the removal arm or an empirical extinction estimate.

The q = 0.20 source with the largest shared-quality joint mean is not a witness:
its ESS is 82.01 and relative MC error 0.106. The map correctly uses the two
lower-mean but qualified sources. The descriptive q-specific reference must
therefore remain separate from witness status.

Capacity below 20 is not the general explanation for compatibility. Of the 465
compatible primary cells, 448 contain a witness with `K_R >= 20`. Seventeen
cells rely only on sampled witnesses below 20: nine R_H, four R_C and four R_J,
all at q = 0.02 or 0.05. Those 17 should retain the explicit low-capacity label;
the threshold itself is a diagnostic boundary rather than demographic
validation.

Among 274 permissive, primary, qualified R_J source profiles, 213 overshoot
contrasts have valid support. Their terminal-survival changes span -0.02353 to
+0.03358 and have median zero in every configuration. Sixty-one additional
profiles are correctly undefined because an altered history with positive
factual support cannot supply a dated removal. These results do not support a
stable directional survival effect of the piscivory overshoot, but the selected
source set and mixed MC precision prevent an absence-of-effect claim.

The 64-history restriction toggles are useful only as fixed-parameter process
diagnostics. Just 228 of 9,144 source/profile/toggle combinations meet their
diagnostic concentration rule, and none can meet the primary ESS >= 100 rule.
They cannot replace the independently refitted restriction comparison.

## Strongest remaining threats

1. **Observation-scale identifiability.** q is a scenario parameter, and the
   compatibility and survival interpretation changes sharply with it. Model
   counts are not calibrated to surveyed fish or historical effort.
2. **Compatibility is not survival evidence.** Base R_H witnesses have
   factual-weighted survival of 0.992-1.000 and base R_T witnesses have survival
   1.000, while the two q = 0.20 witnesses have near-zero weighted survival.
   The same compatibility framework therefore permits opposing demographic
   histories under different observation assumptions.
3. **Finite search and declared cutoffs.** A not-found cell excludes neither an
   unsampled parameter region nor a mechanism. No primary cell passes the
   strictest 0.95/0.01 cutoff pair; this does not identify which biological
   pathway is wrong.
4. **Refuge scale and site transport.** The insurance screen filters poor
   establishment but does not calibrate historical refuge capacity or correct
   transport of capacity between sites.
5. **Removal and counterfactual scope.** The dated-removal arm omits the 20
   founders removed in 1990-1991 and is not a test of the broader removal
   hypothesis. Invalid altered removals materially limit the counterfactual
   subset.
6. **Structural interpretation.** R_C supplies 183 of the 465 compatible
   primary cells and 43 of 48 primary q-specific reference sources, whereas R_T
   supplies 35 compatible cells. This makes climbing-without-trout the most
   recurrent sampled explanation, but separate refocusing, different effective
   dimensions and non-independent grid cells preclude model ranking or field
   attribution.

## Required reporting boundary and residual uncertainty

No numerical correction or rerun is required. The synthesis should retain the
q-specific results, the 17 low-capacity-only cells, MC qualification, the 61
undefined qualifying counterfactual profiles, and the distinction between a
descriptive reference and a qualified witness. Cell counts should not be
presented as probabilities, likelihood ratios or votes for mechanisms.

After those constraints, the result remains conditional on the observation
law, latent abundance scale, stable relative catchability in CT005, finite
search coverage, structural arms and declared thresholds. It is credible as a
map of sampled compatibility and as evidence against a strong necessity claim;
it is not a causal reconstruction of the Pedder galaxias decline.
