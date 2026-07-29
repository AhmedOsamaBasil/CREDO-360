# CREDO-360 GPU replay testbed

This is a reviewable prototype for coverage-calibrated, deprivation-aware
multi-user 360-degree streaming.

## Scope

- The QoE model uses the author's published subjective dataset: 170 valid
  stimuli, 13 recovered named features, and 36 ratings.
- Network variation is replayed from 30 packet captures in the published repo.
- Model training and action scoring run on CUDA (tested on an RTX 3090).
- Users, shared-link allocation, viewport misses, distribution shift, and
  online QoE outcomes are simulated. This is not a live VR experiment.
- Captured traffic is an observed replay signal, not latent path capacity.

See `FEATURE_SCHEMA.md` for the recovered MAT column mapping.

## Pipeline

1. `prepare_data.py` extracts named ratings/features, PCAP traces, and
   provenance.
2. `model.py` trains a five-member heteroscedastic deep ensemble.
3. `calibration.py` supplies one-sided conformal QoE bounds with practical
   clipped ACI-style feedback and hierarchical regime warm-starting.
4. `run_experiment.py` compares six controllers under a mid-run shift.
5. `analyze_results.py` runs paired Wilcoxon/Holm tests, bootstrap intervals,
   and plots.
6. `analyze_sensitivity.py` compares service floors 1.5, 2.0, and 2.5.

The optimizer evaluates a deterministic 384-point cover of the feasible joint
bitrate space as one CUDA batch per epoch. It is approximate.

## Reproduce

From the repository root:

```bash
python testbed/prepare_data.py \
  --phd-repo /path/to/PhD \
  --output testbed/data

python testbed/run_experiment.py \
  --config testbed/config.yaml \
  --data testbed/data \
  --output testbed/results_explicit_final

python testbed/analyze_results.py \
  --results testbed/results_explicit_final
```

Tests:

```bash
python -m pytest testbed/tests -q
```

## Guardrails

- Phase 1 is preserved as rejected: its anonymous feature mapping was not
  defensible.
- The final 12-seed result is prototype evidence, not a final powered study.
- The clipped groupwise calibration is audited empirically; the exact
  unmodified ACI theorem is not transferred to it.
- The result improves worst-user mean QoE, Jain fairness, and rebuffering but
  worsens mean QoE, CVaR, and service-floor violation versus uncertainty Nash.
- A paper-ready evaluation needs an independent immersive dataset and live
  DASH/Mininet or hardware-in-the-loop validation.
