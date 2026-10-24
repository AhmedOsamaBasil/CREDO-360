# Exposed-data diagnostic results

Development only: both catalogues were previously inspected. Six paired seeds per catalogue; 360 episodes / 216,000 user-rounds. Intervals in `paired_diagnostics.csv` are descriptive, conditional on these fixed content pools, and are not independent confirmation.

**No candidate passed the locked development screen. No new holdout was consumed.**

## Range-normalized ceiling: complete policy means

The quality index is clipped to [1,5]; worst quality is the minimum of the five user time averages. Fixed shortfall uses target 4 for every policy. Stall is cumulative seconds per user. Direct rules have no active recovery state; their logged residual balances are shadow diagnostics.

### exposed_v2

| Policy | Worst quality | Worst VW-PSNR (dB) | Mean quality | Fixed shortfall | Stall (s/user) | Active (%) |
|---|---:|---:|---:|---:|---:|---:|
| nash | 3.216877 | 31.3013 | 3.770446 | 44.979163 | 20.586396 | 0.000 |
| instant_maxmin | 3.223608 | 31.3416 | 3.765865 | 44.949267 | 17.204088 | 0.000 |
| window_maxmin | 3.224795 | 31.3488 | 3.757838 | 45.853031 | 18.619466 | 0.000 |
| window_nash | 3.194316 | 31.1659 | 3.772893 | 45.535781 | 20.093903 | 0.000 |
| floor_bank | 3.223867 | 31.3432 | 3.767880 | 45.000723 | 19.636317 | 29.361 |
| floor_nobank | 3.224959 | 31.3498 | 3.767068 | 45.018570 | 19.304673 | 51.611 |
| floor_memoryless | 3.186819 | 31.1209 | 3.762184 | 46.275596 | 18.645213 | 30.111 |
| fair_bank | 3.223290 | 31.3397 | 3.767720 | 44.998571 | 19.632939 | 35.139 |
| fair_nobank | 3.224016 | 31.3441 | 3.767101 | 45.033824 | 19.329105 | 57.611 |
| fair_memoryless | 3.182997 | 31.0980 | 3.760684 | 46.443365 | 18.628696 | 31.917 |

### exposed_v3

| Policy | Worst quality | Worst VW-PSNR (dB) | Mean quality | Fixed shortfall | Stall (s/user) | Active (%) |
|---|---:|---:|---:|---:|---:|---:|
| nash | 4.207781 | 37.5025 | 4.505477 | 5.326171 | 12.935212 | 0.000 |
| instant_maxmin | 4.197566 | 37.3259 | 4.483477 | 4.987040 | 8.827406 | 0.000 |
| window_maxmin | 4.208033 | 37.6089 | 4.465617 | 6.308003 | 6.694192 | 0.000 |
| window_nash | 4.221168 | 37.6898 | 4.505644 | 5.342297 | 12.954838 | 0.000 |
| floor_bank | 4.207781 | 37.5025 | 4.505477 | 5.326171 | 12.935212 | 1.444 |
| floor_nobank | 4.206977 | 37.4977 | 4.505325 | 5.259035 | 12.935212 | 13.500 |
| floor_memoryless | 4.205137 | 37.4774 | 4.503344 | 5.393084 | 12.735104 | 12.389 |
| fair_bank | 4.200369 | 37.3489 | 4.493034 | 5.384827 | 10.485927 | 67.444 |
| fair_nobank | 4.201681 | 37.3720 | 4.494359 | 5.247466 | 10.794171 | 88.500 |
| fair_memoryless | 4.191346 | 37.4231 | 4.475016 | 6.169801 | 7.433684 | 47.917 |

## Exact failed development checks

All passing and failing checks are retained in `all_development_checks.csv`.

### floor_bank

- exposed_v2:floor_memoryless:stall_guard
- exposed_v2:window_maxmin:worst_quality_gain
- exposed_v2:window_maxmin:stall_guard
- exposed_v3:nash:worst_quality_gain
- exposed_v3:window_maxmin:worst_quality_gain
- exposed_v3:window_maxmin:stall_guard
- exposed_v3:window_nash:worst_quality_gain

### floor_nobank

- exposed_v3:nash:worst_quality_gain
- exposed_v3:window_maxmin:worst_quality_gain
- exposed_v3:window_maxmin:stall_guard
- exposed_v3:window_nash:worst_quality_gain

### fair_bank

- exposed_v2:fair_memoryless:stall_guard
- exposed_v2:window_maxmin:worst_quality_gain
- exposed_v2:window_maxmin:stall_guard
- exposed_v3:nash:worst_quality_gain
- exposed_v3:fair_memoryless:stall_guard
- exposed_v3:window_maxmin:worst_quality_gain
- exposed_v3:window_maxmin:stall_guard
- exposed_v3:window_nash:worst_quality_gain

### fair_nobank

- exposed_v2:window_maxmin:worst_quality_gain
- exposed_v3:nash:worst_quality_gain
- exposed_v3:fair_memoryless:stall_guard
- exposed_v3:window_maxmin:worst_quality_gain
- exposed_v3:window_maxmin:stall_guard
- exposed_v3:window_nash:worst_quality_gain

## Files and interpretation boundaries

- `policy_means.csv`: all 60 cohort/scenario/policy combinations, not just the main stress case.
- `window_accounting.csv`: delivery and expiry are separate; expiry is never called recovery. Row aggregates are descriptive.
- `impairment_by_content.csv`: sender-only absolute/relative severity, counted once rather than ten times across policies.
- `action_disagreements_aggregated.csv`: individual rung decisions, 3,600 comparisons per cohort/scenario/pair.
- Parent `paired_diagnostics.csv`: all locked matched contrasts, including target and banking factors, with descriptive seed intervals.
- Two figures show primary quality comparisons and activation/targets, respectively.

No human validation, adaptive coverage guarantee, novel queue theorem, or successful new-method claim follows from this experiment. The range ceiling is a synthetic known capability profile, not equal absolute or perceptual impairment. Runtime is measured but not charged to playback. Six source segments repeat; this is not a live player.
