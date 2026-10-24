# Bounded-loss causal opportunity development

This plan precedes the new replay outcomes. All six source scenes and all
participants have already been exposed in earlier studies. This is development,
not independent confirmation or a new held-out result. Historical protocols,
sources and adverse outcomes remain unchanged. No manuscript update is planned.

## Question and deliberately restricted setting

Can a causal opportunity forecast support compensation timing while bounding
absolute terminal unpaid loss, instead of improving regret at uncontrolled
absolute cost? The primary cap is **unpaid fraction <= 0.5 in every modeled
future for every policy with positive mixture weight**. This is a service
specification for investigation, not a validated human-perception threshold.
Sensitivity caps .25 and .75 are reported, not selected after seeing results.
Absolute means loss rather than regret; the cap is normalized by initial D.
Raw unpaid utility is reported too.

Use a two-user, one-transfer service abstraction. One compensation transfer
is permitted during four recovery periods, even if its donor loss is zero.
The donor may lose at most .5 utility in that transfer; recipients retain the
current reference floor. This additional one-transfer restriction makes timing
auditable, but is not an unrestricted multi-user allocator. It isolates the
question before another full streaming campaign.

## Data and information boundary

Use only `feasibility_recovery/data/v2` and `horizon_recovery/data/v3`:
both historically named calibration/heldout quality files, plus segment sizes.
Those names describe old splits, not current data status. The six scenes are
ParkFountains01, River01, Train01, BuskingUnderpass05, Cheerleading01 and
ConferenceParticipant02. Each has six 10-second segments and 28 participant
panels. No repeated loops, new videos, download, encoding or model training on
new participants is involved.

For each scene, pair sorted participant IDs consecutively and evaluate both
recipient/donor directions: 28 ordered pairs per scene, **168 episodes** total.
Both users view the same scene. Reference representations are rung 2 (zero
based). In segments 0 and 1, the recipient is artificially capped to rung 0;
sum positive reference shortfalls to obtain D. The donor stays at rung 2.
Segments 2--5 are recovery. Baselines retain the actual two event observations
in their rolling history (H=24), rather than a manufactured balanced history.

Utility is the existing objective index `1+4*clip((PSNR-18)/24,0,1)`, rounded
to .001 units with decimal half-up rounding. This is not MOS. Recipient boost
rungs 3--5 and donor rungs 0--1 are eligible if their combined bytes do not
exceed two rung-2 segments, recipient gain is positive and donor loss <= .5.
The common current menu contains baseline and the eligible boost with largest
gain, then least donor harm, then bytes/rung tie-breaks. No eligible boost means
zero opportunity. Baseline and transfer bytes, utilities and rung IDs are saved.

**Current full-information idealization:** the replay reveals current measured
counterfactual viewport utilities to every policy before choosing. This is not
an implementable viewport predictor; it provides an upper-information test of
timing. Future utilities are unavailable to the controller. No prediction of
future head movements, transport stalls or live playback is claimed.

## Causal model, frozen choices

At the first recovery decision, use D and the first three observed opportunity
gains (two past, one current). The training pool excludes the target scene and
EVERY trajectory containing either target participant ID. It therefore uses
five other exposed scenes, not future outcomes from the current episode.
Rank by integer L1 distance in three gains plus half the D distance, with stable
scene/pair tie-breaks. Take eight neighbors. For each remaining recovery period,
use the minimum/maximum neighbor gain plus .05 utility padding, clipped to
[0,4]. Fit once; no later refitting or future-dependent parameter selection.
Save all neighbor IDs/distances and envelopes. Evaluate both gain error and
whole-trajectory envelope coverage, separately for raw gains and gains capped
at D (excess beyond D cannot affect repayment). The progression check uses
decision-relevant capped-gain membership. No calibrated-coverage claim is made.

Candidate policies spend at the first positive gain meeting a fixed fraction
of D in {0,.25,.5,.75,1}, or wait until the last period. If still unused, all
take any positive final opportunity. Sample one policy at episode start and
retain it. Exact mixture expectations, not Monte Carlo seeds, form the results.
An out-of-envelope observation permanently flags model breach and switches an
unused allowance to greedy current recovery. This preserves the one-transfer
and donor limits, but does not restore a lost terminal-loss guarantee.

## Robust absolute-loss constraint and optimization

Use the entire rectangular integer-gain envelope, not only neighbor paths.
Threshold boundaries, adjacent integers and interval endpoints define finite
critical scenarios. Within each cell the spend time is fixed; terminal loss
is affine and regret against the one-transfer offline optimum is convex.
Their maxima occur at those critical vertices. This gives exact worst-policy
losses and exact mixture regret bounds on the envelope, including unseen
combinations. It does not prove the actual future is in that envelope.

Exclude any policy whose worst unpaid fraction exceeds alpha. Among survivors,
minimize worst expected regret with a finite matrix-game LP. Check rationalized
primal/dual witnesses (gap <= 1e-7). Certificate is within this SIX-policy class,
not all possible causal strategies. If no policy qualifies, report infeasible
and choose deterministic minimum worst loss, then worst regret; alpha is never
relaxed or redefined. For D=0 report no-debt separately; choose baseline.

## Comparisons and outputs

Primary candidate: `bounded_knn` (alpha=.5). Also report .25/.75 sensitivities,
unconstrained KNN (alpha=1), persistence envelope (current gain +/-.05), and
physical envelope [0,D] with no learned future model. All forecasts are causal.
Controls: rolling Nash, rolling lexicographic max-min, stateless Nash, greedy
recovery and always-baseline. The offline oracle knows the four future gains
and is a benchmark ONLY. Every control shares the same current menu, original
loss, byte limit, one-transfer restriction and donor protection.

Save every episode, neighbor/forecast, critical-scenario certificate and all
positive-weight realized paths; report per-scene and pooled terminal unpaid
fraction/raw loss, regret, cap violations, admission/infeasibility, model misses,
donor loss, post-event mean/worst utility and bytes. No empirical p-values or
independence claim: participants/content repeat and selection is development.
No outcome-dependent episode removal, even when D=0 or no boost is feasible.

## Development progression screen

Before considering a fresh reserve require ALL of:

1. Conditional pathwise and ledger checks pass; zero empirical primary-cap
   violations among episodes declared feasible; no clipped cap accounting.
2. At least half of positive-debt episodes are declared feasible, and whole
   future-envelope membership is at least 90% on these exposed replays.
3. Primary candidate has strictly lower mean unpaid fraction and no higher cap
   violation rate than BOTH rolling Nash and rolling max-min in EACH cohort
   (v2 and v3), not merely favorable pooled performance.
4. Mean post-event utility is no more than .03 below each rolling comparator;
   donor loss <=.5 and every byte cap holds on every realized path.

These are deliberately demanding development heuristics, not significance
tests or guarantees for unseen data. A failure blocks fresh confirmation and
is published without retuning this batch. Passing would justify further
prediction/transport development, not a paper-ready result. No fresh reserve
is authorized by this plan.
