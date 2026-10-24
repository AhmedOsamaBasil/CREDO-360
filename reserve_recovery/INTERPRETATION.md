# Headroom and a limited reserve: findings and next decision

## What is established

The work is complete on **existing exposed data and constructed analytical
examples only**. The method and plan were pushed as `515549b` before the full
catalogue calculation. The old event losses, service references and target of
repaying at least half the loss were retained. No new holdout was consumed.

There are now two separately enforced resource constraints:

1. Each segment must fit its contemporaneous payload-capacity budget.
2. The sum of positive bytes above the original baseline must fit a finite
   episode reserve. There is no refill or refund within the episode.

The reserve is an entitlement to use additional bytes **when physical service
exists**, not storage of past idle bandwidth. Quality debt is a different
ledger and decreases only through delivered excess quality. Donor loss is zero
throughout the exposed-table calculation. Full source, results, witnesses and
checks are in this package; no manuscript or acknowledgment was edited.

## Is the headroom realistic?

**The available evidence cannot establish field headroom, but it can quantify
the demand much more meaningfully than a relative multiplier alone.**

The 30 existing captured-traffic traces contain 4,368 one-second bins of
observed traffic, not available path capacity. Earlier live links were
configured and the corrected replay capacities were synthetic. We cannot infer
unused capacity or competing-load guarantees from those records. This follows
the capacity/usage distinction in [RFC5136](https://www.rfc-editor.org/rfc/rfc5136.html#section-2.3.4).

Across the 24 recovery content/segment contexts, the original two-user rung2
baseline is **0.3521--0.5157 Mbit/s** of payload. With the fixed 3x per-segment
cap, 147/168 episodes admit half-repayment at some cumulative reserve. Among
those feasible episodes, the **minimum additional reserve** has:

| Demand quantity | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Extra payload over the four-slot episode | 0.8533 MB | 1.7109 MB | 3.5875 MB |
| Maximum per-slot total payload rate of that witness | 1.0925 Mbit/s | 1.1707 Mbit/s | 1.2352 Mbit/s |
| Extra payload rate averaged over all 40 seconds | 0.1707 Mbit/s | 0.3422 Mbit/s | 0.7175 Mbit/s |

MB means decimal million bytes. Rate is bytes divided by the 10-second slot,
not an instantaneous wire-rate measurement. The minimum-reserve witness is
not also optimized for minimum peak rate. Quantiles exclude the 21 episodes
infeasible at 3x; the denominator is explicit rather than silently discarded.

These rates are not intrinsically extreme compared with the previously
configured whole-bottleneck profiles, but those links served other clients.
They do **not** prove that this much residual service is available to this
particular pair. The content was encoded at 1920x960, not 8K delivery. Transport
overhead, competing sessions, within-slot variability and deadlines still need
to be accounted for before claiming deployment feasibility. The previous 3x
factor should not be interpreted as tripling an entire physical link.

## What a finite reserve changes

Let rho be extra reserve divided by the sum of the four original pair-baseline
byte counts. Thus rho=1 permits at most an additional baseline episode's bytes,
not unlimited use of the peak capacity. The median minimum rho among feasible
episodes is 0.7076. It is a descriptive requirement, **not** a chosen service
budget or a guarantee for every episode.

At a 3x peak cap, target-attainment counts are:

| Extra reserve fraction rho | Rolling Nash | Rolling max-min | Greedy compensation | Future-known oracle |
|---:|---:|---:|---:|---:|
| 0.25 | 0/168 | 0/168 | 0/168 | 0/168 |
| 0.5 | 46/168 | 56/168 | 56/168 | 56/168 |
| 1 | 82/168 | 90/168 | 90/168 | 97/168 |
| 2 | 115/168 | 145/168 | 147/168 | 147/168 |

These are exact finite-catalogue calculations with known **current** qualities
for the three causal controls. Only the oracle uses realized future qualities.
No new causal future predictor is evaluated in this table. A gap from rolling
fairness can reflect different objectives; the greedy compensation control
retains the same recovery priority and is therefore important.

At rho=1, increasing the peak cap from 3x to 4x leaves oracle attainment at 97/168,
but reduces greedy/max-min attainment from 90 to 62 and Nash from 82 to 60.
Larger early actions can exhaust a fixed cumulative reserve. This is a real
distinction between peak and cumulative budgets, not a violation of oracle
feasibility monotonicity. It is not evidence that less network capacity is
generally better. All grid cells and quality metrics are retained, including
the <=2x cases where no policy can meet the target.

At 3x/rho2 the greedy rule already matches the oracle's target-attainment count.
There is no reason to claim a timing innovation from that nonbinding-budget
case. At 4x/rho2 both greedy and max-min reach 157/168; the same eleven catalogue-
limited episodes remain impossible. A selective report of the largest oracle
gap would overstate how broadly a temporal method is needed.

Recovery is also not synonymous with higher post-event quality. At 3x/rho1,
the mean episode worst-user quality is 4.0582 for Nash, 4.0202 for max-min,
4.0051 for greedy and 3.9993 for the recovery oracle. Mean quality is 4.1729
for Nash versus 4.1559 for that oracle. These descriptive trade-offs remain
even though all users retain their reference floors. They preclude calling
better compensation a universal improvement in objective quality or fairness.

## Analytical comparison: a conditional improvement, not a new theorem

Eight constructed cases were checked by complete causal-policy enumeration
and an independent robust Bellman recursion. Both enforce integral actions,
shared-prefix nonanticipation, the reserve and instantaneous capacity.

- **Useful timing case:** current gain 0.4; the next gain is either 0.6 or 0.9;
  only one boost fits the reserve. The robust causal plan waits and has worst
  unpaid fraction 0.4, versus 0.6 for rolling Nash, rolling max-min and greedy.
  It meets half-repayment in both declared futures. This requires the supplied
  lower-opportunity model to be correct; it is not a learned guarantee.
- **Delayed revelation:** the corresponding worst losses are 0.3 versus 0.8.
  This constructed example confirms that spending a small amount early can
  block a later indivisible action. It is not an empirical effect estimate.
- **No timing need:** when both boosts fit the reserve, all rules fully recover.
  With no reserve or no contemporaneous capacity, no rule recovers.
- **Causal admission gap:** both futures individually permit offline unpaid
  loss 0.4, but every shared-prefix causal rule has worst loss at least 0.7.
  The half-repayment contract is explicitly rejected; future-known feasibility
  must not be substituted for causal admission.
- **Wrong future model:** if the expected later opportunity disappears, the
  waiting rule leaves all loss unpaid, versus 0.6 for immediate controls.
  The executor flags model breach and remains reserve-safe, but cannot restore
  the missed service guarantee.

The complete proofs and prior-art boundaries are in [THEORY.md](THEORY.md).
Token accounting, multiple-choice budget optimization and robust dynamic
programming are established tools. The contribution here is an executable
service contract and diagnosis, not a newly invented optimization principle.

## What should happen before another holdout

This is a coherent setting for timing research, but not yet a validated novel
streaming controller. The next defensible step is an **exposed-data-only
admission and opportunity-model study** with a justified service budget:

1. Specify where residual payload service comes from: an enforced reservation
   or a measured controlled bottleneck after all baseline clients and overhead.
   Validate availability over the actual delivery deadlines.
2. Set the cumulative reserve for an operational reason, not because a selected
   rho produces a large oracle gap. Keep reserve-expense and quality trade-offs.
3. Test whether a causal opportunity model can safely distinguish when to spend
   or retain it. Retain model misses, rejected admissions and best-effort cases.
4. Compare against greedy, rolling controls and a model-aware optimizer. Only
   a meaningful gain under matched information justifies a new frozen holdout.

No such new network measurement, fitted opportunity model or fresh experiment
has been launched by this analysis.

## Verification

- 17 new synthetic tests, including 18 exact formula instances, pass.
- Windows: 195 tests plus 24 subtests; Linux: 191 plus 24 (four optional torch
  tests omitted). Portable suite: 5 tests on each OS. All pass.
- Both platforms fully regenerate all 8 constructed cases, 168 catalogue
  episodes, 304 minimum-reserve witnesses and 10,080 online/oracle comparisons.
- A separately labeled **post-run independent check** enumerates 1,336,174
  unpruned integral paths and verifies 4,032 exact minimum-cost/budget queries.
  Both platforms agree; no method or target was altered after outcomes.
- Scientific SHA256:
  `f547b786ef5e9fd4514f42b64003ecd1b5f92ee7eb0c57d8fe57b2a38e51158f`.
- The previous feasibility-frontier artifact still fully replays with its
  unchanged scientific hash. Historical sources/results were not edited.

See the [generated report](results/analysis_v1/REPORT.md),
[reserve-grid figure](results/analysis_v1/figures/reserve_grid.png), and the full
machine-readable results and verification records beside them.
