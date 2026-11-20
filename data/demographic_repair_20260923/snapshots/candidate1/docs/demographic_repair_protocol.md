# Recruitment-regulated demographic repair: candidate 1

23 September 2026. Barry approved the demographic repair as a priority in
Codex after the diagnosis in `common_model_density_regulation_assessment.md`.
This protocol covers implementation and bounded local qualification. A new
comparative search, new empirical priors and historical inference follow only
after substantive review of this formulation and its evidence. Preserve the
original kernels, protocols, inputs and results unchanged.

## Endpoint and scope

Deliver a usable, separately versioned demographic transition, explicit census
and parameter definitions, reproducible analytical/deterministic qualification,
small stochastic and serial/parallel checks, and one independent methods audit.
Post this package to Fable for a bounded scientific review. Do not select
parameters by the historical compatibility map or claim restored ecological
equifinality. No commit, push or publication is included.

The local envelope is at most 1,500 deterministic diagnostic paths of at most
2,000 annual steps, plus 256 small stochastic scenario executions of at most
38 years. These are development/qualification calculations, not calibration,
refocusing, or an extension of the completed production experiment. There is
no remote dispatch and no restart of the paused follow-through automation.
Record actual counts. Preserve failed attempts rather than overwriting them.

## Annual census and reproductive closure

Retain lake/refuge compartments and two annual states. At the recorded
post-breeding/end-year census t, J_t includes young-of-year and older immature
fish; A_t denotes fish eligible to breed in the next annual season. It is a
breeding-eligibility class, not a measured gonadal maturity census on that date.
Recruitment in update t uses A_(t-1). Only J_(t-1) survives and matures during
that update; incoming recruits cannot mature immediately. Consequently recruits
entering J_2008 can enter A_2009 but cannot reproduce before update 2010.
The two-state approximation does not fit an age-specific maturation curve,
guarantee a maximum age of six, or establish the proportion breeding at ages
three and four. Do not describe the eligibility fraction as a measured adult
fraction without a matching census definition.

Retain pooled breeders A=A_L+A_R and the necessary-count guard A<2 => no
recruitment. Apply the same coarse threshold to deterministic fractional states;
report its consequences. This is neither an explicit sex model nor proof of
mate encounter between compartments. Stochastic states must be integer fish
counts; reject fractional inputs. For the small historical smoke, round the
analytic starting state explicitly, record it, and do not hide the change.

## Transition and independent inputs

Demography consists of s_J, s_A, maturation m, baseline effective recruitment b,
and lake settlement fraction p. RecruitmentLimits supplies separate C_L,C_R for
each scenario; a missing scenario is an error. C denotes an asymptotic **mean
annual recruitment** in fish/year, not a hard cap on a Poisson realisation and
not equilibrium census abundance. There is no implicit translation from
PR004, PR008–PR011 or PR039.

With w_L=p and w_R=1-p:

    x_i = b * A * w_i * Q_t
    E[R_i] = x_i / (1 + x_i/C_i,t), or zero if A<2 or C_i,t=0
    J_i,next = s_J*(1-m)*J_i + R_i
    A_i,next = s_A*A_i + s_J*m*J_i

Use Poisson recruitment and binomial survival/maturation in stochastic mode.
Existing common-model stage-specific hazards and lake-to-refuge movement act
after these transitions. None of the newly produced recruits thins existing
adults or existing juveniles through density mortality.

b combines female/breeding contribution, fecundity and survival to the juvenile
census. It is not eggs per female. The literature supports egg counts but does
not identify this composite; do not recycle the old 250–900 prior as b.

For the common-forcing adapter, normalise spawning quality by its neutral
value Q0=(1-PR005)+PR005*PR032, so b means neutral effective recruitment.
Q_t includes Q(H)/Q0, the specified spawning-habitat switch and the existing
upsurge multiplier M=1+PR031*U. Retain M on the lake recruitment limit as well;
the refuge limit stays fixed. This placement preserves the previously specified
two upsurge pathways. It is explicit and subject to review: BH(M*x,M*C)=M*BH(x,C),
so the lake response is linear in M at fixed A and spawning quality, not
quadratic. It is not independent evidence for those pathways.

Reuse the common invader forcing and connected, lagged exposure calculations,
without invoking old initialization or old abundance-index/capacity functions.
No historical observation score or compatibility classification is calculated.
The annual/within-year observation bridge needs review before a new search.

## Analytical predictions

Let r=(1-s_A)/(s_J*m) and g=r*[1-s_J*(1-m)]. For a positive neutral equilibrium,
J_i=r*A_i. Total adults solve

    sum_i w_i*b / (1+w_i*b*A/C_i) = g

over active recruitment routes. A_i=R_i(A)/g. A positive unguarded equilibrium
requires the effective low-density recruitment across active routes to exceed g.
Report whether it also satisfies A>=2; do not initialize a guarded history at
an inconsistent positive solution. The eligibility fraction is
s_J*m/(1-s_A+s_J*m). No 30–60% empirical target is imposed.

Engineering reference: s_J=.35, s_A=.65, m=.7, b=4, p=.7; historical C=(105,45).
The analytic prediction is J_total=114.026337, A_total=79.818436,
N_total=193.844773 and eligibility fraction .411764706. Adult survival before
threats remains .65. This is a test fixture, not a recovered pre-flood census.

Separate illustrative insurance limits: Oberon C=(1050,450), Strathgordon
C=(350,150). Their factors of ten and ten-thirds relative to the historical
fixture span larger established populations without asserting estimated site
capacity. These values, and any future priors, require scientific review.
Use existing dated founder inputs and spawning-habitat schedules. Strathgordon's
2008 switch is imposed input, so matching it verifies timing implementation and
does not independently validate habitat causality.

## Frozen diagnostic design

Before inspecting repaired outputs, use the following deterministic grid:

- s_J in {.15,.35,.60}, s_A in {.45,.65,.85}, m in {.50,.70,.85};
- b/g in {.5,1,1.5,3,6}, including decline and critical-boundary controls;
- total recruitment limit in {15,150,1500}, divided .7/.3: 405 cells;
- 18 allocation stress cells at reference survival and b=4: p in {.35,.7,.9}
  crossed with C in {(105,45),(150,0),(0,150),(149,1),(1,149),(75,75)}.

For each cell compare the unguarded analytic fixed point with one exact
deterministic transition. For guarded dynamics, use three starts: 31 lake
adults with no other fish, half the positive analytic state, and twice that
state. For subcritical/zero analytic solutions, use fixed nonzero starts of
5 and 500 in each state for the latter two. Iterate to a declared tolerance
or 2,000 steps. Record extinction approaches, positive fixed points, cycles,
and unresolved-at-cap cases; critical slowing and guard-induced failure to
establish must not be silently relabelled as numerical defects.

For each insurance site, cross b/g in {1.5,3,6} with limit multipliers
{.1,1,10}, preserving all 18 deterministic outcomes. Also report the reference
insurance trajectories, a neutral reference from multiple starts, and the old
and guarded-old reference burn-ins as diagnostic comparisons.

Small stochastic qualification: 32 seeds each for the reference Oberon and
Strathgordon scenarios, and eight seeds for each of four common-model
restrictions under base historical forcing: 96 unique paths, executed once
serially and once with two workers (192 executions). Compare records exactly.
Do not interpret survival frequencies in this small smoke as scientific
survival estimates. Tests and debug reruns also count toward the finite envelope.

## Acceptance and reporting

Required mechanical checks: finite nonnegative states; integer stochastic
states; exact reproductive delay and guard; no zero/singleton-total rebound;
neutral existing-adult survival independent of b and C; analytic fixed-point
agreement; conserved movement totals; explicit scenario limits; no legacy
fecundity/capacity dependence; preserved invader forcing and null restrictions;
reproducible event-keyed streams and exact serial/parallel agreement.

Report reference convergence, multi-start behaviour, all exceptions across the
grid, implied low-density growth and eligibility fractions, and capacity
sensitivity of founder establishment. The diagnosis's alternating default
cycle should disappear; do not force this result by choosing burn-in parity.
Unexpected cycles, adult suppression, algebra failures or hidden cross-site
coupling require repair/review before claiming the core qualified.

A passing qualification establishes implemented demographic coherence under
declared assumptions. It does not validate b, site limits, the observation
bridge, chronology likelihoods, causal attribution or historical reconstructions.
One bounded independent audit and Fable's substantive review close this tranche.
