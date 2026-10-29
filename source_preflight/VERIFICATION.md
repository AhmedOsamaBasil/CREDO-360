# Verification and access limits

The offline assessment reproduces SHA-256
`be8b83bd962c6ac7e619012864d110c50b6ea084228cd73b11c540aa9df38080`
on Windows and WSL/Linux. It binds the original confirmation design, saved
source-access observations, review, intake/probe code and tests. It does not
claim to hash or verify the entire remote archive or any source video.

All55 new tests pass on both systems. They cover exact decimal sampling-age
boundaries; unsupported timestamp/frame inputs; missing or conflicting source
metadata; duplicate sessions; archive path/link/case safety; opaque pose fields;
private-field non-emission; bounded HTTP ranges and rejection of whole-body
fallback; full eighteen-clip accounting; the explicit author correction; failed
HEAD preservation; and rejection of promoted media/outcome claims.

Full regression:593 tests plus24 subtests pass on Windows;589 plus24 pass on
WSL. The four legacy Torch tests are covered on Windows. They cannot collect
in the current WSL environment because Torch is absent; the first broad Linux
invocation reported that dependency error, then the supported suite passed.
Portable-model tests pass5 on each system; Windows feedback tests pass11
assertions and shared-payload service tests also pass.

One initial Windows filesystem test failed because its default sandbox temporary
directory was not writable. An explicit workspace temporary directory resolved
the environment issue; the test and complete suite were rerun successfully.
A harmless Linux resource-cleanup warning appeared for a synthetic HTTP error,
and a WSL systemd-session warning did not prevent the checks from running.

The first range probe reused a temporary CDN redirect and received HTTP403.
Fresh requests through the original public download link succeeded without
authentication bypass or reduced TLS verification. The final saved probe uses
nine exact ranges, transferring119,200bytes; only the central directory and two
small video metadata members were inspected. The archive's actual member names
are `videoMeta.csv`, not the initially guessed `videoMetadata.csv`. All18 HEAD
checks succeeded, advertising3,470,683,984bytes in total. None of those video
bodies was downloaded or validated. No participant/demographic member was read.

The existing design registration still verifies as
`c40d455824ee689d8b2adc356526026ba6a18aed763bb42de3f1b5cfc69d9487`.
Its GitHub workflow40942455054 at a1d815e was verified completed successfully.
That is not a claim about completion of CI for a later commit.

No earlier frozen result/method, manuscript, acknowledgment, contract, source
eligibility rule or submitted file was changed. Raw third-party source files
and full papers remain outside the public repository. This artifact supports
the next source-validation step, not a new scientific performance claim.
