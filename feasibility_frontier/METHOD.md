# Exact finite-catalogue feasibility method

## Question, units and data

For each unchanged exposed episode, can at least half its original loss D be
repaid in the remaining four segments, and what resource/donor allowances are
necessary? D is the sum of positive recipient shortfalls relative to rung2
over the first two segments, when that recipient used rung0. Both users' service
references remain their segment-specific rung2 qualities. The recipient floor
is enforced at every subsequent segment; reference relaxation is not recovery.

Reuse six published v2/v3 quality and byte tables through the previous episode
definitions. Sorted adjacent participant IDs form 14 pairs in both directions
for each of six scenes: 168 episodes. These reuse the same 28 participants,
share source content, and are not 168 independent subjects or new holdouts.
The clipped objective index is 1+4*clip((VW-PSNR-18)/24,0,1), rounded half-up
to .001; integer milli-units preserve all constraint comparisons. It is not MOS.
Segments have equal 10-second duration, so sums are in utility-segments; a
quality-time convention would multiply every loss, gain and budget by ten.

## Finite optimization

For each segment t and each of its 36 joint rungs a, retain the action only if
recipient quality is at least its rung2 reference. Define:

    g_t(a) = q_recipient,t(a) - b_recipient,t
    h_t(a) = max(b_donor,t - q_donor,t(a), 0)
    r_t(a) = max(1, bytes_t(a) / (2*rung2_bytes_t))
    z_t(a) = 1[g_t(a)>0]
    T = ceil(D/2)

For fixed maximum actions M, per-segment donor cap epsilon and resource cap
lambda, minimize sum h_t subject to:

    sum g_t >= T;  sum z_t <= M;
    h_t <= epsilon and r_t <= lambda for every t.

The answer meets a cumulative donor budget B exactly when this minimum is <=B.
The reference pair is always available. A zero-gain alternative may consume
fewer bytes, but cannot refund earlier donor harm or increase recovery credit.
Peak resource is a per-segment upper bound, not total bandwidth or playback
time. The total encoded-byte ratio of each witness is reported but not minimized.

## Dominance and exact enumeration

For this particular target T, replace each gain by min(g,T) only when testing
dominance and feasibility. This preserves whether a path reaches T: if any
gain exceeds T the path already qualifies; otherwise nothing is changed.
If an action has at least as much capped gain and no more harm, peak-resource
factor or positive-gain action count, it can replace a dominated action in any
path without violating a constraint or increasing the objective. Equal tuples
use stable lexicographic rung IDs. Thus per-segment pruning preserves this
feasibility frontier, but need not preserve objectives for a different target
or minimum total bytes. Original, uncapped gains are used in debt witnesses.

Enumerate the Cartesian product of the remaining four menus. All schedules
are integral; no expected-quality relaxation is used. Rank the distinct exact
rational resource factors. For each path reaching T, record its action count,
smallest declared epsilon slice allowing its peak harm, peak resource rank,
total harm and stable path index. A three-dimensional prefix minimum over
count, epsilon and resource yields the minimum total harm for each allowance.
Lexicographic (harm,path index) codes resolve ties deterministically.

Publish a point only when increasing the resource factor strictly lowers the
minimum total harm. Its complete four-action witness attains that resource
breakpoint and satisfies the original tables. Empty slices remain explicit.
This constructs an exact staircase for each M in {1,2,4} and each epsilon
in {0,.125,.25,.5,1,2,4}. It is not a continuous frontier over every epsilon,
an efficient large-system algorithm, or a new optimization theorem.

## Independent checks

A separate multiple-choice dynamic program visits all original, unpruned
actions. State (count,cumulative harm) retains maximal capped gain. For equal
count, a state with no higher gain at greater harm is safely discarded.
This DP uses no resource ranks, enumeration arrays or frontier pruning.
Compare its feasibility decisions at all seven displayed resource caps and
six highlighted contracts for every episode: 7,056 comparisons. Synthetic
cases also compare pruned enumeration, unpruned enumeration, direct Cartesian
search and DP at exact allowance boundaries.

Each published witness is independently reconstructed from the original
qualities and bytes. Delivered credit is min(remaining debt,actual gain), so
credited recovery plus remaining debt always equals original D. Monotonicity
is checked across every declared M/epsilon/B query and within staircases.
The fully relaxed catalogue count must agree with the prior 157/168 diagnosis.
Hashes bind code, plan, method, original inputs and results; a full replay is
required on both Windows and Linux and in fresh-checkout continuous integration.

## What the audit cannot establish

The oracle sees every future viewport quality. Feasibility is only an
opportunity bound for a causal policy with the same action and service
constraints but less future information; it does not validate prediction, timing, network delivery
or human experience. The repeated participant/content structure precludes
independent-trial interpretations. Neither lower donor loss nor extra bytes
is assigned an externally justified acceptable value. Positive opportunities
in multiple periods do not prove timing competition: an unconstrained policy
could simply use them all. A new controller must later earn its advantage
against information- and allowance-matched simple controls.
