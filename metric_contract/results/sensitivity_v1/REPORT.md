# Exposed metric and service-contract sensitivity

Fixed paths are rescored, not retuned. Offline bounds know future quality.
No new holdout, player experiment, human-QoE validation or controller success claim.

## Original-event, four-segment eventual playback

| Metric | Policy | Positive loss / episodes | Mean unpaid | Targets 25/50/75/100% met | Donor/recipient floor violations |
|---|---|---:|---:|---|---:|
| fine_index | completed_mpc | 168/168 | 0.380393768806 | 153 / 92 / 53 / 46 | 24/2 |
| fine_index | offline | 168/168 | 0.344985407862 | 164 / 96 / 56 / 56 | 0/0 |
| fine_index | prefix_cost_greedy | 168/168 | 0.369166055599 | 156 / 90 / 56 / 56 | 20/2 |
| fine_index | prefix_greedy | 168/168 | 0.371670163803 | 156 / 90 / 55 / 53 | 29/11 |
| fine_index | prefix_maxmin | 168/168 | 0.378154014303 | 156 / 90 / 53 / 47 | 29/11 |
| fine_index | prefix_mpc | 168/168 | 0.3759658527 | 156 / 92 / 54 / 46 | 23/2 |
| fine_index | prefix_nash | 168/168 | 0.521069301832 | 121 / 68 / 38 / 31 | 25/14 |
| fine_index | slack_mpc | 168/168 | 0.380393768806 | 153 / 92 / 53 / 46 | 24/2 |
| fine_index | wait_mpc | 168/168 | 0.375420577169 | 154 / 92 / 54 / 48 | 27/2 |
| index | completed_mpc | 168/168 | 0.38041125864 | 153 / 92 / 53 / 46 | 0/1 |
| index | offline | 168/168 | 0.344993976139 | 164 / 96 / 56 / 56 | 0/0 |
| index | prefix_cost_greedy | 168/168 | 0.36918515745 | 157 / 90 / 56 / 56 | 0/1 |
| index | prefix_greedy | 168/168 | 0.371690251931 | 157 / 90 / 55 / 53 | 2/2 |
| index | prefix_maxmin | 168/168 | 0.378167565359 | 157 / 90 / 53 / 47 | 2/2 |
| index | prefix_mpc | 168/168 | 0.375974204002 | 156 / 92 / 54 / 46 | 0/1 |
| index | prefix_nash | 168/168 | 0.521072124036 | 121 / 68 / 38 / 31 | 2/2 |
| index | slack_mpc | 168/168 | 0.38041125864 | 153 / 92 / 53 / 46 | 0/1 |
| index | wait_mpc | 168/168 | 0.375430452947 | 154 / 92 / 54 / 48 | 1/1 |
| negative_mse | completed_mpc | 168/168 | 0.773615790769 | 52 / 14 / 2 / 0 | 24/2 |
| negative_mse | offline | 168/168 | 0.716699481926 | 56 / 28 / 14 / 2 | 0/0 |
| negative_mse | prefix_cost_greedy | 168/168 | 0.754092439604 | 55 / 14 / 3 / 2 | 20/2 |
| negative_mse | prefix_greedy | 168/168 | 0.738294538957 | 55 / 22 / 10 / 2 | 29/11 |
| negative_mse | prefix_maxmin | 168/168 | 0.752192251769 | 54 / 17 / 9 / 1 | 29/11 |
| negative_mse | prefix_mpc | 168/168 | 0.772375118097 | 53 / 13 / 2 / 0 | 23/2 |
| negative_mse | prefix_nash | 168/168 | 0.812834936806 | 37 / 15 / 7 / 0 | 25/14 |
| negative_mse | slack_mpc | 168/168 | 0.773615790769 | 52 / 14 / 2 / 0 | 24/2 |
| negative_mse | wait_mpc | 168/168 | 0.767624240072 | 53 / 16 / 3 / 0 | 27/2 |
| psnr_db | completed_mpc | 168/168 | 0.202285617153 | 168 / 153 / 106 / 46 | 24/2 |
| psnr_db | offline | 168/168 | 0.149323241995 | 168 / 168 / 117 / 60 | 0/0 |
| psnr_db | prefix_cost_greedy | 168/168 | 0.20745863307 | 168 / 137 / 108 / 60 | 20/2 |
| psnr_db | prefix_greedy | 168/168 | 0.20996275164 | 168 / 137 / 107 / 57 | 29/11 |
| psnr_db | prefix_maxmin | 168/168 | 0.216446597937 | 168 / 137 / 105 / 51 | 29/11 |
| psnr_db | prefix_mpc | 168/168 | 0.198955621777 | 168 / 153 / 107 / 46 | 23/2 |
| psnr_db | prefix_nash | 168/168 | 0.419635147091 | 137 / 95 / 59 / 34 | 25/14 |
| psnr_db | slack_mpc | 168/168 | 0.202285617153 | 168 / 153 / 106 / 46 | 24/2 |
| psnr_db | wait_mpc | 168/168 | 0.19811940839 | 168 / 153 / 107 / 49 | 27/2 |

## Offline feasibility across contracts

Same total four-slot byte reserve for all horizons. Only completed recipient segments count before a deadline.

| Metric | Initial rung | H | Contract | Positive loss | Targets 25/50/75/100% feasible | Mean unpaid |
|---|---:|---:|---|---:|---|---:|
| fine_index | 0 | 1 | deadline | 168 | 0 / 0 / 0 / 0 | 1.0 |
| fine_index | 0 | 1 | media | 168 | 75 / 56 / 26 / 15 | 0.629198996206 |
| fine_index | 0 | 2 | deadline | 168 | 47 / 28 / 2 / 0 | 0.782490559813 |
| fine_index | 0 | 2 | media | 168 | 156 / 62 / 56 / 56 | 0.424957316005 |
| fine_index | 0 | 4 | deadline | 168 | 159 / 96 / 56 / 56 | 0.347891532666 |
| fine_index | 0 | 4 | media | 168 | 164 / 96 / 56 / 56 | 0.344985407862 |
| fine_index | 1 | 1 | deadline | 168 | 0 / 0 / 0 / 0 | 1.0 |
| fine_index | 1 | 1 | media | 168 | 139 / 123 / 98 / 64 | 0.306079737617 |
| fine_index | 1 | 2 | deadline | 168 | 111 / 95 / 70 / 36 | 0.472743576402 |
| fine_index | 1 | 2 | media | 168 | 168 / 168 / 165 / 150 | 0.020031714768 |
| fine_index | 1 | 4 | deadline | 168 | 168 / 168 / 166 / 155 | 0.012125369805 |
| fine_index | 1 | 4 | media | 168 | 168 / 168 / 168 / 158 | 0.006329522172 |
| index | 0 | 1 | deadline | 168 | 0 / 0 / 0 / 0 | 1.0 |
| index | 0 | 1 | media | 168 | 75 / 56 / 26 / 15 | 0.629211539538 |
| index | 0 | 2 | deadline | 168 | 47 / 28 / 2 / 0 | 0.782488757087 |
| index | 0 | 2 | media | 168 | 156 / 62 / 56 / 56 | 0.424974986952 |
| index | 0 | 4 | deadline | 168 | 159 / 96 / 56 / 56 | 0.347906982145 |
| index | 0 | 4 | media | 168 | 164 / 96 / 56 / 56 | 0.344993976139 |
| index | 1 | 1 | deadline | 168 | 0 / 0 / 0 / 0 | 1.0 |
| index | 1 | 1 | media | 168 | 139 / 123 / 98 / 64 | 0.306048544374 |
| index | 1 | 2 | deadline | 168 | 111 / 95 / 70 / 36 | 0.472715211041 |
| index | 1 | 2 | media | 168 | 168 / 168 / 165 / 150 | 0.020047019083 |
| index | 1 | 4 | deadline | 168 | 168 / 168 / 166 / 155 | 0.012101238925 |
| index | 1 | 4 | media | 168 | 168 / 168 / 168 / 158 | 0.006311026025 |
| negative_mse | 0 | 1 | deadline | 168 | 0 / 0 / 0 / 0 | 1.0 |
| negative_mse | 0 | 1 | media | 168 | 26 / 3 / 0 / 0 | 0.871343576477 |
| negative_mse | 0 | 2 | deadline | 168 | 0 / 0 / 0 / 0 | 0.936401425265 |
| negative_mse | 0 | 2 | media | 168 | 55 / 27 / 13 / 2 | 0.73697286619 |
| negative_mse | 0 | 4 | deadline | 168 | 56 / 27 / 13 / 2 | 0.720220763875 |
| negative_mse | 0 | 4 | media | 168 | 56 / 28 / 14 / 2 | 0.716699481926 |
| negative_mse | 1 | 1 | deadline | 168 | 0 / 0 / 0 / 0 | 1.0 |
| negative_mse | 1 | 1 | media | 168 | 140 / 93 / 54 / 23 | 0.44315639778 |
| negative_mse | 1 | 2 | deadline | 168 | 112 / 65 / 34 / 17 | 0.581712913189 |
| negative_mse | 1 | 2 | media | 168 | 168 / 145 / 135 / 88 | 0.135362023761 |
| negative_mse | 1 | 4 | deadline | 168 | 168 / 168 / 163 / 92 | 0.055220338281 |
| negative_mse | 1 | 4 | media | 168 | 168 / 168 / 163 / 94 | 0.052873165148 |
| psnr_db | 0 | 1 | deadline | 168 | 0 / 0 / 0 / 0 | 1.0 |
| psnr_db | 0 | 1 | media | 168 | 126 / 71 / 26 / 15 | 0.543560221601 |
| psnr_db | 0 | 2 | deadline | 168 | 98 / 43 / 2 / 0 | 0.696851799067 |
| psnr_db | 0 | 2 | media | 168 | 168 / 109 / 88 / 60 | 0.272974274391 |
| psnr_db | 0 | 4 | deadline | 168 | 168 / 168 / 117 / 60 | 0.151575894507 |
| psnr_db | 0 | 4 | media | 168 | 168 / 168 / 117 / 60 | 0.149323241995 |
| psnr_db | 1 | 1 | deadline | 168 | 0 / 0 / 0 / 0 | 1.0 |
| psnr_db | 1 | 1 | media | 168 | 140 / 140 / 135 / 117 | 0.187054693011 |
| psnr_db | 1 | 2 | deadline | 168 | 112 / 112 / 107 / 89 | 0.3537185267 |
| psnr_db | 1 | 2 | media | 168 | 168 / 168 / 168 / 168 | 0.0 |
| psnr_db | 1 | 4 | deadline | 168 | 168 / 168 / 168 / 168 | 0.0 |
| psnr_db | 1 | 4 | media | 168 | 168 / 168 / 168 / 168 | 0.0 |

## Verification

- original_policy_scores: 1344
- original_strict_oracles: 168
- saved_clock_decisions: 5376
- independent_queries: 4032
- minimum_cost_target_checks: 32256
- affine_path_checks: 1463616
- strict_saved_path_bound_checks: 57476
- monotonicity_checks: 4032

All cohort/scene cells and minimum-cost path witnesses are in results.json.gz.
Targets are accounting choices, not perceptual thresholds. Initial-rung1 fixed paths are counterfactual rescoring only.
