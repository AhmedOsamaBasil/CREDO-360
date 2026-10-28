# Feasibility admission: results and limits

The fixed contract was not relaxed. The full study uses the same 168 exposed
directed episodes, actual media durations, 50% distortion repayment by 40 s,
strict quality floors, four recovery segments, and original byte allowances.
Method/protocol commit `699bca5` preceded the batch; no method was tuned after
the outcomes. The new work is admission logic and deterministic replay, not a
new physical-player, network or human experiment.

## Main result

| Entry-time method | Admissions /168 | Fulfilled in replay | False promises | Observed precision |
|---|---:|---:|---:|---:|
| Spatially certified planner | 0 | 0 | 0 | Undefined |
| Point-prediction minimum-byte planner | 28 | 27 | 1 | 27/28 |
| Cost-greedy | 28 | 27 | 1 | 27/28 |
| Rolling Nash | 17 | 4 | 13 | 4/17 |
| Max-min | 17 | 4 | 13 | 4/17 |

These are the primary 0.5 s per-segment execution-allowance results. Ideal timing
gives the same counts. Applying the spatial certificate to any point-control
path admits zero requests. With unbounded execution, no deadline promise is
certified. Zero false promises with zero admissions is not useful admission
performance; precision is intentionally undefined.

The certified planner distinguishes **112 model-impossible episodes** from
**56 abstentions**. Impossibility is established using an optimistic upper bound
that permits all four segments to complete and ignores floors: it is not an
artifact of a pessimistic deadline. All BuskingUnderpass05, Cheerleading01,
ConferenceParticipant02 and Train01 episodes are impossible under this
quality/resource relaxation. All ParkFountains01 and River01 episodes remain
unresolved by the conservative certificate. Abstention is not a proof of
infeasibility: the exact future-known comparison admits 27 River01 episodes.

## Why the positive point result is not a new reliable mechanism

All 28 point-planner admissions come from **one scene, River01**. All use the
same path: recipient rung4 for the first two recovery segments and rung2 for
the rest, with the donor always on rung2. Point planner and cost-greedy have
identical admission decisions and executed paths in **all 168 episodes**.
No distinct benefit of the more elaborate planner is established. On this
exposed catalogue its admission decisions also coincide with a River-only rule;
this is a post-outcome observation, not a separately validated classifier.

The false promise is recipient12/donor11 on River01. Predicted repayment is
60.5433%, but actual replay repayment is **49.8513%**, below the unchanged50%
target. There are no quality-floor violations in this case. Even the exact
future-known best path reaches only49.8513%; the shortfall is small but cannot
be retrospectively labeled successful. There is no risk-calibrated probability
bound behind the observed27/28 precision, and these are not independent fresh
content trials.

Rolling Nash/max-min are precisely specified **entry-time planning controls**
using the shared causal point forecast and cumulative positive PSNR utilities.
They are not reruns of the historical adaptive controllers with the same names.
Their13 failed admissions have native quality-floor losses. For the identical
rolling-Nash paths,21 individual losses have a maximum of0.001754dB and a mean
of0.000703dB. These small differences violate an exact floor but are not evidence
of noticeable human harm. We do not relax the floor or hide their magnitude.

Likewise, comparing27 new successes directly with the historical primary's1
would conflate changes in forecast, entry-time commitment and contract-aligned
planning with admission filtering. It is not an isolated admission-effect test.

## Why the conservative certificate abstains

The sender envelope covers arbitrary convex tile weights and is wider than the
actual geometric viewport family. On River01, the mean certified lower repayment
is only6.91%, compared with76.07% for actual future-known optimization and135.32%
for the deliberately optimistic upper bound. These uncapped ratios summarize
different bounds, not confidence intervals or achievable causal gains.

A separately labeled post-outcome check removes floor restrictions from lower-
bound maximization. The maximum lower credit does not improve in any scene.
Thus inadequate guaranteed positive gain, not only tiny floor violations, blocks
admission. No threshold or envelope was tightened after observing these results.

## Timing and information assumptions

All152 earlier measured segment records satisfy the assumed0.5s incremental
execution envelope; the largest observed residual is0.178512s. Those samples
come from the earlier19 software decode/pacing sessions, not new execution of
these admission-selected paths. They do not establish a hard OS/player latency
bound or a statistical reliability level. The reserved transfer-service bound
also remains conditional. Unbounded service/execution cannot justify a deadline
promise, regardless of how accurate a quality forecast appears.

Admission assumes an exact completed-event debt/reference ledger. Existing
sampling/pose-alignment error and client attestation are not newly resolved.
Only past quality enters the entry API; future viewport labels are used solely
for offline evaluation. Sender content maps and file sizes are available in
advance. The planner computes and commits its schedule before the first recovery
request, when the fixed contract starts its clock. This study does not measure
admission-computation latency or establish a pre-request response deadline.

## Research decision

The result supports an auditable **rejection/abstention boundary**, not a useful
certified positive-admission system or new optimal-controller claim. It also
shows why a successful point forecast is insufficient for a promise.

A defensible next development is to tighten the spatial envelope to the actual
geometric viewport family while keeping the same contract and exposed data,
then determine whether any conditional positive admissions become nonvacuous.
Any motion or probabilistic restriction would need an explicit, justified
assumption. Another fresh holdout or manuscript success claim is premature.
