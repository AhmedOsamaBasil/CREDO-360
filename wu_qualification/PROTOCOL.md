# Reserved-source clock/media qualification

Apply the adapter specification published at60c2f0a to all sixteen registered
confirmation clips,48 original source-ID files each. The two calibration clips
remain excluded by design. This is metadata qualification, not pose conversion,
quality-label derivation, a recovery experiment or a new participant sample.
Freeze this implementation and its source bindings before the full batch.

## Inputs and immutable rules

- Verify the complete private trace archive and all sixteen private original
  media files against the source audit's SHA-256/byte counts. Keep all source
  files unchanged. Reuse the frozen sequential-decoding audit; this stage is
  not another decode, playback or network measurement.
- Parse the exact nine-column header, wall Timestamp and PlaybackTime only.
  Quaternion and position strings remain opaque; no demographics are opened.
  Do not extract raw members or publish calendar values/clock sequences.
- Call the frozen `wu_calibration.adapter.select_indices` without modifying it.
  Count ALL ascending crossings before checking age. Require exactly one for
  every0.5,1.5,...,59.5s target, age<=0.1s, an initial bracket, coverage through60s
  and valid nondecreasing relative wall timestamps. Retain duplicates and all
  original row order. No sorting, prefix removal, offset, interpolation, first/
  last selection or time stretching. Scan complete logs so later repeated
  passages cannot silently evade the uniqueness check.
- Independently accumulate crossing counts/indices using scalar interval
  counting and compare every acceptance decision and selected-index list.
  Publish counts, unique-crossing ages and a selected-index digest, not poses.
- Retain the source audit's strict media gate. In particular e2v02/e2v09 have
  nonzero origins and remain media-ineligible. Do not normalize them using
  evidence from other clips. Recheck the audit's scalar pass flags for consistency.

## Accounting and exclusions

Report all768 registered files. Missing, malformed, nonfinite, ambiguous, stale,
incomplete or invalid-wall-clock records receive explicit metadata reasons;
never replace a source ID or clip. A failed input hash or independent-check
mismatch stops the batch rather than manufacturing an exclusion. No partial
artifact is presented as a complete roster.

A source ID is clock/media-qualified only when both checks pass. A clip needs
at least two such IDs. Pair qualified IDs using the original string-lexicographic
directed cycle, each once as recipient and once as donor. Keep clock-only passes
separate from final metadata qualification so media exclusions stay visible.
Retain every clip even when no pair exists. Preserve eight registered clips in
each viewing condition, report results per condition, and account separately for
the two calibration exclusions. Counts do not imply independent people or trials.

## Release gate

The output freezes a metadata candidate roster, not a fully validated pose/source
manifest. Selected quaternion validity and pose conversion remain unperformed;
no full-source-readiness flag or automatic outcome launcher is allowed. Any
subsequent versioned pose adapter must bind this roster and exact sources,
retain the calibrated texture direction, check selected quaternion validity
and preserve all failures before quality/recovery outcomes. The original
50%/40s/R4/1.5MB contract, native floors, ladder and angular viewport are unchanged.

Public outputs contain original software, technical methods, source hashes,
metadata summaries, ID rosters/pairs and tests only. Raw traces, reference data,
media, calendar timestamps and instruction files remain private. Commit/push
this stage before any manuscript changes. No submission or journal contact.
