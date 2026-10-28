# Engineering contract: actual-duration replay

Frozen actions; sampled distortion-seconds credited only on completed playback by40s.

| Duration | Policy | Half /168 | Protected half | Deadline unpaid | Eventual unpaid | Mean finish s | Donor/recipient floor losses |
|---|---|---:|---:|---:|---:|---:|---:|
| actual | baseline | 0 | 0 | 1.000000 | 1.000000 | 44.201220 | 0/0 |
| actual | completed_mpc | 4 | 4 | 0.808490 | 0.773616 | 46.964209 | 24/2 |
| actual | prefix_cost_greedy | 10 | 10 | 0.764070 | 0.754092 | 46.972552 | 20/2 |
| actual | prefix_greedy | 22 | 9 | 0.738321 | 0.738295 | 47.064405 | 29/11 |
| actual | prefix_maxmin | 17 | 6 | 0.752219 | 0.752192 | 47.177904 | 29/11 |
| actual | prefix_mpc | 1 | 1 | 0.806350 | 0.772375 | 46.963418 | 23/2 |
| actual | prefix_nash | 15 | 7 | 0.812861 | 0.812835 | 48.040640 | 25/14 |
| actual | slack_mpc | 4 | 4 | 0.808490 | 0.773616 | 46.964209 | 24/2 |
| actual | wait_mpc | 1 | 1 | 0.842785 | 0.767624 | 56.214451 | 27/2 |
| nominal | baseline | 0 | 0 | 1.000000 | 1.000000 | 44.206776 | 0/0 |
| nominal | completed_mpc | 4 | 4 | 0.808490 | 0.773616 | 46.969765 | 24/2 |
| nominal | prefix_cost_greedy | 10 | 10 | 0.764070 | 0.754092 | 46.978108 | 20/2 |
| nominal | prefix_greedy | 22 | 9 | 0.738321 | 0.738295 | 47.069961 | 29/11 |
| nominal | prefix_maxmin | 17 | 6 | 0.752219 | 0.752192 | 47.183460 | 29/11 |
| nominal | prefix_mpc | 1 | 1 | 0.806350 | 0.772375 | 46.968974 | 23/2 |
| nominal | prefix_nash | 15 | 7 | 0.812861 | 0.812835 | 48.046196 | 25/14 |
| nominal | slack_mpc | 4 | 4 | 0.808490 | 0.773616 | 46.969765 | 24/2 |
| nominal | wait_mpc | 1 | 1 | 0.842785 | 0.767624 | 56.220007 | 27/2 |

nominal strict future-known bound: deadline half 27/168; eventual half 28/168; mean deadline unpaid 0.720220764.

actual strict future-known bound: deadline half 27/168; eventual half 28/168; mean deadline unpaid 0.720220764.
