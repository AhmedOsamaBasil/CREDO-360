# Recovery feasibility frontier

An exact offline audit of the resource and donor-quality allowances needed to
repay at least half the original loss in the 168 **already exposed** episodes.
It retains the original loss and service references, expands the action menu
to all joint representations respecting the recipient floor, and separates
byte headroom, donor step loss, total donor loss and number of recovery actions.

- [Fixed plan](PLAN.md)
- [Method and correctness arguments](METHOD.md)
- [Findings and limitations](INTERPRETATION.md)
- [Generated cohort/scene report](results/audit_v1/REPORT.md)
- [Resource/donor frontier figure](results/audit_v1/figures/feasibility_frontier.png)

Completed finding: no episode meets half-repayment at <=2x peak byte allowance,
even without donor protection. At 3x and with zero donor loss, 147/168 are feasible
with up to four recovery actions; 11 remain impossible at any allowance. These
are future-known opportunity limits, not evidence of controller superiority.

No new data or manuscript changes are involved. This is not an online-policy
experiment, fresh validation or a human-QoE claim.

## Reproduction

Python 3.12+, NumPy and pytest suffice for audit/testing. From the repository root:

```bash
python -m pytest feasibility_frontier -q
python -m feasibility_frontier.run --output work/frontier_reproduction
python -m feasibility_frontier.verify --output work/frontier_reproduction
python -m feasibility_frontier.check_breakpoints --output work/frontier_reproduction
```

The runner refuses to overwrite an existing directory. No media download, GPU,
network access or commercial solver is needed. Results include exact rational
breakpoints, integral action witnesses and all infeasible slices. The verifier
replays all episodes and checks independent dynamic programming, monotonicity,
ledger conservation and file hashes.

To verify the published snapshot, omit `--output` in the two verification
commands. The additional endpoint checker was added after the initial audit;
it independently tests every staircase breakpoint without altering its method
or results. Both Windows and Linux reports are included. Optional visualization
uses Matplotlib: `python -m feasibility_frontier.plot --output work/frontier_figures`.
