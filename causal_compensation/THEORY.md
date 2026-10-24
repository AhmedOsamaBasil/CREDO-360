# Absolute-loss protection and a causal opportunity envelope

## 1. Objective and deliberate restriction

The earlier [allowance timing analysis](../allowance_scheduler/THEORY.md)
demonstrated that lower regret can coexist with worse absolute recovery. Here
we first impose a terminal unpaid-fraction limit alpha, then optimize regret
inside that feasible class. The original event loss D is never reduced by
forecasting, redefinition or fallback. A remaining fraction above alpha is a
violation, including when it was correctly predicted to be infeasible.

This first data-connected implementation restricts the service to one recipient,
one donor and at most one transfer. Each current transfer respects an actual
byte cap, recipient reference floor and donor loss <= .5 utility. Even a
zero-harm transfer consumes the one-transfer entitlement. This is a deliberately
restricted timing problem, not an unrestricted five-user streaming controller.
The general event-debt model is not silently replaced in old experiments.

Let g_t be available recipient gain at recovery period t. Since at most one
transfer is possible, delivered compensation is min(D,g_tau) when choosing
time tau. With no transfer it is zero. Define

    L(pi,g) = 1 - min(D, selected_gain(pi,g))/D,
    L*(g) = 1 - min(D, max_t g_t)/D,
    R(pi,g) = L(pi,g) - L*(g).

Only L* knows all future gains. D=0 is handled separately without division:
no compensation is owed and baseline service is used.

The quantities are objective utility, not human QoE. Later quality cannot
repair past displayed distortion. No transport, stall or perceptual guarantee
is inferred from these accounting constraints.

## 2. Causal forecast and information assumptions

There are six previously exposed scenes, each with six segments and 28 source
participant panels. Past segments 0--1 define a fixed artificial impairment;
segments 2--5 are recovery. Their measured viewport utilities are converted
to the previously used clipped index, then rounded to integer milli-units.
The exact rounding, menu construction, paired participant layout and all
hyperparameters are in [PLAN.md](PLAN.md).

At the first recovery decision, the forecaster receives only the original D
and three revealed gains: two past counterfactual opportunities and the current
opportunity. It receives no target future, scene ID feature, hidden scenario
label, future head movement or future capacity. Training trajectories exclude
the target content and both target source IDs. Using outcomes of other exposed
training trajectories is normal offline fitting, not access to the current
episode's future. All these data were exposed historically, so this computational
separation is not an independent test or a claim of unexposed participants.

Eight nearest training trajectories under a fixed L1 distance supply coordinate
min/max future gains, padded by .05 utility. The result is a rectangular envelope
G=product_t [l_t,u_t] on the integer lattice. Its coordinates need not share a
training trajectory; the robustness check includes their cross combinations.
The current gain is a singleton coordinate. The model is fixed at episode
start; it is not refitted after seeing the target future.

**Important upper-information assumption:** every policy receives exact current
counterfactual viewport utilities before choosing. Past counterfactual gains
are likewise available in this abstraction, including the two artificially
impaired segments. This is more information than a deployed player normally
has. The forecast is causal within this information model; the system is not
a causal viewport-estimation implementation. This stage asks whether timing
is useful even when current utility estimation is idealized.

Persistence (current gain plus/minus .05) and the physical range [0,D] are
also causal forecast controls. Full physical uncertainty is conservative but
can be uninformative. Neither interval construction has calibrated coverage;
the min/max of eight neighbors is not a conformal prediction guarantee.

## 3. Fixed causal policy class

Policies spend at the first positive gain reaching a fixed fraction of D:
theta in {0,1/4,1/2,3/4,1}. Thresholds are rounded upward to integer milli-units,
with minimum one. A sixth policy waits until the final period. If a transfer
remains unused, every policy takes any positive gain in the final period.
Only the observed current gain and the time index enter each decision.

This is a restricted, auditable policy class, not enumeration of every causal
strategy. A whole policy is selected once per episode. Expected outcomes are
computed exactly over its mixture weights; no random seeds are searched.
Rolling Nash/max-min retain the actual past event observations and see the
same current menus and limits. They are not deprived of event history in order
to manufacture a difference in performance.

## 4. Pathwise absolute-loss constraint

Retain policy pi only if

    max_{g in G} L(pi,g) <= alpha.

Every policy given positive probability must meet this inequality. We do not
merely require max_g E[L] <= alpha, which would permit individual episodes to
exceed the cap because of randomization even when their future is in G.

Among the retained policies, solve

    min_{p in simplex} max_{g in G} sum_pi p_pi R(pi,g).

Consequently, if the future belongs to G, every sampled path meets the terminal
loss cap. The regret bound holds in expectation over the policy draw for each
fixed exogenous future; it does not cover an adversary adapting to the draw.
Current quality, one-transfer and donor protections hold independently of
forecast correctness because every actual chosen action is checked locally.

If no policy is retained, the requested cap is marked infeasible **within this
policy class and envelope**, not physically impossible under every conceivable
controller. Fallback chooses the policy with smallest worst absolute loss,
then smallest worst regret, then a stable index. Alpha stays unchanged. Its
realized cap failures are counted. In particular, zero regret in a no-opportunity
case does not mean any of D was repaid.

## 5. Exact reduction of the integer envelope

Clip gains at D because larger gains have identical compensation. For each
future coordinate, include the interval endpoints and every policy threshold
and the adjacent integer immediately below it when inside the interval. Their
Cartesian product is the critical scenario set.

Between successive threshold cuts, each policy's first accepted time is fixed.
Selected compensation is therefore one coordinate or zero, hence affine on
that cell. Terminal loss is affine. Regret is `max_t g_t` minus that selected
coordinate, divided by D; it is convex. A nonnegative mixture of regrets remains
convex. Every point of the rectangular cell is a convex combination of its
vertices, so the maximum cannot exceed the largest vertex value. Integer
threshold-adjacent endpoints include both sides of every decision discontinuity.
Thus these finite scenarios attain the exact worst loss of every policy and
the exact worst regret of every mixture over the integer envelope.

This reduction would not automatically hold for arbitrary learned policies,
multiple transfers, coupled future action menus or real-valued gains without
an explicit convention at open threshold boundaries. Tests compare the critical
grid with all integer paths on small complete envelopes, not only solver output.

## 6. Numerical optimization, rational certification

The finite matrix game is solved with a standard linear program. The primal
distribution and sparse dual adversarial distribution are rationalized and
renormalized. The code then computes, in exact rational arithmetic:

    U = max_s sum_pi p_pi R(pi,s),
    Z = min_admitted_pi sum_s y_s R(pi,s).

Primal/dual feasibility yields Z <= optimum <= U. Publication requires
0 <= U-Z <= 1e-7. The saved U is a valid conservative bound, not a rounded
optimizer printout. This certificate is for the admitted threshold class.
An infeasible-cap fallback has no minimax-optimality certificate and is labeled
as such. All positive-weight policies still have exact hard-cap membership
checks; the LP tolerance cannot admit an unsafe policy.

This is a standard constrained minimax construction and duality certificate,
not a new general scheduling theorem. See the prior-art references in the
[allowance note](../allowance_scheduler/THEORY.md#7-prior-art-boundary), including
[Regan and Boutilier, AAAI 2010](https://ojs.aaai.org/index.php/AAAI/article/view/7740)
for minimax-regret policy computation and
[MIT online-algorithm notes](https://courses.csail.mit.edu/6.854/20/Notes/n25-online.html)
for randomized online analysis. Compensation with controlled donor degradation
also predates this project; see the earlier event-local objective note.

## 7. What the new cap costs in the original counterexample

For D=2, current gain 1 and future gain in [0,2], unconstrained minimax regret
is 1/4, using equal probabilities of spending now and waiting. Waiting leaves
all D unpaid if the future gain is zero. At alpha=.5, every waiting policy is
therefore excluded. Spending now meets the cap and has worst regret .5. Even
alpha=.75 cannot include a policy with pathwise loss 1. At alpha=.25 no causal
policy can satisfy both futures; the software reports infeasibility rather
than averaging a violation away. This is the intended protection/regret trade-off.

## 8. Model misses and evaluation boundaries

On the first observed gain outside the D-capped envelope, model breach is
permanently flagged. If unused, the allowance switches to greedy current
compensation. This remains locally protected but cannot recover a missed
earlier opportunity. A model-admitted episode may violate alpha when the
forecast is wrong; such violations are reported, not described as guaranteed
recovery. Raw and D-capped future-envelope membership are both measured.

Development outputs retain every episode, forecast neighbor, certificate,
policy-weighted trajectory and control. The same participant IDs and scenes
occur repeatedly, so no independence claim or inferential p-value is attached.
An adverse result does not trigger a hidden parameter change. The frozen screen
requires nontrivial admission, adequate coverage, no admitted cap violations,
and gains over both rolling comparators in both cohorts with a mean-quality
guard. Passing only one scene, sensitivity or pooled mean is insufficient.

No buffer, elapsed-time, switching or network mechanism is simulated here.
The hypothesis remains a bounded-impact service-timing contribution. Before
a fresh reserve or a revised positive manuscript claim, utility prediction,
uncertainty coverage and transport feasibility must still be demonstrated.
