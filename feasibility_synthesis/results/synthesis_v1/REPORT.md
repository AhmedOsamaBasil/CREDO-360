# Feasibility evidence: what each result can establish

Post-outcome reconciliation of frozen artifacts; no new experiment, optimization or significance test.

## Primary conditional contract: 0.5-second execution allowance

| Scene | Episodes | Optimistic infeasible | Trace feasible, not guaranteed | Trace infeasible without optimistic rejection |
|---|---:|---:|---:|---:|
| all | 168 | 134 | 27 | 7 |
| BuskingUnderpass05 | 28 | 28 | 0 | 0 |
| Cheerleading01 | 28 | 28 | 0 | 0 |
| ConferenceParticipant02 | 28 | 28 | 0 | 0 |
| ParkFountains01 | 28 | 22 | 0 | 6 |
| River01 | 28 | 0 | 27 | 1 |
| Train01 | 28 | 28 | 0 | 0 |

The three columns partition episodes within one timing condition. They are NOT three independent experiments.
All trace-feasible cases still fail the universal-policy promise under unrestricted future sampled masks.
Zero temporal lower certificates are not an impossibility result for coupled motion.

## Metric sensitivity (separate historical nominal-duration contract)

| Metric | Clock | Known-trace half-feasible /168 |
|---|---|---:|
| index | media | 96 |
| index | deadline | 96 |
| fine_index | media | 96 |
| fine_index | deadline | 96 |
| psnr_db | media | 168 |
| psnr_db | deadline | 168 |
| negative_mse | media | 28 |
| negative_mse | deadline | 27 |

These metric cells are not pooled with the fixed actual-duration contract.

## Claim qualifiers

### known_trace

Known-trace feasibility and point-prediction success do not establish a universal admission promise.

Required qualifiers: finite_catalogue, future_known, not_online_admission.

### optimistic_rejection

An optimistic upper bound below the target rules out that finite-contract promise even before selecting a scheduler.

Required qualifiers: finite_catalogue, fixed_contract, floor_relaxed_upper.

### universal_policy_limit

Per-policy adversarial sequences bound deterministic causal whole-segment policies under temporally unrestricted sampled viewports.

Required qualifiers: deterministic, not_expected_randomized, not_smooth_human_motion, per_policy_counterexample, unrestricted_sampled_futures, whole_segment_commitment.

### failed_temporal_certificate

Zero entry-cone certificates do not prove coupled-motion infeasibility; empirical source-speed consistency is not deployment coverage.

Required qualifiers: empirical_speed_not_guarantee, not_coupled_impossibility, source_clock_only, sufficient_lower_only.

### paced_measurement

The pacing audit measures decoder and software-event timing for scripted arrivals, not physical display or network delivery.

Required qualifiers: decode_and_software_pacing, not_human_qoe, not_network_measurement, not_pixel_rendering, scripted_arrivals.

## Measurement boundary

19 existing paced sessions and 45594 frame checks; measured decode/hash and software pacing; scripted arrivals; not rendering/HMD/network.
The 19 sessions and 336 timing rows are not new subjects or independent replications.
All original scientific artifacts remain unchanged. This report validates joins and scopes, not every original optimizer.
