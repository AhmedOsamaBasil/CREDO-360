# Absolute-loss-constrained compensation: exposed-data development

This package adds a pathwise terminal unpaid-loss cap to allowance timing and
a causal nearest-neighbor opportunity envelope. It uses only the already
exposed v2/v3 objective-quality catalogues; it is not a fresh holdout.

The first data-connected setting is deliberately small: two users, one bounded
compensation transfer, two past impairment segments and four recovery segments.
Every policy is given exact current viewport utilities. Future gains are
forecast from other content and participant IDs, without target-future inputs.
This is a current-information timing diagnostic, not a deployable streaming
player or human-QoE validation.

- [Locked plan](PLAN.md): data, controls, fixed settings and progression screen.
- [Technical derivation](THEORY.md): hard-cap filtering, interval reduction,
  rational certificates, causal boundaries and infeasibility handling.
- [Complete development report](results/development_v1/REPORT.md): all scenes,
  sensitivities, controls and failures after evaluation.
- [Interpretation and feasibility diagnosis](INTERPRETATION.md): the completed
  screen fails; no episode can satisfy the half-repayment request under the
  tested menu, even with perfect future knowledge. No fresh test is justified.

## Reproduce

From the repository root, with Python 3.12+, NumPy, SciPy and pytest:

```bash
python -m pytest causal_compensation -q
python -m causal_compensation.verify
python -m causal_compensation.diagnose
# Regenerate only into a new directory; never overwrite the published batch:
python -m causal_compensation.run --output work/causal_compensation_rebuild
```

Keep assertions enabled (do not use `python -O`). The result includes the
complete original episode inputs, nearest-neighbor identities, interval bounds,
six-policy loss/regret certificates and every selected realized trajectory.
Expectations over randomized policies are exact, not estimates from sampled
seeds. Published source/input/result hashes support full replay verification.

The primary cap is unpaid fraction <=.5, an exploratory service specification.
It is enforced for every mixture component in every modeled future. An
infeasible forecast is reported explicitly; a model miss can still break the
realized terminal cap. Neither condition is silently relabeled as recovery.
All donor/byte/one-transfer constraints remain pathwise regardless of forecast.

No older experimental files are modified. No new media or participant data are
downloaded, and no manuscript claim is updated by this development package.
