# Synthesis verification

This is post-hoc evidence reconciliation. No controller, optimizer, network
measurement, human study or holdout was rerun for the synthesis. Earlier
scientific artifacts remain frozen and retain their independent verifiers.

The canonical synthesis SHA-256 is:

`ae1d8148e76906edc0483eeb507f2f2859cd2eb5b9ce97923d807d55b4d3dd39`

The same hash and generated report reproduce on Windows and WSL/Linux.
Metadata binds the four implementation/test sources and seven inputs. Each
input is verified against its own published canonical scientific hash before
aggregation; changed values are not ignored by newline or compression handling.

## Coverage of the new checks

- All 336 episode/timing joins across geometric, adaptive and temporal layers.
- All 3,024 temporal model cells and 3,024 geometric control cells for the two
  timing assumptions; missing/duplicate cells fail explicitly.
- Equal past-debt ledgers, native half thresholds, R4 reference-byte entitlement,
  and ideal actual-duration oracle parity for all 168 episodes.
- Point-planner/cost-greedy action, admission and score equivalence retained;
  no planning novelty is inferred from identical decisions.
- Eight metric/clock cells independently reaggregated from oracle rows and
  compared to their historical summaries; their contract remains separate.
- Nineteen paced sessions, 45,594 recorded frame checks and the zero-credit
  negative control reconciled without calling these pixel or network evidence.
- Five structured claim kinds require their distinct qualifiers and reject
  promotion to deployment guarantees or human-QoE validation. These schema
  checks do not verify arbitrary natural-language prose.

All **19 new tests** pass. Full regression runs pass **454 tests plus 24
subtests on Windows** and **450 plus 24 on Linux**; the four Torch tests are
Windows-only. Portable-model tests pass five on each OS, and the Windows
client-protocol check passes 11 assertions. The case-inspection command was
also run for the retained false-promise episode `v2:River01:12:11`.

No scientific or test failure occurred. Two initial read-only inspections
used the workspace Git cwd and an incorrect compressed-results suffix;
both were corrected without changes to data or Git settings. WSL emitted a
nonfatal root systemd-session warning during a portable test; the test passed.
Literature retrieval timeouts/rate limits are documented in `RELATED_WORK.md`.
No inaccessible full text is represented as fully reviewed.

Local regression success is distinct from GitHub CI. Consult the workflow for
the exact final commit; this file does not predict its completion. Building
the synthesis refuses to overwrite the saved result directory.
