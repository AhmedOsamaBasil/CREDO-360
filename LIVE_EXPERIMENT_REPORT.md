# Live Mininet integration report

> This document records the initial eight-epoch integration run. The completed
> 30-seed confirmatory campaign supersedes it for efficacy claims; see
> `LIVE_POWERED_EXPERIMENT_REPORT.md`. The initial run remains preserved as a
> transparent engineering milestone.

## Purpose

This experiment moves CREDO-360 from trace replay to concurrent, measured HTTP
segment delivery. It is an integration and mechanism-activation test, not a
confirmatory human-QoE study.

## Validated testbed

- Ubuntu 26.04 LTS under WSL2, kernel 6.6.87.2.
- Mininet 2.3.0 with Open vSwitch 3.7.1; `pingall` passed with 0% loss.
- Five isolated clients and one HTTP server on a single OVS bridge.
- One shaped server egress, varied over 1.3-4.2 Mb/s, is the shared bottleneck.
- Real 10-second Big Buck Bunny `.m4s` segments from the author's repository.
- Concurrent curl transfers with bytes, total time, TTFB, and goodput logged.
- The five-member PyTorch ensemble was trained on the RTX 3090 and exported to
  a framework-neutral JSON artifact.
- NumPy inference in WSL matched PyTorch reference predictions with maximum
  absolute error `2.40e-7`, below the prespecified `2e-5` tolerance.

Artifact SHA-256:
`f28f3320cee852467a2ec7b829c273a1c5779e6ca350990b65c34688dd07a2dc`.

## Protocol

The paired experiment used conformal Nash and opportunity-aware calibrated QoE
debt over eight identical capacity epochs and five clients (40 segment
observations per controller). The live operational-QoE floor was fixed at 4.0.
This differs from the replay floor because the live predicted-QoE support is
substantially higher. The first live run at 1.5 is retained as a rejected
configuration: its debt queue remained zero, so it could not test the proposed
mechanism.

Operational QoE is the published-data model estimate based on actual transfer
features with explicit stall and switching penalties. It is not a new
subjective MOS observation.

## Results

| Metric | Conformal Nash | Risk debt | Delta |
|---|---:|---:|---:|
| Mean operational QoE | 4.1364 | 4.0419 | -0.0946 |
| Worst-user mean operational QoE | 3.5078 | 3.7847 | +0.2769 |
| Jain fairness of user means | 0.9892 | 0.9983 | +0.0091 |
| Service-violation rate | 0.300 | 0.350 | +0.050 |
| Mean service shortfall | 0.2636 | 0.3280 | +0.0644 |
| Total stall time (s) | 22.2655 | 22.1943 | -0.0712 |
| Representation-switch rate | 0.725 | 0.675 | -0.050 |

Every joint action respected the shared capacity; the closest allocation
remained `0.010827` Mb/s below the limit. Risk debt activated and changed later
allocations. In this small run it reproduced the central trade-off seen in
replay: improved inter-user equalization and slightly less stalling/switching,
but lower mean QoE and worse absolute service compliance.

## What can and cannot be claimed

The run validates:

1. real concurrent transfers through an enforced shared bottleneck;
2. portable execution of the learned QoE ensemble;
3. online activation of the calibrated opportunity/debt allocation rule; and
4. complete segment-level observability and capacity feasibility.

It does not establish statistical efficacy, conformal coverage under live
labels, generalization to a headset/player, or subjective QoE improvement.
The subsequent powered campaign adds 30 paired seeds, counterbalanced
controller order, five baselines, a frozen analysis protocol, and
multiplicity-corrected inference. Independent content and human or
independently validated live QoE labels remain necessary.
