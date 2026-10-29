# Verification record

## Frozen sequence and retained corrections

The initial protocol/method was published as 18763c7 before private derivation.
Correction 24be731 restores the original offline pose-sampling convention after
a parent-quality parity assertion rejected the causal-cache sampler. The 96
parent/480 child payload and decoded-frame checks had already succeeded; their
cached files were revalidated without overwriting them.

The initial remux/replay and browser timestamp diagnostic are retained at
bd994c0 and under `data/v1`, `results/replay_v1`, `results/compatibility_v1`.
The first child had a nonzero PTS origin and a 2.066667s browser duration rather
than 2s. Uniform zero-origin normalization was frozen at 36f2b40 before v2
preparation or full measurement. It preserves every encoded payload and decoded
frame while recounting container bytes. Data/replay/corrected smoke were
published as 123f533 before the 74-session batch. No frozen primary file changed
during or after that batch. Details are in [AMENDMENTS.md](AMENDMENTS.md).

Preparation verifies all 96 original parents and 480 independently decodable
children against ordered packet payloads and decoded frames. Private offline
quality features for 168 episodes were independently rederived on Windows and
Linux; maximum parent-label difference is 4.998413736245766e-7dB, within the
unchanged 2e-6dB parity tolerance. This is sampled objective-label reconstruction,
not human-QoE or physical-display validation.

## Completed measurement and independent checks

The full sequential browser batch ran once on Windows: 72 scheduled main
sessions plus two controls, all 74 completed and passed audit. There were no
automatic retries or omitted sessions. The earlier two-unit compatibility
smokes are separate and excluded. Heavy regressions/preparation were not run
concurrently with the timed batch; lightweight source review and documentation
work did occur on the shared workstation.

Public replay/verification on both Windows and WSL/Linux gives identical hashes:

```text
Analytical replay, 2688 cells:
b9ceec4e37906888ca38024f564ae0e5335474e4fbf852f60ddb30654537f7e5
Frozen measured-record audit, 74 sessions:
a36de5d4cac90ebcd4cabcbd383d93fa5cbfda25e4eada8a927ec793294be5be
Independent post-hoc diagnostics:
b21192a69c9779e237f02af787f5c86eec725a232ec2bc35dbd7433ab3ff90ea
Figure summary:
a9bff5eabc9399ccd71db88fa1065adc0df4b00b5e31a643e517387687b5ec1e
```

Cross-platform replay audits the **same** measured records. It is not a second
independent measurement batch. Timestamped runs are not expected to reproduce
bit-for-bit; their archived raw logs, analysis and summaries are hash-bound.

- 672 independent original clock/score parity checks and 62 published executed-
  gate score checks. Proposed ungated paths are distinguished from old gate
  fallback paths.
- 5,376 independent analytical ledgers and 2,688 independent extra-byte ledgers.
- 131,409 nonoverlapping service-credit intervals; 1,809 server payload identities
  (including the background transfer); 1,808 matching client/server report bodies.
- 296 independent measured account reconstructions, with separate ended-event,
  client-report-ready and callback-tail timing. The first-request alignment
  sensitivity is retained rather than silently changing the frozen audit.
- Payload identities, shared-rate budget, request/setup cadence, actual media
  duration, event ordering, callback progression and charged startup checked.
- The PNG was visually inspected. PNG/SVG bytes and their plotted source values
  are bound to the renderer and audit hashes; cross-platform verification checks
  those published bytes, not font-dependent rerendering equivalence.

## Tests and environment

All 36 new Python method/validation tests pass on both operating systems,
including raw-event corruption rejection and an independent integer ledger.
Full regressions pass 490 tests plus 24 subtests on Windows and 486 plus 24 on
Linux; four Torch-dependent legacy tests run on Windows only. Portable-model
checks pass five on each operating system. Windows JavaScript checks include
11 existing feedback-protocol assertions, the new shared-service tests and
syntax checks of all three runtime scripts. The elementary Nash counterexample
also passes 1,001 exact rational identity checks; it is not a new theorem.

The first post-batch Windows full-suite attempt had 489 passes and one fixture
setup error: the sandbox's default temporary directory could not be created.
The full unchanged suite then passed with a new explicit workspace-local
`--basetemp`; no scientific data or source was altered to make it pass. A
Matplotlib font-cache permission warning did not prevent figure generation.
WSL emitted a nonfatal root systemd-session warning. These environment issues
are separate from the retained preparation/compatibility corrections above.

Runtime: Windows 10.0.26300, i9-11900K/16 logical processors, 127.85GiB RAM,
RTX3090 driver617.14, Node24.19.0, Playwright1.62.1 and isolated
Chromium151.0.7922.34. FFmpeg preparation used8.0.1-3ubuntu2. The browser
executable hash is in raw metadata. All 1,808 media property records report a
platform D3D11 decoder, without identifying a physical GPU for every operation.
Server files are preloaded/hash-checked before the session clock; this is not
a cold-cache or physical-link benchmark.

New code/results, public reproduction notes and focused source comparison are
isolated under `player_timing/`. Earlier frozen packages/results remain unchanged.
Source videos, raw poses, supplied paper PDFs and local instruction files are
not included. The manuscript and acknowledgment remain unchanged. Local test
success is distinct from remote CI for the final commit; consult that exact
workflow rather than inferring its completion from these checks.
