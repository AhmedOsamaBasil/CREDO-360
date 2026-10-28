# Verification record

Protocol and primary implementation: `533a402`, published before the batch.
Primary method files were not changed after outcomes. The fixed-plan worst-case
diagnostic is explicitly post-outcome and leaves all primary artifacts unchanged.

Both Windows and Linux reproduce:

- **216** distinct geometric masks and216 valid orientation witnesses, matching
  independent complete integer-grid enumeration.
- **4,320** extrema checked against independent scalar reductions of466,560
  mask/rung/second weighted values over the six sender maps.
- **12,096** observed quality-difference containment checks. These include
  repeated recipient/donor occurrences, not independent samples.
- **336** independent scalar admission-certificate checks and336 unchanged
  future-known oracle comparisons.
- **3,024** independent score/resource/clock ledgers and1,344 exactly retained
  point-control rows, within the3,192-row full batch.
- **168** post-outcome fixed-plan upper-bound diagnostics with explicitly
  synthetic extremal-mask sequences; no new participant observations.

Canonical scientific hashes:

```text
Primary geometric admission:
4bc047c4030b43510e883661c6a2670e74a2dfbcd4a14cbc2d31e40bf97903a5
Post-outcome diagnostics:
6d3712060f420ce0f6a6f77e4e71858561c002904bf7898fe6e39d598c707aec
```

All18 new tests pass on both operating systems. Full regression: Windows402
tests plus24 subtests; Linux398 plus24 subtests. Four Torch tests run only on
Windows. Portable-model5 tests pass on both systems;11 JavaScript feedback
assertions pass on Windows. The PNG/SVG figure was visually inspected and hashed.

```console
python -m unittest geometric_admission.test_geometry geometric_admission.test_validation -v
python -m geometric_admission.run --verify
python -m geometric_admission.diagnose --verify
```

Public scalar evidence and the already published sender maps suffice; private
poses, raw videos and a GPU are not required. A new run without `--verify`
refuses to overwrite results. CI runs the new tests and complete deterministic
replays when artifacts are present. Local verification is not a claim that a
pending remote job has completed.

No old frozen methods/results, manuscript, acknowledgment or fresh holdout were
changed. Valid software and tighter bounds do not establish positive-admission
usefulness, a novel optimal controller or an unconditional recovery guarantee.
