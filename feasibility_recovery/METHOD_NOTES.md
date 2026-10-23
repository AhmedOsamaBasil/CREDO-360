# Feasible-reference queue: properties and limits

These are elementary implementation properties, not a new stability theorem.
The primary empirical question is delivered quality under identical constraints,
not whether a queue can be made smaller by lowering its target.

## Simultaneous feasibility

Let A(B) contain all joint representation choices with summed bytes at most B.
Before building a reference, the cheapest action for every client must fit B;
otherwise the implementation raises an explicit admission failure. An individual
quality ceiling is restricted to actions that could fit while the other clients
receive their cheapest actions. This individual upper envelope alone is not a
joint feasible target: two clients may each individually reach four but not both.

For any proposed threshold vector f, define m_i(f_i) as the minimum bytes among
user i's actions satisfying L_i(a)>=f_i. A joint action attaining f exists if
and only if sum_i m_i(f_i)<=B. The forward direction follows because each
feasible action costs at least its respective minimum; the reverse direction
uses the independent minimizers as a witness. This works with nonmonotone
representation quality and nonmonotone measured byte counts.

For f_i(h)=min(u_i,h), feasibility is monotone in h. Its boundaries occur at
the finite predicted quality levels and capped individual ceilings. Enumeration
of those thresholds therefore finds the largest capped common level and an
explicit feasible witness. This is not a continuous-convex approximation, an
independently maximized target vector, or a claim about the unknown actual
viewport outcomes. It does not force the utility optimizer to select the
witness; deviations below the reference can create subsequent debt.

## Queue properties

With gamma=0.9, q in [1,5], f in [1,4] and D(0)=0,

    D(t+1) = max(gamma*D(t) + f(t) - q(t), 0).

The bound D(t)<=3*(1-gamma^t)/(1-gamma)<=30 follows by induction. The fixed-floor
comparator has the same elementary bound, so boundedness is not a differentiator.
If q(t)>=f(t) at every round and D(0)=0, no debt accumulates. Surplus above f
repays existing debt. Repeated unavoidable fixed-floor misses can instead
accumulate fixed-target debt even when every feasible reference is met.

For an identical outcome sequence, feasible-reference debt never exceeds
fixed-target-four debt, by induction and monotonicity of the positive-part
map. This **does not compare the outcomes of two policies**, since different
queues select different actions. A smaller queue cannot prove an improvement
in fairness, shortfall, recovery or stalls. That is why all primary quality
metrics keep the same external target of four.

## Quality envelope

The predictor is deterministic sender-side full-sphere quality. One calibration
score is the maximum absolute prediction error over every measured context and
representation for one source ID. With nine exchangeable calibration panels,
the finite-sample 90% rank is ceil((9+1)*0.9)=9. A single new exchangeable panel
has the corresponding marginal coverage, including its adaptively selected
actions because the score covers the whole finite catalogue. This does not
yield simultaneous coverage across all users, conditional coverage, guarantees
for unseen contexts, or validity under arbitrary prediction/ceiling shifts.

The common radius is used to form quality bounds only. Subtracting two such
bounds is not treated as a certified gain. Even valid quality intervals would
not make the predicted feasible reference a guarantee about realized quality:
actual bandwidth may also differ from the causal forecast.

## Scope of the pilot

All candidate action vectors are enumerated exactly for five users. Random
nonmonotone test tables verify the reference against brute force, and separate
scalar enumeration verifies the allocation score. Reference construction is
permutation-equivariant. Selection is equivariant for unique optima; exact
score-and-byte ties use enumeration order and can favor different user labels.
The public data and raw actions make this limitation inspectable.

The pilot does not resolve generalization to an independent dataset, tuning
sensitivity, live player overhead, scalable approximate optimization, perceived
quality, or theoretical/literature novelty. These are not implied by passing
the predeclared descriptive progression screen.
