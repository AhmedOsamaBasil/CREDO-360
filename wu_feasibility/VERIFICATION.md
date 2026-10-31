# Verification record

## Local checks

- Windows Python 3.12.14, NumPy 2.3.5: 44 new tests pass;
  full suite **973 tests + 89 subtests** passes.
- WSL Ubuntu Python 3.14.4: 44 new tests pass;
  full suite **969 tests + 89 subtests** passes. Four legacy Torch tests are
  verified on Windows, not included in that Linux count.
- No registered source changed after method publication `4358275`.
- The registered Windows evaluation completes and replays exactly.
- Complete Linux recomputation passes every registered scalar scientific check,
  but strict serialization replay fails at e1v05. The saved complete Linux
  artifact has four different maximum-mask witness IDs and zero other field or
  summary differences. This is **not an exact cross-platform replay pass**.
- The disclosed post-freeze scientific audit passes: original scalar extrema
  checks plus exact equality of all non-witness fields. It introduces no bound,
  quality, resource, clock, floor or endpoint tolerance.
- Both saved platform artifacts, input/method bindings and exact discrepancy
  records verify. No media, original poses or network access is needed to
  reproduce the numerical feasibility analysis.

## Clean-export verification

Use a complete `git archive` exported from the results commit, and run from the
extracted directory itself (not the development repository). Check on both OS:

```sh
python -m wu_feasibility.spec
python -m unittest wu_feasibility.test_core wu_feasibility.test_replication wu_feasibility.test_artifact -q
python -m wu_feasibility.replication --verify-saved wu_feasibility/results/replication_linux_v1
python -m wu_feasibility.replication --audit
```

On the original Windows numerical environment, additionally:

```sh
python -m wu_feasibility.run --verify
```

The original strict verifier intentionally remains strict; cross-platform
witness-ID serialization differences must not be described as passing it.
The scientific-output audit prints all differences rather than normalizing
or overwriting the original witnesses. Tests for bounds, rewards, paths and
summary mismatches remain exact.

## Scope and artifact inventory

The new result artifact has **37 files, 546,236 bytes**: 18 primary files and
19 complete Linux-replication/comparison files. It contains numerical derived
evidence only. The six excluded registrations remain as explicit records. The
local workspace guide is outside the repository and not part of the archive.

The 0.5-second allowance remains a conditional analytical premise. No new
browser playback, physical-network, HMD or participant study was conducted.
Remote CI status is separate from these local checks and must be read from the
specific GitHub Actions run; local success does not imply completed remote CI.
