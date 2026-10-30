# Wu preparation v2: registered output-frame bound

This version integrates the generated-video-tested `-frames:v 1800` output
bound and durable early-stage evidence. All scientific inputs, arithmetic,
eligibility rules and validation thresholds are inherited unchanged. The
original pipeline and [failed first attempt](../wu_boundary/README.md) remain
immutable. See [protocol](PROTOCOL.md).

The new runner imports the original encoder's bounded command, metric,
sampling, timeline and segmentation routines without monkey-patching v1.
The only encoding-command addition is the output-frame bound. Full-frame
resize and the existing sampling-phase caveat remain explicit. Checkpoints
are evidence only, not permission to resume or reuse selected partial outcomes.

Pure validation, with no GPU or private media access:

```sh
python -m wu_pipeline_v2.spec
python -m unittest wu_pipeline_v2.test_v2 -v
```

An explicitly authorized run after registration publication requires the pinned
WSL runtime, exact source hashes and a new private output directory:

```sh
python -m wu_pipeline_v2.prepare --private-dir PRIVATE_ORIGINALS \
  --output NEW_PRIVATE_ATTEMPT --activate-fresh-quality EXACT_V2_REGISTRATION_SHA256
```

The expected complete preparation contains16registered clips,10eligible clips,
452directed pairs,60renditions,360parents,800recovery children and452trace-label
rows. No recovery algorithm, causal controller or software-player timing study
is run by this command. A successful preparation is not a successful recovery
result. Derived quality labels are exposed offline evaluation data thereafter.

Audit/export a completed or failed private attempt, without publishing media
or raw participant poses:

```sh
python -m wu_pipeline_v2.audit --attempt PRIVATE_ATTEMPT --output NEW_PUBLIC_AUDIT
python -m wu_pipeline_v2.audit --output NEW_PUBLIC_AUDIT
```

The complete audit checks the exact frozen plan, served-file hashes, native
label arithmetic and feature bindings; it does not independently re-encode
the videos or rerun pose aggregation. The failed audit retains the stage
sequence and file hashes without presenting partial data as confirmation.
Subsequent independent pose reaggregation must be described separately.

At this method-publication stage no v2 real-source outcome is claimed. Any
later results are published in a separate commit after their actual audit.
