# Exact analytical results

**Constructed witnesses and finite model checks, not experimental validation.** No content, HMD trace, new holdout or GPU experiment is used. The offline oracle knows the future; online rules do not. All values are exact rational numbers.

The objective is the largest fraction of original event loss still unpaid at the declared deadline (smaller is better), with total unpaid fractions as a secondary criterion. Donor harm is reported, not hidden as free recovery. See `THEORY.md` for proofs, assumptions and prior art.

## forgotten_event

Finite-window averaging forgets an unresolved old event.

Initial debt: ['2', '0']. Total donor allowances: ['0', '2'].

| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |
|---|---|---:|---:|---|---:|---|
| stateless_nash | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_nash | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_maxmin | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| max_weight | compensate, compensate | 0 | 0 | ['0', '2'] | 2 | True |
| greedy_recovery | compensate, compensate | 0 | 0 | ['0', '2'] | 2 | True |
| offline_oracle | compensate, compensate | 0 | 0 | ['0', '2'] | 2 | True |

## recent_event

Rolling equalization can repay part of a recent loss but optimize a different endpoint.

Initial debt: ['2', '0']. Total donor allowances: ['0', '2'].

| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |
|---|---|---:|---:|---|---:|---|
| stateless_nash | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_nash | compensate, baseline | 1/2 | 1/2 | ['0', '1'] | 5/2 | False |
| rolling_maxmin | compensate, baseline | 1/2 | 1/2 | ['0', '1'] | 5/2 | False |
| max_weight | compensate, compensate | 0 | 0 | ['0', '2'] | 2 | True |
| greedy_recovery | compensate, compensate | 0 | 0 | ['0', '2'] | 2 | True |
| offline_oracle | compensate, compensate | 0 | 0 | ['0', '2'] | 2 | True |

## zero_harm_allowance

No compensation without slack or permitted donor loss on this frontier.

Initial debt: ['2', '0']. Total donor allowances: ['0', '0'].

| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |
|---|---|---:|---:|---|---:|---|
| stateless_nash | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_nash | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_maxmin | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| max_weight | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| greedy_recovery | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| offline_oracle | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |

## no_recipient_headroom

Inability to deliver excess does not erase outstanding event loss.

Initial debt: ['2', '0']. Total donor allowances: ['0', '2'].

| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |
|---|---|---:|---:|---|---:|---|
| stateless_nash | help_other, help_other | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_nash | help_other, help_other | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_maxmin | help_other, help_other | 1 | 1 | ['0', '0'] | 3 | False |
| max_weight | help_other, help_other | 1 | 1 | ['0', '0'] | 3 | False |
| greedy_recovery | help_other, help_other | 1 | 1 | ['0', '0'] | 3 | False |
| offline_oracle | help_other, help_other | 1 | 1 | ['0', '0'] | 3 | False |

## shared_success_with_slack

Both direct rolling rules and recovery can fully compensate; no exclusive advantage.

Initial debt: ['1', '1']. Total donor allowances: ['0', '0'].

| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |
|---|---|---:|---:|---|---:|---|
| stateless_nash | help_first, help_first | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_nash | help_first, help_second | 0 | 0 | ['0', '0'] | 7/2 | True |
| rolling_maxmin | help_first, help_second | 0 | 0 | ['0', '0'] | 7/2 | True |
| max_weight | help_first, help_second | 0 | 0 | ['0', '0'] | 7/2 | True |
| greedy_recovery | help_first, help_second | 0 | 0 | ['0', '0'] | 7/2 | True |
| offline_oracle | help_first, help_second | 0 | 0 | ['0', '0'] | 7/2 | True |

## future_opportunity_trap

Myopic normalized recovery loses to a known-future oracle and debt-weighted control.

Initial debt: ['2', '1', '0']. Total donor allowances: ['0', '0', '2'].

| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |
|---|---|---:|---:|---|---:|---|
| stateless_nash | baseline, baseline | 1 | 2 | ['0', '0', '0'] | 3 | False |
| rolling_nash | baseline, baseline | 1 | 2 | ['0', '0', '0'] | 3 | False |
| rolling_maxmin | baseline, baseline | 1 | 2 | ['0', '0', '0'] | 3 | False |
| max_weight | help_first, help_second | 1/2 | 1/2 | ['0', '0', '2'] | 2 | False |
| greedy_recovery | help_second, baseline | 1 | 1 | ['0', '0', '1'] | 5/2 | False |
| offline_oracle | help_first, help_second | 1/2 | 1/2 | ['0', '0', '2'] | 2 | False |

## donor_budget_trap

Spending a scarce donor budget early makes greedy recovery worse than rolling Nash.

Initial debt: ['2', '0']. Total donor allowances: ['0', '1'].

| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |
|---|---|---:|---:|---|---:|---|
| stateless_nash | baseline, later_compensation | 0 | 0 | ['0', '1'] | 5/2 | True |
| rolling_nash | baseline, later_compensation | 0 | 0 | ['0', '1'] | 5/2 | True |
| rolling_maxmin | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| max_weight | compensate, baseline | 1/2 | 1/2 | ['0', '1'] | 5/2 | False |
| greedy_recovery | compensate, baseline | 1/2 | 1/2 | ['0', '1'] | 5/2 | False |
| offline_oracle | baseline, later_compensation | 0 | 0 | ['0', '1'] | 5/2 | True |

## opportunity_disappears

Same first step and budget, but waiting now loses the only compensation opportunity.

Initial debt: ['2', '0']. Total donor allowances: ['0', '1'].

| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |
|---|---|---:|---:|---|---:|---|
| stateless_nash | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_nash | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_maxmin | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| max_weight | compensate, baseline | 1/2 | 1/2 | ['0', '1'] | 5/2 | False |
| greedy_recovery | compensate, baseline | 1/2 | 1/2 | ['0', '1'] | 5/2 | False |
| offline_oracle | compensate, baseline | 1/2 | 1/2 | ['0', '1'] | 5/2 | False |

## quality_ceiling

A reference already at maximum quality cannot be compensated by more quality.

Initial debt: ['2', '0']. Total donor allowances: ['0', '2'].

| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |
|---|---|---:|---:|---|---:|---|
| stateless_nash | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_nash | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| rolling_maxmin | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| max_weight | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| greedy_recovery | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |
| offline_oracle | baseline, baseline | 1 | 1 | ['0', '0'] | 3 | False |

## Finite exact checks

- Single-recipient family: 480 cases match the closed-form repayment bound and exhaustive oracle exactly.
- Multiple-recipient opportunity family: 24 cases check conservation, protection and comparisons with the offline optimum.
- These are enumerated mathematical instances, not independent observations or a representative workload distribution.

| Rule | Equal terminal oracle | Strictly worse terminal oracle |
|---|---:|---:|
| stateless_nash | 0 | 24 |
| rolling_nash | 0 | 24 |
| rolling_maxmin | 0 | 24 |
| max_weight | 12 | 12 |
| greedy_recovery | 12 | 12 |

## Conclusion

The event-local objective is distinguishable from rolling average fairness. It is not uniformly better: explicit donor sacrifice is required without spare capacity, all methods can be unable to pay, simple controls sometimes tie, and greedy recovery can lose even on its own endpoint. The conditional single-user proof does not establish general online optimality or new algorithmic novelty. No empirical campaign or manuscript update follows automatically.
