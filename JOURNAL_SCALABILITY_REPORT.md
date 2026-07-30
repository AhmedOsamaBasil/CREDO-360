# TMM deterministic-action-cover scalability result

This report closes Experiment B in `JOURNAL_EXPERIMENT_PROTOCOL.md`. The
canonical campaign was executed on 29 July 2026 without changing the frozen
population sizes, seed count, decisions per seed, or 384-candidate bound.

## Execution identity

- Ubuntu 26.04 under WSL2, Linux 6.6.87.2;
- 11th Gen Intel Core i9-11900K at 3.50 GHz;
- Python 3.14.4 and NumPy 2.3.5;
- portable CPU/NumPy ensemble inference;
- `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, and
  `NUMEXPR_NUM_THREADS` fixed to one;
- model self-check performed before timing, with no measured controller
  decisions excluded as warm-up;
- peak process RSS: 84,115,456 bytes (80.2 MiB), measured with Linux
  `ru_maxrss`.

## Results

Each population size contains 30 deterministic state seeds and eight measured
decisions per seed.

| Users | Decisions | Median candidates | Median (ms) | p95 (ms) | p99 (ms) | Feasibility violations |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 240 | 384 | 77.07 | 101.18 | 111.35 | 0 |
| 10 | 240 | 384 | 174.83 | 208.78 | 222.67 | 0 |
| 20 | 240 | 384 | 307.94 | 348.89 | 383.72 | 0 |
| 30 | 240 | 384 | 438.35 | 504.06 | 540.39 | 0 |

The full bitrate Cartesian product is not materialized above five users.
Thirty-user p99 remains below the prespecified one-second segment-controller
reference while the candidate set stays bounded at 384 and every selected
allocation remains feasible.

## Evidence boundary

This is a controller-side computational benchmark, not an end-to-end network
latency or subjective-QoE result. Raw per-decision measurements, the aggregate
table, machine-readable metadata, and the generated figure are preserved in
`live_testbed/results/journal_scalability/`.
