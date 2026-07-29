# Experiment C: independent multimedia generalization

## Purpose

Experiment C tests whether the controller-side fairness effect survives a
change from the original Big Buck Bunny DASH asset to independently sourced
360-degree content and measured HMD viewport trajectories. It is an objective
multimedia validation, not a new subjective study.

## Independent data

The source is the public QoEVAVE Saliency Dataset associated with:

> A. Singla, T. Robotham, W. Menz, A. Raake, and E. A. P. Habets,
> "Saliency of Omnidirectional Videos with Different Audio Presentations:
> Analyses and Dataset," QoMEX 2023,
> doi: `10.1109/QoMEX58391.2023.10178588`.

The frozen test uses the no-audio traces for Badminton05, ForestWalk03, and
Skateboarding01. Each sequence has 28 HMD users. A deterministic hash assigns
9 users to calibration and 19 to held-out test; only test users enter the
campaign outcomes. Third-party video and traces are downloaded locally and
are not redistributed.

| Content | P.910-style SI | P.910-style TI | Relative rank |
|---|---:|---:|---|
| Skateboarding01 | 71.39 | 4.00 | low |
| Badminton05 | 100.70 | 4.09 | medium |
| ForestWalk03 | 98.78 | 18.82 | high |

The low/medium/high labels are empirical ranks over the declared set using
standardized SI plus TI; they were not assigned from content names.

## Media and transport pipeline

- Original source: 7680x3840, 60 fps equirectangular video.
- Representations: 1920x960 H.264 NVENC at the six CREDO-360 ladder targets.
- Segment duration: 10 s; actual encoded VBR bytes are measured per segment.
- Distortion analysis: 960x480 luma at 1 frame/s on a 12x6 grid.
- Viewport: 100x100 degrees centered on measured HMD yaw/pitch, with spherical
  tile-area weighting.
- Outcome: viewport-weighted luma PSNR (VW-PSNR).
- Transport: exact equal processor sharing for simultaneous flows using the
  measured segment sizes and frozen shared-capacity schedules.
- Campaign: 30 paired seeds, five users, six segments, and
  stable/bursty/shift regimes.
- Controllers: conformal Nash, ungated resource debt, and CREDO-360.

The declared 1--5 viewport-quality index is
`1 + 4*clip((VW-PSNR - 18)/24, 0, 1)`. It is used for debt and Jain-fairness
accounting and is not a MOS mapping.

## Audit

The audit passes:

- 2,700 raw rows;
- 30 complete seeds and 90 controller--seed pairs;
- no duplicate or incomplete cells;
- no content, trace, regime, or capacity mismatch within paired observations;
  and
- only held-out test traces in campaign outcomes.

## Prespecified result

CREDO-360 is compared with conformal Nash using paired two-sided Wilcoxon
tests, Holm correction over exactly four primary outcomes, 20,000-resample
paired-bootstrap confidence intervals, and matched-pairs rank-biserial
effects.

| Primary outcome | CREDO-360 | Conformal Nash | Delta [95% CI] | Holm p | Rank-biserial |
|---|---:|---:|---:|---:|---:|
| Worst-user VW-PSNR (dB) | 26.7549 | 26.2718 | +0.4831 [0.2700, 0.7027] | 0.000601 | +0.801 |
| Jain fairness over per-user mean quality | 0.963905 | 0.955758 | +0.008147 [0.004680, 0.012007] | 0.000519 | +0.828 |
| Total stall (s) | 5.3562 | 5.3562 | 0.0000 [0.0000, 0.0000] | 1.000 | 0.000 |
| Representation-switch rate | 0.6311 | 0.6067 | +0.0244 [-0.0178, 0.0656] | 0.476 | +0.260 |

The evidence supports improved worst-user viewport quality and inter-user
fairness on the declared independent testbed. It does not support a stall or
switching improvement.

## Heterogeneity and claim boundary

The secondary content-stratified mean VW-PSNR differences are heterogeneous:
`-0.157 dB` for Badminton05 (interval crosses zero), `+0.525 dB` for
ForestWalk03, and `-0.649 dB` for Skateboarding01. Therefore the result is a
worst-user/fairness effect, not a claim that CREDO-360 improves mean quality
for every content.

The video-quality metric is objective, downsampled, and temporally sampled.
The viewport is approximated on a coarse grid, and transport is a deterministic
fluid replay rather than the Mininet testbed. No new participant viewed
compressed or stalled representations. Human/headset validation remains
required for perceptual generalization.

## Reproduction

See `multimedia_testbed/README.md`. The committed artifact contains source
URLs, hashes, split assignments, measured segment sizes, derived viewport
outcomes, raw paired campaign rows, audits, statistical tables, and figures.
