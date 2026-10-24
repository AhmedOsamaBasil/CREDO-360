# When to spend a compensation allowance

**Analytical reference implementation, not a validated streaming controller.**
This package extends the [event-local objective](../recovery_objective/THEORY.md)
without changing its service-loss ledger or any historical experiment.
It decides when to use a scarce donor-quality allowance by balancing the regret
of spending too early against the regret of missing an opportunity.

The rule solves a finite minimax game over **causal policies**, then samples
one policy for the entire recovery episode. Its current-step executor does not
receive the realized future. Every sampled policy obeys the resource cap,
recipient floor and donor-loss limits on every path. The possible-future set
is assumed supplied; predicting that set is not solved here.

## Main result and its limitation

In a two-period construction with loss 2, one available allowance, gain 1 now,
and either gain 0 or 2 later, the optimal probability of spending now is 1/2.
Its worst expected regret is 1/4, versus 1/2 for rolling Nash and 1 for rolling
max-min. These are **exact constructed results**, not measured improvements.

The same rule has worst expected unpaid fraction 3/4, compared with 1/2 for
greedy recovery. Thus better regret is **not** better absolute worst recovery.
An incorrect future set or a future reacting to the sampled policy can break
the regret bound. All of these adverse cases are retained in the
[complete report](results/analytic_v1/REPORT.md).

Read [THEORY.md](THEORY.md) for the objective, proof, assumptions, prior art,
comparator definitions and conditions required before another experiment.

## Reproduce

Run from the repository root with Python 3.12 or newer. The analysis and exact
solver use only the standard library. Tests also use pytest and SciPy (the
latter independently checks the exact game values using a floating-point LP).
Do not use Python's `-O` flag: verification assertions must remain enabled.

```bash
python -m pytest allowance_scheduler -q
python -m allowance_scheduler.verify
# A separate new directory; published results cannot be overwritten:
python -m allowance_scheduler.run_analysis --output work/allowance_rebuild
```

The saved analysis includes all eight cases, all enumerated policies/outcomes,
exact mixtures and primal/dual certificates, baseline comparisons, 30 formula
checks, 256 matrix-game checks, and 61 policy/scenario executions. No random
sampling noise enters the report: mixture expectations are evaluated exactly.
Source/result hashes and a canonical scientific hash support checkout replay.

Minimal current-observation execution:

```python
from random import Random
from allowance_scheduler.cases import two_future
from allowance_scheduler.core import plan, sample_policy, Controller

problem = two_future()  # declared possible futures, not a realized-future label
planned = plan(problem.scenarios, problem.contract)
index = sample_policy(planned['solution']['weights'], Random(123))  # once
controller = Controller(planned['policies'][index], problem.contract)
action = controller.advance(problem.scenarios[0][0])  # current step only
```

The example seed is for reproduction, not secret randomization. An adversary
that knows the sampled policy is outside the guarantee. In an eventual system,
the environment must be independent of the policy draw. The current interface
also assumes exact current utilities; it is not a viewport prediction model.

## Files

- `core.py`: causal policy enumeration, planning, sampling and protected execution.
- `game.py`: rational support search and independently checkable dual witness.
- `cases.py`, `checks.py`: declared examples and finite verification families.
- `test_scheduler.py`: causality, safety, objective trade-offs and failure tests.
- `run_analysis.py`, `verify.py`: complete result publication and exact replay.

Enumeration is deliberately limited and unsuitable for real-time deployment.
This work establishes a conditional decision rule and testable limitations,
not new minimax theory, general superiority, human QoE benefit or a reason to
relabel previously exposed data as a fresh holdout.
