# Metric and service-contract sensitivity

Exploratory audit of **exposed** data; no controller tuning or new holdout.
The [fixed protocol](PLAN.md) separates rescoring eight saved policy paths from
future-known strict-floor opportunity bounds. Four metric mappings, two initial
impairment-rung accounts, four repayment targets, three recovery horizons and
two credit clocks are fixed before the batch. All earlier artifacts are unchanged.

## Reproduce

From the repository root, using Python with NumPy:

```console
python -m unittest metric_contract.test_core -v
python -m metric_contract.run --verify
```

`--verify` reruns the complete grid, independent scalar path enumeration,
minimum-cost witnesses and historical parity checks, then checks source/input
hashes and the published outcome. Without `--verify`, the command creates a
new result directory and refuses to overwrite it. No private telemetry, media,
network transfer or GPU is needed: the inputs are existing published scalar
quality values, actual-file sizes and frozen paths.

Results will be published after the frozen batch. Do not infer a favorable
outcome from this implementation or its synthetic tests. Neither the bound nor
the counterfactual rescoring is a deployable new recovery controller.
