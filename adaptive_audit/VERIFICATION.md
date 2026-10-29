# Analytical audit verification

Frozen protocol/method: `556d3e9`, published before the exposed batch.
Primary code was not edited after its outcomes. `render.py` is a separate
post-outcome presentation step, with its own source/result/figure hashes.

Both Windows and WSL Linux reproduce the complete audit with scientific SHA256:

```text
6d2c7bb49afe5737bd8222684d795cd04d8bd1ac62c87f8e4259c60e02dfa823
```

- 336 episode/timing comparisons: 168 exposed episodes, two timing allowances.
- Complete 216-mask family and orientation witnesses checked.
- 96 action-conditioned ten-mask responses, each scored for all six rungs:
  576 independent scalar native-MSE checks.
- 24 Bellman versus complete-path comparisons over 50,688 path appearances
  (two reward tables and two timing modes across six scenes, not independent
  observed trials).
- 168 exact parity checks against the published generous fixed-plan bound.
- 36 deterministic waiting checks and all deadline/resource witness ledgers.
- 256 rectangular and 512 coupled finite games checked by independent
  exhaustive causal-policy enumeration, plus four named information examples.
- Past-only debt projection excludes future observed qualities and poses.

All 18 new tests pass on both platforms. Full regression: Windows 420 tests
plus 24 subtests; Linux 416 plus 24 subtests. Four Torch tests run on Windows
only. Portable-model and feedback-client checks are separate from these counts.
Portable-model five tests pass on both systems; the eleven JavaScript client
assertions pass on Windows. The unchanged geometric primary and diagnostic
artifacts also replay successfully in WSL with their original scientific hashes.
PNG/SVG presentation files were hash-checked on both systems; the PNG was
visually inspected. A nonfatal Windows font-cache permission warning occurred
while rendering, but the figure and its provenance verification completed.

The first unprivileged WSL availability check returned access denied; the
approved run in the existing environment succeeded. No scientific batch or
unit test failed. Before publication, three artifact-dependent tests were
explicitly skipped because the results did not yet exist; after the batch all
18 tests ran and passed. No outcome was repaired or threshold retuned.

```console
python -m unittest adaptive_audit.test_core adaptive_audit.test_validation -v
python -m adaptive_audit.run --verify
python -m adaptive_audit.render --verify
```

No new physical/network/player experiment, private pose access or future
participant label loading was performed. The input predecessor archive contains
historical results, but only identifiers and past debt are projected into the
new bound; prior bound values are read solely for consistency checks. Tests
mutate future fields and confirm they do not enter that projection. Synthetic
responses are never represented as recorded human trajectories.
