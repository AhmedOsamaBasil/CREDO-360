# Analytical adaptive-policy feasibility audit

This package checks whether causal feedback can overcome the previous
fixed-plan limitation **without changing the contract**. It does not add a
learned controller or consume fresh observations. Read [PLAN.md](PLAN.md) and
the model-specific [proof and information assumptions](THEORY.md).

The whole-segment action must be committed before its viewport samples are
played. All previously available feedback is allowed; future sampled viewports
remain temporally unrestricted. An explicit geometric response rule yields
an upper bound on every deterministic causal policy's universal credit. The
quality floors are relaxed only for the upper bound, not for service admission.
Small finite games deliberately include cases where adaptation DOES help.

```console
python -m unittest adaptive_audit.test_core adaptive_audit.test_validation -v
python -m adaptive_audit.run
python -m adaptive_audit.run --verify
```

The first run refuses to overwrite results. Once published, the full replay
verifies source/input bindings, all generated results and the report. Public
sender maps and past scalar debts suffice; no media, private poses, future
participant-quality labels, GPU, HMD or new network measurement is needed.

These are analytical model checks, not human-QoE evidence, practical controller
superiority, calibrated probabilistic admission or a new general DP theorem.
