# Verification record

## Frozen method and provenance

Commit `f7f2cd6fcdbb655a2aaa710dad73b41cd3109a58` was committed and pushed
before deriving the new private motion features or applying the audit to all
exposed episodes. Its eight hash-bound method, test and protocol files remain
unchanged after outcomes. Dependency and input hashes are retained in both
metadata files. `diagnose.py`, its figures and interpretation are explicitly
post-outcome additions, not a change to the model or contract.

| Artifact | Canonical scientific SHA-256 |
|---|---|
| Derived scalar features | `cc4aa69d5bb7c107bf27f818e483785a81ac351998b9c0bca4a671f79f4f50ef` |
| Complete conditional audit | `f66e7e92aa3aab21c7e5b93d9347dc671a9a2cf091504692dc167f0b85046fcc` |
| Post-outcome diagnostics | `95a4dd56137506c6f1b2c866c35a70ffc4a3d154daf1c33f7484f65d7f28c519` |

All three canonical hashes reproduce on Windows and WSL/Linux. Compressed-file
hashes are separately recorded; they are not the same as canonical JSON hashes.

## Checks completed

- Private re-derivation verifies original archive, sender-map and causal-event
  hashes, timestamps and past-only anchor agreement. It reproduces 3,024
  configurations and 3,024 scalar tables from the existing licensed originals.
- Every one of 92,484 geometry/timing table entries agrees with direct reachable
  mask reduction, independently of the optimized prefix-minimum reduction.
- Public replay enumerates 6,386,688 path appearances across configurations;
  these are repeated finite paths, not independent experimental trials.
- Independent scalar clocks/resource accounting verify all 3,024 maximizing
  witnesses. Complete independent scalar DFS agrees for 108 frozen queries:
  the first episode in each of six scenes, all nine models and both timings.
- 672 fitting-rule exclusion queries and 2,016 speed-nesting comparisons pass.
- All 15 new tests pass after publication of the local artifacts. Three
  artifact-dependent tests were deliberately skipped before batch generation.
  Geometry tests include wraparound, poles, containment, random actual masks,
  latency nesting and a non-vacuous static case with a positive lower gain.
- Full regressions: **435 tests plus 24 subtests on Windows; 431 plus 24 on
  Linux**. The four Torch tests run in the Windows environment only.
- Portable-model tests: five on each OS. Client-protocol tests: 11 assertions
  in Windows Node. Diagnostic values and PNG/SVG hashes verify on both OSs.
- The saved PNG was visually inspected for axis labels, legends and layout.

These are deterministic software/data checks, not independent confirmation of
the scientific model. Both environments use the same source data. No real-time
or physical experiment was performed for this audit. No scientific batch or
regression failure occurred. A harmless Windows font-cache warning during
rendering did not prevent figure production. A read-only attempt to inspect a
nonexistent `ci.yml` was corrected to the actual `tests.yml`; no workflow data
or experiment was affected.

## Reproduce

From the repository root, with NumPy and the existing project dependencies:

```console
python -m unittest temporal_viewport.test_core temporal_viewport.test_validation -v
python -m temporal_viewport.run --verify
python -m temporal_viewport.diagnose --verify
```

This public path needs no raw poses or video. The input tables are derived
artifacts; reproducing their source derivation additionally requires the
original licensed six trace archives and the unchanged local causal-event
cache used by the earlier feedback study:

```console
python -m temporal_viewport.prepare --verify
```

Generation commands refuse to overwrite existing outputs. Saved figures are
verified by hashes; cross-platform font rendering need not be byte-identical.
Remote CI status is separate from the completed local checks and should be
read from the workflow attached to the exact commit, not inferred here.
