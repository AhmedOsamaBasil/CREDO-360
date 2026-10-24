# Headroom and limited cumulative recovery reserve

This package assesses what existing evidence can establish about spare capacity
and adds a finite, non-refilling byte entitlement to the recovery contract.
The reserve is separate from contemporaneous capacity and the quality-loss
ledger. No new holdout, network experiment or manuscript revision is involved.

- [Fixed plan](PLAN.md)
- [Contract, proofs, limitations and primary references](THEORY.md)

Constructed causal tests compare an absolute-loss minimax plan with rolling
Nash, rolling max-min and greedy recovery. An independent Bellman recursion
checks the finite-policy enumeration. The future model is supplied, not fitted.
Separate exposed-catalogue calculations retain all168 episodes and quantify
minimum extra bytes, payload-rate demand and matched fixed-reserve comparisons.
Required capacity is not evidence of measured spare capacity.

## Reproduction

Use the existing Python environment with NumPy and pytest, from the repository root:

```bash
python -m pytest reserve_recovery -q
python -m reserve_recovery.run --output work/reserve_reproduction
python -m reserve_recovery.verify --output work/reserve_reproduction
```

The runner refuses to overwrite an existing directory. No GPU, new media or
external solver is required. Every analytical decision and budget comparison
uses exact integer/rational arithmetic. Source/input/result hashes bind the
artifact; full replay verifies every retained result, including failures.
