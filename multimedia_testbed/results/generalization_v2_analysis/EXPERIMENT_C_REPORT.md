# Experiment C: independent multimedia generalization

## Validation

- Audit: **PASS**
- Raw paired rows: 7,200
- Seeds: 30
- Outcomes: objective viewport-weighted luma PSNR and SSIM; not subjective MOS.

## Content complexity

| Content | SI | TI | Relative rank | Held-out users |
|---|---:|---:|---|---:|
| Badminton05 | 100.70 | 4.09 | high | 19 |
| BuskingCity01 | 37.95 | 6.87 | low | 19 |
| ConferenceCenter01 | 66.93 | 3.86 | medium | 19 |
| ForestWalk03 | 98.78 | 18.82 | high | 19 |
| Lake01 | 45.74 | 6.12 | low | 19 |
| Skateboarding01 | 71.39 | 4.00 | medium | 19 |

## Prespecified CREDO-360 versus conformal Nash tests

| Outcome | CREDO | Baseline | Delta [95% CI] | Holm p | Rank-biserial |
|---|---:|---:|---:|---:|---:|
| Worst-user VW-PSNR (dB) | 28.61321 | 27.43428 | +1.17893 [+0.80935, +1.57014] | 2.053e-05 | +0.974 |
| Worst-user VW-SSIM | 0.92557 | 0.90761 | +0.01796 [+0.01162, +0.02488] | 2.752e-05 | +0.958 |
| Jain viewport-quality fairness | 0.96640 | 0.95583 | +0.01057 [+0.00715, +0.01430] | 1.662e-05 | +0.985 |
| Total stall (s) | 6.09020 | 6.09020 | +0.00000 [+0.00000, +0.00000] | 1 | +0.000 |
| Representation-switch rate | 0.59444 | 0.60556 | -0.01111 [-0.04556, +0.02444] | 0.8358 | -0.156 |

## Component ablation

The six estimable calibration/debt/gate cells are executable. The two gate-on/debt-off cells are algebraically identical to their gate-off counterparts and are therefore structural aliases.

| Contrast | Outcome | Delta [95% CI] | Holm p |
|---|---|---:|---:|
| calibration_without_debt | Worst-user VW-PSNR (dB) | +0.02327 [+0.00000, +0.06980] | 1 |
| calibration_without_debt | Worst-user VW-SSIM | +0.00044 [+0.00000, +0.00132] | 1 |
| calibration_without_debt | Jain viewport-quality fairness | +0.00019 [-0.00012, +0.00073] | 1 |
| debt_given_calibration | Worst-user VW-PSNR (dB) | +1.17893 [+0.80935, +1.57014] | 7.187e-05 |
| debt_given_calibration | Worst-user VW-SSIM | +0.01796 [+0.01162, +0.02488] | 0.0001193 |
| debt_given_calibration | Jain viewport-quality fairness | +0.01057 [+0.00715, +0.01430] | 4.987e-05 |
| gate_given_calibrated_debt | Worst-user VW-PSNR (dB) | +0.00000 [+0.00000, +0.00000] | 1 |
| gate_given_calibrated_debt | Worst-user VW-SSIM | +0.00000 [+0.00000, +0.00000] | 1 |
| gate_given_calibrated_debt | Jain viewport-quality fairness | +0.00000 [+0.00000, +0.00000] | 1 |
| calibration_given_gated_debt | Worst-user VW-PSNR (dB) | -0.06879 [-0.22982, +0.04644] | 1 |
| calibration_given_gated_debt | Worst-user VW-SSIM | -0.00126 [-0.00432, +0.00092] | 1 |
| calibration_given_gated_debt | Jain viewport-quality fairness | -0.00119 [-0.00245, -0.00028] | 0.1201 |
| gate_given_mean_debt | Worst-user VW-PSNR (dB) | +0.00000 [+0.00000, +0.00000] | 1 |
| gate_given_mean_debt | Worst-user VW-SSIM | +0.00000 [+0.00000, +0.00000] | 1 |
| gate_given_mean_debt | Jain viewport-quality fairness | +0.00000 [+0.00000, +0.00000] | 1 |

## Recent-method executable adaptations

`fair_edge_nsw_proxy` implements the uncertainty-adjusted Nash edge objective but not the published MARL/GNN policy. `aci_nash` implements per-user adaptive conformal alpha feedback but not the single-user viewport model from Risk as a Resource.

| Comparator | Outcome | CREDO delta [95% CI] | Holm p |
|---|---|---:|---:|
| fair_edge_nsw_proxy | Worst-user VW-PSNR (dB) | +1.19679 [+0.82816, +1.58490] | 4.107e-05 |
| fair_edge_nsw_proxy | Worst-user VW-SSIM | +0.01853 [+0.01211, +0.02545] | 4.125e-05 |
| fair_edge_nsw_proxy | Jain viewport-quality fairness | +0.01070 [+0.00731, +0.01435] | 2.009e-05 |
| fair_edge_nsw_proxy | Total stall (s) | +0.00000 [+0.00000, +0.00000] | 1 |
| fair_edge_nsw_proxy | Representation-switch rate | -0.01000 [-0.04222, +0.02222] | 1 |
| aci_nash | Worst-user VW-PSNR (dB) | +1.17893 [+0.80935, +1.57014] | 4.107e-05 |
| aci_nash | Worst-user VW-SSIM | +0.01796 [+0.01162, +0.02488] | 4.587e-05 |
| aci_nash | Jain viewport-quality fairness | +0.01057 [+0.00715, +0.01430] | 2.992e-05 |
| aci_nash | Total stall (s) | +0.00000 [+0.00000, +0.00000] | 1 |
| aci_nash | Representation-switch rate | -0.01111 [-0.04556, +0.02444] | 1 |

## Interpretation boundary

The experiment tests controller behaviour under independently sourced content, measured VBR segment sizes, and held-out public HMD traces. VW-PSNR, VW-SSIM, and the declared quality index are objective engineering measures. They do not establish subjective perceptual superiority.

Content-stratified effects are secondary and are retained in `content_effects.csv`; they are not additional confirmatory tests. They are heterogeneous and therefore do not support a claim of mean-quality improvement for every content.
