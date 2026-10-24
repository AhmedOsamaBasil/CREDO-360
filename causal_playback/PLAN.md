# Causal current-quality and transport integration protocol

Publish this plan and implementation before the complete exposed-data replay
or live pilot. Preserve every earlier frozen method/result. No new holdout,
downloads, manuscript changes, journal contact or human participants.

## Media and information boundary

Reuse the six exposed v2/v3 scenes and 168 directed two-user episodes. Remux
the existing 1920x960 renditions into six 10-second MP4 files without encoding.
Verify source hashes and per-segment ordered video-packet payload hashes/sizes
against the original PTS bins. Use ACTUAL remuxed file bytes, including container
overhead, for every new budget calculation. Save provenance; do not redistribute
third-party media. If packet identity fails, stop rather than silently align
different content to old quality labels. Segment data are available locally.

Original event loss is retrospective loss over segments0/1; the recovery phase
begins AFTER both were played. Initial recovery buffer is zero. This models a
cold recovery boundary, not a continuously buffered commercial player. All
policies know the same original loss, past selected-rung quality feedback,
sender full-sphere quality tables, representation sizes and reserved service.
They NEVER receive current/future target viewport labels before selection.

Current-quality estimator: per-user exponentially smoothed residual between
observed selected-rung quality and sender full-sphere quality, coefficient1/2.
Initialize with the first observed residual; update only after that segment's
modeled playback COMPLETES. Predict each current rung by sender quality plus
the residual, clipped to the existing [1,5] objective index and integer .001
units. Sender quality itself is retrospective offline content metadata; it
does not use future head movement. Completed-segment quality feedback is a
reference-assisted emulation, not a deployed client quality-measurement system.

Candidate future opportunity model: eight nearest training trajectories from
other scenes, excluding BOTH target identities (130 eligible records). Distance
is original-event-loss difference plus selected-feedback residual differences
at matching segment/user/rung observations. Predict future rung residuals by
their rounded mean, added to known future sender quality. Current estimates
are identical across all policies, not replaced by the neighbor forecast.
Persistence and unconditional-mean controls use the same optimizer. No tuned
hyperparameters, uncertainty coverage or safe admission guarantee is claimed.

## Shared action and recovery contract

Use a structural minimum rung2 for both users, with all16 joint pairs of
rungs2..5 considered. This prevents predicted clipping plateaus from justifying
representation downgrades. Also mask actions below PREDICTED reference quality.
This is not a guarantee of actual viewport-quality floors: measure every actual
recipient/donor violation. The action set differs from the previous oracle-
current audit, so changes cannot be attributed solely to prediction.

Absolute cap1,500,000 file bytes per round; non-refilling reserve equal to summed
pair-rung2 bytes over the four recovery segments. Debit positive extra file
bytes, with no refunds. Keep original D and half-repayment target. Actual credit
is positive quality over the original reference, available to the controller
only after playback completion. Pending delivered segments contribute only
predicted commitments to the planning deficit; they are not actual repayment.
Report predicted versus realized floors, commitments and debt separately.

Compare candidate, greedy recovery, cost-matched greedy, rolling Nash, rolling
lexicographic max-min, persistence lookahead and unconditional-mean lookahead.
All use causal current estimates and the same delayed feedback. Rolling history
uses actual selected quality once reported, otherwise its stored prediction.
Window24 contains all six segments; no expiry. Model predictive choices use
the exact existing gain/cost DP; no new algorithmic principle is asserted.

## Exposed deterministic replay

All168 episodes x seven policies. Simulated shared payload service1.2Mbit/s,
80ms round-trip setup,50ms controller cost, equal-rate sharing while both flows
are active. Ten-second paced round starts (late rounds extend); use continuous
playback accounting including startup, controller/setup, transfer, waiting and
inter-round overhead. This replay is explicitly a fluid timing model, not live
evidence. Compare with separately labeled oracle-current prior results only as
context, not a matched causal effect. Keep all adverse outcomes.

## Live engineering pilot

Preselect recipient1/donor2 in each of six scenes, not by observed performance.
For each, test candidate, greedy, rolling Nash and rolling max-min once under
the prior isolated2Mbit/s HTB parent: foreground1.5Mbit/s, saturated background
0.5Mbit/s, borrowing disabled,80ms configured RTT, offloads disabled. Rotate
policy order by scene index. Run at most two independent namespace pairs in
parallel. Twenty-four nominal episodes, four selected transfers per user each.

Add six candidate-only stress episodes, same scenes/IDs, with foreground
750kbit/s while the controller still assumes the nominal budget. These are
intentional service-contract breaches, not comparative efficacy evidence.

Transfer the selected MP4 files concurrently over instrumented TCP. Receiver
must verify exact bytes/SHA256 and report monotonic receipt timestamps. All
controller, process launch, file I/O, hashing, synchronization and pacing time
is charged. Buffer updates use the previously corrected playback clock.
Quality feedback cannot be released at download completion; it waits until
the queued segment's playback end. Final draining is computed analytically,
not displayed or decoded. Never count post-end-of-media waiting as a stall.
This is a measured transport plus emulated playback-clock test, NOT an HMD,
decoder, HTTP/TLS or subjective study. Preserve partial/error records.

## Predeclared engineering/research checks

Integrity: zero current/future-label leakage under mutation tests; exact byte
and source identities; debt/reserve conservation; receipt and feedback-clock
replay; all selected transfers fit their declared cap/reserve. Record, do not
hide, any actual floor losses or unsuccessful quality predictions.

Before considering another holdout require candidate mean unpaid fraction at
least0.005 lower than EACH of the six causal controls in BOTH exposed cohorts,
no lower half-repayment count, mean episode worst-quality loss no worse than
0.02 versus EACH control, and zero actual donor floor violations. These are
exploratory practical gates, not statistical inference. Nominal live transfers
must all complete within9.5s from each decision boundary, including control
and receipt verification; report startup stall separately. Stress probes need
not all fail a deadline because actual selected demand varies. Do not retune
the candidate, quality target, selection, service or gate after outcomes.

Publish code, raw timing/receipts, replay results, adverse findings, figures,
cross-platform verification and reproducibility notes before any new holdout.
