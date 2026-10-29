# Wu original-source acquisition and alignment audit

All18 author-linked original videos and the trace archive were acquired
privately and hashed: **3,651,951,337 bytes across19 files**. This completes
acquisition, **not the source-adapter freeze**. No participant orientations,
demographics, quality labels or recovery outcomes were interpreted or derived.
The earlier confirmation design and all frozen results remain unchanged.

## Findings

| Check | Result | Interpretation |
|---|---|---|
| Source catalogue |18 videos, corrected Experiment2/Video9 link;864 trace files |Two9-clip conditions and48 repeated source identities, not864 independent people |
| Strict trace clock |94/864 pass;770 contain a backward step before completion of the audited interval |The current adapter cannot silently sort or repair these records |
| Sequential source decode |16/18 pass the strict zero-start test |Experiment2/Video2 starts at0.040s; Video9 at0.067s; source offsets remain unresolved |
| Quaternion formula |Signed-axis and200 independent multiplication checks pass |This verifies the published vector formula, not texture orientation |
| Texture mapping |Horizontal wrapping sign not independently verified |No default production adapter or full source-freeze manifest issued |

The clock checks inspect only `PlaybackTime` and row shape. Wall timestamps,
quaternions and positions remain opaque. Duplicate playback times are retained.
The actual archive uses `Experiment_E/ID/video_K.csv` with zero-based K, rather
than the folder names drawn in the paper. All864 members and their exclusions
are accounted for; the candidate roster uses the frozen string-lexicographic
directed-cycle rule. Timing exclusions are **not poor recovery outcomes**.

The separately labeled post-inspection diagnostic looks for the first exact
zero PlaybackTime, without changing eligibility.360 files have no exact-zero
record; among the504 with one,431 have subsequent backward steps, including139
whose preceding time is at least the first0.5s target. The largest such step
is2.598s. Therefore deleting a startup prefix is neither a complete solution
nor an authorized repair. These checks do not establish that the original
benchmark is invalid; they show that our assumed clock adapter is insufficient.

An initial `ffprobe -read_intervals 0%61` check inadvertently sought into the
file and skipped decoder preroll. The corrected audit uses `%61` without an
initial seek; the earlier private report is retained and is not the source
timing result. An initial version also stopped on a nonzero stream start;
the final report retains such sources as failed checks. No source file was
retimed, trimmed or replaced. Catalogue frame rates/counts/durations are kept
alongside actual stream metadata rather than treated as ground truth.

A private5s contact sheet was visually checked for gross content/projection
appearance. Some original clips contain dark/title material at that time;
none was dropped or shifted for that reason. This is not landmark-coordinate
validation or an assessment of quality. Source images are not redistributed.

## Reproduce

Offline checks (no network or private source access):

```sh
python -m unittest wu_source.test_source wu_source.test_audit -v
python -m wu_source.audit --verify
python -m source_preflight.audit --verify
python -m confirmation_protocol.register --verify
```

Private acquisition and complete metadata derivation, for authorized source
users with sufficient disk space and ffprobe on PATH:

```sh
python -m wu_source.acquire --private-dir /path/outside/repository/assets
python -m wu_source.media --private-dir /path/outside/repository/assets --output /new/private/media.json
python -m wu_source.audit --private-dir /path/outside/repository/assets --media-audit /new/private/media.json --output /new/private/audit
```

Existing complete files are hash-checked, not overwritten. Incomplete attempts
are preserved; an explicit `--attempt 2` or `--attempt 3` uses a separate partial
file. Three first attempts timed out, two completed on the second attempt, and
the remaining video completed on the third. Four incomplete files are recorded
in the report. These are acquisition attempts, not experimental repetitions.

The public report contains hashes, clock summaries, source-ID rosters, decoded
timing summaries and explicit blocking flags. Offline validation checks their
consistency and method bindings; it cannot independently reconstruct omitted
private source values. Full reproduction requires the exact hashed originals.

## What remains before confirmation

Resolve the playback-clock/session and media-origin conventions using source
evidence, then independently verify texture wrapping against a known renderer
or published coordinate reference. Any revised alignment rule must be explicit
and frozen before quality outcomes; do not choose it for favorable recovery.
One possible next step is a separately declared calibration subset using the
clips illustrated in the source paper, with remaining clips reserved for later
content confirmation. That would amend the original all18-clip design and needs
an explicit decision; **no such calibration or exclusion has been performed**.
Repeated identities would still preclude a person-independent holdout claim.

## Sources and reuse

Wu et al., *A Dataset for Exploring User Behaviors in VR Spherical Video
Streaming*, MMSys2017, DOI[10.1145/3083187.3083210](https://doi.org/10.1145/3083187.3083210),
Sections2.1--2.4 and Figures5--6. [Author dataset page](https://wuchlei-thu.github.io/).
The author page links the supplied edited stimuli and explicitly corrects
Experiment2/Video9. Its citation request supports attributed research use,
not blanket redistribution rights over participant records or media.

The author site's source at commit
`6ea44d0e2193679cd00d6f02850f3f9cd16ffbd1` contains a visualization using
precomputed projected coordinates, but the inspected `js/my_plot.js` does not
provide the quaternion-to-texture conversion. It does not independently settle
the sign. No third-party code, full paper, source media or raw traces are
included here. No new scientific superiority, subjective QoE or deployment
guarantee follows from passing these software tests.
