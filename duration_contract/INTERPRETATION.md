# Interpretation: engineering contract and actual media duration

## What is being tested

This study makes the engineering claim precise rather than changing the metric
to favor the controller. It follows the earlier exposed-data sensitivity study;
it is not independent confirmation or a new subjective-quality model.

The account is the positive reduction in sampled viewport MSE relative to rung2,
weighted by actual media duration. Initial loss is the same rung0 impairment in
segments0 and1. Recovery credit is earned only after a complete segment,
including its last frame dwell, completes by40s from the first recovery request.
The target is50% of that initial account, an engineering choice, not a perceptual
threshold. Both users must also avoid native-MSE floor losses on every selected
recovery segment for protected attainment. Floor checks include segments that
finish after the deadline. Startup and subsequent delays remain separate costs.

The per-round1.5MB actual-file cap and non-refilling R4 extra-byte allowance are
unchanged. Actions, requests and scripted arrivals are frozen. These policies
were not trained or optimized for the new account; this comparison cannot show
that no possible causal controller would perform better.

## Complete exposed replay

All168 directed episodes and eight saved policies plus the baseline were scored
under both nominal and measured media durations:3,024 rows. All2,688 historical
nominal negative-MSE scores match. Independent scalar enumeration verifies all336
duration-specific future-known bounds.

| Policy | Raw half-repayment by40s /168 | With both-user floors /168 | Mean deadline unpaid fraction |
|---|---:|---:|---:|
| Primary prefix planner | 1 | 1 | 0.806350 |
| Cost-greedy | 10 | 10 | 0.764070 |
| Greedy | 22 | 9 | 0.738321 |
| Rolling Nash | 15 | 7 | 0.812861 |
| Max-min | 17 | 6 | 0.752219 |

The primary controller is worse than cost-greedy on both protected target count
and mean unpaid loss. Some higher raw counts rely on paths with small native
quality-floor violations; their magnitude should not be confused with evidence
of noticeable perceptual harm, but they do invalidate an exact zero-loss claim.
The complete report also retains completed-feedback, slack and waiting policies.

Even strict future-known optimization can meet the deadline target in only27/168
episodes (28/168 eventually). That is a conditional upper bound under the stated
catalogue, structural rungs, floors, resources and timing model, not a causal
service guarantee or proof about all streaming systems. No estimator can solve
infeasible instances without changing a declared service requirement.

## What actual durations change

All216 existing MP4 files pass the saved hash/size and contiguous-presentation
timeline checks. Only River01's six final representations contain299 rather than
300 frames:9.966667s instead of10s. Across the frozen paths, actual-duration
accounting leaves deadline/eventual recovery and protected target outcomes
unchanged. River final completions advance by exactly1/30s; other scenes do not
change. A duration-weighted secondary PSNR mean can change without changing the
recovery account. Correcting the nominal duration is necessary bookkeeping, but
does not rescue this controller or explain its shortfall.

With a cold buffer,40s of nominal media cannot all finish within40s of the first
request when startup is positive. This is explicit in the contract; it is not
silently treated as40s of completed playback. The last-segment dwell must not be
omitted to create apparent on-time credit.

## Measurement boundary

All19 fixed sessions completed without decoder, PTS, frame-count or conservation
failures:45,594 frame events and152 segment records. The late-release control
earned zero recipient credit by40s. Independent repeated-file comparison checks
109 repeat streams across43 distinct encoded files. No failed session was
discarded or selectively rerun.

For the six nominal fixed pairs per policy, measured mean added finish time
relative to ideal playback is0.225803s/user for primary,0.256300s for cost-greedy
and0.183995s for baseline. Corresponding startup/later delay means are
4.738427/2.429452s,6.280213/0.949359s and3.703059/0.687712s. These are one-batch
descriptive values, not confidence intervals or a causal latency comparison.
Summed software pacing lateness averages0.292557s per player; it is not simply
added to ideal completion because some delay is absorbed by later scheduled gaps.

Four nominal sessions lose some deadline credit compared with the ideal clock:
primary and cost-greedy on BuskingUnderpass05 and Cheerleading01. The recipient's
third recovery segment ideally completes at39.802773s and39.968600s respectively,
but completes around40.095--40.109s in the measured sessions. This illustrates
deadline sensitivity to even modest implementation overhead. None of these
sessions reaches half-repayment under either clock; none of the six nominal
pairs reaches it for either policy. Mean measured unpaid loss is0.807455 for
primary and0.782974 for cost-greedy. This small subset does not change the full
population's conclusion or establish statistically significant policy differences.

The real-time harness decodes the existing files and paces frame events using
their PTS. Arrivals are scripted from previously saved schedules. Pixels are
hashed and discarded, not rendered. Queued frame metadata are not a real player's
pixel buffer. File identity is checked before each session, warming the cache.
There are at most two concurrent sessions, one trial per fixed scene/policy, and
no timing confidence interval or field-service guarantee.

Decoder availability, software wake-up delay and final-frame dwell all contribute
to completion. Their scalar timestamps permit independent no-drop, no-overlap
and conservation checks. Repeated-file frame hashes can establish deterministic
decode consistency, not source-reference image-quality correctness. A recipient
release delayed40s must receive no deadline credit.

These measurements do not constitute new TCP transfer measurements, physical
display/HMD playback, client attestation, human QoE validation or a fresh holdout.
The six fixed directed pairs cannot replace the full168-episode comparison.
Existing quality samples remain coarse, reference-assisted segment estimates;
duration weighting is not a new frame-exact distortion integration.

## Research consequence

The result is an auditable service-account and timing boundary, not a successful
new recovery controller. A next design should explicitly reject unsupported
recovery promises or state a different service budget, target or segment timescale
before testing. Any such change is a new contract, not retrospective success for
this one. Another fresh holdout is not justified by the current outcomes.
