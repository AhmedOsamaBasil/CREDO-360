# Recovery feasibility frontier

An exact offline audit of the resource and donor-quality allowances needed to
repay at least half the original loss in the 168 **already exposed** episodes.
It retains the original loss and service references, expands the action menu
to all joint representations respecting the recipient floor, and separates
byte headroom, donor step loss, total donor loss and number of recovery actions.

- [Fixed plan](PLAN.md)
- [Method and correctness arguments](METHOD.md)

No new data or manuscript changes are involved. This is not an online-policy
experiment, fresh validation or a human-QoE claim.

## Reproduction

Python 3.12+, NumPy and pytest suffice for audit/testing. From the repository root:

```bash
python -m pytest feasibility_frontier -q
python -m feasibility_frontier.run --output work/frontier_reproduction
python -m feasibility_frontier.verify --output work/frontier_reproduction
```

The runner refuses to overwrite an existing directory. No media download, GPU,
network access or commercial solver is needed. Results include exact rational
breakpoints, integral action witnesses and all infeasible slices. The verifier
replays all episodes and checks independent dynamic programming, monotonicity,
ledger conservation and file hashes.
