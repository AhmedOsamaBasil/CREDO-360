# Metric and service-contract findings

## Decision

**Recovery feasibility and policy ranking are materially dependent on the
chosen quality account. The old bounded-index result cannot be promoted to a
metric-independent compensation claim.** This is useful diagnostic evidence,
not a new successful recovery controller or a journal-readiness declaration.

The protocol and tested methods were committed and pushed as `5178cd8` before
the complete batch. We rescored 64,512 fixed-path/grid rows and evaluated 8,064
future-known bound/grid rows, each with four repayment targets. These reuse
168 directed episodes, six scenes and 28 participant identifiers; they are not
that many independent trials or people. No controller was tuned, no metric was
chosen as a new primary after seeing outcomes, and no fresh holdout was used.

## 1. The metric changes the feasible compensation target

For the original rung-0 impairment and four recovery segments, with the same
1.5 MB per-round actual-file cap and fixed total extra-byte reserve:

| Quality account | Offline half-repayment /168 | Mean unpaid fraction |
|---|---:|---:|
| Original rounded, clipped index | 96 | 0.344994 |
| Finer-resolution clipped index | 96 | 0.344985 |
| Unclipped viewport PSNR | 168 | 0.149323 |
| Weighted distortion reduction, using negative MSE | 28 | 0.716699 |

These are four different engineering objectives. None is a human QoE measure.
PSNR differences are logarithmic; distortion differences operate on squared
pixel error. Equal fractional repayment on these scales does not mean the same
physical improvement or perceived compensation. The original clipping suppresses
gains beyond the index ceiling, while MSE discounts the absolute distortion
reduction available when quality is already high.

Finer rounding alone barely changes aggregate repayment. A separately labeled
post-hoc check intersects all four native floor-admissible path sets: the same
96/96/168/28 half-repayment counts and mean unpaid values remain. Thus the
large difference is not merely an artifact of allowing different unsafe paths.
The original rounded metric has extra admissible paths in 52 episodes, but
those paths do not change this particular optimum. Full witnesses remain public.

## 2. A policy ranking can reverse without any changed action

The fixed primary prefix planner versus fixed prefix cost-greedy:

| Account | Primary mean unpaid | Cost-greedy mean unpaid | Primary minus cost-greedy |
|---|---:|---:|---:|
| Original index | 0.375974 | 0.369185 | +0.006789 |
| Fine index | 0.375966 | 0.369166 | +0.006800 |
| PSNR | 0.198956 | 0.207459 | -0.008503 |
| Distortion | 0.772375 | 0.754092 | +0.018283 |

Lower unpaid is better. The pooled PSNR ranking reverses, but it is not uniform:
primary-minus-cost-greedy is -0.018025 in v2 and +0.001019 in v3. Under distortion
the primary is worse in both cohorts, and its half-repayment count is 13/168
versus 14/168 for cost-greedy. Plain prefix-greedy has lower distortion unpaid
(0.738295) than either, but also incurs native-scale floor violations. The
complete report includes all eight policies; none is declared a universal winner.

These are **rescored paths optimized originally for the bounded index**, not
newly optimized PSNR/MSE controllers. The result does not establish which
algorithm would win if every controller were redesigned for a different goal.
The waiting variant's lower PSNR unpaid does not erase its previously measured
in-simulation waiting/stall cost. The old progression failure remains unchanged.

## 3. Severity, target and deadline are part of the claim

Changing the initial-loss account to the milder rung-1 impairment raises the
four-segment offline half-repayment count to 168/168 on every scale. This is a
counterfactual initial-account sensitivity, not a new run in which controllers
experienced a different event. Lowering severity after seeing a failure would
not rescue the original claim.

Under the original impairment and index, future-known counts reaching
25/50/75/100% repayment are 164/96/56/56. The corresponding distortion counts
are 56/28/14/2. The target fraction is therefore consequential, not an arbitrary
label that can be changed without changing the research question.

Completion of H segments is not a guarantee by wall time 10H:

| Original impairment | Eventual two-segment half count | Half count by 20 s | Eventual four-segment half count | Half count by 40 s |
|---|---:|---:|---:|---:|
| Index | 62 | 28 | 96 | 96 |
| PSNR | 109 | 43 | 168 | 168 |
| Distortion | 27 | 0 | 28 | 27 |

The deadline contract counts only fully played recipient segments. It does not
estimate partial-segment quality from a segment-average label. With cold buffers
and a nominal ten-second first segment, no segment can finish within ten seconds
when download time is positive: the H=1 deadline zero is an expected boundary
case, not a new scheduling discovery. Four-segment index half counts coincide,
but mean unpaid still rises from 0.344994 to 0.347907 under the 40 s deadline.
The fixed four-slot reserve is held constant across horizons; no extra resources
are silently introduced for a longer deadline.

## 4. Precision affects strict floor language

The fixed primary path has one original-index recipient-floor violation and
zero donor violations. Finer PSNR accounting exposes 25 small losses: 23 donor
and two recipient segment events. Of these, 24 were hidden by the original
rounded/clipped account. Maximum loss is 0.002967 dB and median 0.000309 dB.
These magnitudes do not establish meaningful perceptual harm. They do show
that an exact zero-loss assertion depends on scale and precision; an engineering
tolerance must be justified and declared, not fitted afterward to eliminate
violations. Offline strict bounds use the actual selected scale's floors.

## Validation and limits

- Original 1,344 saved policy scores and 168 strict offline bounds reproduced.
- 5,376 saved decision clocks reproduced using exact integer ticks, retaining
  all waits and starts. No timestamps or choices were rewritten.
- 4,032 independent scalar metric/horizon/clock enumerations and 32,256
  target/minimum-cost witness checks pass. Positive affine invariance is checked
  on 1,463,616 path/metric appearances; these are not independent experiments.
- Complete Windows and WSL scientific replay agrees on SHA256
  `479f9d67fe6bee493728ef5889c65aae5292c2091b4c74b67aa23ad62b5d02fe`.
- The common-floor, ranking and floor-magnitude diagnostics are post-hoc and
  separately hashed. Their reporting-only build failure is recorded in
  [MEASUREMENT_NOTES.md](MEASUREMENT_NOTES.md); no frozen scientific method changed.

All metrics inherit the old compressed reference, coarse spatial/temporal
sampling and pose alignment. MSE is reconstructed from stored segment PSNR,
not a new pixel measurement. Segment duration is nominal ten seconds, including
the known River01 final partial segment; no decoder, renderer, HMD or new network
measurement was added. The offline result knows future viewport quality and
cannot be advertised as a causal admission guarantee. Pair/horizon scale is
unchanged; no larger-population generalization follows.

## Recommended next step

Define the engineering service objective before any further controller or
holdout evaluation. Distortion-reduction integrated over actually played time
is a plausible additive account, with unclipped PSNR and fairness reported
separately, but it is not automatically the correct user-experience objective.
Its poor feasibility here must not be hidden by selecting the favorable PSNR
account. An operational choice needs a stated reason independent of which
method wins.

Then test actual-duration, segment-timescale and player-aligned feedback under
that locked contract on exposed data. Retain the original index as a historical
comparison and preserve all adverse results. The robust conclusion available
now is **contract-dependent feasibility and timing**, not restored controller
superiority, metric-invariant recovery or human QoE fairness.
