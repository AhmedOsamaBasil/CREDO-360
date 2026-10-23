# Longer-horizon objective-quality recovery

Exploratory redesign following the explicitly failed v1 and v2 recovery pilots.
Developed on exposed v2 data; the selected configuration and fresh-content
protocol were published before downloading the v3 inputs. See
[DEVELOPMENT.md](DEVELOPMENT.md), [PROTOCOL.md](PROTOCOL.md), and the complete
[development search](results/development_v1/selection.csv). Do not infer a
successful holdout from the successful development screen.

## Technical distinction and limits

The old instantaneous feasible lower target almost always left the recovery
queue inactive. This version instead forms a six-segment time-average contract
from sender-known representation quality and sizes. The contract LP mixes
**joint** resource-feasible actions; it does not combine independent user maxima
that cannot be served together. Every support action fits the bytes selected by
a common stateless bounded-Nash allocation for that context. The capped max-min
contract is feasible in expectation under its forecast, not a guaranteed
integer schedule or a lower bound on actual viewport quality.

For signed residual e(i,t)=target(i,t)-observed_quality(i,t), the controller state
is D(i,t)=max(0, sum of e(i,s) over the preceding H decisions). Positive delivery
surplus can offset earlier shortfall. Sliding-window expiry is separately
recorded: disappearance of old debt must not be called delivered recovery.
The selected24-round memory is shorter than the40-round impairment. Pre-impairment
residuals therefore expire before restoration, and the feasibility-aware target
is itself reduced during a known ceiling. This is recent-window service tracking,
not an entitlement to repay every fixed-target loss accumulated during an outage.
Exact joint action selection maximizes bounded Nash utility minus the squared
predicted terminal positive deficit, scaled by strength/(2H).

All policies share the current stateless Nash byte cap, so recovery cannot spend
more bytes than its Nash reference at that decision. This does not promise
unchanged per-user stall or equal cumulative bytes. The strongest memoryless
control multiplies the latest positive residual by H; it matches deficit scale,
so accumulating a larger number alone is not evidence of memory's value. An
unscaled control and a fixed-target-four window controller are also retained.
There is no switching penalty in any of these five policies.

This is finite-window feedback with a multi-period reference, **not** a full
receding-horizon optimal control solver. It uses established fair-allocation,
queueing and finite-memory ideas. A working implementation or a passed pilot
would not itself establish literature novelty.

## Reproduce

Use Python3.12+ with NumPy, SciPy, Matplotlib and pytest. No GPU is required to
replay the public derived data. Raw preparation additionally needs ffmpeg with
H264 NVENC, an NVIDIA GPU, public-source downloads and sufficient disk space.

```bash
python -m pytest horizon_recovery -q
python -m horizon_recovery.prepare
python -m horizon_recovery.run --output work/horizon-replication
python -m horizon_recovery.analyze --output work/horizon-replication
python -m horizon_recovery.audit --output work/horizon-replication --save
```

Skip preparation if `data/v3/` is present. Outputs are immutable: choose a new
empty directory for a replay. To verify the published run directly:

```bash
python -m horizon_recovery.audit
```

To recreate all development configurations, run `python -m horizon_recovery.develop`
in a fresh checkout with the archived `results/development_v1/` moved aside to a
separate safe location. The script refuses to replace it. It accesses only the
exposed v2 dataset. Do not rerun development against v3 after inspecting its
outcomes; v3 must then be treated as exposed for future redesigns.

## Artifact map

| File | Purpose |
|---|---|
| `core.py` | Joint-mixture LP, signed-window ledger, exact action selection |
| `run.py` | Causal plan, fluid transport, corrected clock, paired summaries |
| `develop.py` | All six predeclared configurations on exposed data |
| `evaluate.py` | Frozen primary Nash and scale-matched-memoryless screen |
| `prepare.py`, `manifest.json` | Source provenance and separate calibration/test labels |
| `audit.py` | Source/data hashes, LP witnesses, complete decision/ledger/clock replay |
| `analyze.py` | All paired/content/expiry diagnostics and scientific figures |
| `test_core.py` | Synthetic exactness, causal-input and mechanism checks |

The new scenes are BuskingUnderpass05, Cheerleading01, ConferenceParticipant02.
Only their first60 seconds are used; six10-second segments repeat for120 rounds.
The19 held-out source IDs come from the same28-person dataset pool as earlier
work, with different trace sequences. Nine panels calibrate the sender predictor.
This is neither a new-human study nor independent-dataset validation.

Media are compressed8K references; the delivery representations are1920x960.
Viewport scores use a960x480,1fps tile-center approximation, not exact perspective
rendering or MOS. Network/impairments are simulated. Runtime is measured but not
injected into playback. No new live/headset experiment is claimed. Public
derived measurements do not redistribute source media or full raw HMD archives.

Sources and original terms: [QoEVAVE scenes](https://qoevave.github.io/database/docs/Scenes),
[public saliency traces](https://qoevave.github.io/database/docs/Saliency),
[QoMEX2022 dataset paper](https://doi.org/10.1109/QoMEX55416.2022.9900893),
[QoMEX2023 saliency paper](https://doi.org/10.1109/QoMEX58391.2023.10178588).
