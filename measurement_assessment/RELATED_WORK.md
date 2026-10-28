# Targeted novelty and evidence review

Review date: 28 October 2026. This is a focused claim audit, **not a completed
systematic literature review**. Queries covered wireless fair-queueing
compensation/reservation, streaming MPC, viewport-prediction baselines, QoE
fairness and recent risk-aware 360-degree streaming. Primary author/publisher
sources support the claims below. No claim of exhaustive coverage, citation-count
ranking or first-ever invention is made. Bibliographic metadata is in
[references.bib](references.bib); access limitations are retained here.

| Prior work and source | Evidence inspected | Consequence for this project |
|---|---|---|
| Ng, Stoica and Zhang, INFOCOM 1998, [Packet Fair Queueing Algorithms for Wireless Networks with Location-Dependent Errors](https://www.cs.cmu.edu/~hzhang/papers/INFOCOM98a.pdf) | Author-hosted paper excerpts and [author publication list](https://www.cs.cmu.edu/~hzhang/QoS.html); direct PDF open timed out on this pass | Compensating lagging service while considering unaffected flows is established. A quality-denominated compensation account is not by itself a new scheduling principle. |
| Ramanathan and Agrawal, MobiCom 1998, [Adapting Packet Fair Queueing Algorithms to Wireless Networks](https://www.researchgate.net/publication/2513531_Adapting_Packet_Fair_Queueing_Algorithms_to_Wireless_Networks) | Author-paper text including its long-term fairness server; venue corroborated by [Stanford course bibliography](https://web.stanford.edu/class/ee384c/paper_references.html) | Reserved capacity for compensation has direct precedent. Conference/reprint DOI metadata differs across records; no unverified DOI is assigned here. |
| Yin et al., SIGCOMM 2015, [A Control-Theoretic Approach for Dynamic Adaptive Video Streaming over HTTP](https://www.xia.cs.cmu.edu/resources/Documents/Yin_sigcomm15.pdf) | Author-paper abstract/introduction excerpts | Throughput/buffer-aware MPC for streaming is established. Finite-horizon planning in this artifact is an application, not a new MPC principle. |
| Romero Rondon et al., [Revisiting Deep Architectures for Head Motion Prediction in 360-degree Videos](https://arxiv.org/abs/1911.11702), v3 (2021), TRACK | Primary abstract and author-version HTML introduction/method context; no new reproduction of TRACK | Strong simple baselines and diagnosis of metric, dataset and horizon effects already matter in this domain. Our weaker forecast error must be evaluated through decisions, not treated as proof of useful scheduling. TRACK also provides a stronger predictor; its success does not validate our negative study. |
| Guan et al., [Pano](https://arxiv.org/abs/1911.04139), 2019 | Author abstract and metadata | Pano studies perception-specific factors and evaluates perceived quality. Our coarse objective distortion map is not a substitute for that evidence and does not establish human QoE. |
| Hoßfeld et al., [A new QoE fairness index for QoE management](https://doi.org/10.1007/s41233-018-0017-x), 2018 | Publisher abstract/introduction and metadata | Resource fairness and QoE fairness are not interchangeable. Neither equal compensation nor a higher objective index alone establishes human-quality fairness. |
| Singla et al., [QoEVAVE saliency dataset documentation and citation](https://qoevave.github.io/database/docs/Saliency), QoMEX 2023 | Original dataset documentation and supplied bibliographic entry | The head traces originate from an earlier human study. Reusing them here does not mean this controller underwent a new subjective study or create independent participants for every replay. |
| Chimento and Ishac, [RFC 5136: Defining Network Capacity](https://www.rfc-editor.org/rfc/rfc5136.html), 2008 | Primary definitions and abstract | Traffic usage, capacity and available capacity are distinct. A configured reserved-service experiment is not evidence of spare capacity in a field deployment. |

## Recent overlap still requiring full-text resolution

- [FairEdge360](https://doi.org/10.3390/jimaging12060234), Journal of Imaging
  12(6), 234 (2026): primary indexed title/abstract describe uncertainty-aware
  multi-user 360-degree fairness and Nash social welfare. Direct publisher access
  was rate-limited and the PMC mirror requested browser verification on the final
  retrieval. Earlier repository notes contain more detail, but this pass is not
  a fresh complete full-text audit. Do not endorse broad guarantees from its
  abstract without checking assumptions. Our analytic Nash control is not a
  reproduction of its learning architecture.
- [Risk as a Resource: Personalized 360-degree Streaming via Adaptive Conformal
  Prediction](https://doi.org/10.1145/3798065.3798085), NOSSDAV 2026: title,
  authors and venue are in the prior discovery record; ACM access was blocked.
  Detailed novelty differentiation still requires the full paper.
- [DK-MARC: Risk-Adaptive 360-degree Streaming via Dual-Uncertainty
  Quantification and Multi-Modal Fusion](https://dblp.org/rec/conf/mmsys/KhahP26),
  MMSys 2026: discovery-level record; no accessible primary full text verified
  in this pass. Do not infer absence of compensation from an inaccessible paper.

These are unresolved review items, not evidence that the proposed contribution
is unique. Before a new submission, acquire lawful full texts and add a precise
method/assumption comparison. Foundational highly cited work is important, but
recent closest work cannot be omitted merely because it has fewer citations.

## Novelty boundary

The potentially distinctive output is the **specific reproducible diagnostic
chain** from an objective service contract, through finite feasibility and
resource/quality tradeoffs, to presentation-timed information and measured
transfer/feedback boundaries. This is a candidate application contribution,
not a demonstrated new general algorithm. To support a journal claim it needs
the robustness and operational usefulness described in the validation plan.

This assessment replaces the *current interpretation*, not the historical
files, of the July novelty draft. Later failures and mechanism equivalences
prevent carrying its original combination claim into a revised paper unchanged.
