# Proposed validation gates

**Not executed or preregistered.** This is a decision plan, not a report of new
results. Specify exact implementations and thresholds before each future batch;
keep all previous frozen outcomes. No new holdout is justified for the current
failed controller.

## 1. Is the conclusion robust to the accounting contract?

On exposed inputs, preserve the original bounded 1--5 index as the historical
primary result and separately report unclipped viewport PSNR and distortion
reductions where the source measurements permit. Do not call these MOS scales.
Vary the repayment target, initial loss severity and recovery horizon according
to an advance-fixed grid, including infeasible cases. Compare a fixed amount of
played media with a fixed wall-clock service deadline; these are different
contracts. Show sensitivity of feasibility counts and policy rankings, not only
one favorable mean.

Reason: debt and positive credits are sums of quality differences. With an
unrounded positive affine change q'=a*q+b, both scale by a and their repayment
ratio is unchanged. A nonlinear transform, clipping or rounding does not in
general preserve these differences or rankings. This elementary accounting
property is not a new theorem. A result that depends mainly on an arbitrary
mapping should be presented as mapping-dependent, not general compensation.

Deliverable: source-bound sensitivity matrix, example ranking reversals, and a
clear choice of operational units. **Proceed only if there is a useful, honestly
bounded insight after disclosing the sensitivities.** Do not relax the old
controller progression threshold retrospectively.

## 2. Does the timing finding survive realistic segment and buffer scales?

Use real, valid segment boundaries (for example 1, 2, 5 and 10 seconds where
the encodes permit); audit keyframes, actual duration, bytes and presentation
timestamps. Do not pretend a ten-second quality label is a one-second label.
Keep displayed duration, service rate, initial loss and cumulative entitlement
comparable in physical units, rather than allowing shorter segments more total
budget. Include cold and prebuffered starts, asynchronous users and delayed,
missing or reordered reports. All waiting and startup costs remain charged.

Integrate the completed and incremental feedback paths with a real software
player's decode/presentation timestamps. A physical HMD or human QoE study is
not necessary for an objective-metric claim, but sender/renderer alignment and
time of information availability must be measured. Retain a simulation-only
label until this is actually done. The current loopback protocol demonstrates
serialization/reconstruction, not that integration.

Deliverable: equal-contract timing comparison of cost-greedy, rolling Nash,
max-min and the diagnostic planners, plus actual packet/timestamp records.
**If the waiting penalty is specific to the current cold ten-second design,
narrow the conclusion accordingly.**

## 3. Is the finding larger than one small exposed catalogue?

Only after gates 1 and 2, choose a separate dataset or a defensibly independent
content-and-participant partition with adequate duration. Audit identities and
exposure before any tuning. More seeds, reversed pairs or policies on the same
traces are not independent replication. Freeze the claim, implementation,
outcomes and analysis before opening confirmation data. Keep per-content and
per-person dependence in the analysis; report clusters and descriptive ranges
rather than treating every timestep as an independent sample.

The present exact algorithm enumerates two-user, four-step actions. Either keep
that scope in the paper/title or establish exactness/optimality-gap and runtime
for larger populations and horizons. Old multi-user experiments using a
different controller do not validate this implementation's scalability.

Deliverable: genuinely separate confirmation of the **feasibility/timing
finding**, not another opportunity to select a winning controller. Failure may
still yield a useful boundary result, but must not be described as confirmation.

## 4. Does the framework help make a management decision?

Choose one concrete question, such as: what peak service, cumulative byte
entitlement and donor protection are required to offer a specified accounting
target over a specified duration? Return feasible witnesses and rejection
certificates for the finite catalogue. Distinguish offline provisioning bounds
from online admissions that require a valid uncertainty model; an offline
certificate cannot guarantee future viewport-dependent recovery.

Validate the proposed service contract under competing clients and variable
service/overhead, including violated-contract negative controls. Measure actual
available service rather than infer headroom from traffic usage. Compare against
simple cost-greedy, rolling Nash and max-min under matched information and
resource contracts. If a modern learned system is compared, implement its actual
method or label any simplification explicitly as a proxy.

Deliverable: an actionable tradeoff with deployment limits and overhead, not
another unvalidated optimal scheduler. A stronger paper may center on accurate
feasibility diagnosis even if no controller dominates every quality objective.

## Stop/go order

Start with exposed-data gate 1, then timing gate 2. Do not automatically launch
new acquisition or holdout evaluation. Gates 3 and 4 require a locked protocol
and the necessary data/integration authority. If no robust management insight
survives, keep the public artifact as a transparent research result rather than
force a full-journal novelty claim.
