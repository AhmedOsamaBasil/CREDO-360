# Remaining recovery opportunities and quality feedback

This package audits the remaining opportunity under the **existing** resource
contract and implements a sender-reference-assisted feedback path. It uses
exposed data only. The feedback channel works, but the unchanged recovery
controller still fails its practical progression screen.

- [Fixed protocol](PLAN.md), published as `a162d37`; controller/receiver/audit
  implementation published as `447f3a4` before complete outcome evaluation.
- [Interpretation](INTERPRETATION.md), [corrected result report](results/diagnostics_v1/REPORT.md)
  and [opportunity/feedback figure](results/diagnostics_v1/opportunity_feedback.png).
- [Measurement attempt notes](MEASUREMENT_NOTES.md).

## What the feedback path does

The content provider precomputes per-rung, per-second 12x6 distortion maps
against its source reference. The JavaScript client reports ten viewed-tile
masks after a segment completes. The Python receiver combines those masks
with the maps and latitude weights, reconstructing both selected-rung quality
and the counterfactual rung2 reference needed for repayment accounting.

The client receives **neither reference video nor per-user quality labels**.
This is client-reference-free, not no-reference quality assessment: the sender
still requires reference analysis. The original source is the previously
downloaded compressed reference, not a lossless master. The metric remains
the existing 1fps grayscale tile-center approximation, not human QoE or exact
perspective-viewport rendering quality.

`client.mjs` exports `SegmentFeedback`. Feed `observe(mediaTime,yaw,pitch)`
from the renderer's presentation events, in the declared yaw/pitch convention.
It selects only a stored past pose at each half-second sampling point and
rejects missing/stale samples. `finish(mediaTime)` emits the completed report.
`sample(...)` is the explicit resampling interface used by the trace harness.
No automatic HMD connection is claimed: the adapter was exercised in Node.js
24.19.0 with recorded pose events and cross-checked against Python.

For a real integration, obtain the pose actually used for rendering, not a
download-completion callback. The [W3C WebXR frame/pose API](https://www.w3.org/TR/webxr/#xrframe)
defines viewer-pose access within the frame loop. Mapping that pose into this
dataset's yaw/pitch convention, aligning media presentation time, handling
missing tracking, and validating the resulting renderer remain player-specific
tasks. The prototype uses six nominal ten-second segments; the known one-frame
short River01 ending still needs correct media-end normalization in a player.
No actual HMD, decoder or WebXR device was tested here.

## Binary report and receiver

| Field | Bytes |
|---|---:|
| Protocol magic `VQF1` | 4 |
| Sender-map descriptor SHA256 | 32 |
| Segment / selected rung | 1 / 1 |
| Sequence number | 4 |
| Completed media position, float64 | 8 |
| Ten 72-bit tile masks | 90 |
| Total | **140** |

Multibyte fields are big-endian. Tile bits are row-major, least-significant bit
first within the logical 72-bit integer; each integer is serialized big-endian.
The descriptor binds the map asset; it is **not** a message-authentication code.
The server rejects malformed packets, incomplete playback positions, unknown
content and duplicate/out-of-order reports. Test HTTP listeners bind to
`127.0.0.1` only and are shut down after the run.

Production use requires authenticated sessions, TLS, bounded session storage,
rate limiting, consent/retention controls and a trustworthy player timeline.
The current receiver trusts client playback/pose reports; it does not provide
remote attestation. Viewport masks can reveal viewing behavior and must not be
treated as anonymous. Real pose/mask packets stay in ignored local storage.

## Reproduce public scientific checks

From the repository root, with Python, NumPy, pytest and Node installed:

```sh
python -m pytest feedback_opportunity -q
node feedback_opportunity/test_client.mjs
python -m feedback_opportunity.verify
python -m feedback_opportunity.diagnose --verify
```

The public audit checks map/output hashes, exact old-sampling parity, all
derived feedback values, exhaustive paths versus independent dynamic
programming, and all 1,176 controller replays. It does not recreate private
pose packets or rerun a network experiment. All opportunity paths and
controller choices are available in compressed JSON.

**Reporting correction:** the original frozen `audit_v1` summary compared an
in-memory tuple with a JSON list, incorrectly reporting 672 changed actions
per policy. Raw actions and scientific outcomes are unaffected. The separate
`diagnostics_v1` report normalizes representations and verifies **zero changed
actions across all 4,704 decisions**. Use that corrected report, not the known
incorrect original summary field. Both artifacts are retained for traceability.

## Reproduce private preparation and wire checks

The six exposed source/rendition/trace caches must already exist under
`.external/feasibility_v2` and `.external/horizon_v3`, with matching source
hashes and appropriate source permissions. No download is performed here.
Preparation refuses to overwrite artifacts; use alternate output/private
paths for a new preparation, and explicitly rebind any new asset hashes.

The original execution sequence was:

```sh
python -m feedback_opportunity.prepare
node feedback_opportunity/client.mjs .external/feedback_opportunity_v1/client_events.json .external/feedback_opportunity_v1/client_packets.json
python -m feedback_opportunity.wire
python -m feedback_opportunity.run
python -m feedback_opportunity.verify --private
```

Do not rerun default preparation/output commands over the published outputs.
`wire` and `run` accept `--output` for separate replications. Private verification
checks all 1,008 JavaScript packets byte-for-byte against independently encoded
Python masks and reconstructs every recorded response. Sender maps and scalar
derived results are public; third-party media, raw traces, pose events and
mask packets are not redistributed.
