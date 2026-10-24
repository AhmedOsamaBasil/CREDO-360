# What this development test can establish

## Service and reserve are different constraints

In each 10-second slot the pair may deliver at most A=1,500,000 application
payload bytes. Separately, additional bytes above the original pair baseline
consume a finite episode reserve R; its debit is max(S_t-B_t,0). It never
refills, and unused physical capacity is not banked. The old event loss D is
unchanged. Only actual positive quality above the fixed reference pays D down.
Both ledgers are pathwise constraints, not constraints merely in expectation.

The service test provisions an isolated HTB class and checks receiver-confirmed
TCP completion under competition. Nominal 1.5 Mbit/s class rate and 1.2 Mbit/s
payload demand leave 20% headroom for protocol behavior; this margin is a test
choice, not an inferred theorem. The joint measured deadline is9.5s and the
whole client subprocess must finish within10s. Those observations support only
the tested configuration. Controller execution is not included in the TCP
probe and therefore an integrated controller/player deadline remains untested.

Observed traffic is not unused service capacity; this distinction follows
[RFC5136](https://www.rfc-editor.org/rfc/rfc5136.html). HTB class rate/ceil and
classification behavior are documented in the
[Linux HTB manual](https://man7.org/linux/man-pages/man8/tc-htb.8.html).
An end-to-end guaranteed service requires stronger path conditions than this
local test, as explained in [RFC2212](https://www.rfc-editor.org/rfc/rfc2212.html).
No RFC2212 implementation, field-capacity measurement or general latency
guarantee is claimed. Higher capacity is an explicit managed-service cost.

## Information and control

All online rules have the same exact CURRENT counterfactual viewport-quality
menu, resource cap, reserve and history. This is an oracle-current experiment,
not an implemented viewport estimator. Sender-side future encoded byte sizes
are available, but future viewer-dependent quality is not. Training uses only
already-exposed other scenes and excludes both target subject IDs. This is a
development split within a previously examined dataset, not a fresh holdout.

The KNN model uses only the observed prefix and loss. Its eight neighbors give
a rounded point forecast. Optimize predicted remaining compensation subject to
reserve/cap/floors, execute one actual-current action, update from delivery and
repeat. Predicted floors are not imposed as guarantees on future actual labels;
at the next step the actual current mask enforces the real floor again.
Consequently reserve and floor safety do not depend on prediction accuracy,
but half-repayment does. A false forecast can spend too soon or too late.

For integer outstanding loss d, let V_t(g) be the smallest extra-byte cost to
obtain capped compensation g over the first t planned slots. Initialize
V_0(0)=0. For each protected action a with gain g_a and cost c_a, update
V_{t+1}(min(d,g+g_a)) with V_t(g)+c_a, retaining minimum costs within R. A
higher-gain state at strictly lower/equal cost dominates a lower-gain state
for this objective. Choose maximum terminal gain then minimum cost. This is
ordinary multiple-choice knapsack dynamic programming; KNN and receding-horizon
optimization are established tools, not novel principles. Oracle equality is
possible when prediction is exact, but is not a general causal guarantee.

The persistence control uses the same optimizer without cross-scene learning;
greedy uses only current repayment, while rolling Nash/max-min optimize quality
histories. Improving repayment is not automatically improving post-event quality
or human experience. We retain both outcomes rather than changing the objective
after observing which controller wins. An offline oracle quantifies headroom,
not achievable online improvement.

## Evidence limits

Six scenes and dependent paired users cannot provide strong generalization
evidence. A point-predicted half-repayment flag is not calibrated admission.
Training exclusion and exact software replay prevent particular leakage/errors;
they do not turn exposed development into independent confirmation. A controlled
service pass and a model gain would still need a defensible service provider,
causal current-quality estimates, timing integration and a separately locked
evaluation before a deployment or manuscript success claim.
