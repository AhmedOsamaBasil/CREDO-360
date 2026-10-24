# Interpretation: capacity is the binding limitation in this contract

## Outcome

The fixed exposed-data audit is complete. It establishes an exact **offline
feasibility boundary**, not a successful causal controller or new holdout result.
The original event losses, recipient service floors, four recovery segments and
half-repayment target were not changed after inspection. The plan and method
were committed and pushed as `fa09f4f` before the complete audit ran.

At the original byte allowance, **0/168 episodes** can repay half their loss.
Even doubling that allowance leaves **0/168**, including when donor protections
are completely relaxed and all four recovery actions are allowed. The lowest
resource multiplier admitting even one episode under the most permissive
contract is approximately **2.09090**. Donor sacrifice alone cannot fix the
capacity shortage within these menus and this recovery horizon.

With **zero donor-quality loss** and up to four positive-gain recovery actions,
a 3x per-segment byte allowance permits half-repayment in **147/168 (87.5%)**
episodes. Approximately 3.27535x permits **157/168 (93.45%)**, the unrestricted
catalogue ceiling. The remaining eleven are all ConferenceParticipant02
episodes and cannot meet the fixed target with any combination of available
representations over these four segments. Their infeasibility is retained.

## Resource and donor allowances

All values below are minimum peak per-segment encoded-byte multipliers relative
to the unchanged two-user rung2 baseline. They are approximate displays of
exact rational breakpoints in `results.json.gz`, not bandwidth measurements or
stall guarantees. Coverage thresholds include **all 168 episodes**, including
the impossible ones; they are not conditional medians. M=4 throughout.

| Donor per-segment cap | Cumulative positive-loss cap | Resource for >=50% of episodes | >=75% | >=90% |
|---:|---:|---:|---:|---:|
| 0 | 0 | 2.66541x | 2.78982x | 3.27535x |
| 0.25 | 0.5 | 2.66541x | 2.78982x | 3.27535x |
| 0.5 | 1 | 2.56388x | 2.70124x | 3.27023x |
| 0.5 | 2 | 2.56388x | 2.70124x | 3.27023x |
| 1 | 4 | 2.37747x | 2.70124x | 3.27023x |
| Fully relaxed (4) | Fully relaxed (16) | 2.36516x | 2.50547x | 3.02917x |

No listed contract reaches 100% at any resource allowance. The 90% threshold
means at least 152/168 episodes, not 90% of the recoverable subset. Donor caps
use objective utility-segments, not MOS; positive losses are never refunded
by later surplus. A 2.79x allowance is approximately **179% additional peak
byte headroom**, not a 2.79% increase and not a financial budget.

Mild donor concessions can reduce resource needs for some individual episodes,
but the .25/.5 contract does not improve the displayed pooled coverage
thresholds. Doubling total allowance from 1 to 2 with step cap 0.5 leaves those
thresholds unchanged. Fully relaxing protection yields a lower resource bound,
not an acceptable operational recommendation. The source has correlated
episodes and discrete ladders, so these are descriptive counts, not population
success estimates. Cohort/scene tables and every other fixed budget query are
retained in the [generated report](results/audit_v1/REPORT.md) and full artifact.

## Number of recovery actions

Under zero donor loss, allowing one, two or four positive-gain actions gives
unrestricted-resource ceilings of **56, 117, 157 episodes**, respectively.
At 3x capacity the corresponding counts are 56, 97, 147. With only two actions,
some recoverable episodes require resource factors above 4; the maximum minimum
factor is approximately 11.45. Spreading repayment across four opportunities
can therefore be substantially less resource-demanding than concentrating it.

The old one-action, step 0.5 / total 0.5 contract remains infeasible at its original
1x resource allowance even with this broader action menu. Its 56/168 ceiling
at sufficiently high resources does not overturn the earlier negative result:
the extra resources are an explicit changed allowance.

At 3x capacity under zero donor loss, all 168 episodes have at least two positive
opportunities, 159 have at least two individually capable of repaying a quarter
of the target, and 147 meet the full target. Individual opportunity counts do
not establish joint feasibility or the necessity of a timing predictor.

## Implication for the research approach

The immediate issue is not resolved by training a more sophisticated predictor:
below these feasibility limits, even a future-known oracle cannot satisfy the
contract. These conclusions apply to the specified two-user catalogue audit,
not all streaming systems or every earlier five-user experiment.

There is a further structural limitation. With M=4 and zero donor loss, every
constraint in this audit is per-segment: cumulative donor loss is automatically
zero and the action-count cap cannot bind across four segments. Thus maximizing
the recipient gain independently in each segment maximizes total recovery.
Given exact current action qualities, this simple rule needs no future forecast
and reaches the offline maximum. Feasibility under that contract **cannot by
itself support a new temporal scheduling contribution**.

Do not consume another holdout or present the exposed-data feasibility result
as method superiority. A defensible next decision is whether such substantial
post-impairment headroom is realistic. If it is, a genuinely scarce cumulative
reserve (or another physically justified intertemporal constraint) could create
a meaningful allocation/timing problem; its objective and simple-baseline
separations should be tested analytically first. That would be a new contract,
not a retroactive explanation of this audit. If the headroom is unrealistic,
revisit the service specification, encoding ladder or impairment model openly,
without lowering the current target and relabeling it as successful recovery.

No controller change, new prediction experiment, fresh data collection,
manuscript revision or acknowledgment edit was made during this audit.

## Verification and artifacts

- 17 synthetic tests pass, including direct search, pruned/unpruned enumeration,
  independent dynamic programming and exact boundary comparisons.
- 97,601 pruned complete schedules examined; all 6,815 staircase witnesses replay
  their original quality/byte data and conserve the fixed recovery ledger.
- 7,056 independent DP comparisons over the fixed displayed contracts pass.
- An additional **post-run validation**, without changing the method or target,
  checks every exact staircase endpoint: 18,135 DP decisions verify feasibility,
  minimum cumulative harm, and minimum resource for that harm. Both OSes pass.
- Full scientific replay/hash verification passes on Windows (Python 3.12.14) and
  Linux (Python 3.14.4), with identical scientific SHA256:
  `1378353ca5e0d0d3db0ad4d194f8454aedb612ab5f0db4ed83b66bb9b1f3ae2c`.
- Windows regression: 178 tests and 24 subtests; Linux: 174 and 24 (four optional
  torch tests excluded). Portable suite: 5 tests on each OS. All pass.
- Previous absolute-loss/causal-opportunity artifact fully replays on both OSes
  with its original scientific hash unchanged. Earlier frozen files are not edited.

The [figure](results/audit_v1/figures/feasibility_frontier.png) shows both action
count and donor-loss effects. Its renderer and data hashes are recorded
separately; it is a visualization of the frozen audit, not an additional test.
