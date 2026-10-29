# Temporal geometry: assumptions, lower bounds and limits

## A conditional motion model

Represent yaw y and pitch p by the unit forward direction
u=(cos(p)cos(y),cos(p)sin(y),sin(p)). Its shortest spherical separation from v
is atan2(||u cross v||,u dot v). For a speed envelope omega, an anchor u0 at
wall time t0 restricts future direction to angle(u0,u(t)) <= omega*(t-t0).
At radius180degrees the cone is the entire sphere. This is a conditional
Lipschitz-style model; recorded maxima cannot establish it for future humans.
It ignores roll because the historical quality metric ignores roll.

The original tile-centre metric is a100x100degree yaw/pitch angular window,
not a perspective frustum. Its mask membership changes only at tile-centre
plus/minus50degree boundaries. Cartesian products of all singleton boundaries
and intervening open intervals partition orientation space. For safety we
replace open rectangles by their closures. At a pole different yaw windows
can have the same forward direction; the conservative set retains them all.

For anchor(y0,p0) and a closed cell [yL,yU]x[pL,pU], minimize angular separation
by maximizing the dot product. First maximize cos(y-y0) on the yaw interval:
test its endpoints and y0 modulo360 if inside. Calling this maximum c, maximize
cos(p0)*c*cos(p)+sin(p0)*sin(p) over the pitch interval. Test the two endpoints
and the interior stationary maximum atan2(sin(p0),cos(p0)*c), when present.
The arccosine of the largest dot product gives the cell distance. Take the
minimum across every cell yielding a mask. Distances are rounded DOWN to
microdegrees with a two-microdegree outward numerical guard. Cone radii are
rounded UP. This is a deterministic numerical guard, not a confidence level.

## Timing and quality certificates

The anchor is the causal source pose used at media19.5s, at its actual source
timestamp; request entry is20s. Anchor staleness is rounded upward in clock
ticks. This entry information is assumed available, as is the previous exact
past-debt ledger. For each candidate resource path, the fixed service and
execution model bounds completion time. Placing its allowed execution delay
before playback gives an upper sample time for the cone calculation. The cold
start, transfer latency, accumulated queues, actual durations and0/0.5s extra
execution are included. Long playback delays widen, rather than tighten,
uncertainty. The contract does not permit free waiting or partial credit.

For each second's reachable masks use the minimum sender-map
reference-minus-selected MSE. Average these ten minima, outward-round as in
the previous geometric audit, and enforce each user's native floor. Optimizing
over the complete finite resource-valid path set yields the largest sufficient
conditional credit and any minimum-byte half-repayment witness. All sample
cones share the entry anchor, but their joint trajectory consistency is
relaxed. Therefore failure of this certificate is NOT an impossibility proof
for the coupled motion model. The previous unrestricted adaptive upper bound
also does not automatically apply after narrowing the uncertainty class.

Zero speed and a known generic orientation approach a static-viewport model,
with conservative boundary-cell ambiguity. Increasing speed or elapsed time
can only add masks and decrease the best guaranteed credit. Sufficiently large
cones exactly recover the prior complete geometric lower bound. These nesting
properties are tested independently of observed outcomes.

## What the exposed traces can establish

The source database documents50Hz head tracking. We inspect actual timestamps
and compute discrete adjacent-sample speeds rather than inferring a rate from
that description. Sampled speeds are LOWER bounds on maximum instantaneous
speed between observations. The1Hz quality samples can hide quick turns.
No outlier is deleted because it makes a candidate envelope inconvenient.

The training rule uses other scenes and excludes both target participant IDs.
Its95th-percentile trajectory maximum is an empirical quantile, not conformal
calibration or a95% joint/policy/deployment guarantee. Trajectories share people
and content; the168episode cases are not168 independent participants. All are
already exposed development data. Their original viewing clock differs from
the simulated network/playback clock. Source consistency does not validate
motion during a stall, feedback transport, continuous-time physiology or
unseen content/people. These checks identify whether this simple conditional
model is plausible and informative enough to merit further development.

## Sources and novelty boundary

The [QoEVAVE dataset documentation](https://qoevave.github.io/database/docs/intro)
describes the50Hz source tracking and source-data license. Original archives
remain local; public artifacts contain derived scalar measurement summaries,
not redistributed pose trajectories.

M. F. Romero Rondon, L. Sassatelli, R. Aparicio Pardo and F. Precioso,
[Revisiting Deep Architectures for Head Motion Prediction in360-degree Videos](https://arxiv.org/abs/1911.11702)
(author manuscript, revised2021) studies trajectory/content prediction and
emphasizes horizon-dependent evaluation and strong trajectory-only baselines.
That supports careful information/timing evaluation, not a numerical hard
speed threshold for our data. A useful point predictor is not automatically
a guaranteed uncertainty envelope. This audit neither implements TRACK nor
claims a novel motion predictor or a completed systematic literature review.

Spherical reachability, finite enumeration and empirical speed envelopes are
not new general methods. Any contribution here is the reproducible diagnosis
of coverage versus useful service guarantees under the explicitly fixed
streaming contract. Positive certificates alone would not establish novelty
or validate the model assumptions.
