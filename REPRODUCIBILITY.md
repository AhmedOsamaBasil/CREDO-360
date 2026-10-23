# Reproducibility guide

## Artifact layers

Post-audit experiments are versioned separately: [corrected recovery v1](recovery_pilot/README.md)
and [fresh-content feasibility-aware v2](feasibility_recovery/README.md). The
first failed its performance screen; historical files below are not silently
recomputed with the repaired clock or new controller.

| Layer | Entry point | Evidence |
|---|---|---|
| Dependency-light feasibility model | `prototype.py` | `results.csv` |
| CUDA trace-replay benchmark | `testbed/run_experiment.py` | `testbed/results_explicit_final/` |
| Statistical analysis | `testbed/analyze_results.py` | paired tests, bootstrap intervals, figures |
| Service-floor sensitivity | `testbed/analyze_sensitivity.py` | `testbed/sensitivity/` |
| Live shared-bottleneck integration | `live_testbed/run_mininet_experiment.py` | `live_testbed/results/live_run/` |
| Portable learned model | `live_testbed/portable_qoe.py` | `live_testbed/artifacts/qoe_ensemble.json` |
| TMM gate-identification campaign | `live_testbed/analyze_gate_campaign.py` | `live_testbed/results/journal_gate_analysis/` |
| TMM deterministic-cover scaling | `live_testbed/benchmark_scalability.py` | `live_testbed/results/journal_scalability/` |
| Independent multimedia generalization | `multimedia_testbed/run_generalization.py` | `multimedia_testbed/results/generalization_analysis/` |

## Minimal verification

Create a Python 3.12+ environment. Install the pinned GPU environment for the
full replay, or install NumPy and pytest for the dependency-light checks.

```bash
python -m pytest testbed/tests -q
python live_testbed/test_portable.py
```

Expected result: four replay/controller tests and three portable-model tests
pass.

## CUDA replay

From the repository root:

```bash
python testbed/run_experiment.py \
  --config testbed/config.yaml \
  --data testbed/data \
  --output testbed/results_explicit_final

python testbed/analyze_results.py \
  --results testbed/results_explicit_final
```

The accepted experiment uses 12 paired seeds, five users, 160 epochs, six
controllers, and a mid-run distribution shift. `testbed/config.yaml` is the
authoritative configuration.

## Live Mininet integration

The live harness requires Linux/WSL, root privileges, Mininet, Open vSwitch,
FFmpeg, and access to legal DASH media segments. It does not require CUDA
because inference uses the exported NumPy artifact.

```bash
sudo python3 live_testbed/run_mininet_experiment.py \
  --model live_testbed/artifacts/qoe_ensemble.json \
  --media-root /path/to/dash/media \
  --output live_testbed/results/live_run

python live_testbed/analyze_live.py \
  live_testbed/results/live_run/live_measurements.csv
```

See `live_testbed/ENVIRONMENT.md` for the validated platform.

## Independent multimedia generalization

Third-party QoEVAVE media and traces are not committed. The manifest contains
the official URLs and the preparation output records their SHA-256 hashes.
From WSL with FFmpeg/NVENC and the scientific dependencies installed:

```bash
python3 multimedia_testbed/prepare_qoevave.py
python3 multimedia_testbed/run_generalization.py
python3 multimedia_testbed/analyze_generalization.py
python3 -m pytest multimedia_testbed/test_generalization.py -q
```

Expected outputs are under `multimedia_testbed/artifacts/qoevave/`,
`multimedia_testbed/results/generalization_30seed/`, and
`multimedia_testbed/results/generalization_analysis/`. The campaign audit must
report `passed: true`, 2,700 rows, and 30 paired seeds.

## Integrity and interpretation

- `testbed/data/provenance.json` records the source and SHA-256 of the
  published QoE data.
- The portable artifact SHA-256 is recorded in
  `live_testbed/ENVIRONMENT.md`.
- The accepted and rejected phases are retained separately.
- Live operational QoE is a model estimate, not a new subjective MOS.
- The current live result is a mechanism/integration test and is not powered
  confirmatory evidence.

## Double-blind review

This repository identifies the author. For a double-blind venue, create an
anonymous archival snapshot without account identifiers and cite that snapshot
during review. Reveal this canonical repository after the anonymity period.
