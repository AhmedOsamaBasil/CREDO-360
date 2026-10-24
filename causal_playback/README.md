# Causal current-quality and selected-transfer playback test

This is an **exposed-data development and engineering test**, not a new holdout
or a validated player. The frozen practical progression screen **fails**.
The implementation removes current viewport-quality labels from the decision
API, delays feedback until modeled playback completes, and transfers the actual
selected encoded MP4 files in isolated Linux network namespaces.

Read [PLAN.md](PLAN.md) for the protocol frozen at `d304470` before preparation
and outcomes, [INTERPRETATION.md](INTERPRETATION.md) for findings and limitations,
and [the full replay report](results/replay_v1/REPORT.md) for all seven policies
and six scenes. Prior packages and their negative findings remain unchanged.

## Information and resource contract

- Current estimates use known sender full-sphere quality plus per-user
  exponentially smoothed residuals from **completed selected segments only**.
- The opportunity model uses eight neighbors from 130 other-scene,
  target-identity-excluded trajectories. Known future encoded properties are
  allowed; current/future target viewport labels are not.
- Selected-quality feedback and the reference-rung counterfactual used to
  calculate recovery credit are **reference-assisted retrospective emulation**.
  No deployed telemetry system obtains these values in this prototype. The
  original event loss is also known retrospectively. Causal availability in
  the experiment is not proof of inexpensive client-side observability.
- Both users have minimum representation rung2. Predicted quality floors do
  not certify actual viewport-quality floors. Every actual loss is retained.
- Every round has a 1,500,000-byte actual-file cap. A finite, non-refilling
  extra-byte reserve equals the four-round baseline bytes. Pending predicted
  repayment affects planning only, not recorded delivered recovery.
- Recovery begins with zero buffer. All controller, launch, file I/O, hashing,
  transfer, waiting and pacing time is charged. The final playback tail is
  computed, not displayed or decoded. This is instrumented TCP, not HTTP/TLS.

## Reproduce without media or privileged networking

From the repository root, with Python, NumPy and pytest installed:

```sh
python -m pytest causal_playback -q
python -m causal_playback.verify
python -m causal_playback.verify --live
python -m causal_playback.audit_integration
python -m causal_playback.diagnose --verify
```

The deterministic audit regenerates all 1,176 episode-policy outcomes from the
published derived quality/size tables. The measured-data audit replays the
recorded receipt/feedback clocks and decisions; it does **not** rerun networking.
The independent support audit uses a separate queue recursion and checks
causality, cumulative reserve, selected-byte caps, training exclusion, service
rates, backlogged background traffic and the media-duration record.

To generate a new deterministic run without overwriting the frozen one:

```sh
python -m causal_playback.replay --output work/causal_replay_replication
```

## Repeat actual transfers locally

Requires Linux root, `iproute2`, `ethtool`, `ffmpeg`/`ffprobe`, and the previously
prepared, licensed local v2/v3 renditions. The media are **not** redistributed.
See the earlier [v2](../feasibility_recovery/README.md) and
[v3](../horizon_recovery/README.md) data preparation descriptions and source
terms. The following preparation uses existing files only, not downloads:

```sh
python -m causal_playback.prepare --output work/replication_media_manifest.json --cache work/replication_segments
```

Preparation verifies each source hash, remuxes without reencoding, and checks
ordered encoded-packet identity against the quality-label segment boundaries.
Container serialization can depend on the FFmpeg version. Compare the new
manifest with the published one; the live runner requires the published file
hashes, and intentionally rejects different bytes rather than mislabeling them.
The original local cache `.external/causal_playback_v1` matches those hashes.

For matching media, in a root Linux shell (only newly created namespaces are
modified; the host interfaces are not shaped):

```sh
python -m causal_playback.live --cache .external/causal_playback_v1 --output work/causal_live_replication
```

This runs the fixed 24 nominal and six undersized-service stress episodes,
at most two isolated namespace pairs concurrently. It creates real TCP
traffic and takes several minutes. It refuses to overwrite an existing
output directory, retains partial failures and cleans up its own namespaces.
Recorded timing varies across machines; do not expect identical timestamps.

## Artifacts and interpretation boundaries

`results/replay_v1/` contains all fluid-timing outcomes, the failed fixed screen,
hashes and both operating-system replay audits. `results/live_v1/` contains
selected rungs, file hashes/byte receipts, monotonic times, controller feedback,
raw per-episode journals, network configuration/counters and audited playback.
`data/media_manifest.json` binds 216 segments to 36 existing renditions.

The separate post-run media audit finds that the six final River01 files have
299 frames (299/30 seconds); all other files have 300 frames (10 seconds).
The frozen experiment retains its nominal ten-second clock. Because only the
last segment differs, duration-aware final completion is 1/30 second earlier
for River01, with **no decision, stall or repayment change**. Do not label the
frozen clock as a decoder-measured presentation timeline.

The first post-run support checker incorrectly required zero PTS offset even
for segment0, which was played before the recovery pilot and actually starts
at 0.1s. That initial checker remains unchanged because it was hash-bound in
the live metadata. `audit_integration` supersedes its whole-artifact check;
all transferred recovery segments start at zero. No scientific files changed.

The six scenes and participant trajectories were already exposed. Episodes
share content and identities; they are not 168 independent new subjects.
Quality is the existing clipped objective PSNR index, not human MOS. All
negative outcomes, including tiny actual floor losses and adverse quality
tradeoffs, remain available. No safe-admission, field-bandwidth, new scheduling
principle, independent confirmation or successful recovery claim is established.
