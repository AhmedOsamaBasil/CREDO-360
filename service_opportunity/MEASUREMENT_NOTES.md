# Measurement implementation correction

The first service attempt at `a9751b3` completed all15 payload probes but failed
the final check of background bytes in idle versus busy trials. The runner had
not yet saved raw per-flow/counter observations, so the failed trial identity
cannot be recovered. The console timings and failure are preserved in
`results/service_attempt1_failure.json`; they are not validated service evidence.

A likely mechanism is orphan TCP send queues after terminating the background
process: process exit need not immediately stop its queued bytes. The harness
now uses abortive background socket close and starts a fresh receiver for every
probe. Raw completed-run measurements are saved before the integrity check so
a failed audit is retained. The namespace cleanup completed on the failed run.
These are isolation/recording corrections, not a new service configuration.
The fixed rates, payload, deadline, repetitions, model and comparison thresholds
are unchanged. No exposed model outcomes were inspected before this correction.
