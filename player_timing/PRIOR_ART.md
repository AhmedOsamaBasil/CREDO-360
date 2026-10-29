# Focused primary-source follow-up

This is a targeted methods check during the exposed timing study, not an
exhaustive systematic review or a claim that a novel controller has emerged.

## FairEdge360: accessible primary methods

Gallena Watthage and Fernando, *Journal of Imaging*, 12(6),234,2026,
[DOI](https://doi.org/10.3390/jimaging12060234),
[institutional full text](https://strathprints.strath.ac.uk/96381/1/Watthage-Fernando-JI-2026-FairEdge360-distributed-multi-agent-reinforcement-learning.pdf).

The institutional PDF resolves the previous full-text-access gap for this
methods comparison. Sections3.2 and3.5-3.6 describe partially observed multi-user
allocation, a composite per-step utility, Nash social welfare and uncertainty-
dependent coordination. Their reviewed state/reward definitions do not specify
our fixed past-loss ledger, cumulative compensation reserve and repayment
deadline. This is a difference in research question, not proof of superiority.
Our analytic Nash comparator still does not reproduce their learned system.
Section3.8 explicitly separates streaming decision latency from physical
head-tracking-to-display latency; we must likewise keep those clocks separate.

Theorem1, Eq.(31),p.14 asserts a per-user normalized share bound. The page and
proof were visually checked. Its proof assumes a below-average user's quality
can be increased without reducing others while staying feasible. That step is
not generally available under shared resources. Do not import that claim as a
guarantee for our heterogeneous catalogue. This observation concerns the stated
mathematical implication, not the authenticity of their experimental results.

## Independent elementary counterexample

Let two users split one resource: x+y<=1, x,y>=0. Define positive utilities
Q1=1+x and Q2=1+2y. Maximizing the Nash product uses y=1-x, giving

    Q1 Q2 = (1+x)(3-2x) = 25/8 - 2(x-1/4)^2.

The unique optimum is x=1/4,y=3/4, with Q=(5/4,5/2). It is Pareto efficient:
increasing either utility requires more of that user's resource, and at this
boundary the other allocation must fall. Nevertheless Q1/(Q1+Q2)=1/3<1/2.
Thus Nash optimality and Pareto efficiency alone do not imply equal normalized
quality shares. This standard counterexample is an assumption check, NOT a new
general fairness theorem or a replacement for matched experiments. Rational
arithmetic checks are in `prior_art_check.py`.

## Risk as a Resource: full text reviewed

Nik Khah and Prakash, *Risk as a Resource: Personalized 360-degree Streaming
via Adaptive Conformal Prediction*, NOSSDAV2026,134-140.
[Publisher DOI](https://doi.org/10.1145/3798065.3798085).

All seven pages were read; the conformal-set and controller equations on
printed p137 were visually checked. Sections3.2-3.4 combine a multimodal
Transformer with LoRA personalization, recent-error spherical-cap prediction
sets, and a buffer-dependent risk parameter. Equation(4) raises alpha when
buffer health falls, reducing the requested coverage region. Thus conformal
viewport uncertainty and dynamically spending a coverage-risk budget are
already prior work; they must not be presented as a new generic contribution.

Section4 reports trace-driven evaluation using85 users/25 videos, coverage,
quality and stalls. Section5 explicitly acknowledges heuristic controller
stability and the absence of physical-HMD deployment. Its statistical coverage
objective is not a theorem about repayment of a specified past quality loss by
a wall-clock deadline while protecting another user's quality. No such
past-debt/reserve/two-user-floor contract is specified in its method.

For any later use here, the coverage assumptions would need to be checked for
the actual sequential calibration/model updates and selected playback horizon.
A reported average coverage near an average alpha target is not by itself a
conditional, joint deadline-and-repayment guarantee. This is a boundary on
transferring a claim, not an independent reanalysis of the paper's experiments.

## DK-MARC: full text reviewed

Nik Khah and Prakash, *DK-MARC: Risk-Adaptive 360-degree Streaming via
Dual-Uncertainty Quantification and Multi-Modal Fusion*, MMSys2026,61-71.
[Publisher DOI](https://doi.org/10.1145/3793853.3795747).

All eleven pages were read; printed pp63,65,69 were visually checked for the
timing, objective and profiling definitions. Sections3.1-3.2 use server-side
audio/visual/head-motion fusion and a client throughput/buffer UKF. Equations
(8)-(14) combine viewport-weighted log-rate utility, smooth risk/severity
penalties, a sampled CVaR term and an uncertainty-dependent risk weight. The
finite bitrate search uses100 belief samples; the stated5% tail uses five
samples. This is existing uncertainty-adaptive risk-sensitive streaming,
not a new concept available for us to claim.

The evaluation reports200 network-trace/video tuples, matched baselines,
an iso-input BOLA360-UKF ablation, and separate client profiling on Quest3.
The latter is reported execution profiling, not a full perceptual-validation
study. Sections4.5 and5.3 evaluate uncertainty as a risk surrogate through
bins and correlations; this is different from conformal coverage and from a
universal service promise. The paper's method does not specify our initial
past-loss ledger, nonrefilling extra-byte entitlement and protected two-user
repayment target. Its numerical results are not comparable to ours across
different datasets, clocks, objectives and action spaces.

Latency-aware viewport prediction is also already discussed explicitly in
Section3.1. Our measurements must therefore be positioned as an audit of a
particular completion contract, not discovery that playback timing matters.
The CVaR objective and smooth buffer-risk surrogate cannot be substituted for
our completed-media ledger without changing the research question.

## Claim boundaries after the full-text comparison

| Dimension | Risk as a Resource | DK-MARC | Current CREDO-360 audit |
|---|---|---|---|
| Main decision | Personalized coverage/bitrate trade-off | Uncertainty-weighted expected utility and CVaR | Whether a declared past-loss repayment commitment is feasible |
| Risk information | Recent prediction errors and conformal caps | Perceptual and network UKF beliefs | Explicit future-mask class, sender distortion maps and resource/playback contract |
| Historical deficit | Not an explicit repayment state in the presented method | Not an explicit repayment state in the presented method | Frozen initial native-MSE-duration debt |
| Other-user protection | Not the stated optimization target | Not the stated optimization target | Both-user floors and cumulative compensation-byte limit |
| Evidence here | Reviewed publication, not reproduced | Reviewed publication, not reproduced | Exposed analytical bounds and matched-path software timing; no superior controller established |

The defensible candidate distinction is a **contract-specific feasibility and
information-limit audit**, including how measured completion can invalidate an
idealized credit decision. It is not conformal prediction, uncertainty-aware
ABR, compensation queues, robust dynamic programming, or adding a debt weight
to an existing objective. Those ingredients have substantial prior work.
Differences in problem definition alone do not establish a strong new method
or sufficient journal novelty. The earlier fair-queueing/compensation and
robust-control references in `feasibility_synthesis/RELATED_WORK.md` remain
necessary; this targeted follow-up is not an exhaustive systematic review.

Cost-greedy/Nash/max-min are matched diagnostic controls, not implementations
of either reviewed system. A future performance-superiority paper would need
appropriate modern streaming baselines under a common information/resource
contract, with predictor and controller contributions separated. A feasibility
paper should instead evaluate the correctness, tightness and operational
usefulness of its certificates without claiming to beat these systems.

### Source access and provenance

Initial publisher requests returned403. On29October2026 the author supplied
the two publisher PDFs, resolving both access gaps. The full texts and rendered
review pages remain local, not redistributed in this artifact. SHA-256:

- Risk as a Resource: `6bad289f2f7bacbb524e38044701c977eb08e9a869c53f296490a98dde95cf43`.
- DK-MARC: `8f6a45b09a189c3eea5b7df49c37ff849637ac9c47ea5eeefd2a596d8f92e230`.

The statements above describe the supplied versions; their experiments were
not rerun. Bibliographic entries are provided in `references.bib`.

## Measurement API and container semantics

The [video-frame-callback specification](https://wicg.github.io/video-rvfc/)
defines compositor-submission and expected-display metadata, not measured
screen photons. Callback omissions are possible; `presentedFrames` can expose
gaps. The [FFmpeg segment documentation](https://ffmpeg.org/ffmpeg-formats.html#segment_002c-stream_005fsegment_002c-ssegment)
warns that timestamp resetting is codec/muxer dependent. Our retained smoke
failure and uniform zero-origin normalization are an implementation finding,
not a previously unknown browser or video-coding principle.
