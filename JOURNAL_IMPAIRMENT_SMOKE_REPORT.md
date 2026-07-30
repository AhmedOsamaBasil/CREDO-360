# TMM non-actionable-impairment engineering smoke test

Run on 29 July 2026 before the powered journal campaign. This is a one-seed
engineering validation and must not be reported as confirmatory evidence.

## Purpose

The earlier live comparison used an absolute calibrated-floor debt term. When
every candidate's lower bound exceeds the minimum-action lower bound, that
term and CREDO-360's opportunity term differ only by an action-independent
constant. The resulting null comparison cannot identify the opportunity gate.

The journal harness therefore adds a genuinely ungated resource-debt
comparator:

\[
J_{\mathrm{resource}}(\mathbf a)=
\sum_i\log L_i(\mathbf a)
+\lambda\sum_i\frac{d_i}{1+\bar d}\frac{a_i}{b_{\max}}
-\eta S(\mathbf a,\mathbf a_{t-1}).
\]

It can spend representation bitrate on a deprived user even when that
resource has no calibrated QoE opportunity.

## Smoke-test condition

- seed 20260728;
- five Mininet clients and the shared live DASH bottleneck;
- one warm-up plus one analysed transfer epoch;
- client selected by `seed mod users` capped at 0.18 Mb/s with 180 ms access
  delay;
- resource-debt comparator and CREDO-360 receive the same capacity and segment
  schedule.

## Engineering observation

In the single analysed epoch:

| Controller | Impaired allocation | Measured throughput | Excess above ceiling | Impaired stall |
|---|---:|---:|---:|---:|
| Resource debt, ungated | 0.987061 Mb/s | 0.170201 Mb/s | 0.807061 Mb/s | 33.818 s |
| CREDO-360 | 0.252988 Mb/s | 0.165632 Mb/s | 0.072988 Mb/s | 2.627 s |

The harness therefore creates a materially active service ceiling and the
comparators make different decisions. No effectiveness or statistical claim
is made from this one seed. The powered campaign remains 30 paired seeds per
condition under `JOURNAL_EXPERIMENT_PROTOCOL.md`.
