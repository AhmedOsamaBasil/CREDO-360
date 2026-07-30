# Experiment C: objective viewport-quality fairness

## Claim boundary

Experiment C evaluates objective viewport quality and controller mechanics. It
is not a subjective study, does not estimate MOS, and does not establish human
QoE or perceptual superiority. The quality index used by the controller is a
declared normalization of objective viewport quality.

The frozen protocol predates inspection of the strengthened campaign outcomes
and is committed as `multimedia_testbed/STRENGTHENING_PROTOCOL.md`.

## Independent public data

The source is the public QoEVAVE Saliency Dataset associated with:

> A. Singla, T. Robotham, W. Menz, A. Raake, and E. A. P. Habets,
> "Saliency of Omnidirectional Videos with Different Audio Presentations:
> Analyses and Dataset," QoMEX 2023,
> doi: `10.1109/QoMEX58391.2023.10178588`.

Six no-audio sequences cover balanced low, medium, and high empirical
complexity ranks: Badminton05, BuskingCity01, ConferenceCenter01,
ForestWalk03, Lake01, and Skateboarding01. Each sequence has 28 HMD traces. A
deterministic content-specific hash assigns 9 traces to calibration and 19 to
held-out testing; only test traces enter campaign outcomes. Third-party video
and traces are downloaded locally and are not redistributed.

| Content | P.910-style SI | P.910-style TI | Rank |
|---|---:|---:|---|
| BuskingCity01 | 37.95 | 6.87 | low |
| Lake01 | 45.74 | 6.12 | low |
| ConferenceCenter01 | 66.93 | 3.86 | medium |
| Skateboarding01 | 71.39 | 4.00 | medium |
| Badminton05 | 100.70 | 4.09 | high |
| ForestWalk03 | 98.78 | 18.82 | high |

## Media, metrics, and campaign

- Original media: 7680x3840, 60 fps equirectangular video.
- Representations: 1920x960 H.264 NVENC at six ladder targets; actual VBR
  segment bytes are measured.
- Objective analysis: 960x480 luma at 1 frame/s on a 12x6 grid.
- Viewport: 100x100 degrees centered on measured HMD yaw/pitch, with spherical
  tile-area weighting.
- Quality metrics: viewport-weighted PSNR and viewport-weighted SSIM.
- Transport: exact equal processor sharing using measured segment sizes and
  frozen shared-capacity schedules.
- Campaign: 30 paired seeds, five users, six segments, and
  stable/bursty/shift regimes.
- Controllers: eight total, including the six unique estimable
  calibration/debt/gate cells, conformal Nash, CREDO-360, and two recent-method
  adaptations.

The declared 1--5 controller index is
`1 + 4*clip((VW-PSNR - 18)/24, 0, 1)`. It is used for deprivation and Jain
fairness accounting and is not a MOS mapping.

## Audit and inference

The audit passes: 7,200 rows, 30 complete paired seeds, eight expected
controllers, no duplicate or incomplete cells, identical paired plans, and
held-out traces only. Primary inference uses paired two-sided Wilcoxon tests,
20,000-resample paired-bootstrap intervals, and Holm correction over exactly
five outcomes.

| Primary outcome | CREDO-360 | Conformal Nash | Delta [95% CI] | Holm p |
|---|---:|---:|---:|---:|
| Worst-user VW-PSNR (dB) | 28.6132 | 27.4343 | +1.1789 [0.8093, 1.5701] | 2.05e-5 |
| Worst-user VW-SSIM | 0.925574 | 0.907610 | +0.017964 [0.011618, 0.024877] | 2.75e-5 |
| Jain viewport-quality fairness | 0.966396 | 0.955828 | +0.010568 [0.007153, 0.014303] | 1.66e-5 |
| Total stall (s) | 6.0902 | 6.0902 | 0.0000 [0.0000, 0.0000] | 1.000 |
| Representation-switch rate | 0.5944 | 0.6056 | -0.0111 [-0.0456, 0.0244] | 0.836 |

The evidence supports a worst-user objective viewport-quality and inter-user
fairness effect. It does not support a stall or switching benefit.

## Component identification

The six unique factorial cells isolate calibration, persistent deprivation
debt, and the opportunity gate. The two gate-on/debt-off settings are omitted
because the gate cannot change an action when no debt recovery is requested.
Holm correction covers all 15 declared ablation tests.

Adding debt to calibrated Nash produces the entire primary quality effect:
+1.1789 dB VW-PSNR, +0.017964 VW-SSIM, and +0.010568 Jain fairness (all
Holm-adjusted p below 1.2e-4). Calibration without debt is not significant.
The opportunity gate is exactly action-equivalent to ungated debt in this
capacity-only multimedia replay. Therefore Experiment C identifies debt as the
active fairness mechanism; it does not independently validate the gate. Gate
mechanics are identified only in the separate non-actionable service-ceiling
condition.

## Recent-method adaptations

The testbed includes two executable, objective-aligned adaptations:

1. an uncertainty-adjusted Nash proxy motivated by FairEdge360; and
2. an adaptive-conformal Nash proxy motivated by recent conformal
   viewport-risk control.

They are not presented as exact reproductions of the original systems. Against
the FairEdge-style proxy, CREDO-360 improves worst-user VW-PSNR by 1.1968 dB,
VW-SSIM by 0.018531, and Jain fairness by 0.010699. Against adaptive-conformal
Nash, the corresponding improvements are 1.1789 dB, 0.017964, and 0.010568.
All six quality/fairness contrasts remain significant under their prespecified
ten-test Holm family; stall ties and switching differences are nonsignificant.

## Heterogeneity and limitations

Mean content effects are heterogeneous: CREDO-360 improves mean quality for
Badminton05 and ForestWalk03 but reduces it for the other four contents. The
claim is therefore limited to worst-user quality and inter-user fairness, not
universal mean-quality improvement.

The campaign uses one public dataset, no audio, a coarse viewport grid,
temporal subsampling, and deterministic fluid transport. No participant viewed
the compressed or stalled representations. Human/headset validation would be
required before making subjective perceptual or QoE claims.

## Reproduction

See `multimedia_testbed/README.md`. The committed package contains source URLs
and hashes, 168 trace assignments, 216 measured segment sizes, 6,048 derived
viewport observations, 7,200 paired campaign rows, audit files, tests,
statistical tables, and publication figures.
