# Density-regulation assessment

23 September 2026. Assessment of Fable's Correspondence thread 31, message
425, requested by Barry. The completed common-model and singleton-guard
experiments remain preserved. This note proposes a demographic amendment;
it does not authorize or implement a replacement kernel or another search.

## Diagnosis

The current implementation adds annual recruits proportional to total adults,
then applies the same post-recruitment density-survival factor to juveniles
and adults. This occurs in `simulation.py:233-263`,
`common_model.py:241-266` and the corresponding mate-guard transition.
Under neutral forcing, write juvenile survival as s, adult survival as a,
maturation as m and the compartment's density factor as d. Then

    J_next = d * [s * (1-m) * J + allocated_recruits]
    A_next = d * [a * A + s * m * J]

At a positive equilibrium, A/J = d*s*m/(1-d*a). Thus the same strong
regulation needed to reduce hundreds of offspring per adult also depresses
adult survival and the adult fraction. The consequence is material even
before habitat change or invader exposure.

Direct calls to the unchanged two-compartment kernels, using resolved
`transient_perfect_storm` defaults, neutral forcing and 1,000 deterministic
burn-in steps, reproduce Fable's calculation:

| Diagnostic | Result |
| --- | ---: |
| Original total juveniles | 232.966532 |
| Original total adults | 4.900302 |
| Original adult fraction | 0.020601 |
| Original effective annual adult survival, lake | 0.050023 |
| Original effective annual adult survival, refuge | 0.058454 |
| Nominal adult survival PR002 | 0.650000 |
| Guarded cycle, total adults in successive phases | 46.747546; 0.333762 |

The numbers are totals over both compartments, except the explicitly labelled
survival rates. The 1,000-step calculation diagnoses the limiting behaviour;
it does not replace the archived 100-step initialization. The two subsequent
unguarded steps agree to floating-point precision; the guarded second step
returns to the first phase.

Changing only PR004=250, PR001=0.6, PR002=0.85 and PR010=0.1 gives 1,107.311293
juveniles and 50.896958 adults (4.3945% adults), also matching Fable's example.
These checks confirm the examples and mechanism, not an exhaustive statement
about every point in the prior. At default values, a single neutral transition
from 31 founder adults and no juveniles leaves 0.268969 adults and 254.981643
juveniles. This demonstrates founder thinning, without establishing that it
alone explains each of the 108 archived viability failures.

## Biological interpretation and candidate repair

The structural problem is the placement and parameterization of regulation
within the life cycle. Beverton-Holt recruitment remains a defensible candidate.
Recruitment regulation and adult density-dependent processes are distinct
modelling assumptions; adult density effects are not biologically impossible.
See [van Gemert and Andersen (2018)](https://academic.oup.com/icesjms/article/75/4/1296/4817093)
for an explicit model separating those processes.

The recommended candidate regulates establishment of new juveniles, leaving
existing adult survival at its declared baseline before specified threats:

    R(A) = b*A / (1 + b*A/R_max)
    J_next = s*(1-m)*J + R(A)
    A_next = a*A + s*m*J

This is a schematic single-compartment expression, not a frozen replacement
for the two-compartment model. Recruitment allocation, spawning habitat,
upsurge, mating closure and census timing still need explicit specification.
Juvenile-only thinning is a separate candidate, not automatically equivalent
to regulating only incoming recruits.

For this recruitment-only candidate, a positive equilibrium has adult fraction
s*m/(1-a+s*m): 41.18% at current defaults, and 12–77.27% over the rectangular
survival/maturation bounds. These are mathematical consequences, not estimated
Pedder adult fractions. Fable's suggested 30–60% is not an empirical acceptance
interval established by the available evidence. The census definition matters:
including larvae changes the denominator substantially.

PR004 needs re-expression. Hamr (1995), available in
`literature/pedder/hamr_1995_envirbiolfishes_pedderensis.md`, reports 200–1,200
eggs **per female**. The current prior calls 250–900 an effective number of eggs
or recruits **per adult**. A replacement must distinguish eggs, breeding/female
contribution and survival to the juvenile census, or use one explicitly defined
composite productivity parameter. Simply copying PR004 into b would preserve
the ambiguity. Likewise R_max is a recruitment ceiling, not equilibrium total
abundance: any interpretation as capacity requires a derived mapping. For the
schematic compartment, let r=(1-a)/(s*m) and g=r*[1-s*(1-m)]. Then a positive
equilibrium requires b>g, with A*=R_max*(1/g-1/b) and N*=(1+r)*A*. The
unresolved cross-site capacity issue must remain explicit.

## What the earlier checks missed

The deleted Module 1.5 report is recoverable with
`git show 3bd828d^:docs/module1_5_review.md`. Its gates checked peak timing,
boom ratios, late totals, invader dominance timing and persistence across 20
stochastic runs. Neither that report nor the retained gates in
`tests/test_latent_kernel.py` checked stage composition or realised adult
survival. Its broad ecological-readiness conclusion exceeded those checks.

Exact replay and serial/parallel agreement establish implementation
reproducibility. They do not establish demographic adequacy. The old numerical
results remain valid descriptions of their specified kernels; their compatible
witnesses should not currently support plausible population-history narratives,
causal rankings or model-derived conservation recommendations. The factual
record, observation-likelihood mathematics and documented data limitations
remain useful. Ecological equifinality under a repaired kernel remains to be
demonstrated.

## Recommended next tranche

First define the census stages, recruitment productivity and capacity mapping,
then assess the proposed demographic map analytically and deterministically.
Check effective adult survival, stage composition, low-density growth, stable
initialization from multiple starts, and the Oberon/Strathgordon founder
scenarios. Diagnose cycles rather than choosing a convenient burn-in parity.
The hard singleton closure also needs evaluation on the revised map.
Strathgordon's imposed spawning-habitat switch checks implementation; reproducing
its imposed timing is not independent biological validation.

Acceptance should concern coherent life-history behaviour across declared
parameter ranges, not recovery of the old compatibility map or a chosen adult
percentage. Freeze the resulting amendment before any new comparative search.
A production comparison would need newly justified parameter ranges, a new
search and its own resource envelope; replaying selected old witnesses cannot
substitute for that comparison. No such run was started in this assessment.

## Provenance

Read-only numerical diagnostics used the existing local locked environment.
No historical stochastic trajectories were generated. Git HEAD was
`81e37202f6322e37ac7f1b0070402b76b7967a82` with prior uncommitted programme files.
One bounded independent methodological check reproduced the default fixed
point and guarded cycle, derived the equilibrium ratios and capacity mapping,
and supported the diagnosis with the biological qualifications recorded above.
Verified unchanged SHA-256:

- `common_model.py`: `2031373352dbdb55b30db571dc7b861e67f804fc0b5709ef99233f73e8e463c4`
- `mate_guard.py`: `7da473275457d9970c7b6a748e4ac92043c96ccdd14266142fb6e02827bdb332`

Correspondence's embedded connection reports API version 2. The complete
response read was message 425; retrieval checkpoint 468; explicit acknowledgement
425. Astra posted the checked assessment as message 473 at 2026-09-23 02:47 UTC;
the recommendation is with Barry, and no additional Fable work was requested.
Original frozen protocols, source archives and completion receipts are unchanged.
