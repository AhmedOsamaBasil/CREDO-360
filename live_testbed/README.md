# Live Mininet DASH testbed

This stage validates that the controller can operate on measured transfers, not
only replayed bandwidth traces. Five isolated Mininet clients concurrently fetch
real 10-second Big Buck Bunny `.m4s` segments through one Open vSwitch. A token
bucket on the server-to-switch interface creates a shared, time-varying
bottleneck.

Training remains in Windows/PyTorch so the RTX 3090 is used. The learned
ensemble is exported to JSON with reference predictions; WSL loads the exact
dense-layer weights with NumPy and rejects the artifact if its predictions
differ by more than `2e-5`.

The accepted integration configuration uses `--target-qoe 4.0`. The earlier
1.5-floor run is preserved under `results/live_run_floor15_rejected/` because
its debt queue never activated.

## Powered paired campaign

The publication campaign is preserved in `results/live_campaign_30seed/`.
It contains 30 complete paired seeds, six controllers, five clients, three
capacity regimes, counterbalanced controller order, and 8,100 measured rows.
The analysis plan was frozen in `POWERED_EXPERIMENT_PROTOCOL.md`.

Recreate its statistics and figures with:

```bash
python live_testbed/analyze_live.py \
  live_testbed/results/live_campaign_30seed/live_measurements.csv \
  --output live_testbed/results/live_campaign_30seed
```

See `../LIVE_POWERED_EXPERIMENT_REPORT.md` for the confirmatory results and
the interpretation boundary. The key negative result is retained: opportunity
gating was active for 99.3--100% of users, so this capacity-only campaign
cannot establish a gate-specific benefit over ungated debt.

## Reproduce

From the repository root. Export the model on the CUDA host:

```bash
python live_testbed/export_portable_model.py
```

Run the network experiment as root inside Linux/WSL:

```bash
sudo python3 live_testbed/run_mininet_experiment.py \
  --model live_testbed/artifacts/qoe_ensemble.json \
  --media-root /path/to/dash/media \
  --output live_testbed/results/live_run

python live_testbed/analyze_live.py \
  live_testbed/results/live_run/live_measurements.csv
```

The repository intentionally does not redistribute third-party media. Supply a
legal DASH corpus through `--media-root`.

## Interpretation boundary

`operational_qoe` is the published-data model estimate computed from actual
download time, throughput, latency, buffer, bitrate, and switching, with
explicit stall/switch penalties. It is not a new human subjective MOS. This
stage validates system mechanics and produces measurements for a later
human-in-the-loop experiment; it does not establish subjective-QoE efficacy.
