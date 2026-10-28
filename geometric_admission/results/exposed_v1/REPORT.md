# Geometric viewport admission under the fixed contract

existing 100x100-degree tile-centre angular rectangle; not physical HMD

| Timing | Method | Admitted | Fulfilled in replay | False promises | Precision |
|---|---|---:|---:|---:|---:|
| half_second | certified_planner | 0 | 0 | 0 | undefined |
| half_second | cost_greedy | 28 | 27 | 1 | 0.964 |
| half_second | cost_greedy_certified | 0 | 0 | 0 | undefined |
| half_second | maxmin | 17 | 4 | 13 | 0.235 |
| half_second | maxmin_certified | 0 | 0 | 0 | undefined |
| half_second | point_planner | 28 | 27 | 1 | 0.964 |
| half_second | point_planner_certified | 0 | 0 | 0 | undefined |
| half_second | rolling_nash | 17 | 4 | 13 | 0.235 |
| half_second | rolling_nash_certified | 0 | 0 | 0 | undefined |
| ideal | certified_planner | 0 | 0 | 0 | undefined |
| ideal | cost_greedy | 28 | 27 | 1 | 0.964 |
| ideal | cost_greedy_certified | 0 | 0 | 0 | undefined |
| ideal | maxmin | 17 | 4 | 13 | 0.235 |
| ideal | maxmin_certified | 0 | 0 | 0 | undefined |
| ideal | point_planner | 28 | 27 | 1 | 0.964 |
| ideal | point_planner_certified | 0 | 0 | 0 | undefined |
| ideal | rolling_nash | 17 | 4 | 13 | 0.235 |
| ideal | rolling_nash_certified | 0 | 0 | 0 | undefined |
| unbounded | certified_planner | 0 | 0 | 0 | undefined |

ideal three-way counts: {'impossible': 134, 'abstain': 34}.

half_second three-way counts: {'impossible': 134, 'abstain': 34}.

unbounded three-way counts: {'impossible': 134, 'abstain': 34}.

Complete family: 216 distinct masks. All bounds, extrema and retained controls verified.
