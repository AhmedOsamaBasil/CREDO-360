# CREDO-360 TMM journal-extension protocol

Protocol initiated on 29 July 2026 before inspecting journal-extension
outcomes. Existing conference-draft results remain development evidence and
are not re-labelled as journal confirmatory evidence.

## Research questions

1. Does counterfactual opportunity gating prevent QoE-debt expenditure on a
   persistently constrained immersive client when added representation
   bitrate cannot improve its calibrated QoE floor?
2. Are the fairness effects robust across content/network regimes and user
   populations?
3. Does the deterministic action cover keep decision time compatible with a
   segment-level controller as the population grows?

## Experiment A: gate-identification campaign

- Five concurrent DASH clients sharing one bottleneck.
- Two impairment conditions:
  - capacity-only control;
  - non-actionable condition in which one counterbalanced client has a
    persistent access/decode-throughput cap plus latency excursion.
- Controllers: conformal Nash, resource-debt allocation without opportunity
  gating, and full CREDO-360. The resource-debt comparator rewards bitrate
  assigned to deprived users even when the calibrated QoE counterfactual is
  non-positive.
- Thirty paired seeds per condition, with identical capacity, segment, client,
  and impairment schedules within each seed.
- Primary comparison: CREDO-360 versus ungated debt in the non-actionable
  condition.
- Primary outcomes:
  1. wasted allocation above the impaired client's measured service ceiling;
  2. worst-unimpaired-user mean operational QoE;
  3. debt-weighted opportunity-gate activation;
  4. total stall duration.
- Paired two-sided Wilcoxon tests with Holm correction across the four primary
  outcomes; paired bootstrap confidence intervals and rank-biserial effects.

Operational QoE remains model-derived. This experiment identifies controller
mechanics, not subjective MOS validity.

## Experiment B: scalability

- User counts: 5, 10, 20, and 30.
- Capacity per user and state distributions are held constant.
- Thirty paired state seeds per population size.
- Report median, p95, and p99 controller decision latency; candidate count;
  feasibility violations; GPU/CPU identity; and peak resident memory.
- The candidate constructor must not materialize the full
  \(|\mathcal{B}|^N\) Cartesian product above five users.

## Experiment C: multimedia generalization

- At least three independently sourced 360-degree sequences spanning low,
  medium, and high spatial/temporal complexity.
- Public head-motion traces with user-disjoint train/test assignment.
- Report viewport-weighted quality, stall, switching, and inter-user
  fairness. If a human/headset experiment is not completed, all perceptual
  conclusions remain explicitly limited to validated objective measures.

## Stopping and reporting

Parameters and primary outcomes will not be changed after aggregate inspection.
Engineering failures are rerun with the same seed. Null and adverse results,
including gate saturation, remain in the report. Experiments B and C are
separate validations and will not be pooled with Experiment A.
