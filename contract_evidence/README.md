# Recovery-contract evidence presentation

This post-freeze layer assembles the complete published Wu feasibility and
software-playback results for technical reporting. It does not change a source,
contract, controller, measurement, registered endpoint or evaluation. All sixteen
registered clips, six metadata exclusions and 452 directed pairs are retained.
The playback input must be a complete audited 366-session public export, not a
selected subset of private in-progress logs.

The independent descriptive assembly checks the original equal-clip macros,
retains undefined admission-fulfillment rates, and keeps failed measurements
missing rather than turning them into zero recovery. It preserves the distinction
between the original-parent account and the secondary actual-chunk account.
The three repeats of a playback cell are not independent participants. No
population inference, new superiority test or fresh-quality-holdout claim is made.

Pure constructed-fixture checks (no real playback data required):

```sh
python -m unittest contract_evidence.test_assemble -v
python -m unittest contract_evidence.test_latex_tables -v
```

Only after complete technical playback results have been exported and audited:

```sh
python -m contract_evidence.assemble --output contract_evidence/results/evidence_v1
python -m contract_evidence.assemble --output contract_evidence/results/evidence_v1 --verify
python -m contract_evidence.render --evidence contract_evidence/results/evidence_v1 --output contract_evidence/results/figures_v1
python -m contract_evidence.render --evidence contract_evidence/results/evidence_v1 --output contract_evidence/results/figures_v1 --verify
python -m contract_evidence.latex_tables --evidence contract_evidence/results/evidence_v1 --output contract_evidence/results/tables_v1
python -m contract_evidence.latex_tables --evidence contract_evidence/results/evidence_v1 --output contract_evidence/results/tables_v1 --verify
```

The output records exact fractions and source hashes. Both feasibility conditions
remain separate; pair-pooled counts and equal-clip macro fractions are explicitly
distinguished. A zero positive-admission count is not evidence of useful positive
certification or a 100% fulfillment rate.

The static figures retain every eligible clip and all 120 main timing cells.
The signed credited-fraction heatmap uses the fixed range [-1,1]. Incomplete
three-repetition cells are displayed as missing. Completion markers show a
cell's mean and full minimum--maximum range, not a confidence interval. The
two perturbation controls remain separate from the main figures and appear in
the complete evidence tables. Rendering does not select a favorable trace or
silently replace the original-parent metric with actual-chunk quality.

LaTeX exports contain source-bound table rows and numerical commands, without
choosing which outcomes to report. They retain all registrations, both conditions,
all controls and all planned timing cells. Missing macro estimates and undefined
fulfillment rates appear as `--`, not zero. Every file identifies the exact
evidence digest; decimal display uses half-even rounding without a binary64
integer conversion. The exact rational values remain in the JSON artifact.

The [related-methods comparison](LITERATURE.md) distinguishes this contract
audit from prior compensation queues, quality-aware admission, network-assisted
streaming, robust control and viewport prediction. It includes primary-source
links and [bibliographic records](references.bib), without claiming reproduction
or performance superiority over those systems.
