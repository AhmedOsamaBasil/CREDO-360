# Verification record

Original registration (unchanged):
`af5c81f5b4711d9ee565413772d3a1d585722c10912be68a719a057f814a85b1`.

Failed-attempt audit SHA-256:
`a50b276952b1ef14dc0e8b516944b46d5f50ce1c1a2e3039718632aafd598f0f`.

Generated matrix report SHA-256:
`32fbfab4e5b45f83c9545ecbfc4dba36a263c3259eefa4aaac0b6f06b386816a`.

Both saved artifacts bind the original registration and this audit's source
files. The probe ledger supports independent endpoint arithmetic; a separate
FFprobe decoded-frame count confirms1,801 frames. Neither is a new real-source
encode. The generated matrix comprises four source generations and eight
NVENC output encodes, with no Wu source access by the synthetic runner.

Each bounded output contains exactly1,800 decoded frames, zero first PTS,
1/30s intervals and60.000000s container duration. The six-parent/five-tail-child
identity check passes. The unbounded29.97fps outputs fail, and those failures
are retained rather than dropped. All first1,800 decoded frame hashes agree
within each original/bounded synthetic pair. No claim of hardware bit parity
across machines or of success on the remaining real sources follows.

Tests cover command equality apart from the output cap at every ladder rung;
invalid durations/rungs; no overwrite or real-runner modification; output
directory guards; extra/missing frames; origin, grid, duration and keyframe
violations; ledger mutation; saved bindings and unsupported scope claims.
Artifact-dependent tests were skipped only before artifacts existed, then
rechecked after derivation. Test counts are software checks, not independent
scientific observations.

All25 new tests pass, with15 subtests. Full regressions pass891tests plus76
subtests on Windows, and887plus76 on Linux. The four legacy Torch tests are
covered on Windows and excluded from this local Linux suite. Saved artifact
hashes and original registration reproduce on both platforms. No GPU encode
is claimed on Windows. A scoped clean archive is checked separately before
publication, from its own working directory rather than the development tree.

The prior pipeline-release CI41066598818 at1d043ef completed successfully.
This release's local regression, clean-archive verification and remote workflow
status are separate checks; a prior successful workflow cannot certify a new
commit. All original source/pose/pipeline records remain frozen. Raw source
and encoded videos, participant records and local instruction files are not
part of this release. No manuscript or acknowledgment was changed.
