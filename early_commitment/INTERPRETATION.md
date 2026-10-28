# Early-commitment findings

## Conclusion

**Earlier causal viewport information is useful, but this controller still
does not beat the strongest simple recovery control. Waiting for completed
reports is expensive in stalls. Do not consume a new holdout for this method.**

We ran the fixed1,512 exposed-data episode-policy combinations. The primary
policy holds the last observed viewport over known future sender distortion
maps and plans over the remaining byte reserve. Partial samples are released
only after modeled presentation plus80ms. The500ms sensitivity was fixed in
advance and is not an alternative winner selected after seeing outcomes.

## Primary outcomes

| Policy | Half-repayment /168 | Mean unpaid fraction | Mean worst-user quality | Mean stall (s) |
|---|---:|---:|---:|---:|
| Matched prefix cost-greedy |90|0.369185|3.997177|6.978108|
| Completed-feedback planner |92|0.380411|3.998055|6.969765|
| Primary prefix planner |92|0.375974|3.998658|6.968974|
| Wait-for-completion planner |92|0.375430|3.998658|16.220007|

Compared with its completed-only ablation, the primary reduces mean unpaid
fraction by0.004437, with no half-repayment-count change. The improvements are
0.006451 in v2 and0.002423 in v3. Earlier samples change26 second decisions,
14 third decisions and15 fourth decisions out of168 each; first decisions
are identical because both start with the same pre-event observations.

However, **primary unpaid loss is worse than matched cost-greedy by0.006789**
pooled, by0.005597 in v2 and by0.007982 in v3. Reaching half-repayment in two
additional episodes does not compensate for worse mean residual loss under
the declared objective. The two additional threshold successes are in Train01;
per-scene outcomes and adverse effects are retained in the full report.

Relative to matched rolling Nash, primary repayment improves but worst-user
quality declines by0.058037 pooled (v2:0.067693; v3:0.048381), exceeding the
declared0.02 guard. Compared with max-min, v2 worst-user quality declines0.037051;
v3 unpaid loss is worse by0.007999. These are distinct service objectives, not
evidence that every lower-unpaid policy is a fairer-quality policy.

The primary incurs zero donor-floor losses and one recipient-floor loss of
**0.001 quality-index units**, Cheerleading01 recipient26/donor25, segment2.
This tiny difference does not demonstrate substantial harm, but it invalidates
a zero-actual-loss guarantee. The meaningful-gain and quality checks fail
independently of that small violation. All failures remain published.

## What timing and information changed

At the second decision,284/336 user-decision cases have at least one newly
displayed sample; the count ranges0--7, median6. This is useful information
before a full ten-second report. Selected-quality forecast MAE falls from
0.114562 to0.106376 compared with completed-only planning. These are errors
against the existing coarse objective metric, not human-perception errors.

The conditional future-known opportunity decomposition is informative:

| Policy | Lost fraction at decision1 | Decision2 | Decision3 | Decision4 |
|---|---:|---:|---:|---:|
| Completed-only planner |0.006975|0.021870|0.006535|0.000037|
| Prefix planner |0.006975|0.016301|0.007664|0.000040|
| Prefix cost-greedy |0.003017|0.021135|0.000000|0.000040|

Prefix planning reduces second-decision loss relative to both controls, but
its extra first/third-decision losses outweigh that advantage over cost-greedy.
The identity sums to each policy's gap from the structural future-known bound.
It is an offline diagnostic, not a claim that those missing opportunities are
predictable or safely attainable online. Better forecast MAE alone does not
imply better resource-allocation decisions.

Waiting for complete reports adds9.250242 seconds of mean stall relative to
completed-only planning, for just0.004981 less unpaid loss. The conservative
slack-only rule never waits in this catalogue and exactly reproduces the
completed-only policy. This is not proof that every possible pacing or
asynchronous-player design lacks useful slack.

The basic timing constraint is straightforward: if the queued media ends at F,
a report arrives at F+delta and the next download requires tau>0, a decision
conditioned on that report cannot deliver the next segment before F+delta+tau.
Without additional buffered media, this forces at least delta+tau starvation.
Tests exercise the bound and the contrasting case with another segment queued.

The500ms sensitivity retains92/168 half-repayments and unpaid0.375603. A small
non-monotone change is possible because different observed masks change
discrete actions; do not claim that higher latency improves recovery in general.
The frozen primary remains80ms and its failed screen is unchanged.

## Evidence boundary and next research decision

Windows and Linux independently regenerate every outcome and pass all6,048
clock/resource decisions and672 independent Cartesian optimizer comparisons.
All1,008 completed scalar projections match the prior feedback exactly.
The prefix table is derived from previously recorded poses; this incremental
feedback path has not been measured on a network or HMD. The fixed fluid
service, nominal10s media durations, fixed feedback latency, tile-center metric,
small six-scene pool and reused participants remain limitations. Repayment is
assessed after four media segments, not at a guaranteed wall-clock deadline.
Future sender maps assume pre-encoded video-on-demand content; the method is
not validated for live capture where those future representation properties
are unavailable.

There is no new fitted model, calibration guarantee or general optimization
novelty here. Hold-last-view forecasting, finite-reserve dynamic programming
and buffer-aware waiting are known building blocks. Their tested integration
and the timing/opportunity diagnosis are technical artifacts, not established
evidence of a superior novel recovery controller.

Further parameter sweeps or another holdout for this policy are not justified.
The next decision should be whether to reposition the contribution as a
feasibility/measurement study, or develop a demonstrably better decision rule
under an explicit operational recovery-versus-quality objective. Any such
redesign should first outperform the simple cost-greedy baseline on exposed
data while meeting the stated quality and stall limits. Do not silently change
the objective or relax the failed screen to declare this version successful.
