# Frozen exposed-data sensitivity protocol

Freeze this method before the full batch. This is exploratory sensitivity on
already exposed data, not independent confirmation or a new controller trial.
Previous outcomes and progression screens remain unchanged.

## Inputs and fixed grid

Use only the published v2/v3 calibration+heldout quality tables (both now
exposed), actual-file manifest, and eight saved early-commitment 80 ms policy
paths. The 500 ms sensitivity is not another selectable primary. There are
168 directed episodes, six scenes and 28 reused participant identifiers.

Four increasing-quality scales, calculated deterministically from each stored
segment viewport PSNR with Decimal precision 40:

- `index`: original clip(1+(PSNR-18)/6,1,5), nearest 0.001, half-up.
- `fine_index`: same clipped mapping, nearest 0.000001, half-up. This separates
  coarse rounding from clipping; it is not literally infinite precision.
- `psnr_db`: unclipped PSNR, nearest micro-dB.
- `negative_mse`: -65025*10^(-PSNR/10), nearest micro-MSE. This reconstructs the
  segment's weighted mean distortion from its stored PSNR, not new pixel data.
  More positive values mean better quality. The compressed source reference,
  1 fps sampling, tile-center viewport approximation and original pose sampling
  are unchanged; this is not rendered or subjective truth.

All arithmetic on quality differences is integral after the declared rounding.
Keep metric units separate. Do not average their raw quality values together.

Initial impairment rung is 0 (historical) or 1 (milder counterfactual); reference
is rung 2 on event segments 0 and 1. Loss is the sum of positive reference-minus-
impaired differences. A zero-loss case is explicitly not applicable, not a
repayment success. The rung-1 panel only changes accounting of the initial loss;
it does not claim the saved controllers would take the same decisions if that
different event had occurred.

Repayment targets: 1/4,1/2,3/4,1. Recovery horizon: first 1,2,4 recovery segments.
**The same total entitlement R=sum of four pair-baseline actual-file sizes is
held fixed at every horizon** to isolate time from total resources. It does not
refill, and savings never refund positive extra bytes. Every round retains the
1,500,000-byte cap. A shorter horizon is not a new per-second entitlement.

## Two different questions

**A: Fixed-path rescoring.** Do not change any saved decision, start, arrival or
playback end. Recompute debt, positive credit and floor violations in each scale.
All shorter-horizon results are prefixes of the original four-slot policies,
not newly optimized short-horizon controllers. Rung-1 results are counterfactual
accounting only. Report all eight paths, cohort and scene variation, ranking
reversals and differences from the historical primary.

**B: Strict future-known opportunity.** Enumerate all structural rung2..5 pair
actions satisfying the actual-file cap and cumulative reserve; enforce both
users' actual native-scale reference floors. Recompute the maximum available
positive credit and the minimum-extra-byte witness for each target. This is a
finite offline feasibility bound, not an online predictor, admission guarantee,
learned controller or human fairness result. A metric can also change the
admissible set through its floor/rounding; report that, not just gain changes.

Both panels use these credit contracts:

1. `media`: credit after all H selected recovery segments finish playing.
2. `deadline`: credit only for selected recipient segments fully played by
   10*H seconds after the first recovery decision (time zero, cold buffer).
   No credit is prorated from an aggregate segment mean. Partial displayed
   improvements are uncounted, so this is a completed-segment contract, not an
   exact continuous-time perceptual-loss measure. Actions must meet floors and
   their full bytes are charged even if their presentation finishes after the
   deadline. The offline deadline bound uses the same scheduled H-action family,
   not a general scheduler allowed to abort or invent different segment times.

Preserve the nominal 10 s duration and previous ideal fluid service: two flows
share 1.2 Mbps payload, 0.13 s setup/control allowance, starts separated by at
least 10 s or transfer completion. Reconstruct with exact integer ticks
(150,000/s). Saved waiting-policy times are read, not removed. Existing River01
final duration is 9.966667 s; this nominal-clock sensitivity does not replace the
separate media-duration audit. New segment sizes/durations/player integration
are deliberately outside this study.

## Checks and reporting fixed before outcomes

- Original index/rung0/H4/media rescoring must reproduce all saved 80 ms
  unpaid fractions and floor counts. Original strict oracle must match the
  previously published strict bound for every episode.
- Independently re-enumerate using scalar recursion, rather than the vectorized
  path implementation: all 168*4*3*2=4,032 metric/horizon/clock queries, both
  losses and four targets, including minimum witness cost.
- Positive affine quality changes preserve all losses/credits up to scale and
  thus repayment ratios/floor eligibility; test exactly. A constructed nonlinear
  ranking reversal is illustrative, not new empirical data or a new theorem.
- Target feasibility is nonincreasing with target fraction. Deadlined credit
  cannot exceed eventual credit on the same path. Maximum opportunity cannot
  decrease as horizon/deadline increases under fixed R and a feasible baseline
  continuation. Strict-feasible saved paths cannot exceed their offline bound.
- Retain zero-loss denominators, floor violations, adverse rankings, all grid
  cells and per-scene results. No independent-sample p-values or new success
  threshold. This study does not reverse prior failed progression screens.
- Publish source/input hashes, exact witnesses, complete scalar outcomes,
  cross-platform replay, tests and separately labeled interpretation/figures.
  No new holdout, acquisition, network trial, manuscript or acknowledgment edit.
