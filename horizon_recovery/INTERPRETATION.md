# Outcome: development gain did not generalize

The frozen fresh-content progression screen **failed**. This is not a successful
validation of longer-horizon recovery, and the manuscript must not present it as
one. No parameter, seed, content, or progression rule was changed after opening
the holdout. All previous failed pilots remain intact.

## What was developed and tested

The redesigned controller uses a six-period jointly feasible mixture contract,
a signed24-round residual window, and exact terminal-deficit action selection.
Every decision fits the same per-round byte cap as stateless bounded Nash.
The scale-matched memoryless comparator uses24 times its last positive residual;
the unscaled and fixed-target-window controls remain secondary comparisons.

The exposed-data search retained all six H/strength configurations and720
episodes. The prespecified selection was H24/strength8, with development
known-ceiling worst-user gains +0.017144 over Nash and +0.032493 over scaled
memoryless. Its state was active33.08% of user-rounds. All720 development
episodes were recomputed on Linux and reproduced the Windows selection.

The fresh test used three unused QoEVAVE video/trace sequences,20 paired seeds,
four conditions, five policies and120rounds:400episodes,48000joint decisions,
240000user-round records. The source pool is still the same28participants;
this is content/trace-sequence holdout, not new-human or cross-dataset evidence.
Nine panels calibrated the sender predictor (radius0.903384); all19 held-out
panels were covered on the fixed catalogue. This is not a conditional/adaptive
coverage guarantee or a guarantee under the imposed prediction shift.

## Primary known-ceiling results

Differences are candidate minus comparator. Intervals are descriptive paired-seed
95% bootstrap intervals conditional on this fixed content and participant pool.

| Metric | Versus Nash | Versus scaled memoryless |
|---|---:|---:|
| Worst-user quality index | -0.000315 [-0.001711, +0.001090] | -0.007020 [-0.012895, -0.001357] |
| Post-restoration fixed shortfall | -0.054857 [-0.082227, -0.032538] | -0.009745 [-0.021625, +0.000128] |
| Cumulative fixed shortfall | -0.105389 [-0.159407, -0.061261] | -0.009929 [-0.025107, +0.000305] |
| Stall, seconds/user | -0.148172 [-0.420571, -0.006316] | +0.373289 [+0.071234, +0.872543] |
| Mean quality index | -0.000204 [-0.000284, -0.000130] | +0.000950 [+0.000192, +0.001790] |

The weak mean restoration checks and the quality/stall guards passed. The
worst-user improvement checks failed against BOTH primary baselines. The
activation criterion and Nash-disagreement criterion also failed. It would be
misleading to promote the small shortfall reductions while hiding these failures.

The candidate differs from Nash in only71/12000primary individual actions
(0.592%); across all four conditions it differs in276/48000(0.575%). Its state
is active only1.167% of primary user-rounds, versus9.55% for scaled memoryless.
It differs from the fixed-target-four window in only2primary actions, and is
exactly action-equivalent to that control in capacity_only and prediction_shift.
Thus this holdout does not establish a distinct benefit from the joint contract.
All20episodes satisfy the two-successive-round restoration-event definition for
every policy; none is censored, so this endpoint also has limited discrimination.

Other conditions do not rescue the claim: worst-user quality declines versus
scaled memoryless in all four conditions. Versus Nash it is lower in capacity_only
and prediction_shift, with conditional intervals wholly below zero. The slight
content-wise quality improvements for Cheerleading01 coexist with adverse
BuskingUnderpass05 differences. Full contrasts and sign counts are retained in
`results/v3/diagnostics/content_contrasts.csv`.

## Mechanistic reading (post-hoc diagnosis, not another tuned experiment)

The current quality contract is capped at4 while the observed mean quality is
4.534 and the worst-user time-average is4.334. Mean contract target is3.9964.
In the12000primary candidate records,19.43% of quality values hit the index's
upper cap5 and only10.26% are below4. Mean delivered surplus relative to the
contract is0.5472 per user-round, versus0.00939new positive deficit. Signed
surplus credits therefore dominate and usually suppress the window state.
Every primary episode's worst-user time-average exceeds4 (minimum4.1876).
These quantities are reproducible with `posthoc.py` and recorded with input
hashes in `results/v3/posthoc_diagnostics.json`; they were not selection inputs.

These measurements support a structural mismatch: a threshold-recovery controller
has little reason to redistribute service once everyone is already above its
contract on average, even if a max-min fairness objective would prefer further
redistribution. Memory length alone does not resolve that mismatch. The fresh
content also changes what a fixed bitrate-rung ceiling means in quality terms;
the same network/ceiling settings are not guaranteed to impose comparable
deprivation severity across videos. These are interpretations of the observed
data, not isolated causal effects of clipping or surplus banking.

The24-round window is shorter than the40-round impairment; old residuals can
expire before restoration. Expiry and actual delivered surplus are separately
logged, and neither a declining queue nor positive expired debt is counted as
an independent performance benefit. The current controller is recent-window
service tracking, not a promise to repay all historical losses.

## Consequence for the research claim

Do not add more seeds to this now-exposed holdout and call that new confirmation.
Do not tune on v3 and continue to call it fresh. A further redesign should first
define whether the objective is minimum-service recovery or max-min fairness
above a floor, then investigate credit banking and content-normalized impairment
severity on exposed data. Any subsequent confirmatory test needs another
independent reserve, preferably a different content/trace collection.

This pilot establishes a reproducible implementation and a useful negative
finding, not a publishable superiority/novelty claim by itself. No manuscript or
acknowledgment was changed as part of this experiment.

## Traceability

Windows and Linux independently replayed all240000scientific rows and checked
12150joint LP support witnesses. Both integrity audits passed. Maximum playback
clock residual was2.84e-14seconds and no action exceeded the common Nash byte
cap. Wall-clock runtimes were measured but not replayed or injected. The final
Windows regression suite passed72tests plus24subtests, Linux68plus24, and the
separate portable-model suite5tests. Both prior frozen pilots also passed their
complete integrity audits unchanged. The figures were visually inspected.

- `881b20f`: implementation and exposed-data development plan.
- `3e19afd`: all development outcomes and frozen fresh-test protocol, before downloads.
- `e4a156e`: scientific replay auditor, diagnostics and tests.
- `d7c7ad3`: all720 development episodes verified across platforms.
- `2a3802d`: explicit finite-memory limitation; frozen fresh run used this head.
- Plot review corrected a scenario-axis ordering issue in the diagnostic renderer;
  scientific measurements and protocol were unchanged. Initial plot files remain
  in a local scratch archive, not as an alternative result set.

See the saved integrity reports for full fresh-test row, LP witness, clock,
resource and hash checks. Engineering integrity and scientific benefit are
separate questions.
