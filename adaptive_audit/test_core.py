import unittest
from itertools import product
import numpy as np
from adaptive_audit.finite import values, enumerate_two_stage, analytic_cases
from adaptive_audit.core import State, advance, solve, score_path, feedback_visibility, response_table
from geometric_admission.geometry import family, bounds
from metric_contract.core import TICKS, path_arrays
from admission_contract.core import clocks, path_stats, ETA


class FiniteGameTests(unittest.TestCase):
    def test_complete_small_games(self):
        r = analytic_cases()
        self.assertEqual((r['rectangular_exact_checks'], r['coupled_exact_checks']), (256, 512))

    def test_informative_coupling_helps(self):
        r = analytic_cases()['cases']['coupled_informative_past']
        self.assertEqual((r['open_loop'], r['causal'], r['clairvoyant']), (0, 1, 1))

    def test_no_information_no_help(self):
        r = analytic_cases()['cases']['coupled_uninformative_past']
        self.assertEqual((r['open_loop'], r['causal'], r['clairvoyant']), (0, 0, 1))

    def test_revelation_order_matters(self):
        r = analytic_cases()['cases']
        self.assertEqual(r['current_outcome_after_commit']['causal'], 0)
        self.assertEqual(r['current_outcome_before_commit']['causal'], 1)

    def test_invalid_game(self):
        with self.assertRaises(ValueError): values([], [[0]], 0, [])
        with self.assertRaises(ValueError): values([[[1]]], [[2]], 1, [[0]])
        with self.assertRaises(ValueError): enumerate_two_stage([[[1]]], [[0]], 0, [[0]])


class ClockGameTests(unittest.TestCase):
    def setUp(self):
        self.costs = np.tile([10000, 20000, 100000, 200000, 400000, 800000], (6, 1))
        self.ds = [10*TICKS]*6
        self.reserve = int(2*self.costs[2:, 2].sum())
        self.reward = np.tile([0, 0, 0, 3, 7, 9], (6, 1))

    def test_dynamic_matches_independent_vector(self):
        arrays = path_arrays(self.costs, 4, self.reserve)
        for eta in (0, ETA):
            for multiplier in (0, 1, 3):
                reward = self.reward*multiplier
                result = solve(self.costs, self.ds, self.reserve, reward, eta)
                _, gain = path_stats(reward, arrays['choices'], clocks(self.costs, arrays['choices'], self.ds, eta), self.ds)
                self.assertEqual(result['credit_upper'], int(gain.max()))
                self.assertEqual(score_path(result['path'], self.costs, self.ds, self.reserve, reward, eta)['credit'], int(gain.max()))

    def test_wait_is_charged_and_never_improves(self):
        result = solve(self.costs, self.ds, self.reserve, self.reward)
        fast = score_path(result['path'], self.costs, self.ds, self.reserve, self.reward)
        for waits in product((0, TICKS), repeat=4):
            slow = score_path(result['path'], self.costs, self.ds, self.reserve, self.reward, waits=waits)
            self.assertLessEqual(slow['credit'], fast['credit'])
            for a, b in zip(fast['steps'], slow['steps']):
                self.assertLessEqual(a['recipient_end_ticks'], b['recipient_end_ticks'])
        late = score_path(result['path'], self.costs, self.ds, self.reserve, self.reward, waits=[40*TICKS, 0, 0, 0])
        self.assertEqual(late['credit'], 0)

    def test_budget_and_cap(self):
        self.assertIsNone(advance(State(), (5, 5), self.costs, self.ds, self.reserve))
        self.assertIsNone(advance(State(), (4, 2), self.costs, self.ds, 0))
        self.assertEqual(advance(State(), (2, 2), self.costs, self.ds, 0).spent, 0)

    def test_bad_actions_and_time(self):
        with self.assertRaises(ValueError): advance(State(), (1, 2), self.costs, self.ds, self.reserve)
        with self.assertRaises(ValueError): advance(State(), (2, 2), self.costs, self.ds, self.reserve, wait=-1)
        with self.assertRaises(ValueError): solve(self.costs, self.ds, -1, self.reward)

    def test_completion_boundary(self):
        path = [[2, 2]]*4
        q = self.reward.copy(); q[:, 2] = 1
        s = score_path(path, self.costs, self.ds, self.reserve, q, eta=0)
        first = s['steps'][0]['recipient_end_ticks']
        exact = score_path(path, self.costs, self.ds, self.reserve, q, eta=0, waits=[40*TICKS-first, 0, 0, 0])
        over = score_path(path, self.costs, self.ds, self.reserve, q, eta=0, waits=[40*TICKS-first+1, 0, 0, 0])
        self.assertEqual(exact['credit'], 10*TICKS)
        self.assertEqual(over['credit'], 0)

    def test_feedback_no_future_and_delay_monotonic(self):
        s = score_path([[2, 2]]*4, self.costs, self.ds, self.reserve, self.reward)
        fast = feedback_visibility(s['steps'], self.ds)
        slow = feedback_visibility(s['steps'], self.ds, TICKS)
        self.assertTrue(all(r['own_segment_samples_before_commit'] == 0 for r in fast))
        self.assertFalse(fast[1]['past_segment_information'][0]['completed_report_available'])
        self.assertGreater(fast[1]['past_segment_information'][0]['samples_available'], 0)
        for a, b in zip(fast, slow):
            for x, y in zip(a['past_segment_information'], b['past_segment_information']):
                self.assertLessEqual(y['samples_available'], x['samples_available'])

    def test_adversary_uses_same_mask_for_reference(self):
        maps = np.full((6, 60, 72), 20.0)
        maps[3] = 19.0; maps[4] = 21.0
        masks = family(); lower, _, witness = bounds(maps, masks)
        delta, rows = response_table(maps, masks, witness)
        self.assertTrue((delta[2:, 3] == 1000000).all())
        self.assertTrue((delta[2:, 4] == -1000000).all())
        self.assertTrue((delta[:, 2] == 0).all())
        self.assertEqual(len(rows), 16)
        self.assertTrue((delta[2:, 3:] <= lower[2:, 3:]+5).all())


if __name__ == '__main__':
    unittest.main()
