# Resource and donor-loss feasibility audit

**Exposed data only; exact future-known feasibility, not online performance.** Original losses and rung-2 references are unchanged. The target remains at least half of the original loss repaid.

Lambda is a per-segment encoded-byte allocation multiplier, not aggregate bytes, measured throughput or a stall guarantee. Donor loss uses the objective index and sums only positive losses; surplus never refunds it. All action schedules are integral. Quantiles below are conditional on feasible episodes; coverage thresholds use ALL episodes.

## all

Episodes: 168.

| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |
|---|---:|---:|---:|
| legacy: M1, step 0.5, total 0.5 | 56/168 | 2.2798 | infeasible |
| no_donor_loss: M4, step 0, total 0 | 157/168 | 2.6654 | 2.7898 |
| step025_total05: M4, step 0.25, total 0.5 | 157/168 | 2.6654 | 2.7898 |
| step05_total1: M4, step 0.5, total 1 | 157/168 | 2.5639 | 2.7012 |
| step05_total2: M4, step 0.5, total 2 | 157/168 | 2.5639 | 2.7012 |
| step1_total4: M4, step 1, total 4 | 157/168 | 2.3775 | 2.7012 |

| Contract | lambda 1 | lambda 1.1 | lambda 1.25 | lambda 1.5 | lambda 2 | lambda 3 | lambda 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0 | 0 | 0 | 0 | 0 | 56 | 56 |
| no_donor_loss | 0 | 0 | 0 | 0 | 0 | 147 | 157 |
| step025_total05 | 0 | 0 | 0 | 0 | 0 | 147 | 157 |
| step05_total1 | 0 | 0 | 0 | 0 | 0 | 147 | 157 |
| step05_total2 | 0 | 0 | 0 | 0 | 0 | 147 | 157 |
| step1_total4 | 0 | 0 | 0 | 0 | 0 | 147 | 157 |

Counts are episodes capable of half-repayment, not observed success rates of an online controller. The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.

## v2

Episodes: 84.

| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |
|---|---:|---:|---:|
| legacy: M1, step 0.5, total 0.5 | 56/84 | 2.2798 | infeasible |
| no_donor_loss: M4, step 0, total 0 | 84/84 | 2.6654 | 2.7898 |
| step025_total05: M4, step 0.25, total 0.5 | 84/84 | 2.6654 | 2.7898 |
| step05_total1: M4, step 0.5, total 1 | 84/84 | 2.5639 | 2.7012 |
| step05_total2: M4, step 0.5, total 2 | 84/84 | 2.5639 | 2.7012 |
| step1_total4: M4, step 1, total 4 | 84/84 | 2.3775 | 2.5055 |

| Contract | lambda 1 | lambda 1.1 | lambda 1.25 | lambda 1.5 | lambda 2 | lambda 3 | lambda 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0 | 0 | 0 | 0 | 0 | 56 | 56 |
| no_donor_loss | 0 | 0 | 0 | 0 | 0 | 84 | 84 |
| step025_total05 | 0 | 0 | 0 | 0 | 0 | 84 | 84 |
| step05_total1 | 0 | 0 | 0 | 0 | 0 | 84 | 84 |
| step05_total2 | 0 | 0 | 0 | 0 | 0 | 84 | 84 |
| step1_total4 | 0 | 0 | 0 | 0 | 0 | 84 | 84 |

Counts are episodes capable of half-repayment, not observed success rates of an online controller. The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.

## v3

Episodes: 84.

| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |
|---|---:|---:|---:|
| legacy: M1, step 0.5, total 0.5 | 0/84 | infeasible | infeasible |
| no_donor_loss: M4, step 0, total 0 | 73/84 | 2.6795 | 2.9973 |
| step025_total05: M4, step 0.25, total 0.5 | 73/84 | 2.6795 | 2.9973 |
| step05_total1: M4, step 0.5, total 1 | 73/84 | 2.6056 | 2.9536 |
| step05_total2: M4, step 0.5, total 2 | 73/84 | 2.6056 | 2.9536 |
| step1_total4: M4, step 1, total 4 | 73/84 | 2.3829 | 2.9536 |

| Contract | lambda 1 | lambda 1.1 | lambda 1.25 | lambda 1.5 | lambda 2 | lambda 3 | lambda 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no_donor_loss | 0 | 0 | 0 | 0 | 0 | 63 | 73 |
| step025_total05 | 0 | 0 | 0 | 0 | 0 | 63 | 73 |
| step05_total1 | 0 | 0 | 0 | 0 | 0 | 63 | 73 |
| step05_total2 | 0 | 0 | 0 | 0 | 0 | 63 | 73 |
| step1_total4 | 0 | 0 | 0 | 0 | 0 | 63 | 73 |

Counts are episodes capable of half-repayment, not observed success rates of an online controller. The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.

## BuskingUnderpass05

Episodes: 28.

| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |
|---|---:|---:|---:|
| legacy: M1, step 0.5, total 0.5 | 0/28 | infeasible | infeasible |
| no_donor_loss: M4, step 0, total 0 | 28/28 | 2.6795 | 3.2753 |
| step025_total05: M4, step 0.25, total 0.5 | 28/28 | 2.6795 | 3.2753 |
| step05_total1: M4, step 0.5, total 1 | 28/28 | 2.6056 | 3.2702 |
| step05_total2: M4, step 0.5, total 2 | 28/28 | 2.6056 | 3.2702 |
| step1_total4: M4, step 1, total 4 | 28/28 | 2.6056 | 3.2702 |

| Contract | lambda 1 | lambda 1.1 | lambda 1.25 | lambda 1.5 | lambda 2 | lambda 3 | lambda 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no_donor_loss | 0 | 0 | 0 | 0 | 0 | 18 | 28 |
| step025_total05 | 0 | 0 | 0 | 0 | 0 | 18 | 28 |
| step05_total1 | 0 | 0 | 0 | 0 | 0 | 18 | 28 |
| step05_total2 | 0 | 0 | 0 | 0 | 0 | 18 | 28 |
| step1_total4 | 0 | 0 | 0 | 0 | 0 | 18 | 28 |

Counts are episodes capable of half-repayment, not observed success rates of an online controller. The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.

## Cheerleading01

Episodes: 28.

| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |
|---|---:|---:|---:|
| legacy: M1, step 0.5, total 0.5 | 0/28 | infeasible | infeasible |
| no_donor_loss: M4, step 0, total 0 | 28/28 | 2.4661 | 2.4661 |
| step025_total05: M4, step 0.25, total 0.5 | 28/28 | 2.4661 | 2.4661 |
| step05_total1: M4, step 0.5, total 1 | 28/28 | 2.4139 | 2.4139 |
| step05_total2: M4, step 0.5, total 2 | 28/28 | 2.4139 | 2.4139 |
| step1_total4: M4, step 1, total 4 | 28/28 | 2.3303 | 2.3303 |

| Contract | lambda 1 | lambda 1.1 | lambda 1.25 | lambda 1.5 | lambda 2 | lambda 3 | lambda 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no_donor_loss | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step025_total05 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step05_total1 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step05_total2 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step1_total4 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |

Counts are episodes capable of half-repayment, not observed success rates of an online controller. The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.

## ConferenceParticipant02

Episodes: 28.

| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |
|---|---:|---:|---:|
| legacy: M1, step 0.5, total 0.5 | 0/28 | infeasible | infeasible |
| no_donor_loss: M4, step 0, total 0 | 17/28 | 2.9973 | infeasible |
| step025_total05: M4, step 0.25, total 0.5 | 17/28 | 2.9973 | infeasible |
| step05_total1: M4, step 0.5, total 1 | 17/28 | 2.9536 | infeasible |
| step05_total2: M4, step 0.5, total 2 | 17/28 | 2.9536 | infeasible |
| step1_total4: M4, step 1, total 4 | 17/28 | 2.9536 | infeasible |

| Contract | lambda 1 | lambda 1.1 | lambda 1.25 | lambda 1.5 | lambda 2 | lambda 3 | lambda 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no_donor_loss | 0 | 0 | 0 | 0 | 0 | 17 | 17 |
| step025_total05 | 0 | 0 | 0 | 0 | 0 | 17 | 17 |
| step05_total1 | 0 | 0 | 0 | 0 | 0 | 17 | 17 |
| step05_total2 | 0 | 0 | 0 | 0 | 0 | 17 | 17 |
| step1_total4 | 0 | 0 | 0 | 0 | 0 | 17 | 17 |

Counts are episodes capable of half-repayment, not observed success rates of an online controller. The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.

## ParkFountains01

Episodes: 28.

| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |
|---|---:|---:|---:|
| legacy: M1, step 0.5, total 0.5 | 28/28 | 2.5639 | 2.5639 |
| no_donor_loss: M4, step 0, total 0 | 28/28 | 2.6654 | 2.6654 |
| step025_total05: M4, step 0.25, total 0.5 | 28/28 | 2.6654 | 2.6654 |
| step05_total1: M4, step 0.5, total 1 | 28/28 | 2.5639 | 2.5639 |
| step05_total2: M4, step 0.5, total 2 | 28/28 | 2.5639 | 2.5639 |
| step1_total4: M4, step 1, total 4 | 28/28 | 2.3775 | 2.3775 |

| Contract | lambda 1 | lambda 1.1 | lambda 1.25 | lambda 1.5 | lambda 2 | lambda 3 | lambda 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| no_donor_loss | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step025_total05 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step05_total1 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step05_total2 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step1_total4 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |

Counts are episodes capable of half-repayment, not observed success rates of an online controller. The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.

## River01

Episodes: 28.

| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |
|---|---:|---:|---:|
| legacy: M1, step 0.5, total 0.5 | 28/28 | 2.2647 | 2.2647 |
| no_donor_loss: M4, step 0, total 0 | 28/28 | 2.4251 | 2.4251 |
| step025_total05: M4, step 0.25, total 0.5 | 28/28 | 2.4251 | 2.4251 |
| step05_total1: M4, step 0.5, total 1 | 28/28 | 2.2647 | 2.2647 |
| step05_total2: M4, step 0.5, total 2 | 28/28 | 2.2647 | 2.2647 |
| step1_total4: M4, step 1, total 4 | 28/28 | 2.0985 | 2.0985 |

| Contract | lambda 1 | lambda 1.1 | lambda 1.25 | lambda 1.5 | lambda 2 | lambda 3 | lambda 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| no_donor_loss | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step025_total05 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step05_total1 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step05_total2 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step1_total4 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |

Counts are episodes capable of half-repayment, not observed success rates of an online controller. The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.

## Train01

Episodes: 28.

| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |
|---|---:|---:|---:|
| legacy: M1, step 0.5, total 0.5 | 0/28 | infeasible | infeasible |
| no_donor_loss: M4, step 0, total 0 | 28/28 | 2.7898 | 2.7898 |
| step025_total05: M4, step 0.25, total 0.5 | 28/28 | 2.7898 | 2.7898 |
| step05_total1: M4, step 0.5, total 1 | 28/28 | 2.7012 | 2.7012 |
| step05_total2: M4, step 0.5, total 2 | 28/28 | 2.7012 | 2.7012 |
| step1_total4: M4, step 1, total 4 | 28/28 | 2.7012 | 2.7012 |

| Contract | lambda 1 | lambda 1.1 | lambda 1.25 | lambda 1.5 | lambda 2 | lambda 3 | lambda 4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| no_donor_loss | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step025_total05 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step05_total1 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step05_total2 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |
| step1_total4 | 0 | 0 | 0 | 0 | 0 | 28 | 28 |

Counts are episodes capable of half-repayment, not observed success rates of an online controller. The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.

## Verification

- 6815 staircase witnesses replay against original tables.
- 7056 independent dynamic-programming decisions match enumeration.
- All tested allowance monotonicity checks pass.
- Unrestricted catalogue ceiling agrees with the prior diagnosis: 157/168 episodes.

No new holdout, new participants, human-QoE claim, causal guarantee or novel optimization theorem is implied. An acceptable donor/resource contract remains a service-design choice.
