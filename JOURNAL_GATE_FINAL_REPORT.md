# CREDO-360 journal gate-identification result

## Status

Experiment A of the frozen TMM journal-extension protocol is complete. Both
conditions contain 30 paired seeds, three controllers, five users, one warm-up
epoch, and eight analysed epochs:

- non-actionable impairment: 4,050 raw rows and 90 complete
  controller--seed pairs;
- capacity-only control: 4,050 raw rows and 90 complete controller--seed
  pairs.

The automated audit passed for both conditions. There are no duplicate rows,
incomplete pairs, capacity- or segment-profile mismatches, impaired-client
identity mismatches, capacity violations, or censored transfers.

## Frozen primary comparison

The confirmatory comparison is CREDO-360 (`risk_debt`) versus resource-debt
allocation without opportunity gating (`resource_debt_ungated`) in the
non-actionable condition. Tests are paired two-sided Wilcoxon signed-rank tests
over 30 seeds, with Holm correction across exactly four primary outcomes.
Intervals are 10,000-draw paired-bootstrap 95% confidence intervals for the
mean paired difference (CREDO-360 minus ungated debt).

| Primary outcome | CREDO-360 | Ungated debt | Paired difference [95% CI] | Holm p | Rank-biserial |
|---|---:|---:|---:|---:|---:|
| Wasted allocation (Mb/s) | 0.1258 | 0.4811 | -0.3554 [-0.4137, -0.2983] | 5.19e-6 | -1.000 |
| Worst-unimpaired-user operational QoE | 4.2323 | 4.0291 | +0.2032 [0.1269, 0.2775] | 6.91e-5 | +0.802 |
| Debt-weighted opportunity activation | 0.99977 | 1.00000 | -0.00023 [-0.00070, 0.00000] | 0.507 | -1.000 |
| Total stall (s) | 66.5093 | 227.4538 | -160.9445 [-187.7597, -134.9373] | 7.45e-9 | -1.000 |

CREDO-360 therefore reduced mean wasted allocation by 73.9% and aggregate
stall by 70.8%, while increasing the worst unimpaired user's operational QoE
by 0.203 points (5.0%). These are controller-mechanics results under
model-estimated operational QoE, not subjective MOS validation.

The activation primary outcome is null after multiplicity correction and must
remain in the paper. Activation saturates for both controllers, so the
mechanistic novelty is supported by resource-use and downstream QoE/stall
effects rather than by a difference in the binary activation frequency itself.

## Condition interaction

The difference-in-differences analysis is consistent with an effect specific
to non-actionable impairment:

- wasted allocation: -0.3554, bootstrap 95% CI [-0.4146, -0.2984];
- worst-unimpaired-user QoE: +0.1306 [0.0343, 0.2203];
- total stall: -161.0178 s [-188.1724, -134.7483].

The activation interaction is again null because activation is nearly
saturated.

## Reproducibility artefacts

- Raw measurements:
  `live_testbed/results/journal_gate_{nonactionable,capacity}_30seed/`
- Audits, seed metrics, aggregate tables, primary tests, and interactions:
  `live_testbed/results/journal_gate_analysis/`
- Paper figure:
  `gate_primary_outcomes.png` and `gate_primary_outcomes.pdf`
- Frozen protocol and incident log: `JOURNAL_EXPERIMENT_PROTOCOL.md`
- Analysis implementation: `live_testbed/analyze_gate_campaign.py`
