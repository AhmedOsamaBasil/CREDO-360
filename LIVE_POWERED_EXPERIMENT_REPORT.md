# Powered live Mininet experiment report

## Study purpose

This paired campaign tests whether CREDO-360 changes persistent inter-user
operational QoE under real concurrent HTTP segment delivery through an
enforced shared bottleneck. It is a confirmatory network-emulation experiment,
not a human-subject or headset study. Operational QoE remains the published-data
model estimate computed from measured transfer features.

The analysis plan was frozen in
`live_testbed/POWERED_EXPERIMENT_PROTOCOL.md` before the campaign completed.
No run was excluded based on its outcome.

## Design and integrity

- 30 paired seeds (`20260730`--`20260759`), with 10 stable, 10 bursty, and
  10 distribution-shift capacity profiles.
- Six controllers: mean greedy, proportional fair, uncertainty Nash,
  conformal Nash, conformal debt without opportunity gating, and CREDO-360.
- Five concurrent Mininet clients, one warm-up epoch, and eight analysed
  segment epochs per controller.
- Identical capacity profile and segment schedule within every paired seed.
- Cyclic controller ordering: every controller occupied every ordinal position
  exactly five times across the campaign.
- 8,100 logged rows: 900 warm-up and 7,200 analysed observations.
- 180/180 controller--seed pairs and 30/30 seeds complete.
- Zero capacity or media-schedule mismatches; maximum allocation excess was
  exactly `0.0` Mb/s.
- Mean controller decision latency across all decisions was `68.3` ms.

One process watchdog timeout produced an incomplete pair during collection.
The incomplete pair was discarded automatically and rerun from the same
prespecified seed; it was not inspected or selected by outcome. The watchdog
threshold was then increased from 90 to 180 seconds for process reliability.

## Confirmatory analysis

The two prespecified baselines were conformal Nash and conformal debt without
opportunity gating. The three prespecified outcomes were worst-user mean
operational QoE, Jain fairness over user means, and total stall time. Paired
two-sided Wilcoxon signed-rank tests were Holm-corrected over these six tests.
Intervals are 10,000-resample paired bootstrap confidence intervals for the
mean difference. Positive deltas favour CREDO-360 for QoE and Jain fairness;
negative deltas favour it for stall time.

| Baseline | Outcome | CREDO mean | Baseline mean | Mean delta [95% paired-bootstrap CI] | Positive/negative pairs | Rank-biserial | Confirmatory Holm p |
|---|---|---:|---:|---:|---:|---:|---:|
| Conformal Nash | Worst-user mean QoE | 4.1859 | 3.9769 | +0.2090 [0.1416, 0.2886] | 28/2 | 0.978 | 1.12e-7 |
| Conformal Nash | Jain fairness | 0.998373 | 0.995979 | +0.002393 [0.001447, 0.003594] | 27/3 | 0.944 | 8.20e-7 |
| Conformal Nash | Total stall (s) | 2.0364 | 1.6081 | +0.4283 [-0.0555, 1.1349] | 7/8 | 0.017 | 1.000 |
| Ungated conformal debt | Worst-user mean QoE | 4.1859 | 4.1592 | +0.02669 [0.00291, 0.05404] | 18/12 | 0.385 | 0.254 |
| Ungated conformal debt | Jain fairness | 0.998373 | 0.998275 | +0.000097 [-0.000082, 0.000296] | 19/11 | 0.389 | 0.254 |
| Ungated conformal debt | Total stall (s) | 2.0364 | 2.0372 | -0.00077 [-0.00598, 0.00315] | 8/6 | 0.162 | 1.000 |

CREDO-360 therefore shows a large, consistent improvement over conformal Nash
in persistent worst-user QoE and a smaller but consistent improvement in Jain
fairness. The campaign does not support a stall-time improvement. It also does
not reject the confirmatory null against the ungated debt controller.

The positive bootstrap interval for the *mean* worst-user difference against
ungated debt does not contradict the nonsignificant Wilcoxon/Holm result: the
interval estimates a mean effect, whereas the signed-rank test targets paired
rank location and is additionally corrected for six confirmatory tests. The
multiplicity-corrected test governs the confirmatory claim.

## Secondary outcomes

CREDO-360's grand means were operational QoE `4.4204`, worst-user mean QoE
`4.1859`, CVaR10 `3.3058`, Jain fairness `0.998373`, violation rate `0.1617`,
total stall `2.0364` s, and representation-switch rate `0.5375`.

Against conformal Nash, the mean operational-QoE difference was only `+0.0073`,
the CVaR10 difference `+0.0254`, and the violation-rate difference `-0.015`;
none was significant after multiplicity correction. CREDO-360 switched more
often (`+0.070`), a statistically significant adverse secondary result.

Worst-user improvements over conformal Nash remained positive in every
capacity regime:

| Regime | Mean paired delta | Positive seeds |
|---|---:|---:|
| Stable | +0.2015 | 9/10 |
| Bursty | +0.2884 | 9/10 |
| Shift | +0.1371 | 10/10 |

The same worst-user delta was positive at all six CREDO-360 controller
positions (four or five positive pairs out of five per position). Because
capacity regime and controller-order shift are only balanced marginally, not
fully crossed, regime-specific and position-specific effects are descriptive
robustness checks rather than separate causal estimates.

## Mechanism and negative ablation

CREDO-360's mean QoE-deprivation debt fell from `0.826` in analysed epoch 0 to
`0.161` in epoch 7; the selected debt contribution to the objective fell from
approximately `6.43` to `1.77`. This demonstrates that the persistent state
was active and influenced allocation.

Opportunity gating, however, was active for `99.3%` of users in epoch 0 and
`100%` thereafter. The live impairment profiles were almost always actionable
by bitrate, so the gate rarely suppressed debt. This explains the null
confirmatory ablation against ungated debt. The experiment validates the debt
mechanism but does **not** establish the necessity of the opportunity gate.
A decisive gate test requires non-actionable impairments such as viewport
prediction error, device limitation, latency spikes, or decoder overload.

## Claim boundary

Supported:

1. paired live-emulation evidence that CREDO-360 improves persistent
   worst-user operational QoE and Jain fairness over conformal Nash;
2. executable learned-model inference and online decision making under
   measured concurrent transfers;
3. capacity safety, complete observability, and stable sub-100-ms decisions;
4. active QoE-deprivation debt with an auditable temporal trajectory.

Not supported:

1. subjective MOS or headset-user improvement;
2. a stall reduction in the powered live campaign;
3. an advantage over ungated conformal debt after confirmatory correction;
4. causal necessity of opportunity gating in capacity-only regimes;
5. generalization to independent content, devices, access networks, or users.

All raw measurements, the frozen protocol, seed-level metrics, paired tests,
bootstrap intervals, campaign audit, and figures are retained under
`live_testbed/results/live_campaign_30seed/`.
