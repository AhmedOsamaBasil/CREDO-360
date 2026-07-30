# CREDO-360 package manifest

## Entry points

- `README.md` - topic, mathematical seed, and package map.
- `TECHNICAL_NOVELTY.md` - opportunity-aware calibrated debt formulation.
- `EXPERIMENT_REPORT.md` - corrected phase-2 results and qualified claims.
- `LIVE_EXPERIMENT_REPORT.md` - measured Mininet integration experiment.
- `LIVE_POWERED_EXPERIMENT_REPORT.md` - 30-seed paired live campaign,
  confirmatory inference, mechanism analysis, and claim boundary.
- `JOURNAL_EXPERIMENT_PROTOCOL.md` - frozen TMM journal-extension protocol.
- `JOURNAL_GATE_FINAL_REPORT.md` - completed 30-seed, two-condition
  gate-identification result and qualified claims.
- `JOURNAL_MULTIMEDIA_GENERALIZATION_REPORT.md` - completed independent
  360-degree content/head-trace result, heterogeneity, and claim boundary.
- `JOURNAL_SCALABILITY_REPORT.md` - completed single-threaded WSL controller
  latency, bounded-candidate, feasibility, and peak-memory result.
- `JOURNAL_IMPAIRMENT_SMOKE_REPORT.md` - one-seed engineering validation of
  the non-actionable service-ceiling condition; not inferential evidence.
- `EXPERIMENT_REPORT_PHASE1_REJECTED.md` - preserved rejected first phase.
- `testbed/README.md` - reproduction and interpretation guide.
- `testbed/FEATURE_SCHEMA.md` - recovered 13-column published-data schema.
- `testbed/config.yaml` - final 12-seed configuration.
- `testbed/prepare_data.py` - named data and packet-trace preparation.
- `testbed/model.py` - heteroscedastic CUDA deep ensemble.
- `testbed/calibration.py` - conformal calibration and feedback.
- `testbed/run_experiment.py` - shared-link replay benchmark.
- `testbed/analyze_results.py` - paired tests, intervals, and figures.
- `testbed/analyze_sensitivity.py` - service-floor sensitivity analysis.
- `testbed/tests/` - unit tests.
- `testbed/data/provenance.json` - source provenance and limitations.
- `live_testbed/export_portable_model.py` - RTX training and portable export.
- `live_testbed/portable_qoe.py` - NumPy inference and live controller.
- `live_testbed/benchmark_scalability.py` - deterministic-cover scalability
  campaign.
- `live_testbed/plot_scalability.py` - journal scalability figure generator.
- `live_testbed/test_candidate_scaling.py` - 5--30-user feasibility,
  boundedness, and determinism tests.
- `live_testbed/run_mininet_experiment.py` - shared-link concurrent DASH run.
- `live_testbed/POWERED_EXPERIMENT_PROTOCOL.md` - frozen live analysis plan.
- `live_testbed/analyze_live.py` / `plot_live.py` - live inference and figures.
- `live_testbed/analyze_gate_campaign.py` / `plot_gate_campaign.py` - frozen
  Experiment A audit, paired inference, interactions, and journal figure.
- `live_testbed/run_journal_gate_campaign.py` - resumable sequential runner
  for both frozen Experiment A conditions.
- `live_testbed/test_portable.py` - export and capacity-safety checks.
- `multimedia_testbed/prepare_qoevave.py` - public-media acquisition,
  NVENC representations, content complexity, and held-out viewport outcomes.
- `multimedia_testbed/run_generalization.py` - 30-seed paired trace-driven
  campaign using measured VBR segment sizes.
- `multimedia_testbed/analyze_generalization.py` - audit, paired inference,
  content heterogeneity, and publication figures.
- `multimedia_testbed/test_generalization.py` - split, viewport, transport,
  quality-index, and analysis tests.

## Literature

- `literature/REVIEW_PROTOCOL.md` - systematic-review protocol.
- `literature/search_openalex.py` - reproducible discovery script.
- `literature/discovery/` - raw queries and 470-record candidate table.
- `literature/included_studies.csv` - current 25-study evidence matrix.
- `literature/LITERATURE_SYNTHESIS.md` - evidence synthesis.
- `literature/NOVELTY_ASSESSMENT_DRAFT.md` - invalidated/surviving claims.

## Results

- `testbed/results_explicit_final/` - corrected 12-seed run and statistics.
- `testbed/sensitivity/` - QoE service-floor sensitivity outputs.
- `live_testbed/results/live_run/` - accepted floor-4.0 integration trace.
- `live_testbed/results/live_campaign_30seed/` - complete 30-seed paired
  campaign, audit, seed metrics, tests, intervals, and publication figures.
- `live_testbed/results/journal_scalability/` - raw per-decision timing,
  aggregate table, metadata, and figure from the 30-seed journal campaign.
- `live_testbed/results/journal_impairment_smoke/` - one-seed engineering
  trace used only to validate the powered impairment design.
- `live_testbed/results/journal_gate_nonactionable_30seed/` and
  `journal_gate_capacity_30seed/` - complete raw 30-seed paired conditions.
- `live_testbed/results/journal_gate_analysis/` - passed audits, seed and
  aggregate metrics, frozen primary tests, condition interactions, and
  publication PNG/PDF.
- `multimedia_testbed/artifacts/qoevave/` - source hashes, empirical
  complexity, subject split, measured segment sizes, and derived VW-PSNR.
- `multimedia_testbed/results/generalization_30seed/` - complete raw paired
  campaign and frozen plan.
- `multimedia_testbed/results/generalization_analysis/` - passed audit,
  seed metrics, four primary tests, content effects, and publication figures.
- `live_testbed/results/live_run_floor15_rejected/` - preserved zero-debt run.
- Phase-1 and `screen_*` folders are retained as tuning and negative runs.
  They document decisions and are not confirmatory evidence.

The package now contains a live network-emulation stage with real concurrent
HTTP segment delivery. Its QoE values remain model-estimated, not new human
ratings or a headset experiment.
