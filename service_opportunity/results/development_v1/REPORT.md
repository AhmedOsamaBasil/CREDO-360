# Controlled service and causal opportunity development

Exposed data only; oracle-current viewport qualities. No independent confirmation or human QoE claim.

## Controlled service probes

{
  "controlled_contract_pass": true,
  "negative_control_detected": true,
  "nominal_pass_count": 12,
  "negative_miss_count": 3,
  "nominal_max_seconds": 8.506160811,
  "nominal_min_seconds": 8.378695141999998,
  "negative_min_seconds": 12.665654203999992,
  "field_available_capacity_validated": false
}

Development progression: **True**. All individual checks are in the result artifact.

## all

| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1/2 | knn_mpc | 56/168 | 0.572135 | 3.9934 | 4.0853 | 0.3383 | 57/1 |
| 1/2 | rolling_nash | 46/168 | 0.649550 | 4.0076 | 4.0908 | n/a | 0/0 |
| 1/2 | rolling_maxmin | 56/168 | 0.573641 | 3.9931 | 4.0852 | n/a | 0/0 |
| 1/2 | greedy_recovery | 56/168 | 0.573641 | 3.9931 | 4.0852 | n/a | 0/0 |
| 1/2 | persistence_mpc | 56/168 | 0.603969 | 3.9894 | 4.0784 | 0.1469 | 56/0 |
| 1/2 | offline | 56/168 | 0.538257 | 3.9935 | 4.0925 | n/a | 0/0 |
| 1 | knn_mpc | 92/168 | 0.362157 | 3.9988 | 4.1535 | 0.3383 | 88/24 |
| 1 | rolling_nash | 79/168 | 0.464875 | 4.0628 | 4.1763 | n/a | 0/0 |
| 1 | rolling_maxmin | 90/168 | 0.375825 | 4.0207 | 4.1654 | n/a | 0/0 |
| 1 | greedy_recovery | 90/168 | 0.369137 | 4.0056 | 4.1650 | n/a | 0/0 |
| 1 | persistence_mpc | 90/168 | 0.384517 | 3.9983 | 4.1515 | 0.1469 | 102/16 |
| 1 | offline | 96/168 | 0.344994 | 3.9995 | 4.1574 | n/a | 0/0 |
| 2 | knn_mpc | 157/168 | 0.228625 | 4.0008 | 4.1891 | 0.3383 | 142/11 |
| 2 | rolling_nash | 112/168 | 0.334637 | 4.1549 | 4.2820 | n/a | 0/0 |
| 2 | rolling_maxmin | 156/168 | 0.232360 | 4.0917 | 4.2663 | n/a | 0/0 |
| 2 | greedy_recovery | 157/168 | 0.225936 | 4.0725 | 4.2685 | n/a | 0/0 |
| 2 | persistence_mpc | 157/168 | 0.233456 | 4.0008 | 4.1916 | 0.1469 | 154/1 |
| 2 | offline | 157/168 | 0.225936 | 4.0008 | 4.1892 | n/a | 0/0 |

## BuskingUnderpass05

| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1/2 | knn_mpc | 0/28 | 0.774781 | 4.4720 | 4.5410 | 0.2032 | 0/0 |
| 1/2 | rolling_nash | 0/28 | 0.807265 | 4.4959 | 4.5488 | n/a | 0/0 |
| 1/2 | rolling_maxmin | 0/28 | 0.763998 | 4.4743 | 4.5450 | n/a | 0/0 |
| 1/2 | greedy_recovery | 0/28 | 0.763998 | 4.4743 | 4.5450 | n/a | 0/0 |
| 1/2 | persistence_mpc | 0/28 | 0.804067 | 4.4673 | 4.5349 | 0.2305 | 0/0 |
| 1/2 | offline | 0/28 | 0.756346 | 4.4722 | 4.5456 | n/a | 0/0 |
| 1 | knn_mpc | 0/28 | 0.570178 | 4.4848 | 4.5929 | 0.2032 | 8/8 |
| 1 | rolling_nash | 0/28 | 0.689689 | 4.5040 | 4.5980 | n/a | 0/0 |
| 1 | rolling_maxmin | 0/28 | 0.600196 | 4.4825 | 4.5859 | n/a | 0/0 |
| 1 | greedy_recovery | 0/28 | 0.600196 | 4.4825 | 4.5859 | n/a | 0/0 |
| 1 | persistence_mpc | 0/28 | 0.636478 | 4.4834 | 4.5769 | 0.2305 | 7/7 |
| 1 | offline | 0/28 | 0.553113 | 4.4845 | 4.5970 | n/a | 0/0 |
| 2 | knn_mpc | 28/28 | 0.242398 | 4.4874 | 4.6754 | 0.2032 | 28/0 |
| 2 | rolling_nash | 16/28 | 0.459727 | 4.6146 | 4.6932 | n/a | 0/0 |
| 2 | rolling_maxmin | 28/28 | 0.264172 | 4.5014 | 4.6770 | n/a | 0/0 |
| 2 | greedy_recovery | 28/28 | 0.242398 | 4.4874 | 4.6754 | n/a | 0/0 |
| 2 | persistence_mpc | 28/28 | 0.242398 | 4.4874 | 4.6754 | 0.2305 | 28/0 |
| 2 | offline | 28/28 | 0.242398 | 4.4874 | 4.6754 | n/a | 0/0 |

## Cheerleading01

| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1/2 | knn_mpc | 0/28 | 0.671998 | 4.2386 | 4.3244 | 0.1725 | 0/0 |
| 1/2 | rolling_nash | 0/28 | 0.711140 | 4.2487 | 4.3271 | n/a | 0/0 |
| 1/2 | rolling_maxmin | 0/28 | 0.671998 | 4.2390 | 4.3246 | n/a | 0/0 |
| 1/2 | greedy_recovery | 0/28 | 0.671998 | 4.2390 | 4.3246 | n/a | 0/0 |
| 1/2 | persistence_mpc | 0/28 | 0.671998 | 4.2386 | 4.3244 | 0.1283 | 0/0 |
| 1/2 | offline | 0/28 | 0.657822 | 4.2386 | 4.3282 | n/a | 0/0 |
| 1 | knn_mpc | 28/28 | 0.343071 | 4.2386 | 4.4105 | 0.1725 | 2/0 |
| 1 | rolling_nash | 19/28 | 0.436432 | 4.2946 | 4.4149 | n/a | 0/0 |
| 1 | rolling_maxmin | 28/28 | 0.343071 | 4.2390 | 4.4107 | n/a | 0/0 |
| 1 | greedy_recovery | 28/28 | 0.343071 | 4.2390 | 4.4107 | n/a | 0/0 |
| 1 | persistence_mpc | 28/28 | 0.343071 | 4.2386 | 4.4105 | 0.1283 | 27/0 |
| 1 | offline | 28/28 | 0.343071 | 4.2386 | 4.4105 | n/a | 0/0 |
| 2 | knn_mpc | 28/28 | 0.343071 | 4.2386 | 4.4105 | 0.1725 | 2/0 |
| 2 | rolling_nash | 19/28 | 0.436432 | 4.2946 | 4.4149 | n/a | 0/0 |
| 2 | rolling_maxmin | 28/28 | 0.343071 | 4.2390 | 4.4107 | n/a | 0/0 |
| 2 | greedy_recovery | 28/28 | 0.343071 | 4.2390 | 4.4107 | n/a | 0/0 |
| 2 | persistence_mpc | 28/28 | 0.343071 | 4.2386 | 4.4105 | 0.1283 | 27/0 |
| 2 | offline | 28/28 | 0.343071 | 4.2386 | 4.4105 | n/a | 0/0 |

## ConferenceParticipant02

| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1/2 | knn_mpc | 0/28 | 0.846972 | 4.6813 | 4.7299 | 0.1592 | 0/0 |
| 1/2 | rolling_nash | 0/28 | 0.897414 | 4.7065 | 4.7357 | n/a | 0/0 |
| 1/2 | rolling_maxmin | 0/28 | 0.858794 | 4.6813 | 4.7265 | n/a | 0/0 |
| 1/2 | greedy_recovery | 0/28 | 0.858794 | 4.6813 | 4.7265 | n/a | 0/0 |
| 1/2 | persistence_mpc | 0/28 | 0.855338 | 4.6783 | 4.7275 | 0.0625 | 0/0 |
| 1/2 | offline | 0/28 | 0.826720 | 4.6813 | 4.7358 | n/a | 0/0 |
| 1 | knn_mpc | 0/28 | 0.709019 | 4.6852 | 4.7702 | 0.1592 | 0/0 |
| 1 | rolling_nash | 0/28 | 0.796833 | 4.7432 | 4.7840 | n/a | 0/0 |
| 1 | rolling_maxmin | 0/28 | 0.714147 | 4.6852 | 4.7687 | n/a | 0/0 |
| 1 | greedy_recovery | 0/28 | 0.714147 | 4.6852 | 4.7687 | n/a | 0/0 |
| 1 | persistence_mpc | 0/28 | 0.729247 | 4.6845 | 4.7644 | 0.0625 | 3/3 |
| 1 | offline | 0/28 | 0.685590 | 4.6852 | 4.7771 | n/a | 0/0 |
| 2 | knn_mpc | 17/28 | 0.461619 | 4.6852 | 4.8426 | 0.1592 | 28/11 |
| 2 | rolling_nash | 8/28 | 0.614854 | 4.7996 | 4.8663 | n/a | 0/0 |
| 2 | rolling_maxmin | 17/28 | 0.461619 | 4.6852 | 4.8426 | n/a | 0/0 |
| 2 | greedy_recovery | 17/28 | 0.461619 | 4.6852 | 4.8426 | n/a | 0/0 |
| 2 | persistence_mpc | 17/28 | 0.461619 | 4.6852 | 4.8426 | 0.0625 | 15/1 |
| 2 | offline | 17/28 | 0.461619 | 4.6852 | 4.8426 | n/a | 0/0 |

## ParkFountains01

| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1/2 | knn_mpc | 28/28 | 0.311775 | 3.6934 | 3.8188 | 0.3387 | 28/0 |
| 1/2 | rolling_nash | 27/28 | 0.333722 | 3.6980 | 3.8196 | n/a | 0/0 |
| 1/2 | rolling_maxmin | 28/28 | 0.311775 | 3.6934 | 3.8188 | n/a | 0/0 |
| 1/2 | greedy_recovery | 28/28 | 0.311775 | 3.6934 | 3.8188 | n/a | 0/0 |
| 1/2 | persistence_mpc | 28/28 | 0.311775 | 3.6934 | 3.8188 | 0.0626 | 28/0 |
| 1/2 | offline | 28/28 | 0.232076 | 3.6934 | 3.8334 | n/a | 0/0 |
| 1 | knn_mpc | 28/28 | 0.000000 | 3.6934 | 3.9478 | 0.3387 | 28/0 |
| 1 | rolling_nash | 28/28 | 0.120027 | 3.7934 | 3.9519 | n/a | 0/0 |
| 1 | rolling_maxmin | 28/28 | 0.006735 | 3.7033 | 3.9481 | n/a | 0/0 |
| 1 | greedy_recovery | 28/28 | 0.000000 | 3.6934 | 3.9478 | n/a | 0/0 |
| 1 | persistence_mpc | 28/28 | 0.000000 | 3.6934 | 3.9478 | 0.0626 | 28/0 |
| 1 | offline | 28/28 | 0.000000 | 3.6934 | 3.9478 | n/a | 0/0 |
| 2 | knn_mpc | 28/28 | 0.000000 | 3.6934 | 3.9478 | 0.3387 | 28/0 |
| 2 | rolling_nash | 28/28 | 0.006735 | 4.0311 | 4.2255 | n/a | 0/0 |
| 2 | rolling_maxmin | 28/28 | 0.000000 | 3.9796 | 4.2172 | n/a | 0/0 |
| 2 | greedy_recovery | 28/28 | 0.000000 | 3.9661 | 4.2231 | n/a | 0/0 |
| 2 | persistence_mpc | 28/28 | 0.000000 | 3.6934 | 3.9478 | 0.0626 | 28/0 |
| 2 | offline | 28/28 | 0.000000 | 3.6934 | 3.9478 | n/a | 0/0 |

## River01

| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1/2 | knn_mpc | 28/28 | 0.086602 | 2.6587 | 2.7854 | 0.9266 | 28/0 |
| 1/2 | rolling_nash | 19/28 | 0.356715 | 2.6789 | 2.7990 | n/a | 0/0 |
| 1/2 | rolling_maxmin | 28/28 | 0.080301 | 2.6587 | 2.7880 | n/a | 0/0 |
| 1/2 | greedy_recovery | 28/28 | 0.080301 | 2.6587 | 2.7880 | n/a | 0/0 |
| 1/2 | persistence_mpc | 28/28 | 0.178569 | 2.6587 | 2.7688 | 0.1288 | 28/0 |
| 1/2 | offline | 28/28 | 0.034572 | 2.6587 | 2.7950 | n/a | 0/0 |
| 1 | knn_mpc | 28/28 | 0.016132 | 2.6587 | 2.8339 | 0.9266 | 28/0 |
| 1 | rolling_nash | 26/28 | 0.089428 | 2.8128 | 2.9328 | n/a | 0/0 |
| 1 | rolling_maxmin | 28/28 | 0.033390 | 2.7871 | 2.9192 | n/a | 0/0 |
| 1 | greedy_recovery | 28/28 | 0.000000 | 2.7062 | 2.9170 | n/a | 0/0 |
| 1 | persistence_mpc | 28/28 | 0.045119 | 2.6587 | 2.8488 | 0.1288 | 28/0 |
| 1 | offline | 28/28 | 0.000000 | 2.6587 | 2.8345 | n/a | 0/0 |
| 2 | knn_mpc | 28/28 | 0.016132 | 2.6587 | 2.8339 | 0.9266 | 28/0 |
| 2 | rolling_nash | 28/28 | 0.019867 | 2.8830 | 3.0492 | n/a | 0/0 |
| 2 | rolling_maxmin | 28/28 | 0.000000 | 2.8948 | 3.0258 | n/a | 0/0 |
| 2 | greedy_recovery | 28/28 | 0.000000 | 2.8158 | 3.0346 | n/a | 0/0 |
| 2 | persistence_mpc | 28/28 | 0.045119 | 2.6587 | 2.8488 | 0.1288 | 28/0 |
| 2 | offline | 28/28 | 0.000000 | 2.6587 | 2.8345 | n/a | 0/0 |

## Train01

| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1/2 | knn_mpc | 0/28 | 0.740681 | 4.2161 | 4.3120 | 0.2298 | 1/1 |
| 1/2 | rolling_nash | 0/28 | 0.791042 | 4.2174 | 4.3144 | n/a | 0/0 |
| 1/2 | rolling_maxmin | 0/28 | 0.754979 | 4.2120 | 4.3084 | n/a | 0/0 |
| 1/2 | greedy_recovery | 0/28 | 0.754979 | 4.2120 | 4.3084 | n/a | 0/0 |
| 1/2 | persistence_mpc | 0/28 | 0.802068 | 4.1998 | 4.2962 | 0.2686 | 0/0 |
| 1/2 | offline | 0/28 | 0.722007 | 4.2168 | 4.3169 | n/a | 0/0 |
| 1 | knn_mpc | 8/28 | 0.534539 | 4.2320 | 4.3657 | 0.2298 | 22/16 |
| 1 | rolling_nash | 6/28 | 0.656840 | 4.2288 | 4.3760 | n/a | 0/0 |
| 1 | rolling_maxmin | 6/28 | 0.557409 | 4.2273 | 4.3599 | n/a | 0/0 |
| 1 | greedy_recovery | 6/28 | 0.557409 | 4.2273 | 4.3599 | n/a | 0/0 |
| 1 | persistence_mpc | 6/28 | 0.553189 | 4.2308 | 4.3608 | 0.2686 | 9/6 |
| 1 | offline | 12/28 | 0.488190 | 4.2364 | 4.3776 | n/a | 0/0 |
| 2 | knn_mpc | 28/28 | 0.308529 | 4.2415 | 4.4244 | 0.2298 | 28/0 |
| 2 | rolling_nash | 13/28 | 0.470205 | 4.3068 | 4.4429 | n/a | 0/0 |
| 2 | rolling_maxmin | 27/28 | 0.325296 | 4.2502 | 4.4244 | n/a | 0/0 |
| 2 | greedy_recovery | 28/28 | 0.308529 | 4.2417 | 4.4245 | n/a | 0/0 |
| 2 | persistence_mpc | 28/28 | 0.308529 | 4.2415 | 4.4244 | 0.2686 | 28/0 |
| 2 | offline | 28/28 | 0.308529 | 4.2415 | 4.4244 | n/a | 0/0 |

## v2

| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1/2 | knn_mpc | 56/84 | 0.379686 | 3.5228 | 3.6388 | 0.4984 | 57/1 |
| 1/2 | rolling_nash | 46/84 | 0.493826 | 3.5315 | 3.6443 | n/a | 0/0 |
| 1/2 | rolling_maxmin | 56/84 | 0.382352 | 3.5214 | 3.6384 | n/a | 0/0 |
| 1/2 | greedy_recovery | 56/84 | 0.382352 | 3.5214 | 3.6384 | n/a | 0/0 |
| 1/2 | persistence_mpc | 56/84 | 0.430804 | 3.5173 | 3.6279 | 0.1534 | 56/0 |
| 1/2 | offline | 56/84 | 0.329552 | 3.5230 | 3.6484 | n/a | 0/0 |
| 1 | knn_mpc | 64/84 | 0.183557 | 3.5281 | 3.7158 | 0.4984 | 78/16 |
| 1 | rolling_nash | 60/84 | 0.288765 | 3.6116 | 3.7536 | n/a | 0/0 |
| 1 | rolling_maxmin | 62/84 | 0.199178 | 3.5726 | 3.7424 | n/a | 0/0 |
| 1 | greedy_recovery | 62/84 | 0.185803 | 3.5423 | 3.7416 | n/a | 0/0 |
| 1 | persistence_mpc | 62/84 | 0.199436 | 3.5277 | 3.7191 | 0.1534 | 65/6 |
| 1 | offline | 68/84 | 0.162730 | 3.5295 | 3.7200 | n/a | 0/0 |
| 2 | knn_mpc | 84/84 | 0.108221 | 3.5312 | 3.7354 | 0.4984 | 84/0 |
| 2 | rolling_nash | 69/84 | 0.165602 | 3.7403 | 3.9058 | n/a | 0/0 |
| 2 | rolling_maxmin | 83/84 | 0.108432 | 3.7082 | 3.8891 | n/a | 0/0 |
| 2 | greedy_recovery | 84/84 | 0.102843 | 3.6745 | 3.8940 | n/a | 0/0 |
| 2 | persistence_mpc | 84/84 | 0.117883 | 3.5312 | 3.7403 | 0.1534 | 84/0 |
| 2 | offline | 84/84 | 0.102843 | 3.5312 | 3.7356 | n/a | 0/0 |

## v3

| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1/2 | knn_mpc | 0/84 | 0.764584 | 4.4639 | 4.5318 | 0.1783 | 0/0 |
| 1/2 | rolling_nash | 0/84 | 0.805273 | 4.4837 | 4.5372 | n/a | 0/0 |
| 1/2 | rolling_maxmin | 0/84 | 0.764930 | 4.4648 | 4.5320 | n/a | 0/0 |
| 1/2 | greedy_recovery | 0/84 | 0.764930 | 4.4648 | 4.5320 | n/a | 0/0 |
| 1/2 | persistence_mpc | 0/84 | 0.777134 | 4.4614 | 4.5289 | 0.1404 | 0/0 |
| 1/2 | offline | 0/84 | 0.746963 | 4.4640 | 4.5365 | n/a | 0/0 |
| 1 | knn_mpc | 28/84 | 0.540756 | 4.4695 | 4.5912 | 0.1783 | 10/8 |
| 1 | rolling_nash | 19/84 | 0.640985 | 4.5139 | 4.5990 | n/a | 0/0 |
| 1 | rolling_maxmin | 28/84 | 0.552471 | 4.4689 | 4.5884 | n/a | 0/0 |
| 1 | greedy_recovery | 28/84 | 0.552471 | 4.4689 | 4.5884 | n/a | 0/0 |
| 1 | persistence_mpc | 28/84 | 0.569598 | 4.4688 | 4.5839 | 0.1404 | 37/10 |
| 1 | offline | 28/84 | 0.527258 | 4.4694 | 4.5949 | n/a | 0/0 |
| 2 | knn_mpc | 73/84 | 0.349029 | 4.4704 | 4.6428 | 0.1783 | 58/11 |
| 2 | rolling_nash | 43/84 | 0.503671 | 4.5696 | 4.6581 | n/a | 0/0 |
| 2 | rolling_maxmin | 73/84 | 0.356287 | 4.4752 | 4.6434 | n/a | 0/0 |
| 2 | greedy_recovery | 73/84 | 0.349029 | 4.4705 | 4.6429 | n/a | 0/0 |
| 2 | persistence_mpc | 73/84 | 0.349029 | 4.4704 | 4.6428 | 0.1404 | 70/1 |
| 2 | offline | 73/84 | 0.349029 | 4.4704 | 4.6428 | n/a | 0/0 |

## Boundaries

The network experiment tests an engineered reservation and synthetic byte transfers, not real path availability, an implemented player or new content. The point forecast is uncalibrated; predicted half-repayment is not a guarantee. All 168 pairs are retained and are dependent within six exposed scenes. No confidence claim is made from these counts.

The matched persistence controller distinguishes forecasting from lookahead optimization. Offline results use future labels explicitly and are not a deployable method. Quality tradeoffs remain visible.
