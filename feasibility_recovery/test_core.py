import unittest
import numpy as np
from feasibility_recovery.core import (
    feasible_reference, select_action, update_debt, partition, quality_radius,
)
from recovery_pilot.core import all_actions


class FeasibilityTests(unittest.TestCase):
    def test_joint_target_not_independent_maxima(self):
        q = np.array([[1, 4], [1, 4.]])
        costs = np.array([[1, 4], [1, 4.]])
        floor, ceiling, witness, level = feasible_reference(q, costs, 5)
        np.testing.assert_equal(ceiling, [4, 4])
        np.testing.assert_equal(floor, [1, 1])
        self.assertLessEqual(costs[np.arange(2), witness].sum(), 5)
        self.assertEqual(level, 1)

    def test_ceiling_does_not_drag_other_clients_to_its_floor(self):
        q = np.array([[1, 2, 2], [1, 3, 4.]])
        costs = np.array([[1, 2, 8], [1, 2, 3.]])
        floor, ceiling, witness, _ = feasible_reference(q, costs, 5)
        np.testing.assert_equal(floor, [2, 4])
        np.testing.assert_equal(witness, [1, 2])

    def test_nonmonotone_tables_match_brute_force(self):
        rng = np.random.default_rng(8231)
        for _ in range(120):
            q = rng.uniform(1, 5, (3, 4))
            costs = rng.uniform(1, 20, (3, 4))
            budget = costs.min(axis=1).sum() + rng.uniform(0, 30)
            f, u, witness, height = feasible_reference(q, costs, budget)
            a = all_actions(3, 4)
            a = a[costs[np.arange(3), a].sum(axis=1) <= budget + 1e-8]
            self.assertTrue(np.all(q[np.arange(3), witness] >= f - 1e-12))
            self.assertLessEqual(costs[np.arange(3), witness].sum(), budget + 1e-8)
            for h in np.unique(np.r_[1, u, q[q <= 4]]):
                reachable = np.any(np.all(q[np.arange(3), a] >= np.minimum(u, h) - 1e-12, axis=1))
                if h > height:
                    self.assertFalse(reachable)
            perm = [2, 0, 1]
            fp, up, _, hp = feasible_reference(q[perm], costs[perm], budget)
            np.testing.assert_allclose(fp, f[perm])
            np.testing.assert_allclose(up, u[perm])
            self.assertEqual(height, hp)

    def test_admission_and_invalid(self):
        with self.assertRaises(ValueError):
            feasible_reference([[2, 4], [2, 4]], [[2, 5], [2, 5]], 3)
        with self.assertRaises(ValueError):
            feasible_reference([[np.nan, 4]], [[2, 5]], 3)

    def test_infeasible_debt_antiwindup_and_surplus_repayment(self):
        fixed = feasible = np.array([0.])
        for _ in range(30):
            fixed = update_debt(fixed, [4], [2])
            feasible = update_debt(feasible, [2], [2])
        self.assertGreater(fixed[0], 19)
        self.assertEqual(feasible[0], 0)
        np.testing.assert_equal(update_debt([2], [2], [4]), [0])

    def test_equal_targets_imply_equal_queues_and_actions(self):
        q = np.array([[2, 3, 4, 4.2, 4.5, 5], [2.1, 3.1, 4, 4.1, 4.6, 5]])
        costs = np.tile(np.arange(1, 7), (2, 1))
        args = (q, 0, costs, 12, np.array([2., 1]), np.ones(2), np.ones(2, int))
        a, meta = select_action("feasible_recovery", *args)
        b, baseline = select_action("fixed_debt", *args)
        np.testing.assert_equal(a, b)
        np.testing.assert_equal(meta["target"], baseline["target"])

    def test_exact_score_and_permutation_unique_optima(self):
        rng = np.random.default_rng(375)
        for _ in range(20):
            q = rng.uniform(1.4, 5, (3, 6))
            costs = rng.uniform(1, 8, (3, 6))
            debt, last, previous = rng.uniform(0, 6, 3), np.zeros(3), np.array([1, 2, 0])
            a, m = select_action("feasible_recovery", q, .2, costs, 16, debt, last, previous)
            perm = np.array([2, 0, 1])
            b, _ = select_action("feasible_recovery", q[perm], .2, costs[perm], 16, debt[perm], last, previous[perm])
            np.testing.assert_equal(b, a[perm])
            # Independent scalar exhaustive evaluation, excluding exact score ties.
            from recovery_pilot.core import LADDER
            scores = []
            for candidate in all_actions(3):
                if costs[np.arange(3), candidate].sum() <= 16:
                    lower = np.maximum(1, q[np.arange(3), candidate] - .2)
                    score = np.sum(np.log(lower) + debt / (1 + debt.mean()) * lower)
                    score -= .08 * np.mean(np.abs(np.log((LADDER[candidate] + .05) / (LADDER[previous] + .05))))
                    scores.append(score)
            self.assertAlmostEqual(m["objective"], max(scores))

    def test_split_and_radius_have_no_test_argument(self):
        p = partition(list(range(1, 29)))
        self.assertFalse(set(p["calibration"]) & set(p["test"]))
        self.assertEqual(len(p["test"]), 19)
        pred = np.ones((18, 6)) * 3
        cal = np.broadcast_to(pred, (9, 18, 6)).copy()
        cal[8, 17, 5] = 3.7
        radius, scores = quality_radius(pred, cal)
        self.assertAlmostEqual(radius, .7)
        self.assertEqual(len(scores), 9)


if __name__ == "__main__":
    unittest.main()
