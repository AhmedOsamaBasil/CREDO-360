# Recorded implementation corrections

Before the measured batch, method `18763c7` completed payload and decoded-frame
validation for all 96 parents and 480 children. Its quality-parity assertion
then failed, so no derived feature/result artifact was produced and no full
browser session was run. The input had been the older causal feedback cache,
whose previous-pose sampling differs from the original quality-label sampler.

The correction derives offline chunk labels from the existing hash-bound trace
archives using the original first-pose-at/after rule. It preserves the parity
tolerance. The already remuxed files are revalidated, not overwritten. The
original quality/deadline/reserve, controllers, schedule and analysis stay fixed.
This correction is committed before the renewed preparation and measurements.
