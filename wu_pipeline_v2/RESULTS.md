# Completed Wu v2 offline preparation

The first v2 attempt completed all registered preparation and validation steps.
Method commit 95a143e was published before execution. The subsequent independent
scalar checker was published as c39ed46 before it was applied to these labels.
Neither changed the frozen scientific plan or the running preparation method.
The failed v1 attempt remains preserved and is not counted as a successful run.

## Complete census

All 16 registered clips are retained: 10 eligible clips were prepared and six
retain their original exclusions. The complete artifact contains 60 renditions,
360 ten-second parents, 800 two-second recovery children and 452 clip-trace label
records, corresponding to the 452 original directed pairs. Each rendition has
1,800 contiguous 30-fps frames over 60 s and passes the original timestamp,
keyframe, container-duration and decode checks. Parent/child compressed-packet
and decoded-frame identity checks pass. All 1,220 rendition, parent and child files were independently
hash-checked on Windows and Linux; both audit reports have the same digest.

| Viewing condition | Eligible clips | Clip-trace records / directed pairs |
|---|---:|---:|
| Free exploration | 5 | 216 |
| Content-focused memory test | 5 | 236 |

These are repeated recordings of the source cohort, not 452 independent people.
Conditions are not pooled as exchangeable samples or interpreted as a causal
comparison. The two earlier calibration clips are not confirmation clips.

Original exclusions remain e1v07, e1v08, e1v09 and e2v05 for insufficient qualified
two-user clock rosters, and e2v02 and e2v09 for nonzero media origin. No original
source was shifted, repaired or replaced to change eligibility. No validation
threshold, rounding rule, metric, resource allowance or service deadline was
relaxed. No automatic retry occurred within this v2 attempt.

## Independent numerical replay

The public export includes original derived tile-MSE arrays and offline labels,
not videos, images, raw participant poses, demographics or private timestamps.
The primary audit checks their hashes, shapes, integer conversion and roster.
Its report explicitly does not claim a separate pose reaggregation; that check
is recorded in the two additional scalar-replay reports.

On both Windows and Linux, the independent Hamilton-product pose projection,
scalar angular-window weights and compensated scalar aggregation reproduce all
97,632 parent/child label values across 452 traces with **zero micro-MSE integer
disagreements**. Maximum native-MSE difference is 1.1368683772161603e-13 on
each platform, below the unchanged 1e-9 check. Both platform reports are retained;
their hashes differ because they record platform/runtime-specific evidence.
This is reaggregation of the same measurements, not another hardware encode,
independent cohort, replication of a physical display or recovery experiment.

## Retained sampling-phase caveat

The original-source 1-fps sampler and 30-fps-to-1-fps cascade differ on the
following numbers of one-second samples. All differences are retained, without
changing the primary sampler or selecting clips by this diagnostic.

| Clip | Trace records | Different sample bins out of 60 |
|---|---:|---:|
| e1v01 | 27 | 26 |
| e1v03 | 47 | 0 |
| e1v04 | 48 | 26 |
| e1v05 | 46 | 26 |
| e1v06 | 48 | 25 |
| e2v01 | 46 | 26 |
| e2v03 | 48 | 0 |
| e2v06 | 47 | 26 |
| e2v07 | 48 | 0 |
| e2v08 | 47 | 0 |

Native MSE therefore includes spatial resizing, temporal resampling and
compression. It is not guaranteed same-source-frame compression error or
human-perceived quality. The existing angular-window tile model is preserved,
not replaced with a rendered perspective viewport. Equal pixel hashes alone
also do not prove identical source-frame identity in static content.

## Artifact bindings and verification

- V2 registration: f152b6fc38cb70447d87389e508dcc4946fea8a365b9c1b01fd0c72dece59717
- Complete manifest: fe9e5ae6ef81180b0a910af06b8299f3bf0bdaae1ea34902765146df4b1a72ea
- Complete audit: 235f7db5cc012bef307e79ba8b026ae3b27281f5eb36dcccb72e1c2aff04f87d
- Windows scalar replay: b26ae82e23a81190b0ea5f0a5318c5769a284449be6ede8b5a86646999f35439
- Linux scalar replay: 0f04b763bc2f7d8ad493ea6967d15ace2f9efebfac3eaedf4ad8107d6c1d1909

Full software regressions pass 929 tests plus 89 subtests on Windows and 925 plus 89
on Linux; four legacy Torch tests are covered on Windows. These counts are
software checks, not scientific replications. Both method 95a143e and auxiliary
checker c39ed46 have verified successful remote CI runs. This results commit's
workflow status is separate.

Verify without opening private media or poses:

```sh
python -m wu_pipeline_v2.spec
python -m wu_pipeline_v2.audit --output wu_pipeline_v2/results/attempt_01
python -m wu_pipeline_v2.replay --export wu_pipeline_v2/results/attempt_01 --output wu_pipeline_v2/results/replay_windows_v1
python -m wu_pipeline_v2.replay --export wu_pipeline_v2/results/attempt_01 --output wu_pipeline_v2/results/replay_linux_v1
```

This establishes a complete audited offline measurement artifact under the
unchanged contract. It does **not** establish that the 50% recovery target is
feasible, that a controller outperforms Nash/max-min, or that subjective QoE
improves. A subsequent frozen feasibility/controller evaluation must preserve
the causal information boundary. These derived labels are now exposed; later
method tuning cannot reuse them while claiming they remain an unseen holdout.
No manuscript or acknowledgment was changed.
