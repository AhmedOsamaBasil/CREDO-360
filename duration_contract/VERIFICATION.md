# Verification record

The fixed protocol and initial method were published as `1a1fa78`. The secondary
PSNR axis correction and regression fixture were published as `66495ee` before
the completed replay or real-time timing batch. The first reporting failure is
retained in [execution notes](EXECUTION_NOTES.md); no scientific artifact was
overwritten and no threshold or selected action was retuned.

## Scientific and integrity checks

| Check | Result |
|---|---|
| Existing media hashes, sizes and packet presentation timelines | 216/216 pass |
| Complete exposed policy/duration replay | 3,024 rows reproduce |
| Historical nominal-MSE score parity | 2,688/2,688 exact |
| Independent scalar vs vector future-known bounds | 336/336 match |
| Actual/nominal fixed behavior pairs | 1,512 unchanged |
| Independent per-round/cumulative byte ledgers | 3,024/3,024 pass |
| Real-time software timing sessions | 19/19 complete; no selective rerun |
| Frame events / segment records audited | 45,594 / 152 pass |
| Late-release negative control | Zero credit before the deadline |
| Repeated-file decode consistency | 109 repeat streams match; 43 distinct files |
| New method and artifact tests | 25 pass on both operating systems |

Windows and Linux reproduce the same canonical results and hashes:

```text
Exact replay:
c0f655019f96fcc3ef01ddb242e46ded6a10180bb812e18a9da5a597f9dd448e
Measured-record audit:
3e13dc52d0ca32c5b5f8e27cdab1a8d690ad84a2613cea3025e820d1a4ddb647
Post-batch diagnostics:
c33d319041bae50f70fca24745fbb146f0cd7b40c1e120888b8c7f818c19ec3c
```

The real-time measurement itself ran **once under WSL**, not once per operating
system. Windows and Linux independently re-execute the deterministic replay and
audit the same measured records. Timing values are not expected to repeat exactly
on another wall-clock run. Figure PNG/SVG artifacts were visually checked and
their bytes are hash-bound separately from the scientific result.

## Runtime and regression coverage

Timing host: Intel Core i9-11900K, 8 cores / 16 logical CPUs; Linux
6.6.87.2-microsoft-standard-WSL2, Python 3.14.4, FFmpeg 8.0.1-3ubuntu2.
One software decoder thread and one raw encoder thread per file, at most two
sessions concurrently; no GPU acceleration. File integrity is checked before
each session, so this is a warm-cache experiment. No heavy regression or replay
work was run alongside the timed batch. CPU model was inventoried after the
batch; runtime library versions and concurrency were recorded before it.

Full regression after measurement:

- Windows: **361 tests and 24 subtests pass**, including four Torch tests.
- Linux: **357 tests and 24 subtests pass**; the Linux environment lacks Torch.
- Portable model: **5 tests pass on each operating system**.
- Feedback client: **11 JavaScript assertions pass** under Windows Node.

The full suite covers the historical recovery packages through the current
duration contract, measurement assessment, portable/scaling/gate/live-runner
checks and multimedia generalization. No previous frozen method or result file
was modified. The CI workflow now verifies the new replay, measured-record audit,
diagnostics and tests when their artifacts are present. Local verification is
not a claim that an as-yet-running remote CI job has finished.

## Public reproduction boundary

The [README commands](README.md#reproduction) verify all published scalar results
without redistributing raw videos or pose telemetry. The public timeline audit
binds the existing media identities; reproducing **decoding and new wall-clock
measurements** additionally requires the original, hash-matched local media cache
and FFmpeg/ffprobe. Their preparation/measurement commands deliberately refuse
to overwrite the frozen attempt.

Engineering checks passed. Controller superiority and a deployable recovery
guarantee were **not** established. The manuscript, acknowledgment and unused
holdout data were not changed.
