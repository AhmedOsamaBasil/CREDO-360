# Feasibility and measurement contribution assessment

Assessment date: 28 October 2026. **Post-hoc synthesis, not a new experiment,
preregistered claim, manuscript revision or completed systematic review.**

## Decision

There is a coherent research question here, but **the current evidence is not
ready for journal resubmission merely by changing the framing**. Stop treating
successive recovery-controller variants as the main contribution. The latest
primary controller fails its declared development screen and loses to matched
cost-greedy on mean unpaid loss in both exposed cohorts.

The defensible direction is a bounded analytical and measurement study:

> When is compensation for an earlier objective viewport-quality shortfall
> feasible, what resource and other-user quality costs does it require, and
> which opportunities remain usable when feedback follows actual presentation?

A possible working title is **When Can Objective Viewport-Quality Loss Be
Compensated? Feasibility, Resource Budgets, and Feedback Timing in Immersive
Streaming**. This is a proposal, not a change to the submitted manuscript.

## Candidate contributions, with limits

1. **Auditable feasibility certificates.** Exact witnesses and infeasibility
   results for a finite representation catalogue, explicit donor protection,
   action limits and cumulative extra-byte reserve. The application-specific
   frontier and its interpretation are potentially useful; enumeration, dynamic
   programming, token accounting and robust optimization are not new principles.
2. **A separation of compensation, quality fairness and information timing.**
   Lower uncompensated loss need not improve worst-user quality; more peak
   allowance can worsen a myopic policy under a fixed cumulative reserve;
   improved forecast accuracy need not improve scheduling. These are observed
   cases and familiar possible phenomena, not universal new theorems.
3. **An inspectable implementation boundary.** Sender reference-distortion maps,
   compact viewport reports, measured selected-file transfers, and causal
   playback bookkeeping make the assumptions testable. Completed reports have
   loopback measurements; incremental reports and playback remain simulated.
   This is a research prototype, not an HMD-validated streaming system.

The combination may support a useful methods/measurement paper **if** robustness
and management usefulness survive the validation gates below. Novelty is not
established just because no retrieved title uses the same terminology. Prior
service compensation, reserved compensation, streaming MPC and fairness research
are explicitly acknowledged in [RELATED_WORK.md](RELATED_WORK.md).

## What the existing evidence says

| Evidence layer | Supported observation | Boundary |
|---|---|---|
| Relative encoded-payload frontier | No half-repayment at 1x or 2x across the audited donor slices; 147/168 at 3x with zero donor loss; 11 episodes remain impossible at any resource | Four recovery segments and fixed objective index; future known; no cumulative reserve in this layer |
| Finite extra-byte reserve | At reserve fraction 1, greedy half-repayments fall from 90 to 62 when the peak factor rises from 3 to 4; offline remains 97 | A particular myopic rule and catalogue, not harm from capacity itself; payload accounting |
| Fixed 1.5 MB actual-file cap | Strict offline bound reaches 96/168; adding the diagnostic per-episode Nash-minus-0.02 quality guard gives 95/168 | Different contract from the relative frontier; future-known upper bound, not realizable causal gain |
| Causal prefix playback | Primary unpaid 0.375974 vs completed-only 0.380411 and cost-greedy 0.369185 | Simulation; all three values from matched 80 ms cells; lower is better |
| Waiting for completed reports | Mean modeled stall 16.220 s vs completed-only 6.970 s | Cold-start, four-segment design; not an impossibility claim about all buffering strategies |
| Measured TCP transfers | 96/96 nominal selected-transfer deadlines met; reduced-service stress misses 12/24 | Reserved emulator service, six fixed directed pairs, no physical video rendering |
| Completed-report implementation | 1,008 loopback reports; substituting reconstructed credit changes none of 4,704 prior actions | Sender reference assisted; coarse metric parity is not perceptual validation |

The source-bound [generated register](results/assessment_v1/summary.json) retains
all matched policy cells, cohort contrasts, timing results and source hashes.
The [compact generated report](results/assessment_v1/REPORT.md) is regenerated
from the same inputs. These numbers are not pooled into one unified experiment.

There are six exposed scenes and 168 directed episodes reusing 28 participant
identifiers. Neither 1,512 policy runs nor thousands of decisions increases the
number of independent people or scenes. No new uncertainty interval or
significance claim is introduced by this synthesis.

## What must not be claimed

- A validated superior recovery controller, successful calibrated admission,
  human QoE improvement, or a new general scheduling/optimization principle.
- That favorable offline paths imply a causal policy can identify them in time.
- That an entitlement to extra bytes supplies future physical capacity, or that
  observed traffic traces measure spare bandwidth.
- That compensating an accounting deficit erases previously experienced
  distortion. Compensation is an explicitly chosen service objective.
- That older objective proxies reproduce named contemporary learning systems.
- That passing software tests repairs a failed scientific progression screen.

The older `literature/NOVELTY_ASSESSMENT_DRAFT.md` and July literature synthesis
are historical design documents. Their proposed surviving novelty is **not the
current conclusion** after the later mechanism and timing audits. They remain
unchanged for provenance; this assessment supplies the current narrower view.

## Minimum work before reconsidering a journal submission

See [VALIDATION_PLAN.md](VALIDATION_PLAN.md). First investigate metric/contract
and segment-timescale sensitivity on exposed data. Only then lock a confirmatory
study using genuinely independent content/identities. A further controller
tuning sweep is not the recommended next step.

A prospective paper would proceed through: (1) the service question and related
work; (2) exact contract and objective; (3) finite feasibility certificates;
(4) causal information and playback timing; (5) measurements and robustness;
(6) management implications and limits. The many historical failed variants
belong in the evidence trail, not as separate claimed contributions.

TNSM remains a *conditional* venue possibility for a genuine network/service
management contribution, not an acceptance prediction. Its official guidance
evaluates significance, novelty and usefulness to its readership:
[TNSM policies and guidelines](https://www.comsoc.org/publications/journals/ieee-tnsm/policies-guidelines).
No resubmission, journal contact or manuscript update is made here.

## Reproduce this assessment

From the repository root, with Python 3.12 or newer and no new dependencies:

```console
python -m measurement_assessment.synthesize
python -m unittest measurement_assessment.test_synthesize -v
```

The verifier reloads seven frozen JSON artifacts, reaggregates the 1,512 saved
episode rows, checks agreement with the original summaries, and compares the
published synthesis. Hashes bind **canonical decoded JSON**, permitting gzip
and text newline differences without ignoring changed values. It does not rerun
the original controllers or replace their independent scientific audits.
`--build` creates the output once and refuses to overwrite an existing directory.
