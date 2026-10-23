# Objective shortfall-recovery pilot

This is a versioned, exploratory test of a candidate recovery mechanism, not
an assertion of novelty or successful performance. Read [PROTOCOL.md](PROTOCOL.md)
before interpreting results. The original manuscript has not been updated.

**v1 outcome: progression criterion failed.** Across 12 paired seeds in the
known-ceiling scenario, the candidate increased cumulative shortfall by 0.1964
index-rounds/user versus bounded-quality debt, with only a 0.0085 decrease in
post-restoration shortfall. Do not promote it as an improved controller.
[Full results](results/v1/REPORT.md) and
[interpretation](INTERPRETATION.md) retain the adverse results and uncertainty.

## Corrections

- Objective-quality training and calibration replace the old subjective-model
  residual transfer. No subjective ensemble is loaded by the pilot.
- A whole-source-ID-panel score simultaneously bounds quality error and
  ordered-action shortfall-gain error over a fixed known-content catalogue.
- Recovery credit uses a **direct** shortfall-gain bound and is capped by debt.
  It is not a difference of quality lower bounds. A zero credit is abstention,
  not a guarantee that the action cannot harm quality.
- Exact small-system allocation removes approximate-search confounding.
- Common-clock playback includes post-download waiting, censored transfers,
  and (in the live runner) controller/setup/logging time. Buffered media is no
  longer silently truncated. The pilot reports CPU runtime separately rather
  than injecting nondeterministic runtime into simulated time.
- Historical measurements are immutable. The legacy objective runner requires
  explicit acknowledgment of its target mismatch; live resume checks reject
  mixed clock versions and changed configurations.

## Reproduce

From the repository root, Python 3.12+ and NumPy are enough for the pilot:

```bash
python -m pip install numpy pytest
python -m pytest recovery_pilot -q
python -m recovery_pilot.run --output recovery_pilot/results/v1
python -m recovery_pilot.audit_results --results recovery_pilot/results/v1
```

The run refuses a nonempty output directory. To replicate already-published
results, choose a different empty directory and compare scientific fields;
measured runtime and platform metadata naturally differ. Raw rows are stored
as `measurements.csv.gz`, with all 12 paired seeds, all scenarios and all eight
controllers, including adverse outcomes. `seed_metrics.csv` and
`paired_diagnostics.csv` are human-readable summaries. `metadata.json` contains
input/source hashes and the predeclared engineering progression decision.

Run the published v1 campaign at software commit `26b744b` to reproduce the
recorded code hashes exactly. Later integrity-audit/documentation additions do
not change its policy or runner. The audit checks hashes before arithmetic.
Historical input CSVs may be checked out by Git as LF or CRLF. The original
raw SHA-256 values remain in metadata; `input_text_hashes.json` also binds them
to canonical-LF hashes. The audit permits **only** this recorded line-ending
change, never numerical/content edits. New result files are byte-preserved via
`.gitattributes`, and hashed source files are checked out as LF.

An additional two-client, three-round live Mininet clock smoke test is stored
in `results/live_clock_smoke_v1/`. It uses existing Big Buck Bunny DASH, NOT the
new recovery policy or immersive media; it verifies real completion-time
accounting only. A Linux replication of the first seed reproduced all 9,600
scientific rows exactly, excluding measured CPU runtime.

## Boundaries

This predictor is a training-trace average for known prerecorded content. The
pilot loops the six measured segments; it is not new long-duration footage,
independent repeated HMD subjects, live networking, or subjective QoE validation.
Representation ceilings and predictor shifts are explicit synthetic stresses.
The direct-gain envelope relies on exchangeable source-ID panels and the fixed
catalogue, not arbitrary-shift or conditional-on-user guarantees. Nine test
panels cannot establish precise population coverage. Baselines here are exact,
controlled engineering comparisons, not reproductions of published MARL systems.

Prior components include virtual-queue network control and conformal prediction;
combining them is not by itself novelty. Relevant foundations are
[Neely's stochastic network optimization](https://ee.usc.edu/stochastic-nets/docs/non-convex-ita2010.pdf)
and [Gibbs and Candes' adaptive conformal inference](https://proceedings.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html).
This pilot uses a fixed split envelope, **not** that adaptive algorithm.

The principal comparison is against bounded-quality debt, with matched
uncertified and memoryless ablations. If the gate fails, retain that result and
do not promote the candidate or silently retune against these test traces.
