# Qualified Wu sampled-pose adapter

All 452 metadata-qualified trace files pass selected-quaternion and independent
geometry validation: 27,120 samples across ten clips. No new source exclusions
were needed. All 452 original directed candidate pairs remain usable for the
next engineering stage. **This is not a quality or recovery-performance result.**

The method was committed and published as `88c0616` before reserved-pose access.
It binds the [qualified metadata roster](../wu_qualification/README.md), the
calibrated negative texture direction and the original source files. The
norm limit, sample-clock rule, strict media origins and service contract are
unchanged. [PROTOCOL.md](PROTOCOL.md) is the frozen specification.

## What was validated

The complete private trace archive and sixteen registered original videos were
size/hash-checked again. Only the 452 metadata-qualified trace members were read
for selected poses. Their member hashes, full original clock evidence and
selected-row digests were checked against the preceding roster. The other 316
registered trace files retain their earlier exclusions without pose inspection.

For each eligible trace, only sixty xyzw quaternions at the frozen selected rows
were converted. Every selected sample was numeric, finite, nonzero and within
the unchanged 0.01 norm-error limit. The largest observed absolute norm error
was approximately 0.000778697. Samples were explicitly normalized, not repaired
by replacing, interpolating or smoothing invalid values.

Forward-vector rotation and calibrated texture coordinates were checked against
independent scalar Hamilton multiplication. Legacy angular-window viewport
weights were checked against a separate scalar implementation, including exact
nonzero tile membership. This verifies the existing 6-by-12 angular approximation,
not fractional perspective overlap, image quality or physical display timing.

| Viewing condition | Registered clips | Clips with usable pairs | Selected samples | Original usable pairs |
|---|---:|---:|---:|---:|
| Free exploration | 8 | 5 | 12,960 | 216 |
| Content-focused/memory-test | 8 | 5 | 14,160 | 236 |

All sixteen clips, 768 source-ID records and 452 original pairs remain in the
accounting. The four clips with no clock-qualified IDs and two nonzero-origin
media exclusions are unchanged. No identity was substituted and no cycle was
rebuilt. The same 48 original identities recur; neither pairs nor samples are
independent participants. The conditions remain separate and eligibility may
favor cleaner recordings.

## Reproduce

From the software repository root, with its Python numerical dependencies:

```sh
python -m unittest wu_pose.test_core wu_pose.test_validation -v
python -m wu_pose.run --verify
python -m wu_pose.run --verify --output wu_pose/results/linux_v1
python -m wu_pose.replication --verify
```

These public checks verify method/source bindings, published aggregate checks,
scope, all exclusions and original pair accounting. Recomputing the actual
geometry requires the exact private author-linked originals:

```sh
python -m wu_pose.run --private-dir /path/to/original-assets --output /path/to/new-result
python -m wu_pose.run --verify --output /path/to/new-result
```

The private directory has `vr-dataset.zip` and the sixteen original clip MP4s.
Existing output directories are refused. A failed input/clock/independent check
halts the batch and retains a sanitized failure artifact and completed progress.
Invalid selected quaternions are accounted for per trace; their original pairs
would remain recorded as unusable rather than being replaced. Synthetic tests
exercise this path even though no actual selected quaternion failed.

## Reproduction and interpretation limits

Windows and Linux agree on all discrete outcomes, source identities and pair
rosters. Their full reports are not bit-identical: 122 floating summaries differ,
by at most 2.85e-14 in their respective units. Both reports and an executable
comparison are published; no numerical rounding hides the discrepancy.
[VERIFICATION.md](VERIFICATION.md) records hashes and test results.

This release validates selected sampled poses only. Unselected quaternion rows,
positions and demographics were not interpreted. Raw media, traces, calendar
timestamps and actual converted yaw/pitch series are not published. Both systems
reuse the earlier sequential PTS audit rather than performing independent media
decodes or physical-HMD measurements.

The state is `sampled_pose_validation_complete`, while `full_experiment_ready`
and automatic outcome launch remain false. The next stage must bind this adapter
and fixed roster into the encoding/measurement pipeline before new quality or
recovery outcomes. Earlier negative recovery evidence is unchanged. There is no
new perceptual claim, manuscript modification or journal submission here.
