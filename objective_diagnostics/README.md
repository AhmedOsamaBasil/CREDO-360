# Objective and window-accounting diagnosis

This package is a **development-only** comparison on already exposed v2/v3
content. It is not another fresh holdout. No recovery variant passed its locked
development screen; do not describe it as a successful new-method result.

Read [INTERPRETATION.md](INTERPRETATION.md) for the scientific conclusion,
[PLAN.md](PLAN.md) for the frozen method/stopping rule, and the generated
[complete report](results/development_v1/diagnostics/REPORT.md) for all checks.
The method and plan were committed and pushed as `8ddd46b` before this run.
All historical source, data and result artifacts remain unchanged.

## What is implemented

- Exact next-window accounting: expire before selecting, retain negative
  balance for banking, or use the maximum suffix residual for non-banking.
  Expiry-induced changes are separate from delivered service.
- A matched factorial: joint-mixture target cap 4/5, crossed with signed
  banking/non-banking/H-scaled memoryless feedback. Window 24 and strength 8
  were fixed, not selected by this comparison.
- Direct stateless Nash, instantaneous max-min, window max-min and window
  Nash controls under exactly the same stateless-Nash byte cap.
- Capacity-only, fixed-rung ceiling and sender-quality-range ceiling cases.
  Current capability profiles are observed; future transition times are not.
- Two exposed catalogues, six paired seeds each, 120 rounds, five users,
  ten policies: 360 episodes and 216,000 scientific user-round records.

The contract is feasible over mixtures of joint actions in expectation. It
is not a guaranteed integral schedule or actual-quality guarantee. Virtual
queues and logarithmic fairness are established methods; see the primary
prior-art references in [PLAN.md](PLAN.md). The finite window does not inherit
infinite-horizon queue guarantees automatically. These controls are not new
theoretical contributions.

## Reproduction

Run commands from the repository root. NumPy, SciPy, Matplotlib and pytest are
required; no GPU, raw source media download or network access is needed for
this derived-data replay.

```bash
python -m pytest objective_diagnostics -q
python -m objective_diagnostics.audit
```

The audit verifies hashes, re-fits the sender/calibration tables, re-solves
both contract variants and checks every support witness, replays every
scientific record and reconstructs window balances independently by enumerating
suffixes. It also checks fixed budgets, playback conservation, manipulation
severity, summaries, descriptive bootstrap contrasts and every screen flag.
Measured wall-clock runtimes are checked for validity, not reproduced.

To run an additional DEVELOPMENT replication without replacing the frozen run:

```bash
python -m objective_diagnostics.run --output work/objective_replication
python -m objective_diagnostics.analyze --output work/objective_replication
python -m objective_diagnostics.audit --output work/objective_replication
```

Both the run directory and diagnostic subdirectory must be new. No overwrite
option is provided. The two original data directories remain
`feasibility_recovery/data/v2` and `horizon_recovery/data/v3`; their original
test labels are now exposed and must not be advertised as fresh here.

## Saved artifacts

`results/development_v1/` contains the compressed raw records, 360 episode
summaries, calibrated models, seed plans, LP witnesses, all paired contrasts,
action disagreements, frozen source/input/output hashes and the failed screen.
`diagnostics/` contains all 60 policy/scenario/catalogue means, window accounting,
content-level impairment severity, all development checks, and PNG/PDF figures.
Separate Windows/Linux integrity reports accompany the completed publication.

No new human subjects, live headset playback, subjective QoE measurement or
new independent dataset is involved. The six source segments repeat; CPU
runtime is not injected into the synchronized fluid playback clock. Quality
uses the existing clipped normalized PSNR index, with raw VW-PSNR also reported.
Six-seed intervals are descriptive and conditional on the exposed content.
