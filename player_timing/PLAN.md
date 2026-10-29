# Exposed matched-path browser timing protocol

## Question and scope

Does the earlier timing/repayment diagnosis depend on long delivery units and
cold start? This is an exposed engineering sensitivity study, not independent
confirmation, a new controller, an optimal shorter-segment policy, or human QoE.
Six existing scenes and all 168 previously exposed directed episodes are used
for deterministic replay. No new media, people, head traces or subjective labels.

Freeze this protocol, preparation, replay and measurement code before the full
derivation and measured batch. Compatibility probes and synthetic tests may
precede the freeze. Retain every scheduled failure; do not silently retry runs.
Necessary fixes after a freeze require a recorded amendment and new version.

## Locked reference and explicitly secondary variants

1. Original files: four approximately ten-second recovery segments, reference
   rung 2, initial past-only loss, 50% target, 40-second first-request deadline,
   original R4 nonrefilling extra-byte allowance and 1.5 MB per parent-pair cap.
   Replay the frozen `admission_contract` ideal-timing **proposed** paths of
   cost_greedy, rolling_nash and maxmin. Baseline rung2 is an additional replay
   control. These are ungated entry-time plans, not continuously recomputed
   controllers or the previously published admit/abstain actions. Keep them
   even if their original admission gate abstained, and report all false targets.
2. Secondary two-second delivery units: lossless packet remux at existing key
   frames; no encoding/quality tuning. Require five independently decodable
   chunks per parent, unchanged ordered payload hashes and decoded-frame hashes,
   correct PTS durations, and no non-keyframe start. Actual final duration stays
   299/30 seconds where present. If these conditions fail, report failure, not
   approximate quality by copying a ten-second label into every chunk.
3. Retain each parent rung for all its children. This separates delivery and
   completion granularity from adaptation. The unchanged four-action feasible
   oracle is context only; it is NOT an optimum for the secondary configuration.
4. Cold: each client starts as soon as its first whole file has arrived.
   Buffered: both clients wait until each has at least four media seconds in
   complete received units. Whole-unit rounding means one 10s or two 2s units.
   The 40s clock still starts at the first recovery request. There is no free
   prefetch, free advance bytes, initial buffer or restarted compensation reserve.
5. A request pair starts at entry, then no earlier than one nominal unit duration
   after the preceding pair and only after both preceding receipts. The same
   150000 payload bytes/s shared service and 0.13s setup per request apply.
   New two-second cadence/setup overhead is explicitly a changed transport
   contract, not a silent replacement of the original result.
6. Count every MP4 container byte. Sum each selected pair's positive excess over
   that unit's rung2 pair, without refunds. Use original R4; aggregate each
   parent pair's bytes against its original 1.5MB cap. Report violations; do not
   increase limits or change a frozen action to make it fit.

## Two separate quality accounts

Primary comparable account retains original past debt and original ten-second
quality/floors. Credit a parent only after **all** its children complete, using
the original duration and positive native-MSE improvement. Therefore splitting
cannot invent quality credit or erase an original floor violation.

Secondary chunk account derives actual per-second viewport-weighted MSE from
the existing sender tile maps and recorded sample masks, then averages only
within that chunk. Use original past debt, actual chunk duration and positive
chunk improvement, with both-user native chunk floors. Clipping/averaging and
floor granularity differ from the primary contract and are reported separately.
Per-second samples are not per-frame perceptual measurements; old acquisition
poses indexed by media time are not newly measured stalled-viewer motion.
All future quality stays in offline scoring, never in path selection or player.

Preparation correction, before timing outcomes: use the original label sampler
(first recorded pose at/after each half-second sample), not the earlier causal
feedback cache (last pose at/before). The initial 96-file remux validated but
the quality-parity assertion correctly rejected that cache. Revalidate cached
files without rewriting them and derive scoring masks from the same hash-bound
exposed trace archives. This is not a causal online quality estimator. No
tolerance, quality target, path, measurement schedule or deadline is relaxed.

Report timing-only, accounting-granularity, resource and floor effects separately.
Do not generalize the old universal infeasibility theorem to changed contracts.

## Deterministic and actual service

Analytical replay uses shared-fluid receipt times, actual packet durations,
zero additional decoder delay, and exact cold/buffer queues. All 168 episodes
times four paths times two unit sizes times two startup modes are reported.
Original cold 10s scores must match an independent original integer ledger;
where the old admission gate executed the proposed path, also verify its score.

The measured harness uses two real HTML video elements in one isolated headless
Chromium page, HTTP fetches through one loopback application payload shaper,
and whole-file Blob playback. Its finite-quantum fair shaper is not physical
network capacity, tc/Mininet emulation, end-to-end RTT, or a deployed DASH stack.
Pair concurrency competes for one cap, not separate per-user rates. A background
client negative control must share the same cap. Record shaper batches to audit
byte conservation and rate envelope; do not infer unused link capacity.

Every client event uses the same browser performance clock: request/response,
full receipt, play request, loadeddata/canplay, waiting/playing, video frame
callback, ended and completion-report availability. Keep server monotonic
events in their own domain; do NOT subtract unsynchronized server/client times.
Record requestVideoFrameCallback mediaTime, presentationTime, expectedDisplayTime,
presentedFrames and processingDuration where present. Missing callbacks,
dropped frames and timestamp uncertainty are outcomes, not silently imputed
frames. An ended event with a callback close to the final frame is an observed
software completion, not evidence of every displayed pixel or HMD presentation.
No hard .5s bound follows from a finite run. Report timing censoring/ambiguity.

## Fixed measurement schedule

Six scenes, recipient1/donor2 (fixed by identity, not selected by performance),
three frozen paths, two unit sizes, two startup modes: **72 sessions**. Rotate
the 12 cells cyclically by scene index to avoid a fixed policy/order alignment.
Run sessions sequentially, no heavy data preparation/regressions concurrently.
No run is an independent person or random seed. Report scene-level matched
descriptions, no p-values or confidence intervals from the 72 dependent runs.

Then two controls on ParkFountains01 cost_greedy, 2s cold: (a) delay first recipient
delivery by 40s before shaper eligibility; (b) a 6MB competing background fetch
eligible at entry. Both consume wall clock; background bytes do not count as
recovery reserve but share the service cap. Retain all receipts/censoring.
Per-session watchdog 150s, no automatic reruns. Browser/file compatibility
smoke checks are engineering development, separately labeled and excluded.

## Measurement validity and claims

Check file hashes, exact transferred payload bytes, no duplicate/missing unit
completion reports in successful sessions, monotone event order, media duration,
frame callback progression and actual request cadence. Detect all shortfall,
floor and budget failures. Replay accounting independently from raw events.
An invalid session remains invalid and cannot support a success claim. Do not
call received bytes played, callback counts people, or software events photons.
Report original parent completion credit at ended-event and report-available
times separately. Also report a conservative callback-tail witness: last
callback mediaTime must reach within 1.5 frame periods of the final PTS.

Primary API/format references:
- https://wicg.github.io/video-rvfc/
- https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement/requestVideoFrameCallback
- https://ffmpeg.org/ffmpeg-formats.html#segment_002c-stream_005fsegment_002c-ssegment

Code/data/results are published before any manuscript update. Raw source
videos and pose streams remain local under their existing source terms.
