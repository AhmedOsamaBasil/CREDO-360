# Frozen implementation specification for Experiment A

Frozen on 29 July 2026 after the engineering smoke test and before inspecting
any aggregate powered-campaign result. This document operationalizes the four
primary outcomes named in `JOURNAL_EXPERIMENT_PROTOCOL.md`; it does not change
their family, direction, or inferential procedure.

## Analysis unit and exclusions

- The paired seed is the analysis unit.
- The single warm-up epoch is retained in the raw log and excluded from every
  outcome.
- All five users and all eight analyzed epochs must be present for every
  seed--controller pair.
- CREDO-360 is represented by controller key `risk_debt`; the primary
  comparator is `resource_debt_ungated`.
- The primary family is evaluated only in the `non_actionable` condition.
  The capacity-only condition estimates condition-by-controller interactions
  and is not pooled into the primary tests.

## Primary outcomes

For seed \(s\), controller \(c\), user \(i\), and analyzed epoch \(t\), let
\(a_{s,c,i,t}\) be allocated representation rate, \(z_{s,i}=1\) identify the
counterbalanced impaired user, \(h_{s,i}\) be its service ceiling,
\(q_{s,c,i,t}\) be operational QoE, \(d_{s,c,i,t}\) be debt before the
decision, and \(g_{s,c,i,t}\) be selected counterfactual opportunity.

1. **Mean wasted allocation above the service ceiling (Mb/s):**
   \[
   W_{s,c}=\frac{1}{T}\sum_t
   \max(a_{s,c,i^\star,t}-h_{s,i^\star},0),
   \quad z_{s,i^\star}=1.
   \]
   Lower is favorable.
2. **Worst-unimpaired-user mean operational QoE:**
   \[
   Q_{s,c}^{\min}=\min_{i:z_{s,i}=0}
   \frac{1}{T}\sum_t q_{s,c,i,t}.
   \]
   Higher is favorable.
3. **Debt-weighted opportunity activation:**
   \[
   A_{s,c}=
   \frac{\sum_{i,t}d_{s,c,i,t}\mathbb{1}[g_{s,c,i,t}>10^{-9}]}
   {\sum_{i,t}d_{s,c,i,t}},
   \]
   defined as zero when total pre-decision debt is zero. This measures the
   share of outstanding deprivation attached to a selected action with
   positive calibrated opportunity; it is descriptive in direction.
4. **Total stall duration (s):**
   \[
   S_{s,c}=\sum_{i,t}\mathrm{stall}_{s,c,i,t}.
   \]
   Lower is favorable.

Secondary diagnostics include impaired-user stall, impaired allocation,
measured impaired throughput, unimpaired-user mean QoE, gate activation on the
impaired user alone, switching rate, and decision latency. They cannot replace
or expand the primary family.

## Inference

For each primary outcome, compute the paired CREDO-360 minus resource-debt
difference over the same 30 seeds. Use a two-sided Wilcoxon signed-rank test,
Holm correction across exactly four p-values, a deterministic 10,000-draw
paired bootstrap 95% interval for the mean difference, and matched
rank-biserial effect size. Report raw paired values, including null and adverse
outcomes. If capacity-only data are complete, also report the paired
difference-in-differences for each outcome as secondary interaction evidence.
