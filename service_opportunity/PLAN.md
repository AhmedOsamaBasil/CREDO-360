# Service contract and causal opportunity development

Freeze this plan and implementation before measuring service or running the
complete development comparison. Preserve all earlier artifacts. No new media,
participants, holdout, manuscript changes or retrospective threshold tuning.

## Controlled service validation, not Internet headroom estimation

Use two isolated Linux network namespaces connected only by a veth pair. A
2 Mbit/s HTB parent has a non-borrowing 1.5 Mbit/s foreground class and a
0.5 Mbit/s competing class. Two foreground TCP connections share the reserved
class. Disable segmentation/coalescing offloads on the two experiment devices.
Use 20/80 ms configured round-trip propagation, idle/saturated TCP background,
three repetitions each: twelve probes. Each probe transfers 1,500,000 payload
bytes, equally split between the two connections, using new TCP connections.
Require receiver-confirmed completion within 9.5 seconds, leaving 0.5 seconds
of the 10-second service slot for control/setup. Save full command/configuration,
per-flow timings, receiver byte counts, background evidence and qdisc counters.
Count connection setup and waiting for the slower foreground flow. Check a
negative control: foreground class reduced to 1 Mbit/s, same payload budget,
80 ms RTT, saturated competing class, three repetitions. Do not quietly lower
the payload budget if it fails. Clean up only namespaces created by this run.

The application contract is A=1,500,000 payload bytes per 10-second slot
(1.2 Mbit/s payload); the 20% difference from the reserved rate is an explicit
engineering margin, not a statistically certified service curve. This is a
controlled reservation, not evidence of spare bandwidth on real user paths.
There is no loss/jitter/wireless/multi-hop/HTTP/TLS/video-player validation.
Do not infer an end-to-end stall guarantee or RFC2212 implementation.

## Exposed-data model and matched comparisons

Retain the same 168 two-user episodes, six already-exposed scenes, .001 quality
units, first-two-segment loss D, fixed rung2 references and four 10-second
recovery slots. No donor loss or recipient reference-floor violation is allowed.
Both current payload cap A and finite non-refilling positive extra-byte reserve
apply. Reserve fractions rho=0.5,1,2 of four-slot baseline bytes; primary rho=1.
This grid is an engineering sensitivity, not a measured admission policy.

Model: deterministic 8-nearest-neighbor prefix forecast. Exclude the target
scene AND both target participant IDs from training: 130 other exposed
trajectories per target. Distance is absolute difference in original event loss
plus absolute differences in recipient and donor quality at every rung of the
observed recovery prefix, scaled in integer quality units. Current full quality
menus are revealed equally to all controllers, an oracle-current idealization;
the predictor never receives target future viewport-quality labels. Future
encoded representation sizes are known sender-side metadata, declared available.
Predict future absolute qualities by the rounded arithmetic mean of eight
neighbors; construct future zero-loss menus relative to their predicted rung2
qualities. No subjective model, fitted uncertainty coverage or repayment guarantee.

At each decision use exact multiple-choice gain/cost dynamic programming over
the actual current menu and point-predicted suffix; maximize capped terminal
compensation, then minimize reserve cost, then stable rung-path order. Execute
ONLY the first action and reforecast after the next current menu is observed.
Reserve and quality debt update from actual delivered actions, never forecasts.
This is standard certainty-equivalent receding-horizon control, not a claimed
new DP or learning principle. Report predicted half-repayment feasibility as a
diagnostic, not a hard admission guarantee.

Controls: greedy recovery, rolling Nash, rolling lexicographic max-min with
identical current menus/cap/reserve/history; a persistence forecast using the
same optimizer; and an explicitly future-known offline oracle. Windows=24,
same two initial impairment observations, no expiry within this short episode.
All methods may use the same exposed training data; rolling rules ignore it by
definition. The persistence control separates forecasting from optimization.

Record all actions, reserve/debt ledgers, prediction errors, nearest-neighbor
IDs, predicted feasibility and realized breaches, per-scene/cohort/all results,
absolute unpaid fractions, half-repayment, quality tradeoffs and action changes.
Do not treat 168 dependent pairs as independent replicates or use significance
tests to promote these exposed development results to confirmation.

Development progression requires: nominal service probes all meet the deadline;
negative control detects insufficient service; primary model mean unpaid loss
strictly lower than each of greedy/Nash/max-min/persistence in EACH v2/v3 cohort;
half-repayment counts no lower than each control in each cohort; and oracle
gap exists. Report failures without retuning. Even passing this exploratory
gate does not authorize or validate another holdout, deployment or new claims.

## Verification

Independent brute-force small DP checks, future-label mutation/prefix causality,
scene/identity exclusion, exact byte/debt conservation, zero donor loss, service
receipt/deadline verification, Windows/Linux complete deterministic replay,
prior immutable artifact checks, source/input/result hashes and fresh checkout.
Raw live timings are checked, not expected to reproduce byte-for-byte on rerun.
