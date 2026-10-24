# Causal current-quality exposed replay

Completed-feedback-only estimates; simulated fluid timing; no new holdout.

Exploratory practical gate passed: **False**.

## all

| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| knn_recovery | 90/168 | 0.371245 | 3.9971 | 4.1585 | 6.9830 | 0.1142 | 1/1 |
| greedy_recovery | 90/168 | 0.370941 | 4.0052 | 4.1644 | 7.0538 | 0.1162 | 2/2 |
| cost_greedy | 90/168 | 0.369140 | 3.9972 | 4.1618 | 6.9748 | 0.1161 | 0/1 |
| rolling_nash | 89/168 | 0.393596 | 4.0231 | 4.1644 | 7.3233 | 0.1166 | 2/2 |
| rolling_maxmin | 90/168 | 0.376229 | 4.0211 | 4.1647 | 7.2320 | 0.1161 | 2/2 |
| persistence_mpc | 90/168 | 0.371854 | 3.9969 | 4.1577 | 6.9760 | 0.1160 | 1/1 |
| unconditional_mpc | 90/168 | 0.373381 | 3.9966 | 4.1577 | 6.9866 | 0.1158 | 1/1 |

## v2

| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| knn_recovery | 62/84 | 0.186313 | 3.5264 | 3.7300 | 6.9902 | 0.1259 | 1/0 |
| greedy_recovery | 62/84 | 0.189406 | 3.5415 | 3.7404 | 7.1230 | 0.1255 | 1/1 |
| cost_greedy | 62/84 | 0.185803 | 3.5264 | 3.7357 | 6.9649 | 0.1254 | 0/0 |
| rolling_nash | 62/84 | 0.199982 | 3.5733 | 3.7410 | 7.4795 | 0.1253 | 1/1 |
| rolling_maxmin | 62/84 | 0.199982 | 3.5733 | 3.7410 | 7.4795 | 0.1253 | 1/1 |
| persistence_mpc | 62/84 | 0.186313 | 3.5264 | 3.7289 | 6.9891 | 0.1259 | 1/0 |
| unconditional_mpc | 62/84 | 0.185803 | 3.5264 | 3.7298 | 6.9928 | 0.1260 | 1/0 |

## v3

| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| knn_recovery | 28/84 | 0.556178 | 4.4677 | 4.5870 | 6.9757 | 0.1025 | 0/1 |
| greedy_recovery | 28/84 | 0.552476 | 4.4689 | 4.5884 | 6.9845 | 0.1068 | 1/1 |
| cost_greedy | 28/84 | 0.552476 | 4.4679 | 4.5879 | 6.9847 | 0.1068 | 0/1 |
| rolling_nash | 27/84 | 0.587210 | 4.4729 | 4.5877 | 7.1670 | 0.1079 | 1/1 |
| rolling_maxmin | 28/84 | 0.552476 | 4.4689 | 4.5884 | 6.9845 | 0.1068 | 1/1 |
| persistence_mpc | 28/84 | 0.557394 | 4.4674 | 4.5865 | 6.9629 | 0.1061 | 0/1 |
| unconditional_mpc | 28/84 | 0.560959 | 4.4668 | 4.5855 | 6.9803 | 0.1057 | 0/1 |

## BuskingUnderpass05

| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| knn_recovery | 0/28 | 0.592393 | 4.4827 | 4.5872 | 7.1401 | 0.1467 | 0/0 |
| greedy_recovery | 0/28 | 0.600196 | 4.4825 | 4.5859 | 7.1457 | 0.1570 | 0/0 |
| cost_greedy | 0/28 | 0.600196 | 4.4800 | 4.5844 | 7.1457 | 0.1570 | 0/0 |
| rolling_nash | 0/28 | 0.624440 | 4.4886 | 4.5865 | 7.4105 | 0.1579 | 0/0 |
| rolling_maxmin | 0/28 | 0.600196 | 4.4825 | 4.5859 | 7.1457 | 0.1570 | 0/0 |
| persistence_mpc | 0/28 | 0.600196 | 4.4800 | 4.5844 | 7.1457 | 0.1570 | 0/0 |
| unconditional_mpc | 0/28 | 0.603826 | 4.4802 | 4.5837 | 7.1401 | 0.1574 | 0/0 |

## Cheerleading01

| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| knn_recovery | 28/28 | 0.343071 | 4.2386 | 4.4105 | 7.1996 | 0.0765 | 0/1 |
| greedy_recovery | 28/28 | 0.343071 | 4.2389 | 4.4107 | 7.1990 | 0.0766 | 1/1 |
| cost_greedy | 28/28 | 0.343071 | 4.2386 | 4.4105 | 7.1996 | 0.0765 | 0/1 |
| rolling_nash | 27/28 | 0.354801 | 4.2426 | 4.4104 | 7.2898 | 0.0771 | 1/1 |
| rolling_maxmin | 28/28 | 0.343071 | 4.2389 | 4.4107 | 7.1990 | 0.0766 | 1/1 |
| persistence_mpc | 28/28 | 0.343071 | 4.2386 | 4.4105 | 7.1996 | 0.0765 | 0/1 |
| unconditional_mpc | 28/28 | 0.343071 | 4.2386 | 4.4105 | 7.1996 | 0.0765 | 0/1 |

## ConferenceParticipant02

| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| knn_recovery | 0/28 | 0.733070 | 4.6817 | 4.7633 | 6.5874 | 0.0841 | 0/0 |
| greedy_recovery | 0/28 | 0.714161 | 4.6852 | 4.7687 | 6.6088 | 0.0870 | 0/0 |
| cost_greedy | 0/28 | 0.714161 | 4.6852 | 4.7687 | 6.6088 | 0.0870 | 0/0 |
| rolling_nash | 0/28 | 0.782391 | 4.6875 | 4.7662 | 6.8009 | 0.0887 | 0/0 |
| rolling_maxmin | 0/28 | 0.714161 | 4.6852 | 4.7687 | 6.6088 | 0.0870 | 0/0 |
| persistence_mpc | 0/28 | 0.728915 | 4.6835 | 4.7645 | 6.5433 | 0.0846 | 0/0 |
| unconditional_mpc | 0/28 | 0.735980 | 4.6817 | 4.7624 | 6.6012 | 0.0832 | 0/0 |

## ParkFountains01

| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| knn_recovery | 28/28 | 0.000000 | 3.6934 | 3.9478 | 6.6317 | 0.0491 | 0/0 |
| greedy_recovery | 28/28 | 0.000000 | 3.6934 | 3.9478 | 6.6317 | 0.0491 | 0/0 |
| cost_greedy | 28/28 | 0.000000 | 3.6934 | 3.9478 | 6.6317 | 0.0491 | 0/0 |
| rolling_nash | 28/28 | 0.006735 | 3.7033 | 3.9481 | 6.7299 | 0.0490 | 0/0 |
| rolling_maxmin | 28/28 | 0.006735 | 3.7033 | 3.9481 | 6.7299 | 0.0490 | 0/0 |
| persistence_mpc | 28/28 | 0.000000 | 3.6934 | 3.9478 | 6.6317 | 0.0491 | 0/0 |
| unconditional_mpc | 28/28 | 0.000000 | 3.6934 | 3.9478 | 6.6317 | 0.0491 | 0/0 |

## River01

| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| knn_recovery | 28/28 | 0.001530 | 2.6587 | 2.8823 | 7.3353 | 0.0897 | 1/0 |
| greedy_recovery | 28/28 | 0.010808 | 2.7039 | 2.9136 | 7.7358 | 0.0883 | 1/1 |
| cost_greedy | 28/28 | 0.000000 | 2.6587 | 2.8993 | 7.2594 | 0.0882 | 0/0 |
| rolling_nash | 28/28 | 0.035803 | 2.7893 | 2.9150 | 8.7070 | 0.0879 | 1/1 |
| rolling_maxmin | 28/28 | 0.035803 | 2.7893 | 2.9150 | 8.7070 | 0.0879 | 1/1 |
| persistence_mpc | 28/28 | 0.001530 | 2.6587 | 2.8790 | 7.3318 | 0.0895 | 1/0 |
| unconditional_mpc | 28/28 | 0.000000 | 2.6587 | 2.8817 | 7.3432 | 0.0898 | 1/0 |

## Train01

| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |
|---|---:|---:|---:|---:|---:|---:|---:|
| knn_recovery | 6/28 | 0.557409 | 4.2272 | 4.3598 | 7.0037 | 0.2390 | 0/0 |
| greedy_recovery | 6/28 | 0.557409 | 4.2273 | 4.3599 | 7.0017 | 0.2390 | 0/0 |
| cost_greedy | 6/28 | 0.557409 | 4.2272 | 4.3598 | 7.0037 | 0.2390 | 0/0 |
| rolling_nash | 6/28 | 0.557409 | 4.2273 | 4.3599 | 7.0017 | 0.2390 | 0/0 |
| rolling_maxmin | 6/28 | 0.557409 | 4.2273 | 4.3599 | 7.0017 | 0.2390 | 0/0 |
| persistence_mpc | 6/28 | 0.557409 | 4.2272 | 4.3598 | 7.0037 | 0.2390 | 0/0 |
| unconditional_mpc | 6/28 | 0.557409 | 4.2272 | 4.3598 | 7.0037 | 0.2390 | 0/0 |

Predicted floors are not certified actual-quality guarantees. Minimum rung2, actual MP4 bytes and delayed feedback differ from the prior oracle-current audit. Do not attribute a cross-study difference solely to prediction.
