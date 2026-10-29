# Targeted novelty check for the feasibility framing

Checked 29 October 2026. This is a focused primary-source update, not a complete
systematic review, citation-count ranking or first-ever claim. Preserve the
earlier broader [review](../measurement_assessment/RELATED_WORK.md); its
unresolved items are not resolved merely by changing the paper title.

## Established ideas that must be credited

| Work and primary source | Evidence available in this pass | Consequence for the proposed contribution |
|---|---|---|
| Ng, Stoica and Zhang, INFOCOM 1998, [Packet Fair Queueing Algorithms for Wireless Networks with Location-Dependent Errors](https://www.cs.cmu.edu/~hzhang/papers/INFOCOM98a.pdf) | Indexed author-PDF text on lagging/leading sessions and compensation; direct full-PDF fetch timed out | Past service deficits, compensation and protection of unaffected flows have direct precedent. Do not claim the debt/recovery idea as new. |
| Yin et al., SIGCOMM 2015, [A Control-Theoretic Approach for Dynamic Adaptive Video Streaming over HTTP](https://conferences.sigcomm.org/sigcomm/2015/pdf/papers/p325.pdf) | Official conference-paper text and venue metadata | Throughput/buffer-aware MPC and practical player evaluation are established. Planning and a testbed alone are not sufficient novelty. |
| Iyengar, 2005, [Robust Dynamic Programming](https://doi.org/10.1287/moor.1040.0129) | Publisher abstract and bibliographic metadata | Robust DP and the role of rectangular uncertainty are established. Our conditional response construction is an application-specific upper-bound argument, not a new general DP theorem. |
| Romero Rondon et al., [Revisiting Deep Architectures for Head Motion Prediction in 360-degree Videos](https://arxiv.org/abs/1911.11702), v3, 2021 | Primary abstract, version history and authors | Prediction evaluation already needs careful horizons and strong trajectory-only baselines. TRACK's empirical predictive success is neither reproduced nor contradicted by our failed hard speed cone. |
| Chimento and Ishac, [RFC 5136: Defining Network Capacity](https://www.rfc-editor.org/rfc/rfc5136.html), 2008 | Primary definitions of capacity, usage and available capacity | A byte entitlement or observed traffic rate is not a measured service guarantee. The prototype must distinguish provisioning assumptions from available-service measurements. |

The [official TNSM scope](https://www.comsoc.org/publications/journals/ieee-transactions-network-and-service-management)
includes service provisioning and quality assurance and encourages theoretical
and applied system contributions. This supports considering the venue for a
validated management result; it does not establish novelty or readiness.

## Recent closest work: still unresolved

- **FairEdge360**, [publisher DOI](https://doi.org/10.3390/jimaging12060234).
  Indexed publisher excerpts discuss uncertainty-aware coordination, Nash
  social welfare and joint prediction/allocation. Direct DOI and publisher
  access returned HTTP 429. This pass does not constitute a complete methods
  comparison. Do not infer that it lacks any compensation mechanism from the
  retrieved excerpts, and do not call an analytic Nash proxy a reproduction.
- **Risk as a Resource: Personalized 360-degree Streaming via Adaptive
  Conformal Prediction**, [DOI from the earlier discovery record](https://doi.org/10.1145/3798065.3798085).
  The primary full text remains inaccessible through the available retrieval.
  No new detailed claims are based on third-party snippets. This is especially
  important if a later project changes to a risk-limited formulation.
- **DK-MARC: Risk-Adaptive 360-degree Streaming via Dual-Uncertainty
  Quantification and Multi-Modal Fusion**, [earlier discovery record](https://dblp.org/rec/conf/mmsys/KhahP26).
  The record was not accessible in this pass; primary full text was not obtained.
  Its detailed relation to the proposed framework remains an open review item.

Searches used the exact three titles and primary-source queries for fair
queueing compensation, streaming MPC, robust DP and rectangularity. The
author-hosted MPC URL returned a gateway error; the official conference PDF
provided an alternative. Third-party search hits were used only to locate
primary sources, not to certify technical superiority or absence of overlap.

## Defensible distinction to test, not a settled novelty claim

The candidate contribution is the combination of a specific objective-quality
service contract, independently checked necessary/sufficient feasibility
evidence, explicit causal information order, and measured implementation
boundaries. Its concrete output is an explanation of when a promise cannot
be justified and what evidence is missing when a trace appears favorable.

The distinctive finding is not simply that a conservative model performs
poorly. It is the separation of resource/quality impossibility, known-trace
opportunity and universal-policy limits while exposing how metric and clock
choices alter the conclusion. Establishing that this adds significant value
over the closest work still requires full-text comparison and the timing/
operational validation in `VALIDATION_PLAN.md`. Negative findings plus a large
repository are not automatically a journal contribution.
