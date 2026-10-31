# Quality recovery contracts and related methods

The recovery-contract audit concerns a specific question: can a streaming
service repay a stated fraction of past objective distortion loss by a deadline,
within a nonrefilling byte reserve, while protecting both users' reference
quality? Its distinctive evidence is the separation of recorded-trajectory
feasibility, promises over unknown future viewports, and measured completion.
It is not a new general theory of compensation, admission control, fairness,
robust dynamic programming or viewport prediction.

## Compensation and quality-aware admission

[Ng, Stoica and Zhang](https://www.cs.cmu.edu/~hzhang/papers/INFOCOM98a.pdf)
already distinguish lagging and leading sessions in wireless fair queueing,
compensate service deficits, and protect flows unaffected by errors. Thus
historical deficit and bounded compensation have direct networking precedent.
Their service quantity is packet service rather than the present sampled
distortion-duration credit, but that change alone is not an algorithmic novelty.

[Chen et al.](https://utw10503.utweb.utexas.edu/publications/2015/chen2015rate.pdf)
combine video rate adaptation with quality-aware admission. Their quality
constraints use a second-order empirical cumulative distribution, and virtual
queues track accumulated constraint violations. Admission considers predicted
quality through an adaptively controlled threshold. This is particularly close
prior work: accumulated quality shortfall and admission are already coupled.
The present contract instead fixes a past event, a repayment fraction and a
wall-clock deadline, and asks for necessary or sufficient evidence under an
explicit future-viewport class. It does not establish better QoE than Chen's
system or inherit that work's subjective validation.

## Network management and immersive streaming

[FROG](https://repository.essex.ac.uk/43811/) coordinates network-assisted
adaptive streaming using CMCD/CMSD feedback, bandwidth/path optimization and
buffer-aware quality selection. Its emulated-network evaluation and large-scale
optimization address deployment concerns beyond this two-user finite audit.
The current artifact implements neither FROG's standardized feedback interface
nor its routing and multi-server optimization. The relevant distinction is
checking the validity of a particular recovery commitment, not outperforming
FROG's quality-selection system.

The full-method comparisons for FairEdge360, Risk as a Resource and DK-MARC
are recorded in [the immersive-streaming comparison](../player_timing/PRIOR_ART.md).
They already establish uncertainty-aware coordination, adaptive conformal
viewport coverage and risk-sensitive streaming as prior art. The analytic
greedy, rolling-Nash and max-min controls in this artifact are matched diagnostic
controls, not reproductions of those learned or uncertainty-aware systems.

## Information and completion guarantees

[Iyengar](https://doi.org/10.1287/moor.1040.0129) and
[Nilim and El Ghaoui](https://people.eecs.berkeley.edu/~elghaoui/Pubs/RobMDP_OR2005.pdf)
provide established robust-control foundations. Here the model-specific step
constructs an allowed adverse mask sequence separately for each deterministic
causal whole-parent policy. The resulting Bellman value is an upper bound on a
universal promise, not a newly discovered Bellman theorem or necessarily the
exact minimax value. It relies on an unrestricted, temporally rectangular
sampled-mask class; a validated coupled or probabilistic model changes the
question.

[TRACK](https://arxiv.org/pdf/1911.11702) studies empirical head-motion prediction
from past positions and content. Predictive accuracy and universal coverage
over every allowed future are different properties. The failed sufficient
entry-cone certificates in the exposed development study do not refute TRACK
or other empirical predictors.

[RFC 5136](https://www.rfc-editor.org/rfc/rfc5136.html) distinguishes network
capacity, usage and available capacity. A declared compensation-byte allowance
does not itself provide a service-rate guarantee. Similarly, the browser
[video-frame-callback API](https://wicg.github.io/video-rvfc/) reports compositor
metadata, not measured screen photons. The current playback evidence concerns
software completion under a controlled loopback payload service, with offline
viewport quality; it is not an interactive HMD or a physical-network guarantee.

## Evidence boundary

The frozen Wu evaluation finds additional geometric rejections on three of ten
eligible clips and recorded-trajectory opportunity/universal-promise gaps on
two. It admits no pair. Consequently, its present contribution is diagnostic
decision evidence rather than a demonstrated useful positive-admission service
or superior recovery controller. A difference in contract definition is not,
by itself, proof of significant novelty.

This is a focused methods comparison, not an exhaustive systematic review or
a citation-count ranking. Bibliographic records for the additional sources are
in [references.bib](references.bib); the two supplied ACM papers' records remain
in [the original reference file](../player_timing/references.bib).
