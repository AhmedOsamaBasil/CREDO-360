# Frozen Wu encoding and measurement pipeline

This release freezes source-specific preparation code under the unchanged
recovery contract. **Only synthetic video was used for runtime testing. No Wu
encoding, fresh quality label, recovery experiment or manuscript change occurred.**

The [validated pose adapter](../wu_pose/README.md), original sources, runtime,
fixed roster, measurement arithmetic and failure rules are hash-bound in
`registration.json`. The frozen method is in [PROTOCOL.md](PROTOCOL.md).

## Planned preparation, not completed research measurements

| Item | Fixed count |
|---|---:|
| Registered clips, retaining exclusions | 16 |
| Eligible clips, five per viewing condition | 10 |
| Original directed pairs | 452 |
| Sixty-second, six-rung renditions | 60 |
| Ten-second parent files | 360 |
| Two-second recovery children | 800 |

Encoding retains the original NVENC p5/hq VBR settings, 1920x960/30 fps,
GOP 60 and six-rung ladder. No content-dependent target, rate, crop, floor or
viewport tuning is allowed. All served MP4 bytes are charged, including container
overhead. The original 50%/40 s/four-parent/1.5 MB contract is unchanged.

The implementation checks contiguous presentation intervals, keyframes, exact
frame counts, zero derivative origins, container duration, compressed-packet
identity and decoded-pixel identity across copy-remuxed parents and children.
Normalization applies only to generated derivatives, not excluded original
media. A failure preserves the attempt; there is no automatic retry or encoder
fallback. The runtime fingerprint is an environment binding, not a guarantee
of cross-hardware NVENC bit reproducibility.

## Sampling-phase limitation discovered before fresh outcomes

A generated sixty-second test pattern showed that direct `fps=1` and cascaded
`fps=30,fps=1` sampling differ in nine bins for 30000/1001 fps. They agree in
the tested 16, 25 and 30 fps patterns. The probe is retained; it is not a Wu
quality result. The fps filter's rounding behavior and segment muxer's keyframe
requirements are documented by [FFmpeg](https://www.ffmpeg.org/ffmpeg-filters.html#fps)
and its [format documentation](https://ffmpeg.org/ffmpeg-formats.html#segment_002c-stream_005fsegment_002c-ssegment).

The primary legacy measurement is unchanged: the original stimulus and encoded
rendition each use the same 1 Hz grayscale sampler, associated with nominal
half-second pose targets. Its native MSE includes temporal resampling and spatial
resizing as well as compression. It must not be described as pure compression
error between guaranteed identical source frames. Every future source receives
the same mandatory phase diagnostic, without dropping clips, changing the
reference or selecting a favorable sampler. Pixel equality alone does not prove
temporal source-frame identity, particularly in static scenes.

Native viewport MSE retains the original float32 tile representation and
float64 angular weights. Parent and child labels are separate. Direct native
micro-MSE integers use nearest-even rounding, and independent scalar aggregation
must give the same integers. No PSNR-roundtrip, rung monotonicity repair or
quality clipping is introduced. Actual pose series are not published.

## Verification without fresh inputs

From the software repository root:

```sh
python -m unittest wu_pipeline.test_core wu_pipeline.test_validation -v
python -m wu_pipeline.spec
python -m wu_pipeline.synthetic --verify
```

These commands verify the frozen registration and saved synthetic smoke. They
do not run FFmpeg or access fresh source media. The GPU smoke itself was run
once under WSL on an RTX 3090, using a generated ten-second fixture at rung 2.
It exercises encoding, parent/child transport checks and sampled tile MSE;
it is not a completed sixty-second, six-rung media campaign. Pure tests and
offline artifact checks run on Windows and Linux. See [VERIFICATION.md](VERIFICATION.md).

## Separate activation required

After publication and separate authorization for fresh preparation, the executable
requires exact original files, the matching registered runtime, a new private
directory outside the repository and the exact registration digest:

```sh
python -m wu_pipeline.prepare --private-dir /path/to/original-assets \
  --output /path/to/new-private-preparation \
  --activate-fresh-quality REGISTERED_SHA256
```

The flag guards accidental launches; it does not itself prove author approval
or publication. No command above has been used on Wu inputs in this freeze.
Derived labels are explicitly offline-evaluation data. The past-only interface
does not validate a subsequent controller or authorize its use of future labels.
Controller/feasibility integration and real browser timing remain separate work.

All earlier excluded clips/pairs remain in the reporting plan, including
nonzero media origins. Reference infeasibility, zero debt and unfavorable quality
must be reported later, not used to alter the service contract. This release
does not establish recovery success, human QoE or publication readiness.
