# Finite geometry and the fixed-plan worst-case diagnostic

## Complete family for the existing metric

Longitude tile centres are -165,-135,...,165 degrees; latitude centres are
75,45,15,-15,-45,-75 degrees. A tile belongs to the viewport exactly when its
circular longitude distance and latitude distance from the viewport centre are
both at most50 degrees. Its weight is proportional to the cosine of its latitude.

On either axis a membership indicator can change only when the viewport centre
crosses a tile centre plus/minus50 degrees. Testing every boundary and one point
inside each intervening open interval therefore enumerates all possible masks.
Include the yaw seam and pitch endpoints. Their Cartesian product produces
216 distinct masks with explicit orientation witnesses. No participant trace
is used to choose this family. Independent integer-grid enumeration is complete
for this fixed geometry because the breakpoints are integral and the open gaps
are wider than one degree; it produces the same family.

This is exact for the historical angular-window/tile-centre metric, not for a
perspective renderer, rolled camera, different FOV, pixel-exact projection or HMD.
The same mask/weights must apply to selected and reference representations.

For rung r and sampled second s, let v(s,r,m) be the reference-minus-selected
MSE under mask m. The segment's smallest possible raw difference is

    m(t,r) = (1/10) sum_{s in segment t} min_{m in family} v(s,r,m).

The analogous maximum bounds it above. Each per-second extremum is attained by
a saved mask. Taking the average of individual extrema is valid because the
uncertainty class permits independent changes between sampled seconds. No
motion-smoothness restriction is inferred from observed traces. Both intervals
are subsets of the former arbitrary-convex-tile interval, apart from handled
floating rounding boundaries. Intersecting the valid intervals preserves
validity and exact numerical nesting.

## Post-outcome upper bound on a fixed plan's worst-case repayment

This diagnostic was added after the primary outcomes and does not change the
admission method. It is separate from the optimistic impossibility certificate.

Let L(t,r) be the stored geometric lower bound in micro-MSE units. Before
intersection it is floor(10^6 m(t,r))-2. Native differences are differences of
two independently rounded MSE quantities. For the constructed extremal-mask
sequence their value is no greater than L(t,r)+5; the extra allowance covers
the two-unit outward guard, native rounding and arithmetic conservatively.
Intersection can only increase L, so it cannot invalidate this upper bound.
The reference rung is exactly zero and receives no artificial five-unit credit.

For every resource-valid precommitted path, compute completed credit using
max(0,L+5), the same actual durations, and the primary conditional timing
realization (fluid arrival envelope plus0.5s execution per segment). Ignore
quality-floor restrictions. Maximize that value over **all** resource-valid
paths, yielding B. For each fixed path there exists a geometric sampled sequence
that attains the corresponding raw minima; therefore

    max_fixed_path min_allowed_future credit <= B.

If B < D/2, no fixed plan can promise half repayment for every future sequence
in this uncertainty class. The ignored floors and generous micro-unit allowance
make this an upper bound, not an optimistic admission test. The implementation
also publishes a constructed sequence for the path maximizing this upper bound
and checks its native-quantity ledger. These are synthetic counterexamples, not
newly observed human trajectories. Different fixed paths may require different
counterexample sequences.

This does **not** prove impossibility for all adaptive policies, policies with
additional justified information, other timing/service models, or restricted
motion classes. It does not show that recovery is impossible on a particular
observed trace. The universal fixed-plan promise and observed-trace feasibility
have different quantifiers; they must not be conflated.
