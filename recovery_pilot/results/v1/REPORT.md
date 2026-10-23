# Recovery pilot v1 results

Exploratory engineering replay; not confirmatory or live validation.

Progression gate: **FAIL**. No post-test tuning was performed.

Joint quality/gain radius: 0.474135 objective-index units; calibration IDs: 9; test IDs: 9.
Held-out catalogue panels covered: 9/9.

## Candidate minus bounded-quality debt

Negative shortfall/stall differences favor the candidate; positive quality differences favor it.

| Scenario | Cumulative shortfall | Post-restoration shortfall | Stall s/user | Worst-user quality |
|---|---:|---:|---:|---:|
| capacity_only | 0.1263 | 0.0327 | 0.1572 | -0.0083 |
| known_ceiling | 0.1964 | -0.0085 | 0.0921 | -0.0016 |
| delayed_ceiling | 0.1560 | -0.0489 | 0.0438 | -0.0006 |
| prediction_shift | 0.1343 | 0.0064 | 0.0429 | -0.0090 |

Full per-seed results, descriptive paired intervals, calibration panels, action disagreements and compressed raw measurements accompany this report.

Recovery-event times are right-censored at 20 rounds; do not interpret capped waiting means as observed recovery for every user.

The finite-catalogue envelope assumes exchangeable grouped ID panels; it does not promise validity under the deliberately injected prediction shift or stale ceiling observation.

See PROTOCOL.md for the fixed design and metadata.json for code/data hashes. Hardware runtime fields are not injected into replay timing.
