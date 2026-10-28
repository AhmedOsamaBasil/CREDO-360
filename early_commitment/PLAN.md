# Early commitment and causal viewport-prefix study

## Scope and fixed decision before outcomes

Continue the exposed-data diagnosis, not a fresh confirmation. Use exactly the
168 existing episodes, six scenes, original event losses, 1,500,000-byte joint
cap, structural rungs2..5 and non-refilling reserve from the previous study.
Preserve earlier source and outcome hashes. No downloads, encoding, manuscript
edits, new participants or holdout. Publish implementation before the batch.

The previous bound locates most avoidable loss at the second allocation, before
completed recovery feedback. Test timing and earlier observable information,
not another fitted-model or parameter sweep. Viewport persistence and finite
dynamic programming are established mechanisms, not new algorithms claimed here.

## Causal information and forecasts

Reuse the private causal half-second pose samples and public sender distortion
maps. At each sample index h, combine only masks observed through h with known
sender maps. For unobserved frames, hold the most recently observed viewport
fixed. Aggregate weighted MSE before log/quality conversion. Generate derived
scalar quality forecasts for all six segments and rungs, but never publish raw
poses or masks. Future sender media is known; future viewport motion is not.
Mutation tests must prove that later masks cannot change a prefix forecast.

Releases follow the modeled per-user playback clock, not download completion.
Initial segments0/1 are already played. Completed-only mode uses a segment's
last sample only after playback completion plus feedback delay. Prefix mode
uses each half-second sample only after its presentation plus delay. Fixed
primary delay80ms; primary-policy sensitivity500ms, not a measured transport
claim. The new incremental feedback channel is replayed, NOT wire/HMD tested.
Earlier completed-segment wire measurements do not validate this extension.

Forecast pending commitments with the same visible prefix. Pending predicted
surplus affects planning only; actual debt credit still waits for complete
feedback. Initial reported loss and completed credits use the existing
reconstructed feedback. Evaluation retains original event loss and old labels.

## Policies and clock

Primary: prefix_mpc, exact capped-gain/minimum-extra-byte lookahead with the
hold-last-viewport forecast. Matched prefix_cost_greedy, prefix_greedy,
prefix_nash and prefix_maxmin share every information/action/resource rule.
completed_mpc uses the same optimizer but only completed-segment telemetry.

Two timing diagnostics use completed_mpc: wait_mpc waits for the next pending
completed report; slack_mpc waits only if every structurally allowed current
action remains deliverable before both users' queued media expires. No waiting
at cold start. Waiting charges elapsed playback/stall time; no free information.
Use .05s controller + .08s setup and 1.2Mbps equal-share fluid transfers as
before, ten-second pacing and nominal media segments. The prior final River01
duration caveat remains. No live throughput, decoder or HMD claim.

## Evaluation and stopping rule

All8 policies x168 episodes at80ms plus prefix_mpc x168 at500ms:1,512 runs.
Report unpaid fraction, half-repayment, quality, startup/total stalls, resource
use, actual donor/recipient floor violations, first/second decision changes,
visible prefix lengths, prediction errors and all per-scene/cohort outcomes.
Retain the seven previous policies as explicitly historical comparators; they
use different information and no added report delay, not matched ablations.

Progression requires primary80ms prefix_mpc to beat each matched nonwaiting
control AND each historical control by at least.005 mean unpaid fraction,
separately in v2/v3, with half-count not lower, worst-quality loss<=.02 and
mean-stall increase<=.1s. Require zero actual donor AND recipient floor losses.
This is an exploratory screen, not a significance/generalization claim. Wait
variants and500ms are diagnostics, not alternative winners selected afterward.
If it fails, preserve the failure and do not consume a fresh holdout.

Verify full scientific replay on Windows/Linux, public hash/source integrity,
private prefix derivation, independent clock/ledger and optimization checks.
Include analytical wait examples: receiving a report at F+delay for media ending
at F cannot fetch a next segment of positive latency tau by F; absent additional
buffer the forced starvation is at least delay+tau. No universal impossibility
claim for asynchronous players, other feedback schedules or other action sets.
