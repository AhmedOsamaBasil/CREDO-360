# Analytical recovery objective and exact counterexamples

This package defines **event-local service compensation under an explicit
donor-impact budget**. It is an analytical reference model, not the next
successful CREDO controller. No new data or empirical experiments are used.
It does not revise any previous failed result or the manuscript.

Start with [THEORY.md](THEORY.md) for definitions, proofs, counterexamples and
primary prior-art references. The saved [exact report](results/analytic_v1/REPORT.md)
contains every constructed case, including ties, impossibility and failures.

## Main findings

1. Recovery is precisely defined as delivered utility above the present
   reference paying an immutable, event-local loss. No prepayment, expiry or
   feasibility relabeling counts as payment. Unpaid loss remains visible.
2. Without spare capacity or permission to reduce other users' service,
   a Pareto-efficient reference leaves no compensation opportunity.
3. Rolling Nash/max-min can forget an unpaid old event. An event ledger can
   repay it, but may reduce post-event worst-user quality. That is a different
   service contract, not universal fairness improvement.
4. Greedy repayment is optimal for one recipient with independent opportunities
   and nonbinding cumulative donor limits. The exact formula is checked on
   480 small rational instances.
5. Multiple recipients and scarce donor budgets invalidate the generalization.
   Concrete cases show greedy recovery losing to debt-weighted priority,
   rolling Nash or the offline oracle on the recovery endpoint itself.
6. Two indistinguishable current states can need opposite first actions under
   different futures. No causal policy can always match that future-known
   oracle without further assumptions.

These are elementary analytical results and executable specifications, not
claimed novel theorems. Compensation and graceful degradation already appear
in wireless fair queueing. Relevant sources are linked in `THEORY.md`.

## Reproduction

The reference implementation uses only Python's standard library and exact
`fractions.Fraction` arithmetic. Tests additionally require pytest. No GPU,
new content, media encoding, HMD traces, fitted model or network connection
is needed.

```bash
python -m pytest recovery_objective -q
python -m recovery_objective.verify
```

To regenerate into a new directory without overwriting the saved evidence:

```bash
python -m recovery_objective.run_analysis --output work/recovery_objective_replication
python -m recovery_objective.verify --output work/recovery_objective_replication
```

The verifier regenerates every witness, exhaustive oracle and finite check,
and checks hashes and the exact report. Scientific rational values are
platform-independent; separate Windows/Linux verification reports record
the actual environments. No confidence intervals are computed for hand-made
mathematical instances.

## Files and boundaries

- `core.py`: event loss, protected action sets, delivered-credit accounting,
  five causal reference rules and an exhaustive future-known oracle.
- `cases.py`: nine declared analytical witnesses, including a matching-prefix
  pair proving why future-blind oracle optimality is unavailable.
- `checks.py`: 480 one-recipient identities and 24 multiple-recipient cases.
- `test_core.py`: exact accounting, protection, causal inputs and explicit
  positive, null and adverse outcomes.
- `results/analytic_v1/`: all exact results, source hashes, readable report
  and cross-platform verification.

All policies share current quality information and the same protected feasible
action set. Only the explicitly marked offline oracle sees the future. The
model uses equal-duration periods, positive abstract utility, a single event
and small finite joint action sets. It does not model subjective QoE, adaptive
uncertainty, session arrivals, overlapping events or playback stalls. Its
quality-protection budget is not automatically a stall guarantee. Any empirical
extension requires a fixed application utility, causal baseline/reference,
explicit harm budget, forecast assumptions and stronger prior-art comparisons.
