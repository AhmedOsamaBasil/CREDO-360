# Qualified Wu pose adapter, version 1

Freeze and publish this method before inspecting reserved-clip quaternion
values. Bind the exact metadata report at `ecc4e5d` (SHA-256
`58007f8a9264dd8318efc58bc41cd5687c0d89500ccfbc4af4d505cd1dadf6d2`).
This is source engineering validation, not fresh quality/recovery evaluation.

## Access and selection

Retain all 16 registered clips and 768 source-ID records, including every
earlier exclusion. Read selected quaternions only for the 452 clock-and-media-
qualified files. Check the complete archive and all sixteen original videos
against the frozen source hashes before access. Media are hashed, not decoded
again. Check each accessed member hash, original clock evidence and selected-
row digest against the metadata roster. The six excluded clips and all other
excluded source-ID files must fail the pose-access guard before a member read.

Use the unchanged conservative clock selector: one ascending crossing of each
0.5, 1.5, ..., 59.5-second target, counting all chronological crossings before
age filtering; age at most 0.1 seconds; original wall-clock order, initial bracket
and coverage through 60 seconds. No sorting, trimming, shifting, interpolation
or first/last choice. Recheck all decisions against scalar interval counting.

Only the four xyzw fields in the sixty selected data rows are converted to
numbers. Other pose rows and all positions remain opaque strings; no demographic
member is accessed. Report selected-sample integrity, not whole-trace quaternion
validity. Calendar timestamps and all actual pose series remain private.

## Quaternion, geometry and numerical checks

Reject a trace if any selected quaternion is nonnumeric, nonfinite, zero, or has
absolute norm error greater than 0.01. Record reason counts and the number of
selected samples affected. Do not repair a failed sample or keep a partial pose
series. Normalize only valid samples explicitly, as in the calibrated adapter.
The existing floating-point threshold comparison is unchanged.

Use the calibrated rotation of +Z and negative texture mapping:
u = (-atan2(z,x)/(2*pi)) modulo 1, v = acos(y)/pi;
legacy yaw = 360*u - 180, pitch = 90 - 180*v. No alternate mapping is fitted.
Compare each normalized forward vector with independent scalar Hamilton
multiplication (component tolerance 1e-12), and circular yaw/pitch with the
existing scalar projection (1e-10 degrees). At a mathematically ill-conditioned
pole or tile boundary, a disagreement still stops the validation batch; it is
not silently waived or used to exclude a participant. Any required numerical
amendment must retain the attempt and be versioned before rerunning.

Compare the unchanged legacy 6-by-12 angular-window viewport weights against
the scalar implementation at absolute tolerance 1e-12 and identical nonzero
tile membership. These weights are geometry only: no image distortion, PSNR,
SSIM, encoding, quality label or recovery calculation is allowed. Synthetic
axis, sign, scale, seam, rotation and fault tests run before real pose access.

## Failure accounting and fixed pairs

Input-hash, clock/index, method-binding or independent-geometry inconsistency
halts the batch with a sanitized failure artifact and retained progress. Do not
mislabel it as scientific ineligibility. Invalid selected quaternion samples
are explicit trace-level validation failures, with no silent data substitution.

Keep all 452 original directed candidate pairs exactly as registered. A pair
is usable only if both endpoint traces pass. Retain failed pairs and their
reasons; do not rebuild the cycle, replace an identity or remove a registered
clip. Report both conditions separately and account for the repeated 48 source
identities. A usable source pair is not a feasible service or recovery outcome.

## Release and replication

The versioned method binds this protocol, implementation, synthetic tests,
metadata roster, calibrated adapter and original viewport geometry. Freeze it
before the full batch; later artifact tests may check but not alter selection.
Reproduce from private originals on Windows and Linux. Preserve both reports
if floats differ; cross-platform comparison requires exact discrete values
and absolute tolerance 1e-10 for finite numeric summaries. Any difference in
acceptance, source identity, counts, pairs, flags or reason codes fails.

The report may certify the sampled pose adapter for usable registered pairs,
not historical physical display alignment, a complete media/experiment pipeline,
human QoE, population generalization or controller superiority. Automatic
outcome launch and full-experiment readiness remain false. The earlier source
reports, calibration guards, contract, manuscript and acknowledgment remain
unchanged. Publish only original code, aggregate checks, source hashes and
eligibility records; no raw inputs, actual yaw/pitch series or instruction files.
