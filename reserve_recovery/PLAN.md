# Fixed scope: headroom and a finite cumulative reserve

No new holdout, media download, human experiment or manuscript revision.
All previous hashed artifacts remain immutable. Publish this plan and its
implementation before the complete exposed-catalogue calculation.

## Evidence and physical meaning

Inventory the existing capacity evidence: captured traffic is not unused path
capacity; configured Mininet links and synthetic replay profiles are not field
measurements. Convert encoded demand into payload bytes and Mbit/s over each
10-second slot. Do not label a convenient peak multiplier realistic without
measuring the residual service available after other traffic and overhead.

Separate two constraints: a fixed, non-refilling episode reserve R (bytes of
additional service entitlement) and contemporaneous per-slot payload capacity.
Debit max(selected bytes - original reference bytes,0). No refunds from a
low-rate action, no stockpiling of elapsed idle bandwidth, no advance credit
for future refill. Baseline infeasibility is an explicit error, not hidden
reference relaxation. Retain the event-quality debt and half-repayment target.

## Analytical tests

Use exact rational arithmetic and integral actions. Enumerate finite causal
policies over declared possible future observations; equal observation prefixes
require equal actions. Select the deterministic policy minimizing worst
absolute unpaid fraction, with sum of scenario losses, maximum reserve spend,
sum reserve spend and stable enumeration order as tie-breaks. Sum is not a
probabilistic expectation. Admit the half-repayment service only if every
scenario satisfies unpaid fraction <=1/2. Keep best-effort output and explicit
infeasibility otherwise. No randomization can evade this pathwise requirement.

Compare with rolling Nash, rolling lexicographic max-min and greedy recovery
under identical current menus, histories, byte caps, reserve and donor floors.
The future set is declared information, not secretly withheld; rolling rules
do not exploit it by definition. Include future-known oracle and independent
robust Bellman recursion to separate information from optimization.

Retain favorable bounded-future cases, disappearing opportunities, nonbinding
reserve, zero reserve, insufficient instantaneous capacity, delayed revelation,
and a causal admission gap despite each future being feasible offline. An
out-of-model disappearance must flag model breach and preserve physical/byte
constraints without claiming the recovery target still holds. No fitted or
calibrated opportunity model is introduced.

## Exposed-data finite-catalogue calculation

Keep the original168 episodes and six previously exposed scenes. Original
impairment loss, rung2 references, .001 quality units and four recovery slots
are unchanged. Enforce zero donor loss; examine all floor-respecting joint rungs.
Peak byte factors:1,2,3,4. Reserve fractions of summed four-slot baseline bytes:
0,1/4,1/2,1,2. These are sensitivities, not measured service commitments.

An exact multiple-choice gain/cost dynamic program finds minimum additional
bytes needed for half-repayment and the maximum recovery at each reserve.
No mixing of action expectations. Compare all fixed grid cells with rolling
Nash/max-min/greedy under the same masks and reserve. Current quality is exact
and future outcomes are used ONLY by the explicitly offline oracle. Rolling
window24 contains the two actual impairment observations plus this four-slot
episode; no observation expires in this short audit.

Report all infeasible episodes, per-scene/cohort counts, minimum-reserve
distributions conditional on feasible episodes, fixed-grid absolute loss,
target attainment, donor loss, reserve spend and quality trade-offs. Translate
minimum-reserve witnesses to additional MB, total payload Mbit/s and extra
Mbit/s; never present this witness as minimizing peak rate too. No p-values,
independence assumptions, new validation claim or controller-success screen.

## Verification

Independent brute-force small cases for the cost DP, robust Bellman versus
complete causal enumeration, causal-prefix tests, no-refund and separate
capacity checks, exact debt and reserve conservation. Full data/source/result
hashes, Windows/Linux regeneration, broad regression, fresh Git archive check
and GitHub publication. The local workspace guide is not a public artifact.
