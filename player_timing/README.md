# Matched-path software-player timing study

This exposed engineering study tests whether the earlier completion/debt result
depends on ten-second files and cold startup. It does **not** introduce a new
recovery controller. The original service contract remains a reference, while
two-second lossless remux and charged buffering are explicitly secondary
transport configurations. No fresh holdout or new participant data is used.

Read the [protocol](PLAN.md), [implementation amendments](AMENDMENTS.md),
[results](results/diagnostics_v2/REPORT.md), [interpretation](INTERPRETATION.md)
and [verification record](VERIFICATION.md) together.

## What is compared

- Six existing scenes, the same 28 identities and 168 directed exposed episodes.
- Frozen **ungated proposed entry paths** from cost-greedy, rolling Nash and
  max-min; rung2 is a replay-only control. These are not the earlier admission
  gate's executed fallback actions, continuously adaptive policies, or a
  reproduction of a learned system from the literature.
- Four delivery/startup configurations: original ten-second or remuxed
  two-second files, each with cold start or a charged four-second buffer.
  Whole-file buffering rounds up to one ten-second or two two-second files.
- The original past-loss ledger, 50% target, 40-second first-request deadline,
  R4 nonrefilling reserve and 1.5MB parent-pair limit remain fixed. All MP4
  container bytes count; the two-second request cadence/setup is a changed
  transport configuration, not a replacement of the historical contract.
- Original parent credit requires every child of a parent to finish. A separate
  chunk account changes quality-floor and positive-improvement granularity;
  its labels are recomputed, not copied from the ten-second parent.
  Floors cover the full selected path, including late units; the past debt is
  an input from the earlier exposed records, not a newly induced human deficit.

The deterministic factorial contains 2,688 cells, **not 2,688 independent
trials**. The fixed browser schedule contains 72 sessions: six scenes, identity
pair1:2, three paths and four configurations, followed by two negative controls.
There is one session per cell, no selected reruns, no inferential p-values and
no population-level confidence interval.

## Measurement boundary

Two HTML video elements receive actual H.264 files through one shared loopback
HTTP payload shaper at 150,000 bytes/s. There is a 0.13s setup per request and
a capped finite service quantum. Raw logs retain each payload, service batch,
receipt, playback event, video-frame callback and completion report. A delayed
recipient and a competing 6MB fetch exercise deadline and shared-service
accounting. The same offline quality labels are never sent to the player.
Files are hash-checked and loaded into server memory before the session clock;
server disk I/O is excluded. "Cold" means no initial playback buffer, not cold
operating-system or media caches.

Browser events share one monotonic clock; server events remain in a separate
clock domain. `requestVideoFrameCallback` observes compositor submission, not
physical screen photons. Decoded-frame hashes establish remux identity, not
that every frame was displayed. Whole-file Blob playback is not a deployed
DASH/MSE player, physical network emulator, HMD experiment or subjective QoE
validation. Old pose acquisition time remains an offline media-indexing
assumption, not measured head motion during these playback delays.
The browser plays complete equirectangular files, not an interactive 3D
viewport extraction pipeline. Viewport quality is evaluated offline from the
existing tile maps and sampled traces, separately from these playback events.
Only the four recovery parents are played in these sessions; the earlier
twenty-second loss-generating interval is not remeasured here.

The browser run epoch precedes the first request slightly. The frozen audit
uses that stricter epoch; the post-hoc diagnostic explicitly realigns to the
first request and checks whether any parent credit or half-target changes.
It does not silently alter the primary output.
The saved `report_available_score` uses client-side report-ready time. It is
not a synchronized estimate of arrival at a remote controller; report receipt
and acknowledgment are recorded separately.

## Public reproduction

From the repository root, with the repository's Python dependencies and Node:

```sh
python -m player_timing.replay --verify
python -m player_timing.audit --verify
python -m player_timing.diagnose --verify
python -m player_timing.render --verify
python -m unittest player_timing.test_core player_timing.test_validation -v
node player_timing/test_service.cjs
python -m player_timing.prior_art_check
python -m player_timing.inspect --index 17
```

These commands replay published scalar data and audit raw events. They do not
download videos, access private poses or repeat the browser measurement. Raw
measurements have nondeterministic timestamps; their recorded audit and
scientific summaries are deterministic and hash-bound.

| Artifact | Purpose |
|---|---|
| `data/v2/derived.json.gz` | 96 parent/480 child identities, actual bytes/durations and exposed offline chunk labels |
| `results/replay_v2/` | All 2,688 analytical cells and fixed 74-session schedule |
| `results/browser_v2/` | Every scheduled raw browser/server record, runtime metadata and completion ledger |
| `results/audit_v2/` | Frozen raw-event checks and separately reported completion accounts |
| `results/diagnostics_v2/` | Post-hoc independent ledgers, matched differences, clock alignment and report |
| `results/presentation_v2/` | Source-bound figure data, PNG and SVG |
| `data/v1/`, `results/replay_v1/`, `results/compatibility_v1/` | Retained pre-normalization artifacts and failing compatibility smoke |
| `results/compatibility_v2/` | Corrected two-unit compatibility smoke, excluded from the 74 sessions |

## Repeating private preparation or live measurement

Raw media and poses are not redistributed. Existing source terms and the
hash-bound source manifest apply. Preparation expects the earlier local
`.external/causal_playback_v1` media and original exposed trace archives;
`python -m player_timing.prepare` creates a new output only. It verifies ordered
encoded payloads and every decoded-frame hash before deriving offline labels.
`--resume-media` permits explicit revalidation of a partial cache, not overwriting
a published feature artifact. The original failure history is in AMENDMENTS.md.

The browser harness needs Playwright and an isolated Chromium executable with
H.264 support. Set `PLAYWRIGHT_MODULE` to the installed module (or use normal
Node resolution) and `PLAYER_BROWSER` to that executable. Then
`node player_timing/measure.cjs --smoke` performs a separate compatibility
check; `node player_timing/measure.cjs` runs the full fixed schedule. Both refuse
an existing destination. A later replication must use a new explicitly
versioned destination and preserve the original records. Do not run heavy
regressions/preparation concurrently with live timing sessions.

Recorded environment: Windows10.0.26300, Intel i9-11900K,16 logical processors,
127.85GiB RAM, RTX3090/driver617.14, Node24.19.0 and isolated Chromium151.0.7922.34.
Exact executable/dependency hashes and decoder properties are in the records.
Chromium reports a platform D3D11 video decoder; this does not identify which
physical GPU performed every decode operation.
The workstation was shared with lightweight inspection/document editing, not
isolated as a controlled laboratory appliance. No personal browser was used.

The [focused primary-source follow-up](PRIOR_ART.md) resolves the three prior
full-text-access gaps, including both publisher PDFs supplied by the author.
Neither this study nor
passing tests establishes a novel general scheduling theorem or journal
readiness. Earlier frozen experiments and theoretical claim boundaries remain
unchanged; the old universal bound is not extended to a changed action class.
