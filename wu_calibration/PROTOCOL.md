# Two-clip alignment calibration amendment

The author approved this explicit amendment after the source-only audit.
Experiment1/Video2 (skiing; paper Figures10--12) and Experiment2/Video4
(basketball; Figures7--9) are **calibration**, not confirmation. The remaining
16 original clips, eight per viewing condition, are reserved for subsequent
content confirmation. The same48 identities recur: no person-disjoint or
random-population holdout claim is warranted. Previously inspected metadata
and original-video previews are disclosed by the preceding source audit.

This amendment does not edit the original design or change the50%/40s/R4/1.5MB
contract, ladder, native floors or whole-parent actions. It permits calibration
pose/time inspection only for these two clips. No quality/recovery outcome,
remaining-clip pose conversion, new controller or manuscript update is run.
The original all18-clip design is retained as history, not silently overwritten.

## Coordinate reference

Use the source-author basketball visualization pinned to the commit/blob in
`amendment.json`, never a convenient third-party converter. The inspected
renderer maps each pair(a,b) to(u=b/2,v=abs(a-.5)) and uses the last CSV row in
each truncated decisecond bucket. Bind downloaded bytes to Git's blob hash
and SHA-256. Verify its relationship to the basketball stimulus; if that
relationship or the schema cannot be established, report the uncertainty.

At the five prespecified times compare the paper's xyzw forward-vector formula
with both horizontal texture signs, using first and last admissible ascending
crossings in the original trace order. Do not sort nonmonotonic playback times
or assume demo columns identify particular people. Use spherical distance and
minimum-sum assignment for unordered48-point sets; keep per-time and pooled
errors, both signs and both crossing rules. The fixed evidence gate is in the
amendment. A match can establish this source's projection convention, not
ground-truth historical HMD presentation timing or perceptual validity.

## Clock diagnosis

Read all96 calibration traces with exact header and explicit clip guard. Keep
calendar timestamps and raw poses private; public artifacts contain only
relative-clock diagnostics, aggregate coordinate residuals and source hashes.
Positions and demographic files are not used. Record quaternion norm errors;
normalization is explicit and limited as specified, never selected by quality.

For every half-second target in the original first60s, list admissible ascending
crossings (previous playback time below target, current time at/above it with
age<=.1s). A first record already above a target is not a bracketed crossing.
Compare first/last crossing, count missing/multiple crossings, and retain wall
clock order and playback regressions. Startup transients, later reversals and
repeated clock values must be distinguished. A single crossing despite an
earlier reversal is diagnostic evidence, not automatic authorization to delete
records or a guarantee that the historical player showed that exact frame.

All threshold and timing-map development is confined to calibration. Any
subsequent adapter must document what is supported, ambiguous or excluded and
be frozen before inspecting the16 reserved clips' poses. The two nonzero media
origins previously found in reserved clips cannot be silently normalized based
on a calibration result from different files. Source evidence is still needed.

## Public artifact scope

Publish original calibration software, tests, source hashes, residual summaries
and all failed checks before any manuscript edits. Do not redistribute the
reference CSV, raw source traces, source frames or full paper. Author citation
instructions are not a blanket redistribution license. Preserve prior frozen
packages and this amendment even when later findings require a new version.

Reference: Wu et al., *A Dataset for Exploring User Behaviors in VR Spherical
Video Streaming*, MMSys2017, DOI[10.1145/3083187.3083210](https://doi.org/10.1145/3083187.3083210),
and the [author visualization](https://wuchlei-thu.github.io/).
