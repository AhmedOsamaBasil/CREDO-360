# Feasibility-based admission under the fixed contract

Conditional engineering certificates; exposed data, not fresh confirmation.

| Timing | Method | Admit | Success | False promises | Precision | Offline feasible |
|---|---|---:|---:|---:|---:|---:|
| half_second | certified_planner | 0 | 0 | 0 | undefined | 27 |
| half_second | cost_greedy | 28 | 27 | 1 | 0.964 | 27 |
| half_second | cost_greedy_certified | 0 | 0 | 0 | undefined | 27 |
| half_second | maxmin | 17 | 4 | 13 | 0.235 | 27 |
| half_second | maxmin_certified | 0 | 0 | 0 | undefined | 27 |
| half_second | point_planner | 28 | 27 | 1 | 0.964 | 27 |
| half_second | point_planner_certified | 0 | 0 | 0 | undefined | 27 |
| half_second | rolling_nash | 17 | 4 | 13 | 0.235 | 27 |
| half_second | rolling_nash_certified | 0 | 0 | 0 | undefined | 27 |
| ideal | certified_planner | 0 | 0 | 0 | undefined | 27 |
| ideal | cost_greedy | 28 | 27 | 1 | 0.964 | 27 |
| ideal | cost_greedy_certified | 0 | 0 | 0 | undefined | 27 |
| ideal | maxmin | 17 | 4 | 13 | 0.235 | 27 |
| ideal | maxmin_certified | 0 | 0 | 0 | undefined | 27 |
| ideal | point_planner | 28 | 27 | 1 | 0.964 | 27 |
| ideal | point_planner_certified | 0 | 0 | 0 | undefined | 27 |
| ideal | rolling_nash | 17 | 4 | 13 | 0.235 | 27 |
| ideal | rolling_nash_certified | 0 | 0 | 0 | undefined | 27 |
| unbounded | certified_planner | 0 | 0 | 0 | undefined | None |

ideal three-way decisions: {'abstain': 56, 'impossible': 112}.

half_second three-way decisions: {'abstain': 56, 'impossible': 112}.

unbounded three-way decisions: {'abstain': 56, 'impossible': 112}.

Prior execution-envelope backcheck: 152/152 segments within 0.5s; maximum 0.178511786s. This is not a universal upper bound.
