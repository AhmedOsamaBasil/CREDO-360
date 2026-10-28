# Early commitments and causal viewport-prefix planning

This exposed-data experiment tests whether earlier observable viewport feedback
or delayed commitment fixes the preceding recovery controller's limitation.
**The predeclared progression screen fails.** The prefix planner improves over
its completed-feedback ablation but not over simple cost-greedy. Waiting for
reports substantially increases simulated stalls. See
[INTERPRETATION.md](INTERPRETATION.md), the [fixed plan](PLAN.md), and the
[complete results](results/development_v1/REPORT.md).

## Implemented mechanism

For every observed half-second viewport sample, combine the previously observed
tile masks with the sender's per-frame/per-rung distortion maps. Unknown future
viewport masks are replaced by the **last observed mask**, not by true future
motion. Average weighted MSE before converting to PSNR and the existing quality
index. This is a reference-assisted sender-side forecast, not a no-reference
metric, a learned predictor or a new optimization principle.
The whole clip must already be encoded so its future sender maps and file sizes
are available: this is a video-on-demand assumption, not unseen live content.

`core.py` selects visible samples using each user's playback-completion clock
and a declared feedback delay. `replay.py` passes scalar forecasts to matched
greedy, Nash, max-min and finite-horizon controllers. All policies share the
same actual-file byte cap, finite reserve, structural rung floor and predicted
quality protections. Pending compensation is a planning estimate only; the
delivered ledger waits for complete reconstructed feedback.

`wait_mpc` waits for the next complete report; `slack_mpc` does so only when a
conservative bound permits every currently structural-feasible action without
starving either user. All waiting is charged to playback. Terminal repayment
is measured over four played recovery segments, **not by a fixed wall-clock
deadline**; longer waits increase the reported media-finish and stall times.

The primary feedback delay is80ms with a fixed500ms sensitivity. Both are
modeled assumptions, not measured incremental-channel guarantees. No new
network transfer, physical HMD, renderer integration or human QoE trial was run.
Previous wire tests concern completed-segment feedback and must not be used as
validation of this new incremental channel. No authentication/TLS/packet-loss,
telemetry bandwidth or jitter model was added. The earlier nominal ten-second
duration approximation remains, including the one-frame-short River01 tail.

## Reproduce from the public checkout

Use the repository Python dependencies (NumPy and pytest suffice for the new
tests/replay; Matplotlib renders the optional figure):

```sh
python -m pytest early_commitment -q
python -m early_commitment.verify
python -m early_commitment.diagnose --verify
```

The verifier reconstructs all1,512 runs, checks6,048 allocation/clock/ledger
decisions, and independently enumerates672 primary-policy optimization queries.
Both Windows and Linux produce scientific hash
`9ebf798b46f0db9d9033bf5d129d1e107e238d2c61817bf65e763165aece44cf`.
The separate diagnostic checks1,008 completed-feature parity cases and the
telescoping future-known opportunity-loss identity. It is explicitly post-hoc.

`data/prefix_v1/forecasts.json.gz` contains scalar forecasts for168 user-scene
records x60 observed prefixes x6 segments x6 representations. It contains no
raw pose or mask stream. These are pseudonymous derived research measurements,
not a promise that orientation cannot be inferred from them. Respect the
original dataset terms and do not treat these results as independent people.

Private regeneration, when the original ignored local events are available:

```sh
python -m early_commitment.prepare --verify
```

It checks the original event-file and sender-map hashes and recreates every
forecast. Public verification does not require or redistribute private traces.
`prepare` and `run` refuse to overwrite existing output directories. Preserve
frozen results; use a separate versioned study for any methodological change.

## Provenance and limits

Implementation and protocol were committed as `23d1fc4` before prefix-data
preparation and full outcomes. Initial synthetic-test corrections concerned
an over-saturated spatial-MSE fixture and a fixture whose optimizer deferred
the first gain; the underlying method was not changed to pass those assertions.
All28 new tests passed before the batch. Full regression: Windows301 tests and
Linux297 tests, each plus24 subtests; four Torch tests run only on Windows.
Portable5 tests pass on both systems; the existing JavaScript client passes11
assertions. Cross-platform agreement validates implementation, not superiority.

All six scenes and participant sequences were already exposed. The analysis
does not provide independent validation, novelty proof, perceptual efficacy,
calibrated uncertainty, a general scheduling theorem or a safe admission rule.
No new holdout or manuscript change is warranted by the failed screen alone.
