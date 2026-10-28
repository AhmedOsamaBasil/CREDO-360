# Geometric viewport bounds under the unchanged recovery contract

Freeze method and protocol before the complete exposed batch. Preserve all
historical sources/results. No fresh holdout, private pose loading, new media,
network/player trial, manuscript edit or submission is included.

## Exact scope of geometry

Use the **existing sampled viewport model**, not a new physical renderer:
12 longitude by6 latitude tile centres, 100-degree horizontal and vertical
angular windows, circular yaw, pitch in[-90,90], inclusive50-degree half-FOV
boundaries, and normalized cosine(latitude) weights. This latitude/longitude
rectangle is not a perspective camera frustum, lens-distortion model or HMD
validation. Changing projection/FOV/grid/roll would change the contract's metric.

Enumerate every membership breakpoint (tile centre plus/minus50 degrees) and
one representative of each open interval on each axis, including poles and
the yaw seam. Deduplicate their Cartesian-product masks, retaining orientation
witnesses. Membership is constant inside an interval, so this is a complete
finite enumeration, not a sampled search over participant poses.

Independently exhaust all integer yaw/pitch positions with scalar membership
tests. In this fixed geometry all breakpoints are integral and adjacent gaps
exceed one degree, so that lattice covers every boundary and open-interval
pattern. Its mask set must agree exactly. Random and boundary probes additionally
check membership, normalized weights and wraparound; they are not the proof.

## Tighter envelope, unchanged admission logic

For each rung and sampled second, minimize/maximize reference-minus-selected
MSE over the complete geometric mask family instead of all convex tile weights.
Average the ten per-second extrema to bound a segment. Keep the existing
outward micro-MSE rounding/two-unit guard; rung2 remains identically zero.
Intersect with the already valid convex interval to enforce numerical nesting
at floating rounding boundaries; this does not loosen either bound or a floor.
Publish the extremal mask IDs for every rung/second and verify all extrema
independently using scalar weighted reductions. Allow arbitrary viewport changes
between samples: no head-speed bound, future trajectory or fitted risk level.

Reuse the frozen admission certificate and scalar path checker. The fixed
contract remains actual media duration, initial rung0 event, rung2 reference,
50% completed-segment repayment by40s, both-user native quality floors,1.5MB
per-round actual-file cap and the non-refilling R4 reserve. Exact initial past
ledger and known sender metadata remain declared assumptions.

Primary timing is the existing conditional0.5s per-segment execution allowance;
retain ideal and unbounded execution cases. No unconditional service guarantee.
The optimistic impossibility bound still credits all four segments and ignores
floors, so it does not confuse an arrival upper bound with a physical lower bound.
Separate admit, impossible and abstain; zero-admission precision is undefined.

Reproduce the previous all-convex certificate and retain exactly the same causal
point-planner/cost-greedy/rolling-Nash/max-min paths as matched controls. Their
saved paths were generated from past information, not future labels. Verify
their ledgers without retuning, and apply the new geometric certificate to
those paths. The independent exact future-known comparison is evaluation only.

## Predeclared evidence checks

- Complete mask enumeration and orientation witnesses; independent lattice match.
- Geometric lower bounds cannot decrease and upper bounds cannot increase
  relative to the old convex envelope; preserve all old impossibility decisions.
- Check every exposed native quality difference against the new bounds and
  every admitted witness against the actual trace's fixed contract.
- Independent scalar vs vector certificate extrema, feasible-path counts and
  minimum witness cost; previous future-known feasibility unchanged.
- Identical point-only controls and resource/clock ledgers; future-quality
  labels cannot enter geometry or the admission API.
- Report all outcomes, both cohorts and each scene, not only successes. Report
  tighter numerical bounds separately from useful positive admission.

All data are exposed. No result is independent confirmation or evidence of new
robust-control theory. If the tighter model still admits nobody, report it
without changing the target, timing allowance, floors or viewport domain.
