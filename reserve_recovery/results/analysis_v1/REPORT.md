# Limited cumulative recovery reserve

**Constructed analytical tests and already-exposed tables only. No new holdout or validated field headroom.**

## Evidence boundary

The 30 captured traffic traces do not identify spare path capacity. Earlier network capacities were configured or synthetic. Demand below is encoded payload, not measured supply.

The finite reserve pays only positive bytes above the unchanged baseline, with no refill or refunds. Every action must also fit contemporaneous capacity. It is an entitlement, not stored bandwidth.

## Exact analytical comparison

| Construction | Half-repayment admitted | Causal worst unpaid | Rolling Nash | Rolling max-min | Greedy | Offline worst unpaid |
|---|---|---:|---:|---:|---:|---:|
| bounded_better_future | True | 0.4000 | 0.6000 | 0.6000 | 0.6000 | 0.4000 |
| disappearing_opportunity | True | 0.4000 | 0.4000 | 0.4000 | 0.4000 | 0.4000 |
| no_half_repayment_admission | False | 0.6000 | 0.6000 | 0.6000 | 0.6000 | 0.6000 |
| nonbinding_reserve | True | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| zero_reserve | False | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| no_instantaneous_headroom | False | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| delayed_revelation | True | 0.3000 | 0.8000 | 0.8000 | 0.8000 | 0.3000 |
| causal_admission_gap | False | 0.7000 | 0.7000 | 0.7000 | 0.7000 | 0.4000 |

All causal values agree with an independent robust Bellman recursion. The future scenario set is supplied, not fitted. Model-aware planning is not an information-matched improvement over myopic rules.

Out-of-model disappearance: candidate unpaid fraction1, versus0.6 for the three immediate controls. The reserve remains safe but the repayment guarantee fails. The causal-admission-gap example is feasible in each future offline but not guaranteed by any shared-prefix policy.

## all

Episodes: 168.

### Minimum additional reserve for half-repayment

Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.

| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |
|---|---:|---:|---:|---:|
| 1 | 0/168 | infeasible | infeasible | infeasible |
| 2 | 0/168 | infeasible | infeasible | infeasible |
| 3 | 147/168 | 1.7109 [0.8533, 3.5875] | 0.7076 | 1.1707 [1.0925, 1.2352] |
| 4 | 157/168 | 1.7109 [0.8533, 3.5875] | 0.7076 | 1.1707 [1.0925, 1.2352] |

### Fixed reserve grid

Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. All policies use the same per-slot capacity, reserve and zero-donor-loss floor.

| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1/4 | 0 | 0 | 0 | 0 |
| 1 | 1/2 | 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1/4 | 0 | 0 | 0 | 0 |
| 2 | 1/2 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1/4 | 0 | 0 | 0 | 0 |
| 3 | 1/2 | 46 | 56 | 56 | 56 |
| 3 | 1 | 82 | 90 | 90 | 97 |
| 3 | 2 | 115 | 145 | 147 | 147 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 4 | 1/4 | 0 | 0 | 0 | 0 |
| 4 | 1/2 | 46 | 56 | 56 | 56 |
| 4 | 1 | 60 | 62 | 62 | 97 |
| 4 | 2 | 137 | 157 | 157 | 157 |

Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; no causal future predictor is evaluated on these exposed tables.

## v2

Episodes: 84.

### Minimum additional reserve for half-repayment

Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.

| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |
|---|---:|---:|---:|---:|
| 1 | 0/84 | infeasible | infeasible | infeasible |
| 2 | 0/84 | infeasible | infeasible | infeasible |
| 3 | 84/84 | 0.8761 [0.8533, 2.5570] | 0.4107 | 1.1249 [1.0925, 1.2352] |
| 4 | 84/84 | 0.8761 [0.8533, 2.5570] | 0.4107 | 1.1249 [1.0925, 1.2352] |

### Fixed reserve grid

Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. All policies use the same per-slot capacity, reserve and zero-donor-loss floor.

| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1/4 | 0 | 0 | 0 | 0 |
| 1 | 1/2 | 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1/4 | 0 | 0 | 0 | 0 |
| 2 | 1/2 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1/4 | 0 | 0 | 0 | 0 |
| 3 | 1/2 | 46 | 56 | 56 | 56 |
| 3 | 1 | 60 | 62 | 62 | 69 |
| 3 | 2 | 76 | 83 | 84 | 84 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 4 | 1/4 | 0 | 0 | 0 | 0 |
| 4 | 1/2 | 46 | 56 | 56 | 56 |
| 4 | 1 | 60 | 62 | 62 | 69 |
| 4 | 2 | 79 | 84 | 84 | 84 |

Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; no causal future predictor is evaluated on these exposed tables.

## v3

Episodes: 84.

### Minimum additional reserve for half-repayment

Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.

| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |
|---|---:|---:|---:|---:|
| 1 | 0/84 | infeasible | infeasible | infeasible |
| 2 | 0/84 | infeasible | infeasible | infeasible |
| 3 | 63/84 | 2.4803 [1.7109, 3.5875] | 1.1136 | 1.1707 [1.1244, 1.1733] |
| 4 | 73/84 | 2.4803 [1.7109, 3.5875] | 1.1136 | 1.1707 [1.1244, 1.1733] |

### Fixed reserve grid

Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. All policies use the same per-slot capacity, reserve and zero-donor-loss floor.

| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1/4 | 0 | 0 | 0 | 0 |
| 1 | 1/2 | 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1/4 | 0 | 0 | 0 | 0 |
| 2 | 1/2 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1/4 | 0 | 0 | 0 | 0 |
| 3 | 1/2 | 0 | 0 | 0 | 0 |
| 3 | 1 | 22 | 28 | 28 | 28 |
| 3 | 2 | 39 | 62 | 63 | 63 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 4 | 1/4 | 0 | 0 | 0 | 0 |
| 4 | 1/2 | 0 | 0 | 0 | 0 |
| 4 | 1 | 0 | 0 | 0 | 28 |
| 4 | 2 | 58 | 73 | 73 | 73 |

Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; no causal future predictor is evaluated on these exposed tables.

## BuskingUnderpass05

Episodes: 28.

### Minimum additional reserve for half-repayment

Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.

| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |
|---|---:|---:|---:|---:|
| 1 | 0/28 | infeasible | infeasible | infeasible |
| 2 | 0/28 | infeasible | infeasible | infeasible |
| 3 | 18/28 | 2.4803 [2.4803, 2.4803] | 1.1136 | 1.1707 [1.1707, 1.1707] |
| 4 | 28/28 | 2.4803 [2.4803, 2.6132] | 1.1136 | 1.1707 [1.1707, 1.1707] |

### Fixed reserve grid

Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. All policies use the same per-slot capacity, reserve and zero-donor-loss floor.

| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1/4 | 0 | 0 | 0 | 0 |
| 1 | 1/2 | 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1/4 | 0 | 0 | 0 | 0 |
| 2 | 1/2 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1/4 | 0 | 0 | 0 | 0 |
| 3 | 1/2 | 0 | 0 | 0 | 0 |
| 3 | 1 | 0 | 0 | 0 | 0 |
| 3 | 2 | 3 | 17 | 18 | 18 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 4 | 1/4 | 0 | 0 | 0 | 0 |
| 4 | 1/2 | 0 | 0 | 0 | 0 |
| 4 | 1 | 0 | 0 | 0 | 0 |
| 4 | 2 | 22 | 28 | 28 | 28 |

Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; no causal future predictor is evaluated on these exposed tables.

## Cheerleading01

Episodes: 28.

### Minimum additional reserve for half-repayment

Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.

| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |
|---|---:|---:|---:|---:|
| 1 | 0/28 | infeasible | infeasible | infeasible |
| 2 | 0/28 | infeasible | infeasible | infeasible |
| 3 | 28/28 | 1.7109 [1.7109, 1.7109] | 0.7076 | 1.1733 [1.1733, 1.1733] |
| 4 | 28/28 | 1.7109 [1.7109, 1.7109] | 0.7076 | 1.1733 [1.1733, 1.1733] |

### Fixed reserve grid

Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. All policies use the same per-slot capacity, reserve and zero-donor-loss floor.

| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1/4 | 0 | 0 | 0 | 0 |
| 1 | 1/2 | 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1/4 | 0 | 0 | 0 | 0 |
| 2 | 1/2 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1/4 | 0 | 0 | 0 | 0 |
| 3 | 1/2 | 0 | 0 | 0 | 0 |
| 3 | 1 | 22 | 28 | 28 | 28 |
| 3 | 2 | 28 | 28 | 28 | 28 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 4 | 1/4 | 0 | 0 | 0 | 0 |
| 4 | 1/2 | 0 | 0 | 0 | 0 |
| 4 | 1 | 0 | 0 | 0 | 28 |
| 4 | 2 | 28 | 28 | 28 | 28 |

Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; no causal future predictor is evaluated on these exposed tables.

## ConferenceParticipant02

Episodes: 28.

### Minimum additional reserve for half-repayment

Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.

| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |
|---|---:|---:|---:|---:|
| 1 | 0/28 | infeasible | infeasible | infeasible |
| 2 | 0/28 | infeasible | infeasible | infeasible |
| 3 | 17/28 | 3.5875 [2.6496, 3.5875] | 1.8512 | 1.1259 [1.1244, 1.1259] |
| 4 | 17/28 | 3.5875 [2.6496, 3.5875] | 1.8512 | 1.1259 [1.1244, 1.1259] |

### Fixed reserve grid

Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. All policies use the same per-slot capacity, reserve and zero-donor-loss floor.

| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1/4 | 0 | 0 | 0 | 0 |
| 1 | 1/2 | 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1/4 | 0 | 0 | 0 | 0 |
| 2 | 1/2 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1/4 | 0 | 0 | 0 | 0 |
| 3 | 1/2 | 0 | 0 | 0 | 0 |
| 3 | 1 | 0 | 0 | 0 | 0 |
| 3 | 2 | 8 | 17 | 17 | 17 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 4 | 1/4 | 0 | 0 | 0 | 0 |
| 4 | 1/2 | 0 | 0 | 0 | 0 |
| 4 | 1 | 0 | 0 | 0 | 0 |
| 4 | 2 | 8 | 17 | 17 | 17 |

Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; no causal future predictor is evaluated on these exposed tables.

## ParkFountains01

Episodes: 28.

### Minimum additional reserve for half-repayment

Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.

| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |
|---|---:|---:|---:|---:|
| 1 | 0/28 | infeasible | infeasible | infeasible |
| 2 | 0/28 | infeasible | infeasible | infeasible |
| 3 | 28/28 | 0.8533 [0.8533, 0.8533] | 0.4107 | 1.0925 [1.0925, 1.0925] |
| 4 | 28/28 | 0.8533 [0.8533, 0.8533] | 0.4107 | 1.0925 [1.0925, 1.0925] |

### Fixed reserve grid

Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. All policies use the same per-slot capacity, reserve and zero-donor-loss floor.

| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1/4 | 0 | 0 | 0 | 0 |
| 1 | 1/2 | 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1/4 | 0 | 0 | 0 | 0 |
| 2 | 1/2 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1/4 | 0 | 0 | 0 | 0 |
| 3 | 1/2 | 27 | 28 | 28 | 28 |
| 3 | 1 | 28 | 28 | 28 | 28 |
| 3 | 2 | 28 | 28 | 28 | 28 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 4 | 1/4 | 0 | 0 | 0 | 0 |
| 4 | 1/2 | 27 | 28 | 28 | 28 |
| 4 | 1 | 28 | 28 | 28 | 28 |
| 4 | 2 | 28 | 28 | 28 | 28 |

Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; no causal future predictor is evaluated on these exposed tables.

## River01

Episodes: 28.

### Minimum additional reserve for half-repayment

Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.

| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |
|---|---:|---:|---:|---:|
| 1 | 0/28 | infeasible | infeasible | infeasible |
| 2 | 0/28 | infeasible | infeasible | infeasible |
| 3 | 28/28 | 0.8761 [0.8761, 0.8762] | 0.3752 | 1.1926 [1.1926, 1.1927] |
| 4 | 28/28 | 0.8761 [0.8761, 0.8762] | 0.3752 | 1.1926 [1.1926, 1.1927] |

### Fixed reserve grid

Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. All policies use the same per-slot capacity, reserve and zero-donor-loss floor.

| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1/4 | 0 | 0 | 0 | 0 |
| 1 | 1/2 | 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1/4 | 0 | 0 | 0 | 0 |
| 2 | 1/2 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1/4 | 0 | 0 | 0 | 0 |
| 3 | 1/2 | 19 | 28 | 28 | 28 |
| 3 | 1 | 26 | 28 | 28 | 28 |
| 3 | 2 | 28 | 28 | 28 | 28 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 4 | 1/4 | 0 | 0 | 0 | 0 |
| 4 | 1/2 | 19 | 28 | 28 | 28 |
| 4 | 1 | 26 | 28 | 28 | 28 |
| 4 | 2 | 28 | 28 | 28 | 28 |

Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; no causal future predictor is evaluated on these exposed tables.

## Train01

Episodes: 28.

### Minimum additional reserve for half-repayment

Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.

| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |
|---|---:|---:|---:|---:|
| 1 | 0/28 | infeasible | infeasible | infeasible |
| 2 | 0/28 | infeasible | infeasible | infeasible |
| 3 | 28/28 | 2.5570 [1.6549, 2.5570] | 1.1619 | 1.1249 [1.1041, 1.2352] |
| 4 | 28/28 | 2.5570 [1.6549, 2.5570] | 1.1619 | 1.1249 [1.1041, 1.2352] |

### Fixed reserve grid

Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. All policies use the same per-slot capacity, reserve and zero-donor-loss floor.

| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1/4 | 0 | 0 | 0 | 0 |
| 1 | 1/2 | 0 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 2 | 0 | 0 | 0 | 0 |
| 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1/4 | 0 | 0 | 0 | 0 |
| 2 | 1/2 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 3 | 1/4 | 0 | 0 | 0 | 0 |
| 3 | 1/2 | 0 | 0 | 0 | 0 |
| 3 | 1 | 6 | 6 | 6 | 13 |
| 3 | 2 | 20 | 27 | 28 | 28 |
| 4 | 0 | 0 | 0 | 0 | 0 |
| 4 | 1/4 | 0 | 0 | 0 | 0 |
| 4 | 1/2 | 0 | 0 | 0 | 0 |
| 4 | 1 | 6 | 6 | 6 | 13 |
| 4 | 2 | 23 | 28 | 28 | 28 |

Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; no causal future predictor is evaluated on these exposed tables.

## Verification

- 304 minimum-reserve witnesses checked against original tables.
- 10080 matched online/oracle comparisons preserve both ledgers and zero donor loss.
- Unlimited-reserve feasibility agrees with the previous exact headroom frontier.
- Independent robust recursion checks every constructed scenario game.
- No repayment reference, impairment loss or target was reduced.
