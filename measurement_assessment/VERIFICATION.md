# Synthesis verification

28 October 2026. This verification concerns aggregation and claim provenance,
not a new scientific experiment or a rerun of every historical controller.

- Windows Python 3.12.14: 11 synthesis tests pass; complete register regeneration
  agrees with the published summary and report.
- WSL Python 3.14.4: the same 11 tests pass; identical regenerated register.
- Canonical synthesis SHA256 on both systems:
  `79b41bf818fa3bd52da21363dddbacd1b62e634a3eb55b2daacf5d1de7465124`.
- Seven canonical input-JSON hashes are recorded in `results/assessment_v1/summary.json`.
  All 1,512 saved early-commitment rows are aggregated by policy/delay/cohort and
  checked against frozen summaries. No new data are downloaded or experiments run.
- Tests reject incomplete cells, duplicate episodes, summary discrepancies,
  holdout contamination and non-finite serialization. They retain the adverse
  cost-greedy comparison and distinguish contracts and sample units.
- No prior experimental code, inputs or outcomes are edited. The repository CI
  adds this verifier while retaining the previous scientific replay checks.
- The preceding experiment's final CI run 40703920330 at
  `a2d5d4787c3df7d2266f2f834fb436e05cb096f7` was verified completed/success.
  This is not a claim about CI for a later assessment commit.

The literature audit explicitly identifies inaccessible recent full texts.
Software verification cannot resolve those novelty-review gaps, establish
human QoE, or turn the failed development screen into a successful method.
