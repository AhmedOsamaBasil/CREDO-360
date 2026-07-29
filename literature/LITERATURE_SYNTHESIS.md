# Literature synthesis for CREDO-360

Search date: **28 July 2026**. OpenAlex citation counts below are dated
discovery metadata and will change over time.

## Established foundations

| Foundation | Role | OpenAlex cited-by count |
|---|---|---:|
| Pensieve (SIGCOMM 2017) | Learned adaptive bitrate control | 1,340 |
| MPC for DASH (SIGCOMM 2015) | Predictive bitrate control | 1,002 |
| HAS QoE survey (IEEE ComST 2014) | QoE measurement/model taxonomy | 812 |
| FESTIVE (CoNEXT 2012) | Multi-client fairness/stability | 684 |
| BOLA (INFOCOM 2016) | Buffer-based utility optimization | 496 |
| QFF (ACM FhMN 2013) | Network-wide QoE fairness | 239 |
| QoE management survey (IEEE ComST 2019) | Network QoE control synthesis | 232 |

These publications support the problem framing and baseline choices. Citation
count is not used to infer novelty.

## Evidence streams

### Adaptive streaming and QoE

Pensieve, MPC, BOLA, and FESTIVE establish that bitrate decisions must trade
visual utility, rebuffering, switching, and multi-client stability. Video ATLAS
and LSTM-QoE show that temporal impairments and memory matter for QoE
prediction. The author’s 2022 programmable-network framework provides the
closest implementation lineage for obtaining QoE/network observations.

### Network-wide fairness

QFF, FINEAS, UFair, the QoE fairness index, and Q2oE invalidate any broad claim
that QoE-fair allocation is new. Most evaluate point-valued QoE utility,
instantaneous/aggregate fairness, or preference. The current evidence table did
not identify a method that combines calibrated QoE lower bounds with a carried
per-user deprivation obligation.

Zhu et al. (IEEE Network 2015, DOI `10.1109/MNET.2015.7340418`) further
invalidate a broad “first temporal queue” claim: their D2D video allocator uses
a per-user virtual queue to enforce long-term playback fluency. The remaining
difference is narrower—realized QoE shortfall coupled to a coverage-calibrated
counterfactual gain, with debt spent only where an action can improve the
calibrated QoE floor.

### Immersive streaming uncertainty

Flare, Pano, VAS360, and probabilistic viewport streaming establish the
viewport-prediction and tile/rate-allocation problem. Three 2026 papers sharply
limit novelty:

- **FairEdge360** already supplies uncertainty-aware, QoE-fair multi-user
  360-degree edge coordination.
- **Risk as a Resource** already supplies personalized split/adaptive conformal
  viewport prediction and online risk control.
- **DK-MARC** already supplies risk-adaptive dual-uncertainty 360-degree
  streaming.

Therefore, neither “uncertainty-aware immersive streaming” nor “conformal
360-degree streaming” is novel.

### Calibration under shift

Adaptive Conformal Inference provides a long-run empirical coverage result for
its online alpha update under the paper’s conditions. Conformal calibration in
wireless systems establishes transferability to communication decisions. It is
not valid to claim per-time distribution-free marginal coverage under arbitrary
shift, or to transfer the ACI theorem to a different rolling-window update.

## Resulting research gap

The surviving intersection is:

> shared-link multi-user immersive allocation driven by online calibrated QoE
> lower bounds, coupled to an explicit temporal QoE-deprivation state.

This gap is technically meaningful because each component changes the decision:
calibration controls prediction risk; debt distinguishes persistent deprivation
from snapshot dispersion; and opportunity-aware debt avoids spending capacity
where the calibrated QoE model predicts no recoverable gain.

## Primary references

- Pensieve: DOI `10.1145/3098822.3098843`
- MPC: DOI `10.1145/2785956.2787486`
- FESTIVE: DOI `10.1145/2413176.2413189`
- BOLA: DOI `10.1109/INFOCOM.2016.7524428`
- QFF: DOI `10.1145/2491172.2491181`
- UFair: DOI `10.1109/JSAC.2016.2577318`
- QoE fairness index: DOI `10.1007/s41233-018-0017-x`
- Flare: DOI `10.1145/3241539.3241565`
- VAS360: DOI `10.1109/ICMEW.2019.00062`
- FairEdge360: DOI `10.3390/jimaging12060234`
- Risk as a Resource: DOI `10.1145/3798065.3798085`
- Adaptive Conformal Inference: NeurIPS 2021 official proceedings URL in
  `included_studies.csv`

## Review limitations

This is a reproducible, evidence-backed working review, not yet a publication-
complete SLR. Full text for Risk as a Resource and DK-MARC was not openly
accessible; forward/backward snowballing and explicit exclusion logging remain
to be completed. An “absolute novelty” claim is epistemically impossible; the
qualified claim in `NOVELTY_ASSESSMENT_DRAFT.md` is the strongest supportable
wording at this stage.
