# Feasibility-based recovery admission

The [fixed protocol](PLAN.md) retains the distortion/deadline contract and
distinguishes conditional admission, certified impossibility and abstention.
The [derivation](THEORY.md) uses sender-side spatial bounds without future user
quality. Causal point-planning controls are evaluated under the same contract;
future-known paths are offline diagnostics, not admission inputs.

```console
python -m unittest admission_contract.test_core -v
python -m admission_contract.run
python -m admission_contract.run --verify
```

The batch uses only already exposed public scalar labels, sender error maps,
file-byte metadata, media timelines and prior timing records. No private pose
cache, media download or GPU is needed. Commands refuse to overwrite results.
All code and outcomes are published before any manuscript or fresh holdout work.
Passing software tests alone does not establish useful or deployable admission.
