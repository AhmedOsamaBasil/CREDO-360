# Causal estimates and actual selected transfers: findings

## Decision

**The implementation and transport checks pass; the recovery-performance
progression screen fails. Do not consume another holdout for this candidate.**
No method parameters, service rates, target, selection or progression thresholds
were changed after outcomes. The protocol and method were published as
`d304470` before media preparation and the complete runs. No manuscript changes
or new participant/content collection accompanied this test.

The implementation supplies a more credible experimental interface than the
previous perfect-current-quality assumption. That engineering correction is
not evidence of a stronger recovery mechanism or new scheduling theory.

## Complete exposed replay

All 168 directed episodes across six already exposed scenes were evaluated
under all seven causal policies: **1,176 episode-policy runs, 4,704 joint
decisions**. Every run uses the same causal current estimator, delayed
feedback, actual-file costs, structural rung floor, finite reserve and original
event repayment target. Timing in this batch is explicitly simulated fluid
service, not measured networking.

| Policy | Half-repaid / 168 | Mean unpaid fraction | Mean episode worst quality |
|---|---:|---:|---:|
| Causal KNN recovery | 90 | 0.371245 | 3.9971 |
| Greedy recovery | 90 | 0.370941 | 4.0052 |
| Cost-matched greedy | 90 | 0.369140 | 3.9972 |
| Rolling Nash | 89 | 0.393596 | 4.0231 |
| Rolling max-min | 90 | 0.376229 | 4.0211 |
| Persistence lookahead | 90 | 0.371854 | 3.9969 |
| Unconditional lookahead | 90 | 0.373381 | 3.9966 |

Lower unpaid fraction is better. Candidate unpaid fraction is **0.000305 worse
than greedy** and **0.002106 worse than cost-matched greedy**, despite differing
on 224/672 and 152/672 decisions respectively. It is not merely a copied action
sequence, but the changed actions do not produce a useful recovery gain.

The cohort-specific practical gain requirement also fails. In v2 the candidate
has unpaid fraction0.186313 versus greedy0.189406, below the required0.005
improvement, and exactly ties persistence. In v3 it is worse than greedy and
max-min:0.556178 versus0.552476. Its v2 mean worst quality3.5264 is below
Nash/max-min3.5733 by about0.0469, exceeding the0.02 quality-loss guard.
These failures independently preclude progression, without relying on tiny
quality-floor differences. See the [full report](results/replay_v1/REPORT.md)
and [cohort figure](results/diagnostics_v1/exposed_recovery.png).

The candidate has one donor-floor violation: River01 recipient27/donor28,
segment4, rungs(4,3), donor quality2.706 against reference2.707. One recipient
floor violation occurs for Cheerleading01 recipient26/donor25, segment2,
rungs(3,2), quality4.295 versus4.296. Both are **0.001 on the rounded objective
index**, not substantial demonstrated perceptual harm. They nevertheless show
that predicted floors and nondecreasing representation rung are not a strict
actual-quality guarantee. All other policies' violations are also retained.

The current selected-quality mean absolute error is0.1142 index units for the
candidate. This is a selected-action descriptive error, not calibration,
uniform accuracy, a confidence bound or an estimate of human QoE.

## Measured selected-transfer pilot

The fixed recipient1/donor2 pair was used in each scene, once per nominal
policy. Four policies x six scenes produced **24 nominal episodes**, followed
by **six candidate-only stress episodes**. This small, deliberately fixed
engineering sample is not a substitute for the full exposed-data result.

- **240/240 actual MP4 receipts** match their expected file bytes and SHA256.
  Those files bind to216 identity-verified segments from36 original renditions;
  no reencoding or third-party media redistribution occurred.
- **96/96 nominal rounds** complete within9.5s from the decision boundary,
  including controller execution, process/file overhead and receiver hashing.
  Pair receipt latencies span2.9830--8.6752s. This is engineered1.5Mbit/s
  foreground service under a2Mbit/s parent, not measured field headroom.
- Under intentionally undersized750kbit/s foreground service, **12/24 stress
  rounds miss** the deadline; maximum latency17.0660s. Smaller selected files
  need not miss. The controller continues to assume the nominal budget.
- All120 service snapshots confirm the declared non-borrowing rates and a
  backlogged competing class. All temporary namespaces were cleaned up.
- Nominal live actions match the corresponding fluid-model actions in96/96
  rounds. The clock still uses the measured receipts, not simulated times.

The nominal candidate's mean stall is 6.0312s/user: 4.5159s startup waiting plus
1.5153s later starvation. Greedy has 6.0095s total: 5.3849s startup plus 0.6245s
later starvation. A timely aggregate round is therefore **not** a no-stall
guarantee for each synchronized user. Stress raises candidate stall to20.8749s
(8.6899s startup plus12.1850s later starvation).

All four nominal policies repay half in3/6 episodes. Candidate unpaid
fraction0.369675 is lower than the three controls'0.382027 on this small fixed
subset. That favorable subset does **not** overturn the failed complete
168-episode comparison. See [all live summaries](results/diagnostics_v1/REPORT.md)
and the [timing/stall figure](results/diagnostics_v1/live_playback.png).

## Timing, information and deployment boundaries

Recovery begins after the original event segments were played, with zero
buffer. Feedback is released only after a segment's modeled playback ends,
not when its download completes. Predicted pending credit never counts as
actual repayment. The final media tail is drained analytically. No HMD,
decoder, audio/video synchronization, HTTP/TLS stack or client renderer was
tested.

Quality feedback and reference-rung counterfactual credit remain
reference-assisted retrospective measurements; their production telemetry
cost is not implemented. Causality here means that the controller cannot
inspect current/future target viewport labels. It does not mean that all
feedback can already be measured cheaply in a deployed client.

Actual MP4 container bytes replace old video-payload-only costs; the minimum
rung2 action restriction also differs from the previous oracle-current study.
Consequently, the change in results cannot be attributed solely to estimating
current quality. The objective index is clipped PSNR-derived quality, not MOS.

A separate post-run media audit checks actual packet hashes, sizes and stream
durations. Only River01's final segment is299/30 rather than10 seconds. A
duration-aware calculation shifts final completion earlier by1/30s there,
without changing any decision, stall or repayment. The first post-run support
checker also assumed a zero timestamp for pre-recovery segment0; the observed
timestamp is0.1s, while all recovery segments start at zero. Its assertion
failure is retained and superseded by `audit_integration.py`; the frozen
method, media and results were not rewritten to make a check pass.

## Verification and research consequence

Both operating systems reproduce the complete deterministic outcome hash
`58a33bd73e06b8e487def19d8a347785c028c45fab0e48b8966941bb07af3de9`
and the measured-clock outcome hash
`c01e4c65ded2f9f3583f351f674cec16e819b0c371c8256278e74123fbacc9c0`.
The independent recursion checks all1,206 episode clocks,4,824 training-pool
exclusions and every selected-byte/reserve/feedback ledger. Synthetic tests
mutate current/future labels at every decision and reject premature feedback,
invented repayment, missing startup stalls and incorrect selected byte counts.

Final regression: **247 tests plus 24 subtests on Windows; 243 tests plus 24
subtests on Linux**, with four additional torch-dependent tests on Windows.
The portable-model suite passes all five tests on each platform. The new
package contributes31 tests. Both generated figures were visually inspected;
the derived report and figure hashes verify on both platforms. These are
implementation/integrity checks, not statistical confirmation of performance.

The next research decision should concern whether materially useful scheduling
opportunities remain under this causal information and action set, and how to
obtain deployable quality feedback. Another fresh holdout, a larger seed count,
or a manuscript claim of successful recovery is **not justified by this run**.
The measured integration is reusable, but the candidate's scientific advantage
over simpler causal controls remains unestablished.
