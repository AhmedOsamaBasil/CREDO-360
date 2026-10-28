# Measured decode-and-PTS-paced timing

measured decode/hash and software pacing; scripted arrivals; not rendering/HMD/network

18 nominal sessions (six fixed directed pairs), plus one late-release negative control. Not the full168 population.

| Policy | Sessions | Half by40s | Protected half | Mean unpaid | Added finish vs ideal s | Startup s | Later delay s |
|---|---:|---:|---:|---:|---:|---:|---:|
| prefix_mpc | 6 | 0 | 0 | 0.807455 | 0.225803 | 4.738427 | 2.429452 |
| prefix_cost_greedy | 6 | 0 | 0 | 0.782974 | 0.256300 | 6.280213 | 0.949359 |
| baseline | 6 | 0 | 0 | 1.000000 | 0.183995 | 3.703059 | 0.687712 |

All 45594 frame events and all152 segment records pass the independent timing/identity audit.
The late-release control earns zero recipient credit before40s. Full scalar records are retained.
