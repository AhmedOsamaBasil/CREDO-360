# Exposed-data objective diagnosis (24 October 2026)

This is DEVELOPMENT, not another fresh holdout. Both the v2 and v3 catalogues
and outcomes have been inspected. No new video, participant, or independent
test data will be downloaded. Preserve all frozen historical sources/results.
The v3 GitHub integrity check completed successfully at1d41d87; its performance
screen still failed. Correctness does not establish benefit.

## Questions and controlled factors

1. Does a contract capped at quality4 suppress redistribution above that floor?
2. Does banking negative residuals suppress useful responses to later deficits?
3. Can either change improve fairness beyond direct, simpler history-aware rules?
4. Does a fixed rung ceiling impose different quality loss on different content?

Hold H=24 and penalty strength=8 fixed, as selected in the previous development
search. No parameter grid or selection based on a new holdout. Evaluate TWO
targets (joint mixture contract capped at4 versus allowed up to5) and THREE
feedback modes (signed banking, non-banking finite-window debt, and H-scaled
memoryless residual). The uncapped contract is not a promise of quality5: it
remains capped by predicted jointly feasible average service and individual
attainable ceilings. Retain all six combinations.

Compare against four direct rules: stateless bounded Nash, instantaneous
lexicographic max-min, rolling-window lexicographic max-min, and rolling-window
bounded Nash. All share predictions, past observed feedback, action sets and a
stateless Nash per-context byte cap. Direct max-min sorts each predicted quality
vector in increasing order and maximizes it lexicographically, then breaks ties
by bounded Nash utility, bytes, enumeration. Rolling rules use H-1 actual past
qualities plus current predicted quality (current lower quality for rolling
Nash). These are known design principles, not newly invented fairness concepts.

## Explicit finite-window correction

In v3 the decision proxy clipped the historic signed balance at zero and added
the next residual before expiring the oldest entry. It was not the exact next
state of the claimed H-entry signed window. Historical results stay unchanged.
Here expiry happens BEFORE action selection, leaving at most H-1 previous
observations. A banking rule retains the negative historic balance inside its
predicted terminal calculation: max(S + target - predicted_quality,0). A
non-banking rule uses the maximum suffix sum of the retained residuals, including
the empty suffix0: D=max(0,max_k sum of last k residuals). Appending residual e
then gives max(D+e,0). This prevents prepayment of a future deficit without
preventing current surplus from repaying existing debt. Expiry-induced changes
are recorded separately from delivery. The memoryless rule retains H times the
latest positive residual; no earlier residual changes its decisions.

These corrections apply to ALL relevant new policies. Comparisons between new
banking/non-banking variants isolate that factor; they must not be described as
a single-factor comparison against the original v3 controller.

## Data, stress conditions and information boundary

Use `feasibility_recovery/data/v2` and `horizon_recovery/data/v3` with their
existing9 calibration/19 evaluation IDs, sender predictions and objective
calibration. Both evaluation subsets are now DEVELOPMENT data. Seeds202610500--
202610505 for each catalogue; draw120 capacities using the old Normal(3,.3),
clip[1,4.5], multiply by.4 when t mod8>=5 process, then five distinct source IDs.
Content rotates by seed/user. Initial buffer4s; corrected fluid synchronized
clock. Exact allocation, five users, six actions each. Computation is measured
but not charged to playback. Six source segments repeat across120 rounds.

Three scenarios: capacity_only, fixed_ceiling (rung1 in40--79), range_ceiling.
For range_ceiling, derive a CURRENT capability profile using sender-side quality
only: for each of the six known segments choose the largest rung whose prefix
maximum quality is at most q0 +0.5*(max(q)-q0). Thus at least half the predicted
quality range above rung0 is removed when nonzero. Flat ranges are retained and
reported, not replaced or discarded. This is a synthetic relative-quality stress
profile, not a claim of equal absolute/human impairment. Retain absolute drop
and achieved normalized drop as manipulation checks. The active impaired user
is seed index mod5 in40--79. Reported profile is known immediately; no delay or
prediction-shift claim is made for this diagnostic.

The contract sees sender-known future catalogue entries and the CURRENT reported
capability profile, assumed persistent over its six-period forecast. It cannot
see future transitions, capacities or HMD outcomes. Renew every6 rounds and on
observed impairment activation/restoration. Forecast capacity is the mean of
last12 observations, initial3Mbps; admission uses last observed capacity. Every
joint support action and actual action fits the same stateless Nash byte cap.

## Reporting and stopping rule

Expected360 episodes and216000user-round rows:2 catalogues x6 seeds x3 scenarios
x10 policies x120rounds x5 users. Retain all outcomes, paired contrasts, effects
of target and banking at matched other settings, policy disagreements, activation,
expired residuals, quality-index clipping, objective VW-PSNR, and clock/resource
checks. Primary quality is still the unchanged normalized PSNR index; fixed
target4 shortfall remains an external metric for ALL policies. No win may be
defined just by changing the internal target. Report worst-user time-average
quality and dB, mean quality, post-restoration and impaired-user shortfalls,
cumulative shortfall, stall, and switching. Paired-seed bootstrap1000 draws with
seed202610524 gives DESCRIPTIVE intervals on exposed data, not confirmation.

Only four stateful candidates (floor/fair x bank/nobank) can be development-
promising. In range_ceiling, require positive mean worst-user-quality improvement
against Nash, the matching-target scaled-memoryless control, rolling max-min,
and rolling Nash in BOTH catalogues. For each comparison require mean-quality
loss<=.03, fixed-shortfall increase<=5%, and stall increase<=5% (0.1s if zero).
Do not select a different baseline, cohort or criterion after results. This
screen merely decides whether spending a genuinely new reserve is justified;
even a pass is not a novelty or superiority claim. If no candidate passes,
publish the diagnosis and stop before consuming more independent test data.

## Prior-art anchors (not a completed novelty review)

Virtual-queue and time-average mixture optimization are established, as described
in M. J. Neely's [Network Optimization Notes](https://ee.usc.edu/stochastic-nets/docs/network-optimization-notes.pdf),
Sections VI and VIII. The non-banking recursion used here is not claimed new;
finite-window truncation adds expiry, so standard infinite-horizon queue theorems
do not automatically apply. Log-utility proportional fairness predates this
project: F. P. Kelly, A. K. Maulloo and D. K. H. Tan, “Rate control for communication
networks: shadow prices, proportional fairness and stability,” JORS49,237--252,
1998, [original paper](https://web.stanford.edu/class/cs244/papers/ShadowPricesFairnessStability.pdf).
Applying log utility to a clipped quality index is an operational objective,
not a theorem that it equals perceptual fairness. These references motivate
strong controls; they do not establish a new contribution for this study.
