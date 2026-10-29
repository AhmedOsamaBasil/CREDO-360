# External-source preflight

Wu2017 is the recommended source to validate next: all18 effective original
stimulus links responded to HTTP HEAD on29October2026. **This is not yet a
source/adapter freeze or an independent confirmation experiment.** No participant
trace, demographic record, video body, quality label or recovery outcome was
opened or calculated during this assessment. The existing confirmation design
and all earlier methods/results remain unchanged.

## What was established

The [Wu author page](https://wuchlei-thu.github.io/) links the trace archive,
original paper and a replacement stimulus for Experiment2/Video9. Bounded HTTP
range requests read only the ZIP directory and its two `videoMeta.csv` files:
966 directory entries,181,267,353 archive bytes,119,200 bytes transferred,
zero participant members opened. The archive contains neither video files nor
an identified README/license file. The access record retains both the original
and corrected Video9 links; the original mistakenly duplicates Video8's link.

The source metadata are not media ground truth. In particular, reported frame
counts, nominal frame rates and durations are not always mutually consistent.
Full original-file hashes, decoding/PTS, projection and landmark checks are
still required. A200 HEAD response establishes reachability at the check time,
not the identity, duration, availability forever or correctness of a video.

The paper separates free exploration (Experiment1) from content-focused viewing
with an announced memory test (Experiment2). Preserve both nine-clip catalogues
and report these conditions separately; do not treat them as interchangeable
replications or estimate a causal instruction effect from different videos.
Use the supplied edited stimuli, not replacement online uploads. PlaybackTime
and wall-clock Timestamp are distinct. The paper's quaternion order and texture
origin require an explicit, independently tested source adapter before labels.
See Wu et al., *MMSys2017*, DOI[10.1145/3083187.3083210](https://doi.org/10.1145/3083187.3083210),
Sections2.1--2.4 and Table1.

The author page requests citation for dataset use. That statement is not a
blanket license to republish third-party videos, participant traces or
demographics. Keep raw assets private; document the basis and scope of reuse
before finalizing the source freeze. No legal clearance is claimed here.

## Why the first candidate was not frozen

Both the original Corbillon landing page and direct archive returned HTTP410;
HTTPS failed with a TLS alert. Certificate verification was never disabled.
The [authors' source repository](https://github.com/xmar/360Degree_Head_Movement_Dataset/tree/b3bc7f8ac14c8de7b0023d69b649d697d3920286)
was inspected at a pinned commit, including configuration, logger, renderer,
export and analysis code. No release or verified replacement paired archive
was found in those checks. This is not a claim that no copy exists anywhere.

The five test IDs and source offsets are preserved in `source_review.json`;
training videos are not added. Original `testInfo.txt` records stimulus MD5s;
these legacy identity checks must be supplemented with SHA-256 and actual
frame/PTS checks. Paper notation, the analysis reference vector and the logger's
coordinate transformation cannot simply be interchanged. Reconcile the exact
acquisition version before converting poses; these observations do not prove
an error in the original study. The paper describes MIT software, which does
not settle separate dataset/video terms. Source: Corbillon et al., *MMSys2017*,
DOI[10.1145/3083187.3083215](https://doi.org/10.1145/3083187.3083215),
Sections3--4; exact source-file Git blob IDs are in the review.

## Software and reproduction

`intake.py` is an original, standard-library **Corbillon metadata-only intake
prototype**, retained for an original archive if one becomes available. It
checks session checksum syntax, configuration offsets and candidate timestamp
coverage. It never converts quaternions, extracts archive members, opens user
questionnaires or emits user IDs/raw rows. Sparse traces, duplicate timestamps,
backward frame IDs, missing files and repeated sessions are not silently fixed.
Unsafe archive paths, links, case aliases and oversized records are rejected.
Even a complete synthetic archive remains `blocked_before_outcomes`.

`wu_probe.py` reads only two exact metadata members and checks public stimulus
headers. It refuses unrestricted downloads when byte ranges are not honored,
caps requests/bytes and does not retain temporary signed redirect URLs. Raw
archive/media hashes are NOT claimed from a partial directory inspection.
`audit.py` replays the saved assessment offline; it does not recheck live URLs.

```sh
python -m unittest source_preflight.test_intake source_preflight.test_wu_probe source_preflight.test_audit -v
python -m source_preflight.audit --verify
python -m confirmation_protocol.register --verify
```

Optional future metadata access, never part of CI:

```sh
python -m source_preflight.wu_probe --probe --output NEW_PRIVATE_OUTPUT.json
python -m source_preflight.intake --archive ORIGINAL_LOCAL_CORBILLON_ARCHIVE.tar.gz
```

The probe refuses to replace an earlier output. New attempts must be preserved;
published access records are historical observations, not synthetic experiments.
No third-party source code, full paper or participant/video files are republished.

## Next gate

Acquire the author-linked original files privately, bind hashes and timestamps,
validate geometry using axis/landmark tests, inspect only timestamp/ID metadata
to freeze eligibility, and publish a versioned Wu-specific source/adapter record.
Retain all18 clips with explicit condition and any metadata-only exclusion.
Resolve nominal metadata discrepancies against files; do not repair by choosing
favorable recovery outcomes. Then, and only then, derive fresh labels using the
unchanged50%/40s/R4/1.5MB contract. No manuscript change follows from this
access audit alone.
