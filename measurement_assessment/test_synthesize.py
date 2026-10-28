"""Checks for extraction, evidence boundaries and retained adverse comparisons."""
import copy
import unittest

from measurement_assessment.synthesize import (
    canonical, check_summary, load_inputs, policy_summary, report, synthesize,
)


class SynthesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = load_inputs()
        cls.result = synthesize(cls.inputs)

    def test_sample_units_not_policy_runs(self):
        sample = self.result["sampling"]
        self.assertEqual(sample["reused_episode_keys"], 168)
        self.assertEqual(sample["reused_participant_identifiers"], 28)
        self.assertEqual(len(sample["scenes"]), 6)
        self.assertEqual(sample["early_policy_runs"], 1512)

    def test_primary_remains_failed_and_worse_than_cost_greedy(self):
        result = self.result["simulated_prefix_playback"]
        self.assertFalse(result["frozen_screen_passed"])
        for group in ("all", "v2", "v3"):
            self.assertGreater(result["contrasts"][group]["unpaid_increase_vs_cost_greedy"], 0)
            self.assertGreater(result["contrasts"][group]["unpaid_reduction_vs_completed"], 0)
        self.assertFalse(self.result["interpretation"]["resubmission_ready_by_reframing_alone"])

    def test_contracts_remain_separate(self):
        frontier = self.result["relative_payload_frontier_no_cumulative_reserve"]
        self.assertEqual(frontier["no_donor_loss"]["counts_by_multiplier"]["3"], 147)
        self.assertEqual(frontier["largest_half_count_at_2x_across_all_donor_slices"], 0)
        bounds = {r["benchmark"]: r for r in self.result["fixed_file_cap_offline_opportunity"]}
        self.assertEqual(bounds["strict"]["half_repaid"], 96)
        self.assertEqual(bounds["quality_guard"]["half_repaid"], 95)

    def test_measured_and_simulated_evidence_are_distinct(self):
        measured = self.result["selected_transfer_receipts"]
        self.assertEqual(measured["nominal"]["decisions"], 96)
        self.assertEqual(measured["nominal"]["deadline_misses"], 0)
        self.assertEqual(measured["stress"]["deadline_misses"], 12)
        self.assertIn("simulated", self.result["simulated_prefix_playback"]["scope"])
        self.assertEqual(self.result["completed_feedback_loopback"]["messages"], 1008)
        self.assertFalse(self.result["finite_payload_reserve"]["field_available_capacity_identified"])

    def test_malformed_or_missing_episode_cells_rejected(self):
        inputs = {**self.inputs, "early": {**self.inputs["early"],
                  "rows": self.inputs["early"]["rows"][:-1]}}
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            synthesize(inputs)

    def test_duplicate_episode_rejected(self):
        row = self.inputs["early"]["rows"][0]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            policy_summary([row, row])

    def test_independent_summary_check_detects_changed_value(self):
        row = self.inputs["early"]["rows"][0]
        actual = policy_summary([row])
        with self.assertRaisesRegex(ValueError, "disagrees"):
            check_summary(actual, {**actual, "unpaid_fraction": actual["unpaid_fraction"] + .01})

    def test_json_canonicalization_ignores_key_order_not_values(self):
        self.assertEqual(canonical({"b": 2, "a": 1}), canonical({"a": 1, "b": 2}))
        self.assertNotEqual(canonical({"a": 1}), canonical({"a": 2}))
        with self.assertRaises(ValueError):
            canonical({"invalid": float("nan")})

    def test_holdout_contamination_rejected(self):
        inputs = {**self.inputs, "early": {**self.inputs["early"], "fresh_holdout_used": True}}
        with self.assertRaisesRegex(ValueError, "exposed"):
            synthesize(inputs)

    def test_source_mutation_changes_hash(self):
        inputs = {**self.inputs, "service": copy.deepcopy(self.inputs["service"])}
        inputs["service"]["probes"][0]["repeat"] = 999
        changed = synthesize(inputs)
        self.assertNotEqual(self.result["source_json_sha256"], changed["source_json_sha256"])

    def test_report_retains_failure_and_no_new_test_claim(self):
        text = report(self.result)
        self.assertIn("FAILED", text)
        self.assertIn("no new simulation or statistical test", text)
        self.assertIn("not independent subjects", text)


if __name__ == "__main__":
    unittest.main()
