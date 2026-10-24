# Exposed-data bounded-loss development

**Not a fresh holdout. Exact current utilities are revealed to all controls; future opportunities are forecast causally.**

Development screen: **FAIL**. No positive streaming-validation claim follows from this replay.

Metrics below condition on positive event loss; every zero-loss episode remains in the complete artifact. Mixture outcomes are expectations over episode-level policy randomization, not Monte Carlo estimates. Unpaid fraction is actual loss, not regret. Cap sensitivities have different specified limits and cannot be ranked by violation rate alone.

## all

Episodes: 168; positive debt: 168. Whole future-envelope coverage (capped gains): 100.000%; raw gains: 100.000%. Midpoint gain MAE: 0.025228 utility.

| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |
|---|---:|---:|---:|---:|---:|---:|
| bounded_knn | 0.999354 | 0.000207 | 1.000000 | 3.990127 | 0.087048 | 0.000000 |
| knn_alpha25 | 0.999354 | 0.000207 | 1.000000 | 3.990127 | 0.087048 | 0.000000 |
| knn_alpha75 | 0.999354 | 0.000207 | 1.000000 | 3.990127 | 0.087048 | 0.000000 |
| unconstrained_knn | 0.999166 | 0.000019 | 0.000000 | 3.988488 | 0.100543 | 1.000000 |
| bounded_persistence | 0.999147 | 0.000000 | 1.000000 | 3.988318 | 0.101935 | 0.000000 |
| bounded_physical | 0.999940 | 0.000793 | 1.000000 | 3.996165 | 0.037589 | 0.000000 |
| rolling_nash | 1.000000 | 0.000853 | 1.000000 | 4.000848 | 0.000000 | n/a |
| rolling_maxmin | 0.999153 | 0.000005 | 1.000000 | 3.988488 | 0.100565 | n/a |
| stateless_nash | 1.000000 | 0.000853 | 1.000000 | 4.000848 | 0.000000 | n/a |
| greedy_recovery | 0.999147 | 0.000000 | 1.000000 | 3.988318 | 0.101935 | n/a |
| baseline | 1.000000 | 0.000853 | 1.000000 | 4.000848 | 0.000000 | n/a |

Primary feasible-admission violation mass: 0. Infeasible requests remain failures of the requested cap even when the fallback is useful.

## v2

Episodes: 84; positive debt: 84. Whole future-envelope coverage (capped gains): 100.000%; raw gains: 100.000%. Midpoint gain MAE: 0.025728 utility.

| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |
|---|---:|---:|---:|---:|---:|---:|
| bounded_knn | 0.999868 | 0.000000 | 1.000000 | 3.523055 | 0.073929 | 0.000000 |
| knn_alpha25 | 0.999868 | 0.000000 | 1.000000 | 3.523055 | 0.073929 | 0.000000 |
| knn_alpha75 | 0.999868 | 0.000000 | 1.000000 | 3.523055 | 0.073929 | 0.000000 |
| unconstrained_knn | 0.999868 | 0.000000 | 0.000000 | 3.523055 | 0.073929 | 1.000000 |
| bounded_persistence | 0.999868 | 0.000000 | 1.000000 | 3.523055 | 0.073929 | 0.000000 |
| bounded_physical | 0.999891 | 0.000023 | 1.000000 | 3.524292 | 0.064012 | 0.000000 |
| rolling_nash | 1.000000 | 0.000132 | 1.000000 | 3.532265 | 0.000000 | n/a |
| rolling_maxmin | 0.999879 | 0.000011 | 1.000000 | 3.523394 | 0.071190 | n/a |
| stateless_nash | 1.000000 | 0.000132 | 1.000000 | 3.532265 | 0.000000 | n/a |
| greedy_recovery | 0.999868 | 0.000000 | 1.000000 | 3.523055 | 0.073929 | n/a |
| baseline | 1.000000 | 0.000132 | 1.000000 | 3.532265 | 0.000000 | n/a |

Primary feasible-admission violation mass: 0. Infeasible requests remain failures of the requested cap even when the fallback is useful.

## v3

Episodes: 84; positive debt: 84. Whole future-envelope coverage (capped gains): 100.000%; raw gains: 100.000%. Midpoint gain MAE: 0.024728 utility.

| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |
|---|---:|---:|---:|---:|---:|---:|
| bounded_knn | 0.998840 | 0.000414 | 1.000000 | 4.457199 | 0.100167 | 0.000000 |
| knn_alpha25 | 0.998840 | 0.000414 | 1.000000 | 4.457199 | 0.100167 | 0.000000 |
| knn_alpha75 | 0.998840 | 0.000414 | 1.000000 | 4.457199 | 0.100167 | 0.000000 |
| unconstrained_knn | 0.998464 | 0.000037 | 0.000000 | 4.453920 | 0.127157 | 1.000000 |
| bounded_persistence | 0.998427 | 0.000000 | 1.000000 | 4.453582 | 0.129940 | 0.000000 |
| bounded_physical | 0.999989 | 0.001563 | 1.000000 | 4.468039 | 0.011167 | 0.000000 |
| rolling_nash | 1.000000 | 0.001573 | 1.000000 | 4.469432 | 0.000000 | n/a |
| rolling_maxmin | 0.998427 | 0.000000 | 1.000000 | 4.453582 | 0.129940 | n/a |
| stateless_nash | 1.000000 | 0.001573 | 1.000000 | 4.469432 | 0.000000 | n/a |
| greedy_recovery | 0.998427 | 0.000000 | 1.000000 | 4.453582 | 0.129940 | n/a |
| baseline | 1.000000 | 0.001573 | 1.000000 | 4.469432 | 0.000000 | n/a |

Primary feasible-admission violation mass: 0. Infeasible requests remain failures of the requested cap even when the fallback is useful.

## BuskingUnderpass05

Episodes: 28; positive debt: 28. Whole future-envelope coverage (capped gains): 100.000%; raw gains: 100.000%. Midpoint gain MAE: 0.022089 utility.

| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |
|---|---:|---:|---:|---:|---:|---:|
| bounded_knn | 0.996553 | 0.001241 | 1.000000 | 4.451991 | 0.267000 | 0.000000 |
| knn_alpha25 | 0.996553 | 0.001241 | 1.000000 | 4.451991 | 0.267000 | 0.000000 |
| knn_alpha75 | 0.996553 | 0.001241 | 1.000000 | 4.451991 | 0.267000 | 0.000000 |
| unconstrained_knn | 0.995424 | 0.000112 | 0.000000 | 4.442154 | 0.347971 | 1.000000 |
| bounded_persistence | 0.995312 | 0.000000 | 1.000000 | 4.441138 | 0.356321 | 0.000000 |
| bounded_physical | 1.000000 | 0.004688 | 1.000000 | 4.484509 | 0.000000 | 0.000000 |
| rolling_nash | 1.000000 | 0.004688 | 1.000000 | 4.484509 | 0.000000 | n/a |
| rolling_maxmin | 0.995312 | 0.000000 | 1.000000 | 4.441138 | 0.356321 | n/a |
| stateless_nash | 1.000000 | 0.004688 | 1.000000 | 4.484509 | 0.000000 | n/a |
| greedy_recovery | 0.995312 | 0.000000 | 1.000000 | 4.441138 | 0.356321 | n/a |
| baseline | 1.000000 | 0.004688 | 1.000000 | 4.484509 | 0.000000 | n/a |

Primary feasible-admission violation mass: 0. Infeasible requests remain failures of the requested cap even when the fallback is useful.

## Cheerleading01

Episodes: 28; positive debt: 28. Whole future-envelope coverage (capped gains): 100.000%; raw gains: 100.000%. Midpoint gain MAE: 0.026905 utility.

| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |
|---|---:|---:|---:|---:|---:|---:|
| bounded_knn | 0.999983 | 0.000000 | 1.000000 | 4.236496 | 0.016714 | 0.000000 |
| knn_alpha25 | 0.999983 | 0.000000 | 1.000000 | 4.236496 | 0.016714 | 0.000000 |
| knn_alpha75 | 0.999983 | 0.000000 | 1.000000 | 4.236496 | 0.016714 | 0.000000 |
| unconstrained_knn | 0.999983 | 0.000000 | 0.000000 | 4.236496 | 0.016714 | 1.000000 |
| bounded_persistence | 0.999983 | 0.000000 | 1.000000 | 4.236496 | 0.016714 | 0.000000 |
| bounded_physical | 0.999983 | 0.000000 | 1.000000 | 4.236496 | 0.016714 | 0.000000 |
| rolling_nash | 1.000000 | 0.000017 | 1.000000 | 4.238580 | 0.000000 | n/a |
| rolling_maxmin | 0.999983 | 0.000000 | 1.000000 | 4.236496 | 0.016714 | n/a |
| stateless_nash | 1.000000 | 0.000017 | 1.000000 | 4.238580 | 0.000000 | n/a |
| greedy_recovery | 0.999983 | 0.000000 | 1.000000 | 4.236496 | 0.016714 | n/a |
| baseline | 1.000000 | 0.000017 | 1.000000 | 4.238580 | 0.000000 | n/a |

Primary feasible-admission violation mass: 0. Infeasible requests remain failures of the requested cap even when the fallback is useful.

## ConferenceParticipant02

Episodes: 28; positive debt: 28. Whole future-envelope coverage (capped gains): 100.000%; raw gains: 100.000%. Midpoint gain MAE: 0.025190 utility.

| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |
|---|---:|---:|---:|---:|---:|---:|
| bounded_knn | 0.999986 | 0.000000 | 1.000000 | 4.683112 | 0.016786 | 0.000000 |
| knn_alpha25 | 0.999986 | 0.000000 | 1.000000 | 4.683112 | 0.016786 | 0.000000 |
| knn_alpha75 | 0.999986 | 0.000000 | 1.000000 | 4.683112 | 0.016786 | 0.000000 |
| unconstrained_knn | 0.999986 | 0.000000 | 0.000000 | 4.683112 | 0.016786 | 1.000000 |
| bounded_persistence | 0.999986 | 0.000000 | 1.000000 | 4.683112 | 0.016786 | 0.000000 |
| bounded_physical | 0.999986 | 0.000000 | 1.000000 | 4.683112 | 0.016786 | 0.000000 |
| rolling_nash | 1.000000 | 0.000014 | 1.000000 | 4.685205 | 0.000000 | n/a |
| rolling_maxmin | 0.999986 | 0.000000 | 1.000000 | 4.683112 | 0.016786 | n/a |
| stateless_nash | 1.000000 | 0.000014 | 1.000000 | 4.685205 | 0.000000 | n/a |
| greedy_recovery | 0.999986 | 0.000000 | 1.000000 | 4.683112 | 0.016786 | n/a |
| baseline | 1.000000 | 0.000014 | 1.000000 | 4.685205 | 0.000000 | n/a |

Primary feasible-admission violation mass: 0. Infeasible requests remain failures of the requested cap even when the fallback is useful.

## ParkFountains01

Episodes: 28; positive debt: 28. Whole future-envelope coverage (capped gains): 100.000%; raw gains: 100.000%. Midpoint gain MAE: 0.025750 utility.

| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |
|---|---:|---:|---:|---:|---:|---:|
| bounded_knn | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | 0.000000 |
| knn_alpha25 | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | 0.000000 |
| knn_alpha75 | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | 0.000000 |
| unconstrained_knn | 1.000000 | 0.000000 | 0.000000 | 3.693446 | 0.000000 | 1.000000 |
| bounded_persistence | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | 0.000000 |
| bounded_physical | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | 0.000000 |
| rolling_nash | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | n/a |
| rolling_maxmin | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | n/a |
| stateless_nash | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | n/a |
| greedy_recovery | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | n/a |
| baseline | 1.000000 | 0.000000 | 1.000000 | 3.693446 | 0.000000 | n/a |

Primary feasible-admission violation mass: 0. Infeasible requests remain failures of the requested cap even when the fallback is useful.

## River01

Episodes: 28; positive debt: 28. Whole future-envelope coverage (capped gains): 100.000%; raw gains: 100.000%. Midpoint gain MAE: 0.024976 utility.

| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |
|---|---:|---:|---:|---:|---:|---:|
| bounded_knn | 0.999932 | 0.000000 | 1.000000 | 2.655022 | 0.029750 | 0.000000 |
| knn_alpha25 | 0.999932 | 0.000000 | 1.000000 | 2.655022 | 0.029750 | 0.000000 |
| knn_alpha75 | 0.999932 | 0.000000 | 1.000000 | 2.655022 | 0.029750 | 0.000000 |
| unconstrained_knn | 0.999932 | 0.000000 | 0.000000 | 2.655022 | 0.029750 | 1.000000 |
| bounded_persistence | 0.999932 | 0.000000 | 1.000000 | 2.655022 | 0.029750 | 0.000000 |
| bounded_physical | 1.000000 | 0.000068 | 1.000000 | 2.658732 | 0.000000 | 0.000000 |
| rolling_nash | 1.000000 | 0.000068 | 1.000000 | 2.658732 | 0.000000 | n/a |
| rolling_maxmin | 0.999932 | 0.000000 | 1.000000 | 2.655022 | 0.029750 | n/a |
| stateless_nash | 1.000000 | 0.000068 | 1.000000 | 2.658732 | 0.000000 | n/a |
| greedy_recovery | 0.999932 | 0.000000 | 1.000000 | 2.655022 | 0.029750 | n/a |
| baseline | 1.000000 | 0.000068 | 1.000000 | 2.658732 | 0.000000 | n/a |

Primary feasible-admission violation mass: 0. Infeasible requests remain failures of the requested cap even when the fallback is useful.

## Train01

Episodes: 28; positive debt: 28. Whole future-envelope coverage (capped gains): 100.000%; raw gains: 100.000%. Midpoint gain MAE: 0.026458 utility.

| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |
|---|---:|---:|---:|---:|---:|---:|
| bounded_knn | 0.999672 | 0.000000 | 1.000000 | 4.220696 | 0.192036 | 0.000000 |
| knn_alpha25 | 0.999672 | 0.000000 | 1.000000 | 4.220696 | 0.192036 | 0.000000 |
| knn_alpha75 | 0.999672 | 0.000000 | 1.000000 | 4.220696 | 0.192036 | 0.000000 |
| unconstrained_knn | 0.999672 | 0.000000 | 0.000000 | 4.220696 | 0.192036 | 1.000000 |
| bounded_persistence | 0.999672 | 0.000000 | 1.000000 | 4.220696 | 0.192036 | 0.000000 |
| bounded_physical | 0.999672 | 0.000000 | 1.000000 | 4.220696 | 0.192036 | 0.000000 |
| rolling_nash | 1.000000 | 0.000328 | 1.000000 | 4.244616 | 0.000000 | n/a |
| rolling_maxmin | 0.999704 | 0.000033 | 1.000000 | 4.221714 | 0.183821 | n/a |
| stateless_nash | 1.000000 | 0.000328 | 1.000000 | 4.244616 | 0.000000 | n/a |
| greedy_recovery | 0.999672 | 0.000000 | 1.000000 | 4.220696 | 0.192036 | n/a |
| baseline | 1.000000 | 0.000328 | 1.000000 | 4.244616 | 0.000000 | n/a |

Primary feasible-admission violation mass: 0. Infeasible requests remain failures of the requested cap even when the fallback is useful.

## Frozen progression checks

- PASS: nonempty_positive_debt
- FAIL: at_least_half_feasible
- PASS: forecast_coverage_90pct
- PASS: zero_feasible_cap_violations
- PASS: all_pathwise_guards
- PASS: v2:rolling_nash:unpaid_gain
- PASS: v2:rolling_nash:cap_guard
- PASS: v2:rolling_nash:mean_quality_guard
- PASS: v2:rolling_maxmin:unpaid_gain
- PASS: v2:rolling_maxmin:cap_guard
- PASS: v2:rolling_maxmin:mean_quality_guard
- PASS: v3:rolling_nash:unpaid_gain
- PASS: v3:rolling_nash:cap_guard
- PASS: v3:rolling_nash:mean_quality_guard
- FAIL: v3:rolling_maxmin:unpaid_gain
- PASS: v3:rolling_maxmin:cap_guard
- PASS: v3:rolling_maxmin:mean_quality_guard

## Interpretation boundary

The loss constraint is pathwise only inside its forecast envelope and within the fixed threshold-policy class. No-neighbor-future leakage is enforced, but the forecast is not calibrated. Out-of-envelope observations trigger protected greedy fallback; missed opportunities cannot be repaired retrospectively. Every actually selected path respects the byte cap, donor loss limit, recipient reference floor and single-transfer restriction. These checks are not proofs of stall protection, perceptual benefit, novel scheduling theory or performance on unseen scenes.
