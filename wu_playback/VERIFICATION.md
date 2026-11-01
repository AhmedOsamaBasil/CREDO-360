# Verification record

## Completed real campaign

The registered campaign completed all 366 scheduled sessions with no automatic
retries, runner failures or missing records. The unchanged audit accepts all
366; the public export retains all raw technical event logs, including controls.
Windows and WSL reproduce the entire saved audit and report exactly:
`7e72913a8feb0ab14b4be725e50048ff658dd81d447fd4ab398fb2174c8e53a2`.
WSL replays Windows measurements; it is not an independent Linux browser trial.

The post-campaign full regression suite passes **1,044 tests plus 89 subtests
on Windows**, and **1,040 plus 89 on Linux**. The four-test difference is the
pre-existing Windows Torch set. Windows runner path/schema guards and shared
service tests also pass. No measured outcome caused a registered-source edit.

Combined evidence assembly, all eight LaTeX fragments, and saved figure-data
and artifact-hash verification pass on both platforms. The three PDF figures
were visually inspected and have embedded Arial fonts with no Type 3 fonts.
Linux verifies saved figure data and file hashes, not an independent rendering.
The original playback registration remains
`4b9030e2e4d53966ef56e0601e9f873473dd862fb9645719b53ada1b8b25a2b6`.

Verify without launching a browser:

```sh
python -m wu_playback.reporting --output wu_playback/results/measured_v1 --verify
python -m contract_evidence.assemble --output contract_evidence/results/evidence_v1 --verify
python -m contract_evidence.latex_tables --evidence contract_evidence/results/evidence_v1 --output contract_evidence/results/tables_v1 --verify
python -m contract_evidence.render --evidence contract_evidence/results/evidence_v1 --output contract_evidence/results/figures_v1 --verify
```

Method CI 41231731950, plan CI 41232187180, reporting CI 41248140677 and
presentation CI 41258677144 subsequently completed successfully. They validate
software checks, not an independent repetition of measured outcomes. The
following record preserves what had been checked before real measurement.

## Method-before-plan ordering

The integration was frozen and published as
`a80a5a17e650a5aca63a5d819a27a522d1b7ea7d` before `wu_playback.build` was
applied to the Wu artifact. Its registered code remains unchanged. The
source-specific schedule then built successfully and reproduced exactly on
Windows and WSL, including all native integer accounts, path identities,
resource failures and delivery-only projections. No Wu browser session ran.

## Checks completed

- Before freeze: 32 new tests passed on both platforms; three checks were
  explicitly skipped pending registration and the not-yet-built plan.
- After freeze, before plan: 33 passed, two plan-dependent skips. Full regression
  passed with 1,006 tests plus 89 subtests on Windows and 1,002 plus 89 on Linux,
  with those same two skips. The four-test difference is the existing Torch
  test set run on Windows, not a newly omitted scientific check.
- After plan: all 35 new tests passed without skips on both platforms.
- Final complete regression after plan: 1,008 tests plus 89 subtests passed on
  Windows; 1,004 plus 89 on Linux, with no skips. All 366 delivery entries also
  passed the JavaScript runner's schema validation without launching a browser.
- Both complete saved synthetic reports reproduced exactly on both platforms.
  Linux reaudits Windows events; no Linux browser replication is claimed.
- A complete clean Git export of the method commit was tested from its own
  working directory on both systems: registration, 33 tests/two expected
  plan skips, and both saved synthetic audits passed.
- Windows JavaScript delivery/path-confinement guards and the unchanged shared
  service tests passed. WSL has no Node installation; JavaScript checks were
  not represented as a WSL run. Existing client checks (11 assertions) and
  portable checks (five tests) also passed on Windows.
- Read-only preflight hashed all 408 selected private media files successfully
  on both platforms. No video decoding, encoding or pose inspection occurred
  during that preflight.
- The original preparation, pose, feasibility and timing packages were not
  modified. The generated localhost failure is preserved separately, not
  silently retried or counted as successful.

The exact prior feasibility CI run 41229809374 completed successfully. Method
CI run 41231731950 was still in progress at the first post-push check; local
tests are not a claim that a pending remote workflow has passed.

## Scope at the integration freeze

The fixed first-pair roster, cyclic order, original quality/deadline/resource
contract, separate parent/chunk accounts, exact large-integer arithmetic,
request-aligned clock and no-retry rule are unchanged. Real measurements still
require explicit activation with the published digest and pinned runtime.

The generated compatibility pass does not validate real Wu playback, all
displayed frames, an HMD, a hard execution-delay bound, human QoE or controller
superiority. Twelve two-second configurations already fail the unchanged
per-parent resource cap because of actual container overhead; those failures
remain in the plan and its results, as documented in [RESULTS.md](RESULTS.md).
