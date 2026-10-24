# Exact allowance-scheduling analysis

**Analytical constructions only. No media, HMD data or new experiments.** All expectations below are over the controller's own episode-level randomization, not a presumed distribution of future scenarios. The future set is supplied, not fitted or calibrated. Only an offline benchmark knows the realized future.

The primary loss is the maximum unpaid fraction across recipients at the deadline. Regret subtracts the future-known optimum for that same scenario. Lower regret does not imply smaller worst absolute loss, higher quality, or zero unpaid debt.

## ambiguous_allowance

One allowance: modest opportunity now; absent or better opportunity later.

Exact minimax expected-regret value: **1/4**; duality gap **0**.

| Rule | Worst expected regret | Worst expected unpaid fraction |
|---|---:|---:|
| mixed_regret | 1/4 | 3/4 |
| deterministic_regret | 1/2 | 1 |
| absolute_minimax | 1/2 | 1/2 |
| stateless_nash | 1/2 | 1 |
| rolling_nash | 1/2 | 1 |
| rolling_maxmin | 1 | 1 |
| max_weight | 1/2 | 1/2 |
| greedy_recovery | 1/2 | 1/2 |

| Future | Rule | Expected unpaid fraction | Expected regret | Expected donor loss | Expected worst post-quality |
|---|---|---:|---:|---|---:|
| opportunity_disappears | mixed_regret | 3/4 | 1/4 | ['0', '1/2'] | 11/4 |
| opportunity_disappears | rolling_nash | 1 | 1/2 | ['0', '0'] | 3 |
| opportunity_disappears | rolling_maxmin | 1 | 1/2 | ['0', '0'] | 3 |
| opportunity_disappears | greedy_recovery | 1/2 | 0 | ['0', '1'] | 5/2 |
| better_later | mixed_regret | 1/4 | 1/4 | ['0', '1'] | 5/2 |
| better_later | rolling_nash | 0 | 0 | ['0', '1'] | 5/2 |
| better_later | rolling_maxmin | 1 | 1 | ['0', '0'] | 3 |
| better_later | greedy_recovery | 1/2 | 1/2 | ['0', '1'] | 5/2 |

Selected policies (chosen once per episode):

- Policy 1, probability 1/2; actions by future: [['baseline', 'baseline'], ['baseline', 'boost']].
- Policy 2, probability 1/2; actions by future: [['boost', 'baseline'], ['boost', 'baseline']].

The differently named future branches above are for reporting only. The executor receives current observations, not those names. Shared observed prefixes have identical actions within each selected causal policy.

## known_disappearance

Singleton declared future: perfect-model illustration, not prediction evidence.

Exact minimax expected-regret value: **0**; duality gap **0**.

| Rule | Worst expected regret | Worst expected unpaid fraction |
|---|---:|---:|
| mixed_regret | 0 | 1/2 |
| deterministic_regret | 0 | 1/2 |
| absolute_minimax | 0 | 1/2 |
| stateless_nash | 1/2 | 1 |
| rolling_nash | 1/2 | 1 |
| rolling_maxmin | 1/2 | 1 |
| max_weight | 0 | 1/2 |
| greedy_recovery | 0 | 1/2 |

| Future | Rule | Expected unpaid fraction | Expected regret | Expected donor loss | Expected worst post-quality |
|---|---|---:|---:|---|---:|
| opportunity_disappears | mixed_regret | 1/2 | 0 | ['0', '1'] | 5/2 |
| opportunity_disappears | rolling_nash | 1 | 1/2 | ['0', '0'] | 3 |
| opportunity_disappears | rolling_maxmin | 1 | 1/2 | ['0', '0'] | 3 |
| opportunity_disappears | greedy_recovery | 1/2 | 0 | ['0', '1'] | 5/2 |

Selected policies (chosen once per episode):

- Policy 1, probability 1; actions by future: [['boost', 'baseline']].

The differently named future branches above are for reporting only. The executor receives current observations, not those names. Shared observed prefixes have identical actions within each selected causal policy.

## known_better_later

Singleton declared future: perfect-model illustration, not prediction evidence.

Exact minimax expected-regret value: **0**; duality gap **0**.

| Rule | Worst expected regret | Worst expected unpaid fraction |
|---|---:|---:|
| mixed_regret | 0 | 0 |
| deterministic_regret | 0 | 0 |
| absolute_minimax | 0 | 0 |
| stateless_nash | 0 | 0 |
| rolling_nash | 0 | 0 |
| rolling_maxmin | 1 | 1 |
| max_weight | 1/2 | 1/2 |
| greedy_recovery | 1/2 | 1/2 |

| Future | Rule | Expected unpaid fraction | Expected regret | Expected donor loss | Expected worst post-quality |
|---|---|---:|---:|---|---:|
| better_later | mixed_regret | 0 | 0 | ['0', '1'] | 5/2 |
| better_later | rolling_nash | 0 | 0 | ['0', '1'] | 5/2 |
| better_later | rolling_maxmin | 1 | 1 | ['0', '0'] | 3 |
| better_later | greedy_recovery | 1/2 | 1/2 | ['0', '1'] | 5/2 |

Selected policies (chosen once per episode):

- Policy 1, probability 1; actions by future: [['baseline', 'boost']].

The differently named future branches above are for reporting only. The executor receives current observations, not those names. Shared observed prefixes have identical actions within each selected causal policy.

## three_period_delayed_revelation

Wait through a dominated early offer; future remains hidden at the second decision.

Exact minimax expected-regret value: **1/4**; duality gap **0**.

| Rule | Worst expected regret | Worst expected unpaid fraction |
|---|---:|---:|
| mixed_regret | 1/4 | 3/4 |
| deterministic_regret | 1/2 | 1 |
| absolute_minimax | 1/2 | 1/2 |
| stateless_nash | 1/2 | 1 |
| rolling_nash | 1/2 | 1 |
| rolling_maxmin | 1 | 1 |
| max_weight | 3/4 | 3/4 |
| greedy_recovery | 3/4 | 3/4 |

| Future | Rule | Expected unpaid fraction | Expected regret | Expected donor loss | Expected worst post-quality |
|---|---|---:|---:|---|---:|
| last_disappears | mixed_regret | 3/4 | 1/4 | ['0', '1/2'] | 17/6 |
| last_disappears | rolling_nash | 1 | 1/2 | ['0', '0'] | 3 |
| last_disappears | rolling_maxmin | 1 | 1/2 | ['0', '0'] | 3 |
| last_disappears | greedy_recovery | 3/4 | 1/4 | ['0', '1'] | 8/3 |
| last_improves | mixed_regret | 1/4 | 1/4 | ['0', '1'] | 8/3 |
| last_improves | rolling_nash | 0 | 0 | ['0', '1'] | 8/3 |
| last_improves | rolling_maxmin | 1 | 1 | ['0', '0'] | 3 |
| last_improves | greedy_recovery | 3/4 | 3/4 | ['0', '1'] | 8/3 |

Selected policies (chosen once per episode):

- Policy 1, probability 1/2; actions by future: [['baseline', 'baseline', 'baseline'], ['baseline', 'baseline', 'boost']].
- Policy 2, probability 1/2; actions by future: [['baseline', 'boost', 'baseline'], ['baseline', 'boost', 'baseline']].

The differently named future branches above are for reporting only. The executor receives current observations, not those names. Shared observed prefixes have identical actions within each selected causal policy.

## two_recipient_opportunities

Either recipient may have the final compensation opportunity.

Exact minimax expected-regret value: **1/4**; duality gap **0**.

| Rule | Worst expected regret | Worst expected unpaid fraction |
|---|---:|---:|
| mixed_regret | 1/4 | 3/4 |
| deterministic_regret | 1/2 | 1 |
| absolute_minimax | 1/2 | 1 |
| stateless_nash | 1/2 | 1 |
| rolling_nash | 1/2 | 1 |
| rolling_maxmin | 1/2 | 1 |
| max_weight | 1/2 | 1 |
| greedy_recovery | 1/2 | 1 |

| Future | Rule | Expected unpaid fraction | Expected regret | Expected donor loss | Expected worst post-quality |
|---|---|---:|---:|---|---:|
| first_only_later | mixed_regret | 3/4 | 1/4 | ['0', '0', '3/2'] | 9/4 |
| first_only_later | rolling_nash | 1 | 1/2 | ['0', '0', '0'] | 3 |
| first_only_later | rolling_maxmin | 1 | 1/2 | ['0', '0', '0'] | 3 |
| first_only_later | greedy_recovery | 1/2 | 0 | ['0', '0', '2'] | 2 |
| second_only_later | mixed_regret | 3/4 | 1/4 | ['0', '0', '3/2'] | 9/4 |
| second_only_later | rolling_nash | 1 | 1/2 | ['0', '0', '0'] | 3 |
| second_only_later | rolling_maxmin | 1 | 1/2 | ['0', '0', '0'] | 3 |
| second_only_later | greedy_recovery | 1 | 1/2 | ['0', '0', '1'] | 5/2 |

Selected policies (chosen once per episode):

- Policy 5, probability 1/2; actions by future: [['help_first', 'baseline'], ['help_first', 'help_second']].
- Policy 10, probability 1/2; actions by future: [['help_second', 'help_first'], ['help_second', 'baseline']].

The differently named future branches above are for reporting only. The executor receives current observations, not those names. Shared observed prefixes have identical actions within each selected causal policy.

## no_donor_allowance

Zero regret need not mean any recovery is possible.

Exact minimax expected-regret value: **0**; duality gap **0**.

| Rule | Worst expected regret | Worst expected unpaid fraction |
|---|---:|---:|
| mixed_regret | 0 | 1 |
| deterministic_regret | 0 | 1 |
| absolute_minimax | 0 | 1 |
| stateless_nash | 0 | 1 |
| rolling_nash | 0 | 1 |
| rolling_maxmin | 0 | 1 |
| max_weight | 0 | 1 |
| greedy_recovery | 0 | 1 |

| Future | Rule | Expected unpaid fraction | Expected regret | Expected donor loss | Expected worst post-quality |
|---|---|---:|---:|---|---:|
| opportunity_disappears | mixed_regret | 1 | 0 | ['0', '0'] | 3 |
| opportunity_disappears | rolling_nash | 1 | 0 | ['0', '0'] | 3 |
| opportunity_disappears | rolling_maxmin | 1 | 0 | ['0', '0'] | 3 |
| opportunity_disappears | greedy_recovery | 1 | 0 | ['0', '0'] | 3 |
| better_later | mixed_regret | 1 | 0 | ['0', '0'] | 3 |
| better_later | rolling_nash | 1 | 0 | ['0', '0'] | 3 |
| better_later | rolling_maxmin | 1 | 0 | ['0', '0'] | 3 |
| better_later | greedy_recovery | 1 | 0 | ['0', '0'] | 3 |

Selected policies (chosen once per episode):

- Policy 0, probability 1; actions by future: [['baseline', 'baseline'], ['baseline', 'baseline']].

The differently named future branches above are for reporting only. The executor receives current observations, not those names. Shared observed prefixes have identical actions within each selected causal policy.

## no_headroom

No recipient surplus exists in any period.

Exact minimax expected-regret value: **0**; duality gap **0**.

| Rule | Worst expected regret | Worst expected unpaid fraction |
|---|---:|---:|
| mixed_regret | 0 | 1 |
| deterministic_regret | 0 | 1 |
| absolute_minimax | 0 | 1 |
| stateless_nash | 0 | 1 |
| rolling_nash | 0 | 1 |
| rolling_maxmin | 0 | 1 |
| max_weight | 0 | 1 |
| greedy_recovery | 0 | 1 |

| Future | Rule | Expected unpaid fraction | Expected regret | Expected donor loss | Expected worst post-quality |
|---|---|---:|---:|---|---:|
| blocked | mixed_regret | 1 | 0 | ['0', '0'] | 3 |
| blocked | rolling_nash | 1 | 0 | ['0', '0'] | 3 |
| blocked | rolling_maxmin | 1 | 0 | ['0', '0'] | 3 |
| blocked | greedy_recovery | 1 | 0 | ['0', '0'] | 3 |

Selected policies (chosen once per episode):

- Policy 0, probability 1; actions by future: [['baseline', 'baseline']].

The differently named future branches above are for reporting only. The executor receives current observations, not those names. Shared observed prefixes have identical actions within each selected causal policy.

## three_possible_future_gains

One common current observation and three possible later gains.

Exact minimax expected-regret value: **1/4**; duality gap **0**.

| Rule | Worst expected regret | Worst expected unpaid fraction |
|---|---:|---:|
| mixed_regret | 1/4 | 3/4 |
| deterministic_regret | 1/2 | 1 |
| absolute_minimax | 1/2 | 1/2 |
| stateless_nash | 3/4 | 1 |
| rolling_nash | 1/2 | 1 |
| rolling_maxmin | 1 | 1 |
| max_weight | 1/2 | 1/2 |
| greedy_recovery | 1/2 | 1/2 |

| Future | Rule | Expected unpaid fraction | Expected regret | Expected donor loss | Expected worst post-quality |
|---|---|---:|---:|---|---:|
| none_later | mixed_regret | 3/4 | 1/4 | ['0', '1/2'] | 11/4 |
| none_later | rolling_nash | 1 | 1/2 | ['0', '0'] | 3 |
| none_later | rolling_maxmin | 1 | 1/2 | ['0', '0'] | 3 |
| none_later | greedy_recovery | 1/2 | 0 | ['0', '1'] | 5/2 |
| moderate_later | mixed_regret | 3/8 | 1/8 | ['0', '1'] | 5/2 |
| moderate_later | rolling_nash | 1/4 | 0 | ['0', '1'] | 5/2 |
| moderate_later | rolling_maxmin | 1 | 3/4 | ['0', '0'] | 3 |
| moderate_later | greedy_recovery | 1/2 | 1/4 | ['0', '1'] | 5/2 |
| large_later | mixed_regret | 1/4 | 1/4 | ['0', '1'] | 5/2 |
| large_later | rolling_nash | 0 | 0 | ['0', '1'] | 5/2 |
| large_later | rolling_maxmin | 1 | 1 | ['0', '0'] | 3 |
| large_later | greedy_recovery | 1/2 | 1/2 | ['0', '1'] | 5/2 |

Selected policies (chosen once per episode):

- Policy 3, probability 1/2; actions by future: [['baseline', 'baseline'], ['baseline', 'boost'], ['baseline', 'boost']].
- Policy 4, probability 1/2; actions by future: [['boost', 'baseline'], ['boost', 'baseline'], ['boost', 'baseline']].

The differently named future branches above are for reporting only. The executor receives current observations, not those names. Shared observed prefixes have identical actions within each selected causal policy.

## Preserved failures and limits

- Misspecified model: declaring only the better-later future gives a zero certificate. When the opportunity actually disappears, realized regret is 1/2 and the model-breach flag is set. The fallback respects the remaining service-loss budget but cannot recover the missed opportunity.
- Coin-observing adversary: on the two-future witness it raises expected regret from the oblivious bound 1/4 to 1/2. The guarantee requires an exogenous future independent of the sampled policy.
- Absolute loss trade-off: on the ambiguous witness the mixed rule has worst expected unpaid fraction 3/4; greedy/absolute-minimax have 1/2. Regret is a distinct objective.
- Zero regret with no allowance/headroom still leaves all event debt unpaid.
- Singletons are perfect-model illustrations, not evidence that a forecast is accurate.

## Verification scope

- 30 exact parameter cases match the two-future probability/bound formula.
- 256 finite games have exact primal/dual certificates.
- 61 executions cover every enumerated policy and in-set scenario in the eight constructions, not just selected winners.
- No p-values, holdout claim, general superiority claim or new minimax theorem is made.
