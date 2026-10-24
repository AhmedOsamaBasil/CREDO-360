# Selected-transfer live pilot: descriptive results

One fixed user pair per exposed scene. Six paired scenes per nominal policy; six candidate-only stress episodes.
Not independent efficacy confirmation; the complete exposed replay fails its fixed practical gate.

| Policy / rate | Half / episodes | Unpaid | Worst quality | Startup stall s | Additional stall s | Deadline misses / rounds | Maximum receipt latency s |
|---|---:|---:|---:|---:|---:|---:|---:|
| Causal KNN / 1500 kbit/s | 3/6 | 0.369675 | 4.0038 | 4.5159 | 1.5153 | 0/24 | 8.6752 |
| Greedy / 1500 kbit/s | 3/6 | 0.382027 | 4.0039 | 5.3849 | 0.6245 | 0/24 | 8.6021 |
| Rolling Nash / 1500 kbit/s | 3/6 | 0.382027 | 4.0039 | 5.4056 | 0.6090 | 0/24 | 8.5903 |
| Rolling max-min / 1500 kbit/s | 3/6 | 0.382027 | 4.0039 | 5.3641 | 0.6604 | 0/24 | 8.5901 |
| Causal KNN / 750 kbit/s | 3/6 | 0.382708 | 4.0032 | 8.6899 | 12.1850 | 12/24 | 17.0660 |

Nominal live versus fluid-model action disagreements: 0/96.
Timing can change feedback availability and therefore decisions; a difference is not automatically a replay error.

All startup waiting is counted. Final media drain is analytical, not decoded/displayed.
Quality and debt feedback are reference-assisted retrospective values. No safe actual-quality floor is established.
Each plotted point is a recorded round, not an independent experimental subject. No inferential confidence intervals are claimed.
