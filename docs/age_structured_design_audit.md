# Independent methods check: age-structured candidate 1

27 September 2026. One bounded read-only audit by the native
`age_structure_methods` specialist, integrated and checked by Astra. Scope:
the new age kernel, forcing adapter, observation primitives, evidence registers
and candidate protocol. No historical fitting or ecological inference was run.
The auditor made three single-update calls in two diagnostic probes and read
the focused tests. This is computational/methodological scrutiny, not independent
data or empirical validation.

**Disposition: suitable for Fable's substantive review; not ready for scientific
dispatch.** The audit found two implementation/provenance defects and one RNG
contract that needed explicit qualification:

1. Initial code multiplied deterministic spawning quality after Beverton–Holt.
   The audit probe with potential supply 100, C=10 and Q=2 returned 18.1818;
   the specified supply-side calculation gives 9.5238. Q now multiplies supply
   before density regulation; only mean-one recruitment noise acts after it.
   A regression verifies simultaneous supply/limit scaling. This defect was
   corrected before either recorded qualification attempt or a scientific run.
2. A count event could both add and remove fish, so pre-event state and removal
   eligibility referred to different populations. Such combined events are now
   rejected; separate ordered event IDs are required.
3. Inserting a no-op checkpoint changed the same-seed stochastic trajectory
   (232 versus 249 total in the diagnostic example), because survival draws use
   event segments. The accepted solution is a frozen, hashed union calendar with
   explicit no-op placeholders in every paired arm and observation profile.
   `complete_event_calendar` enforces matching IDs, times and compartments.
   Qualification does not claim arbitrary checkpoint-insertion invariance.
   A calendar change invalidates replay qualification.

The check confirmed the life-table inversion, start/terminal cohort indexing,
age-two breeding onset, actual integer male guard, recruitment-only regulation,
one-month plus eleven-month nursery exposure, shared mean-one post-BH noise,
and conditional early/late Poisson identity. It agreed that 2008 juvenile
detection must not be assigned mechanically to a 2008 birth event.

Parent review also rejected silently dropped terminal-age additions, corrected
the treatment of old age-0 transfers after spawning, and replaced a vacuous
zero-recruitment hazard test with positive-recruitment checks. The equilibrium
constructor explicitly requires the candidate's 1:1 sex ratio. Diagnostics now
separate marginal-over-Z and conditional-on-Z means, the pre-hazard draw and
surviving newborns. Qualification was repeated after this diagnostic naming
change; both completed attempts are preserved and their numerical histories
are identical.

Residual scientific judgments for Fable are the reconstructed founder accounts,
R0 and site-scale search supports, pooled mating, age/length accessibility and
deliberate coarsening of insurance catches. The source conflicts are retained,
not resolved by model agreement. The full linked-site runner must conserve each
realized transfer vector, reject impossible removals without replacement and
use a common calendar. The scorer must map evidence once, including replacement
of the old early-count and late-annual-zero contributions by the conditional
capture block. Lake digitisation and synthetic observation/recovery controls
remain pre-dispatch work under the reviewed design.
