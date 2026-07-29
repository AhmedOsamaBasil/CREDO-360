# CREDO-360

**Open testbed for coverage-calibrated QoE deprivation recovery in fair
multi-user immersive streaming.**

This repository contains the prototype, CUDA replay experiment, statistical
analysis, literature-review evidence, exported learned model, and live
Mininet/DASH integration used by the CREDO-360 paper.

> Research status: powered live-emulation campaign complete. The manuscript is
> in preparation. Operational QoE is model-estimated, not a new subjective MOS.

## Topic

**Coverage-Calibrated Risk and Experiential Deprivation-Aware Optimization for
Multi-User 360-Degree Streaming**

The system combines:

1. a QoE predictor trained on the author's published subjective data;
2. online conformal lower bounds on predicted QoE;
3. persistent per-user QoE-shortfall debt;
4. opportunity gating that spends debt only when a candidate has calibrated
   evidence of improving the user; and
5. constrained multi-user bitrate allocation.

## Mathematical seed

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

The powered WSL2/Mininet campaign uses five clients fetching DASH segments
concurrently through one measured, time-varying shared bottleneck. Across 30
paired seeds and six controllers, CREDO-360 improved worst-user mean
operational QoE by `0.2090` over conformal Nash
(`p_Holm=1.12e-7`, paired-bootstrap 95% CI `[0.1416, 0.2886]`) and Jain
fairness by `0.002393` (`p_Holm=8.20e-7`). Stall time did not improve.
The opportunity gate was saturated and the confirmatory comparison with
ungated debt was null; this limits the gate-specific claim. See
`LIVE_POWERED_EXPERIMENT_REPORT.md`.

## Package map

- `testbed/` - GPU code, named data, tests, configurations, and results.
- `testbed/FEATURE_SCHEMA.md` - recovered published feature mapping.
- `testbed/results_explicit_final/` - corrected 12-seed result.
- `testbed/sensitivity/` - service-floor sensitivity.
- `literature/` - reproducible search, 25-study evidence table, synthesis, and
  qualified novelty assessment.
- `live_testbed/` - learned-model export, Mininet harness, tests, raw live
  measurements, summary, and figure.
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
The next validation stage should add independent content, non-actionable
impairments that can exercise the opportunity gate, and independently
validated live QoE labels.
