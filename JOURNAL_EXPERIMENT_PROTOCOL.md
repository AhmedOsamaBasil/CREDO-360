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

## Engineering incident log

- 29 July 2026: the non-actionable campaign stopped during seed 20260738
  because the original 160 s transfer watchdog was shorter than the physical
  transfer time of the largest 10 s representation at the frozen 0.18 Mbit/s
  impaired-client ceiling. No primary outcome or controller parameter was
  changed. The watchdog was deterministically set to twice the theoretical
  worst-case transfer time plus 5 s (426 s), with a further 30 s parent-process
  margin. The campaign was resumed from complete controller--seed pairs; the
  interrupted pair was rerun under its original seed.
- 29 July 2026: seed 20260743 demonstrated that a valid impaired-client
  transfer can remain unfinished even at the 426 s engineering deadline.
  Because this is an intended consequence of the non-actionable treatment,
  curl deadline exit 28 is henceforth recorded as a right-censored transfer
  only for the predeclared impaired client. Its observed duration is the
  censoring deadline, its stall is therefore a conservative lower bound, and
  no completed segment is added to its buffer. The raw record includes the
  censoring indicator and curl return code. A deadline on any unimpaired client
  remains an infrastructure failure. Outcomes, controllers, seeds, and network
  parameters remain unchanged, and the interrupted pair is rerun.
- 29 July 2026: a transient deadline occurred on unimpaired client c4 during
  the final epoch of the third controller for seed 20260747. The same client,
  object, allocation, and bottleneck profile completed in approximately 9.3 s
  for both preceding paired controllers, supporting classification as an
  infrastructure failure rather than censoring. The orchestrator now performs
  up to three bounded infrastructure retries, cleaning Mininet before each
  attempt. Resume processing retains complete controller--seed pairs and
  discards the incomplete pair, so retrying does not duplicate observations or
  modify experimental parameters.
- 29 July 2026: the capacity-only campaign later produced zero-byte deadlines
  across different clients and media objects after long-lived Mininet/HTTP
  operation, exhausting the bounded retry budget despite advancing between
  failures. This cross-object pattern indicates process-lifetime degradation,
  not a content-specific observation. Each invocation is now limited to one
  newly completed controller--seed pair, after which Mininet and the HTTP server
  are cleanly restarted. Three consecutive failures at an unchanged checkpoint
  remain fatal, while any successful pair resets the consecutive-failure count.
  The frozen campaign plan is regenerated in full on every invocation and
  `--resume` skips completed pairs, preserving schedules, controller order, and
  all estimands.
