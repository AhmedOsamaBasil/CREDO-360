# Experiment C: independent multimedia generalization

## Validation

- Audit: **PASS**
- Raw paired rows: 2,700
- Seeds: 30
- Outcome: objective viewport-weighted luma PSNR; not subjective MOS.

## Content complexity

| Content | SI | TI | Relative rank | Held-out users |
|---|---:|---:|---|---:|
| Badminton05 | 100.70 | 4.09 | medium | 19 |
| ForestWalk03 | 98.78 | 18.82 | high | 19 |
| Skateboarding01 | 71.39 | 4.00 | low | 19 |

## Prespecified CREDO-360 versus conformal Nash tests

| Outcome | CREDO | Baseline | Delta [95% CI] | Holm p | Rank-biserial |
|---|---:|---:|---:|---:|---:|
| Worst-user VW-PSNR (dB) | 26.75491 | 26.27184 | +0.48308 [+0.27004, +0.70266] | 0.0006013 | +0.801 |
| Jain viewport-quality fairness | 0.96390 | 0.95576 | +0.00815 [+0.00468, +0.01201] | 0.0005194 | +0.828 |
| Total stall (s) | 5.35616 | 5.35616 | +0.00000 [+0.00000, +0.00000] | 1 | +0.000 |
| Representation-switch rate | 0.63111 | 0.60667 | +0.02444 [-0.01778, +0.06556] | 0.4757 | +0.260 |

## Interpretation boundary

The experiment tests controller behaviour under independently sourced content, measured VBR segment sizes, and held-out public HMD traces. VW-PSNR and its declared quality index are objective engineering measures. They do not establish subjective perceptual superiority.

Content-stratified effects are secondary and are retained in `content_effects.csv`; they are not additional confirmatory tests. They are heterogeneous and therefore do not support a claim of mean-quality improvement for every content.
