# CREDO-360 novelty assessment

Working name: **CREDO-360 — Coverage-calibrated Risk and Experiential
Deprivation-aware Optimization for multi-user 360-degree streaming.**

## Claims the review invalidates

The following broad claims are not defensible:

- “First uncertainty-aware fair multi-user 360-degree streaming system.”
  FairEdge360 (2026) already combines multi-user 360-degree streaming,
  uncertainty-aware edge coordination, Nash social welfare, and Jain fairness.
- “First conformal prediction method for 360-degree streaming.” Risk as a
  Resource (NOSSDAV 2026) already uses split/adaptive conformal prediction,
  personalization, and an online alpha risk controller. Meaning over Motion
  (2026 preprint) also uses conformal viewport sets.
- “First risk-adaptive uncertainty-aware 360-degree controller.” DK-MARC
  (MMSys 2026) is direct prior art.
- “First network-wide QoE-fair streaming controller.” QFF, FINEAS, UFair,
  FESTIVE, Q2oE, and related work predate this project.
- “First temporal/virtual debt queue for video QoE.” QoE-aware D2D allocation
  (Zhu et al., IEEE Network 2015) uses per-user virtual queues for long-term
  playback fluency, and later Lyapunov streaming systems use virtual queues for
  delay, compute, or fairness constraints.

## Narrow claim that currently survives

> To the best of our knowledge, among the studies retrieved by the documented
> search, verification, and snowballing protocol, no prior system jointly
> inserts online coverage-calibrated **QoE lower bounds** into a shared-link
> multi-user immersive allocation loop and maintains explicit per-user
> **temporal QoE-deprivation debt** that carries unmet service obligations
> across decision epochs, while spending that debt only on actions with a
> positive calibrated counterfactual QoE opportunity.

This is a qualified novelty claim, not an absolute proof of absence. The wording
must remain “to the best of our knowledge” even after the review is complete.

## Closest-work matrix

| Work | Multi-user 360 | QoE fairness | Calibrated uncertainty | Persistent deprivation state | Remaining difference |
|---|---:|---:|---:|---:|---|
| FairEdge360 (2026) | Yes | NSW and Jain | Learned uncertainty; ECE evaluation | Not identified | Its paper explicitly lists conformal guarantees as future work. |
| Risk as a Resource (2026) | No | No shared-link fairness | Split/adaptive conformal viewport sets | Not identified | Personalized single-user viewport risk rather than calibrated QoE fairness. |
| DK-MARC (2026) | No shared multi-user setting identified | No | Dual uncertainty/risk adaptation | Not identified | No carried cross-user QoE obligation. |
| QFF / FINEAS / UFair / Q2oE | Multi-client video | Yes | Point-valued QoE utilities | No conformal debt coupling identified | No coverage-controlled QoE lower bound. |
| Adaptive Conformal Inference | Not a media system | No | Long-run coverage under its stated assumptions | No | Supplies calibration machinery, not resource fairness. |
| QoE fairness index | General QoE | Snapshot metric | No | Explicitly time-scale independent | Measures dispersion but not accumulated individual deprivation. |
| QoE-aware D2D allocation (2015) | Multi-user D2D video | Long-term fluency constraint | No calibrated predictive uncertainty | Per-user virtual playback queue | Queue stabilizes playback time; no calibrated QoE counterfactual or opportunity-gated debt. |

## Technical contribution to develop

1. **Calibrated QoE floor.** A deep ensemble predicts QoE, while conformal
   residual calibration converts its output into an auditable lower bound.
   Coverage and interval width are first-class metrics.
2. **QoE-deprivation debt.** Each user carries a decayed deficit when realized
   QoE falls below a service floor. The next allocation weights that user’s
   calibrated lower-bound utility.
3. **Risk-aware shared-link allocation.** At each epoch, select a feasible
   bitrate vector by maximizing debt-weighted Nash utility of calibrated QoE
   floors, with a switching penalty.
4. **Shift audit.** Evaluate pre/post distribution-shift coverage, lower-tail
   QoE, worst-user QoE, group gap, rebuffering, and switching—not mean QoE
   alone.

## Evidence checked directly

- The full FairEdge360 PDF was rendered and searched. It reports ECE = 0.041,
  contains no identified debt/deprivation/virtual-queue mechanism, and names
  conformal prediction as future work.
- The full Adaptive Conformal Inference paper was inspected. Its guarantee is
  long-run empirical coverage under the stated update, not unconditional
  per-time marginal coverage under arbitrary shift.
- Risk as a Resource was verified bibliographically at DOI
  `10.1145/3798065.3798085`; its full text was not openly accessible during
  this review. Claims about it are therefore limited to abstract-level evidence.

## Remaining novelty audit before submission

1. Obtain and inspect the full Risk as a Resource and DK-MARC papers.
2. Complete backward/forward snowballing from those papers and FairEdge360.
3. Finish IEEE/ACM screening for `deficit`, `virtual queue`, `minimum service`,
   `starvation`, `long-term fairness`, and `risk-sensitive utility`.
4. Match every calibration statement to the exact implemented update and its
   assumptions.
5. Increase paired experimental replications and validate on at least one
   independent immersive dataset or live emulated shared link.
