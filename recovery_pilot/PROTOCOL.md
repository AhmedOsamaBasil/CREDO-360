# Recovery pilot v1: locked engineering protocol

Date: 23 October 2026. This is an exploratory, semi-synthetic engineering
pilot, not a preregistered confirmatory study or a new human-subject experiment.
The original dataset and old outcomes have already been inspected. Parameters
below are fixed before running this new pilot; retain all outcomes and changes.

## Question

Does spending persistent deprivation debt on a directly bounded reduction in
quality shortfall improve recovery over ordinary quality-debt weighting? Is
there a useful contribution from uncertainty and memory, or should the method
be simplified? No claim of methodological novelty is established by this pilot.

## Data and prediction

Use the existing six-content QoEVAVE derived artifact. Predict the objective
index `q = 1 + 4*clip((VW-PSNR-18)/24,0,1)`, NOT the old subjective ensemble.
Sort the 28 source subject IDs by SHA-256 of `recovery-v1-ID`: first 10 train,
next 9 calibrate, last 9 test, consistently across all six contents. Retain the
manifest. The old two-way split is not used for this new version.

The predictor is the training-subject mean for each known content, segment,
representation. This is a deliberately simple, content-specific, prerecorded
streaming predictor. It uses no held-out trace samples, identity-specific
test outcomes, future test viewport, or calibration outcomes in fitting.
It does NOT test unseen-content generalization. Numeric IDs are grouped across
contents conservatively; the artifact alone does not verify identities.

Define H(q)=[4-q]+. For each calibration ID, the score is the maximum over the
entire six-content/six-segment catalogue of (i) absolute quality prediction
error and (ii) the range across actions of H(prediction)-H(realization).
The latter simultaneously bounds every ordered action-pair shortfall-reduction
prediction error. Use rank ceil((n+1)*0.9), not a percentile interpolation.
If too few independent calibration units exist, use the known trivial bound 4
and explicitly flag it. Nine calibration IDs give the maximum observed score.

This gives a joint catalogue-wide quality/gain envelope under exchangeability
of the grouped ID panels, conditional on training. It is NOT conditional-on-user,
arbitrary-shift, population-joint, or live-stream coverage. Adaptive action
selection within a covered finite catalogue needs no additional pointwise
selection argument: all actions/pairs were included. Repeating that catalogue
does not create new independent calibration or test data. Report whole-panel,
selected-action and gain coverage separately; the empirical sample is tiny.

## Candidate mechanism and comparators

At a round, let mu(a) be predicted objective quality, L(a)=max(1,mu(a)-r),
reference action be the minimum representation, and

    predicted_gain(a) = H(mu(reference)) - H(mu(a))
    certified_gain(a) = max(0, predicted_gain(a) - r)
    recovery_credit(a) = min(debt, certified_gain(a))

The controller maximizes sum log L(a) + sum normalized_debt*recovery_credit(a)
minus 0.08 times mean absolute log representation-rate change. The debt update
is max(0,0.9*debt + 4-realized_q); normalized_debt = debt/(1+mean(debt)).
Unlike subtracting quality lower bounds, the gain is calibrated directly after
the shortfall transform. Capping credit at outstanding debt and the floor-based
gain makes the score non-affine in quality. Non-equivalence is necessary, not
evidence of benefit. A zero clipped gain is an abstention, not proof of no harm:
the certified positive-gain interpretation applies only when the bound is >0.

Comparators, all with the same data/information/action set:

- mean-quality Nash, without debt;
- bounded-quality Nash, without debt;
- mean-quality debt;
- bounded-quality debt (principal comparator);
- uncertified recovery: same bounded Nash base, but radius zero ONLY in gain;
- certified recovery (candidate);
- memoryless recovery: same candidate, but previous shortfall replaces debt;
- max-min predicted quality, with mean quality and byte count breaking ties.

All allocation vectors are enumerated exactly for five users/six actions.
Admission constraint: measured segment bytes fit the previous observed link
capacity times 10 seconds. At initialization, all policies receive the same
initial link estimate. Ties prefer fewer bytes, then fixed enumeration order.
Test unique-optimum permutation invariance; document tie indeterminacy.

## Campaign

- 12 paired seeds beginning 202610230; 5 users; 60 rounds; 8 controllers.
- Each user receives a fixed test ID and a counterbalanced content. Loop the
  six measured segments ten times. This is replay of one minute, not ten
  independently recorded minutes or new HMD traces.
- A common seeded bursty capacity schedule is shared across policies. Decisions
  see the previous capacity; true current capacity determines transfer duration.
- Four scenarios: capacity-only; known representation ceiling; one-round-delayed
  ceiling observation; prediction shift. All policies receive identical causal
  information in a scenario.
- Ceiling rounds 20--39: one seed-counterbalanced user can display at most rung
  1 although higher requested rungs still consume their measured bytes. At round
  40 service is restored. This is an explicit synthetic decoder/service model,
  not a measured device fault. Known clamps map actions into the existing
  calibrated catalogue. Delayed clamps can invalidate decision-time bounds.
- Prediction-shift rounds 20--39: add 0.6 to all mean predictions, clipped to
  [1,5], without recalibration. Labels remain measured, unchanged. This is a
  deliberately adverse coverage diagnostic, not a guaranteed adaptation method.
- Exact equal processor-sharing simultaneous transfers, synchronized next
  decision, and a single elapsed-time playback clock. Include time after each
  user's completion until the round ends. No silent buffer-time truncation.
- No GPU is needed for this finite-catalogue pilot; do not equate more compute
  with stronger evidence. No live network or actual video player is claimed.

## Outcomes and decision gates

Record per-user decisions, means/bounds, realized index, source PSNR/SSIM,
debt, capacity, bytes, completion/end times, buffers and stalls. Source metrics
use the effective displayed rung; do not invent distorted video measurements.

Primary engineering comparison: certified recovery minus bounded-quality debt,
paired within each seed and scenario. Report cumulative positive shortfall,
post-restoration shortfall (rounds 40--59), longest under-floor run, and time to
two consecutive at/above-floor segments after restoration (right-censored if
not reached). Also report mean/worst-user quality, stall, excess bytes above
display cap, action disagreement, gain activation and panel/action coverage.
Count each seed once in paired summaries; rows are not independent trials.
Paired bootstrap intervals are descriptive for this fixed-content replay, not
population significance or a substitute for content/subject-level replication.

Predeclared progression gate: no feasibility/timing/split failures; positive
recovery gains must have calibrated target semantics; and the candidate must
reduce both mean cumulative and mean post-restoration shortfall against the
principal comparator in the known-ceiling scenario without increasing mean
stall by >5% (or >0.1 s if baseline is zero). Separately report uncertainty's
increment versus uncertified recovery and memory's increment versus memoryless.
This gate is engineering screening, not a statistical acceptance threshold.
If it fails, do not tune on these test outcomes, promote the candidate, or revise
the manuscript as if it succeeded. Preserve the failure and propose a new
separately versioned design or a simpler debt-only contribution.

## Before manuscript work

Run unit/regression tests, publish code and all pilot results with source hashes,
environment and protocol identity, and verify the remote commit. Preserve the
old studies with prominent limitations. Update AGENTS.md with actual outcomes.
Leave the manuscript acknowledgment unchanged.
