# Execution notes

The initial protocol/method was published as `1a1fa78` before the full audit.
All216 media hashes/packet timelines passed. The first replay attempt then
stopped on an incorrect user/rung index in the secondary PSNR diagnostic.
No replay artifact was produced and the real-time timing stage had not started.

The secondary PSNR axes were corrected and an explicit four-dimensional fixture
was added. The distortion account, deadline, resource constraints, actual-duration
clock, policy paths and measurement plan were unchanged. The correction is
published as `66495ee` before restarting the full replay/timing stages. Initial commit
history and the already valid media audit are retained; no result is overwritten.

Post-batch `diagnose.py` and `test_validation.py` independently check byte
accounting, actual/nominal behavior identity and repeated-file frame consistency.
They do not modify the frozen methods, selections, contract or measured records.
