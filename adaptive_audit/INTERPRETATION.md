# Feedback does not rescue the universal promise in this model

The analytical method, exact-game tests and protocol were published as
`556d3e9` before applying the new audit to the six exposed scenes. No earlier
method/result was edited. No new traces, human observations, timed trial,
learned model, fresh holdout or manuscript change was involved.

## Finding

The universal half-repayment promise is ruled out for **all 168 episodes**
for the defined class of deterministic causal whole-segment policies. This
holds under both ideal execution and the primary 0.5s-per-segment allowance.
The largest episode-specific upper bound is **32.1636191% of the past debt**,
below the unchanged 50% target, even with both quality floors removed.

| Exposed scene | Episodes | Largest episode-specific upper bound |
|---|---:|---:|
| BuskingUnderpass05 | 28 | 2.7243% |
| Cheerleading01 | 28 | 4.1596% |
| ConferenceParticipant02 | 28 | 1.0663% |
| ParkFountains01 | 28 | 20.7506% |
| River01 | 28 | 32.1636% |
| Train01 | 28 | 3.1286% |

These are ceilings on a **worst-case universal guarantee**, not measured
repayment percentages, prediction intervals or optimal observed-trace results.
The original strict floors remain part of the service contract. Removing them
in an upper bound only strengthens the negative conclusion; no floor was
relaxed to manufacture a successful admission.

## What is new relative to the previous diagnostic

Previously, a separate adverse geometric sequence existed for each fixed
action path. That alone did not prove impossibility for adaptive policies.
This audit constructs a causal response rule: after the policy commits its
recipient rung, a valid sequence of future geometric masks is selected for
that segment. For each deterministic policy the recursive construction yields
one complete admissible sequence. The proof then bounds every such policy by
a resource/clock Bellman recursion with an independent full-path cross-check.
This closes the fixed-plan/adaptive quantifier gap for the specified model.

The near equality with the previous 32.16362299% generous bound is expected:
the tiny difference is native rounding, not a new controller gain. The proof,
not a numerical comparison alone, justifies extending the scope. The response
rule is a mathematical counterexample construction, not a behavioral model
claiming that real users respond adversarially to bitrate decisions.

## Why feedback does not change this particular guarantee

Whole-segment rungs are committed before their viewport samples are played.
Past completed or partial viewport reports can affect later decisions, but
the uncertainty set still permits all 216 masks at every later sample. Hence
the past does not exclude the adverse future responses. Additional waiting
charges elapsed time without shrinking that uncertainty set.

The exact-game checks explicitly preserve the opposite cases: informative
past signals improve worst-case reward from 0 to 1 in a temporally coupled
example, and revealing the current state before commitment also changes the
answer from 0 to 1. Without that informative signal the improvement disappears.
These are synthetic logical examples, not alternative experiments or target
changes. They show why a validated temporal model or different information
order would require a new analysis rather than inheriting this conclusion.

## Boundaries and next decision

The result is conditional on the existing coarse angular-window geometry,
unrestricted future sampled poses, whole-segment irreversible actions, past
debt correctness and specified resource/timing model. It is not a statement
that no adaptive streaming method can work, no observed trace can recover,
or humans cannot benefit. The earlier 27 observed River01 traces feasible
offline remain compatible with this universal-promise impossibility result.
No private-randomized expected-risk guarantee is evaluated.

The deterministic bound covers rolling Nash, max-min, greedy and learned
policies that obey this information/action contract, but is not a new measured
comparison of their performance. Bellman recursion and robust uncertainty
analysis are established methods; references and the complete argument are
in [THEORY.md](THEORY.md). There is no new optimal-scheduler claim.

Further feedback-only tuning under the same unrestricted uncertainty class
cannot establish the desired universal promise. A useful next direction
requires an explicit choice: justify and validate a narrower temporal or
probabilistic uncertainty model, change the service/action contract for
engineering reasons, or develop a scoped feasibility/measurement contribution.
None is automatically validated here; another fresh holdout is premature.
