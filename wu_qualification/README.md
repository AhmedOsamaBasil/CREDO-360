# Reserved Wu clock/media qualification

Ten of the sixteen registered confirmation clips pass the frozen metadata gate:
five free-exploration clips and five content-focused/memory-test clips. There
are 452 clock-and-media-qualified source-ID files and 452 directed candidate
pairs. This is **not** a recovery result or a completed source/pose validation.
The same 48 original identities recur; these are not 452 independent people.

The method was committed and published as `4945eae` before the full metadata
batch. It applies the conservative adapter from `60c2f0a` without modification.
The approved two calibration clips, e1v02 and e2v04, remain excluded by design.
[PROTOCOL.md](PROTOCOL.md) specifies the immutable rules and release boundary.

## Complete clip accounting

Every row below represents 48 registered source-ID files. Clock qualification
requires one and only one chronological ascending crossing of each target,
then an age at most 0.1 seconds, valid wall-clock order, an initial bracket and
60-second coverage. All original rows are retained, including later repetitions.
Clock-only passes remain visible even when the media origin is ineligible.

| Clip | Condition | Clock-qualified | Clock and media | Clip exclusion |
|---|---|---:|---:|---|
| e1v01 | Free exploration | 27 | 27 | None |
| e1v03 | Free exploration | 47 | 47 | None |
| e1v04 | Free exploration | 48 | 48 | None |
| e1v05 | Free exploration | 46 | 46 | None |
| e1v06 | Free exploration | 48 | 48 | None |
| e1v07 | Free exploration | 0 | 0 | Insufficient clock-qualified IDs |
| e1v08 | Free exploration | 0 | 0 | Insufficient clock-qualified IDs |
| e1v09 | Free exploration | 0 | 0 | Insufficient clock-qualified IDs |
| e2v01 | Content-focused | 46 | 46 | None |
| e2v02 | Content-focused | 47 | 0 | Nonzero media origin (0.040 s) |
| e2v03 | Content-focused | 48 | 48 | None |
| e2v05 | Content-focused | 0 | 0 | Insufficient clock-qualified IDs |
| e2v06 | Content-focused | 47 | 47 | None |
| e2v07 | Content-focused | 48 | 48 | None |
| e2v08 | Content-focused | 47 | 47 | None |
| e2v09 | Content-focused | 48 | 0 | Nonzero media origin (0.067 s) |

Of 768 files, 547 pass the clock rule; 95 of these belong to the two
media-origin exclusions, leaving 452 metadata-qualified files. The 221 clock
failures contain 196 ambiguous-target, 21 missing-initial-bracket and five
stale-target flags. Flags overlap: they are not mutually exclusive counts.
All files parsed successfully; no file, ID or clip was replaced.

Pairing uses the prespecified string-lexicographic directed cycle, once as
recipient and once as donor per eligible ID. There are 216 candidate pairs in
free exploration and 236 in the content-focused condition. The two conditions
remain separate. Selection is not random and may favor cleaner recording
sessions; later results must retain all 16 registered clips and their exclusions,
with equal-clip and condition-specific reporting rather than pooled pair counts
treated as independent evidence.

The earlier source audit's 94/864 strict globally-monotonic-clock count is a
different rule on a different set. It is not an alternative estimate of this
547/768 unique-target-crossing result. This stage uses the published conservative
adapter, not a newly chosen threshold or an outcome-driven clock repair.

## Reproduction

From the software repository root, with its numerical Python dependencies:

```sh
python -m unittest wu_qualification.test_core wu_qualification.test_validation -v
python -m wu_qualification.run --verify
```

Public verification checks the immutable method/input bindings, complete
768-file census, target-count decisions, clip rosters and directed pairs. It
does not recreate source observations without the private originals.
See [VERIFICATION.md](VERIFICATION.md) for platform hashes, regression results
and the distinction between source qualification and scientific outcomes.

To independently rederive from the exact author-linked originals acquired as
described in [the source audit](../wu_source/README.md):

```sh
python -m wu_qualification.run --private-dir /path/to/original-assets --output /path/to/new-result
python -m wu_qualification.run --verify --output /path/to/new-result
```

The input directory contains `vr-dataset.zip` and the 16 original clip MP4s.
All 17 complete files are size/hash-checked before processing. Existing output
directories are refused. The frozen sequential-decoding audit is reused: this
stage is not a new independent media decode or playback measurement.

Published reports contain source hashes, source IDs, clock summaries, selected
row-index digests, exclusions and candidate pairs. Raw poses, positions,
calendar timestamps, demographics and source media are not published. The
timestamp parser treats quaternion and position fields as opaque strings.

## Next gate and limits

The output state is `metadata_roster_frozen_pose_validation_pending`, and
`full_source_ready` remains false. A separately versioned pose adapter must bind
this exact roster, validate selected quaternions with the previously declared
normalization limit and texture mapping, independently check converted geometry,
and retain any additional failures. No quality/recovery outcome may be derived
automatically by this package. The original 50%/40 s/R4/1.5 MB service contract,
encoding ladder and angular viewport model remain unchanged.

There is no subjective-QoE inference, physical-HMD validation, successful
recovery-controller claim, manuscript update or journal submission in this
artifact. Metadata qualification cannot establish those claims.
