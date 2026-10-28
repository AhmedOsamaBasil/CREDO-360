# Exposed-data feasibility admission protocol

Freeze this protocol and implementation before the complete batch. All six
scenes and 168 directed episodes are already exposed. No new media, held-out
data, learning campaign, network measurement or manuscript change is authorized.

## Unchanged contract

Use `duration_contract/PLAN.md`: actual packet media durations, rung0 event on
segments0/1, rung2 reference, half repayment, complete-segment credit by40s,
strict native micro-MSE floors for both users, 1.5MB per-round actual-file cap,
non-refilling R4 extra bytes and four recovery segments. No partial-segment
credit or stall compensation. The quality quantity remains the sampled,
reference-assisted distortion surrogate, not human QoE.

At admission, the completed initial-event account and both users' historical
reference quality are supplied as exact past ledger inputs. This is an explicit
assumption, not a new validation of telemetry accuracy or attestation. No current
or future user quality label is supplied to the admission API. Sender maps,
encoded bytes and media durations are known before requests.

## Three-way decision and witnesses

For each second and rung, bound the reference-minus-selected MSE difference by
the minimum/maximum over all72 sender tiles. Any nonnegative normalized viewport
weights lie within those bounds. Average ten samples per segment; round outward
to micro-MSE with a two-unit numerical/quantization guard. Rung2 differences are
identically zero. This does not relax the quality floor. The envelope includes
all convex weights, wider than the actual geometric viewport family.

Enumerate every resource-valid four-step joint rung path in2..5:

- **Admit conditionally:** a single path respects both users' lower-bound floors
  and its lower-bound completed credit reaches half the past debt. Select the
  minimum-extra-byte witness, then greatest certified credit, deterministic ties.
- **Reject as impossible within the fixed catalogue/resources:** even the largest
  upper-bound credit is insufficient. This optimistic rejection bound allows
  all four segments to finish, ignores quality floors and therefore does not
  infer impossibility merely from an assumed slow arrival clock.
- **Abstain:** neither certificate is available. This does not mean infeasible.
  Rejected/abstained requests receive baseline service with no recovery promise.

An accepted path is precommitted at entry; it is not an adaptive optimal policy.
Future feedback cannot invalidate already conservative spatial envelopes, but
wrong maps, ledger inputs or service assumptions can invalidate the certificate.

## Timing premise, not a measured hard guarantee

The primary conditional certificate assumes each transfer arrives no later than
the existing1.2Mbps fluid payload/0.13s overhead envelope, requests scheduled at
the resulting fixed10s-or-later boundaries. Each segment satisfies

    completion <= max(previous completion, arrival bound) + media duration + eta.

Choose **eta=0.5s per segment** as a declared engineering allowance before the
batch, not an estimated tail probability. It does not change the40s deadline.
Also report eta=0 ideal timing and eta=unbounded. Unbounded execution cannot
support an admission promise; retain possible impossibility certificates.
The previous19 measured sessions are checked retrospectively against0.5s at
every segment. Passing those samples does not establish a universal bound.
No new physical-player or network trial is performed.

## Causal point-planning controls

Use sender full-sphere MSE multiplied, per user, by the ratio of mean past
reference MSE to mean past sender reference MSE. Only completed segments0/1
enter this scale. Forecast all future rungs without future viewport observations.
No fitting/search/hyperparameter tuning is performed. Exact past debt is shared.

Compare a point-prediction minimum-byte half-target planner and three entry-time
precommitted controls: immediate credit/cost greedy, rolling Nash and max-min.
The latter two use cumulative duration-weighted positive PSNR utility, starting
with actual played historical qualities; the PSNR objective does not replace
the fixed distortion repayment target. All share forecast information, predicted
floors, action and byte budgets, timing allowance and admission criterion.
At each planning step Nash maximizes the product of the two cumulative utilities;
max-min maximizes the smaller, then their sum. No future quality feedback enters.
Evaluate both point-only admission and a spatial-certificate gate on each path.

For diagnosis only, evaluate exact future-known feasible paths under eta=0 and
0.5. They are not available to admission. Preserve earlier saved policies as
historical comparisons, not prospective admission inputs.

## Outcomes and checks

Report admission/abstention/impossibility counts, protected successes, false
promises, precision (undefined for zero admissions), capture of offline-feasible
episodes and resource costs. Report both cohorts/scenes, not just pooled results.
Never describe reject-all as useful admission performance or zero failures as a
statistical guarantee. No new holdout progression is authorized by this study.

Check every observed quality difference against the sender envelope, all resource
ledgers, independent scalar vs vector certificate extrema/witness costs, fixed
contract parity at eta=0, and past-only inputs via future-label mutations.
Synthetic tests must exercise nonvacuous admission, impossibility, abstention,
unbounded execution, false point promises, deadline boundaries, floor losses,
non-refilling reserves and changed future observations. Publish all failures.

The conditional certificate is elementary convex bounding and finite scheduling,
not a claim of new robust-control theory, calibrated probability or deployment.
