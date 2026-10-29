# Fixed-contract causal-policy feasibility audit

This is an analytical extension on already exposed data, not a new holdout,
learned controller or independent confirmation. Prior geometric outcomes are
already known. Freeze this specification and implementation before its full
application; retain all outcomes and all earlier frozen files unchanged.

## Unchanged service question

Can a causal whole-segment policy promise at least half of the fixed past
distortion-seconds loss by 40 seconds, with both native quality floors, the
1.5 MB per-round cap, R4 nonrefilling extra-byte reserve and rungs 2..5?
Use the exact existing media durations and the existing 216 geometric masks.
Primary timing has 0.5 seconds extra execution per segment; report ideal
execution separately. No motion bound or distribution is introduced.

## Information and audit

Each selected whole-segment rendition is irrevocably committed before any
sample of that selected segment is played. Sender maps, file sizes, durations,
past debt, and all causally received earlier viewport feedback are available.
No unplayed future viewport samples are available. A zero-latency, complete
past-feedback relaxation is permitted for the upper-bound argument. Show
completed-report and sample-prefix timing for bound-maximizing example paths
with 0/80/500 ms reporting delay; these are analytical clocks, not wire tests.

Define a valid response adversary: after each recipient rung commitment, use
the ten saved geometric-minimum masks for that rung and segment. For any
deterministic policy this recursively defines an admissible fixed future
sequence. It does not assume a real user reacts adversarially to bitrate.
Compute native rounded credit from shared reference/selected masks. Relax
quality floors ONLY in the upper-bound optimization, never in the contract.
If even this enhanced controller cannot meet the target, the original cannot.

Compute a Bellman optimum over segment, reserve spent and playback/request
clocks. Independently enumerate every resource-valid four-action path using
the historical vector clock. Also repeat with the older generous lower+5
rounding envelope and require parity with published fixed-plan upper bounds.
Nonnegative extra waits must not increase credited recovery for a fixed path.
Publish every action-conditioned mask response, maximizing example path and
168 episode-specific comparisons; no target or bound selection after results.

## Analytical safeguards and scope

Exhaustively check 256 binary rectangular games and 512 coupled-subset games
against independent policy enumeration. Include positive examples where
informative past feedback or pre-commit current-state revelation improves
performance. These prevent overgeneralization of the information argument.
Synthetic masks/games are not measured human data.

The primary claim concerns deterministic causal policies and universal
pathwise promises in this temporally unrestricted, coarse angular-window
model. It is not an optimality theorem for all streaming controllers, an
expected-performance statement, a calibrated risk guarantee, or a result
about smooth human motion, perspective HMD rendering, within-segment
adaptation, action cancellation, speculative rendition downloads, or private
randomization against an oblivious stochastic environment.

Verify source/input/result hashes, scalar mask scoring, Bellman/path parity,
past-only debt projection, zero-current-sample access, waiting monotonicity,
rounding-envelope containment and both operating systems before publication.
No manuscript, acknowledgment, fresh holdout, network/HMD or participant work.
