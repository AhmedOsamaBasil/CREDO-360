# Fixed Wu playback results

## Completed measurements

The single registered campaign completed all **366 sessions**, including 360
main observations and six perturbation controls, without retries or failed
sessions. All raw-event/accounting audits pass. The complete technical logs,
audit, descriptive report and source bindings are in
[`results/measured_v1`](results/measured_v1). No source video or raw pose is
redistributed. The registered runner, first-pair schedule, contract and paths
were not changed after observing outcomes.

**Every main observation has exactly zero measured-minus-ideal original-parent
recovery credit.** All 24 equal-clip summaries are consequently zero, with all
five clips and three repetitions present in each condition. There are no
protected-target discordances. This campaign does not establish a recovery
advantage or a timing-induced loss under the main configurations.

| Main-session result | Count |
|---|---:|
| Scheduled and valid | 360 |
| Original-parent resource-protected half-debt target met | 36 |
| Secondary actual-chunk resource-protected target met | 24 |
| Per-parent resource-cap failures | 36 |
| Cumulative-reserve failures | 0 |
| Missing final-frame callback witnesses | 0 |
| Ended/report-ready, callback-tail or old-epoch credit discordances | 0 |

All protected successes occur on **e2v07**. These are executions of ungated
proposed paths, not positive certified admissions: the preceding feasibility
audit admitted zero of 452 pairs. Repeated executions of ten fixed pairs are
not independent people or evidence of population-level superiority.

The 12-success difference between accounts consists of the two-second
rolling-Nash and max-min paths on e2v07, both startup modes, repeated three
times. Their original-parent quality floors pass, but each user's secondary
child-level account has one floor violation. Both credit fractions exceed
one half. Thus the difference is a **changed temporal quality-floor contract**,
not less numerical recovery credit under otherwise equivalent criteria.

The recipient's complete forty seconds of recovery media finishes between
41.4219 and 50.2625 seconds after its first recovery request (mean 45.6879).
Finishing every media unit is not the half-debt repayment criterion: sufficient
positive credit can accrue before the remaining media ends. Timing plots retain
all 120 configurations and show repetition ranges, not confidence intervals.

The three late-recipient controls each reduce the original-parent credited
fraction by exactly `51022126/137431607` (approximately 0.371255) relative to
the unperturbed ideal account; the three background-transfer controls have
zero credit difference. Their mean complete-media finish times are 84.0180 and
58.6514 seconds, respectively. Both controls inherit the e1v01 two-second cap
failure and are kept separate from the main summaries. The background control
intentionally violates the exclusive two-flow service assumption; it is not a
counterexample to a theorem conditioned on that assumption.

All 366 saved sessions identify Chromium 151.0.7922.34 and report a platform
D3D11 video decoder. The batch used one browser process and a fresh isolated
context/page per session; it did not reset operating-system or process caches.
Cold means no initial playback buffer. Video callbacks witness compositor
submission, not physical HMD presentation or every displayed frame. Finite
measurements do not establish a hard execution-delay bound or human QoE.

The complete source-bound figures and tables are in
[`../contract_evidence/results`](../contract_evidence/results).

- Measured report SHA-256: `7e72913a8feb0ab14b4be725e50048ff658dd81d447fd4ab398fb2174c8e53a2`
- Combined evidence SHA-256: `161c6bf22c20b6489a9641fa013bdac20a459b9134d406cb7e61712a2ee34f20`
- Figure-data SHA-256: `38f8015d191d3220cd4ae2441b80cea69068fe769a33432962bd68e04093d63f`

## Earlier integration-stage record

### Status at the integration freeze

Method `a80a5a17e650a5aca63a5d819a27a522d1b7ea7d` was published before the
source-specific plan was derived. The plan is an offline integration of already
exposed, frozen inputs. **No actual Wu browser-playback campaign has run at this
stage.** The four successful browser sessions below use generated test patterns,
not Wu videos, and cannot establish recovery performance.

### Generated-only evidence

The first attempt failed before playback with `ERR_NETWORK_ACCESS_DENIED` on
localhost. Its failed session and the three not-run configurations are retained
in `results/synthetic_01`. A separately approved loopback-access environment
check used a new directory with the same code, generated media and parameters.
All four sessions in `results/synthetic_02` completed and passed event audits:

| Delivery unit | Startup | Event audit | Missing tail witnesses |
|---|---|---|---:|
| 10 seconds | Cold | Pass | 0 |
| 10 seconds | Charged four-second buffer | Pass | 0 |
| 2 seconds | Cold | Pass | 0 |
| 2 seconds | Charged four-second buffer | Pass | 0 |

These fixtures repeat one previously generated ten-second pattern and its
children to exercise forty seconds of playback. They use a dummy zero-credit
quality ledger and are not contract-success tests. Raw event evidence, file
bindings, failed/not-run dispositions and report hashes are retained. Reauditing
the saved Windows sessions under Linux reproduces the exact reports; this is
not an independent Linux browser measurement.

### Fixed Wu schedule

All 16 registered clips remain accounted for: ten eligible clips, five in each
condition, and the original six exclusions. Exactly the first directed pair
per eligible clip is used. No pair was selected on recovery feasibility or
deadline proximity. The three frozen ideal-timing **ungated proposed** paths
are replayed; the schedule is not a claim of successful certified admission.

The 120 distinct configurations have 60 free-exploration and 60 content-focused
cells. Three repetitions give 360 main sessions; late-recipient and background
controls after each repetition give six more. Control indices are 120, 121,
242, 243, 364 and 365. All 408 distinct selected media files passed read-only
hash/size checks against the original private Wu v2 preparation on both systems.

The original-parent account is primary. Two-second delivery changes container
overhead and request cadence, so chunk quality and transport results are
secondary. Actual container overhead causes the first recovery parent in
`e1v01` and `e1v04` to exceed the fixed 1,500,000-byte cap:

| Clip | Two-second files per selected parent pair | Excess over cap |
|---|---:|---:|
| e1v01 | 1,502,228 bytes | 2,228 bytes |
| e1v04 | 1,507,160 bytes | 7,160 bytes |

This affects all three paths and both startup modes for those two clips:
12 configurations, 36 repeated main sessions. The six controls also inherit
the e1v01 two-second case. These records are retained, not replaced or repaired;
their resource-protected-success flag cannot be true even if playback later
meets its quality and deadline checks. All 120 configurations satisfy the
original cumulative reserve; all ten-second configurations satisfy the parent
byte cap. No allowance or path was changed to remove this finding.

No new people, fresh quality holdout, fitted controller, physical-network
measurement, interactive HMD presentation or subjective QoE result is claimed.
The later real campaign must preserve this entire schedule and failure ledger.

### Bindings

- Registration: `4b9030e2e4d53966ef56e0601e9f873473dd862fb9645719b53ada1b8b25a2b6`
- Complete cases/roster/schedule: `7c89c1cf432fa064fc3895192de8532ec7a85477c0ef22bd0dbe3a59f52767f3`
- Delivery-only schedule: `5ee8a175fb9a981b8a774d9b47311edf784235d92dd138f96a18723a96b04daf`
- Failed generated report: `87afb7c0129a97cc7e48cf657d5dc72cd8dfda1bc83057e4f6d302a4ff0080e8`
- Successful generated report: `8e458913fca2b760a39180553bf3426c01112d12e42f78150e8c99d286ec125c`

Use the commands in [README.md](README.md) to verify these published artifacts
without starting measurements. See [VERIFICATION.md](VERIFICATION.md) for checks.
