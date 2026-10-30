# Pose-adapter verification and provenance

Frozen method commit: `88c0616f38d1e2cbde0c011a180985927d62fd29`.
It was pushed and checked on GitHub before the Windows batch inspected any
reserved selected quaternion. All forty pre-batch synthetic tests passed on
both Windows and Linux. Post-batch artifact tests did not change the method.

## Bound artifacts

- Method registration SHA-256:
  `08d2afbb2a178091cdc7f9f17eb90e18a71ede58bd7afec365fc03efc8d8240e`.
- Parent metadata report:
  `58007f8a9264dd8318efc58bc41cd5687c0d89500ccfbc4af4d505cd1dadf6d2`.
- Windows pose-validation report:
  `e7f9cbf37b1e1107775bd1e4131e43b45623873177ad511196954b24f3968105`.
- Independently derived WSL/Linux report:
  `28293390e28767fca0e268e536362da3769b6f7a8d135a63229047b5130e8a6d`.

The reports retain 122 floating-summary differences; the maximum absolute
difference is 2.842170943040401e-14. Discrete decisions, flags, counts, identities,
exclusions and pairs agree exactly. Both reports pass the per-sample-summary
tolerances as well as the separately frozen cross-platform comparison. Repeated
software runs on the same files are not independent experimental samples.

## Geometry checks

All 27,120 selected quaternions pass integrity and normalization checks. The
maximum norm error is 0.000778696815634694, within the original 0.01 limit.
On Windows, maximum independent discrepancies are:

| Check | Observed maximum | Frozen tolerance |
|---|---:|---:|
| Forward-vector component | 9.993e-16 | 1e-12 |
| Circular yaw, degrees | 8.527e-14 | 1e-10 |
| Pitch, degrees | 7.106e-14 | 1e-10 |
| Angular viewport weight | 2.776e-17 | 1e-12 |

Nonzero tile membership agrees exactly for every sample. These checks compare
mathematical implementations using the calibrated convention; they are not a
second physical coordinate measurement or proof of what an HMD displayed.

## Failure and scope accounting

All 64 new unit/artifact tests pass on both systems, including nine scope-flag
subtests. Full regression passes 812 tests plus 57 subtests on Windows, and
808 plus 57 on Linux. The four legacy Torch tests excluded from Linux's local
environment are covered on Windows. The additional subtests are not independent
research observations. Previous metadata-release workflow 41041898514 is
verified completed successfully; a later commit's CI status is separate.
The five portable-model tests also pass separately on Windows (already included
in broad collection), as do 11 feedback-client assertions and shared-service
checks. Parent metadata, calibration platform comparison and original design
registration verify unchanged.

No scientific validation failure or selected-quaternion exclusion occurred.
The 316 pre-existing trace exclusions and six excluded clips remain unchanged;
their poses were not inspected. All 452 original directed pairs are retained,
with no repair or re-pairing. An injected invalid-endpoint test confirms that
one failed trace disables its two original incident pairs without removing them.

The method does not modify prior packages, source media, timestamp order,
normalization threshold, texture mapping, native quality floors, service budget
or deadline. No quality label, encoding, controller test, physical playback,
manuscript edit or submission was performed. The Linux systemd-session warning
was nonfatal; it did not prevent numerical validation or change any source data.

Both platforms rehashed the same seventeen originals, but reused the same prior
sequential media-timing audit. Only source-bound aggregate numerical checks are
published. Actual quaternions, yaw/pitch series, positions, demographics and
calendar timestamps remain private.
