# Wu measured-playback integration v1

## Scope and immutable predecessors

Integrate the measured software-playback stage in
`confirmation_protocol/design.json`. Preserve the original Wu roster, pose
adapter, encoding/labels, feasibility evaluation and earlier `player_timing`
experiments. No newly sampled people, fresh quality holdout, predictor fitting,
quality/target/cap/reserve change, media re-encoding or manuscript edit occurs.
The numerical feasibility labels are already exposed. The integration method
and exact schedule must be published before any actual Wu playback session.

This is an isolated headless Chromium experiment, not control of a personal
browser. Actual H.264 files are delivered to two HTML video elements over one
shared loopback application payload shaper. The frozen `player_timing/player.js`
and `service.cjs` are reused unchanged. The browser plays equirectangular files,
not a rendered interactive HMD viewport; sampled objective viewport quality
remains offline. No subjective QoE, physical display photons, physical network
capacity or universal hard execution-delay guarantee is established.

## Selection and complete schedule

Retain all 16 registrations and six metadata exclusions. Select exactly the
first directed pair from the frozen cycle of each of the ten eligible clips,
not a feasible/best/near-deadline pair. Select each published **ideal-timing
ungated proposed** path for cost-greedy, rolling Nash and max-min, matching the
earlier player-timing protocol. These are not the admission-gated reference
fallbacks and do not represent useful certified admissions. Paths are fixed
before playback and never recomputed from future labels or measured feedback.

For every clip: three paths x delivery unit 10/2 seconds x cold/charged-four-
second startup = twelve cells. There are three repetitions. Within each
repetition, visit sorted clip IDs and sort cells by policy order (cost-greedy,
rolling Nash, max-min), ascending unit duration (2,10), then cold before buffered.
Cyclically rotate those twelve cells by `(clip index + repetition index) % 12`.
After every repetition, run both original negative controls on the first sorted
clip, cost-greedy, 2-second cold: first recipient delayed 40 seconds before
service eligibility, then one concurrent 6,000,000-byte background transfer.
Total: **360 main sessions + 6 controls = 366**, all sequential. Identical
Nash/max-min paths remain separate scheduled measurements, not independent
algorithmic evidence. Repetitions are not independent participants.

Missing/unusable first pairs or missing frozen proposed paths cause explicit
preparation failure; never substitute another pair, path or clip. Existing
registration and input hashes are checked. No result-dependent scheduling,
optional stopping, automatic retries or resume. Failed sessions are retained
and the fixed later cells continue; a fatal batch/infrastructure failure retains
completed checkpoints and identifies an incomplete batch. An incomplete batch
cannot be summarized as the planned complete experiment. Failed scientific
audits invalidate affected claims, not the remaining failure ledger.

## Transport, clocks and bytes

Use the exact private Wu v2 manifest and prepared parent/child MP4s, without
modifying them. Hash all unique selected files before starting the batch; each
session also verifies and preloads its files before its measured server epoch.
Disk I/O is excluded from the session clock. Cold means no initial playback
buffer, not cold operating-system/media caches. Record the actual pinned Node,
Playwright, Chromium executable/main library/resources and host runtime; this
is not a hermetic snapshot of all OS dependencies. Abort before measurement
if that runtime changes. Browser contexts are isolated; no personal profile.

The unchanged shaper serves at 150,000 payload bytes/s, 0.13-second setup and
the existing capped 20ms service quantum; idle capacity is not banked. Requests
follow one nominal unit interval and both previous verified receipts. Two-second
delivery changes request cadence/setup, explicitly a secondary transport
configuration, not an extension of the whole-parent policy theorem.

Every actual container byte counts. Per-unit positive excess over the matched
rung-2 pair accumulates without refunds or refill against original R4. Aggregate
actual selected unit bytes per parent against 1,500,000 bytes. Report any
two-second overhead-induced cap/reserve failure; do not change a path to fit.
The competing background fetch shares capacity but is not recovery reserve.
Buffered startup waits until both users have at least four seconds in complete
received units: one 10-second or two 2-second units. All wait and delivery time
is charged; no free prefetch or restarted deadline.

Primary measured time starts at the first recovery request on the **browser's
own** monotonic clock. Preserve the earlier browser-run epoch as a separately
reported sensitivity, not silently as the deadline origin. Server clocks remain
separate; never subtract server from browser timestamps. The 150-second watchdog
retains censored raw events, not an assumed completion.

## Quality and accounting

Use already published nearest-even negative micro-MSE parent/child labels.
Past positive debt, improvement, floor and target arithmetic uses exact Python
integers in micro-MSE x media ticks, including quantities above 2^53. Do not
round through JSON floating-point values. Native units never enter Node/page
configuration; the delivery allowlist contains only unit/file identity and
execution parameters. Original past debt is input, not newly induced human harm.

The primary account uses the original parent gain and floors. All children
must complete before a parent is credited, and both users' floors include
late parents. Secondary chunk gain/floors use the actual published child labels,
not copied parent averages. Report chunk/parent differences separately. Keep
zero-debt status distinct from successful recovery.

The ideal reference uses exact integer transfer and playback ticks, zero decoder
delay and charged buffering. Cold 10-second clocks and primary credit must
match the earlier independent integer ledger. Controls compare to an explicitly
unperturbed ideal reference, not a claimed exact prediction of injected traffic.

Measured ended, client-report-ready and callback-tail accounts are separate.
Convert decimal serialized browser milliseconds and the first request to exact
rationals for deadline comparison; no new positive deadline epsilon. The old
event/media/service validators and their engineering tolerances are retained
unchanged, but their floating-point credit summaries are not used as this
integration's primary result. An independent scalar accumulator checks primary
and secondary measured credit. Tail callbacks are compositor evidence, not proof
of every displayed frame. Missing callbacks/tails remain observed limitations.

## Validation, publication and interpretation

Before freeze, generated-only fixtures test causal delivery allowlists, resource
conservation, late floors, exact boundary/large-integer arithmetic, first-request
alignment, all schedule cells and event corruption. Reuse only the previously
published generated test-pattern media for browser compatibility, in four
40-second parent/chunk cold/buffered cells. This repetition is a synthetic test
fixture, never a replacement/concatenation of Wu stimulus material. Its dummy
zero-credit quality ledger is not a research outcome or a contract-success test.

The initial generated attempt was denied localhost access by the sandbox before
playback; its failed record and three not-run cells are retained. A separately
authorized environment check uses a new directory with loopback access and
unchanged code/media/parameters. It is not a selected rerun of a Wu session.
No original media is redistributed. Publish only code, derived schedules,
synthetic technical logs and eventual raw timing/derived audits without poses,
private credentials or local instructions. Freeze/publish before activation.

Later reporting must retain all signed measured-minus-ideal differences,
protected-target discordances, completion times, missing/invalid accounts and
controls. Use clip-wise matched descriptions and separate free/focused strata;
no iid p-values/intervals over sessions. No outcome is required to exhibit a
deadline cliff, and no finite test establishes a hard 0.5s execution bound.
Passing compatibility/integration tests does not mean the Wu timing campaign
has run, or establish recovery benefit, human QoE or journal readiness.
