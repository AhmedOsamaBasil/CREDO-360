# Development outcome: loss protection exposes insufficient opportunities

**The locked development screen failed. No fresh holdout or manuscript claim
is justified by this batch.** The code implements the absolute-loss constraint
and causal forecast correctly under their stated assumptions, but the tested
service contract cannot deliver meaningful compensation on these exposed data.

Implementation and plan were published as `a9781e5` before execution. All 168
planned episodes and every comparator/sensitivity were retained. No parameter
was retuned after outcomes. Windows and Linux reproduced every outcome and
certificate with canonical scientific SHA256
`74965a6cd969334dc66e8f91094b432578c38533abb7f85e291a492adc605017`.

## 1. What the constraint actually did

The primary service request was to leave at most half of the original event
loss unpaid. **Zero of 168 episodes were admitted as feasible.** The .25 and
.75 unpaid-fraction sensitivities also admitted zero. Every primary episode
therefore used the explicitly labeled infeasible-cap fallback and violated
the requested terminal cap. The original loss and cap were never changed.

The report's zero violations *among feasible admissions* is vacuous: there
were no such admissions. It is not evidence that the method achieved safe
recovery. All policies still obeyed the separate local recipient-floor, donor
loss, byte and one-transfer constraints on every actual trajectory.

The analytical unit tests establish a different, useful result: a pathwise
absolute cap excludes risky mixture components even if their average looks
acceptable. In the original D=2, gain-1-now, gain-0-or-2-later example, alpha=.5
forces spending now, raising the best regret from .25 to .5. This is the
protection/regret trade-off, not a new empirical performance claim.

## 2. Comparison with the requested baselines

Mean terminal unpaid fraction, lower is better:

| Exposed cohort | Constrained KNN fallback | Rolling Nash | Rolling max-min |
|---|---:|---:|---:|
| v2, 84 episodes | 0.999867888 | 1.000000000 | 0.999878800 |
| v3, 84 episodes | 0.998840318 | 1.000000000 | 0.998426644 |
| Pooled, 168 episodes | 0.999354103 | 1.000000000 | 0.999152722 |

The small gain over Nash does not constitute useful restoration: the candidate
leaves about **99.94%** of event loss unpaid on average. It is also worse than
rolling max-min in v3 and pooled. The full-knowledge one-transfer oracle leaves
about **99.91%** unpaid. Greedy recovery happens to match that oracle in this
particular batch. Forecasting sophistication is not establishing a benefit.

Candidate mean original loss is 1.841637 utility units and mean unpaid loss is
1.840357. Mean donor loss is .087048 utility, while the candidate's average
delivered compensation is only .001280. These are different users' objective
utility units, not psychological costs; nevertheless they make clear that the
tiny recipient gain is not a free Pareto improvement. Post-event mean quality
falls from Nash's 4.000848 to 3.990127. The frozen .03 mean-quality guard passes,
but passing a guard is not evidence of a worthwhile trade-off.

No independence-based confidence interval or p-value is attached to these
development aggregates. The same participants/content are reused, and current
counterfactual quality is revealed equally to every policy.

## 3. The more decisive finding: this menu cannot exercise timing

The separately labeled post-hoc diagnosis reconstructs opportunity headroom
from the saved episodes and original input tables, without changing the replay:

- Only **44 of 672 recovery-period opportunities** have positive transferable
  gain under the common menu and constraints.
- **124 episodes have no positive opportunity; 44 have exactly one; none has
  two or more.** There is no realized competition between an early and a later
  positive opportunity in this batch. It is therefore not a discriminating
  empirical test of the intended spend-versus-save trade-off.
- The largest allowable single gain is .016 utility, versus initial event
  losses ranging from .854 to 2.467. Even perfect future knowledge cannot meet
  half-repayment in any episode.
- Summing every available menu gain across all four periods, while dropping
  the one-transfer and cumulative donor restriction, still meets half-repayment
  in zero episodes. The one-transfer limit alone is not the explanation.
- An optimistic upper bound discarding byte, donor and transfer restrictions,
  and using the best existing recipient rung every period, permits half-
  repayment in **157/168** episodes. This is not a feasible controller result.
  It shows that the failure is not an intrinsic impossibility of future service
  compensation: the declared reference/menu/resource/protection combination
  is the limiting setting. The upper bound does not identify which alternative
  contract would be acceptable or fair.

See `results/development_v1/posthoc_opportunity_diagnosis.json` and its separate
hash sidecar. `python -m causal_compensation.diagnose` reconstructs it. It was
written after the primary results and was not used for tuning.

## 4. Why 100% forecast coverage is not a success claim

Every observed future trajectory lies inside the nearest-neighbor envelope,
both before and after gain clipping at D. However, **every envelope has zero
lower gain bounds at all three future positions**. Average interval width is
.051583 utility, exceeding the largest actual gain .016. The fixed .05 padding
therefore covers a mostly zero-opportunity sequence easily while certifying
no useful future compensation. Midpoint gain MAE is .025228 utility.

This is wide, uncalibrated coverage on exposed data, not evidence of a sharp
or generalizable opportunity model. Cross-content/participant exclusion and
future-mutation tests establish the intended information boundary, not unseen-
data prediction validity. The forecast is causal only within the explicitly
idealized exact-current-utility interface.

## 5. Verification and next decision

- New targeted tests: 19 pass.
- Full regression: Windows161 tests plus24 subtests; Linux157 plus24. The four
  additional Windows tests use its available Torch environment.
- Portable-model suite: five tests pass on each platform.
- Both systems recompute all 168 outcomes, conditional certificates, source/
  input/result hashes and the separate post-hoc diagnosis exactly. Previous
  allowance-analysis hashes/results remain unchanged and verify on both.

The next meaningful task is a **feasibility-frontier audit on exposed data**:
establish whether a defensible reference and resource/donor allowance produce
substantial recoverable loss and at least two competing opportunities. Report
the necessary costs rather than lowering the cap until the method passes.
Only a scientifically justified contract with nontrivial headroom would make
further opportunity-model development informative. No fresh data should be
consumed merely to repeat this infeasible setting. A different contract or
multi-transfer mechanism would be a new, explicitly versioned development
study, not a retroactive repair of this failed screen.
