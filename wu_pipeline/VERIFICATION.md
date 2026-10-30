# Freeze-stage verification

Registration SHA-256:
`af5c81f5b4711d9ee565413772d3a1d585722c10912be68a719a057f814a85b1`.

Synthetic hardware-smoke report SHA-256:
`5c439238fd332a15a5f156bfa66317ad25f6b59313db17d76854d2e34dda9902`.

The method and runtime were frozen without opening any new Wu media or pose
values. The prior pose report is verified unchanged. Synthetic tests precede
fresh outcomes; this is not a completed confirmation experiment.

## Hardware and generated inputs

The runtime record binds FFmpeg/ffprobe 8.0.1-3ubuntu2 executable hashes and
build/version output, NVIDIA GeForce RTX 3090 driver 617.14, Python and NumPy
versions. The only encoding execution was a ten-second generated FFV1 test
pattern at 25 fps, encoded by the fixed rung-2 NVENC command. Full packet,
decoded-frame, zero-origin and duration checks pass for the rendition, served
parent and five served children. Ten grayscale samples produce a valid
10-by-6-by-12 tile-MSE map; this checks machinery, not scientific performance.

The served parent is 796,650 bytes; its five children total 800,146 bytes.
The 3,496-byte difference is retained as transport overhead, not discarded or
treated as extra free service. Measured bytes need not equal nominal bitrate
times duration. This test does not imply the fixed reference service is feasible.

The separate sixty-second temporal probe uses 64-by-32 generated patterns at
16, 25, 30 and 30000/1001 fps. Both sampling chains return sixty images.
At 30000/1001 fps, image hashes differ at zero-based bins
19, 23, 24, 29, 50, 52, 54, 55 and 56. Other tested rates show no differences.
These adverse phase results are kept and motivate a mandatory diagnostic;
they do not alter the inherited primary sampler or remove any real clip.

## Test and interpretation boundaries

Pure tests cover every rung's exact command, immutable service parameters,
timestamp gaps/duplicates, nonzero origins, keyframes, container duration,
payload signatures, no frame-count truncation, native-MSE arithmetic,
nonmonotone quality, past-only access and refusal of unsafe output/activation.
Artifact tests bind the complete roster, census, runtime, scope and retained
phase discrepancy. They do not need FFmpeg, the GPU or the private sources.

All 54 new unit/artifact tests pass on Windows and Linux, with four scope-flag
subtests. Full regression passes 866 tests plus 61 subtests on Windows and
862 plus 61 on Linux. Four legacy Torch tests unavailable in the local Linux
environment are covered on Windows. These test counts are not independent
scientific replications or participants.

One GPU smoke was performed on Linux. Windows verification of its saved report
is not an independent encoded-media experiment. No cross-platform bit identity
of hardware encoding is claimed. Neither synthetic tests nor an environment
fingerprint certify the yet-unrun sixty-second, six-rung Wu batch.

Prior pose-release workflow 41045300338 is verified completed successfully;
the new commit's CI status is separate. The initial read-only Git query used
the workspace rather than nested repository and was refused by the ownership
check. Correcting the working directory resolved it without global Git changes.
No raw third-party media, poses, private calendar timestamps, credentials or
local instruction files are included in the release.
