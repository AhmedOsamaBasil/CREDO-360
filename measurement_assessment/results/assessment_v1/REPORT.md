# Frozen-evidence synthesis

Post-hoc descriptive aggregation; no new simulation or statistical test.

## Matched prefix-playback comparison (simulation)

| Policy | Half / episodes | Mean unpaid | Worst quality | Stall s |
|---|---:|---:|---:|---:|
| prefix_cost_greedy@0.08s | 90/168 | 0.369185 | 3.997177 | 6.978108 |
| completed_mpc@0.08s | 92/168 | 0.380411 | 3.998055 | 6.969765 |
| prefix_mpc@0.08s | 92/168 | 0.375974 | 3.998658 | 6.968974 |
| wait_mpc@0.08s | 92/168 | 0.375430 | 3.998658 | 16.220007 |

The frozen progression screen remains FAILED. Lower unpaid is better.
Half-repayment is the declared accounting target, not a perceptual threshold.

## Evidence boundaries

- 168 reused directed episodes, six scenes, 28 participant identifiers; 1,512 policy runs are not independent subjects.
- Relative encoded-payload frontiers and fixed actual-file-cap bounds are different contracts.
- TCP receipts and completed-feedback loopback are measurements; incremental feedback/playback is simulated.
- Frozen inputs are bound by canonical decoded-JSON hashes in summary.json.
- This verifier checks extraction and aggregation, not every original optimizer; each source retains its own replay/audit.
- See ../../README.md, ../../RELATED_WORK.md and ../../VALIDATION_PLAN.md for the assessment.
