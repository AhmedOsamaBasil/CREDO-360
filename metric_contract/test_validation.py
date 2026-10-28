"""Post-publication regression checks, separate from frozen method fixtures."""
import gzip
import json
import unittest
from metric_contract.data import ROOT

OUT = ROOT/"metric_contract/results"


@unittest.skipUnless((OUT/"sensitivity_v1/metadata.json").exists(), "Outcomes not yet published")
class PublishedSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with gzip.open(OUT/"sensitivity_v1/results.json.gz", "rt") as stream:
            cls.result = json.load(stream)
        cls.diagnostic = json.loads((OUT/"diagnostics_v1/results.json").read_text())

    def test_complete_grid_and_independent_checks(self):
        self.assertEqual(len(self.result["fixed_path_rows"]), 64512)
        self.assertEqual(len(self.result["oracle_rows"]), 8064)
        self.assertEqual(self.result["audits"]["independent_queries"], 4032)
        self.assertEqual(self.result["audits"]["minimum_cost_target_checks"], 32256)

    def test_original_parity_is_retained(self):
        self.assertEqual(self.result["audits"]["original_policy_scores"], 1344)
        self.assertEqual(self.result["audits"]["original_strict_oracles"], 168)

    def test_common_floors_do_not_remove_metric_dependence(self):
        self.assertEqual({r["metric"]: r["half"] for r in self.diagnostic["common_floor_oracle"]},
                         {"index": 96, "fine_index": 96, "psnr_db": 168, "negative_mse": 28})

    def test_ranking_reversal_and_adverse_cohort_retained(self):
        rows = {(r["group"],r["metric"]):r["primary_minus_cost_greedy_unpaid"]
                for r in self.diagnostic["primary_cost_greedy_contrasts"]}
        self.assertGreater(rows["all", "index"], 0)
        self.assertLess(rows["all", "psnr_db"], 0)
        self.assertGreater(rows["v3", "psnr_db"], 0)
        self.assertGreater(rows["all", "negative_mse"], 0)

    def test_tiny_floor_losses_not_misrepresented_as_large(self):
        losses = self.diagnostic["primary_floor_loss_summary"]
        self.assertEqual(losses["count"], 25)
        self.assertEqual(losses["hidden_by_legacy_rounding_or_clipping"], 24)
        self.assertLess(losses["max_db"], .003)

    def test_no_new_success_or_holdout(self):
        self.assertFalse(self.result["fresh_holdout"])
        self.assertFalse(self.result["new_controller_tuned"])
        self.assertFalse(self.diagnostic["new_scientific_success_claim"])


if __name__ == "__main__":
    unittest.main()
