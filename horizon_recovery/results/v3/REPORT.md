# Fresh-content window-recovery pilot

Frozen progression screen: **FAIL**.

All deltas are window recovery minus baseline. Intervals are paired-seed bootstrap diagnostics conditional on the fixed content/participant pool, not human-population validation.

## Known-ceiling contrasts

| Baseline | Metric | Mean delta | Conditional 95% interval |
|---|---|---:|---|
| nash | worst_user_quality | -0.000315 | [-0.001711, +0.001090] |
| nash | post_restoration_shortfall | -0.054857 | [-0.082227, -0.032538] |
| nash | cumulative_shortfall | -0.105389 | [-0.159407, -0.061261] |
| nash | stall_s_per_user | -0.148172 | [-0.420571, -0.006316] |
| nash | mean_quality | -0.000204 | [-0.000284, -0.000130] |
| nash | impaired_restoration_shortfall | -0.054455 | [-0.109953, -0.012921] |
| nash | switch_frequency | -0.001583 | [-0.002669, -0.000500] |
| memoryless_scaled | worst_user_quality | -0.007020 | [-0.012895, -0.001357] |
| memoryless_scaled | post_restoration_shortfall | -0.009745 | [-0.021625, +0.000128] |
| memoryless_scaled | cumulative_shortfall | -0.009929 | [-0.025107, +0.000305] |
| memoryless_scaled | stall_s_per_user | +0.373289 | [+0.071234, +0.872543] |
| memoryless_scaled | mean_quality | +0.000950 | [+0.000192, +0.001790] |
| memoryless_scaled | impaired_restoration_shortfall | -0.017851 | [-0.119544, +0.065993] |
| memoryless_scaled | switch_frequency | -0.007167 | [-0.010750, -0.003667] |

## Every frozen check

- PASS: all_20_paired_seeds
- FAIL: active_state_above_5_percent
- FAIL: nash_worst_quality_ci_above_zero
- PASS: nash_post_restoration_shortfall_reduced
- PASS: nash_impaired_restoration_shortfall_reduced
- PASS: nash_mean_quality_guard
- PASS: nash_fixed_shortfall_guard
- PASS: nash_stall_guard
- FAIL: nash_action_disagreement_above_1_percent
- FAIL: memoryless_scaled_worst_quality_ci_above_zero
- PASS: memoryless_scaled_post_restoration_shortfall_reduced
- PASS: memoryless_scaled_impaired_restoration_shortfall_reduced
- PASS: memoryless_scaled_mean_quality_guard
- PASS: memoryless_scaled_fixed_shortfall_guard
- PASS: memoryless_scaled_stall_guard
- PASS: memoryless_scaled_action_disagreement_above_1_percent

## Mechanism and censoring

- nash: active bookkeeping fraction 1.1667%; observed recovery events 20/20; remaining cases right-censored at40 rounds. Nash bookkeeping does not affect its decisions.
- window_recovery: active bookkeeping fraction 1.1667%; observed recovery events 20/20; remaining cases right-censored at40 rounds. Nash bookkeeping does not affect its decisions.
- memoryless_scaled: active bookkeeping fraction 9.5500%; observed recovery events 20/20; remaining cases right-censored at40 rounds. Nash bookkeeping does not affect its decisions.
- memoryless_unscaled: active bookkeeping fraction 9.5167%; observed recovery events 20/20; remaining cases right-censored at40 rounds. Nash bookkeeping does not affect its decisions.
- fixed_window: active bookkeeping fraction 1.5917%; observed recovery events 20/20; remaining cases right-censored at40 rounds. Nash bookkeeping does not affect its decisions.

Expiry is not delivered recovery. See `diagnostics/window_dynamics.csv` for separate positive expiry, negative credit expiry, new deficit and delivered surplus.

## Content-specific mean-quality differences

| Baseline | Content | Mean delta | Positive/negative seeds |
|---|---|---:|---|
| nash | BuskingUnderpass05 | -0.003602 | 0/16 |
| nash | Cheerleading01 | +0.003262 | 16/0 |
| nash | ConferenceParticipant02 | -0.000583 | 1/2 |
| memoryless_scaled | BuskingUnderpass05 | -0.006423 | 1/10 |
| memoryless_scaled | Cheerleading01 | +0.004224 | 8/2 |
| memoryless_scaled | ConferenceParticipant02 | +0.003409 | 10/0 |

No parameters were changed after opening the holdout. This is offline fluid transport and objective trace replay, not live streaming or subjective QoE. Six source segments repeat across120 rounds; panel and seed dependence must not be ignored.
