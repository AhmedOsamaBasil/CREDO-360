# Feasibility-aware recovery pilot

A separate, versioned experiment following the failed
[v1 recovery pilot](../recovery_pilot/INTERPRETATION.md). The new mechanism uses
a jointly forecast-feasible quality reference to prevent recovery-queue windup
from persistent unattainable demand. The primary comparator changes only the
queue target; allocation objectives and information are matched.

Read [PROTOCOL.md](PROTOCOL.md) for equations, fixed settings, freshness,
calibration assumptions, metrics and the predeclared progression screen.
The [method notes](METHOD_NOTES.md) derive the feasible-witness and queue
properties, and distinguish them from claims that require experimental evidence.
Protocol/core commit `0bbdaa3` preceded new source downloads; campaign commit
`2d8a72d` preceded held-out evaluation. No post-outcome parameter search is used.

## What is and is not held out

ParkFountains01, River01 and Train01 were not in the earlier six-scene campaign.
Each contributes new HMD trace sequences and new measured encoding outcomes.
Nine source-ID panels calibrate the deterministic full-sphere sender predictor;
nineteen disjoint panels evaluate it. IDs are held consistently across scenes.
This is **content/sequence holdout within QoEVAVE**, not an independent dataset,
new human participants, or a subjective-quality study. Participant IDs overlap
earlier work. The source labels are used as simulation outcomes, never as
decision-time look-ahead.

The source videos are 8K, but this experiment encodes 1920x960 H.264 and measures
960x480 luma at 1 fps. It uses a declared tile-center viewport approximation,
not a full-resolution perspective viewport renderer. Six measured 10-second
segments repeat over a 90-round control session. Transport/ceiling impairments
are synthetic; neither deployment nor genuinely long original video is implied.
The downloadable 25-Mbps source itself is compressed; distortion is measured
relative to that distributed reference, not a lossless camera master.

## Reproduce from published derived measurements

Use Python 3.12+ with NumPy, pytest and Matplotlib (figures only), from the
repository root. No GPU or third-party source downloads are needed to replay
the published derived measurements.

```sh
python -m pytest feasibility_recovery -q
python -m feasibility_recovery.run --output work/feasibility-reproduction
python -m feasibility_recovery.audit --output work/feasibility-reproduction
python -m feasibility_recovery.analyze --output work/feasibility-reproduction
```

The full run has 20 paired seeds, four scenarios, six policies, five clients
and 90 rounds: 216,000 user-round records. All scientific fields should repeat;
measured decision runtimes and consequently compressed-file hashes need not.
Outputs are exclusive: choose a new directory rather than overwrite old runs.
The audit recomputes every allocation and scientific row, reference witnesses,
quality/debt feedback, time conservation, summaries, paired intervals and screen.

`data/v2/` contains separate calibration/test objective-quality tables, sender
predictor values, measured video-packet bytes, the source-ID split, source asset
hashes and preparation metadata. `results/v2/` contains raw compressed records,
per-seed summaries, all matched contrasts, panel coverage and a frozen report.
The analysis additionally reports action agreement with bounded Nash, zero
debt, floor relaxation and content-wise effects; these are mechanism diagnostics,
not substituted primary outcomes. See `INTERPRETATION.md` for the actual finding.

## Recreate the measurements

Requires ffmpeg/ffprobe with H.264 NVENC, an NVIDIA GPU and source-dataset access:

```sh
python -m feasibility_recovery.prepare --output work/fresh-derived-data
python -m feasibility_recovery.run --data work/fresh-derived-data --output work/fresh-replay
```

Source files remain under ignored `.external/feasibility_v2/`; media and HMD
archives are not redistributed here. Rerunning encodes with different hardware,
drivers or ffmpeg can change bytes/quality: this is a new preparation, not an
exact copy of frozen measurements. Hashes and runtime versions make that visible.

## Scope and attribution

The quality envelope is a finite-catalogue panel-level bound under an
exchangeability assumption. It is not conditional validity, a guarantee under
injected shift, a bound on differences of lower bounds, or a user-population
simultaneous guarantee. Bootstrap seed intervals condition on three scenes.
Lower internal debt cannot establish efficacy: fixed target-four shortfall,
stall and delivered quality remain the external outcomes. Exact enumeration
supports the five-user pilot, not a scalability claim. Exact score/byte ties
use enumeration order, so identity-neutrality in tied cases is not guaranteed.

Anti-windup, virtual queues and fair allocation are established concepts. A
working implementation or favorable pilot would not establish publication-level
novelty by itself. The earlier negative study remains part of the evidence.

Dataset sources and required scholarly citations:

- [QoEVAVE scenes and original downloads](https://qoevave.github.io/database/docs/Scenes).
  T. Robotham et al., “Audiovisual Database with 360° Video and Higher-Order
  Ambisonics Audio for Perception, Cognition, Behavior, and QoE Evaluation
  Research,” QoMEX 2022. [DOI](https://doi.org/10.1109/QoMEX55416.2022.9900893).
- [QoEVAVE saliency and HMD traces](https://qoevave.github.io/database/docs/Saliency).
  A. Singla et al., “Saliency of Omnidirectional Videos with Different Audio
  Presentations: Analyses and Dataset,” QoMEX 2023.
  [DOI](https://doi.org/10.1109/QoMEX58391.2023.10178588).

Consult original source terms before acquiring or redistributing third-party
assets. The repository license does not relicense those assets.
