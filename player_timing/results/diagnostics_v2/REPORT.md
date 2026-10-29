# Exposed matched-path timing results

Original parent credit and the secondary chunk account remain distinct. Six scenes,
28 reused identities; 168 exposed episodes, not 2,688 independent trials.

## Analytical replay

| Path | Unit | Buffered | Parent protected half /168 | Chunk protected half /168 | Recipient finish s |
|---|---:|---|---:|---:|---:|
| baseline | 2 | False | 0 | 0 | 41.062 |
| baseline | 2 | True | 0 | 0 | 42.832 |
| baseline | 10 | False | 0 | 0 | 44.201 |
| baseline | 10 | True | 0 | 0 | 44.201 |
| cost_greedy | 2 | False | 27 | 27 | 42.876 |
| cost_greedy | 2 | True | 27 | 27 | 43.934 |
| cost_greedy | 10 | False | 27 | 27 | 49.730 |
| cost_greedy | 10 | True | 27 | 27 | 49.730 |
| maxmin | 2 | False | 4 | 4 | 42.847 |
| maxmin | 2 | True | 4 | 4 | 43.934 |
| maxmin | 10 | False | 4 | 4 | 49.730 |
| maxmin | 10 | True | 4 | 4 | 49.730 |
| rolling_nash | 2 | False | 4 | 4 | 42.847 |
| rolling_nash | 2 | True | 4 | 4 | 43.934 |
| rolling_nash | 10 | False | 4 | 4 | 49.730 |
| rolling_nash | 10 | True | 4 | 4 | 49.730 |

## Browser measurements

Valid audited sessions: 74/74; failures remain in the raw artifacts.

| Path | Unit | Buffered | Sessions | Parent protected half | Chunk protected half | Recipient finish s |
|---|---:|---|---:|---:|---:|---:|
| cost_greedy | 2 | False | 6 | 1 | 1 | 43.203 |
| cost_greedy | 2 | True | 6 | 1 | 1 | 44.357 |
| cost_greedy | 10 | False | 6 | 1 | 1 | 49.823 |
| cost_greedy | 10 | True | 6 | 1 | 1 | 49.853 |
| maxmin | 2 | False | 6 | 0 | 0 | 43.194 |
| maxmin | 2 | True | 6 | 0 | 0 | 44.371 |
| maxmin | 10 | False | 6 | 0 | 0 | 49.833 |
| maxmin | 10 | True | 6 | 0 | 0 | 49.837 |
| rolling_nash | 2 | False | 6 | 0 | 0 | 43.207 |
| rolling_nash | 2 | True | 6 | 0 | 0 | 44.381 |
| rolling_nash | 10 | False | 6 | 0 | 0 | 49.835 |
| rolling_nash | 10 | True | 6 | 0 | 0 | 49.842 |

Recorded video callbacks: 156,655. Callback sequence gaps: 19,685. Missing final-tail witnesses: 0.
Summed per-file browser dropped-frame counters: 122. Callback gaps and these counters are different quantities, neither a physical pixel audit.
Controlled payload bytes served: 303,416,638. These are not physical link-capacity measurements.

## Controls

- late_recipient: original parent repayment 0.000%; recipient finish 82.239s; served 3874125 payload bytes.
- background: original parent repayment 34.470%; recipient finish 57.216s; served 9874125 payload bytes.

## Independent checks

{'analytical_ledgers': 5376, 'resource_ledgers': 2688, 'nonoverlapping_service_intervals': 131409, 'server_payload_identities': 1809, 'client_server_report_matches': 1808, 'measured_ledgers': 296}

The first-request offset from the browser run epoch is also retained. Realigning
the deadline changes parent credit in 0 sessions and half classification in 0 sessions.
The secondary chunk credit changes in 0 sessions and chunk half classification in 0 sessions.

No physical pixel/HMD measurement, subjective QoE, new controller, new holdout,
or general optimality for shorter-segment actions is established.
