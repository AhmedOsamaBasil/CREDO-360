# Experiment C: independent multimedia generalization

> Historical v2 results have known calibration/clock limitations. The new
> objective-target implementation is in `recovery_pilot/`. The legacy runner
> now requires `--allow-legacy-subjective-transfer`, writes to a different
> default directory, and fixes synchronized playback timing. Its subjective
> residuals still do not establish objective PSNR coverage. To reproduce the
> *original* results, use the original recorded software commit, not this fixed
> runner. No frozen v2 measurements were edited.

This testbed evaluates CREDO-360 on third-party 8K equirectangular content and
public HMD traces from the QoEVAVE Saliency Dataset. It does not redistribute
third-party media or claim a new subjective MOS.

The strengthened frozen design uses:

- six scenes: Badminton05, BuskingCity01, ConferenceCenter01, ForestWalk03,
  Lake01, and Skateboarding01;
- no-audio head-rotation traces and a deterministic subject-disjoint split;
- six H.264 representations matching the CREDO-360 rate ladder;
- measured representation segment sizes;
- a 12x6 distortion grid and a 100x100-degree viewport;
- viewport-weighted luma PSNR and SSIM (VW-PSNR and VW-SSIM);
- exact fluid processor-sharing completion times for simultaneous transfers;
- 30 paired seeds, five users, and stable/bursty/shift capacity regimes; and
- six unique calibration/debt/gate ablations, two recent-method executable
  adaptations, and CREDO-360.

The design and claim boundary were frozen before outcome inspection in
`STRENGTHENING_PROTOCOL.md`. The FairEdge360-aligned Nash comparator is an
analytic objective proxy rather than a reproduction of its trained MARL/GNN
policy. The adaptive-conformal comparator is likewise an executable
risk-control adaptation rather than a reproduction of the proprietary
single-user viewport model.

## Prepare the external artifact

The original assets are downloaded into `.external/`, which is ignored by
Git. On the WSL/RTX host:

```bash
python3 multimedia_testbed/prepare_qoevave.py
```

The script uses NVENC for six representations per content and records source hashes,
complexity, held-out subject assignments, segment sizes, and VW-PSNR under
`multimedia_testbed/artifacts/qoevave/`.

## Run and analyse

The historical commands were `python3 multimedia_testbed/run_generalization.py`
and `python3 multimedia_testbed/analyze_generalization.py`. Use
`python -m recovery_pilot.run` for the new objective-target pilot. Do not apply
the frozen v2 statistical analysis to differently designed corrected runs.

The expanded outputs are written under
`results/generalization_v2_30seed/` and
`results/generalization_v2_analysis/`. The controller debt queue uses a
declared monotonic transformation of VW-PSNR. Both reported viewport metrics
are objective engineering measures, not human opinion scores.
