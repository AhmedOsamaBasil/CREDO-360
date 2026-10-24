# Allowance timing under uncertain compensation opportunities

## 1. The unchanged contract and the new decision

The [event-local compensation model](../recovery_objective/THEORY.md) remains
unchanged. A past event leaves fixed losses D_i. During K equal-duration
recovery periods, each action has exact current utility q_i,t and a common
exogenous feasible service reference b_i,t. Positive-loss recipients may not
fall below b. Other users may surrender at most epsilon_j per period and B_j
in total, measured as positive service loss [b_j,t-q_j,t]_+. Positive surplus
does not refill their allowance. Resource constraints also hold at each step.

Delivered compensation is min(d_i,t-1, [q_i,t-b_i,t]_+). Outstanding d decreases
only by that quantity: it cannot expire, be redefined away or become negative.
This models future service compensation, not reversal of a damaged frame or
psychological equivalence between past and future quality.

The unanswered decision is **when to spend** B. Using it for a small gain now
can prevent a larger gain later; saving it can miss the only opportunity.
The present candidate selects a policy for that trade-off, with explicit
uncertainty assumptions rather than knowledge of the realized future.

## 2. Information and causality

Before execution, declare a finite set S of possible length-K sequences of
current feasible actions, references and resource caps. These are possible
future observations, not probabilities and not the selected future. They are
hand-constructed here. The sequence must be exogenous to the policy's private
random draw. The cumulative allowance is decision-dependent state, but the
future underlying opportunity sequence is not decision-dependent in this model.

A deterministic causal policy maps the full observation prefix to one current
action. Two scenarios with identical prefixes must receive identical actions
under that policy. Each policy must satisfy all protections in every scenario.
The implementation enumerates integral feasible paths and retains only path
combinations meeting this nonanticipation condition. This is not a separate
clairvoyant optimization in each future followed by an average.

The observation consists of the current reference, cap, action names, utilities
and resources. The executor receives no scenario label, future schedule or
future head movements. Exact current utilities are an analytical assumption;
they would require an additional prediction/error treatment in deployment.
Reported past rolling histories are 23 balanced reference observations. D is
an older, separately supplied event loss; the histories are not empirical data.

Every comparator has the same current actions, utilities, contract and ledger.
The possible-future set is declared problem information. Rolling policies do
not exploit it in their definitions; it is not withheld from them. To separate
the benefit of randomization from simply using the future model, comparisons
also include a best deterministic minimax-regret policy and a best deterministic
absolute-minimax policy using the identical scenario set. Only the explicitly
offline benchmark knows which future will actually occur.

## 3. Minimax expected regret

For a causal policy pi and scenario s define the primary terminal loss

    L(pi,s) = max_{i:D_i>0} d_i,K / D_i,

with value zero if no loss is positive. It lies in [0,1]. Let L*(s) be the
minimum primary loss among all protected integral paths knowing future s.
Define R(pi,s)=L(pi,s)-L*(s). The offline routine has secondary tie-breaks, but
only its primary value enters R. The previous lexicographic sum of unpaid
fractions is reported, **not optimized as a second objective in this game**.

For the complete finite causal policy set P, solve

    minimize v over p_pi >= 0, sum_pi p_pi = 1
    subject to sum_pi p_pi R(pi,s) <= v  for every s in S.

Choose one pi with probabilities p at the start of the episode, independently
of the future, and follow it. This is a distribution over deterministic causal
policies, not a fractional action that violates an instantaneous protection.
It is also not a policy that re-solves a new regret game every period. Such
re-optimization could change the commitment and requires a separate analysis.

The objective is max_s E_pi[max_i d_i,K/D_i - L*(s)]. The maximum over users is
taken before the expectation over policies. It is not max_i E_pi[d_i,K/D_i],
and no average over a presumed future-scenario distribution is optimized.

### Exact certificate

The dual maximizes z over y_s>=0, sum_s y_s=1, with

    sum_s y_s R(pi,s) >= z  for every pi in P.

For any feasible p and y, weak duality gives z<=v. If all scenario-weighted
primal payoffs are at most v and all policy-weighted dual payoffs are at least
the same v, optimality follows with zero gap. The saved certificate lists both
sets of rational payoffs. The dual y is an adversarial mathematical witness,
**not an estimated distribution of future content**.

The implementation removes duplicate and componentwise dominated rows for
search, then verifies the certificate against every original policy. A finite
game admits a basic optimal mixture supported on at most |S| policies; support
enumeration plus rational linear-system solving supplies the reference solver.
The independent floating-point LP is an additional test, not the proof.

### Scope of the guarantee

For every fixed s in S, independently of the sampled policy,

    E_pi[L(pi,s)-L*(s)] <= v.

This is an expectation over internal randomization, not an almost-sure
guarantee in one episode. It also holds under any exogenous distribution over
S by averaging. It need not hold if the environment observes the draw or its
actions and chooses a different future in response. The supplied scenarios
must contain the actual observations exactly in this finite reference model.

Pathwise protection is stronger and separate: every enumerated policy consists
of feasible protected paths, so selecting any of them retains each recipient
floor and each per-step/cumulative donor limit. Ledger conservation follows
from the unchanged feedback update. This does not establish stall or latency
protection; playback clocks, buffers and prediction error are not modeled.

## 4. Closed-form spend-or-save result

One recipient has D>=b>a>0 unpaid units. One donor's allowance can fund exactly
one compensation opportunity. Spending now delivers a; waiting permits either
no compensation or compensation b. The first observed period is identical in
both futures. Waiting and then refusing b is dominated, so the two relevant
causal policies are spend-now and wait-for-later.

| Policy | Regret if opportunity vanishes | Regret if gain b arrives |
|---|---:|---:|
| Spend now | 0 | (b-a)/D |
| Wait, then spend if possible | a/D | 0 |

With spend probability p, the two expected regrets are (1-p)a/D and p(b-a)/D.
The former decreases and the latter increases with p. Equating them minimizes
their maximum, yielding

    p* = a/b,
    v* = a(b-a)/(bD).

The best deterministic regret is min(a,b-a)/D, strictly larger for 0<a<b.
This is an elementary finite-game calculation, not a new general minimax theorem.
Thirty rational parameter cases check it exactly, including different D.

For D=2,a=1,b=2, reference (3,3), and total donor allowance 1, the current boost
is (4,2); the possible later boost is (5,2). The rule spends now with probability
1/2 and has worst expected regret 1/4. On the declared balanced H=24 histories:

- Rolling Nash waits now and takes (5,2) if it appears: worst regret 1/2.
- Rolling max-min refuses both boosts because the donor's rolling minimum
  would decline: worst regret 1.
- Greedy recovery and capped debt-weighted priority spend now: worst regret 1/2.
- The model-aware best deterministic minimax-regret rule has value 1/2 too.

These comparisons are exact for this construction, not uniform performance
rankings. Rolling rules pursue different fairness objectives. Reducing regret
about compensation may worsen post-event worst-user quality; that metric and
donor losses are therefore reported rather than suppressed.

## 5. Preserved counterexamples and boundary cases

**Absolute recovery risk.** In the same example, the mixed rule's worst expected
unpaid fraction is 3/4. Spending now always leaves fraction 1/2, so greedy and
the deterministic absolute-minimax policy have worst absolute loss 1/2. Choosing
minimax regret is therefore a normative risk preference, not a free improvement
in every recovery criterion. A service requiring a strict terminal-loss cap
would need that additional constraint and a new feasibility analysis.

**Wrong future set.** Planning only for the better-later scenario yields zero
regret within that singleton and causes waiting. If the opportunity disappears,
the entire D=2 remains unpaid and actual regret is 1/2. At the first unexpected
prefix the implementation flags `model_breach` permanently and switches to
current protected stateless Nash. It continues to respect the remaining
allowance but cannot retroactively recover the missed opportunity. Baseline
feasibility is required; an empty safe action set raises an error, not a claim
of continued safety. A changed deadline/horizon is likewise outside the model.

**Adaptive future.** If an adversary sees which of the two policies was drawn,
it can supply b after a spend and no opportunity after a wait. Expected regret
is then 1/2, not the oblivious-scenario bound 1/4. The report includes this
calculation, not just favorable model-consistent outcomes.

**Zero regret is not repayment.** With no donor allowance or no surplus
headroom, both the offline benchmark and every causal policy leave all debt
unpaid. Regret is zero while unpaid fraction is one.

**Delayed revelation and multiple recipients.** Additional examples retain
shared prefixes through two decisions, or make the final opportunity favor
one of two recipients. Policies must commit before the distinguishing
observation arrives. Their exact results are in the report; no assertion of
general multi-user superiority is inferred from these small constructions.

## 6. Practical limits and next research gate

The exact solver permits at most four scenarios, 2,000 policy rows and 24
nondominated rows. The causal path-combination cap is 200,000; individual path
enumeration remains exponential. These are reference-scale checks, not
complexity guarantees or production input hardening. Exact ties use stable
enumeration/name conventions; optimum values are invariant to scenario/action
ordering, but a particular equally optimal policy need not be anonymous.

No scenarios are fitted, no new data are consumed, and no p-values or new
holdout evidence are produced. The prior failed experiments remain failed.
Before any new empirical campaign:

1. Choose whether the actual service objective is regret, absolute unpaid loss,
   or an explicit constrained combination; the analytical trade-off is real.
2. On already exposed data only, establish useful compensating actions under
   a defensible utility reference and declared donor harm budget.
3. Build a causal, compact opportunity model and assess misses without using
   future HMD outcomes. A numerical finite set will need a justified tolerance
   or uncertainty-envelope treatment; this exact lookup is not that solution.
4. Add buffer/clock protections and scalable decisions, and compare with
   rolling Nash/max-min, debt-weighted recovery and model-aware deterministic
   controls under matched information. Measure absolute loss as well as regret.
5. Only after a frozen development criterion succeeds, reserve genuinely
   untouched data and freeze the new protocol before confirmation.

This package justifies investigating timing; it does not yet justify a new
positive manuscript claim or consumption of another fresh content reserve.

## 7. Prior-art boundary

Minimax regret, randomized online policies and LP-duality certificates are
established methods. The contribution here is an explicit, executable
**application and diagnostic** for the declared compensation contract, not an
invention of those principles or a completed novelty review.

- K. Regan and C. Boutilier, *Robust Policy Computation in Reward-Uncertain
  MDPs Using Nondominated Policies*, AAAI 24(1), 1127-1133, 2010.
  [Publisher and DOI](https://ojs.aaai.org/index.php/AAAI/article/view/7740).
  Their reward-uncertain MDP setting uses minimax regret and nondominated
  policies; the present finite opportunity-sequence game does not reproduce
  their algorithm or establish novelty over that broader literature.
- MIT 6.854, *Online algorithms*, 2020 course notes.
  [Original notes](https://courses.csail.mit.edu/6.854/20/Notes/n25-online.html).
  Randomization and distinctions between adversarial information models are
  standard in online analysis; our bound explicitly requires an oblivious,
  exogenous future rather than one responding to the policy draw.
- Stanford CS369, *Lecture Notes*, Section 4, *Yao's Minimax Theorem from LP
  Duality*. [Original notes](https://web.stanford.edu/class/cs369/files/cs369-notes.pdf).
  The primal/dual finite-game proof is standard; our exact witnesses certify
  these particular constructed games.
- T. S. Eugene Ng, I. Stoica and H. Zhang, *Packet Fair Queueing Algorithms for
  Wireless Networks with Location-Dependent Errors*, IEEE INFOCOM, 1998.
  [Author-hosted paper](https://www.cs.cmu.edu/~hzhang/papers/INFOCOM98a.pdf).
  Compensation with controlled degradation of other flows predates this work.
  See the preceding objective note for additional fairness/queueing context.
