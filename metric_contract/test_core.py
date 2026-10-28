"""Synthetic fixtures only; no exposed outcomes needed to validate the method."""
import unittest
import numpy as np
from metric_contract.data import metric_values, INPUTS
from metric_contract.core import (
    TICKS, SLOT, offsets, debt, score, path_arrays, metric_paths, bound, rescore,
)
from metric_contract.check import scalar_frontier, compare


def fixture():
    quality = np.tile(np.array([10, 20, 30, 40, 50, 60]), (6, 2, 1))
    costs = np.tile(np.array([50000, 100000, 150000, 200000, 250000, 300000]), (6, 1))
    return quality, costs


class MetricContractTests(unittest.TestCase):
    def test_original_mapping_and_mse_inverse(self):
        self.assertEqual(metric_values("30"), (3000, 3000000, 30000000, -65025000))

    def test_clipping_separated_from_unclipped_metric(self):
        a, b = metric_values("42"), metric_values("48")
        self.assertEqual(a[:2], b[:2])
        self.assertLess(a[2], b[2])
        self.assertLess(a[3], b[3])

    def test_rounding_half_up_and_finer_scale(self):
        self.assertEqual(metric_values("30.003")[0], 3001)
        self.assertEqual(metric_values("30.003")[1], 3000500)

    def test_nonfinite_rejected(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.assertRaises(ValueError):
                metric_values(value)

    def test_no_private_or_new_data_input(self):
        self.assertEqual(len(INPUTS), 7)
        self.assertFalse(any(".external" in p or p.endswith("mp4") for p in INPUTS))

    def test_zero_debt_not_counted_as_success(self):
        self.assertEqual(score(0, 7), {"applicable": False, "unpaid": None, "targets_met": [None]*4})

    def test_thresholds_and_credit_cap(self):
        self.assertEqual(score(8, 4)["targets_met"], [True, True, False, False])
        self.assertEqual(score(8, 99)["unpaid"], 0)
        with self.assertRaises(ValueError):
            score(1, -1)

    def test_transfer_offsets_are_exact_and_asymmetric(self):
        self.assertEqual(offsets((100000, 300000)), (219500, 419500))
        self.assertEqual(offsets((300000, 100000)), (419500, 219500))
        with self.assertRaises(ValueError):
            offsets((0, 1))

    def test_cold_deadline_excludes_first_segment(self):
        quality, costs = fixture()
        arrays = path_arrays(costs, 1, 1200000)
        safe, gains = metric_paths(quality, arrays, 1)
        self.assertEqual(int(gains["deadline"].max()), 0)
        self.assertGreater(int(gains["media"].max()), 0)

    def test_reserve_zero_only_baseline_with_strictly_increasing_cost(self):
        quality, costs = fixture()
        arrays = path_arrays(costs, 2, 0)
        self.assertEqual(arrays["resource_paths"], 1)
        self.assertEqual(arrays["choices"].tolist(), [[[2, 2], [2, 2]]])

    def test_positive_extra_spending_never_refunded(self):
        quality, costs = fixture()
        costs[3, 3] = 100000  # Saving does not refund an earlier upgrade.
        arrays = path_arrays(costs, 2, 0)
        self.assertFalse(any(p[0, 0] == 3 for p in arrays["choices"]))

    def test_floor_failure_is_not_hidden_by_structural_rung(self):
        quality, costs = fixture()
        quality[2, 1, 3] = 29
        arrays = path_arrays(costs, 1, 1200000)
        safe, _ = metric_paths(quality, arrays, 1)
        self.assertTrue(all(not s for s, p in zip(safe, arrays["choices"]) if p[0, 1] == 3))

    def test_positive_affine_invariance(self):
        quality, costs = fixture()
        arrays = path_arrays(costs, 2, 200000)
        safe, gains = metric_paths(quality, arrays, 2)
        safe2, gains2 = metric_paths(3*quality+7, arrays, 2)
        np.testing.assert_array_equal(safe, safe2)
        for clock in gains:
            np.testing.assert_array_equal(3*gains[clock], gains2[clock])
            self.assertEqual(score(debt(quality, 0), int(gains[clock].max())),
                             score(debt(3*quality+7, 0), int(gains2[clock].max())))

    def test_nonlinear_change_can_reverse_path_rankings(self):
        q, _ = fixture()
        q[:2, 0, 2] = 20
        q[2, 0, 2:4] = (20, 30)
        q[3, 0, 2:4] = (40, 49)
        def saved(rungs):
            return {"rounds": [{"segment": j+2, "decision": {"rungs": [a, 2]},
                                "play_end": [20+10*j, 20+10*j]} for j, a in enumerate(rungs)]}
        a, b = saved((3, 2)), saved((2, 3))
        self.assertLess(rescore(q, a, 2, 0, "media")["unpaid"], rescore(q, b, 2, 0, "media")["unpaid"])
        self.assertGreater(rescore(q*q, a, 2, 0, "media")["unpaid"], rescore(q*q, b, 2, 0, "media")["unpaid"])

    def test_exact_deadline_boundary_includes_completion(self):
        q, _ = fixture()
        saved = {"rounds": [{"segment": 2, "decision": {"rungs": [3, 2]}, "play_end": [10, 10]}]}
        self.assertEqual(rescore(q, saved, 1, 0, "deadline")["gain"], 10)
        saved["rounds"][0]["play_end"][0] += 1/TICKS
        self.assertEqual(rescore(q, saved, 1, 0, "deadline")["gain"], 0)

    def test_scalar_enumerator_and_witness_minimum_cost(self):
        rng = np.random.default_rng(20261028)
        for _ in range(5):
            q, costs = fixture()
            q[:, :, 3:] += rng.integers(-15, 16, size=(6, 2, 3))
            reserve = 200000
            arrays = path_arrays(costs, 2, reserve)
            safe, gains = metric_paths(q, arrays, 2)
            independent = scalar_frontier(q, costs, 2, reserve)
            for clock in ("media", "deadline"):
                for impairment in (0, 1):
                    self.assertTrue(compare(independent, bound(debt(q, impairment), safe, gains[clock], arrays), clock))

    def test_all_path_deadline_gain_bounded_by_eventual(self):
        q, costs = fixture()
        arrays = path_arrays(costs, 2, 1200000)
        _, gains = metric_paths(q, arrays, 2)
        self.assertTrue((gains["deadline"] <= gains["media"]).all())

    def test_monotone_targets_and_horizons(self):
        q, costs = fixture()
        prior = {"media": 0, "deadline": 0}
        for horizon in (1, 2, 4):
            arrays = path_arrays(costs, horizon, 200000)
            safe, gains = metric_paths(q, arrays, horizon)
            for clock in prior:
                result = bound(debt(q, 0), safe, gains[clock], arrays)
                self.assertGreaterEqual(result["max_gain"], prior[clock])
                self.assertEqual(result["targets_met"], sorted(result["targets_met"], reverse=True))
                prior[clock] = result["max_gain"]


if __name__ == "__main__":
    unittest.main()
