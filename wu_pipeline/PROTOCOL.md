# Wu encoding and offline measurement freeze

This stage freezes code and validates it on generated patterns only. No Wu
media encoding, fresh quality/recovery outcome or manuscript change is part of
the freeze. Publish the method before an explicitly authorized fresh run.

## Immutable inputs and contract

Bind the pose method and both validation reports from `5be33f5`, the complete
qualified metadata roster and original confirmation design. Preserve all sixteen
registered clips, 768 source-ID records, 452 original directed pairs and previous
exclusions. Only the ten clips with validated pairs may be encoded. Do not
replace a clip or rebuild a pair cycle. Keep viewing conditions separate; the
48 repeated source identities are not independent new people.

The contract remains 50% repayment, a 40-second deadline, four recovery parents,
1,500,000-byte pair cap, cumulative rung-2-pair reserve, native per-parent floors,
150,000 payload bytes/s, 0.13-second setup and the original execution allowances.
No free startup, buffer, waiting time or reserve refill. This package does not
implement or run the subsequent recovery controller/feasibility campaign.

## Encoding and transport assets

Hash all seventeen originals first. Encode each eligible original's first sixty
seconds with the unchanged six nominal Mbps values:
0.045373, 0.088482, 0.252988, 0.368912, 0.987061, 3.792491. The inherited rounding
gives 45, 88, 253, 369, 987 and 3792 kbps; maxrate is twice and buffer four times
that value. Use 1920x960, 30 fps, H.264 NVENC p5/hq VBR, GOP/keyint 60, yuv420p,
no audio, and faststart. Preserve the inherited full-frame resize, including
non-2:1 input rasters; do not crop or change the calibrated normalized texture.

Freeze FFmpeg/ffprobe versions and executable hashes plus GPU/driver identity.
A changed runtime aborts rather than silently substituting a CPU encoder or
changing defaults. Runtime identity does not guarantee bit-identical NVENC
outputs on different hardware. Hash and preserve every actual encoded file.

Each rendition must have 1800 contiguous 1/30-second packets, zero first PTS
and stream origin, sixty-second container duration within 0.002 s, and keyframes
at all two-second boundaries. Validate six ten-second parent files per rendition.
For recovery rungs 2--5 and parents 2--5, also derive five two-second children.
Planned totals: sixty renditions, 360 parents and 800 recovery children.

Use the previously validated copy-remux and generated-container normalization
(`avoid_negative_ts=disabled`) only on newly encoded derivatives. It must never
repair an excluded original stimulus. Every final parent/child must independently
decode on its zero-origin timeline and preserve both compressed-packet hashes
and decoded-frame hashes against the parent sequence. Missing frames, a late
keyframe, extra packet, timing gap or identity mismatch halts the attempt.

Charge the final served MP4 file's entire byte length, including container
overhead. Payload-only bytes are diagnostic, not the service cost. Four-parent
durations are derived from audited presentation intervals and remain 10 s in
this fixed-CFR pipeline. Child overhead is recorded separately; no reuse of
parent costs as child costs. Raw intermediate remux files remain private.

## Measurement definition and temporal-phase diagnostic

Keep the legacy primary reference: the original verified stimulus decoded with
`fps=1,scale=960:480:flags=lanczos,format=gray`. Apply the same sampler to each
rendition. Require exactly sixty frames; never truncate to the shorter input.
Associate the original nominal half-second labels with the frozen pose adapter's
selected samples. Retain the inherited float32 tile-MSE representation, then
float64 cosine-latitude-weighted means over the 12-by-6 angular-window tiles.

The native metric includes resizing, frame-rate conversion and compression.
It is not pure compression error between guaranteed identical source frames.
A pre-freeze synthetic sixty-second probe found nine different sampled images
at 30000/1001 fps when comparing direct fps=1 with fps=30,fps=1; 16, 25 and
30 fps had no differences in that probe. Therefore record this pixel-hash phase
comparison for every real source. Differences are retained diagnostics, not
exclusion rules, alternative quality targets or an instruction to retime video.
Equal pixel hashes can reflect static content and do not prove source-frame
identity. The primary sampler and original comparison remain unchanged.

FFmpeg's fps filter drops/duplicates frames according to timestamp rounding;
the segment muxer splits at available keyframes and timestamp resetting alone
does not promise an exact zero origin. This motivates the executable checks,
not a claim of equivalence based on nominal frame rate alone. References:
[FFmpeg filters](https://www.ffmpeg.org/ffmpeg-filters.html#fps) and
[FFmpeg segment muxer](https://ffmpeg.org/ffmpeg-formats.html#segment_002c-stream_005fsegment_002c-ssegment).

For each trace, compute six-rung native viewport MSE for each ten-second parent
and, separately, each two-second child. Integer labels are nearest-even
`rint(-mean_MSE * 1e6)`, as in the exposed native chunk account, without converting
through rounded dB. Ticks are 150000 per second. Independently aggregate with
scalar compensated summation; require native agreement within 1e-9 MSE and
identical quantized integers. A rounding discrepancy is a technical failure,
not license to change a target/floor or select a favorable rounding rule.

Keep nonmonotone rung quality and any infeasible reference costs. No isotonic
repair, quality clipping, ladder selection or content-dependent target is allowed.
Zero loss will be a no-event disposition in later evaluation, not a success.

## Information boundary, failures and publication

All derived trace labels are explicitly offline-evaluation data. The pure
past-only view exposes completed parents strictly before a declared decision
boundary; it does not validate a controller implementation or permit access to
future poses. Freeze and audit the subsequent controller/measurement integration
before making causal performance claims. No browser timing is measured here.

Real preparation requires a separate explicit CLI activation containing the
registered method digest, a matching runtime and a new private output directory
outside the software repository. This flag is an accidental-launch guard, not
proof of author approval or GitHub publication. All input checks precede encode.
No retries, overwrites, fallback encoders, optional stopping or replacements.
On failure, retain private files and sanitized stage progress; no partial result
is reported as a completed confirmation. Publishing raw stimuli/traces is forbidden.

The release contains original code, source/runtime bindings, synthetic checks
and method metadata only. It does not certify physical-display timing, subjective
QoE, controller superiority, a new successful recovery mechanism or journal readiness.
