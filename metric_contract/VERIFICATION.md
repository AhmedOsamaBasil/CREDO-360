# Verification record

## Frozen method and complete scientific replay

- Protocol/method commit pushed before outcomes: `5178cd80a929cf8d46dec0855af680206762e0c5`.
- Original method sources and `PLAN.md` remain unchanged after that commit.
- Full Windows and WSL runs reproduce all 64,512 fixed-path rows, 8,064 bound
  rows, source/input hashes, historical scores, exact-clock checks and witness
  checks. Canonical scientific SHA256:
  `479f9d67fe6bee493728ef5889c65aae5292c2091b4c74b67aa23ad62b5d02fe`.
- 4,032 independent scalar queries, 32,256 minimum-cost target checks, 1,344
  original policy-score checks and 168 historical strict-bound checks pass.
- Separate post-hoc diagnostic SHA256 agrees on both systems:
  `2eb8384e4ce872614c715c151fbc2c6de11d40fe1f3c19ccd772b21f4c5a3eb3`.
- PNG/SVG visually inspected; exact published figure hashes verified on both
  systems. Original and portable successor diagnostic metadata are retained.

## Tests

- 18 pre-batch synthetic method tests pass on both systems.
- 6 post-outcome regression checks retain grid completeness, adverse rankings,
  tiny floor-loss magnitudes and the no-new-success/no-holdout boundary.
- Full Windows regression: **336 tests and 24 subtests pass**.
- Available Linux regression: **332 tests and 24 subtests pass**. The four
  additional Torch tests run in the Windows environment, not the local Linux
  environment; this is not a four-test scientific disagreement.
- Existing portable-model tests: **5 pass on each OS**.
- Existing JavaScript client protocol: **11 assertions pass**.

The initial Windows temporary-directory fixture error and diagnostic metadata
portability correction are documented in `MEASUREMENT_NOTES.md`. Their fixes
do not change frozen methods or scientific outputs. No historical test was
relaxed. The public CI includes the complete new replay and diagnostics.

No live network, media download/re-encoding, player/HMD experiment, model tuning,
fresh holdout, manuscript or acknowledgment update was performed. Passing these
checks establishes reproducibility, not controller superiority or human QoE.
