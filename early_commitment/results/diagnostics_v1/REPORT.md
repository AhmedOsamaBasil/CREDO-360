# Early-commitment mechanism diagnosis

Post-hoc descriptive checks; no parameter changes or independent confirmation.

Exploratory progression screen: **False**.

| Group | Comparator (delay s) | Unpaid delta | Worst-quality delta | Stall delta s | Half-count delta |
|---|---|---:|---:|---:|---:|
| all | completed_mpc (0.08) | -0.004437 | +0.000603 | -0.000791 | +0 |
| all | prefix_cost_greedy (0.08) | +0.006789 | +0.001481 | -0.009134 | +2 |
| all | prefix_nash (0.08) | -0.145098 | -0.058037 | -1.077222 | +24 |
| all | prefix_maxmin (0.08) | -0.002193 | -0.018961 | -0.214486 | +2 |
| all | wait_mpc (0.08) | +0.000544 | +0.000000 | -9.251033 | +0 |
| all | prefix_mpc (0.5) | +0.000371 | +0.000000 | -0.000353 | +0 |
| v2 | completed_mpc (0.08) | -0.006451 | +0.000000 | -0.002288 | +0 |
| v2 | prefix_cost_greedy (0.08) | +0.005597 | +0.002860 | -0.009200 | +2 |
| v2 | prefix_nash (0.08) | -0.151752 | -0.067693 | -1.048969 | +7 |
| v2 | prefix_maxmin (0.08) | -0.012385 | -0.037051 | -0.420112 | +2 |
| v2 | wait_mpc (0.08) | -0.001372 | +0.000000 | -9.047365 | +0 |
| v2 | prefix_mpc (0.5) | +0.000006 | +0.000000 | +0.000000 | +0 |
| v3 | completed_mpc (0.08) | -0.002423 | +0.001205 | +0.000706 | +0 |
| v3 | prefix_cost_greedy (0.08) | +0.007982 | +0.000101 | -0.009068 | +0 |
| v3 | prefix_nash (0.08) | -0.138444 | -0.048381 | -1.105476 | +17 |
| v3 | prefix_maxmin (0.08) | +0.007999 | -0.000872 | -0.008861 | +0 |
| v3 | wait_mpc (0.08) | +0.002460 | +0.000000 | -9.454702 | +0 |
| v3 | prefix_mpc (0.5) | +0.000736 | +0.000000 | -0.000706 | +0 |
| BuskingUnderpass05 | completed_mpc (0.08) | +0.000000 | +0.000000 | +0.000000 | +0 |
| BuskingUnderpass05 | prefix_cost_greedy (0.08) | -0.003154 | +0.002000 | +0.000000 | +0 |
| BuskingUnderpass05 | prefix_nash (0.08) | -0.134610 | -0.020330 | -0.882396 | +0 |
| BuskingUnderpass05 | prefix_maxmin (0.08) | -0.003154 | -0.000554 | +0.000000 | +0 |
| BuskingUnderpass05 | wait_mpc (0.08) | +0.000000 | +0.000000 | -8.787202 | +0 |
| BuskingUnderpass05 | prefix_mpc (0.5) | +0.000000 | +0.000000 | +0.000000 | +0 |
| Cheerleading01 | completed_mpc (0.08) | +0.000000 | +0.000000 | +0.000000 | +0 |
| Cheerleading01 | prefix_cost_greedy (0.08) | +0.000000 | +0.000000 | +0.000000 | +0 |
| Cheerleading01 | prefix_nash (0.08) | -0.204012 | -0.095259 | -1.542325 | +17 |
| Cheerleading01 | prefix_maxmin (0.08) | +0.000051 | -0.000366 | +0.000621 | +0 |
| Cheerleading01 | wait_mpc (0.08) | +0.000000 | +0.000000 | -10.590351 | +0 |
| Cheerleading01 | prefix_mpc (0.5) | +0.000000 | +0.000000 | +0.000000 | +0 |
| ConferenceParticipant02 | completed_mpc (0.08) | -0.007270 | +0.003616 | +0.002117 | +0 |
| ConferenceParticipant02 | prefix_cost_greedy (0.08) | +0.027098 | -0.001696 | -0.027203 | +0 |
| ConferenceParticipant02 | prefix_nash (0.08) | -0.076709 | -0.029554 | -0.891708 | +0 |
| ConferenceParticipant02 | prefix_maxmin (0.08) | +0.027098 | -0.001696 | -0.027203 | +0 |
| ConferenceParticipant02 | wait_mpc (0.08) | +0.007379 | +0.000000 | -8.986552 | +0 |
| ConferenceParticipant02 | prefix_mpc (0.5) | +0.002209 | +0.000000 | -0.002117 | +0 |
| ParkFountains01 | completed_mpc (0.08) | +0.000000 | +0.000000 | +0.000000 | +0 |
| ParkFountains01 | prefix_cost_greedy (0.08) | +0.000000 | +0.000000 | +0.000000 | +0 |
| ParkFountains01 | prefix_nash (0.08) | -0.180162 | -0.113598 | -1.277075 | +1 |
| ParkFountains01 | prefix_maxmin (0.08) | -0.013767 | -0.009661 | -0.098237 | +0 |
| ParkFountains01 | wait_mpc (0.08) | +0.000000 | +0.000000 | -8.223133 | +0 |
| ParkFountains01 | prefix_mpc (0.5) | +0.000000 | +0.000000 | +0.000000 | +0 |
| River01 | completed_mpc (0.08) | -0.019370 | +0.000000 | -0.006864 | +0 |
| River01 | prefix_cost_greedy (0.08) | +0.051867 | +0.000000 | -0.009079 | +0 |
| River01 | prefix_nash (0.08) | -0.101515 | -0.110813 | -1.146776 | +3 |
| River01 | prefix_maxmin (0.08) | +0.011465 | -0.109911 | -1.146776 | +0 |
| River01 | wait_mpc (0.08) | -0.004134 | +0.000000 | -9.846064 | +0 |
| River01 | prefix_mpc (0.5) | +0.000000 | +0.000000 | +0.000000 | +0 |
| Train01 | completed_mpc (0.08) | +0.000018 | +0.000000 | +0.000000 | +0 |
| Train01 | prefix_cost_greedy (0.08) | -0.035077 | +0.008580 | -0.018523 | +2 |
| Train01 | prefix_nash (0.08) | -0.173579 | +0.021330 | -0.723055 | +3 |
| Train01 | prefix_maxmin (0.08) | -0.034855 | +0.008420 | -0.015322 | +2 |
| Train01 | wait_mpc (0.08) | +0.000018 | +0.000000 | -9.072897 | +0 |
| Train01 | prefix_mpc (0.5) | +0.000018 | +0.000000 | +0.000000 | +0 |

All deltas are primary prefix_mpc minus comparator. Lower unpaid/stall is better. These are descriptive fixed-catalogue comparisons, not independent-subject inference.

Changed actions versus completed-only by decision: [0, 26, 14, 15] (168 per decision).
Second-decision new samples: {'min': 0, 'median': 6.0, 'max': 7, 'with_any': 284, 'total': 336}.
Actual primary floor losses (0.001 index units): [{'key': 'v3:Cheerleading01:26:25', 'segment': 2, 'user_role': 0, 'loss_units': 1}].

| Policy | Decision 1 lost fraction | Decision 2 | Decision 3 | Decision 4 | Episodes with loss |
|---|---:|---:|---:|---:|---:|
| prefix_mpc | 0.006975 | 0.016301 | 0.007664 | 0.000040 | 73 |
| completed_mpc | 0.006975 | 0.021870 | 0.006535 | 0.000037 | 76 |
| prefix_cost_greedy | 0.003017 | 0.021135 | 0.000000 | 0.000040 | 68 |

Losses are conditional future-known structural opportunity, not causally available information. Their sum telescopes to the structural-optimum repayment gap.
All 1008 completed segment projections exactly match the previous reconstructed rounded feedback.
