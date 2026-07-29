# CREDO-360 phase-1 rejected experiment report

Run date: 28 July 2026  
Hardware: NVIDIA GeForce RTX 3090, CUDA 12.8, PyTorch 2.11  
Design: 6 controllers × 8 paired seeds × 5 users × 160 epochs

## Purpose

This phase tested whether calibrated QoE lower bounds and persistent
deprivation debt can improve worst-user and lower-tail QoE under a mid-run
network/device shift.

## Testbed

- Five-member heteroscedastic deep ensemble trained on the author’s published
  subjective dataset: 170 valid stimuli, 13 anonymous input columns, and 36
  ratings per stimulus.
- Group-disjoint train/calibration/test split; held-out predictor MAE 0.332 and
  RMSE 0.407 MOS.
- Thirty replay signals derived from packet captures in the author’s published
  repository.
- Five simulated users sharing a constrained bitrate budget.
- Published bitrate ladder:
  0.045, 0.088, 0.253, 0.369, 0.987, and 3.792 Mbps.
- Distribution shift at epoch 80.
- Practical group-conditioned rolling conformal calibration with clipped
  ACI-style miscoverage feedback.
- Approximate action optimizer: deterministic 384-point cover of the feasible
  joint bitrate space, evaluated as one CUDA batch per epoch.

## Final result

| Controller | Mean QoE | Worst-user mean | QoE CVaR10 | Group gap | Post-shift coverage | Rebuffer rate |
|---|---:|---:|---:|---:|---:|---:|
| Mean greedy | 1.641 | 1.448 | 1.110 | 0.146 | 0.913 | 0.049 |
| Proportional fair | 1.654 | 1.472 | 1.133 | 0.163 | 0.907 | 0.041 |
| Uncertainty Nash | **1.667** | **1.485** | **1.166** | 0.148 | 0.900 | **0.012** |
| Conformal Nash | 1.658 | 1.455 | 1.115 | 0.176 | 0.910 | 0.041 |
| Static conformal + debt | 1.651 | 1.481 | 1.128 | 0.163 | 0.914 | 0.014 |
| Adaptive conformal + debt | 1.646 | 1.439 | 1.084 | 0.177 | 0.913 | 0.065 |

The adaptive calibrator achieved 0.911 overall coverage and 0.913 post-shift
coverage for a nominal 0.90 target. This supports the calibration
implementation as an empirical mechanism in this replay.

The proposed adaptive debt controller did **not** improve fairness or tail QoE.
Against uncertainty Nash, its paired differences were −0.045 worst-user MOS and
−0.082 CVaR10. With eight pairs, neither remained significant after Holm
correction (adjusted p = 0.188 and 0.391). The result does not support a
performance claim.

## Engineering findings retained

1. An unattainable QoE target causes debt to grow and degrades allocation. The
   rejected configuration and results are preserved.
2. A new calibration regime must inherit pooled residual history; starting from
   one observation creates spuriously narrow bounds.
3. Residual-window replacement alone does not control post-shift coverage.
   Miscoverage feedback brought aggregate/post-shift coverage close to target.
4. Debt should weight only model-predicted recoverable QoE gain. Raw debt
   multiplication over-serves users whose impairment is not actionable.
5. Very high debt gain is unstable; the screening run at gain 10 is preserved.

## Decisive limitation

The MAT file does not expose names or semantics for its 13 input columns.
Although it supports held-out QoE prediction, converting candidate bitrate and
network states back into those anonymous columns requires assumptions that are
not strong enough for a causal/controller claim. Packet-capture traffic is also
observed delivered traffic, not latent link capacity.

Therefore this phase is a **prototype and hypothesis-rejection result**, not
paper-ready evidence that deprivation debt works.

## Next publishable experiment

1. Recover the exact feature schema and extraction code for the published MAT
   dataset, or create a new labelled table with explicit bitrate, throughput,
   buffer, stall, switch, latency, viewport miss, device, and MOS columns.
2. Run a live shared-link emulator (Linux traffic control/Mininet or the
   existing P4/DASH lineage) with real segment downloads and 360-degree content.
3. Use debt to prioritize only counterfactual actions whose calibrated QoE
   lower bound improves, with a formal Lyapunov/constraint interpretation.
4. Evaluate at least 30 paired traces, a second immersive dataset, oracle and
   no-shift controls, and sensitivity to target, gain, decay, calibration
   window, and action-search approximation.
5. Treat coverage, worst-user QoE, CVaR, rebuffering, and cumulative service
   violation as co-primary outcomes; preregister the direction of improvement.

The technical novelty remains worth testing, but the present evidence correctly
prevents a premature positive claim.
