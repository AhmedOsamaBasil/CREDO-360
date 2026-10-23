# CREDO-360

> **Technical correction in progress (October 2026).** The historical studies
> below remain available, but legacy subjective residuals do not validate
> objective-quality coverage, the original gate can be action-equivalent to
> ordinary quality debt, and synchronized playback timing required correction.
> Do not treat those results as validation of a distinct calibrated recovery
> mechanism. See [`recovery_pilot/`](recovery_pilot/README.md) for the corrected
> objective-target pilot, fixed protocol, tests and explicit progression gate.
> Historical result files are unchanged; new software refuses to overwrite or
> mix them with corrected runs.

The first corrected recovery pilot **failed** its progression screen. A separate
[feasibility-aware recovery experiment](feasibility_recovery/README.md) now tests
a jointly feasible anti-windup reference on three previously unused QoEVAVE
scenes. Its fixed protocol, matched baselines and fresh calibration/test split
are published before evaluation. Neither the historical gate nor a smaller
internal queue should be read as evidence of delivered-quality improvement.
The completed [v2 findings](feasibility_recovery/INTERPRETATION.md) also fail the
predeclared screen: aggregate shortfall/stall improve relative to fixed debt,
but worst-user quality declines and actions nearly coincide with bounded Nash.
Both studies' raw results, adverse findings and audits remain public.

A separate [longer-horizon redesign](horizon_recovery/README.md) develops a
joint-mixture service contract and signed-window recovery on exposed v2 data.
Its complete six-configuration development search and stricter fresh-content
protocol are frozen before evaluation. Comparisons include stateless Nash and
a scale-matched memoryless control under a common per-round byte cap.

**Open research testbed for objective viewport-quality fairness and
deprivation recovery in multi-user immersive streaming.**

This repository contains the prototype, CUDA replay experiment, statistical
analysis, literature-review evidence, exported learned model, and live
Mininet/DASH integration used by the CREDO-360 paper.

> Research status: historical campaigns are preserved; post-audit corrections
> and exploratory validation are underway. The paper makes controller and
> objective viewport-quality claims, not new subjective MOS or human-QoE claims.

## Topic

**Coverage-Calibrated Risk and Viewport-Quality Deprivation-Aware Optimization
for Multi-User 360-Degree Streaming**

The system combines:

1. a QoE predictor trained on the author's published subjective data;
2. online conformal lower bounds on predicted QoE;
3. persistent per-user QoE-shortfall debt;
4. opportunity gating that spends debt only when a candidate has calibrated
   evidence of improving the user; and
5. constrained multi-user bitrate allocation.

## Historical mathematical seed

The original expression below is retained for traceability. Its opportunity
term is not a certified gain bound and can be action-equivalent to ordinary
quality debt. The corrected candidate is described in `recovery_pilot/` and
must be judged by that pilot's actual results, not this historical claim.

For predicted lower QoE bound \(L_{i,t}(a)\), service-floor debt

\[
d_{i,t+1}=[\rho d_{i,t}+q^\star-q_{i,t}]_+,
\]

and minimum-service action \(a^{\min}\), the controller selects

\[
a_t^\star = \arg\max_{a\in\mathcal A(C_t)}
\sum_i\log L_{i,t}(a)
+\lambda\sum_i\frac{d_{i,t}}{1+\bar d_t}
[L_{i,t}(a)-L_{i,t}(a^{\min})]_+
-\eta S(a,a_{t-1}).
\]

See `TECHNICAL_NOVELTY.md` for the complete formulation and prior-art
boundary.

## Experimental status

The corrected phase-2 RTX experiment uses:

- the recovered 13-feature MAT schema;
- 170 published subjective stimuli with 36 ratings;
- 30 packet-capture replay traces;
- six controllers, 12 paired seeds, five users, and 160 decision epochs;
- a mid-run network/device distribution shift; and
- paired Wilcoxon tests with Holm correction and bootstrap intervals.

Relative to uncertainty Nash, the proposed method significantly improved
worst-user mean QoE, Jain user-QoE fairness, and rebuffering. It significantly
worsened mean QoE, CVaR, and service-floor violation. This is a measurable
fairness/continuity trade-off, not universal QoE improvement.

See `EXPERIMENT_REPORT.md`. The rejected anonymous-feature phase is preserved
as `EXPERIMENT_REPORT_PHASE1_REJECTED.md`.

The journal testbed adds a deterministic low-discrepancy action cover
that avoids materializing the full bitrate Cartesian product. A frozen
30-seed controller benchmark evaluates 5, 10, 20, and 30 users with 240
decisions per population size. On the single-threaded WSL CPU/NumPy path,
median latency increases from 77.07 ms at five users to 438.35 ms at 30
users; 30-user p99 is 540.39 ms, peak process RSS is 80.2 MiB, and there are
zero feasibility violations. See `JOURNAL_SCALABILITY_REPORT.md`,
`JOURNAL_EXPERIMENT_PROTOCOL.md` and
`live_testbed/results/journal_scalability/`.
The non-actionable Mininet condition has also passed a one-seed engineering
test; its deliberately limited observation is documented in
`JOURNAL_IMPAIRMENT_SMOKE_REPORT.md`.

The powered WSL2/Mininet campaign uses five clients fetching DASH segments
concurrently through one measured, time-varying shared bottleneck. Across 30
paired seeds and six controllers, CREDO-360 improved the worst-user
operational quality index by `0.2090` over conformal Nash
(`p_Holm=1.12e-7`, paired-bootstrap 95% CI `[0.1416, 0.2886]`) and Jain
fairness by `0.002393` (`p_Holm=8.20e-7`). Stall time did not improve.
The opportunity gate was saturated and the confirmatory comparison with
ungated debt was null; this limits the gate-specific claim. See
`LIVE_POWERED_EXPERIMENT_REPORT.md`.

The subsequent frozen gate-identification experiment targets that
limitation with paired capacity-only and non-actionable conditions. Across 30
paired seeds, CREDO-360 reduced wasted allocation by 73.9% and total stall by
70.8% versus ungated resource debt, while improving the worst unimpaired
user's operational QoE by 0.203 points. All three effects remain significant
after Holm correction; the activation-frequency outcome remains null and is
reported as such. Both 4,050-row condition audits pass. See
`JOURNAL_GATE_FINAL_REPORT.md` and
`live_testbed/results/journal_gate_analysis/`.

Experiment C adds independent objective multimedia validation using six public
QoEVAVE 8K 360-degree sequences and user-disjoint HMD traces. Across 30 paired
seeds, CREDO-360 improves worst-user VW-PSNR by 1.179 dB
(`p_Holm=2.05e-5`), worst-user VW-SSIM by 0.01796
(`p_Holm=2.75e-5`), and Jain viewport-quality fairness by 0.01057
(`p_Holm=1.66e-5`). Stall is exactly tied and switching is nonsignificant.
The six-cell component ablation identifies persistent debt as the active
fairness mechanism; the opportunity gate is action-equivalent in this
capacity-only replay. Two executable recent-method adaptations and
heterogeneous content-level effects are reported with explicit claim limits.
See `JOURNAL_MULTIMEDIA_GENERALIZATION_REPORT.md` and
`multimedia_testbed/results/generalization_v2_analysis/`.

## Package map

- `testbed/` - GPU code, named data, tests, configurations, and results.
- `testbed/FEATURE_SCHEMA.md` - recovered published feature mapping.
- `testbed/results_explicit_final/` - corrected 12-seed result.
- `testbed/sensitivity/` - service-floor sensitivity.
- `literature/` - reproducible search, 25-study evidence table, synthesis, and
  qualified novelty assessment.
- `live_testbed/` - learned-model export, Mininet harness, tests, raw live
  measurements, summary, and figure.
- `multimedia_testbed/` - independent 360-degree media preparation,
  held-out head-trace replay, paired statistics, results, and figures.
- `JOURNAL_EXPERIMENT_PROTOCOL.md` - frozen evaluation protocol covering
  non-actionable impairment, scalability, and independent-content validation.
- `JOURNAL_GATE_FINAL_REPORT.md` - completed two-condition gate-identification
  experiment, paired inference, null result, and claim boundary.
- `live_testbed/benchmark_scalability.py` - reproducible 5--30-user
  controller-side benchmark.
- `prototype.py` / `results.csv` - original dependency-light feasibility seed.
- `MANIFEST.md` - complete inventory.
- `REPRODUCIBILITY.md` - minimal checks and end-to-end reproduction commands.
- `CITATION.cff` - software citation metadata.

## Quick verification

Create a Python 3.12+ environment and run:

```bash
python -m pytest testbed/tests -q
python live_testbed/test_portable.py
```

Expected result: four replay/controller tests and three portable-model tests
pass. Full CUDA and Mininet instructions are in `REPRODUCIBILITY.md`.

## Reproduce the accepted replay

```bash
python testbed/run_experiment.py \
  --config testbed/config.yaml \
  --data testbed/data \
  --output testbed/results_explicit_final

python testbed/analyze_results.py \
  --results testbed/results_explicit_final
```

The pinned CUDA environment is in `testbed/requirements.txt`. A CPU-only
environment is sufficient for the portable-model test.

## Citation

Use the repository's `CITATION.cff`. Until the paper receives a DOI, cite the
software release and state the exact commit or release tag used.

## License and data

Code and original documentation are released under the MIT License. Source
data provenance and integrity hashes are recorded in
`testbed/data/provenance.json`. Third-party datasets, media, and packet
captures remain subject to their original licenses; this license does not
relicense them. No copyrighted DASH media segments are included.

## Review anonymity

This canonical repository identifies the author. For a double-blind venue,
cite an anonymized archival snapshot during review and reveal this repository
after the anonymity period.

## Interpretation

The network stage is live emulation with real segment transfer and 30 paired,
counterbalanced seeds, but it is not a headset or human-subject experiment.
Independent-content and non-actionable-impairment stages are now complete.
The remaining external-validity step is a preregistered headset/user study or
an independently validated perceptual outcome model evaluated on the same
compressed/stalled representations.
