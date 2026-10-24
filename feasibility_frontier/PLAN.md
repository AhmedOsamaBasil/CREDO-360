# Exposed-data feasibility-frontier audit

## Fixed scientific scope

This plan precedes the full audit. Use the SAME 168 two-user episodes from the
exposed v2/v3 catalogues, with the same recipient/donor IDs, original event loss
D, rung-2 service references, .001 objective-utility quantization and four
10-second recovery segments. No new data, encoding, holdout or manuscript edit.
Do not lower the reference or shorten the impairment to manufacture recovery.

Keep the previous target: **repay at least half of D**. In integer milli-units,
the required gain is ceil(D/2). This operational meaning of "meaningful" is an
exploratory service specification, not a validated human QoE threshold.

This is a future-known, exact feasibility audit. It neither trains a predictor
nor evaluates a causal controller. Existence of a feasible offline schedule is
a necessary opportunity condition, not evidence an online policy can find it.

## Action space and costs

At each recovery segment, examine ALL 6x6 recipient/donor representation pairs.
Require recipient quality at least its original rung-2 quality. The baseline
pair remains available. Unlike the previous restricted menu, retain alternatives
with different gains, donor losses and resource costs rather than only one boost.

For action a at segment t:

    gain_t = q_recipient(a) - b_recipient,t >= 0
    harm_t = max(b_donor,t - q_donor(a), 0)
    bytes_t = encoded bytes of the two representations
    reference_bytes_t = 2 * rung2_segment_bytes_t

No donor surplus refunds positive harm. Count a recovery action whenever its
recipient gain is positive, even if donor harm is zero. Audit at most M=1,2,4
such actions. An unchanged-reference, non-gain action does not consume M.

Resource allowance is lambda>=1 with bytes_t <= lambda*reference_bytes_t at
EVERY segment. This is encoded byte headroom, not measured bandwidth, wall-clock
stall protection, total-cost equality or a financial budget. Also report total
byte ratio, but do not optimize it or confuse it with the peak constraint.

Donor caps are per-segment epsilon and cumulative positive loss B, both in the
declared objective index. Per-segment epsilon slices are
{0,.125,.25,.5,1,2,4}. Cumulative B queries are {0,.25,.5,1,2,4,8,16}.
These are audit axes, not approved acceptable service degradations.

## Exact frontier construction

Enumerate all four-period combinations after provably safe single-period
dominance pruning. For this half-repayment query only, cap each gain at the
required target. A dominating action offers at least that capped gain with no
more donor loss, no higher max(1,bytes/reference_bytes), and no higher recovery-
action count. Ties use stable rung IDs. Keep original actions for witnesses.

Normalize all possible resource ratios as exact Fractions and rank them.
For each feasible path, compute peak ratio rank, max donor harm, sum donor harm
and positive-gain action count. A prefix-minimum table over count, epsilon slice
and resource rank yields the exact minimum cumulative donor harm. Publish every
strictly improving staircase point, its four-action witness, actual resource
and donor costs, and remaining debt. Empty frontiers remain explicit.

These are exact resource/cumulative-harm frontiers CONDITIONAL on each specified
epsilon and M, not an interpolated or unrestricted continuous multiobjective
surface. Resource breakpoints come from actual action ratios, not a coarse
lambda grid. Every threshold decision uses integer/rational comparisons.

## Reporting fixed before results

Report all episodes plus pooled, cohort and scene summaries. For each epsilon,
B and M, give feasible episode counts and minimum required lambda distributions
among feasible episodes, ALWAYS with the denominator and infeasible count.
Use nearest-rank median and 90th percentile summaries (no inference or
independence claims). Also give the smallest resource allowance covering
50%,75%,90%,100% of ALL episodes, including infeasible episodes in the
denominator; return infeasible when the requested coverage cannot be reached.

Also report feasibility counts at lambda in {1,1.1,1.25,1.5,2,3,4}. Highlight
the legacy contract (lambda1,epsilon.5,B.5,M1), the no-donor-harm slice, and
M4 slices (epsilon.25,B.5), (epsilon.5,B1), (epsilon.5,B2), (epsilon1,B4).
Do not call whichever setting fares best a validated service recommendation.

For those highlighted settings, count periods with any positive gain and any
gain >= one quarter of the repayment target, before enforcing cumulative B.
Two individually possible periods do not prove a jointly feasible schedule or
that a timing algorithm is necessary; publish these as discrimination diagnostics.

Cross-check the unrestricted M4 count against the earlier upper-bound diagnosis
(157/168 half-repayment-possible under no byte/donor/transfer restrictions).
If broader actions change the legacy-contract count, explain the menu difference;
do not silently overwrite the earlier result. No successful-controller screen
is defined here: the output is an audited trade-off boundary with limitations.

## Verification

Check every witness directly against original quality/byte tables. Compare
pruned and unpruned exhaustive enumeration on complete small cases, and use
an independent cumulative-harm dynamic program on all168 episodes at the
highlighted settings. Check monotonicity in lambda,epsilon,B,M, exact recovery
ledger conservation and reproducibility on Windows/Linux. Keep all failed
checks visible. Preserve original source and result hashes. Publish a fixed
implementation/protocol before the full exposed-data audit.
