# Module 3.5 Sensitivity Sweep Results

## Run Summary

The first remote Module 3.5 sensitivity sweep was run on Nectar after resizing
`deep-vm` from parked `c3.xsmall` to `c3.large`. The VM was parked back to
`c3.xsmall` after artifacts were copied back.

Remote execution used:

- host: `nectar-codex` on `deep-vm`
- flavor during runs: `c3.large` (8 vCPU, 16 GiB RAM)
- repo path: `/data/codex/repos/galaxias`
- scratch base: `/data/codex/scratch/galaxias`
- artifact base: `/data/codex/artifacts/galaxias`
- Stage A: 1000 draws per family
- Stage A retention: 100 proposals per family
- Stage B: 20 historical stochastic replicates
- final acceptance cap: 50
- workers: 4 for the primary run; 4 per run for the two concurrent seed repeats

Seeds:

| seed | remote artifact directory | local mirror |
| --- | --- | --- |
| 20260410 | `/data/codex/artifacts/galaxias/module3_5_sensitivity_20260518T104633Z` | `outputs/remote/module3_5_sensitivity_20260518T104633Z` |
| 20260411 | `/data/codex/artifacts/galaxias/module3_5_sensitivity_seed20260411_20260518T105533Z` | `outputs/remote/module3_5_sensitivity_seed20260411_20260518T105533Z` |
| 20260412 | `/data/codex/artifacts/galaxias/module3_5_sensitivity_seed20260412_20260518T105533Z` | `outputs/remote/module3_5_sensitivity_seed20260412_20260518T105533Z` |

Each remote artifact directory contains the Module 3.5 diagnostic bundle plus a
`raw_run/` copy of the underlying Module 3 calibration tables.

## Resource Outcome

The `c3.large` size was sufficient for this sensitivity tier. The primary run
finished in about five minutes, and the two repeat seeds ran concurrently with
eight worker processes using the full VM cleanly. Memory use remained low.

## Sampler Health

The constraint-aware sampler held at the larger scale:

| seed | habitat_only_null | trout_only | climbing_only | persistent_joint_cause | transient_perfect_storm |
| --- | --- | --- | --- | --- | --- |
| 20260410 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 20260411 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 20260412 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

`module3_5_sampler_failures.csv` is header-only for all three runs.

## Accepted Family Mix

The 50 accepted proposals per seed were consistently split among the three
mechanism-rich families.

| seed | climbing_only | persistent_joint_cause | transient_perfect_storm | trout_only | habitat_only_null |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20260410 | 15 | 16 | 19 | 0 | 0 |
| 20260411 | 19 | 17 | 14 | 0 | 0 |
| 20260412 | 13 | 19 | 18 | 0 | 0 |

Across seeds, accepted-count means were:

| family | mean accepted | range |
| --- | ---: | --- |
| persistent_joint_cause | 17.3 | 16-19 |
| transient_perfect_storm | 17.0 | 14-19 |
| climbing_only | 15.7 | 13-19 |
| trout_only | 0.0 | 0 |
| habitat_only_null | 0.0 | 0 |

Interpretation: the larger sweep rejects the earlier climbing-only-only
impression. The current evidence supports a stable frontier of climbing-only,
persistent joint-cause, and transient perfect-storm proposals, while excluding
trout-only and habitat-only-null at this sensitivity tier.

## Best Proposal By Family

| seed | global rank | family | proposal | stochastic overall distance |
| --- | ---: | --- | --- | ---: |
| 20260410 | 1 | climbing_only | `climbing_only:p00216` | 162.643 |
| 20260410 | 2 | transient_perfect_storm | `transient_perfect_storm:p00144` | 166.904 |
| 20260410 | 3 | persistent_joint_cause | `persistent_joint_cause:p00162` | 167.924 |
| 20260411 | 1 | persistent_joint_cause | `persistent_joint_cause:p00884` | 171.810 |
| 20260411 | 2 | climbing_only | `climbing_only:p00903` | 178.909 |
| 20260411 | 3 | transient_perfect_storm | `transient_perfect_storm:p00860` | 185.171 |
| 20260412 | 1 | persistent_joint_cause | `persistent_joint_cause:p00078` | 168.924 |
| 20260412 | 3 | climbing_only | `climbing_only:p00367` | 184.010 |
| 20260412 | 4 | transient_perfect_storm | `transient_perfect_storm:p00466` | 197.074 |

The top family is seed-sensitive, but only within the three mechanism-rich
families. The distance gap among those families is small relative to the gap to
trout-only and habitat-only-null.

## Target Leverage

The accepted-proposal penalties are still dominated by the late-history targets:

| seed | largest accepted target penalties |
| --- | --- |
| 20260410 | `CT007` 90.141, `CT010` 76.882, `CT009` 30.000 |
| 20260411 | `CT010` 84.615, `CT007` 75.364, `CT009` 30.000 |
| 20260412 | `CT007` 105.731, `CT010` 58.761, `CT009` 30.000 |

`CT004` and `CT006` are small in accepted proposals, typically 1.667. This
means family ranking is still mostly being shaped by the late contraction,
last-occurrence, and zero-detection observation bridge rather than by the
presence of trout stocking alone.

## Target-Omission Sensitivity

With no target omitted, the target-sum winner was `persistent_joint_cause` in
all three seeds. The single best stochastic overall proposal was climbing-only
for seed `20260410`, but the target-sum sensitivity still favored persistent
joint-cause.

Important target-block result:

| omitted block | seed 20260410 winner | seed 20260411 winner | seed 20260412 winner |
| --- | --- | --- | --- |
| none | persistent_joint_cause | persistent_joint_cause | persistent_joint_cause |
| `CT007` only | persistent_joint_cause | climbing_only | persistent_joint_cause |
| `CT010` only | transient_perfect_storm | climbing_only | persistent_joint_cause |
| `CT007,CT009,CT010` | transient_perfect_storm | persistent_joint_cause | persistent_joint_cause |
| `CT004,CT005` | persistent_joint_cause | trout_only | persistent_joint_cause |

Interpretation: the late terminal block is influential, but removing it does
not produce a simple climbing-only story. It mostly shifts the best target-sum
proposal between persistent joint-cause and transient perfect-storm. The
`trout_only` appearance after removing `CT004,CT005` in one seed is a warning
that the explicit mechanism targets are doing useful exclusion work.

## Mechanism Parameter Plausibility

Accepted proposals do not appear to require one obviously pathological family
shortcut. However, the accepted set leans on nuisance/observation parameters:

- `PR037` survey overdispersion is high across accepted families, typically
  about 3.0 to 3.4.
- `PR036` survey count scaling sits around 0.28 to 0.34.
- `PR039` latent count scale varies by family and seed, roughly 80 to 135 in
  accepted medians.
- Mechanism-rich accepted proposals retain moderate trout effects, with
  `PR020` around 1.0 to 1.36 and `PR021` around 0.42 to 0.56.
- Transient perfect-storm accepted proposals retain `PR018` above 1.8, so the
  transient trout-piscivory multiplier remains active rather than collapsing to
  the persistent-joint simplification.

## Interpretation

The sensitivity sweep supports moving beyond the sampler-repair phase. The
important result is not that one mechanism family has won; it is that
habitat-only-null and trout-only are consistently outside the accepted frontier,
while the three families involving climbing galaxias remain competitive.

The most scientifically useful next step is a Module 3.75 observation-bridge
diagnostic around `CT007`, `CT009`, and `CT010`, unless a larger PBS
confirmation is desired first. The current sweep is already strong enough to
show that late survey/detection modelling is the main lever on final mechanism
ranking.

## Recommended Next Step

Build Module 3.75 before Module 4:

- decompose `CT007` into occupancy and count components;
- inspect whether `CT009` should remain a hard last-year match or become a
  softer terminal-window constraint;
- test zero-detection sensitivity in `CT010` against plausible detection/count
  nuisance ranges;
- keep `CT004`/`CT005` active because they are doing necessary mechanism
  discrimination.

After Module 3.75, rerun the same Nectar sensitivity tier. Escalate to
`kunanyi` only if the Module 3.75-confirmation grid grows beyond a handful of
seeds or target-bridge variants.
