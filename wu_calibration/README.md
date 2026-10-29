# Two-clip alignment calibration

The source texture direction is now supported by the author's projected
coordinates. A conservative sample adapter is implemented and tested, but
the sixteen reserved clips have **not** undergone pose qualification or any
quality/recovery experiment. No manuscript was changed.

## Declared split and chronology

The author approved reserving Experiment1/Video2 (skiing) and Experiment2/Video4
(basketball) for calibration. They were selected because the source paper
illustrates their projected directions, not because of recovery outcomes.
Amendment `64b6d5d` was published before calibration pose inspection. The other
sixteen clips remain registered for later content confirmation, eight per
condition. The same48 source identities recur; this is not person-independent.
The original all18-clip design and preceding source audit remain unchanged as
historical artifacts. The service contract is not relaxed.

The pinned author reference has1095 rows over0.055--361.036s, approximately3Hz,
not a row at every0.1s bucket. Before pose comparisons, `reference_alignment.json`
documented the source renderer's held-previous-bucket behavior. The five fixed
target times were retained, with actual reference times4.961,9.911,21.793,
39.948 and59.404s used for like-for-like coordinate comparison. No offset search
or interpolation was performed. Implementation `ec3269e` was committed before
the full calibration calculation and pushed after that first calculation.

## Coordinate result

Against48 author-rendered points at each of five fixed targets, using unordered
spherical minimum-sum matching:

| Candidate texture direction | Median error |95th percentile |Maximum |
|---|---:|---:|---:|
|`u=(-atan2(z,x)/(2*pi)) mod1` |0.02815deg |0.06173deg |0.32909deg |
|Opposite sign |22.21445deg |114.59515deg |166.77970deg |

Both prespecified first/last admissible-crossing rules give the same coordinate
comparison here. The negative sign passes the declared evidence gate; the
opposite sign does not. This reproduces the original source projection, not
a new method or independent human observation. The vertical mapping is
`v=acos(y)/pi`; existing angular-window coordinates are `yaw=360*u-180` and
`pitch=90-180*v`. Unit normalization is explicit, with maximum allowed
quaternion-norm error0.01; observed full-calibration maxima are below0.000844.

Private overlays of the two source frames were visually compared with paper
Figures7 and10. The negative-sign placement is consistent with the illustrated
landmarks/direction clusters. This qualitative check is not substituted for
the numeric author-reference comparison and does not establish exact HMD timing.
Source frames, raw coordinates and the author reference are not redistributed.

## Clock result and conservative response

All96 calibration logs have nondecreasing wall timestamps. Yet skiing contains
two admissible crossings of the first0.5s target for every identity. First versus
last occurrence can differ by38.043deg, so picking either silently is unsafe.
Basketball has one admissible crossing at every required target. Some backward
playback steps do not cross a required target; they are retained, not sorted out.

The post-calibration adapter strengthens the rule further: count **all**
ascending crossings before applying the0.1s sample-age limit. Require exactly
one crossing for every0.5,1.5,...,59.5s target, an initial bracket and coverage
through60s. An old out-of-age repeated crossing is still an ambiguity. No partial
pose series is returned for missing, stale or ambiguous samples.

| Calibration clip |Accepted traces |Rejected traces |Reason |
|---|---:|---:|---|
|e1v02, free exploration |0/48 |48/48 |Repeated first-target crossing |
|e2v04, content-focused |48/48 |0/48 |All required crossings unique and timely |

This is source-sample qualification, **not recovery success/failure**. Independent
scalar loops agree on5760 target checks. Independent quaternion multiplication
and scalar tile-weight calculations agree for all2880 accepted samples, using
the unchanged12x6,100x100degree angular viewport and cosine-latitude weighting.

The rule defines a uniquely bracketed recorded pose; it does not prove which
image a historical headset displayed. The nonzero media origins previously
found in two reserved clips remain unresolved and ineligible under the original
strict source-timing gate; they are not normalized using another clip's evidence.

## Reproduction

Offline tests and public scalar-artifact checks:

```sh
python -m unittest wu_calibration.test_core wu_calibration.test_adapter wu_calibration.test_validation -v
python -m wu_calibration.run --verify
python -m wu_calibration.check_adapter --verify
python -m wu_calibration.replication --verify
```

Private derivation with the exact original archive and author reference:

```sh
python -m wu_calibration.fetch_reference --private-dir /new/private/reference
python -m wu_calibration.run --archive /private/vr-dataset.zip --reference /new/private/reference/author_video_3.csv --output /new/private/calibration
python -m wu_calibration.check_adapter --archive /private/vr-dataset.zip --output /new/private/adapter-check
```

Clip guards refuse all sixteen reserved pose files before opening an archive
member. Synthetic tests cover missing/duplicate/stale crossings, wall-clock
errors, normalization, spherical seam handling, independent assignment and
scope preservation. Files and failed checks are retained; no automatic outcome
launcher is present. See [verification](VERIFICATION.md) for platform details.

## Next gate

Freeze and publish this conservative adapter specification, then qualify the
sixteen registered clips using fixed clock/media rules, preserving every
exclusion and condition. Any later pose decoding must follow that frozen rule,
check quaternion validity and preserve raw provenance before quality labels.
No recovery-dependent repair, clip replacement or change of the original
quality/deadline/resource contract is permitted. Full source qualification
and the external confirmation experiment remain unperformed here.

## References

Wu et al., *A Dataset for Exploring User Behaviors in VR Spherical Video
Streaming*, MMSys2017, DOI[10.1145/3083187.3083210](https://doi.org/10.1145/3083187.3083210),
Sections2.4 and3.1, Figures5,7--12. [Author dataset and visualization](https://wuchlei-thu.github.io/).
Reference source commit`6ea44d0e2193679cd00d6f02850f3f9cd16ffbd1`,
`video/video_3.csv`, Git blob`65349d06cf9b511b82c3c8d19083ed76f88161ae`;
renderer`js/my_plot.js`, blob`45fd0e42d491e12cd60563d6ef0d8a2c4652d655`.
No third-party source code, raw traces, paper or source images are republished.
