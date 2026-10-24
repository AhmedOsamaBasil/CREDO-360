# Limited cumulative recovery reserve

## 1. Capacity evidence is not capacity entitlement

The previous audit's multiplier is relative to the **two-user baseline payload**,
not to physical link capacity. Three times a modest baseline demand may fit a
link; three times an already saturated allocation cannot. Neither statement
establishes that spare service actually exists in this application.

The repository's30 PCAP series measure observed traffic on captured interfaces.
They do not identify latent path capacity or unobserved competing traffic.
Earlier Mininet capacities were configured, and corrected v1/v2/v3 capacity
sequences were synthetic. These are useful controlled conditions, not an
empirical distribution of post-impairment headroom. Counting multiple switch
interfaces also does not create independent end-to-end capacity measurements.

RFC5136 distinguishes usage, capacity and available capacity, including their
protocol layer and measurement interval. Observed traffic alone cannot identify
the unused portion without the missing capacity/competing-load information.
[RFC5136, Sections2.3.4--2.3.7](https://www.rfc-editor.org/rfc/rfc5136.html#section-2.3.4).

For slot t of duration tau, let B_t be original baseline bytes and A_t the
payload bytes actually available to this controlled group by its deadline,
after other protected traffic, overhead and safety margins. Require B_t<=A_t.
This idealized A_t is known at decision time in the analysis; a real deployment
needs an admitted service budget or a validated causal estimate with explicit
underprediction/overprediction treatment. A past throughput observation is
not itself a guaranteed future A_t. No such estimate is validated here.

## 2. Two separate ledgers

Let R>=0 be a fixed episode entitlement for additional payload bytes. For a
chosen joint representation requiring S_t bytes, debit

    e_t = max(S_t - B_t,0),
    z_t = z_(t-1) + e_t,       z_0=0,
    S_t <= A_t,               z_t <= R.

R does not refill within this recovery episode. A smaller-than-reference
transfer does not earn a refund. An idle past slot does not supply physical
capacity to a future slot. The reserve authorizes a cumulative amount; A_t
independently limits when it can be sent. Invalid baseline feasibility raises
an explicit error instead of silently changing the quality reference.

This is established budget/token accounting, not a new traffic regulator.
RFC2697 describes byte-count token metering; the present finite episode budget
is not an implementation of its two-bucket marker. RFC2212 separately accounts
for peak/burst constraints and admission when providing guaranteed service.
Neither standard confers a delivery guarantee on this prototype.
[RFC2697](https://www.rfc-editor.org/rfc/rfc2697.html),
[RFC2212](https://www.rfc-editor.org/rfc/rfc2212.html).

The quality ledger is separate. Initial event loss D_i is immutable, and credit
is min(d_i,[q_i-b_i]_+). Outstanding loss decreases only by delivered credit.
The declared target is max_i(d_i/D_i)<=1/2 at the deadline, not low regret or
a newly reduced reference. The main analysis protects both users' current
reference qualities: donor loss is exactly zero. Auxiliary donor constraints
from the frozen core remain enforced if supplied, but no new allowance is
silently granted. Every realized action is integral.

## 3. Conditional causal plan and independent recursion

Declare a finite exogenous set of possible future action menus, references and
capacities. A deterministic policy maps an observed prefix to a current action.
Prefixes include action bytes and baseline/available bytes, not a latent future
label. Enumerate only policies whose realized paths satisfy both ledgers in
every scenario. Optimize worst terminal unpaid fraction; tie-break by sum of
scenario losses, maximum spend, sum spend, then enumeration index. The sum is
only a deterministic tie-break, not an estimated expectation.

Admission requires loss<=1/2 in **every** scenario. When this set is empty,
publish an explicit rejection and the best-effort result, not a successful
recovery certificate. Randomizing among policies that violate the target on
some scenarios cannot create the same pathwise guarantee.

An independent Bellman recursion groups scenarios by the currently observed
prefix, minimizes over protected reserve-feasible actions, and takes the
maximum over next-observation groups. At the deadline its value is unpaid
fraction. Induction on remaining depth proves equivalence with exhaustive
causal policy enumeration: each common-prefix decision is chosen once, and
after a distinguishing observation each child may choose its own continuation.
This standard finite robust planning calculation is a reference solver, not
a new optimization theorem or scalable controller.

Rolling Nash maximizes the product of rolling quality totals (equivalent to
sum log for positive totals); rolling max-min lexicographically maximizes
their sorted values. Greedy recovery minimizes current normalized remaining
loss. They use identical current actions, histories, reserve and capacity.
The supplied future set is public problem information; these rules do not
use it by definition. The causal plan's advantage can therefore reflect that
additional model use. The independent Bellman solution is the model-aware
control, and the future-known oracle is explicitly an unattainable benchmark
when the scenario has not been revealed. No future model is fitted here.

## 4. Analytical separation and necessary qualifications

Take one recipient with D=1 and reference qualities(3,3). The two observed
impairment samples are(2.5,3), so the event ledger is consistent. Every boost
preserves the other user at3. Baseline costs one normalized byte unit; an
ordinary boost costs two and uses one extra unit. Peak capacity is two and
the cumulative reserve is one: exactly one such boost fits.

If current gain is a and next gain is either c or b, with0<a<c<=b<=1, both
rolling rules prefer the immediate strictly improving boost. Their worst
unpaid loss is1-a. Waiting and then using the revealed next offer gives
worst loss1-c. Thus the conditional improvement is c-a. For a=.4,c=.6,b=.9,
the causal plan's worst loss is.4, versus.6 for both rolling controls and
greedy. It meets half-repayment in both declared futures. Eighteen rational
parameter cases check this formula. It depends critically on the future
lower bound c; it is not a distribution-free streaming result.

With reserve two, both boosts fit, and these rules recover the entire loss:
the timing separation disappears. If the actual next offer vanishes outside
the model, the waiting rule leaves all loss unpaid, worse than the immediate
rule. The executor records model breach and uses reserve-safe greedy fallback;
it does not preserve the missed repayment guarantee. If a current baseline
cannot fit, even that fallback is infeasible and must stop explicitly.

**Offline feasibility is not causal admission.** Let the first offer give.3
for.4 extra units. The second is either.3 for.6 units, or.6 for1 unit. Reserve
is1. In the first future an oracle buys both; in the second it skips the first
and buys the larger second offer. Each repays.6. A causal rule must make the
same first decision in both futures. Spending first prevents the large later
offer; waiting misses the small first offer. Its worst repayment is at most.3,
so worst unpaid loss is.7 and the half-repayment contract must be rejected.
This is an exact information/indivisibility obstruction, not a failed solver.

Additional cases retain vanishing opportunities, delayed revelation, no
reserve and no contemporaneous headroom. Quality, unpaid-debt area, donor
loss and spent bytes are reported rather than only the favorable metric.

## 5. Exact exposed-catalogue reserve requirements

Use the prior168 exposed episodes unchanged. For each peak factor lambda,
consider all current floor-respecting actions with zero donor loss and
S_t<=lambda*B_t. A multiple-choice DP maps accumulated capped integer gain
to minimum sum e_t and its integral path. Greater gain at no greater cost
dominates; cap gain at D, not at the admission threshold. Induction over slots
establishes the minimum-cost frontier. Brute-force small instances check it.

Query the least reserve reaching ceil(D/2) and maximum repayment at each
fixed reserve fraction. Full donor-upgrade alternatives remain available to
the rolling controls under the same masks. A difference from those controls
can reflect objective priorities, not necessarily timing novelty; the matched
greedy-compensation control is retained. The offline DP uses future tables;
none of these exposed-table calculations validates a new future predictor.

Demand conversions use actual encoded payload: bytes*8/(10*10^6) Mbit/s per
slot, and total extra bytes*8/(40*10^6) average extra Mbit/s. The minimum-reserve
witness need not minimize peak rate. These encodes are1920x960, not8K delivery;
network overhead, background sessions, buffers and within-slot capacity
variation remain unmodeled. Required capacity is not measured spare capacity.

## 6. What must precede another holdout

1. Establish a defensible current payload service budget with other traffic,
   overhead and deadlines accounted for. Do not infer it from passive traffic.
2. Select a cumulative reserve justified by admission/resource economics,
   not by whichever grid cell wins on these exposed outcomes.
3. Demonstrate a useful causal lower-opportunity model and quantify its misses;
   analytical guarantees are conditional on that model being correct.
4. Retain matched rolling and greedy controls and a model-aware optimizer.
   Prove separations under the chosen objective before claiming a new method.
5. Only then freeze a new experiment and reserve genuinely unused data.

Historical traffic CSV/JSON and the legacy live runner have pre-existing
Git checkout newline variation. Their metadata bind both original raw bytes
and an explicitly listed CRLF-to-LF canonical hash. Verification accepts that
newline-only difference, not arbitrary text changes. New method/data/result
files retain their normal exact-byte checks; no historical file is rewritten.

This work supplies an executable contract and diagnostic boundaries. It does
not establish absolute novelty, field-realistic headroom or publication readiness.
