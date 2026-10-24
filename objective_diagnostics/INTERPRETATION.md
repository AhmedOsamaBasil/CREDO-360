# Interpretation: objective mismatch is not solved by activating the queue

## Decision

**None of the four stateful recovery variants passed the frozen development
screen. Stop before consuming another independent test reserve.** The existing
evidence does not justify updating the manuscript to claim a successful new
recovery mechanism. This is a diagnostic result, not a proof that every possible
recovery design fails, nor an independent confirmation of any baseline's
superiority. All comparisons below use previously exposed data.

The plan/code were published as `8ddd46b` before running this comparison.
Horizon 24 and penalty strength 8 were held fixed. No post-result retuning,
new content download, manuscript edit or acknowledgment change was made.

## What the experiment actually isolates

The new package corrects the next-window decision proxy: expiry precedes
selection; signed credit remains inside the banking terminal calculation;
non-banking uses the maximum suffix sum of retained residuals. The predicted
terminal state agrees with the next observed state when feedback equals the
prediction. The old v3 code and outcomes are preserved, not silently replaced.
Consequently this new banking implementation versus old v3 is not a pure
single-factor comparison. Within this experiment, banking/non-banking and
target cap 4/5 are matched factors.

All ten policies use identical predictions, histories available at the time,
joint action sets and a stateless-Nash byte cap. Direct rolling controls need
no optimized service contract. Counterfactual HMD outcomes, future capacities
and future impairment transitions are unavailable to all controllers. The
known upcoming VoD catalogue and the currently reported capability profile
are available to all; the current profile is assumed persistent, not predicted
from the future. The exact small-system optimization is not a scalability test.

## Main result: range-normalized capability ceiling

The table reports six-seed averages of the minimum per-user time-average
quality index. Higher is better. Each catalogue has three scenes; both were
already exposed before this development experiment.

| Policy | Exposed v2 | Exposed v3 |
|---|---:|---:|
| Stateless Nash | 3.216877 | 4.207781 |
| Instantaneous max-min | 3.223608 | 4.197566 |
| Window max-min | 3.224795 | 4.208033 |
| Window Nash | 3.194316 | 4.221168 |
| Floor / banking | 3.223867 | 4.207781 |
| Floor / non-banking | 3.224959 | 4.206977 |
| Floor / scaled memoryless | 3.186819 | 4.205137 |
| Higher target / banking | 3.223290 | 4.200369 |
| Higher target / non-banking | 3.224016 | 4.201681 |
| Higher target / scaled memoryless | 3.182997 | 4.191346 |

The floor/non-banking candidate passes all development checks on exposed v2,
but fails the worst-quality comparisons on exposed v3. Its advantage over
window max-min in v2 is only 0.000164 quality-index units. The screen requires
both catalogues, not selection of whichever catalogue favors a candidate.

Against stateless Nash, the higher-target/non-banking candidate changes worst
quality by +0.007139 on v2 and -0.006099 on v3. On v3 it also loses 0.019486
against window Nash. The descriptive 95% paired-bootstrap interval for the
v3 difference versus Nash is [-0.028892, 0.012963]; versus window Nash it is
[-0.045945, 0.005364]. These are small, uncertain development differences,
not statistically established population rankings.

There are real trade-offs, not across-the-board dominance: higher-target/
non-banking reduces stall relative to Nash by 1.257291 s/user on v2 and
2.141041 s/user on v3. On v3, its mean-quality change is -0.011118 and its
fixed-target cumulative-shortfall change is -0.078705. It improves some
efficiency/shortfall measures without establishing better worst-user fairness.
It has 3.360487 s/user more stall than the matching higher-target memoryless
control, violating the preset stall guard. Every comparison, including
capacity-only and fixed-ceiling cases, is retained in the complete report.

## Why this is more informative than another failed seed expansion

### 1. Inactivity is addressed, but benefit does not follow

On exposed v3, floor/banking has positive pre-decision state on only 1.444% of
user-rounds and exactly the same 3,600 individual actions as Nash in the main
condition. Non-banking alone raises activation to 13.500%, but changes only
20/3,600 actions (0.556%).

Allowing the feasible target above four raises the mean reference from 3.962216
to 4.514967. Higher-target/non-banking reaches **88.500% active state** and
554/3,600 different actions from Nash (15.389%). Despite this substantial
mechanistic separation, its mean worst-user quality is lower. Thus lack of
activation is not a sufficient explanation for the failure of this design.

### 2. Preventing credit prepayment has small, heterogeneous effects

At the higher target, non-banking minus banking changes worst quality by
+0.000726 on v2 and +0.001313 on v3; both descriptive intervals include zero.
At the floor target the change is +0.001092 on v2 but -0.000804 on v3.
Removing stored negative credit is not a demonstrated general fairness gain.
Expiration is logged separately and must never be presented as delivered
recovery. A finite-window queue can lose deficit merely because it gets old.

### 3. Impairment severity and the quality scale remain important

A rung-1 cap removes different fractions of the sender-predicted quality
range: approximately 49.2% for ConferenceParticipant02 versus 89.1% for River01
in this sample. The new range rule removes at least half of the range for
each non-flat segment, but discrete rungs still produce content-average losses
from 56.7% to 93.5%. It is a controlled minimum-relative-loss stress rule, not
exactly equal absolute or perceptual impairment. No flat ranges occurred in
the sampled impaired-user segments; the implementation retains them if present.

Under Nash, 19.667% of v3 selected qualities hit the index ceiling of five,
versus 0.167% on v2. Clipping suppresses distinctions at high quality. Raw
VW-PSNR is reported alongside the fixed primary index; it is not substituted
post hoc to manufacture a successful primary result. Any different primary
distortion/quality objective must be specified before a new confirmation.

### 4. Simpler history-aware controls are essential, not optional

The favorable baseline changes across catalogues: window max-min is strong
on v2, while window Nash has the highest average worst-user quality on v3.
Neither is claimed universally best or new. Recovery cannot be justified
solely by beating a weaker memoryless rule while losing to these direct
controls. Jointly feasible contract machinery also adds complexity that must
earn a measurable or theoretically grounded benefit.

## Scope and next research decision

These are 360 simulated episodes / 216,000 user-rounds, not 216,000 independent
trials. Six paired seeds per exposed content pool provide development evidence
only. The repeated six-segment catalogue, five-user exact search, sender-side
quality approximation, synthetic immediately observed capability ceilings,
unmodeled controller-time overhead and clipped index limit external validity.
The common Nash byte cap also constrains every method; conclusions are about
this matched action domain, not every possible allocator. There is no new
human study or perceptual fairness validation.

The defensible next step is **not another untargeted window/penalty sweep**.
First decide the intended service objective: threshold restoration and
fairness of quality above the floor are different optimization problems.
Develop an analytical counterexample and success criterion for any proposed
new mechanism, against direct rolling Nash/max-min, before spending a new
content reserve. Alternatively, narrow the contribution to a reproducible
measurement/identifiability study of these trade-offs, subject to a separate
novelty and venue review. Neither route is automatically publication-ready.

No further method or fresh confirmation is implemented by this package.
The manuscript must not be updated as though this diagnostic passed.

## Verification

Windows and Linux each replayed all 216,000 scientific records and checked
12,120 joint-support witnesses. Both audits passed, with zero bytes above the
shared Nash cap and maximum playback conservation error 2.84e-14 s. Independent
suffix enumeration verifies banking, non-banking and expiry accounting.
Source/data/result and figure/report hashes pass. Runtime was not replayed.

The Windows regression suite passes 96 tests plus 24 subtests; the Linux suite
passes 92 plus 24 (the four Torch replay tests run on Windows). The portable
model's five tests pass on both systems. This includes 24 new diagnostic
tests for state updates, expiry, negative credit, exact small-system controls,
common byte caps and causal information access. Both generated figures were
visually inspected. Verification establishes reproducibility and implementation
consistency, not scientific superiority.
