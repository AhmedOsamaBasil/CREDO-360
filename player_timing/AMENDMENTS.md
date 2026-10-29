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

The corrected features reproduced on Windows/Linux, and the v1 analytical
replay completed2,688cases. A two-unit browser smoke then exposed remux container
timing inconsistent with the normalized packet span: first chunk PTS0.1s and
browser duration2.066667s instead of2s. No full measured batch had started.
The diagnostic and v1 derived/replay artifacts are retained. Their code is
available at the commit preceding the v2 normalization, not silently overwritten.

A separate single-file probe confirms that a second lossless MP4 remux with
negative-DTS shifting disabled normalizes first PTS to0 and yields browser
duration2s, preserving the last frame at1.966667s. Preparation v2 applies this
uniformly to every child, with new file hashes, byte costs and source bindings.
It again verifies every encoded payload and decoded-frame hash against the
original. The study schedule, quality ledger, deadline and resource limits do
not change. The final browser batch uses only the validated v2 containers.
