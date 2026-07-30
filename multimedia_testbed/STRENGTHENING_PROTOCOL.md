# CREDO-360 objective multimedia strengthening protocol

Protocol frozen on 30 July 2026 before inspecting outcomes from the expanded
campaign.

## Claim boundary

This experiment evaluates objective viewport-quality fairness and controller
mechanics. It does not collect human ratings and will not be interpreted as
subjective QoE or perceptual superiority.

## Independent content and traces

- Six public QoEVAVE 8K equirectangular scenes: Badminton05, BuskingCity01,
  ConferenceCenter01, ForestWalk03, Lake01, and Skateboarding01.
- No-audio HMD trajectories with the deterministic subject-disjoint split
  already defined by the testbed.
- Only held-out `test` users enter campaign outcomes.
- Six NVENC H.264 representations using the declared CREDO-360 ladder.
- Measured VBR bytes for every content/representation/segment.
- Objective VW-PSNR and VW-SSIM computed at 1 fps on the declared 12x6
  spherical grid and 100x100-degree measured viewport.

## Paired campaign

- 30 paired seeds, five simultaneous users, and six 10-second segments.
- Stable, bursty, and capacity-shift regimes assigned cyclically.
- Identical content/user assignments and capacity profiles for every
  controller within seed.
- Exact equal processor-sharing completion from measured segment bytes.
- All null and adverse results are retained.

## Component ablation

The factors are calibrated lower bound (C), persistent deprivation debt (D),
and positive counterfactual opportunity gate (G). Six unique executable cells
are evaluated:

| Controller | C | D | G |
|---|---:|---:|---:|
| `mean_nash` | 0 | 0 | 0 |
| `conformal_nash` | 1 | 0 | 0 |
| `mean_debt_ungated` | 0 | 1 | 0 |
| `mean_debt_gated` | 0 | 1 | 1 |
| `conformal_debt_ungated` | 1 | 1 | 0 |
| `risk_debt` (CREDO-360) | 1 | 1 | 1 |

The two D=0/G=1 cells are algebraically identical to their D=0/G=0
counterparts because the gate multiplies only the debt term. They are declared
structural aliases and are not rerun under duplicate names.

Five planned ablation contrasts are evaluated over worst-user VW-PSNR,
worst-user VW-SSIM, and Jain fairness. Holm correction covers all 15 tests.

## Recent-method executable adaptations

- `fair_edge_nsw_proxy`: uncertainty-adjusted Nash social welfare aligned with
  the published FairEdge360 edge reward. This is an analytic objective proxy,
  not a reproduction of its trained MARL/GNN policy.
- `aci_nash`: per-user adaptive conformal alpha feedback with Nash welfare,
  aligned with recent adaptive-risk 360-degree streaming. It is not a
  reproduction of the single-user viewport transformer in Risk as a Resource.

CREDO-360 is compared with both adaptations over the five primary outcomes
below. Holm correction covers the ten adaptation-comparison tests.

## Primary CREDO-360 comparison

CREDO-360 versus conformal Nash is tested on exactly:

1. worst-user mean VW-PSNR (higher is better);
2. worst-user mean VW-SSIM (higher is better);
3. Jain fairness over per-user objective quality means (higher is better);
4. total stall (lower is better); and
5. representation-switch rate (lower is better).

Paired two-sided Wilcoxon signed-rank tests, Holm correction across these five
outcomes, 20,000-resample paired bootstrap confidence intervals, and
matched-pairs rank-biserial effects are reported.

## Audit

The campaign fails closed on duplicate rows, incomplete controller-seed pairs,
capacity/content/subject assignment mismatches, unexpected controllers,
incorrect seed count, or any calibration-trace leakage.
