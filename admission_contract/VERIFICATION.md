# Verification record

The method, protocol and 17 synthetic tests were published in `699bca5` before
the exposed batch. All primary sources remain unchanged after outcomes. The
independent ledger and concentration diagnostics are explicitly post-outcome;
they do not retune a controller or overwrite results.

Both Windows and Linux reproduce:

- **3,192 episode/method/timing rows**, including 168 unbounded-execution cases.
- **12,096** quality-difference checks against the sender envelopes (repeated
  recipient/donor occurrences, not 12,096 independent observations).
- **336** independent scalar certificate comparisons, including extrema and
  minimum witness cost; **168** exact prior fixed-contract oracle checks.
- **3,024** independently recomputed outcome, clock and byte ledgers; unbounded
  cases make no admission and are not simulated as fulfilled service.
- **152** prior measured segments checked against the declared execution
  allowance; this is a retrospective check, not a universal guarantee.

Canonical scientific hashes:

```text
Primary admission batch:
58f1f5eff944b22ce75fd3492dd3ec87eecf5ca2d3e89e676f4cf61d5e697ebb
Post-outcome diagnostics:
81a2277066689967d07eada87806ef117b7b8914a591d2cc52a271629a6420ff
```

All23 new tests pass on both operating systems. Full regression: Windows384
tests plus24 subtests; Linux380 tests plus24 subtests. Four Torch tests run on
Windows only. Portable-model5 tests pass on each OS, and11 JavaScript client
assertions pass on Windows. PNG/SVG figures were visually inspected and hashed.

Reproduction needs the repository's published scalar inputs and six existing
sender-map files, not a private pose cache or raw video. No GPU is needed.

```console
python -m unittest admission_contract.test_core admission_contract.test_validation -v
python -m admission_contract.run --verify
python -m admission_contract.diagnose --verify
```

The first command tests the mechanisms; the latter two fully replay public
results and check their source/input/figure bindings. A new batch command without
`--verify` refuses to overwrite an existing artifact. CI includes the same new
tests and replay checks. Local verification does not imply a pending remote CI
job has completed. No old frozen result, manuscript, acknowledgment or fresh
holdout was modified.
