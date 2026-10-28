# Engineering contract and actual-duration timing protocol

Freeze before the full media audit, replay and timed sessions. All data have
already been exposed. The choice of contract follows the earlier sensitivity
findings and is not an independent preregistration or a successful new method.

## Contract: completed-segment distortion-seconds by a fixed deadline

Let e(u,t,r) be the existing reference-assisted viewport MSE estimate for user u,
segment t and representation r, reconstructed from the published segment PSNR.
Let d(t) be the actual media duration obtained from packet presentation timestamps
and durations, normalized to the first displayed timestamp. Units are squared
8-bit luma error times seconds. The source remains compressed reference video,
coarse 1 fps/tile-center/recorded-pose sampling; this is not human QoE or newly
measured per-frame perceptual quality.

Initial event: recipient rung0 rather than reference rung2 for segments0,1:

    D = sum_t d(t) * max(e(recipient,t,0) - e(recipient,t,2), 0).

For recovery segments2..5, a completed segment can supply

    c(t) = d(t) * max(e(recipient,t,2) - e(recipient,t,selected), 0).

Credit vests only after every frame and the final frame duration have completed
the specified playback timing stage. Deadline T=40 seconds from the first
recovery request, with a cold buffer. Credit from later completion is excluded.
Outstanding fraction is max(D-sum(c(t) for completion<=T),0)/D. The historical
50% repayment target is retained as an explicit engineering-account target,
not a human-perception threshold. Eventual credit is a secondary diagnostic.

Actual *media* duration, not elapsed wall time, weights quality. Stalls and
scheduler delays earn no extra credit. A segment mean is never prorated for a
partially displayed segment: deadline credit is conservative completed-segment
accounting. Multiplying a sampled segment mean by its actual duration is a
duration-weighted surrogate, not new frame-exact distortion integration.

Protected target attainment additionally requires neither user's selected
segment MSE to exceed its rung2 reference. Use the same deterministic micro-MSE
precision as `metric_contract`; do not introduce a post-hoc tolerance to hide
small violations. Startup, later starvation/pacing delay and secondary PSNR
are separate outcomes, not silently converted to distortion units. This contract
does not promise stall fairness or repair previously perceived distortion.

Resources remain 1,500,000 actual-file bytes per round and the non-refilling
extra-byte entitlement R=sum of four pair-baseline file sizes. Savings do not
refund prior positive extra bytes. Request cadence remains the frozen10s slots;
actual durations change playback, not previously selected actions or requests.

## Part A: exact-duration replay and finite offline bound

1. Read/hash all216 existing MP4 segments; independently probe packet PTS,
   durations and stream metadata. Require unique, contiguous presentation
   intervals, matching frame/packet counts and equal segment duration across
   representations. Publish scalar packet timelines and file hashes, not media.
2. Recompute playback for the168 exposed directed episodes and all8 frozen80ms
   policies, plus an explicit all-rung2 baseline. Preserve saved requests and
   arrivals. Compare nominal10s and actual packet durations. Report deadline
   and eventual credit, protected attainment, quality-floor losses and timing.
   Policies are not retuned for the new account and are not claimed to be
   optimized for it.
3. Recompute strict future-known opportunity over the same resource-valid paths,
   using actual durations and completed-segment deadline credit. Independently
   enumerate scalar paths. Nominal duration scores must reproduce the previous
   negative-MSE deadline/eventual results. No new causal admission guarantee.

## Part B: measured decode-and-PTS-paced timing

Six existing scenes; recipient1/donor2 fixed. Three schedules per scene:
prefix_mpc, prefix_cost_greedy and all-rung2 baseline. Exactly18 nominal sessions,
plus one ParkFountains01 primary session with all recipient file-release times
delayed40s. The latter must credit nothing to the recipient before40s; it is a
clock/availability negative control, not an additional scientific sample.
Scene order sorted, policy order rotated by scene index. At most2 sessions run
concurrently; report concurrency and hardware. No repeated trials or significance
claim. This small directed subset must not override the full168-episode replay.

Arrival times are scripted from frozen schedules, **not measured network
transfers in this turn**. At each release, FFmpeg software-decodes the selected
local file with one decoder thread and emits raw-frame hashes/PTS. A separate
consumer paces those frame events using the monotonic wall clock. The decoded
pixels are hashed, not displayed; this is a software playback-timing harness,
not a renderer, physical player/HMD or end-to-end perceptual test. No TLS,
client-attestation or deployed-feedback guarantee follows.

The consumer preserves every source-frame dwell duration, without dropping,
accelerating or overlapping frames. Decoder lateness stalls the schedule;
software wake-up lateness is separately recorded. Both affect completion and
deadline credit. Each frame's availability, target, presentation and completion
timestamps are logged, with file/frame identity, total duration and conserved
startup+decoder-wait+pacing-delay accounting. Frame availability is allowed ahead
of pacing; the timing surrogate queues frame metadata, not a rendering buffer.
This intentionally conservative policy is not a model of every commercial player.

Before each run, verify file identity. Preserve any failure, partial record and
timeout; no automatic selective reruns. Stop/clean only owned subprocesses and
threads. Deadline is40s, but drain the finite media to observe eventual completion;
per-session watchdog150s. Decoder/protocol/count/PTS violations invalidate that
session rather than silently correcting it.

## Validation and limits fixed before outcomes

- Synthetic tests: duration rational arithmetic; partial-final frame; first-PTS
  normalization; no pre-arrival credit; exactly-on-deadline inclusion; no credit
  for stalls or incomplete segments; quality floors; frame parser failures;
  pacing conservation; protected vs raw target; negative-control semantics.
- Both-OS exact replay, historical nominal parity, independent scalar bounds.
- Independent audit of every measured frame and segment, including no-drop PTS,
  completion conservation, deadlines and decoder errors. Publish raw scalar
  timings even when the expected timing or protected target fails.
- Record late completions, all measured decoder/pacing overhead and differences
  from ideal replay. Do not relax deadlines, change the account or pick a winner
  after outcomes. Keep original failed progression screens unchanged.
- New segment-timescale/re-encoding, physical rendering, human validation,
  network measurement, new data/holdout and manuscript changes are excluded.
