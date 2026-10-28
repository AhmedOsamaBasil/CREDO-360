# Early commitment exposed-data results

Exploratory progression screen: **False**.

Incremental telemetry and playback timing are simulated. No new holdout, no HMD trial.

## all

| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 0.08 | 92/168 | 0.375974 | 3.9987 | 6.9690 | 0.0000 | 0.1064 | 0/1 |
| completed_mpc | 0.08 | 92/168 | 0.380411 | 3.9981 | 6.9698 | 0.0000 | 0.1146 | 0/1 |
| prefix_cost_greedy | 0.08 | 90/168 | 0.369185 | 3.9972 | 6.9781 | 0.0000 | 0.1116 | 0/1 |
| prefix_greedy | 0.08 | 90/168 | 0.371690 | 4.0072 | 7.0700 | 0.0000 | 0.1103 | 2/2 |
| prefix_nash | 0.08 | 68/168 | 0.521072 | 4.0567 | 8.0462 | 0.0000 | 0.1114 | 2/2 |
| prefix_maxmin | 0.08 | 90/168 | 0.378168 | 4.0176 | 7.1835 | 0.0000 | 0.1100 | 2/2 |
| wait_mpc | 0.08 | 92/168 | 0.375430 | 3.9987 | 16.2200 | 11.4400 | 0.1008 | 1/1 |
| slack_mpc | 0.08 | 92/168 | 0.380411 | 3.9981 | 6.9698 | 0.0000 | 0.1146 | 0/1 |
| prefix_mpc | 0.50 | 92/168 | 0.375603 | 3.9987 | 6.9693 | 0.0000 | 0.1098 | 0/1 |

## v2

| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 0.08 | 64/84 | 0.191474 | 3.5293 | 6.9623 | 0.0000 | 0.1167 | 0/0 |
| completed_mpc | 0.08 | 64/84 | 0.197925 | 3.5293 | 6.9646 | 0.0000 | 0.1236 | 0/0 |
| prefix_cost_greedy | 0.08 | 62/84 | 0.185877 | 3.5264 | 6.9715 | 0.0000 | 0.1239 | 0/0 |
| prefix_greedy | 0.08 | 62/84 | 0.190904 | 3.5456 | 7.1554 | 0.0000 | 0.1213 | 1/1 |
| prefix_nash | 0.08 | 57/84 | 0.343226 | 3.5970 | 8.0113 | 0.0000 | 0.1211 | 1/1 |
| prefix_maxmin | 0.08 | 62/84 | 0.203859 | 3.5663 | 7.3824 | 0.0000 | 0.1208 | 1/1 |
| wait_mpc | 0.08 | 64/84 | 0.192846 | 3.5293 | 16.0097 | 11.4390 | 0.1137 | 1/0 |
| slack_mpc | 0.08 | 64/84 | 0.197925 | 3.5293 | 6.9646 | 0.0000 | 0.1236 | 0/0 |
| prefix_mpc | 0.50 | 64/84 | 0.191468 | 3.5293 | 6.9623 | 0.0000 | 0.1181 | 0/0 |

## v3

| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 0.08 | 28/84 | 0.560475 | 4.4680 | 6.9757 | 0.0000 | 0.0961 | 0/1 |
| completed_mpc | 0.08 | 28/84 | 0.562898 | 4.4668 | 6.9750 | 0.0000 | 0.1056 | 0/1 |
| prefix_cost_greedy | 0.08 | 28/84 | 0.552493 | 4.4679 | 6.9847 | 0.0000 | 0.0993 | 0/1 |
| prefix_greedy | 0.08 | 28/84 | 0.552476 | 4.4689 | 6.9845 | 0.0000 | 0.0993 | 1/1 |
| prefix_nash | 0.08 | 11/84 | 0.698918 | 4.5164 | 8.0811 | 0.0000 | 0.1016 | 1/1 |
| prefix_maxmin | 0.08 | 28/84 | 0.552476 | 4.4689 | 6.9845 | 0.0000 | 0.0993 | 1/1 |
| wait_mpc | 0.08 | 28/84 | 0.558015 | 4.4680 | 16.4304 | 11.4410 | 0.0879 | 0/1 |
| slack_mpc | 0.08 | 28/84 | 0.562898 | 4.4668 | 6.9750 | 0.0000 | 0.1056 | 0/1 |
| prefix_mpc | 0.50 | 28/84 | 0.559738 | 4.4680 | 6.9764 | 0.0000 | 0.1014 | 0/1 |

## BuskingUnderpass05

| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 0.08 | 0/28 | 0.597042 | 4.4820 | 7.1457 | 0.0000 | 0.1428 | 0/0 |
| completed_mpc | 0.08 | 0/28 | 0.597042 | 4.4820 | 7.1457 | 0.0000 | 0.1574 | 0/0 |
| prefix_cost_greedy | 0.08 | 0/28 | 0.600196 | 4.4800 | 7.1457 | 0.0000 | 0.1496 | 0/0 |
| prefix_greedy | 0.08 | 0/28 | 0.600196 | 4.4825 | 7.1457 | 0.0000 | 0.1495 | 0/0 |
| prefix_nash | 0.08 | 0/28 | 0.731653 | 4.5023 | 8.0281 | 0.0000 | 0.1558 | 0/0 |
| prefix_maxmin | 0.08 | 0/28 | 0.600196 | 4.4825 | 7.1457 | 0.0000 | 0.1495 | 0/0 |
| wait_mpc | 0.08 | 0/28 | 0.597042 | 4.4820 | 15.9329 | 11.2993 | 0.1282 | 0/0 |
| slack_mpc | 0.08 | 0/28 | 0.597042 | 4.4820 | 7.1457 | 0.0000 | 0.1574 | 0/0 |
| prefix_mpc | 0.50 | 0/28 | 0.597042 | 4.4820 | 7.1457 | 0.0000 | 0.1506 | 0/0 |

## Cheerleading01

| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 0.08 | 28/28 | 0.343122 | 4.2386 | 7.1996 | 0.0000 | 0.0629 | 0/1 |
| completed_mpc | 0.08 | 28/28 | 0.343122 | 4.2386 | 7.1996 | 0.0000 | 0.0635 | 0/1 |
| prefix_cost_greedy | 0.08 | 28/28 | 0.343122 | 4.2386 | 7.1996 | 0.0000 | 0.0629 | 0/1 |
| prefix_greedy | 0.08 | 28/28 | 0.343071 | 4.2389 | 7.1990 | 0.0000 | 0.0628 | 1/1 |
| prefix_nash | 0.08 | 11/28 | 0.547134 | 4.3338 | 8.7419 | 0.0000 | 0.0641 | 1/1 |
| prefix_maxmin | 0.08 | 28/28 | 0.343071 | 4.2389 | 7.1990 | 0.0000 | 0.0628 | 1/1 |
| wait_mpc | 0.08 | 28/28 | 0.343122 | 4.2386 | 17.7900 | 12.7438 | 0.0557 | 0/1 |
| slack_mpc | 0.08 | 28/28 | 0.343122 | 4.2386 | 7.1996 | 0.0000 | 0.0635 | 0/1 |
| prefix_mpc | 0.50 | 28/28 | 0.343122 | 4.2386 | 7.1996 | 0.0000 | 0.0629 | 0/1 |

## ConferenceParticipant02

| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 0.08 | 0/28 | 0.741260 | 4.6835 | 6.5816 | 0.0000 | 0.0826 | 0/0 |
| completed_mpc | 0.08 | 0/28 | 0.748529 | 4.6799 | 6.5795 | 0.0000 | 0.0958 | 0/0 |
| prefix_cost_greedy | 0.08 | 0/28 | 0.714161 | 4.6852 | 6.6088 | 0.0000 | 0.0855 | 0/0 |
| prefix_greedy | 0.08 | 0/28 | 0.714161 | 4.6852 | 6.6088 | 0.0000 | 0.0855 | 0/0 |
| prefix_nash | 0.08 | 0/28 | 0.817969 | 4.7131 | 7.4733 | 0.0000 | 0.0850 | 0/0 |
| prefix_maxmin | 0.08 | 0/28 | 0.714161 | 4.6852 | 6.6088 | 0.0000 | 0.0855 | 0/0 |
| wait_mpc | 0.08 | 0/28 | 0.733881 | 4.6835 | 15.5682 | 10.2799 | 0.0799 | 0/0 |
| slack_mpc | 0.08 | 0/28 | 0.748529 | 4.6799 | 6.5795 | 0.0000 | 0.0958 | 0/0 |
| prefix_mpc | 0.50 | 0/28 | 0.739051 | 4.6835 | 6.5837 | 0.0000 | 0.0908 | 0/0 |

## ParkFountains01

| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 0.08 | 28/28 | 0.000000 | 3.6934 | 6.6317 | 0.0000 | 0.0624 | 0/0 |
| completed_mpc | 0.08 | 28/28 | 0.000000 | 3.6934 | 6.6317 | 0.0000 | 0.0654 | 0/0 |
| prefix_cost_greedy | 0.08 | 28/28 | 0.000000 | 3.6934 | 6.6317 | 0.0000 | 0.0624 | 0/0 |
| prefix_greedy | 0.08 | 28/28 | 0.000000 | 3.6934 | 6.6317 | 0.0000 | 0.0624 | 0/0 |
| prefix_nash | 0.08 | 27/28 | 0.180162 | 3.8070 | 7.9087 | 0.0000 | 0.0635 | 0/0 |
| prefix_maxmin | 0.08 | 28/28 | 0.013767 | 3.7031 | 6.7299 | 0.0000 | 0.0627 | 0/0 |
| wait_mpc | 0.08 | 28/28 | 0.000000 | 3.6934 | 14.8548 | 11.0609 | 0.0579 | 0/0 |
| slack_mpc | 0.08 | 28/28 | 0.000000 | 3.6934 | 6.6317 | 0.0000 | 0.0654 | 0/0 |
| prefix_mpc | 0.50 | 28/28 | 0.000000 | 3.6934 | 6.6317 | 0.0000 | 0.0628 | 0/0 |

## River01

| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 0.08 | 28/28 | 0.051867 | 2.6587 | 7.2689 | 0.0000 | 0.1037 | 0/0 |
| completed_mpc | 0.08 | 28/28 | 0.071237 | 2.6587 | 7.2757 | 0.0000 | 0.1139 | 0/0 |
| prefix_cost_greedy | 0.08 | 28/28 | 0.000000 | 2.6587 | 7.2780 | 0.0000 | 0.1097 | 0/0 |
| prefix_greedy | 0.08 | 28/28 | 0.015304 | 2.7160 | 7.8329 | 0.0000 | 0.1019 | 1/1 |
| prefix_nash | 0.08 | 25/28 | 0.153382 | 2.7696 | 8.4157 | 0.0000 | 0.1035 | 1/1 |
| prefix_maxmin | 0.08 | 28/28 | 0.040402 | 2.7687 | 8.4157 | 0.0000 | 0.1002 | 1/1 |
| wait_mpc | 0.08 | 28/28 | 0.056001 | 2.6587 | 17.1149 | 12.0263 | 0.1031 | 1/0 |
| slack_mpc | 0.08 | 28/28 | 0.071237 | 2.6587 | 7.2757 | 0.0000 | 0.1139 | 0/0 |
| prefix_mpc | 0.50 | 28/28 | 0.051867 | 2.6587 | 7.2689 | 0.0000 | 0.1040 | 0/0 |

## Train01

| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 0.08 | 8/28 | 0.522554 | 4.2357 | 6.9863 | 0.0000 | 0.1839 | 0/0 |
| completed_mpc | 0.08 | 8/28 | 0.522537 | 4.2357 | 6.9863 | 0.0000 | 0.1914 | 0/0 |
| prefix_cost_greedy | 0.08 | 6/28 | 0.557631 | 4.2271 | 7.0049 | 0.0000 | 0.1996 | 0/0 |
| prefix_greedy | 0.08 | 6/28 | 0.557409 | 4.2273 | 7.0017 | 0.0000 | 0.1996 | 0/0 |
| prefix_nash | 0.08 | 5/28 | 0.696134 | 4.2144 | 7.7094 | 0.0000 | 0.1964 | 0/0 |
| prefix_maxmin | 0.08 | 6/28 | 0.557409 | 4.2273 | 7.0017 | 0.0000 | 0.1996 | 0/0 |
| wait_mpc | 0.08 | 8/28 | 0.522537 | 4.2357 | 16.0592 | 11.2299 | 0.1801 | 0/0 |
| slack_mpc | 0.08 | 8/28 | 0.522537 | 4.2357 | 6.9863 | 0.0000 | 0.1914 | 0/0 |
| prefix_mpc | 0.50 | 8/28 | 0.522537 | 4.2357 | 6.9863 | 0.0000 | 0.1876 | 0/0 |

## Failed predeclared checks

- v2_gain_prefix_cost_greedy
- v2_gain_prefix_greedy
- v2_quality_prefix_nash
- v2_quality_prefix_maxmin
- v2_gain_historical_cost_greedy
- v2_gain_historical_greedy_recovery
- v2_gain_historical_knn_recovery
- v2_gain_historical_persistence_mpc
- v2_quality_historical_rolling_maxmin
- v2_quality_historical_rolling_nash
- v2_gain_historical_unconditional_mpc
- v3_gain_completed_mpc
- v3_gain_prefix_cost_greedy
- v3_gain_prefix_greedy
- v3_quality_prefix_nash
- v3_gain_prefix_maxmin
- v3_gain_historical_cost_greedy
- v3_gain_historical_greedy_recovery
- v3_gain_historical_knn_recovery
- v3_gain_historical_persistence_mpc
- v3_gain_historical_rolling_maxmin
- v3_gain_historical_unconditional_mpc
- v3_recipient_floor_violations
