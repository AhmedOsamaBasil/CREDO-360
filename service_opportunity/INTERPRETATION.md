# Interpretation: service contract and exposed causal scheduling

## Outcome

The frozen exploratory development screen passes, unlike the preceding recovery
pilots. This is a **small, conditional exposed-data improvement**, not independent
confirmation, a safe repayment promise or a demonstrated new scheduling principle.
No further holdout or manuscript update was performed.

The method/protocol were published as `a9751b3` before the measurements and model
comparison. A measurement-isolation correction was published as `e0f0eb4` before
the valid service run; rates, payload, deadlines and model were unchanged. The
invalid first attempt is retained in [measurement notes](MEASUREMENT_NOTES.md).
Additional causality/receipt tests, timing instrumentation and an independent
Cartesian checker do not change the controller. Post-hoc comparisons below are
separately labeled and do not replace the frozen screen.

## What the service test supports

Twelve of twelve nominal probes transferred two concurrent750kB TCP payloads
within the9.5s receiver-confirmed deadline. Completion ranged8.3787–8.5062s;
client-process startup also fits the10s slot. Both20/80ms configured RTT and
idle/saturated competing TCP conditions were exercised. All three negative
controls, with foreground service reduced from1.5 to1Mbit/s, missed the deadline
(approximately12.67–12.68s; exact values are in the raw artifact).

The reserved foreground class is1.5Mbit/s under a2Mbit/s parent, with a separate
0.5Mbit/s competing class and borrowing disabled. Payload entitlement is1.5MB
per10s, i.e.1.2Mbit/s, not1.5Mbit/s application goodput. Receiver receipts and
qdisc counters include protocol costs; nonzero competing receipts and backlog
support the busy condition. Experiment namespaces were removed after execution.

This validates a **controlled managed-service configuration**, not realistic
spare capacity on arbitrary user paths. Equal-size synthetic transfers were
tested, not every asymmetric action split, HTTP/TLS, packet loss, wireless paths,
long sessions or an integrated video player. The model's live transport and
playback timing are not validated by these probes. Traffic usage alone cannot
establish spare capacity; see [RFC5136](https://www.rfc-editor.org/rfc/rfc5136.html).

The forecast/optimizer timing audit covers672 loaded-data decisions per OS;
maximum observed time was approximately1.31ms on both Windows and Linux, below
the0.5s planning allowance. It is separate from the network probes, excludes
data loading and player integration, and is not an end-to-end guarantee.

## Primary exposed comparison

All168 episodes, six scenes, original impairment losses and fixed references
remain unchanged. The primary reserve equals the total baseline bytes over the
four recovery slots; the absolute per-slot payload cap is1.5MB. Zero donor loss
and recipient reference floors apply to every delivered action.
The quality numbers are the existing bounded objective index, not MOS. The
underlying encodes are1920x960, not8K delivery. Decoder/rendering costs were not
measured. This absolute byte cap differs from the preceding multiplier-based
audit; its counts must not be attributed solely to a controller change.

| Controller | Mean unpaid loss fraction | Half-repaid /168 | Mean episode worst quality |
|---|---:|---:|---:|
| Prefix KNN + receding-horizon optimization |0.362157|92|3.9988|
| Greedy recovery |0.369137|90|4.0056|
| Rolling max-min |0.375825|90|4.0207|
| Rolling Nash |0.464875|79|4.0628|
| Persistence + same optimizer |0.384517|90|3.9983|
| Future-known offline oracle |0.344994|96|3.9995|

The reduction against greedy is only0.006980 of original loss on average,
about1.89% relative to greedy's unpaid fraction, and two additional half-repaid
episodes. Mean unpaid loss is lower against all four fixed online controls in
each cohort: v2 candidate0.183557 versus greedy0.185803; v3 candidate0.540756
versus greedy0.552471. No independent sampling or significance claim follows
from these dependent exposed pairs.

The quality cost is real: pooled mean quality is4.1535 versus4.1650 for greedy
and4.1763 for Nash; episode worst quality also declines against those controls.
Event compensation and post-event quality fairness are different objectives.
All reference floors hold, but this is not a Pareto improvement or human QoE gain.

Content effects are heterogeneous. On River01, greedy repays everything while
the candidate leaves mean unpaid0.016132. On Cheerleading01 the candidate,
greedy, max-min and persistence tie. At reserve fraction2, greedy's pooled
unpaid0.225936 is better than the candidate's0.228625. The result is not a
universal advantage across budgets or content.

## Forecast reliability and post-hoc mechanism checks

The prefix model excludes the evaluated scene and both participant IDs from its
130 training trajectories. Future encoded sizes are known sender metadata;
future viewport labels are never passed to the predictor. Exact CURRENT full
quality menus remain an important idealization shared by all controls.

At the primary reserve,88 candidate episodes were initially predicted capable
of half-repayment, but24 failed (27.3% of predicted successes). In v3,8 of10
predicted successes failed. These flags cannot be advertised as safe admission.
Absolute future-quality MAE is0.3383 for KNN versus0.1469 for persistence: better
control outcomes do not establish better overall quality prediction accuracy.
This error measure repeats labels across forecast horizons and is descriptive.

Two additional controls were run AFTER inspecting the fixed primary results:

- **Cost-matched greedy:** same minimum-cost tie-break as the candidate, with
  no future lookahead. Mean unpaid0.369137,90 half-repaid: the repayment gain is
  not explained solely by the old greedy rule's quality-oriented tie-break.
  Its quality outcomes differ, so retain the original and matched controls.
- **Unconditional training mean + lookahead:** all130 eligible training
  trajectories averaged without prefix-dependent neighbor selection. Mean
  unpaid0.378278,91 half-repaid. The prefix model is better pooled and in v3,
  but **worse in v2**:0.183557 versus0.180887. Thus a uniform benefit from
  conditional learning across both cohorts is not established.

These strengthen the diagnosis without changing the candidate or declaring a
new successful screen after the fact. KNN, knapsack DP and receding-horizon
control remain established techniques; this experiment does not establish
absolute novelty or a publishable theoretical advance.

## Verification and next decision

Windows and Linux regenerate all3,024 primary episode-policy outcomes exactly,
with scientific SHA256
`8b482cd668e9b5a964a8e571f2f2b635b1e2789988e9e08793158246942923b9`.
An independent unpruned Cartesian calculation checks404,288 complete action
paths and504 offline queries. All byte/debt conservation and floor constraints
hold. The post-hoc results also replay identically across OS. Twenty-one new
tests include72 small brute-force comparisons and future-menu mutation tests.
The earlier reserve artifact still verifies unchanged.

Before another holdout, the useful next step is an exposed-data **integration
gate**: replace oracle-current quality with a causal current-quality estimate,
test actual selected asymmetric transfers with controller and playback clocks,
and explicitly choose best-effort compensation versus guaranteed admission.
If admission is retained, its forecast failures need a separately developed
risk-control design; do not reinterpret the current point forecast as calibrated.
Retain greedy, cost-matched greedy, rolling rules, persistence and unconditional
mean controls. Freeze a minimum practically meaningful gain and quality-cost
limit before any fresh evaluation. The present small gain is encouraging enough
for that engineering step, not enough to spend another holdout immediately.
