# Endpoint audit after the first Wu preparation failure

The published v1 registration and all previous scientific definitions remain
immutable. This is a post-failure engineering audit, not another Wu trial and
not a successful quality/recovery experiment. The first attempt is preserved.

## Read-only failed-file audit

Require exactly failure.json, an empty progress.jsonl and e1v01/r0.mp4. Bind
the original registration, failure record and all three file sizes/hashes.
Re-probe and independently decode-count the retained rendition. Retain the
packet ledger (timestamps, durations, sizes, flags and hashes), but no media,
images, raw poses, absolute private paths or calendar timestamps. Recompute
the endpoint summary from this ledger on both platforms. This second-platform
check is not an independent hardware encode or media decode.

The original control flow sampled source phase/reference images in memory
before encoding. These transient results were not saved. Failure occurred in
the timeline check before decoded-frame identity, segmentation, tile MSE or
trace-quality aggregation. No phase result may be reconstructed and presented
as the saved original diagnostic. There is no completed clip or experiment.

## Generated-only amendment test

The old command has input-side `-t 60` but no output-frame bound. The proposed
command adds only `-frames:v 1800` immediately before the output URL. It keeps
the input limit, source origin, scale/fps filters, NVENC configuration, ladder,
and every existing validation criterion. The bound is a maximum, not padding:
short output must still fail. It is not used to cut/repair the failed Wu file.

Before running this matrix, fix four generated 61-second 320x160 sources:
H.264 at 30000/1001 with requested B-frame maxima 0 and 3, H.264 at 30 with
maximum 3, and FFV1 at 25. Use testsrc2. H.264 generation uses libx264, preset
fast, CRF18, GOP60 and yuv420p; actual B-frame presence is inspected, not assumed.
For each, run original and proposed commands at rung0 for60s. Save both outputs
and every validation result, even if the old command does not reproduce the
extra frame. Record decoded-prefix pixel differences, without requiring
bit-identical NVENC outputs across differing termination conditions.

For each bounded output, require all frozen timeline and decoded-frame checks.
For the 29.97fps/B3 case, also verify six10s parents and the final parent's
five2s children, including exact compressed-packet and decoded-pixel closure.
These rung0 children are engineering checks, not a modification of which rungs
are eligible for the scientific recovery-child account. No quality scoring.

This limited matrix does not establish behavior for every source/ladder rung.
It is neither proof that B-frames alone cause the issue nor evidence that the
original dataset is invalid. No favorable-case selection, retry, overwrite,
real source re-encode or integration into v1 is allowed here. A new real
attempt requires a separately published versioned preparation method, preserving
all original exclusions, counts, service constraints and failed-attempt evidence.

FFmpeg distinguishes input duration limits from output duration limits, and
documents `-frames` as an output-stream frame limit; see the official
[FFmpeg command-line documentation](https://ffmpeg.org/ffmpeg.html#Main-options).
The prior ten-second/25fps FFV1 smoke did not cover this sixty-second boundary.
