# Common-model comparison: conditional scientific synthesis

19 September 2026. Candidate 2 remained frozen throughout execution. This report
describes the completed finite comparison. The map and synthesis were posted to
Fable in Correspondence thread 31, message 262; substantive review is pending.

## Scientific result

The comparison does **not** establish that direct trout effects, direct climbing
effects, or their combination are necessary to reproduce the declared patterns.
At the least stringent grid point (early-pattern lower 95% bound at least 0.50;
joint-weight lower bound at least 10⁻⁶), q = 0.005 admits qualified examples under
all four restrictions in every configuration, under both primary observation
representations. Every one of those 48 cells has examples with K_R ≥ 20 from
both search seeds. The result therefore does not depend entirely on the
specific K_R < 20 concern raised during protocol review.

This is compatibility with patterns and detection records, not evidence of
historical extinction. In the base configuration, qualifying R_H examples have
within-source, factual-weighted survival through 2002 of 0.992–1.000 across the
primary q scenarios that admit witnesses; R_T examples have survival 1.000.
Low detection scenarios can accommodate the late nondetections while fish
persist. These are simulator quantities conditional on specified parameters and
observation assumptions, not empirical survival probabilities.

Support is not stable across q, observation representation and thresholds.
At q = 0.20, homogeneous weights qualify at none of the 1,001 validated sources.
Shared-quality weights qualify at only two, both R_C under minimum dated
adult-first removals, one from each search seed. Thus there is no stable
exclusion set of restrictions across the full declared sensitivity grid.
Absence of a witness in a finite search remains distinct from causal exclusion.

## Map and precision

The complete [compatibility map](../data/common_model/compatibility_map.csv)
contains all 2,592 cells: six configurations × four restrictions × four q values
× three observation representations × nine cutoff combinations. The two
primary observation representations account for 1,728 cells:

| Classification | Primary cells |
|---|---:|
| Compatible witness found | 465 |
| Unresolved at cap | 284 |
| Not found at cap | 979 |

Cells reuse sources and histories and are not independent trials. These counts
are a map inventory, not model probabilities, evidence ratios, or measures of
biological importance. The episodewise independent-quality diagnostic adds
228 compatible, 134 unresolved and 502 not-found cells; it does not enter source
selection as another primary profile.

The table below shows qualified source counts for the **base configuration** at
the least stringent grid point. Each entry is homogeneous / shared quality;
sources can recur across columns. A zero means no qualified witness at this
slice, not necessarily a not-found classification: inspect the full map for
the unresolved distinction.

| Restriction | q = .005 | q = .02 | q = .05 | q = .20 |
|---|---:|---:|---:|---:|
| R_H: no direct biotic effects | 24 / 27 | 14 / 22 | 0 / 13 | 0 / 0 |
| R_T: no direct climbing effects | 7 / 7 | 0 / 4 | 0 / 0 | 0 / 0 |
| R_C: no direct trout effects | 29 / 32 | 11 / 29 | 1 / 9 | 0 / 0 |
| R_J: both pathways available | 13 / 16 | 5 / 12 | 1 / 2 | 0 / 0 |

All restrictions retain common invasive forcing and habitat/upsurge effects.
The richer R_J does not acquire a superiority claim from its extra mechanisms;
conversely, fewer sampled R_J witnesses do not demonstrate that removing a
mechanism improves the model. Refocusing explores different finite parameter
sets and dimensions. Structural arms also have separate refocusing searches,
including where a restriction renders the changed pathway inactive. Differences
in counts therefore contain search variation as well as structural sensitivity.

Threshold sensitivity matters even at fixed q. For example, base R_T has no
qualified cell at early cutoff 0.80 or 0.95, whereas R_H, R_C and R_J have some.
At joint cutoff 0.01 the base configuration has no witness under either primary
observation law. These predeclared numerical cutoffs are not independently
validated historical-adequacy standards.

Across all 1,001 validated sources, the number with qualified joint weights is:

| q | Homogeneous | Shared quality |
|---|---:|---:|
| .005 | 593 | 619 |
| .02 | 219 | 539 |
| .05 | 27 | 191 |
| .20 | 0 | 2 |

Qualification requires ESS ≥ 100, relative Monte Carlo error ≤ 0.10 and largest
normalised history weight ≤ 0.05. It is necessary but not sufficient to pass a
compatibility cutoff. Finite-log support is retained when ordinary weights
underflow. Unresolved cells include cases whose upper bounds reach the cutoffs
without qualified lower bounds; the zero-event upper bounds are not zero.
These intervals describe sourcewise simulation error; they are not simultaneous
confidence bounds across the searched grid or estimates of field-sampling error.

The archived `delta_log_W` reference is the largest validated log joint mean
within a **fixed q, observation representation and configuration**, across
restrictions and seeds. Its source and Monte Carlo error are reported. It is
not a cross-q likelihood ranking, a posterior weight, or a precision guarantee
for the reference itself. No q was selected from this comparison.
For example, at q = .20 under shared quality and minimum dated adult-first
removals, the largest-mean reference has ESS 82.01 and relative error 0.106,
so it fails qualification. The two lower-mean witnesses qualify independently.

## Capacity, process sensitivities and the removal exception

Of the 465 compatible primary grid cells, 448 include a witness with K_R ≥ 20;
17 depend entirely on K_R < 20 among the sampled qualified witnesses (nine R_H,
four R_C and four R_J). The complete labels are in the map. Passing the
insurance-establishment screen does not validate the historical refuge scale,
and K_R = 20 is a reporting boundary, not proof of demographic viability or a
hard upper bound on realised abundance.

The [qualified profile ranges](../data/common_model/qualified_profile_ranges.csv)
report K_R, PR011, K_R/PR011, PR033 and weighted terminal survival separately by
configuration, restriction, q and primary law for the permissive slice. Full
capacity strata, annual unconditional and factual-weighted refuge abundance and
presence, source exposures, CT005 levels and component pass fractions are in
the verified analysis archive. The current model still transports capacity
between the impoundment and insurance scenarios without site-area scaling;
the binary screen addresses poor establishment, not that calibration gap.

Exposure descriptors prevent a free coefficient from being mistaken for a
material exposure. Among 517 distinct sources witnessing the permissive primary
slice, 87 are R_J; neither active biotic pathway is below the declared 5% peak
isolated annual-mortality descriptor at any of those 87 sources. Zeroed pathways
remain exactly zero in the restricted models. This diagnostic concerns the
simulator's isolated hazards, not measured field mortality or causal necessity.

Neither environmental variance nor juvenile-side climbing produces a result
that is stable enough across observation assumptions to establish a necessary
mechanism. The two q = .20 shared-quality witnesses are a specific exception:

| Search seed | R_C source | K_R | Early-pattern probability | Joint mean | Weight ESS | Weighted survival |
|---|---|---:|---:|---:|---:|---:|
| 20260918 | adult-first, wave 3, source 106 | 75.28 | .917 | .00107 | 131.98 | .000018 |
| 20260919 | adult-first, wave 3, source 99 | 91.44 | .860 | .00523 | 119.55 | .000096 |

Both pass the permissive grid qualification. They supply examples of near-zero
conditional terminal survival without direct trout effects under this specific
configuration and observation law. Their unconditional survival fractions are
0.236 and 0.471 respectively: the near-zero values arise after factual
observation weighting. They do not establish a general removal
effect: the arm contains only the five strictly dated extractions, omits the
20 wild founders removed during 1990–1991, and is explicitly not a test of the
broader removal hypothesis. Both 1996 positives enter all configurations.

## Paired counterfactuals

The overshoot counterfactual covers all 254 final R_J sources, with 1,024 matched
validation streams each. It removes the piscivory overshoot only. Factual
validation weights remain fixed; altered histories are not reweighted to fit
the observations. The three paired restriction switches use the prescribed
first 64 streams at those same sources and remain diagnostic: ESS cannot exceed
64, so they cannot supply primary compatibility witnesses.

Among the R_J source/profile rows that meet the permissive primary compatibility
criterion, 213 overshoot contrasts have qualified factual weights and valid
counterfactual support for the terminal endpoint. Their survival changes range
from −0.02354 to +0.03358; the median is zero in every configuration. These are
conditional parameter-specific contrasts, not a population-average causal
effect or proof that the trophy phase was unimportant.

A further 61 qualifying factual source/profile rows have undefined overshoot
contrasts because a positive-factual-support altered history cannot supply a
dated extraction (17 adult-first and 44 juvenile-first). Their weight is not
discarded or renormalised away. The
[counterfactual range table](../data/common_model/counterfactual_qualified_profile_ranges.csv)
distinguishes profile counts from defined estimates. Full paired Monte Carlo
errors and feasibility masses are retained in the analysis archive. Sign or
small magnitude alone should not be interpreted without those uncertainties.

## Execution and evidence

Production ran on deep-server with eight workers from 2026-09-18 12:13:45 UTC
to 2026-09-19 01:34:45 UTC (11:34 AEST). It completed without a restart:

| Stage | Sources | Executed histories |
|---|---:|---:|
| Search | 28,800 proposed; 28,639 viable | 1,832,896 |
| Refinement | 3,446 | 882,176 |
| Frozen validation | 1,001 | 1,025,024 |
| Overshoot counterfactual | 254 | 260,096 |
| Paired restriction diagnostics | 254 × 3 | 48,768 |
| **Production total** | | **4,048,960** |

The 161 failed viability proposals received no stochastic histories and no
replacement draws. All allocations, refinement/validation memberships and
11,520 immediate-previous-wave local-parent links passed closure verification.
Every archived replicate and both streams were checked: 7,480,192 fresh seeds
are unique across phases and streams; all counterfactual/toggle streams match
the intended validation keys. Frozen source, wrapper, input, phase-output,
analysis-output and archive-parent hashes match. All 146 source-bundle files
were checked on the target, as were the complete raw archives.

Including the 712,000-history exact legacy replay gives 4,760,960 scientific
histories. Adding the conservative 15,000-history implementation-check ceiling
gives **at most 4,775,960**, below the 7.1-million hard ceiling. Earlier
uninstrumented local checks prevent an exact all-inclusive implementation
count; the conservative ceiling is retained. No new simulations were needed
for closure, and unused budget does not authorise additional search.

Evidence pointers:

- [Production verification](../data/common_model/production_verification.json)
  records counts, hashes, ancestry, seed coverage and the budget bound.
- [Retrieval receipt](../data/common_model/retrieval_receipt.json) verifies 50
  local artifacts; five large raw-history archives remain on deep-server and
  were verified there. The counterfactual and toggle raw files were retrieved.
- [Compact numerical summary](../data/common_model/results_summary.json) and
  [reporting script](../scripts/summarize_common_model_results.py) derive the
  report tables from hash-checked archived analysis files.
- Local detailed archive: `outputs/remote/common_model_20260918/production/`.
  Remote: `/data/codex/scratch/galaxias/common_model_20260918/production/`.
- [Independent results audit](common_model_results_audit.md) records the bounded
  check of central classifications, arithmetic and paired-weight interpretation.
  Independent formulas reproduced all 1,025,024 validation histories' 12,012
  profiles, all 2,592 map cells, q-specific references, capacity strata and all
  paired contrasts without a mismatch at the declared tolerances. The largest
  numerical discrepancy was 5.68 × 10⁻¹⁴. This is computational verification,
  not independent empirical validation.

The scientific boundary remains the observation model and the historical
population scale. This completed programme shows where the explicit null
restrictions can and cannot supply sampled compatible examples under declared
assumptions. It does not estimate field q, settle the historical refuge scale,
establish causal necessity, or support a publication claim without further
substantive review. No search, combined arm or new hypothesis has been added.
