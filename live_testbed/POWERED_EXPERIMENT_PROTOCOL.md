# CREDO-360 powered live experiment protocol

Protocol frozen on 29 July 2026 before inspecting aggregate campaign outcomes.
The harness smoke test and individual transport logs were inspected for
technical validity; no aggregate powered-campaign comparison was analysed
before this protocol was fixed.

## Research question

Does opportunity-gated QoE-deprivation debt improve persistent user
equalization and continuity over calibrated Nash allocation and conventional
ungated QoE-debt weighting in a measured shared-bottleneck DASH testbed?

## Design

- 30 paired seeds: `20260730` through `20260759`.
- Five simultaneous Mininet clients and one server-egress TBF bottleneck.
- One paired warm-up segment followed by eight analysed segments.
- Ten stable, ten bursty, and ten mid-run distribution-shift capacity profiles.
- Identical capacity profile and media-segment sequence for every controller
  within a seed.
- Cyclic Latin-square controller ordering; each of six controllers occupies
  each execution position five times.
- Fixed parameters: target operational QoE 4.0, debt decay 0.90, debt weight
  1.0, switching weight 0.08.
- Real concurrent HTTP transfers of `.m4s` segments. Operational QoE remains
  model-estimated and is not a new subjective MOS.

## Controllers

1. mean-greedy QoE;
2. proportional-fair predicted QoE;
3. uncertainty-penalized Nash;
4. conformal-lower-bound Nash;
5. conformal QoE debt without counterfactual opportunity gating; and
6. full CREDO-360 opportunity-gated conformal debt.

## Confirmatory comparisons and outcomes

The two confirmatory comparisons are CREDO-360 versus conformal Nash and
CREDO-360 versus ungated conformal debt.

The confirmatory outcomes are:

1. worst-user mean operational QoE;
2. Jain fairness of per-user mean operational QoE; and
3. total stall duration.

Paired two-sided Wilcoxon signed-rank tests are used. Holm correction is
applied across the six confirmatory tests. Paired 10,000-resample bootstrap
95% confidence intervals accompany every mean difference. Effect direction
and magnitude are reported even when a corrected test is not significant.

## Secondary and exploratory outcomes

- mean operational QoE;
- lower-tail CVaR10;
- service-floor violation rate and mean shortfall;
- switching rate;
- debt and opportunity-gate activation;
- mean and 95th-percentile decision latency;
- capacity-feasibility violations; and
- results stratified by capacity regime and execution position.

Secondary tests are labelled exploratory. The results retain negative and
trade-off outcomes.

## Exclusions and missingness

A seed/controller pair is complete only when it contains five users for all
nine physical transfers. Warm-up rows are retained but excluded from
inference. A technical failure causes the incomplete pair to be removed and
rerun with the same seed, profile, segment sequence, and controller position.
No seed is excluded because of its QoE result.

## Stopping and parameter policy

The campaign stops after 30 complete paired seeds. Controller parameters,
primary outcomes, and inferential procedures are not tuned in response to
powered-campaign outcomes. Any later parameter sweep or additional outcome is
reported as exploratory.

## Claim boundary

The experiment supports conclusions about executable shared-bottleneck
mechanics under measured transport. Because operational QoE is derived from
the published-data model, it cannot independently validate subjective QoE or
conformal coverage. Human or independently labelled validation remains
necessary.
