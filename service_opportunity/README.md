# Controlled service and causal opportunity model

This package tests a finite extra-byte recovery reserve under an explicit
absolute service budget. It combines isolated Linux TCP probes with a causal
prefix forecast on already-exposed QoEVAVE measurements. It does not modify
the earlier frozen experiments or consume a new holdout.

- [Fixed plan](PLAN.md), [technical scope](THEORY.md),
  [findings and limitations](INTERPRETATION.md).
- [Complete report](results/development_v1/REPORT.md),
  [measured service](results/service_v1.json),
  [initial measurement failure](MEASUREMENT_NOTES.md).
- [Service figure](results/development_v1/figures/service_completion.png),
  [controller comparison](results/development_v1/figures/primary_comparison.png).

The fixed development screen passes, but the gain over greedy is small and
post-event quality can decline. Initial forecast-success flags fail24/88 times.
Controlled reservation is not field spare capacity, and current quality is
revealed exactly to every controller. See the interpretation before using any
numbers as evidence for a deployment or scientific contribution.

## Reproduction

From the repository root with NumPy, Matplotlib and pytest installed:

```bash
python -m pytest service_opportunity -q
python -m service_opportunity.verify
python -m service_opportunity.check_oracle
python -m service_opportunity.ablation --verify
python -m service_opportunity.check_support
```

`verify` recomputes every primary deterministic result and checks recorded live
measurements; it does not rerun the live network or expect timing determinism.
The scientific inputs are the six previously published v2/v3 quality/size tables.
Only those tables are used; no source media downloads are required.

To rerun the controlled network protocol, use Linux root with `ip`, `tc`, and
`ethtool` available. The harness creates experiment-specific namespaces linked
only to each other and removes them on completion. It does not configure a host
network interface or contact an Internet endpoint. Choose a new output path:

```bash
sudo /path/to/python -m service_opportunity.service --output work/service_repeat.json
python -m service_opportunity.run --service work/service_repeat.json --output work/service_model_repeat
```

Published outputs are never overwritten. Raw15-probe results include per-flow
receiver receipts, timing, configuration commands and qdisc counters. The first
invalid measurement attempt is retained separately; it is not counted in the
validated15 probes. `benchmark.py` checks672 individual forecasting/planning
decisions using loaded tables; it is not an integrated player timing test.

## Files and comparators

`model.py` implements scene/identity-excluded prefix KNN and exact gain/cost DP.
`run.py` compares KNN, persistence, greedy recovery, rolling Nash, rolling max-min
and a future-known oracle at three fixed reserve sizes. `ablation.py` adds two
explicitly post-hoc diagnostics: minimum-cost greedy and unconditional training
mean with the same optimizer. Per-episode actions, forecast neighbors, debt and
reserve ledgers, predictive feasibility flags and quality tradeoffs are retained
in compressed JSON. Separate Windows/Linux verification and timing records are
included. No scholarly novelty is claimed for the standard component algorithms.
