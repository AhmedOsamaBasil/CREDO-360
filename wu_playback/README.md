# Wu measured-playback integration

This package freezes the predeclared **366-session** software-playback protocol:
ten fixed first pairs, three frozen proposed controls, two delivery sizes, two
startup modes and three repetitions, plus six negative controls. It does not
fit a controller or change the quality/deadline/resource contract.

Read [PROTOCOL.md](PROTOCOL.md). The original parent account is primary; the
changed chunk granularity and transport overhead are reported separately.
Raw videos/poses are not redistributed, and no personal browser is used.

The fixed plan and generated-only evidence are described in
[RESULTS.md](RESULTS.md), with validation in [VERIFICATION.md](VERIFICATION.md).
The real Wu campaign has not yet run. Twelve two-second configurations retain
container-overhead cap failures under the unchanged contract.

## Offline verification

```sh
python -m wu_playback.spec
python -m unittest wu_playback.test_core wu_playback.test_audit wu_playback.test_validation -v
node wu_playback/test_runner.cjs
node player_timing/test_service.cjs
python -m wu_playback.synthetic_audit --output wu_playback/results/synthetic_01 --verify
python -m wu_playback.synthetic_audit --output wu_playback/results/synthetic_02 --verify
python -m wu_playback.build --verify
```

These commands verify published evidence; they do not repeat browser playback.
The first generated-only attempt failed before playback because localhost access
was denied by the sandbox. It and the three not-run cells are retained. The
separate permission-controlled generated attempt completed all four configurations
and passed raw-event audits. Synthetic patterns and a dummy zero-credit ledger
do not establish recovery benefit or source-specific browser compatibility.

## Separate activation boundary

After the method is published, `python -m wu_playback.build` creates the fixed
plan once. Publish that plan before measurement. No output directory is reused.
The real runner also requires an explicit exact registration SHA256, the private
Wu v2 preparation, a new private output directory, the pinned isolated Chromium,
the pinned Playwright installation, and the Python used for read-only preflight.

Set `PLAYWRIGHT_MODULE`, `PLAYER_BROWSER`, and `WU_PYTHON` to those local tools;
the runtime is checked against `runtime.json`. Then, **only when activating a
new authorized real batch**, use:

```sh
node wu_playback/measure.cjs --activate REGISTRATION_SHA256 --private PRIVATE_WU_V2_ROOT --output NEW_PRIVATE_ATTEMPT
```

No resume or automatic retries are provided. The scheduled file hashes are
checked before browser launch and again per session. A loopback permission
failure is retained, not silently rerun. Do not run heavy preparation/regression
jobs concurrently with the measured campaign. Keep the machine awake and record
interruptions; an incomplete batch is not a completed confirmation.

After every scheduled session is accounted for, audit without changing the raw
events:

```sh
python -m wu_playback.audit --raw PRIVATE_ATTEMPT --output NEW_AUDIT.json.gz
python -m wu_playback.audit --raw PRIVATE_ATTEMPT --output NEW_AUDIT.json.gz --verify
```

All numerical decisions use the browser's first request and exact native integer
credit. Existing scalar service/event checks are reused; ended, report-ready,
callback-tail and old-epoch sensitivity accounts remain separate. No finite
compatibility test establishes a hard 0.5-second execution bound, physical HMD
presentation, subjective QoE, new algorithmic superiority or journal readiness.
