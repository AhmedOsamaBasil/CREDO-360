# Wu original-source validation v1

This metadata/source-validation stage precedes any new quality labels or
recovery outcomes. It does not amend the frozen confirmation design or declare
an experimental result. Raw files remain outside the software repository.

## Intake and eligibility

Acquire the exact archive and all18 corrected original stimuli listed in the
frozen `source_preflight/results/access_v1/wu_metadata.json`. Record byte counts
and full SHA-256 hashes. Preserve incomplete acquisition attempts; they are
not experiments. Do not inspect demographics or participant orientations.

The archive layout is `Formated_Data/Experiment_E/ID/video_K.csv`, where E is1
or2, ID is a source string1..48, and K=0..8 maps to catalogue VideoNo=K+1.
Validate the complete864-member Cartesian roster. Keep the two nine-clip
conditions separate. There are48 repeated source identities, not864 people.

Read only the exact CSV header, row shape and PlaybackTime field. The wall
timestamp, quaternion and position fields remain opaque strings. For the
original0..60s window require nonnegative finite, nondecreasing playback times,
an initial sample at/before0.5s, coverage through60s, and a next sample within
0.1s of each target0.5,1.5,...,59.5s. Duplicate playback times are retained
(a render loop can log the same video frame). No sorting, interpolation,
deduplication, looping, concatenation, time stretching or outcome-based repair.
All exclusions and their metadata-only reasons must be reported. Freeze the
eligible string-ID roster before any outcome derivation; directed cycles use
the existing lexicographic rule, not numeric reordering chosen afterward.

## Media timing

Check each completed file's hash against its receipt. Decode the first61s
using ffprobe sequentially (no initial seek), with one video stream selected.
Require start PTS0, strictly
increasing finite decoded frame PTS, coverage through60s and a preceding
displayed frame within0.1s for each half-second target. Retain stream duration,
nominal/average rational frame rates, declared frame count, dimensions and
all source catalogue discrepancies. Catalogue rounding does not override
actual file timing. Frame PTS validation is not measurement of the historical
HMD display clock or of stalled playback.

## Geometry and release gate

Wu et al. Sec2.4 defines xyzw unit quaternions, Unity axes and the forward-vector
formula. Implement that formula and independently test it using quaternion
multiplication, signed axes and q/-q equivalence. The source texture seam is
+X at(u=0,v=.5). A horizontal wrapping sign must be explicitly supported by
source rendering/landmark evidence; synthetic self-consistency is not that
evidence. Until verified, no full source-freeze manifest or production pose
conversion is authorized. A candidate mapping must require an explicit sign
and must not pick that sign using recovery outcomes.

Original50%/40s/R4/1.5MB contract, encoding ladder, whole-parent actions and
angular viewport family remain unchanged. Do not treat a timing/geometry
pass as proof of research novelty, subjective QoE, privacy permission, a
hard execution bound, a new participant cohort or a positive recovery result.
Author-page availability/citation instructions are a research-use basis, not
a blanket redistribution license for participant files or third-party media.
