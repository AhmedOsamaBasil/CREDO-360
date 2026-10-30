# Wu endpoint failure and output-boundary correction test

The first authorized preparation attempt failed at its first rendition,
e1v01/r0. The file is692,247bytes, has1,801 packets and independently decoded
frames, starts at PTS0 and includes a frame at PTS60s. Its presentation end is
1801/30s; its container reports60.033008s. The frozen contract requires1,800
frames ending at60s. The validator correctly rejected it.

The failed file, empty progress log and failure record remain private and
unchanged. Public [audit evidence](results/attempt_01/report.json) contains
only hashes, packet metadata and count results. No completed rung, parent,
child, tile-MSE map, viewport label, complete manifest or recovery result was
produced. Source phase/reference sampling happened in memory before the
encoding; those transient results were not saved and are not asserted here.

## Diagnosis and generated-only test

The original command limits input reading with `-t 60`. This does not enforce
the registered output-frame count after frame-rate conversion. The proposed
`bounded_command` adds exactly one output option, `-frames:v 1800`; it changes
neither the target count nor the sampler, source alignment, ladder or service
contract. It is **not integrated into the original real-source runner** and
has not been applied to any Wu video. No real retry occurred.

Four generated61s sources were encoded with both commands at rung0 using the
frozen RTX3090/FFmpeg runtime. All corrected outputs pass the unchanged
timeline and decode checks:

| Generated source | Original frames | Bounded frames | Differing frame hashes in first1,800 |
|---|---:|---:|---:|
| H.264,30000/1001fps, no B-frames | 1,801 | 1,800 | 0 |
| H.264,30000/1001fps, B-frames present | 1,801 | 1,800 | 0 |
| H.264,30fps, B-frames present | 1,800 | 1,800 | 0 |
| FFV1,25fps | 1,800 | 1,800 | 0 |

The zero entries count differing **frame hashes**, not a pixel-wise numerical
distance. The 29.97fps/B-frame bounded case additionally passes six10s-parent
and final-parent five2s-child packet/pixel identity checks. These tests check
the endpoint implementation, not scientific recovery eligibility at rung0.
The result reproduces the failure without B-frames; it does not attribute it
solely to decoder reordering. The proposed cap does not pad a short stream,
and the old validators still reject missing frames, shifted origins, gaps,
missing keyframes and duration violations.

See [protocol](PROTOCOL.md), [synthetic results](results/synthetic_v1/report.json)
and [verification](VERIFICATION.md). This is a small engineering matrix, not
all six rungs or all Wu sources, nor evidence of subjective QoE or successful
recovery. The earlier 29.97fps one-Hz sampling-phase caveat also remains.

## Reproduce without private inputs

From the repository root with its test dependencies:

```sh
python -m unittest wu_boundary.test_boundary -v
python -m wu_boundary.run
python -m wu_pipeline.spec
```

These commands verify published records and the unchanged original registration;
they do not encode or open private Wu media. The ledger can be checked on
Windows and Linux, but only the pinned WSL runtime performed the GPU encodes
and independent decode count. Reading that saved evidence on Windows is not
an independent hardware experiment.

The explicit `--audit-attempt PRIVATE_ATTEMPT_DIRECTORY` mode reads the retained
failed attempt; `--synthetic-output NEW_PRIVATE_DIRECTORY` generates the fixed
matrix. Publication directories are exclusive-create: both modes refuse to
overwrite these saved results. Retain a distinct versioned package for any
independent rerun. The runtime must match the original frozen record.

## Next boundary

A new real preparation attempt needs a versioned integration/registration of
the output cap, committed and pushed before execution. It must use a new
private output directory, retain this failed attempt, preserve all16clips and
previous exclusions, and rerun every original validation. Do not repair the
failed file in place, label this attempt complete, or change the manuscript
on the basis of these engineering results.
