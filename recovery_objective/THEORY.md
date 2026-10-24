# Event-local, bounded-impact service compensation

This note defines a different, explicit service objective. It does **not**
retroactively change the primary endpoints of the failed v1/v2/v3 experiments.
It supplies elementary proofs and exact executable witnesses, not a claim of
new scheduling theory or a successful immersive-streaming algorithm.

## 1. What recovery means here

A displayed low-quality frame cannot be repaired by a later high-quality frame.
Here **recovery means future service compensation in declared objective-utility
units**, not reversal of past damage, a measured perceptual benefit, or a claim
that PSNR differences are psychological currency. Quality index units are used
only for continuity with the testbed. Choosing a defensible application utility
remains necessary before an empirical claim.

Consider one observed impairment episode E ending at restoration. Affected
users I, the event interval and reference utilities r_i,t must be declared
independently of the recovery policy. Define the initial event loss

    D_i = sum_{t in E} [r_i,t - q_i,t]_+       (i in I),
    D_i = 0                                  (otherwise).

Use equal-duration periods in this reference model. Variable-duration service
would require explicit duration weights throughout; it is not implemented.
References are logged service entitlements, not hindsight estimates of unknown
HMD counterfactuals. This does not identify how much loss was caused by the
network, the representation, the participant, or prediction error. No surplus
before the event cancels D. Even surplus within the event does not cancel a
different period's positive shortfall under this selected loss convention.

After restoration, specify K recovery periods and feasible joint action sets
A_t. Each action has exact utility vector q_t(a) and resource usage c_t(a).
The analysis assumes current action utilities are known; this is not a
calibrated or deployable prediction model. A service-reference vector b_t has
an actual feasible reference action, with c_t <= C_t. It is chosen by the same
exogenous rule for all policies and is not lowered to make recovery easier.
Changing content can change b_t, but cannot change the original D.

## 2. The protection contract

Affected users retain their present service floor: q_i,t >= b_i,t for i in I.
For each unaffected donor j, declare a per-period allowance epsilon_j >= 0
and a total episode allowance B_j >= 0. Let

    h_j,t = [b_j,t - q_j,t]_+,
    h_j,t <= epsilon_j,
    sum_{s<=t} h_j,s <= B_j.

All actions must also satisfy the same resource cap C_t. These constraints
define the protected feasible action set. Every online comparator receives
the same set, original D, observed history and remaining donor allowances.
The rolling rules ignore D in their objective, not because they are denied it.
Positive donor surplus does not replenish B: the budget bounds actual service
reductions, not a signed net balance. A feasible reference action ensures a
safe fallback in this abstraction. A real system in which that action becomes
infeasible must expose the violation; this model does not silently relax b.

This is a **service-quality** protection contract. Resource equality does not
prove equal rebuffering, latency or playback stalls. None is modeled here;
later deployment would need separate clock/buffer constraints.

## 3. Delivered compensation, not forgiven debt

Let d_i,0 = D_i and, after each delivered action, update

    g_i,t = [q_i,t - b_i,t]_+,
    p_i,t = min(d_i,t-1, g_i,t),
    d_i,t = d_i,t-1 - p_i,t.

Because affected users cannot be taken below b during this recovery episode,
no new service deficit is hidden inside this update. If that floor is violated
outside the model, the new loss must be recorded separately, not ignored.
No debt expires, no forecast feasibility projection writes it down, and excess
after full payment creates no credit against a later event. At K, remaining
d_i,K is explicitly unpaid. It is not counted as recovered or silently
reassigned to other users. A new event, departure or overlapping episode needs
an additional policy and is outside this single-event reference model.

**Conservation identity.** For every i and k,

    D_i = d_i,k + sum_{t<=k} p_i,t,
    0 <= d_i,k <= D_i.

Proof: each update subtracts exactly the delivered p, which is between zero
and the preceding d. Telescoping proves the identity. Delay, infeasibility,
expiration and renaming the target supply no p and cannot satisfy it.

## 4. Objective and the feasibility benchmark

For D_i > 0, define the residual fraction rho_i,k = d_i,k / D_i. If there are
no affected users with positive D, the recovery objective is zero. The selected
deadline objective is lexicographic minimization of

    (max_i rho_i,K, sum_i rho_i,K).

First reduce the largest unpaid fraction; then reduce aggregate unpaid
fractions. This is a normative choice that treats equal fractions of different
initial losses equally. It can prefer clearing a small loss over partially
serving a large one. We do not call it the unique correct definition of fairness.
Report absolute unpaid utility, the per-user vector, post-event mean/worst
quality, donor harm and resources alongside it.

The exact offline benchmark enumerates feasible **integral** action sequences
under all cumulative protections. Among equal terminal objectives it minimizes
the sum over periods of outstanding fractions, then maximizes the product of
per-user post-event average utilities, then minimizes resources. The product
is equivalent to a sum of logs because utilities are positive. This benchmark
knows the entire future schedule; online controls do not. It is not a method
whose performance can be claimed against less-informed online baselines.

Write rho* for the optimum largest residual fraction. Full compensation is
feasible exactly when rho*=0. A positive rho* certifies that full recovery is
impossible **for this declared horizon, action model and protection budget**.
It does not imply permanent physical impossibility. Individually maximizing
each user's surplus may give incompatible joint allocations, so individual
headroom is only a necessary bound, not a joint repayment certificate.

For zero B and Pareto-efficient b_t, no positive compensation is possible:
every protected action must satisfy q_t >= b_t componentwise, while Pareto
efficiency rules out a strict increase for any component. Hence g_i,t=0.
If the baseline is not Pareto efficient or capacity expands, compensation may
be free. Otherwise any proposed benefit must disclose whose service is reduced.

## 5. Causal reference rules

All rules select from the current protected feasible set and use exact current
utilities. They have no future schedule or future impairment information.

- **Rolling Nash:** maximize the product of per-user quality sums over the
  previous H-1 observed periods plus the current candidate.
- **Rolling max-min:** maximize that vector in lexicographic ascending order.
- **Stateless Nash:** maximize the current quality product.
- **Capped debt-weighted priority:** maximize sum_i d_i * min(d_i,g_i).
  This is a MaxWeight-style comparison, not a reproduction of a particular
  packet scheduler or a claim of a new policy.
- **Greedy recovery:** minimize (max_i rho_i,next, sum_i rho_i,next).

Ties use current Nash utility, then resources, then stable action name. The
name convention is reproducible, not a theorem of anonymity under exact ties.
H=24 is inherited for the rolling comparisons; it is not tuned here.

### Conditional result: one recipient and independent opportunities

Suppose exactly one D is positive, protected action sets are exogenous, choices
do not alter later opportunities, and total donor allowances cannot bind.
Let m_t be the maximum achievable current excess g_i,t. Then greedy recovery
achieves

    d_i,K = [D_i - sum_t m_t]_+.

Proof: until payment, its terminal criterion chooses the largest clipped
current gain. No future action can provide more than m_t at t. Applying this
pointwise upper bound gives a lower bound on any terminal residual; greedy
attains it by induction. It also minimizes each prefix residual and therefore
the residual area. Full payment requires and is achieved by sum_t m_t >= D_i.
This elementary separable result does **not** cover coupled donor budgets,
multiple recipients, uncertain prediction, adaptive future capacity or buffers.

## 6. Analytical separation from rolling fairness

Two users have reference (3,3), an old event left D=(2,0), and the last H-1
observations all equal (3,3). Current actions are B=(3,3) and A=(4,2), with equal
resource use. Allow one unit of donor loss per period and two in total.

Rolling Nash compares (3H)^2 for B against (3H+1)(3H-1)=(3H)^2-1 for A, so
strictly chooses B. Rolling max-min likewise prefers minimum 3H over 3H-1.
Choosing B leaves the rolling history unchanged. Both rules therefore leave
all D unpaid indefinitely on repeated such opportunities. The two-step greedy
rule chooses A twice and repays D exactly, using two donor-quality units.

This is a real difference in **objective**, not a universal superiority result:
the greedy rule's post-event worst-user quality is 2, versus 3 for both rolling
rules. Average quality is 3 for all. A known debt-weighted rule also repays D.
Event memory and bounded compensation are therefore not exclusive inventions
of this implementation. The constructed example is not statistical evidence.

## 7. Counterexamples that block a general greedy claim

### Multiple recipients and changing opportunities

Let D=(2,1,0), b=(3,3,3) and one donor tolerate one unit per step, two total.
At t=1 the options are b, X=(4,3,2), Y=(3,4,2). At t=2 only b or Y remain.
Greedy chooses Y first: X leaves fractions (1/2,1), while Y leaves (1,0),
so their common maximum is 1 and the latter has smaller sum. It cannot then
repay user 1, ending at largest residual 1. X then Y leaves fractions (1/2,0)
and achieves optimum 1/2. The simple debt-weighted comparator chooses X then Y
as well. The greedy rule loses to an existing design principle even in this
small example; no new universal advantage is established.

### Scarce donor budget: rolling Nash can win on recovery itself

Let D=(2,0), b=(3,3), donor total budget 1 and per-step limit 1. At t=1 choose
b or (4,2); at t=2 choose b or (5,2). Greedy spends the budget on the first
gain of 1 and leaves residual 1. With balanced rolling history, rolling Nash
chooses b first; later it prefers (5,2) and pays the full 2. The oracle agrees
with waiting. The one-recipient theorem does not apply because the total
donor allowance couples decisions across time.

### No future-blind rule can always match the oracle

Keep that identical first period and budget, but change the second period to
baseline only. Now spending at t=1 is uniquely better for terminal recovery.
The two futures have identical observable prefixes and different optimal
first actions. Any deterministic causal policy must choose the same first
action in both, so it is suboptimal in at least one. Randomization cannot
guarantee optimality almost surely in both. Future prediction or reservations
may help under additional assumptions; they cannot be assumed known for free.

## 8. What has and has not been established

The executable checks establish internal consistency and concrete possibility/
impossibility results for this small exact model. They do not establish a new
queueing theorem, general online optimality, calibrated recovery guarantee,
improved viewport fairness, realistic stall protection, or empirical novelty.
The accompanying counterexamples are intentionally retained. They are not
held-out scenes and have no confidence intervals or statistical p-values.

Before another empirical campaign, a candidate needs a justified way to manage
the recovery/harm/deadline trade-off under uncertain future opportunities,
plus comparisons with direct rolling fairness and debt-weighted compensation.
First check whether real actions admit meaningful compensation under a
declared harm budget. Do not fund a new holdout merely because an objective
can be made different from Nash. No new campaign is authorized by this note.

## 9. Prior-art boundary

Compensating flows after channel errors while limiting degradation of other
flows is established prior art, not a new principle introduced here:

- T. S. Eugene Ng, I. Stoica and H. Zhang, *Packet Fair Queueing Algorithms for
  Wireless Networks with Location-Dependent Errors*, IEEE INFOCOM, 1998.
  [Author-hosted original](https://www.cs.cmu.edu/~hzhang/papers/INFOCOM98a.pdf).
  Its CIF-Q framework explicitly addresses compensation and graceful degradation.
- F. P. Kelly, A. K. Maulloo and D. K. H. Tan, *Rate control for communication
  networks: shadow prices, proportional fairness and stability*, JORS 49,
  237-252, 1998. [Original paper](https://web.stanford.edu/class/cs244/papers/ShadowPricesFairnessStability.pdf).
  Logarithmic-utility fairness is not a new objective family.
- M. J. Neely, *Network Optimization Notes*, Spring 2023, Sections VI and VIII.
  [Author's notes](https://ee.usc.edu/stochastic-nets/docs/network-optimization-notes.pdf).
  Virtual queues and time-average constraint handling are established; their
  guarantees cannot simply be transferred to this finite-event construction.

These sources delimit the claim, not constitute a completed systematic review.
Any future novelty claim must address this compensation literature directly,
in addition to multimedia scheduling and recent viewport-quality methods.
