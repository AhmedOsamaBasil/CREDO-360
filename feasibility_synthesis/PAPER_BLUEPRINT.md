# Proposed paper: feasibility and information limits

This is a technical blueprint, not an Overleaf revision, submission or claim
of journal readiness. The current manuscript remains unchanged.

## Positioning

Working title: **Feasibility and Information Limits of Viewport-Quality
Recovery in Two-User Immersive Streaming**.

Use the explicit two-user scope until the exact analysis is extended and
validated. Earlier multi-user experiments with a different controller do not
establish scalability here. Do not lead with calibrated recovery, human QoE,
or an unvalidated superior scheduler. Compensation is a declared future
distortion account; it does not undo an earlier viewing experience.

The central management question is whether a quality-recovery service can
responsibly offer a particular commitment under a specified information,
resource and playback contract. A useful answer may be rejection with a
checkable reason rather than a new allocation algorithm.

## Three candidate contributions

1. **A finite-contract feasibility audit.** A reproducible accounting model
   binds the initial deficit, completed-segment credit, other-user protection,
   cumulative extra bytes and deadline. It distinguishes exact known-trace
   optima, optimistic rejection bounds and sufficient online certificates.
   The application-specific diagnosis is the candidate contribution, not
   enumeration, quality debt or constrained optimization by itself.
2. **A constructive information-limit analysis.** For deterministic causal
   whole-segment choices and temporally unrestricted sampled masks, a
   per-policy counterexample establishes a conditional upper limit. Exact
   synthetic games also show where temporal coupling or observation before
   commitment makes feedback useful. Neither rectangular robust control nor
   Bellman recursion is claimed as a new theorem.
3. **A measurement and model-validity audit.** Metric choice, actual media
   duration, completion timing and viewport uncertainty change what can be
   promised. Existing selected-transfer/feedback measurements and separate
   decoder/software-pacing measurements identify implementation boundaries.
   The exposed speed-model failure explains why one simple narrowing of the
   uncertainty set is not useful. This is not end-to-end HMD validation.

The episode-level synthesis provides an inspectable connection among these
layers. It does not turn their assumptions into measured deployment facts.
Novelty remains conditional on full comparison with closest recent work and
the additional validation below.

## Reader sequence and evidence map

| Section | Reader question | Main evidence and cautions |
|---|---|---|
| Introduction | Why promise recovery rather than only maximize current quality? | Concrete operator commitment; summarize negative findings without a controller-superiority claim |
| Related work | What is established already? | Fair-queueing compensation, streaming MPC, robust DP and uncertainty-aware streaming; unresolved full texts explicitly tracked |
| Contract and system | What exactly counts as recovery? | Native MSE-duration account, actual PTS durations, completed-only 40-second credit, 50% target, two floors, R4 reserve and 1.5 MB cap |
| Feasibility methods | Which statements are sufficient or necessary? | Known-trace exact oracle; optimistic upper rejection; conservative lower certificate; distinguish information sets and rounding guards |
| Information limits | Can feedback rescue the universal promise? | Per-policy response construction, floor-relaxed upper bound, exact counterexamples where adaptation helps |
| Experimental and measurement methods | What was actually executed? | Separate trace replay, selected TCP transfers, loopback reports and decode/pacing; measured vs assumed clocks and service |
| Results | Which conclusion survives each check? | Metric sensitivity first; 134/27/7 partition; all-168 conditional policy limit; zero temporal certificates; no pooled significance |
| Implications and limits | What can a service manager do with this? | Reject unsupported promises; separate resource insufficiency from unresolved uncertainty; expose required evidence for a different contract |
| Conclusion | What is learned, and what is not? | Application-specific feasibility diagnosis; no universal streaming impossibility, perceptual compensation or deployed admission guarantee |

## The critical logical distinctions

For credit C, deficit D and admissible futures W, the following are not
interchangeable:

- Known-trace opportunity: there exists an action path a with
  C(a, observed_future) >= D/2 under the original floors.
- Universal causal promise: there exists a causal policy pi such that for
  every w in W, C(pi,w) >= D/2 under the original floors.
- Adaptive rejection: for every deterministic pi, there exists a possibly
  policy-specific w_pi with C(pi,w_pi) <= U < D/2. The upper optimization
  relaxes floors, so failure still rejects the stricter contract.
- Failed sufficient certificate: the best conservative lower bound is below
  D/2. This alone says neither that the true optimum is below D/2 nor that
  every policy fails under a smaller temporally coupled W.

Thus the 27 recorded-trace feasible cases and the 168 unrestricted universal
failures are compatible. The seven remaining geometric abstentions with
unfavorable recorded traces are not seven proofs of all-trajectory impossibility.
Use explicit statements of these quantifiers beside the corresponding figure
or table, rather than only in an appendix.

## Presentation plan

Retain a concise contract/notation table, a diagram of request commitment,
transfer, playback and report arrival, and the generated scene-level diagnosis
table. Reuse the existing metric-sensitivity, adaptive-ceiling and temporal-model
figures with their limitations intact. Keep physical-unit timing and resource
axes. Do not combine differing metrics/contracts into a single bar chart.

Place exhaustive historical controller searches, complete certificate records,
raw timing logs and proof/test detail in the reproducibility artifact or
supplement. The manuscript should report the failed comparisons necessary to
explain the final question, not narrate every development iteration.

No ten-page rule is assumed for a new venue. TNSM is only a conditional target:
its [official scope](https://www.comsoc.org/publications/journals/ieee-transactions-network-and-service-management)
includes service provisioning, reliability/quality assurance and applied
system studies, while requiring significant management contributions. This is
a fit argument, not an acceptance prediction. Verify the eventual venue's
current instructions before formatting or submission.
