# Feasibility-aware recovery: fresh-content pilot v2

Protocol fixed before new source downloads and outcome inspection, 2026-10-23.
This is an exploratory engineering experiment, not a clinical preregistration,
a live player trial, or proof of theoretical novelty. The failed v1 is retained.

## Question and mechanism

Does removing infeasible target demand from a recovery queue improve objective
quality allocation without increasing stalls or sacrificing worst-user quality?
The method is an **anti-windup queue with a jointly feasible reference**, not a
new name for the v1 positive-gain gate. Integral anti-windup, virtual queues and
fair allocation are established ideas; this pilot tests their concrete coupling.

For the current sender-known representation table, let L_i(a) be the clipped
lower quality estimate, c_i(a) the measured bytes and B the previous-round
capacity estimate times ten seconds. Enumerate the common feasible set exactly.
First set u_i=min(4,max_a L_i(a)), with the maximum restricted to individually
admissible actions (other clients require their cheapest representation).
Choose the largest level h for which all clients can simultaneously reach
f_i=min(u_i,h). Cost is the minimum per-user cost among actions reaching f_i.
Candidate levels are 1, u_i and the finite L_i(a) values at or below 4. Thus f
has a simultaneous feasible witness, even with nonmonotone quality or bytes.

The queue is D_i(t+1)=[0.9 D_i(t)+f_i(t)-q_i(t)]+. The identical allocation
objective in the primary comparator is sum log L_i(a_i) + sum w_i L_i(a_i)
minus 0.08 times mean absolute log bitrate switch; w_i=D_i/(1+mean D).
The comparator uses fixed target 4 instead of f. Actual realized quality is
feedback only AFTER action selection. Surplus above the reference repays debt.
We separately report 4-u_i and u_i-f_i as *predicted ceiling relaxation* and
*contention relaxation*. They are NOT measured unavoidable loss or causal
counterfactuals. f is feasible for the forecast/prediction, not guaranteed for
actual capacity/viewport quality. In particular, lowering a reference cannot
itself count as improving quality: all primary metrics retain fixed target 4.

## Freshness and calibration

Development information is the old six-scene catalogue and failed v1. New
scenes are ParkFountains01, River01 and Train01, first 60 seconds, no audio.
They are absent from prior local media/derived experiments. This is a new
**content-and-trace-sequence holdout**, not an independent dataset or new human
participants. Source IDs overlap earlier QoEVAVE studies; say so explicitly.
If any specified source is unavailable, stop and amend the protocol visibly;
do not substitute a content chosen after seeing performance.

Use six unchanged ladder rates, 1920x960 H.264 NVENC p5 encodes, and 960x480
grayscale analysis at 1 fps. Preserve the declared 12x6 tile-center viewport
approximation and cosine-latitude area weighting. Each segment contains ten
samples, ten seconds and measured video-packet bytes (container/network header
overhead excluded). No extrapolated partial last segment is permitted.

The sender predictor is full-sphere area-weighted PSNR for each segment/rung,
mapped by q=1+4 clip((PSNR-18)/24,0,1). No future head movement, test outcomes
or historical subjective model is a decision feature. No trainable parameters.
Sort 28 source IDs by SHA256('feasibility-v2-ID'); first nine are calibration,
remaining nineteen held-out. Preserve IDs across all three scenes. Calibration
score is max absolute objective-index error across all 18 contexts and six
actions in one ID panel. Radius is the finite-sample 90% split-conformal order
statistic (rank 9 with n=9); test labels are stored separately and not used in
calibration. Catalogue-wide coverage requires exchangeable panels; report
observed coverage, not an arbitrary-shift or conditional guarantee. A shared
radius is for quality only, never called a bound on differences of bounds.

## Locked campaign

- 20 seeds: 202610240 through 202610259; five clients, 90 rounds.
- Three scene assignments rotate deterministically by seed/client; source
  segments repeat modulo six. New scenes do not create 90 independent segments.
- Each seed draws five test IDs without replacement. Capacities are clipped
  Normal(3,0.3) Mbps in [1,4.5], multiplied by 0.4 in rounds t mod 8 >= 5.
  Admission uses previous capacity (initial 3 Mbps, not the future first draw).
- Scenarios: capacity_only, known_ceiling, delayed_ceiling, prediction_shift.
  One client's displayed rung is capped at 1 in rounds 30--59, restored at 60;
  delayed feedback is one round stale. All policies see the same information.
  Prediction shift adds 0.6 index units in rounds 30--59 without recalibration.
- Policies: bounded_nash; fixed_debt; ceiling_debt (target u, no joint
  contention correction); feasible_recovery (target f); memoryless_feasible
  (last deficit in place of queue); max_min. The last policy maximizes minimum
  L then mean L, tie-breaking by byte count. Equal-score ties use fewer bytes,
  then enumeration order; permutation sensitivity is tested and disclosed.
- Exact 6^5 action enumeration. No actor learning or different tuning budget.
  All parameters inherited/fixed; no performance-based search in this version.
- Equal-share fluid transport with synchronized requests and corrected shared
  playback clock. Four-second initial buffer, ten-second media arrivals. No
  artificial buffer cap; decision runtime measured separately, not injected.
  This does not validate throughput in a real player or deployed scheduler.

## Outcomes, contrasts and progression rule

Report all seeds/scenarios/policies, raw user-round outcomes, every action and
reference, debt, calibrated interval coverage, actual PSNR/SSIM, packet bytes,
clock conservation, stall, decision time, switch frequency, and ceiling waste.
Primary fixed-target outcomes: cumulative positive shortfall per user; rounds
60--89 post-restoration shortfall; stall seconds/user; worst-user mean quality.
Also report impaired-user restoration shortfall and time to two consecutive
q>=4 rounds (right-censored at 30), longest deprivation streak, mean quality,
and max queue during/after ceiling. Smaller feasible debt is not efficacy.

Predeclared primary comparison: feasible_recovery versus fixed_debt in
known_ceiling. Descriptive screen requires both cumulative and restoration
shortfall mean differences <0, stall increase <=5% of baseline (0.1 s if zero),
and worst-user mean quality decline no more than 0.02 index units. This is not
a confirmatory significance test. Report paired seed-bootstrap 95% intervals
(2,000 draws, seed 481517) conditional on this small content pool, all scenario
contrasts and both ceiling_debt and bounded_nash comparators. No efficacy claim
based solely on passing a mean screen or cherry-picked scenes/seeds.

Preserve positive/null/adverse outcomes. No retuning on the held-out results.
Publish protocol and software before opening held-out outcomes, then code/data
hashes, derived data and checks before any manuscript changes. Source media and
HMD archives remain local; publish original download URLs and hashes, not those
third-party files. See the dataset's terms and cite both QoEVAVE source papers.
