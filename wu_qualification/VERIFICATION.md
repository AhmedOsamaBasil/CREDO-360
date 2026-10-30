# Verification and release scope

The fixed metadata method was committed and pushed as
`4945eaee0ee8a0c576364058ed860af2cb3d1151` before the complete Windows batch.
The source adapter, two-clip calibration split, original confirmation design
and earlier source audit were not changed. Post-batch artifact mutation tests
check release integrity; they do not change the selection rule.

## Independent reconstruction

Windows and WSL/Linux each rechecked all 17 complete private original files
(the trace archive and the sixteen reserved videos), parsed the 768 registered
trace files and independently generated a report in a separate directory.
Both canonical reports have SHA-256:

`58007f8a9264dd8318efc58bc41cd5687c0d89500ccfbc4af4d505cd1dadf6d2`.

Every trace's 60 target crossings were checked by a scalar interval-counting
implementation against the frozen selector: 46,080 target checks, with exact
agreement on decisions and accepted index lists. Report equality here is exact,
unlike the small floating-point differences in the earlier geometry calibration.
These are software replications on the same sources, not independent observations
or independent media decodes. Both reuse the same frozen sequential PTS audit.

The reports preserve all 768 files: 547 clock passes, 452 joint clock/media passes,
and 10 eligible clips. The two conditions contribute five eligible clips each
and respectively 216 and 236 directed candidate pairs. All 221 clock failures,
including overlapping reason flags, and 95 additional media-only exclusions
remain in the released report. There are no malformed/missing metadata records.

## Regression

- All 54 new unit/artifact tests pass on Windows and Linux. Seven additional
  scope-flag subtests check that the artifact cannot claim unperformed work.
- Full regression: 748 tests plus 48 subtests on Windows; 744 plus 48 on Linux.
  The four legacy Torch tests excluded on Linux are covered on Windows.
- Five portable-model tests also pass separately on Windows; these already
  belong to the broad collection and are not five additional unique tests.
- Windows client checks pass 11 assertions; shared-payload service tests pass.
- Original source report, calibration evidence and confirmation registration
  still verify without modification.

Tests include opaque quaternion/position fields, sanitized parse errors,
archive-path guards, duplicate clocks, backward wall time, late repeated target
crossings, stale repeated crossings, age boundaries, media-origin exclusions,
complete census, input hashes, pair rosters and scope flags. Their success does
not certify the scientific validity of quaternion values not yet inspected.

Previous calibration workflow 40972551713 is verified completed successfully.
This does not assert completion of a later release's workflow; the exact current
commit's GitHub status must be checked separately.

## Interpretation boundary

No source media was altered. No trace sorting, trimming, offset, interpolation,
clock stretching, source-ID replacement or performance-based exclusion occurred.
The metadata gate is deliberately conservative and is not a declaration that
the original dataset is invalid. Its eligible subset may not represent excluded
recordings or the whole source population.

No reserved-clip quaternion or position value was converted or interpreted;
the CSV reader consumes those columns as opaque strings. Demographic files were
not opened. No viewport-quality label, controller outcome, physical display
measurement, manuscript modification or submission is part of this release.
The output explicitly remains `metadata_roster_frozen_pose_validation_pending`.
The next pose/source validation must retain this roster and any further failures
before independent confirmation outcomes can be calculated.
