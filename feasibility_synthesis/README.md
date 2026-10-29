# Feasibility and measurement synthesis

This is the current contribution assessment after the metric, timing,
admission, geometric, adaptive-policy and temporal-model audits. It is a
**post-outcome reconciliation**, not a new experiment or a successful recovery
controller. It supplements the earlier frozen `measurement_assessment/`.

The research question is now:

> Under an explicit objective-quality, resource and playback-deadline contract,
> when can an operator rule out recovery, and what prevents favorable
> known-trace opportunities from supporting a universal promise?

## What is now joined and checked

Seven frozen artifacts are hash-verified. The software matches episode IDs,
past-loss ledgers and timing modes across them, checks every relevant cell for
duplicates/missing values, and keeps evidence types separate. All 168 directed
episodes are reused development cases from six scenes and 28 participant IDs.

| Diagnosis under the fixed contract | Episodes | Interpretation |
|---|---:|---|
| Optimistic quality/resource upper bound below target | 134 | Conditional finite-contract infeasibility, not merely failure of one planner |
| Recorded-trace optimum reaches target | 27 | A future-known opportunity, not a universal online guarantee |
| No optimistic rejection, but recorded-trace optimum misses target | 7 | Neither positive certification nor all-trajectory impossibility |

The partition is identical under ideal and 0.5-second execution assumptions.
Under the separate unrestricted-future model, all 168 also fail the universal
deterministic-policy promise. These statements have different quantifiers.
The nine speed-envelope models yield no sufficient lower certificate; that
failure does not extend the universal impossibility result to coupled motion.

See the [generated report](results/synthesis_v1/REPORT.md),
[episode-level evidence](results/synthesis_v1/summary.json),
[paper blueprint](PAPER_BLUEPRINT.md), [updated validation priorities](VALIDATION_PLAN.md)
and [targeted novelty review](RELATED_WORK.md).

## Reproduction and case inspection

Only the Python standard library is needed for this synthesis:

```console
python -m feasibility_synthesis.synthesize
python -m unittest feasibility_synthesis.test_synthesis -v
python -m feasibility_synthesis.synthesize --episode v2:River01:12:11 --eta half_second
```

The case command prints evidence, contract and required scope qualifiers. It is
a retrospective diagnostic, **not an admission service**. Structured qualifier
checks reject unsupported claim categories; they do not verify arbitrary
manuscript prose or prove the original mathematics. The original method audits
remain authoritative for optimizer, geometry and timing correctness.

`--build` creates a new output directory and refuses to overwrite an existing
one. Source and input hashes are bound in metadata. No old artifact, fresh
holdout, raw pose archive, manuscript or acknowledgment was changed.

Reframing alone does not make the study submission-ready. The contribution is
a candidate application-specific feasibility/measurement result, not a new
general Bellman algorithm, physiology model or calibrated prediction method.
