# Recovery pilot v1: interpretation and next decision

The fixed pilot completed: 12 paired seeds x 4 scenarios x 8 policies x 60
rounds x 5 clients = 115,200 user-round records. No test-driven retuning or
selective seed removal was performed. The progression criterion **failed**.

## What was repaired and verified

The model is trained on objective PSNR-index labels. Training, calibration and
test source-ID groups are disjoint (10/9/9). The joint quality/direct-gain
radius is 0.474135 index units. All nine held-out catalogue panels satisfy the
joint envelope. For the candidate, unshifted selected-action and gain coverage
are 100% on these dependent replay observations. This is not precise evidence
of population coverage, conditional validity, or arbitrary-shift adaptation.
The deliberately injected prediction shift reduces selected quality coverage
to approximately 74%; no adaptation claim is warranted.

Independent row checks verify input/source/result hashes, actual objective
labels, causal capacity forecasts, selected predictions and gain bounds,
admission budgets, all debt updates, playback conservation and saved summaries.
Maximum pilot clock-conservation residual is about 1.4e-14 seconds.

Windows regression: 52 tests and 12 subtests passed. Linux portable regression:
48 tests and 12 subtests passed; the four legacy PyTorch tests were not runnable
in that Linux environment because its PyTorch dependency is absent. They passed
in Windows. The existing Linux virtual environment, not the bare system Python,
contains pytest.

The first seed was repeated in Linux. All 9,600 scientific records matched
Windows exactly; CPU timing fields were excluded. That single seed happens to
pass the screening criterion, while the full 12-seed campaign fails. It is
retained as a reproducibility check, NOT selected as efficacy evidence.

The corrected live runner passed a two-client/three-round real DASH smoke test:
six records, exact buffer/time conservation to stored precision, and observed
post-completion waiting up to 0.10854 seconds. This is not a powered live
recovery study. Synthetic unit tests additionally exercise much longer waits,
right-censored deliveries and inter-round idle time.

## What the mechanism did not establish

In the known-ceiling scenario, candidate minus bounded-quality debt:

| Outcome | Mean paired difference | Descriptive 95% seed-bootstrap interval |
|---|---:|---:|
| Cumulative shortfall (index-rounds/user) | +0.19636 | [0.00843, 0.41307] |
| Post-restoration shortfall (index-rounds/user) | -0.00847 | [-0.15870, 0.14408] |
| Stall (seconds/user) | +0.09215 | [-1.41192, 1.44067] |
| Worst-user mean objective index | -0.00161 | [-0.00700, 0.00463] |

These intervals condition on this finite, looped catalogue and are exploratory;
they are not independent-subject or content-generalization inference. All
comparators and scenarios remain in the raw/summary artifacts.

The new score is algebraically distinct and its gain bound has the correct
target semantics, but those repairs alone did not yield a performance advantage.
The candidate's cumulative shortfall was also worse than its uncertified
counterpart and the memoryless version in the known-ceiling scenario. Compare
worst-user quality and stall as well: persistent memory can trade aggregate
quality for protection of the worst user. Do not claim that debt is universally
harmful, or that this pilot establishes perceptual superiority of any policy.

## Decision

Do not update the paper to claim successful recovery, superiority from calibrated
gating, or established new-method novelty. Keep the acknowledgment unchanged.
The software corrections and this negative result should be reviewed first.

The next research decision is between (a) a simpler objective-quality debt
study that explicitly evaluates its fairness/efficiency trade-off, and (b) a
new mechanism with a principled service-feasibility/recovery objective and a
separate development/evaluation split. Further tuning on the current nine test
IDs would turn them into development data and requires new held-out evidence.
Neither option justifies resubmission of the old manuscript unchanged.

Larger validation still missing: independently held-out content/dataset, actual
immersive-player transport with the new controller, 10--30-user allocation
quality versus exact/reference optima, and full-text closest-work novelty review.
