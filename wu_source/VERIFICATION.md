# Verification record

Canonical source audit SHA-256:
`f42bac62750b48c77e72e4cb6af6fb996a501acd8a693e8c6d50a4a2f002e976`.

Full source-file hashes, the864 clock summaries and the separately labeled
clock diagnostic reproduce independently on Windows and WSL/Linux. Both use
the same saved sequential-media audit: media decoding was performed in WSL
with ffprobe8.0.1, not independently with a Windows decoder. No quality/recovery
outcomes, participant orientations or demographic values were interpreted.

All48 new tests pass on both systems, including opaque pose fields, duplicate
clock retention, backward/missing/stale timing, exact index mapping, explicit
geometry candidates,200 independent quaternion rotations, absent-seek decoder
invocation, retained download attempts, source bindings, complete roster and
rejection of promoted readiness/quality claims.

Full regression excluding ignored historical workspace snapshots:646 tests
plus41 subtests pass on Windows;642 plus41 pass on Linux. The four legacy
Torch tests run on Windows only. The portable-model suite also passes5 in a
separate invocation on each platform (these are not additional independent
tests beyond the broad collection). Windows feedback-client checks pass11
assertions; shared-payload service checks pass.

Earlier source-preflight and confirmation-design hashes remain respectively
`be8b83bd962c6ac7e619012864d110c50b6ea084228cd73b11c540aa9df38080` and
`c40d455824ee689d8b2adc356526026ba6a18aed763bb42de3f1b5cfc69d9487`.
No files inside those frozen packages were changed. The prior GitHub workflow
40962525186 at578efb7 was verified completed successfully; that is not a claim
about CI completion for this later publication.

## Preserved failures and inspection limits

- Three first source-download attempts timed out; one second attempt also
  failed incomplete. All four partial files remain private and their hashes/
  lengths are in the public report. All19 final files satisfy expected lengths,
  signatures and repeated hash checks. No TLS verification was disabled.
- An initial media audit aborted on a nonzero start. A completed seek-based
  audit then revealed that seeking to zero can skip preroll. The final
  sequential decode has no initial seek; previous private artifacts remain.
  The two genuine nonzero-start streams are still reported as failures.
- A broad initial pytest invocation collected ignored historical snapshots,
  producing134 collection errors. Explicitly excluding `work` and `scratch`
  gave the full passing suites above; no old snapshots were removed or edited.
- One test invocation used an unwritable Windows sandbox temporary directory,
  causing two filesystem errors. Setting TEMP/TMP to a workspace directory
  resolved this environment issue. WSL systemd-session warnings did not prevent
  any verification. A denied process-inventory query was replaced by a safe
  process listing; no permission or global configuration was changed.
- A private source contact sheet was visually inspected, but neither it nor
  synthetic coordinate tests verifies the original texture wrapping sign.
  Post-inspection clock diagnostics do not revise the94 eligible trace count.

This is a reproducible source-alignment audit, not a fresh performance trial,
successful source-adapter freeze, full license clearance or journal-readiness
claim. Public results exclude raw media, participant rows and source images.
