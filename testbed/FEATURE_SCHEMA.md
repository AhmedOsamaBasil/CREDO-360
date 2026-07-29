# Recovered published feature schema

The original `matlab.mat` contains a 174 × 13 `input` matrix but no directly
portable table headers. The schema is recoverable from four mutually consistent
sources:

1. `Ensemble994.RequiredVariables`, `trainedModel100MOS.RequiredVariables`, and
   `Resolution.RequiredVariables` embedded in the MAT file;
2. Table 6 of Al-Mashhadani et al., *Network* 2022;
3. the metric sequence exposed by the bundled DASHIF reference-player page; and
4. numeric ranges, unique values, and correlations in the matrix.

## Source-order mapping

| Index | Name | Evidence/range |
|---:|---|---|
| 0 | BufferLength | 0–29.992 seconds |
| 1 | BitrateDownloading | 45–3792 kbps, plus zero rows |
| 2 | IndexDownloading | DASH representation selected for download |
| 3 | CurrentIndex | DASH representation currently rendered |
| 4 | MaxIndex | Normally 20 in valid observations |
| 5 | DropedFrames | Source spelling; cumulative 0–219 |
| 6 | MinimumLatency | 0–0.01 seconds |
| 7 | AverageLatency | 0–0.25 seconds |
| 8 | MaxLatency | 0–0.50 seconds |
| 9 | MinimumDownload | 0–0.84 seconds |
| 10 | AverageDownload | 0–7.72 seconds |
| 11 | MaxDownload | 0–11.0 seconds |
| 12 | Resolution | Selected representation bandwidth, 45,373–3,792,491 bps |

The representation/index mapping observed in stable rows is approximately:

| Representation bandwidth | DASH index |
|---:|---:|
| 45,373 bps | 1 |
| 88,482 bps | 2 |
| 252,988 bps | 6 |
| 368,912 bps | 8 |
| 987,061 bps | 12 |
| 3,792,491 bps | 20 |

Rows during switching can contain a previous/current index or representation,
which explains mixed values within some bitrate groups.

## Controller use

The revised testbed now constructs candidate features using their declared
semantics:

- candidate bitrate sets `BitrateDownloading`, `IndexDownloading`, and
  `Resolution`;
- prior bitrate sets `CurrentIndex`;
- buffer is carried as state;
- latency and download min/mean/max are derived from service time;
- dropped frames are induced only when selected bitrate exceeds user service.

This replaces the rejected anonymous-column mapping used in earlier runs.
The mapping is evidence-backed, but the replay oracle remains simulated and is
not a substitute for a live DASH/Mininet measurement.

