# Conditional certificate and rejection logic

This is an elementary finite-model certificate, not a new scheduling theorem.

Let z(s,k,r) be the sender's squared-error map at sampled second s, tile k and
rung r. The modeled viewport weights w(s,k) are nonnegative and sum to one.
For reference rung2, write delta(s,k,r) = z(s,k,2)-z(s,k,r). Then

    min_k delta(s,k,r) <= sum_k w(s,k) delta(s,k,r)
                         <= max_k delta(s,k,r).

Averaging ten sampled seconds gives segment lower/upper bounds. Reference and
selected qualities use the same viewport weights. Outward rounding and a
two-micro-MSE guard accommodate independently quantized reference/selected
values and floating arithmetic on finite 8-bit-error maps. Rung2 is identically
zero, not a negative guarded value. All empirical metric differences are checked
against these bounds. Bounds are on the existing sampled surrogate, not a
physical renderer or unmeasured perceptual error.

## Admission implication

For one resource-valid precommitted path p, let l(t,u,p) be a segment lower
difference and E(t,u,p) the recursively computed completion upper bound.
If all l >= 0 and

    sum_t d(t) max(l(t,recipient,p),0) 1[E(t,recipient,p)<=40s] >= D/2,

then every modeled viewport sequence satisfies both quality floors and the
half-repayment requirement, provided the announced past debt D is correct and
the transfer/execution assumptions hold. Proof: convex bounding gives each
quality inequality; monotonicity of max establishes the completion upper bound
by induction; sum the nonnegative completed credits. Quality protection is
checked for all four selected segments, including those completed after40s.

This sufficient test may be conservative: independent per-second tile extrema
need not correspond to a geometrically realizable viewport sequence. Failure to
find a certified path is not proof that no causal/adaptive policy could work.
The algorithm chooses the lowest-extra-byte passing witness, not a new optimal
online policy. The exact finite search and an independent scalar traversal check
the certificate extrema and minimum witness cost.

## Impossibility implication

For each resource-valid path sum positive upper differences over all four media
durations, even if they would finish too late, and ignore all quality floors.
If the largest such sum is less than D/2, no valid path can meet the target.
This relaxation makes the rejection valid without treating an upper arrival
bound as a lower bound. It remains relative to the fixed media catalogue,
structural rungs2..5, byte constraints and sampled quality contract. A larger
budget, different encoding, target or action space is a different contract.

Otherwise, absent a sufficient witness, return **abstain**, not impossible.
If execution latency is unbounded, no time-limited admission certificate follows;
the quality/resource impossibility check can still apply. With zero admissions,
precision is undefined and empirical usefulness has not been established.

## Engineering assumptions and validation limits

The0.5s execution allowance is an assumption checked against earlier exposed
measurements, not a measured universal maximum, quantile or reliability level.
Reserved-service validation does not cover arbitrary OS stalls, contention,
wireless loss or remote rendering. Even a nonvacuous successful catalogue test
would not establish an unconditional deployed guarantee. The API uses known
sender metadata and completed-event ledger inputs only; future labels are
restricted to offline evaluation. No statistical coverage or fresh-test claim
is made from the exposed cohort.
