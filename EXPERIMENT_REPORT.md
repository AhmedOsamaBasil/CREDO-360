# CREDO-360 phase-2 experiment report

Run date: 28 July 2026  
Hardware: NVIDIA GeForce RTX 3090, CUDA 12.8, PyTorch 2.11  
Design: 6 controllers × 12 paired seeds × 5 users × 160 epochs

## What changed after phase 1

Phase 1 was rejected because the published MAT input columns were treated as
anonymous. Phase 2 recovered their source schema from:

1. the MATLAB classifiers’ embedded `RequiredVariables`;
2. Table 6 of the author’s 2022 paper;
3. the bundled DASHIF player metric sequence; and
4. numeric range/correlation validation.

The corrected model inputs are buffer length, downloading bitrate, downloading
and current representation indices, maximum index, dropped frames,
minimum/average/maximum latency, minimum/average/maximum download time, and
selected representation bandwidth. The exact mapping is in
`testbed/FEATURE_SCHEMA.md`.

The replay outcome is now a declared media/network oracle independent of the
learned predictor. This avoids evaluating decisions using the same model that
selected them.

## Technical method

The controller maximizes calibrated Nash utility plus a debt-recovery term:

\[
\sum_i \log L_{i,t}(a)
+ \lambda \sum_i
\frac{d_{i,t}}{1+\bar d_t}
\left[L_{i,t}(a)-L_{i,t}(a^{\min})\right]_+
-\eta S(a,a_{t-1}).
\]

The positive-part counterfactual term is the key mechanism: accumulated
deprivation affects allocation only when the calibrated model predicts that the
candidate action can improve the user relative to minimum service.

## Final 12-seed results

| Controller | Mean QoE | Worst-user mean | CVaR10 | Jain QoE | Group gap | Violation rate | Rebuffer |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mean greedy | 1.848 | 1.321 | 1.032 | 0.967 | 0.280 | 0.413 | 0.313 |
| Proportional fair | **1.965** | 1.402 | 1.105 | 0.970 | 0.243 | 0.281 | 0.307 |
| Uncertainty Nash | **2.035** | 1.358 | **1.108** | 0.965 | 0.290 | **0.247** | 0.243 |
| Conformal Nash | 1.909 | 1.373 | 1.058 | 0.967 | 0.493 | 0.393 | 0.099 |
| Static conformal + debt | 1.516 | 1.198 | 1.016 | 0.961 | **0.237** | 0.616 | 0.021 |
| **Opportunity-aware adaptive debt** | 1.892 | **1.535** | 1.012 | **0.981** | 0.353 | 0.377 | **0.010** |

## Paired inference

Against uncertainty Nash, the proposed method produced:

- **+0.177 MOS worst-user mean**, Holm-adjusted \(p=0.0483\);
- **+0.0157 Jain QoE index**, adjusted \(p=0.0273\);
- **−0.2325 rebuffer rate**, adjusted \(p=0.00244\);
- −0.143 mean QoE, adjusted \(p=0.00977\);
- −0.096 CVaR10, adjusted \(p=0.0293\);
- +0.130 service-violation rate, adjusted \(p=0.00977\).

Against proportional fairness, the worst-user gain was +0.133 MOS but was not
significant after correction (\(p=0.151\)); the rebuffer reduction remained
significant (\(p=0.00244\)).

The result therefore supports a specific claim:

> Opportunity-aware calibrated debt improves persistent inter-user
> equalization and playback continuity relative to uncertainty-only allocation,
> at a statistically detectable cost in aggregate and instantaneous-tail QoE.

It does **not** support claims of universal QoE improvement, lower group gap, or
better service-floor compliance.

## Calibration

The proposed adaptive run obtained 0.911 overall empirical lower-bound coverage
for a nominal 0.90 target. Post-shift coverage was 0.884. This is an empirical
audit of a practical clipped, group-conditioned ACI-style update; the exact
unmodified ACI theorem is not claimed.

## Service-floor sensitivity

Two-seed screens at QoE floors 1.5, 2.0, and 2.5 consistently placed the
proposed method above uncertainty Nash in worst-user mean QoE and below it in
rebuffer rate. These screens establish directional robustness, not inferential
power. The plot and seed-level table are in `testbed/sensitivity/`.

## Validity limits

- QoE outcomes and distribution shift are simulated, although the predictor,
  bitrate ladder, subjective ratings, and traffic replay are grounded in the
  author’s published artifacts.
- Packet captures provide observed traffic, not latent path capacity.
- The feasible action search is an approximate deterministic 384-point cover.
- Twelve paired seeds remain modest; publication evaluation should use at least
  30 traces and a second dataset.
- A live DASH/Mininet or P4 hardware-in-the-loop experiment is still required.

## Next experiment

The next stage should reproduce the controller in the author’s Ubuntu
DASH/P4/Mininet testbed, log the recovered 13 features directly from real
segment requests, and compare against uncertainty Nash and proportional
fairness over at least 30 controlled link traces.

