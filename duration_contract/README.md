# Engineering distortion/deadline contract and actual-duration playback

The [fixed protocol](PLAN.md) defines completed-segment sampled distortion-seconds
by40s, with strict native quality floors and separate timing diagnostics. It
does not choose the previously favorable PSNR account or claim human QoE.
Actions, initial event and resource allowances remain fixed; old files are not
modified. No new holdout or controller training is involved.

The new timing stage measures software decoding, frame hashing and monotonic
PTS pacing with scripted arrivals. Pixels are not rendered. This is not a
physical player/HMD experiment or a new network measurement.

## Reproduction

Public scalar evidence, no private media needed:

```console
python -m unittest duration_contract.test_core -v
python -m duration_contract.run --verify
python -m duration_contract.audit --verify
```

Full local preparation and real-time measurement need the original, hash-matched
exposed MP4 cache, FFmpeg/ffprobe and the existing Python/NumPy environment:

```console
python -m duration_contract.prepare
python -m duration_contract.run
python -m duration_contract.paced
python -m duration_contract.audit
```

Commands refuse to overwrite existing artifacts. The19-session measurement
uses at most2 concurrent sessions and takes several minutes; do not run other
compute-intensive work during timing. Metadata records the exact method, media
hashes, platform and session order. Failed/partial sessions are retained.
Results will be published after the frozen batch; passing unit tests is not
evidence of successful compensation or a deployment guarantee.
