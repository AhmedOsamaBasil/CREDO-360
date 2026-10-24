# Remaining opportunity and feedback audit

Exposed data only. Future-known bounds do not certify a causal controller.
The original action-disagreement summary has a tuple/list comparison bug; corrected counts below use raw actions.

| Benchmark | Half / 168 | Mean unpaid | Gap over saved cost-greedy |
|---|---:|---:|---:|
| structural | 96 | 0.344994 | 0.024146 |
| strict | 96 | 0.344994 | 0.024146 |
| quality_guard | 95 | 0.355346 | 0.013794 |
| exact_current_greedy | 90 | 0.369137 | 0.000002 |

| Feedback-integrated policy | Half / 168 | Mean unpaid | Worst quality | Changed actions / 672 |
|---|---:|---:|---:|---:|
| knn_recovery | 90 | 0.371245 | 3.9971 | 0 |
| greedy_recovery | 90 | 0.370941 | 4.0052 | 0 |
| cost_greedy | 90 | 0.369140 | 3.9972 | 0 |
| rolling_nash | 89 | 0.393596 | 4.0231 | 0 |
| rolling_maxmin | 90 | 0.376229 | 4.0211 | 0 |
| persistence_mpc | 90 | 0.371854 | 3.9969 | 0 |
| unconditional_mpc | 90 | 0.373381 | 3.9966 | 0 |

Practical screen passed: **False**.

1008 actual HTTP messages; 6048 reconstructed quality values; 5968 exactly match the saved rounded objective index.
Same-metric difference: mean 0.000608216 dB, maximum 0.202213 dB.
Client payload 141120 bytes total (140/message); response bodies 429340 bytes. HTTP/TCP/TLS overhead is not included.
Loopback roundtrip median/max: 14.977/28.583 ms; server reconstruction 0.572/1.814 ms.
Sender maps: 409700 compressed bytes; 622080 raw float32 bytes across six scenes.

These are reference-assisted metric reconstruction checks, not perceptual validation or WAN/HMD performance.
The controller replay retains the nominal ten-second model and 50ms control allowance, not measured end-to-end feedback timing.
