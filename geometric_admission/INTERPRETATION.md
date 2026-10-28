# Geometric bounds: tighter rejection, no positive admission

The method and protocol were published as `533a402` before evaluating the six
exposed scenes. The contract and previous point-planning controls were kept
fixed. No new media, private pose access, physical playback, network trial,
training, fresh holdout or manuscript change was performed.

## Primary outcomes

| Certificate family | Impossible /168 | Abstain /168 | Admit /168 |
|---|---:|---:|---:|
| Arbitrary convex tile weights | 112 | 56 | 0 |
| Complete geometric viewport masks | 134 | 34 | 0 |

The additional22 impossibility certificates are all ParkFountains01 episodes.
The34 abstentions consist of its remaining6 episodes and all28 River01 episodes.
These counts hold under ideal,0.5s conditional execution and unbounded execution.
Without an execution bound positive deadline admission is not justified anyway.
Zero admissions still means undefined precision, not a successful safe system.

The geometric bounds use all216 masks of the existing100°×100° angular-window
metric, not a selected subset of observed poses. Every envelope is at least as
tight as the old convex envelope. Mean interval-width reductions across the12
recovery-segment/upgraded-rung cells per scene range from19.1% to50.7%.

The mean best certified repayment bound rises from2.06% to16.83% for
ParkFountains01 and from6.91% to22.14% for River01. Both remain well below the
unchanged50% target. This is a substantial numerical tightening, but not useful
positive admission. There is no confidence-interval or perceptual interpretation
of these deterministic bounds.

All1,344 point-only episode/timing/control rows are unchanged. Point planner and
cost-greedy still admit28 River01 episodes and fulfill27 in replay; the false
promise remains. Rolling Nash/max-min each admit17 and fulfill4 under the exact
floors. Applying the geometric gate to any of their proposed paths admits zero.
The earlier conclusions about scene concentration, identical point/greedy paths
and tiny native floor losses are retained; see the prior admission interpretation.

## What the zero-admission result does and does not mean

There are two distinct questions:

1. **Could recovery succeed for some viewport trajectory?** The optimistic upper
   certificate rules this out for134 episodes under the fixed catalogue/resource
   model, even allowing all four segments to finish and ignoring quality floors.
2. **Can one fixed plan promise recovery for every allowed future trajectory?**
   A separate post-outcome diagnostic rules that promise out for all168 episodes
   in the temporally unrestricted sampled-viewport class at the primary timing
   allowance. Even with floors removed and a generous rounding allowance, the
   largest episode-specific upper bound on best worst-case repayment is32.16%.

The second result is stronger than merely observing a failed sufficient test;
the [derivation](THEORY.md) constructs geometrically valid sampled counterexample
sequences and upper-bounds the best fixed plan's worst-case credit. It is not a
claim about all adaptive policies or physically smooth head motion. The synthetic
sequences are explicitly labeled and are not recorded participants or new data.

There is no contradiction with27 observed River01 episodes being offline feasible:
success for an observed trajectory does not establish a promise over every
possible future trajectory. Do not confuse abstention, observed infeasibility,
universal fixed-plan failure and the optimistic impossibility certificate.

## Boundaries and research consequence

The geometry is exact only for the original coarse tile-centre, cosine-weighted
angular rectangle. It is not a perspective frustum, physical HMD, lens model,
new quality metric or subjective validation. Initial debt/reference telemetry
is still assumed correct. The transfer and0.5s execution envelopes remain
conditional; no new deployment guarantee or timing measurement was added.

Further rounding or fixed-plan certificate adjustments are not a justified route
to a successful universal promise in this model. The next substantive decision
is whether to pursue an explicitly risk-limited service with a justified
uncertainty model, study a separately specified adaptive-information mechanism,
or position the work as a feasibility/measurement contribution. None of those
choices is validated by this result, and another fresh holdout is premature.
