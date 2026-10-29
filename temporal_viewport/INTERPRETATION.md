# Outcome: entry-anchor speed envelopes do not yield useful certificates

## Frozen question and outcome

Method commit `f7f2cd6fcdbb655a2aaa710dad73b41cd3109a58` preceded the new
high-rate feature derivation and all temporal-model outcomes. The seven fixed
speeds and two scene-and-identity-excluded fitting rules were not selected by
their recovery results. The original 50%/40-second, actual-duration,
native-quality-floor, R4-reserve and 1.5 MB per-round contract is unchanged.

All nine models yield **zero conditional half-repayment certificates in all
168 episodes**, under both ideal execution and the assumed additional
0.5 seconds per segment. These are failed sufficient certificates, not a new
impossibility theorem for temporally coupled trajectories or adaptive policies.
No controller performance or new human-QoE evidence is reported.

The complete 3,024 model/episode/timing rows are in
`results/exposed_v1/results.json.gz`. The primary report presents the
0.5-second condition; both conditions are retained in the machine-readable file.

| Fixed model | Recorded pair speed consistency | Conditional certificates | Full-mask samples on maximum-credit paths |
|---|---:|---:|---:|
| 5 degrees/s | 0/168 | 0/168 | 46.44% |
| 15 degrees/s | 0/168 | 0/168 | 96.95% |
| 30, 60 or 90 degrees/s, each | 0/168 | 0/168 | 100% |
| 180 degrees/s | 28/168 | 0/168 | 100% |
| 360 degrees/s | 138/168 | 0/168 | 100% |
| Cross-fit 95th-percentile maximum | 154/168 | 0/168 | 100% |
| Cross-fit training maximum | 164/168 | 0/168 | 100% |

The table uses the primary 0.5-second timing assumption. A pair is consistent
only if both users' recorded adjacent-sample rates after the entry anchor do
not exceed the candidate bound. This diagnostic concerns the original source
clock, not measured behavior during network stalls. It does not establish
continuous-time coverage, population coverage or a deployment guarantee.

## Why the fitted envelopes lose information

The fitted 95th-percentile bounds range from 398.27 to 523.32 degrees/s;
training maxima range from 566.52 to 927.58 degrees/s. Each fit uses the other
five scenes and excludes both episode identities: 130 training trajectories.
The percentile is an empirical quantile of trajectory maxima, not conformal
calibration or a 95% joint guarantee. The maximum also fails to cover four
recorded pairs. Neither fitting rule establishes a hard physiological limit.

Separately labeled post-outcome diagnostics show that the conservative
entry-anchor cone permits every one of the 216 angular viewport masks after:

- 0.3053--0.4206 seconds for the cross-fit percentile model;
- 0.1660--0.2949 seconds for the cross-fit maximum model.

These times are measured from the last source pose, not from request entry.
That pose is already at least 0.5 seconds old at the entry decision. Thus every
future sample cone is already uninformative about mask identity for these
models. All 4,844 unique timing cells for each fitted model in the primary
condition contain all masks at all ten sample times and reproduce the prior
unrestricted geometric lower bounds exactly. Even 30 degrees/s gives the same
lower values in all those cells, although some of its sets are not yet full.

The primary mean maximum certified credit is 7.9781% of initial loss for
15 degrees/s and all broader models, compared with 9.2121% at 5 degrees/s.
The narrower model's modest improvement is not usable evidence: its source
speed check fails for every pair and it still certifies no half targets.
Ideal execution raises the corresponding means to 8.6081% and 10.0096%,
without creating a certificate. No favorable speed is chosen after evaluation.

These are bounds from independently minimized sample cones. They may include
mask sequences that no single speed-limited trajectory can realize. The
audit therefore diagnoses this sufficient entry-cone construction, not the
exact optimum under the coupled speed model. The earlier unrestricted
adaptive-policy upper bound cannot simply be transferred to a smaller
temporal uncertainty class.

## Why high-rate traces matter

The audit reads 504,159 observations across 168 existing trajectories: the
same 28 source identities across six scenes, not 168 independent people.
Median sampling interval is 0.02 seconds and minimum interval is 0.0199 seconds.
No identical-timestamp duplicates were removed and no inconvenient outliers
were filtered. Conflicting duplicate timestamps would have aborted derivation.

Every trajectory has a larger maximum sampled forward-direction change rate
at source resolution than in the old 1 Hz sample set. The median ratio is
2.3488 and the maximum ratio is 7.4727. Whole-trajectory high-rate maxima range
from 63.7533 to 927.5820 degrees/s. These are rates in recorded samples, not
validated physiological peak speeds; tracking artifacts are not ruled out.
Even complete sampled consistency cannot exclude faster motion between samples.
The result shows why the coarse quality-sampling cadence cannot certify a
hard movement envelope. It does not validate the original tracking device.

## Scope and next decision

All scenes, people and outcomes are exposed development data. No new media,
holdout, participant, network measurement, pixel rendering or HMD experiment
was used. Public artifacts contain derived scalar summaries and quality-bound
tables; original poses and entry anchors remain local. Source-clock movement
is not an observed stalled-playback clock. Service capacity, execution bounds,
entry-pose availability and exact past debt remain explicit assumptions.

Spherical reachability and empirical speed thresholds are not claimed as new
general methods. The contribution of this audit is a reproducible explanation
of why this particular coverage/usefulness trade-off blocks a useful promise.
It is not evidence of a novel successful recovery controller.

A next positive-mechanism study would need a justified, time-horizon-specific
uncertainty model, or a separately specified later-observation/action contract,
before using another holdout. A probabilistic model would explicitly replace
the universal promise with a risk-limited claim and require group-aware
calibration and independent validation. Alternatively, the existing evidence
can support a feasibility/measurement framing. None of these changes is made
by this audit; neither the manuscript nor its acknowledgment was edited.
