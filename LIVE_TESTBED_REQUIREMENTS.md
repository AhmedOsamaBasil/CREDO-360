# Live testbed status and next requirements

## Completed on this machine

- WSL2 Ubuntu 26.04 LTS with RTX 3090 visibility.
- Mininet 2.3.0, Open vSwitch 3.7.1, FFmpeg 8.0.1, iperf3, and NumPy.
- Five concurrent DASH clients sharing one shaped server-egress bottleneck.
- Real `.m4s` delivery with segment-level transport, buffer, QoE, debt, action,
  stall, and switching logs.
- Portable learned-ensemble inference verified against PyTorch.
- Paired eight-epoch mechanism-activation run.

See `LIVE_EXPERIMENT_REPORT.md` and `live_testbed/`.

## Still required for publication-grade evidence

1. At least 30 randomized paired capacity traces with controller order
   counterbalanced.
2. Proportional-fair, uncertainty-Nash, and conventional debt/virtual-queue
   ablations in the live harness.
3. Independent video/content and network-shift scenarios.
4. A real DASH/360 player or headset exposing viewport/tile selection, decoded
   dropped frames, and motion-to-photon latency.
5. Human ratings or an independently validated live outcome label; model
   estimates alone cannot validate conformal coverage.
6. Preregistered primary metrics and paired inference.
7. Optional P4/BMv2 deployment after the controller behavior is stable.

Docker, P4, and GPAC are not needed for the completed Mininet stage and were
not installed.
