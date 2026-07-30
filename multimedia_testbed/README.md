# Experiment C: independent multimedia generalization

This testbed evaluates CREDO-360 on third-party 8K equirectangular content and
public HMD traces from the QoEVAVE Saliency Dataset. It does not redistribute
third-party media or claim a new subjective MOS.

The frozen design uses:

- Badminton05, ForestWalk03, and Skateboarding01;
- no-audio head-rotation traces and a deterministic subject-disjoint split;
- six H.264 representations matching the CREDO-360 rate ladder;
- measured representation segment sizes;
- a 12x6 distortion grid and a 100x100-degree viewport;
- viewport-weighted luma PSNR (VW-PSNR);
- exact fluid processor-sharing completion times for simultaneous transfers;
- 30 paired seeds, five users, and stable/bursty/shift capacity regimes; and
- conformal Nash, ungated resource debt, and CREDO-360.

## Prepare the external artifact

The original assets are downloaded into `.external/`, which is ignored by
Git. On the WSL/RTX host:

```bash
python3 multimedia_testbed/prepare_qoevave.py
```

The script uses NVENC for the 18 representations and records source hashes,
complexity, held-out subject assignments, segment sizes, and VW-PSNR under
`multimedia_testbed/artifacts/qoevave/`.

## Run and analyse

```bash
python3 multimedia_testbed/run_generalization.py
python3 multimedia_testbed/analyze_generalization.py
```

The outcome quality index is a declared monotonic transformation of VW-PSNR.
It is an objective engineering index, not a human opinion score.
